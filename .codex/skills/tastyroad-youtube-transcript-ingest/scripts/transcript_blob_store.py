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
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


LOCAL_ENV_PATH = Path(".env.local")
DEFAULT_BLOB_ACCESS = "private"
DEFAULT_BLOB_PREFIX = "transcripts"
DEFAULT_BLOB_CLI = "vercel"
DEFAULT_STORAGE_PROVIDER = "vercel_blob"
DEFAULT_SUPABASE_BUCKET = "tastyroad-transcripts"
STORAGE_PROVIDERS = ("vercel_blob", "supabase_storage")


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
    command = [env.get("VERCEL_BLOB_CLI", DEFAULT_BLOB_CLI), "blob", *auth_options, *args]
    scope = env.get("VERCEL_BLOB_SCOPE", "").strip()
    if scope:
        command.extend(["--scope", scope])

    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or f"exit status {exc.returncode}"
        raise RuntimeError(f"Vercel Blob CLI command failed: {detail}") from exc


def blob_is_configured(env_values: dict[str, str] | None = None) -> bool:
    env_values = env_values or load_local_env()
    return bool(blob_auth_options(env_values))


def normalize_storage_provider(
    storage_provider: str | None,
    env_values: dict[str, str] | None = None,
) -> str:
    env_values = env_values or load_local_env()
    provider = (
        storage_provider
        or env_values.get("TRANSCRIPT_STORAGE_PROVIDER", "")
        or DEFAULT_STORAGE_PROVIDER
    ).strip()
    if provider.startswith("sqlite+"):
        provider = provider.split("+", 1)[1]
    if provider not in STORAGE_PROVIDERS:
        raise ValueError(
            f"Unsupported transcript storage provider {provider!r}. "
            f"Expected one of: {', '.join(STORAGE_PROVIDERS)}."
        )
    return provider


def supabase_service_key(env_values: dict[str, str]) -> str:
    return (
        env_values.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or env_values.get("SUPABASE_SECRET_KEY", "").strip()
    )


def supabase_is_configured(env_values: dict[str, str] | None = None) -> bool:
    env_values = env_values or load_local_env()
    return bool(env_values.get("SUPABASE_URL", "").strip() and supabase_service_key(env_values))


def supabase_bucket(env_values: dict[str, str]) -> str:
    return env_values.get("SUPABASE_STORAGE_BUCKET", "").strip() or DEFAULT_SUPABASE_BUCKET


def supabase_object_url(env_values: dict[str, str], pathname: str) -> str:
    base_url = env_values.get("SUPABASE_URL", "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("SUPABASE_URL is required for Supabase Storage transcript archives.")
    bucket = quote(supabase_bucket(env_values), safe="")
    object_path = quote(pathname.strip("/"), safe="/")
    return f"{base_url}/storage/v1/object/{bucket}/{object_path}"


def supabase_headers(env_values: dict[str, str], *, content_type: str | None = None) -> dict[str, str]:
    service_key = supabase_service_key(env_values)
    if not service_key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY is required for private Supabase Storage transcript archives."
        )
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def run_supabase_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    data: bytes | None = None,
) -> bytes:
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=90) as response:
            return response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace").strip()
        raise RuntimeError(
            f"Supabase Storage request failed with HTTP {exc.code}: {detail or exc.reason}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Supabase Storage request failed: {exc.reason}") from exc


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


def upload_vercel_file(
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


def upload_supabase_file(
    path: Path,
    *,
    pathname: str,
    content_type: str,
    env_values: dict[str, str],
) -> BlobObject:
    url = supabase_object_url(env_values, pathname)
    headers = supabase_headers(env_values, content_type=content_type)
    headers["x-upsert"] = "true"
    run_supabase_request("POST", url, headers=headers, data=path.read_bytes())
    return BlobObject(pathname=pathname, size=path.stat().st_size, content_type=content_type)


def upload_file(
    path: Path,
    *,
    pathname: str,
    access: str,
    content_type: str,
    provider: str,
    env_values: dict[str, str],
) -> BlobObject:
    if provider == "vercel_blob":
        return upload_vercel_file(
            path,
            pathname=pathname,
            access=access,
            content_type=content_type,
            env_values=env_values,
        )
    if provider == "supabase_storage":
        return upload_supabase_file(
            path,
            pathname=pathname,
            content_type=content_type,
            env_values=env_values,
        )
    raise ValueError(f"Unsupported transcript storage provider: {provider}")


def upload_transcript_blobs(
    *,
    target: TargetLike,
    transcript: TranscriptLike,
    content_hash: str,
    fetched_at: str,
    prefix: str = DEFAULT_BLOB_PREFIX,
    access: str = DEFAULT_BLOB_ACCESS,
    storage_provider: str | None = None,
    env_values: dict[str, str] | None = None,
) -> TranscriptBlobUpload:
    env_values = env_values or load_local_env()
    provider = normalize_storage_provider(storage_provider, env_values)
    if provider == "vercel_blob" and not blob_is_configured(env_values):
        raise RuntimeError(
            "Vercel Blob is not configured. Run `vercel blob create-store ...` "
            "and `vercel env pull`, or set BLOB_READ_WRITE_TOKEN."
        )
    if provider == "supabase_storage" and not supabase_is_configured(env_values):
        raise RuntimeError(
            "Supabase Storage is not configured. Run `vercel env pull` after adding the "
            "Supabase integration, or set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
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
            provider=provider,
            env_values=env_values,
        )
        segments_blob = upload_file(
            segments_file,
            pathname=segments_pathname,
            access=access,
            content_type="application/gzip",
            provider=provider,
            env_values=env_values,
        )

    return TranscriptBlobUpload(
        provider=provider,
        access=access,
        raw=raw_blob,
        segments=segments_blob,
        uploaded_at=now_iso(),
    )


def download_vercel_blob(
    pathname: str,
    *,
    access: str,
    env_values: dict[str, str] | None = None,
) -> bytes:
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
            ],
            env_values=env_values,
        )
        return output_path.read_bytes()


def download_supabase_blob(pathname: str, *, env_values: dict[str, str]) -> bytes:
    url = supabase_object_url(env_values, pathname)
    headers = supabase_headers(env_values)
    return run_supabase_request("GET", url, headers=headers)


def download_blob(
    pathname: str,
    *,
    access: str = DEFAULT_BLOB_ACCESS,
    storage_provider: str | None = None,
    env_values: dict[str, str] | None = None,
) -> bytes:
    env_values = env_values or load_local_env()
    provider = normalize_storage_provider(storage_provider, env_values)
    if provider == "vercel_blob":
        return download_vercel_blob(pathname, access=access, env_values=env_values)
    if provider == "supabase_storage":
        return download_supabase_blob(pathname, env_values=env_values)
    raise ValueError(f"Unsupported transcript storage provider: {provider}")


def load_segments_blob(
    pathname: str,
    *,
    access: str = DEFAULT_BLOB_ACCESS,
    storage_provider: str | None = None,
) -> list[dict[str, Any]]:
    if not pathname:
        return []
    payload = gzip.decompress(
        download_blob(pathname, access=access, storage_provider=storage_provider)
    ).decode("utf-8")
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
