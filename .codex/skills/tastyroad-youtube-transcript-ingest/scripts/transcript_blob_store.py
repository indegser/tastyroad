#!/usr/bin/env python3

from __future__ import annotations

import gzip
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


LOCAL_ENV_PATH = Path(".env.local")
DEFAULT_BLOB_ACCESS = "private"
DEFAULT_BLOB_PREFIX = "transcripts"
DEFAULT_BLOB_CLI = "vercel"


class TranscriptLike(Protocol):
    language_code: str
    language: str
    is_generated: bool
    raw_segments: list[dict[str, Any]]
    segments: list[dict[str, Any]]
    text: str


class TargetLike(Protocol):
    youtube_video_id: int
    video_id: str
    source_name: str
    title: str


@dataclass(frozen=True)
class BlobObject:
    pathname: str
    size: int
    content_type: str


@dataclass(frozen=True)
class TranscriptBlobUpload:
    provider: str
    access: str
    raw: BlobObject
    segments: BlobObject
    uploaded_at: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_local_env(path: Path = LOCAL_ENV_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def blob_auth_options(env: dict[str, str]) -> list[str]:
    read_write_token = env.get("BLOB_READ_WRITE_TOKEN", "").strip()
    if read_write_token:
        return ["--rw-token", read_write_token]

    oidc_token = env.get("VERCEL_OIDC_TOKEN", "").strip()
    store_id = env.get("BLOB_STORE_ID", "").strip()
    if oidc_token and store_id:
        return ["--oidc-token", oidc_token, "--store-id", store_id]

    return []


def run_blob_cli(args: list[str], *, env_values: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env_values = env_values or load_local_env()
    env = os.environ.copy()
    env.update(env_values)
    auth_options = blob_auth_options(env_values)
    command = [env.get("VERCEL_BLOB_CLI", DEFAULT_BLOB_CLI), "blob", *args, *auth_options]
    scope = env.get("VERCEL_BLOB_SCOPE", "").strip()
    if scope:
        command.extend(["--scope", scope])

    return subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


def blob_is_configured(env_values: dict[str, str] | None = None) -> bool:
    env_values = env_values or load_local_env()
    return bool(blob_auth_options(env_values))


def safe_video_id(video_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in video_id)


def transcript_blob_key(transcript: TranscriptLike, content_hash: str) -> str:
    kind = "generated" if transcript.is_generated else "manual"
    language_code = safe_video_id(transcript.language_code or "unknown")
    return f"{language_code}-{kind}-{content_hash}"


def gzip_json(path: Path, value: Any) -> int:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    with gzip.open(path, "wb") as output:
        output.write(payload)
    return path.stat().st_size


def gzip_jsonl(path: Path, rows: list[dict[str, Any]]) -> int:
    with gzip.open(path, "wt", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            output.write("\n")
    return path.stat().st_size


def segment_blob_rows(transcript: TranscriptLike) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, segment in enumerate(transcript.segments):
        raw_index = int(segment.get("raw_index", index))
        raw_segment = (
            transcript.raw_segments[raw_index]
            if 0 <= raw_index < len(transcript.raw_segments)
            else {}
        )
        rows.append(
            {
                "segment_index": index,
                "start_seconds": float(segment["start"]),
                "duration_seconds": float(segment["duration"]),
                "end_seconds": float(segment["end"]),
                "text": str(segment["text"]),
                "raw_index": raw_index,
                "raw": raw_segment,
            }
        )
    return rows


def upload_file(
    path: Path,
    *,
    pathname: str,
    access: str,
    content_type: str,
    env_values: dict[str, str],
) -> BlobObject:
    run_blob_cli(
        [
            "put",
            str(path),
            "--pathname",
            pathname,
            "--access",
            access,
            "--allow-overwrite",
            "true",
            "--content-type",
            content_type,
        ],
        env_values=env_values,
    )
    return BlobObject(pathname=pathname, size=path.stat().st_size, content_type=content_type)


def upload_transcript_blobs(
    *,
    target: TargetLike,
    transcript: TranscriptLike,
    content_hash: str,
    fetched_at: str,
    prefix: str = DEFAULT_BLOB_PREFIX,
    access: str = DEFAULT_BLOB_ACCESS,
    env_values: dict[str, str] | None = None,
) -> TranscriptBlobUpload:
    env_values = env_values or load_local_env()
    if not blob_is_configured(env_values):
        raise RuntimeError(
            "Vercel Blob is not configured. Run `vercel blob create-store ...` "
            "and `vercel env pull`, or set BLOB_READ_WRITE_TOKEN."
        )

    video_id = safe_video_id(target.video_id)
    blob_key = transcript_blob_key(transcript, content_hash)
    normalized_prefix = prefix.strip("/").strip() or DEFAULT_BLOB_PREFIX
    raw_pathname = f"{normalized_prefix}/raw/{video_id}/{blob_key}.json.gz"
    segments_pathname = f"{normalized_prefix}/segments/{video_id}/{blob_key}.jsonl.gz"
    raw_document = {
        "video_id": target.video_id,
        "youtube_video_id": target.youtube_video_id,
        "source_name": target.source_name,
        "title": target.title,
        "provider": "youtube_transcript_api",
        "language_code": transcript.language_code,
        "language": transcript.language,
        "is_generated": transcript.is_generated,
        "content_hash": content_hash,
        "segment_count": len(transcript.segments),
        "fetched_at": fetched_at,
        "raw_segments": transcript.raw_segments,
    }
    segment_rows = segment_blob_rows(transcript)

    with tempfile.TemporaryDirectory(prefix="tastyroad-transcript-blob-") as directory:
        temp_dir = Path(directory)
        raw_file = temp_dir / "raw.json.gz"
        segments_file = temp_dir / "segments.jsonl.gz"
        gzip_json(raw_file, raw_document)
        gzip_jsonl(segments_file, segment_rows)
        raw_blob = upload_file(
            raw_file,
            pathname=raw_pathname,
            access=access,
            content_type="application/gzip",
            env_values=env_values,
        )
        segments_blob = upload_file(
            segments_file,
            pathname=segments_pathname,
            access=access,
            content_type="application/gzip",
            env_values=env_values,
        )

    return TranscriptBlobUpload(
        provider="vercel_blob",
        access=access,
        raw=raw_blob,
        segments=segments_blob,
        uploaded_at=now_iso(),
    )


def download_blob(pathname: str, *, access: str = DEFAULT_BLOB_ACCESS) -> bytes:
    with tempfile.TemporaryDirectory(prefix="tastyroad-transcript-blob-") as directory:
        output_path = Path(directory) / "blob"
        run_blob_cli(
            [
                "get",
                pathname,
                "--access",
                access,
                "--output",
                str(output_path),
            ]
        )
        return output_path.read_bytes()


def load_segments_blob(pathname: str, *, access: str = DEFAULT_BLOB_ACCESS) -> list[dict[str, Any]]:
    if not pathname:
        return []
    payload = gzip.decompress(download_blob(pathname, access=access)).decode("utf-8")
    segments: list[dict[str, Any]] = []
    for line in payload.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        segments.append(
            {
                "segment_index": int(row["segment_index"]),
                "start_seconds": float(row["start_seconds"]),
                "duration_seconds": float(row["duration_seconds"]),
                "end_seconds": float(row["end_seconds"]),
                "text": str(row["text"]),
            }
        )
    return segments
