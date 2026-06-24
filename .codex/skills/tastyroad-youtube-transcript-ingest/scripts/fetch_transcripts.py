#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from transcript_blob_store import (
    DEFAULT_BLOB_ACCESS,
    DEFAULT_BLOB_PREFIX,
    TranscriptBlobUpload,
    upload_transcript_blobs,
)
from transcript_schema import DEFAULT_SQLITE, ensure_transcript_schema


DEFAULT_CONFIG = Path("data/sources/youtube_sources.json")
DEFAULT_LANGUAGES = ("ko", "en")
DEFAULT_PROVIDER = "youtube_transcript_api"
DEFAULT_STORAGE = "blob"
DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS = 0.0
DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS = 3
LOCAL_ENV_PATH = Path(".env.local")


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


def load_local_env(path: Path = LOCAL_ENV_PATH) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value


def comma_separated_env(name: str) -> list[str] | None:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def int_env(name: str, default: int) -> int:
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    return int(value)


def transcript_proxy_config() -> Any | None:
    load_local_env()
    webshare_username = os.environ.get("WEBSHARE_PROXY_USERNAME", "").strip()
    webshare_password = os.environ.get("WEBSHARE_PROXY_PASSWORD", "").strip()
    if webshare_username and webshare_password:
        try:
            from youtube_transcript_api.proxies import WebshareProxyConfig
        except ImportError as exc:
            raise RuntimeError(
                "youtube_transcript_api is required. Install youtube-transcript-api in the active Python environment."
            ) from exc

        return WebshareProxyConfig(
            proxy_username=webshare_username,
            proxy_password=webshare_password,
            filter_ip_locations=comma_separated_env("WEBSHARE_PROXY_LOCATIONS"),
            retries_when_blocked=int_env("WEBSHARE_PROXY_RETRIES_WHEN_BLOCKED", 10),
            domain_name=os.environ.get("WEBSHARE_PROXY_DOMAIN", "p.webshare.io").strip()
            or "p.webshare.io",
            proxy_port=int_env("WEBSHARE_PROXY_PORT", 80),
        )

    http_proxy = os.environ.get("YT_TRANSCRIPT_HTTP_PROXY", "").strip()
    https_proxy = os.environ.get("YT_TRANSCRIPT_HTTPS_PROXY", "").strip()
    if http_proxy or https_proxy:
        try:
            from youtube_transcript_api.proxies import GenericProxyConfig
        except ImportError as exc:
            raise RuntimeError(
                "youtube_transcript_api is required. Install youtube-transcript-api in the active Python environment."
            ) from exc

        return GenericProxyConfig(http_url=http_proxy or None, https_url=https_proxy or None)

    return None


def fetch_transcript(video_id: str, languages: tuple[str, ...]) -> TranscriptPayload:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:
        raise RuntimeError(
            "youtube_transcript_api is required. Install youtube-transcript-api in the active Python environment."
        ) from exc

    api = YouTubeTranscriptApi(proxy_config=transcript_proxy_config())
    transcript_list = api.list(video_id)
    transcript = transcript_list.find_transcript(list(languages))
    fetched = transcript.fetch()
    raw_segments = raw_segment_data(fetched)
    segments = normalize_segments(raw_segments)
    text = " ".join(segment["text"] for segment in segments).strip()
    return TranscriptPayload(
        language_code=str(transcript.language_code),
        language=str(transcript.language),
        is_generated=bool(transcript.is_generated),
        raw_segments=raw_segments,
        segments=segments,
        text=text,
    )


def raw_segment_data(fetched: Any) -> list[dict[str, Any]]:
    if hasattr(fetched, "to_raw_data"):
        raw_segments = fetched.to_raw_data()
    else:
        raw_segments = fetched

    result: list[dict[str, Any]] = []
    for segment in raw_segments:
        if hasattr(segment, "__dict__") and not isinstance(segment, dict):
            segment = segment.__dict__
        if not isinstance(segment, dict):
            continue
        result.append(dict(segment))
    return result


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


def is_youtube_block_error(error: Exception | str) -> bool:
    message = str(error)
    block_markers = (
        "YouTube is blocking requests from your IP",
        "RequestBlocked",
        "IpBlocked",
        "IP block",
    )
    return any(marker in message for marker in block_markers)


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
    aliases = load_source_aliases(config_path)
    return aliases.get(source, source)


def select_targets(
    connection: sqlite3.Connection,
    *,
    source_name: str | None,
    video_ids: list[str],
    missing_only: bool,
    limit: int | None,
) -> list[VideoTarget]:
    sql = """
        select
          y.id as youtube_video_id,
          y.video_id,
          s.name as source_name,
          y.title
        from youtube_videos y
        join sources s on s.id = y.source_id
        where 1 = 1
    """
    params: list[Any] = []
    if source_name:
        sql += " and s.name = ?"
        params.append(source_name)
    if video_ids:
        placeholders = ",".join("?" for _ in video_ids)
        sql += f" and y.video_id in ({placeholders})"
        params.extend(video_ids)
    if missing_only:
        sql += """
          and not exists (
            select 1
            from youtube_transcript_tracks t
            where t.youtube_video_id = y.id
          )
        """
    sql += " order by y.published_at desc, y.id desc"
    if limit is not None:
        sql += " limit ?"
        params.append(limit)

    return [
        VideoTarget(
            youtube_video_id=int(row["youtube_video_id"]),
            video_id=str(row["video_id"]),
            source_name=str(row["source_name"]),
            title=str(row["title"]),
        )
        for row in connection.execute(sql, params).fetchall()
    ]


def create_job(
    connection: sqlite3.Connection,
    *,
    scope_type: str,
    scope_value: str,
    languages: tuple[str, ...],
) -> int:
    cursor = connection.execute(
        """
        insert into youtube_transcript_jobs (
          scope_type,
          scope_value,
          requested_languages,
          status,
          started_at
        )
        values (?, ?, ?, 'running', ?)
        """,
        (scope_type, scope_value, json_text(list(languages)), now_iso()),
    )
    return int(cursor.lastrowid)


def finish_job(connection: sqlite3.Connection, job_id: int, status: str, stats: dict[str, Any]) -> None:
    connection.execute(
        """
        update youtube_transcript_jobs
        set status = ?,
            finished_at = ?,
            stats_json = ?
        where id = ?
        """,
        (status, now_iso(), json_text(stats), job_id),
    )


def record_attempt(
    connection: sqlite3.Connection,
    *,
    job_id: int | None,
    target: VideoTarget,
    languages: tuple[str, ...],
    status: str,
    error_type: str = "",
    error_message: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    connection.execute(
        """
        insert into youtube_transcript_fetch_attempts (
          job_id,
          youtube_video_id,
          video_id,
          provider,
          requested_languages,
          status,
          error_type,
          error_message,
          attempted_at,
          metadata_json
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            target.youtube_video_id,
            target.video_id,
            DEFAULT_PROVIDER,
            json_text(list(languages)),
            status,
            error_type,
            error_message,
            now_iso(),
            json_text(metadata or {}),
        ),
    )


def upsert_transcript_track(
    connection: sqlite3.Connection,
    *,
    target: VideoTarget,
    transcript: TranscriptPayload,
    fetched_at: str,
    storage: str,
    blob_upload: TranscriptBlobUpload | None,
) -> int:
    store_sqlite_payload = storage in ("sqlite", "both")
    raw_json = json_text(transcript.raw_segments) if store_sqlite_payload else "[]"
    transcript_hash = content_hash(transcript.raw_segments)
    storage_provider = {
        "blob": "vercel_blob",
        "both": "sqlite+vercel_blob",
        "sqlite": "sqlite",
    }[storage]
    raw_blob_path = blob_upload.raw.pathname if blob_upload else ""
    raw_blob_size = blob_upload.raw.size if blob_upload else 0
    segments_blob_path = blob_upload.segments.pathname if blob_upload else ""
    segments_blob_size = blob_upload.segments.size if blob_upload else 0
    blob_uploaded_at = blob_upload.uploaded_at if blob_upload else ""
    blob_metadata = (
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
        if blob_upload
        else {}
    )
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
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            raw_json,
            transcript.text,
            transcript_hash,
            len(transcript.segments),
            storage_provider,
            raw_blob_path,
            raw_blob_size,
            segments_blob_path,
            segments_blob_size,
            blob_uploaded_at,
            json_text(blob_metadata),
            fetched_at,
        ),
    )
    row = connection.execute(
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
    if row is None:
        raise RuntimeError(f"Could not resolve transcript track id for {target.video_id}")

    track_id = int(row["id"])
    connection.execute("delete from youtube_transcript_segments where track_id = ?", (track_id,))
    if store_sqlite_payload:
        for index, segment in enumerate(transcript.segments):
            raw_index = int(segment.get("raw_index", index))
            raw_segment = transcript.raw_segments[raw_index] if raw_index < len(transcript.raw_segments) else {}
            connection.execute(
                """
                insert into youtube_transcript_segments (
                  track_id,
                  segment_index,
                  start_seconds,
                  duration_seconds,
                  end_seconds,
                  text,
                  raw_json
                )
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    track_id,
                    index,
                    float(segment["start"]),
                    float(segment["duration"]),
                    float(segment["end"]),
                    str(segment["text"]),
                    json_text(raw_segment),
                ),
            )
    return track_id


def infer_scope(args: argparse.Namespace, source_name: str | None, video_ids: list[str]) -> tuple[str, str]:
    if video_ids:
        return "video", ",".join(video_ids)
    if source_name:
        return "source", source_name
    if args.all:
        return "all", ""
    return "missing", ""


def run(args: argparse.Namespace) -> dict[str, int]:
    languages = tuple(language.strip() for language in args.languages.split(",") if language.strip())
    if not languages:
        raise ValueError("--languages must include at least one language code")

    video_ids = [video_id.strip() for video_id in args.video_id if video_id.strip()]
    source_name = resolve_source_name(args.source, args.config)
    if not (video_ids or source_name or args.all):
        args.missing_only = True

    with sqlite3.connect(args.sqlite) as connection:
        connection.row_factory = sqlite3.Row
        ensure_transcript_schema(connection)
        targets = select_targets(
            connection,
            source_name=source_name,
            video_ids=video_ids,
            missing_only=args.missing_only and not args.refresh,
            limit=args.limit,
        )
        scope_type, scope_value = infer_scope(args, source_name, video_ids)

        if args.dry_run:
            print(f"Would fetch {len(targets)} transcript(s).")
            for target in targets[: args.preview_limit]:
                print(f"- {target.source_name}\t{target.video_id}\t{target.title}")
            return {"target_count": len(targets), "succeeded": 0, "failed": 0, "skipped": 0}

        job_id = create_job(
            connection,
            scope_type=scope_type,
            scope_value=scope_value,
            languages=languages,
        )
        connection.commit()

        stats = {"target_count": len(targets), "succeeded": 0, "failed": 0, "skipped": 0}
        consecutive_blocks = 0
        for index, target in enumerate(targets, start=1):
            try:
                transcript = fetch_transcript(target.video_id, languages)
                fetched_at = now_iso()
                transcript_hash = content_hash(transcript.raw_segments)
                blob_upload = None
                if args.storage in ("blob", "both"):
                    blob_upload = upload_transcript_blobs(
                        target=target,
                        transcript=transcript,
                        content_hash=transcript_hash,
                        fetched_at=fetched_at,
                        prefix=args.blob_prefix,
                        access=args.blob_access,
                    )
                track_id = upsert_transcript_track(
                    connection,
                    target=target,
                    transcript=transcript,
                    fetched_at=fetched_at,
                    storage=args.storage,
                    blob_upload=blob_upload,
                )
                record_attempt(
                    connection,
                    job_id=job_id,
                    target=target,
                    languages=languages,
                    status="succeeded",
                    metadata={
                        "track_id": track_id,
                        "language_code": transcript.language_code,
                        "is_generated": transcript.is_generated,
                        "segment_count": len(transcript.segments),
                        "storage": args.storage,
                        "raw_blob_path": blob_upload.raw.pathname if blob_upload else "",
                        "segments_blob_path": blob_upload.segments.pathname if blob_upload else "",
                    },
                )
                connection.commit()
                stats["succeeded"] += 1
                consecutive_blocks = 0
                print(
                    f"Fetched {target.video_id}: {transcript.language_code} "
                    f"segments={len(transcript.segments)} storage={args.storage}"
                )
            except Exception as exc:  # noqa: BLE001 - transcript availability varies by video.
                error_type = "youtube_block" if is_youtube_block_error(exc) else exc.__class__.__name__
                record_attempt(
                    connection,
                    job_id=job_id,
                    target=target,
                    languages=languages,
                    status="failed",
                    error_type=error_type,
                    error_message=str(exc),
                )
                connection.commit()
                stats["failed"] += 1
                print(f"Skipped transcript {target.video_id}: {exc}")
                if error_type == "youtube_block":
                    consecutive_blocks += 1
                    if (
                        args.max_consecutive_blocks > 0
                        and consecutive_blocks >= args.max_consecutive_blocks
                    ):
                        print(
                            "Stopping transcript fetch after "
                            f"{consecutive_blocks} consecutive YouTube block errors.",
                            flush=True,
                        )
                        break
                else:
                    consecutive_blocks = 0

            has_more = index < len(targets)
            if args.request_delay > 0 and has_more:
                print(f"Waiting {args.request_delay:g}s before the next transcript request...")
                time.sleep(args.request_delay)

        status = "succeeded" if stats["failed"] == 0 else "completed_with_failures"
        finish_job(connection, job_id, status, stats)
        connection.commit()
        return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube transcripts through the existing Webshare/youtube_transcript_api path."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", help="Source key from data/sources/youtube_sources.json or sources.name.")
    parser.add_argument("--video-id", action="append", default=[], help="YouTube video id. Repeatable.")
    parser.add_argument("--all", action="store_true", help="Fetch across every collected youtube_videos row.")
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Only fetch videos with no stored transcript track.",
    )
    parser.add_argument("--refresh", action="store_true", help="Fetch even when a transcript track exists.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--languages", default=",".join(DEFAULT_LANGUAGES))
    parser.add_argument(
        "--storage",
        choices=("blob", "sqlite", "both"),
        default=DEFAULT_STORAGE,
        help="Where to store transcript payloads. Default stores raw/segments in Vercel Blob and metadata in SQLite.",
    )
    parser.add_argument(
        "--blob-prefix",
        default=DEFAULT_BLOB_PREFIX,
        help="Vercel Blob pathname prefix for transcript archive objects.",
    )
    parser.add_argument(
        "--blob-access",
        choices=("private", "public"),
        default=DEFAULT_BLOB_ACCESS,
        help="Vercel Blob access mode. Tastyroad transcript archives should normally stay private.",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS,
        help="Seconds to wait between transcript requests.",
    )
    parser.add_argument(
        "--max-consecutive-blocks",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS,
        help="Stop after this many consecutive YouTube block errors. Use 0 to disable.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview-limit", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stats = run(args)
    print(json_text(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
