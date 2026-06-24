#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from transcript_blob_store import (
    DEFAULT_BLOB_ACCESS,
    DEFAULT_BLOB_PREFIX,
    DEFAULT_STORAGE_PROVIDER,
    STORAGE_PROVIDERS,
    upload_transcript_blobs,
)
from transcript_schema import DEFAULT_SQLITE, ensure_transcript_schema


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


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


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


def transcript_from_row(track: sqlite3.Row, segment_rows: list[sqlite3.Row]) -> TranscriptPayload:
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


def select_tracks(connection: sqlite3.Connection, missing_only: bool, limit: int | None) -> list[sqlite3.Row]:
    where_clause = "where coalesce(segments_blob_path, '') = ''" if missing_only else ""
    sql = f"""
        select
          t.*,
          y.title
        from youtube_transcript_tracks t
        join youtube_videos y on y.id = t.youtube_video_id
        {where_clause}
        order by t.fetched_at desc, t.id desc
    """
    params: list[Any] = []
    if limit is not None:
        sql += " limit ?"
        params.append(limit)
    return connection.execute(sql, params).fetchall()


def archive(args: argparse.Namespace) -> dict[str, int]:
    with sqlite3.connect(args.sqlite) as connection:
        connection.row_factory = sqlite3.Row
        ensure_transcript_schema(connection)
        tracks = select_tracks(connection, args.missing_only, args.limit)
        stats = {"target_count": len(tracks), "uploaded": 0, "skipped": 0}

        for track in tracks:
            segment_rows = connection.execute(
                """
                select segment_index, start_seconds, duration_seconds, end_seconds, text, raw_json
                from youtube_transcript_segments
                where track_id = ?
                order by segment_index
                """,
                (track["id"],),
            ).fetchall()
            if not segment_rows:
                print(f"Skipping {track['video_id']} track={track['id']}: no SQLite segments")
                stats["skipped"] += 1
                continue

            target = VideoTarget(
                youtube_video_id=int(track["youtube_video_id"]),
                video_id=str(track["video_id"]),
                source_name=str(track["source_name"]),
                title=str(track["title"]),
            )
            transcript = transcript_from_row(track, segment_rows)
            if args.dry_run:
                print(
                    f"Would archive {track['video_id']} track={track['id']} "
                    f"segments={len(segment_rows)} hash={track['content_hash']}"
                )
                continue

            blob_upload = upload_transcript_blobs(
                target=target,
                transcript=transcript,
                content_hash=str(track["content_hash"]),
                fetched_at=str(track["fetched_at"]),
                prefix=args.blob_prefix,
                access=args.blob_access,
                storage_provider=args.storage_provider,
            )
            storage_provider = (
                blob_upload.provider
                if args.prune_sqlite_payload
                else f"sqlite+{blob_upload.provider}"
            )
            raw_json = "[]" if args.prune_sqlite_payload else str(track["raw_json"])
            connection.execute(
                """
                update youtube_transcript_tracks
                set storage_provider = ?,
                    raw_json = ?,
                    raw_blob_path = ?,
                    raw_blob_size = ?,
                    segments_blob_path = ?,
                    segments_blob_size = ?,
                    blob_uploaded_at = ?,
                    blob_metadata_json = ?
                where id = ?
                """,
                (
                    storage_provider,
                    raw_json,
                    blob_upload.raw.pathname,
                    blob_upload.raw.size,
                    blob_upload.segments.pathname,
                    blob_upload.segments.size,
                    blob_upload.uploaded_at,
                    json_text(
                        {
                            "provider": blob_upload.provider,
                            "access": blob_upload.access,
                            "raw": {
                                "pathname": blob_upload.raw.pathname,
                                "size": blob_upload.raw.size,
                                "content_type": blob_upload.raw.content_type,
                            },
                            "segments": {
                                "pathname": blob_upload.segments.pathname,
                                "size": blob_upload.segments.size,
                                "content_type": blob_upload.segments.content_type,
                            },
                        }
                    ),
                    int(track["id"]),
                ),
            )
            if args.prune_sqlite_payload:
                connection.execute(
                    "delete from youtube_transcript_segments where track_id = ?",
                    (track["id"],),
                )
            connection.commit()
            stats["uploaded"] += 1
            print(f"Archived {track['video_id']} track={track['id']} storage={storage_provider}")

        return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive existing SQLite transcript payloads into object storage."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--missing-only", action="store_true", help="Only upload tracks without a segments blob path.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--blob-prefix", default=DEFAULT_BLOB_PREFIX)
    parser.add_argument("--blob-access", choices=("private", "public"), default=DEFAULT_BLOB_ACCESS)
    parser.add_argument(
        "--storage-provider",
        choices=STORAGE_PROVIDERS,
        default=DEFAULT_STORAGE_PROVIDER,
        help="Object storage provider for archived transcript payloads.",
    )
    parser.add_argument(
        "--prune-sqlite-payload",
        action="store_true",
        help="After upload, blank track raw_json and delete timed SQLite segment rows.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stats = archive(args)
    print(json_text(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
