#!/usr/bin/env python3

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from transcript_blob_store import (
    DEFAULT_BLOB_ACCESS,
    download_blob,
    load_local_env,
    upload_transcript_blobs,
    upload_supabase_file,
    blob_is_configured,
    supabase_is_configured,
)
from transcript_schema import DEFAULT_SQLITE, ensure_transcript_schema


SOURCE_PROVIDER = "vercel_blob"
TARGET_PROVIDER = "supabase_storage"


@dataclass(frozen=True)
class VideoTarget:
    youtube_video_id: int
    video_id: str
    source_name: str
    title: str


@dataclass(frozen=True)
class TranscriptPayload:
    language_code: str
    language: str
    is_generated: bool
    raw_segments: list[dict[str, Any]]
    segments: list[dict[str, Any]]
    text: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_env(args: argparse.Namespace) -> dict[str, str]:
    if args.env_file:
        if not args.env_file.exists():
            raise FileNotFoundError(f"Env file does not exist: {args.env_file}")
        return load_local_env(args.env_file)
    return load_local_env()


def validate_gzip_json(pathname: str, payload: bytes, *, jsonl: bool) -> None:
    text = gzip.decompress(payload).decode("utf-8")
    if jsonl:
        for index, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            json.loads(line)
            if index >= 3:
                break
        return
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"{pathname}: expected a JSON object in raw transcript payload.")


def load_raw_segments(track: sqlite3.Row, segment_rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    raw_json = str(track["raw_json"] or "").strip()
    if raw_json and raw_json != "[]":
        value = json.loads(raw_json)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]

    raw_segments: list[dict[str, Any]] = []
    for segment in segment_rows:
        raw_segment = str(segment["raw_json"] or "").strip()
        if raw_segment and raw_segment != "{}":
            value = json.loads(raw_segment)
            raw_segments.append(dict(value) if isinstance(value, dict) else {})
            continue
        raw_segments.append(
            {
                "text": str(segment["text"]),
                "start": float(segment["start_seconds"]),
                "duration": float(segment["duration_seconds"]),
            }
        )
    return raw_segments


def transcript_from_payload_row(track: sqlite3.Row, segment_rows: list[sqlite3.Row]) -> TranscriptPayload:
    raw_segments = load_raw_segments(track, segment_rows)
    segments = [
        {
            "text": str(segment["text"]),
            "start": float(segment["start_seconds"]),
            "duration": float(segment["duration_seconds"]),
            "end": float(segment["end_seconds"]),
            "raw_index": index,
        }
        for index, segment in enumerate(segment_rows)
    ]
    return TranscriptPayload(
        language_code=str(track["language_code"]),
        language=str(track["language"]),
        is_generated=bool(track["is_generated"]),
        raw_segments=raw_segments,
        segments=segments,
        text=str(track["transcript_text"]),
    )


def select_tracks(connection: sqlite3.Connection, args: argparse.Namespace) -> list[sqlite3.Row]:
    sql = """
        select
          t.id,
          t.youtube_video_id,
          t.video_id,
          t.source_name,
          t.language_code,
          t.language,
          t.is_generated,
          t.provider,
          t.content_hash,
          t.fetched_at,
          t.storage_provider,
          t.raw_blob_path,
          t.raw_blob_size,
          t.segments_blob_path,
          t.segments_blob_size,
          t.blob_metadata_json,
          y.title
        from youtube_transcript_tracks t
        join youtube_videos y on y.id = t.youtube_video_id
        where t.storage_provider = ?
          and coalesce(t.raw_blob_path, '') != ''
          and coalesce(t.segments_blob_path, '') != ''
    """
    params: list[Any] = [SOURCE_PROVIDER]
    if args.source:
        sql += " and t.source_name = ?"
        params.append(args.source)
    if args.video_id:
        placeholders = ",".join("?" for _ in args.video_id)
        sql += f" and t.video_id in ({placeholders})"
        params.extend(args.video_id)
    sql += " order by t.fetched_at, t.id"
    if args.limit is not None:
        sql += " limit ?"
        params.append(args.limit)
    return connection.execute(sql, params).fetchall()


def find_payload_track(payload_connection: sqlite3.Connection, track: sqlite3.Row) -> sqlite3.Row:
    payload_track = payload_connection.execute(
        """
        select *
        from youtube_transcript_tracks
        where video_id = ?
          and language_code = ?
          and is_generated = ?
          and provider = ?
          and content_hash = ?
        """,
        (
            str(track["video_id"]),
            str(track["language_code"]),
            int(track["is_generated"]),
            str(track["provider"]),
            str(track["content_hash"]),
        ),
    ).fetchone()
    if payload_track is None:
        raise RuntimeError(f"{track['video_id']} track={track['id']}: no matching payload track found.")
    return payload_track


def payload_segments(payload_connection: sqlite3.Connection, payload_track_id: int) -> list[sqlite3.Row]:
    return payload_connection.execute(
        """
        select segment_index, start_seconds, duration_seconds, end_seconds, text, raw_json
        from youtube_transcript_segments
        where track_id = ?
        order by segment_index
        """,
        (payload_track_id,),
    ).fetchall()


def download_source_object(
    pathname: str,
    *,
    access: str,
    env_values: dict[str, str],
) -> bytes:
    return download_blob(
        pathname,
        access=access,
        storage_provider=SOURCE_PROVIDER,
        env_values=env_values,
    )


def upload_target_object(
    pathname: str,
    payload: bytes,
    *,
    content_type: str,
    env_values: dict[str, str],
) -> int:
    with tempfile.TemporaryDirectory(prefix="tastyroad-blob-migration-") as directory:
        temp_path = Path(directory) / "object.gz"
        temp_path.write_bytes(payload)
        uploaded = upload_supabase_file(
            temp_path,
            pathname=pathname,
            content_type=content_type,
            env_values=env_values,
        )
        return uploaded.size


def verify_target_object(
    pathname: str,
    expected_sha256: str,
    *,
    access: str,
    env_values: dict[str, str],
) -> None:
    payload = download_blob(
        pathname,
        access=access,
        storage_provider=TARGET_PROVIDER,
        env_values=env_values,
    )
    actual_sha256 = sha256_hex(payload)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"{pathname}: Supabase verification hash mismatch "
            f"(expected {expected_sha256}, got {actual_sha256})."
        )


def migrated_metadata(
    track: sqlite3.Row,
    *,
    access: str,
    raw_size: int,
    segments_size: int,
    raw_sha: str,
    segments_sha: str,
    payload_source: str,
) -> str:
    previous_metadata: Any = None
    previous_text = str(track["blob_metadata_json"] or "").strip()
    if previous_text:
        try:
            previous_metadata = json.loads(previous_text)
        except json.JSONDecodeError:
            previous_metadata = previous_text

    metadata: dict[str, Any] = {
        "provider": TARGET_PROVIDER,
        "access": access,
        "migrated_from": SOURCE_PROVIDER,
        "payload_source": payload_source,
        "migrated_at": now_iso(),
        "raw": {
            "pathname": str(track["raw_blob_path"]),
            "size": raw_size,
            "content_type": "application/gzip",
            "sha256": raw_sha,
        },
        "segments": {
            "pathname": str(track["segments_blob_path"]),
            "size": segments_size,
            "content_type": "application/gzip",
            "sha256": segments_sha,
        },
    }
    if previous_metadata:
        metadata["previous_blob_metadata"] = previous_metadata
    return json_text(metadata)


def update_track(
    connection: sqlite3.Connection,
    track: sqlite3.Row,
    *,
    access: str,
    raw_size: int,
    segments_size: int,
    raw_sha: str,
    segments_sha: str,
    payload_source: str,
) -> None:
    migrated_at = now_iso()
    cursor = connection.execute(
        """
        update youtube_transcript_tracks
        set storage_provider = ?,
            raw_blob_size = ?,
            segments_blob_size = ?,
            blob_uploaded_at = ?,
            blob_metadata_json = ?
        where id = ?
          and storage_provider = ?
        """,
        (
            TARGET_PROVIDER,
            raw_size,
            segments_size,
            migrated_at,
            migrated_metadata(
                track,
                access=access,
                raw_size=raw_size,
                segments_size=segments_size,
                raw_sha=raw_sha,
                segments_sha=segments_sha,
                payload_source=payload_source,
            ),
            int(track["id"]),
            SOURCE_PROVIDER,
        ),
    )
    if cursor.rowcount != 1:
        raise RuntimeError(f"{track['video_id']} track={track['id']}: DB update did not affect a row.")
    connection.commit()


def migrate_track(
    connection: sqlite3.Connection,
    track: sqlite3.Row,
    *,
    args: argparse.Namespace,
    env_values: dict[str, str],
    payload_connection: sqlite3.Connection | None,
) -> bool:
    raw_path = str(track["raw_blob_path"])
    segments_path = str(track["segments_blob_path"])

    if args.dry_run and not args.verify_source_read and payload_connection is None:
        print(f"Would migrate {track['video_id']} track={track['id']} source={track['source_name']}")
        return False

    if payload_connection is not None:
        return migrate_track_from_payload_sqlite(
            connection,
            payload_connection,
            track,
            args=args,
            env_values=env_values,
        )

    raw_payload = download_source_object(raw_path, access=args.blob_access, env_values=env_values)
    segments_payload = download_source_object(segments_path, access=args.blob_access, env_values=env_values)
    raw_sha = sha256_hex(raw_payload)
    segments_sha = sha256_hex(segments_payload)

    if not args.skip_gzip_validation:
        validate_gzip_json(raw_path, raw_payload, jsonl=False)
        validate_gzip_json(segments_path, segments_payload, jsonl=True)

    if args.dry_run:
        print(
            f"Readable {track['video_id']} track={track['id']} "
            f"raw={len(raw_payload)} segments={len(segments_payload)} "
            f"raw_sha={raw_sha[:12]} segments_sha={segments_sha[:12]}"
        )
        return False

    raw_size = upload_target_object(
        raw_path,
        raw_payload,
        content_type="application/gzip",
        env_values=env_values,
    )
    segments_size = upload_target_object(
        segments_path,
        segments_payload,
        content_type="application/gzip",
        env_values=env_values,
    )

    if not args.skip_upload_verification:
        verify_target_object(raw_path, raw_sha, access=args.blob_access, env_values=env_values)
        verify_target_object(segments_path, segments_sha, access=args.blob_access, env_values=env_values)

    update_track(
        connection,
        track,
        access=args.blob_access,
        raw_size=raw_size,
        segments_size=segments_size,
        raw_sha=raw_sha,
        segments_sha=segments_sha,
        payload_source=SOURCE_PROVIDER,
    )
    print(f"Migrated {track['video_id']} track={track['id']} source={track['source_name']}")
    return True


def migrate_track_from_payload_sqlite(
    connection: sqlite3.Connection,
    payload_connection: sqlite3.Connection,
    track: sqlite3.Row,
    *,
    args: argparse.Namespace,
    env_values: dict[str, str],
) -> bool:
    payload_track = find_payload_track(payload_connection, track)
    segment_rows = payload_segments(payload_connection, int(payload_track["id"]))
    if not segment_rows:
        raise RuntimeError(f"{track['video_id']} track={track['id']}: payload SQLite has no segments.")

    if args.dry_run:
        print(
            f"Would reconstruct {track['video_id']} track={track['id']} "
            f"segments={len(segment_rows)} source={track['source_name']}"
        )
        return False

    target = VideoTarget(
        youtube_video_id=int(track["youtube_video_id"]),
        video_id=str(track["video_id"]),
        source_name=str(track["source_name"]),
        title=str(track["title"]),
    )
    transcript = transcript_from_payload_row(payload_track, segment_rows)
    blob_upload = upload_transcript_blobs(
        target=target,
        transcript=transcript,
        content_hash=str(track["content_hash"]),
        fetched_at=str(track["fetched_at"]),
        access=args.blob_access,
        storage_provider=TARGET_PROVIDER,
        env_values=env_values,
    )
    if blob_upload.raw.pathname != str(track["raw_blob_path"]):
        raise RuntimeError(
            f"{track['video_id']} track={track['id']}: raw pathname mismatch "
            f"{blob_upload.raw.pathname} != {track['raw_blob_path']}"
        )
    if blob_upload.segments.pathname != str(track["segments_blob_path"]):
        raise RuntimeError(
            f"{track['video_id']} track={track['id']}: segments pathname mismatch "
            f"{blob_upload.segments.pathname} != {track['segments_blob_path']}"
        )

    if args.skip_upload_verification:
        raw_payload = b""
        segments_payload = b""
        raw_sha = ""
        segments_sha = ""
    else:
        raw_payload = download_blob(
            blob_upload.raw.pathname,
            access=args.blob_access,
            storage_provider=TARGET_PROVIDER,
            env_values=env_values,
        )
        segments_payload = download_blob(
            blob_upload.segments.pathname,
            access=args.blob_access,
            storage_provider=TARGET_PROVIDER,
            env_values=env_values,
        )
        if not args.skip_gzip_validation:
            validate_gzip_json(blob_upload.raw.pathname, raw_payload, jsonl=False)
            validate_gzip_json(blob_upload.segments.pathname, segments_payload, jsonl=True)
        raw_sha = sha256_hex(raw_payload)
        segments_sha = sha256_hex(segments_payload)

    update_track(
        connection,
        track,
        access=args.blob_access,
        raw_size=blob_upload.raw.size,
        segments_size=blob_upload.segments.size,
        raw_sha=raw_sha,
        segments_sha=segments_sha,
        payload_source=str(args.payload_sqlite),
    )
    print(f"Reconstructed {track['video_id']} track={track['id']} source={track['source_name']}")
    return True


def migrate(args: argparse.Namespace) -> dict[str, Any]:
    env_values = load_env(args)
    if args.payload_sqlite and args.verify_source_read:
        raise RuntimeError("--verify-source-read cannot be combined with --payload-sqlite.")
    if payload_source_requires_blob(args):
        if not blob_is_configured(env_values):
            raise RuntimeError("Vercel Blob credentials are required to read source transcript objects.")
    if not args.dry_run:
        if not supabase_is_configured(env_values):
            raise RuntimeError("Supabase Storage credentials are required to write target transcript objects.")

    payload_connection = None
    if args.payload_sqlite:
        if not args.payload_sqlite.exists():
            raise FileNotFoundError(f"Payload SQLite does not exist: {args.payload_sqlite}")
        payload_connection = sqlite3.connect(args.payload_sqlite)
        payload_connection.row_factory = sqlite3.Row

    try:
        return migrate_with_connections(args, env_values, payload_connection)
    finally:
        if payload_connection is not None:
            payload_connection.close()


def payload_source_requires_blob(args: argparse.Namespace) -> bool:
    return not args.payload_sqlite and (not args.dry_run or args.verify_source_read)


def migrate_with_connections(
    args: argparse.Namespace,
    env_values: dict[str, str],
    payload_connection: sqlite3.Connection | None,
) -> dict[str, Any]:
    with sqlite3.connect(args.sqlite) as connection:
        connection.row_factory = sqlite3.Row
        ensure_transcript_schema(connection)
        tracks = select_tracks(connection, args)
        stats: dict[str, Any] = {
            "target_count": len(tracks),
            "migrated": 0,
            "checked": 0,
            "failed": 0,
            "failures": [],
        }
        for track in tracks:
            try:
                changed = migrate_track(
                    connection,
                    track,
                    args=args,
                    env_values=env_values,
                    payload_connection=payload_connection,
                )
                if changed:
                    stats["migrated"] += 1
                else:
                    stats["checked"] += 1
            except Exception as exc:
                stats["failed"] += 1
                stats["failures"].append(
                    {
                        "track_id": int(track["id"]),
                        "video_id": str(track["video_id"]),
                        "error": str(exc),
                    }
                )
                print(f"Failed {track['video_id']} track={track['id']}: {exc}")
                if not args.continue_on_error:
                    raise
        return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy Vercel Blob-backed transcript objects to Supabase Storage and update SQLite metadata."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--env-file", type=Path, help="Env file with Vercel Blob and Supabase credentials.")
    parser.add_argument(
        "--payload-sqlite",
        type=Path,
        help="Historical SQLite DB with raw_json and youtube_transcript_segments to reconstruct source payloads.",
    )
    parser.add_argument("--source", help="Limit to a source_name such as 김사원세끼 or 또간집.")
    parser.add_argument("--video-id", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--blob-access", choices=("private", "public"), default=DEFAULT_BLOB_ACCESS)
    parser.add_argument(
        "--verify-source-read",
        action="store_true",
        help="With --dry-run, download and validate source objects instead of only listing targets.",
    )
    parser.add_argument(
        "--skip-gzip-validation",
        action="store_true",
        help="Do not decompress and parse downloaded gzip JSON/JSONL payloads.",
    )
    parser.add_argument(
        "--skip-upload-verification",
        action="store_true",
        help="Do not read uploaded Supabase objects back for SHA-256 verification.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue after a failed track and report failures in the final JSON.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stats = migrate(args)
    print(json_text(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
