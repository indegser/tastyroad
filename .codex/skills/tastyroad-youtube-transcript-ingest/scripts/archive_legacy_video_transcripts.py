#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
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


DEFAULT_CONFIG = Path("data/sources/youtube_sources.json")
DEFAULT_PROVIDER = "youtube_transcript_api"


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


def content_hash(raw_segments: list[dict[str, Any]]) -> str:
    return hashlib.sha256(json_text(raw_segments).encode("utf-8")).hexdigest()


def load_source_aliases(config_path: Path) -> dict[str, str]:
    if not config_path.exists():
        return {}
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    aliases: dict[str, str] = {}
    for item in payload.get("sources", []):
        key = str(item.get("key", "")).strip()
        name = str(item.get("name", "")).strip()
        if key and name:
            aliases[key] = name
            aliases[name] = name
    return aliases


def resolve_source_name(source: str | None, config_path: Path) -> str | None:
    if not source:
        return None
    return load_source_aliases(config_path).get(source, source)


def normalize_segments(raw_segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for raw_index, segment in enumerate(raw_segments):
        text = " ".join(str(segment.get("text", "")).replace("\n", " ").split())
        if not text:
            continue
        start = float(segment.get("start", 0) or 0)
        duration = float(segment.get("duration", 0) or 0)
        segments.append(
            {
                "text": text,
                "start": start,
                "duration": duration,
                "end": start + duration,
                "raw_index": raw_index,
            }
        )
    return segments


def transcript_from_legacy_row(row: sqlite3.Row) -> TranscriptPayload:
    raw_value = json.loads(str(row["transcript_json"]))
    if not isinstance(raw_value, list):
        raise ValueError(f"{row['video_id']}: transcript_json must be a JSON array.")
    raw_segments = [dict(item) for item in raw_value if isinstance(item, dict)]
    segments = normalize_segments(raw_segments)
    if not segments:
        raise ValueError(f"{row['video_id']}: transcript_json has no timed text segments.")
    return TranscriptPayload(
        language_code=str(row["language_code"] or "unknown"),
        language=str(row["language"] or ""),
        is_generated=bool(row["is_generated"]),
        raw_segments=raw_segments,
        segments=segments,
        text=" ".join(segment["text"] for segment in segments).strip(),
    )


def select_legacy_rows(connection: sqlite3.Connection, args: argparse.Namespace) -> list[sqlite3.Row]:
    source_name = resolve_source_name(args.source, args.config)
    sql = """
        select
          vt.external_id as video_id,
          vt.language_code,
          vt.language,
          vt.is_generated,
          vt.transcript_json,
          vt.transcript_text,
          vt.fetched_at,
          y.id as youtube_video_id,
          y.title,
          s.name as source_name,
          coalesce(t.id, 0) as existing_track_id,
          coalesce(t.segments_blob_path, '') as existing_segments_blob_path
        from video_transcripts vt
        join youtube_videos y on y.video_id = vt.external_id
        join sources s on s.id = y.source_id
        left join youtube_transcript_tracks t on t.youtube_video_id = y.id
        where 1 = 1
    """
    params: list[Any] = []
    if source_name:
        sql += " and s.name = ?"
        params.append(source_name)
    if args.video_id:
        placeholders = ",".join("?" for _ in args.video_id)
        sql += f" and vt.external_id in ({placeholders})"
        params.extend(args.video_id)
    if args.missing_tracks_only:
        sql += """
          and not exists (
            select 1
            from youtube_transcript_tracks existing
            where existing.youtube_video_id = y.id
          )
        """
    sql += " order by y.published_at desc, y.id desc"
    if args.limit is not None:
        sql += " limit ?"
        params.append(args.limit)
    return connection.execute(sql, params).fetchall()


def upsert_transcript_track(
    connection: sqlite3.Connection,
    *,
    target: VideoTarget,
    transcript: TranscriptPayload,
    transcript_hash: str,
    fetched_at: str,
    blob_upload: Any,
) -> int:
    blob_metadata = {
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
        "legacy_source_table": "video_transcripts",
    }
    connection.execute(
        """
        insert into youtube_transcript_tracks (
          youtube_video_id,
          video_id,
          source_name,
          language_code,
          language,
          is_generated,
          provider,
          raw_json,
          transcript_text,
          content_hash,
          segment_count,
          storage_provider,
          raw_blob_path,
          raw_blob_size,
          segments_blob_path,
          segments_blob_size,
          blob_uploaded_at,
          blob_metadata_json,
          fetched_at
        )
        values (?, ?, ?, ?, ?, ?, ?, '[]', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(youtube_video_id, language_code, is_generated, provider) do update set
          source_name = excluded.source_name,
          language = excluded.language,
          raw_json = excluded.raw_json,
          transcript_text = excluded.transcript_text,
          content_hash = excluded.content_hash,
          segment_count = excluded.segment_count,
          storage_provider = excluded.storage_provider,
          raw_blob_path = excluded.raw_blob_path,
          raw_blob_size = excluded.raw_blob_size,
          segments_blob_path = excluded.segments_blob_path,
          segments_blob_size = excluded.segments_blob_size,
          blob_uploaded_at = excluded.blob_uploaded_at,
          blob_metadata_json = excluded.blob_metadata_json,
          fetched_at = excluded.fetched_at
        """,
        (
            target.youtube_video_id,
            target.video_id,
            target.source_name,
            transcript.language_code,
            transcript.language,
            1 if transcript.is_generated else 0,
            DEFAULT_PROVIDER,
            transcript.text,
            transcript_hash,
            len(transcript.segments),
            blob_upload.provider,
            blob_upload.raw.pathname,
            blob_upload.raw.size,
            blob_upload.segments.pathname,
            blob_upload.segments.size,
            blob_upload.uploaded_at,
            json_text(blob_metadata),
            fetched_at,
        ),
    )
    track_row = connection.execute(
        """
        select id
        from youtube_transcript_tracks
        where youtube_video_id = ?
          and language_code = ?
          and is_generated = ?
          and provider = ?
        """,
        (
            target.youtube_video_id,
            transcript.language_code,
            1 if transcript.is_generated else 0,
            DEFAULT_PROVIDER,
        ),
    ).fetchone()
    if track_row is None:
        raise RuntimeError(f"Could not resolve transcript track id for {target.video_id}")
    track_id = int(track_row["id"])
    connection.execute("delete from youtube_transcript_segments where track_id = ?", (track_id,))
    return track_id


def count_unarchived_legacy_rows(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        """
        select count(*) as count
        from video_transcripts vt
        join youtube_videos y on y.video_id = vt.external_id
        where not exists (
          select 1
          from youtube_transcript_tracks t
          where t.youtube_video_id = y.id
            and coalesce(t.segments_blob_path, '') != ''
        )
        """
    ).fetchone()
    return int(row["count"])


def archive(args: argparse.Namespace) -> dict[str, Any]:
    with sqlite3.connect(args.sqlite) as connection:
        connection.row_factory = sqlite3.Row
        ensure_transcript_schema(connection)
        if not connection.execute(
            "select 1 from sqlite_master where type = 'table' and name = 'video_transcripts'"
        ).fetchone():
            return {"target_count": 0, "uploaded": 0, "skipped": 0, "legacy_table": "missing"}

        rows = select_legacy_rows(connection, args)
        stats: dict[str, Any] = {
            "target_count": len(rows),
            "uploaded": 0,
            "skipped": 0,
            "dropped_legacy_table": False,
        }
        for row in rows:
            if row["existing_track_id"] and row["existing_segments_blob_path"] and not args.replace_existing:
                print(
                    f"Skipping {row['video_id']}: existing track "
                    f"{row['existing_track_id']} already has Blob segments"
                )
                stats["skipped"] += 1
                continue

            target = VideoTarget(
                youtube_video_id=int(row["youtube_video_id"]),
                video_id=str(row["video_id"]),
                source_name=str(row["source_name"]),
                title=str(row["title"]),
            )
            transcript = transcript_from_legacy_row(row)
            transcript_hash = content_hash(transcript.raw_segments)
            fetched_at = str(row["fetched_at"] or now_iso())
            if args.dry_run:
                print(
                    f"Would archive legacy {target.video_id} storage={args.storage_provider} "
                    f"segments={len(transcript.segments)} hash={transcript_hash}"
                )
                continue

            blob_upload = upload_transcript_blobs(
                target=target,
                transcript=transcript,
                content_hash=transcript_hash,
                fetched_at=fetched_at,
                prefix=args.blob_prefix,
                access=args.blob_access,
                storage_provider=args.storage_provider,
            )
            track_id = upsert_transcript_track(
                connection,
                target=target,
                transcript=transcript,
                transcript_hash=transcript_hash,
                fetched_at=fetched_at,
                blob_upload=blob_upload,
            )
            connection.commit()
            stats["uploaded"] += 1
            print(f"Archived legacy {target.video_id} track={track_id} storage={blob_upload.provider}")

        if args.drop_legacy_table_if_archived and not args.dry_run:
            remaining = count_unarchived_legacy_rows(connection)
            stats["unarchived_legacy_rows"] = remaining
            if remaining:
                print(f"Keeping video_transcripts: {remaining} rows still lack Blob-backed tracks")
            else:
                connection.execute("drop table video_transcripts")
                connection.commit()
                stats["dropped_legacy_table"] = True
                print("Dropped fully archived legacy table video_transcripts")

        return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive legacy video_transcripts rows into Blob-backed youtube_transcript_tracks."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source")
    parser.add_argument("--video-id", action="append", default=[])
    parser.add_argument(
        "--missing-tracks-only",
        action="store_true",
        help="Only archive legacy videos that have no youtube_transcript_tracks rows.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace an existing matching track when the legacy row is selected.",
    )
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
        "--drop-legacy-table-if-archived",
        action="store_true",
        help="Drop video_transcripts only after every legacy row has a Blob-backed track.",
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
