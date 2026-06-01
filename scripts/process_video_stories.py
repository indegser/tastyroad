#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collect_youtube import DEFAULT_SQLITE
from pipeline_schema import ensure_pipeline_schema


DEFAULT_LANGUAGES = ("ko", "en")
DEFAULT_INPUT = Path("data/story_reviews/video_story_reviews.json")


@dataclass(frozen=True)
class TranscriptPayload:
    language_code: str
    language: str
    is_generated: bool
    segments: list[dict[str, Any]]
    text: str


@dataclass(frozen=True)
class StoryProcessResult:
    fetched_transcript_count: int
    applied_review_count: int


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_transcript(video_id: str, languages: tuple[str, ...]) -> TranscriptPayload:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    transcript = transcript_list.find_transcript(list(languages))
    fetched = transcript.fetch()
    segments = normalize_segments(fetched)
    text = " ".join(segment["text"] for segment in segments).strip()
    return TranscriptPayload(
        language_code=str(transcript.language_code),
        language=str(transcript.language),
        is_generated=bool(transcript.is_generated),
        segments=segments,
        text=text,
    )


def normalize_segments(fetched: Any) -> list[dict[str, Any]]:
    if hasattr(fetched, "to_raw_data"):
        raw_segments = fetched.to_raw_data()
    else:
        raw_segments = fetched

    segments: list[dict[str, Any]] = []
    for segment in raw_segments:
        if hasattr(segment, "__dict__") and not isinstance(segment, dict):
            segment = segment.__dict__
        text = " ".join(str(segment.get("text", "")).replace("\n", " ").split())
        if not text:
            continue
        segments.append(
            {
                "text": text,
                "start": float(segment.get("start", 0)),
                "duration": float(segment.get("duration", 0)),
            }
        )
    return segments


def reviewed_restaurant_rows(
    connection: sqlite3.Connection,
    *,
    video_id: str | None = None,
    missing_transcript_only: bool = False,
) -> list[sqlite3.Row]:
    sql = """
        select
          v.video_id,
          v.source,
          v.title,
          v.reviewed_restaurant_names
        from video_pipeline_status v
        left join video_transcripts t on t.external_id = v.video_id
        where v.review_decision = 'restaurant_intro'
    """
    params: list[Any] = []
    if video_id:
        sql += " and v.video_id = ?"
        params.append(video_id)
    if missing_transcript_only:
        sql += " and t.external_id is null"
    sql += " order by v.published_at desc, v.mention_candidate_id desc"
    return list(connection.execute(sql, params).fetchall())


def upsert_transcript(
    connection: sqlite3.Connection,
    video_id: str,
    transcript: TranscriptPayload,
    fetched_at: str,
) -> None:
    connection.execute(
        """
        insert into video_transcripts (
          external_id,
          language_code,
          language,
          is_generated,
          transcript_json,
          transcript_text,
          fetched_at
        )
        values (?, ?, ?, ?, ?, ?, ?)
        on conflict(external_id) do update set
          language_code = excluded.language_code,
          language = excluded.language,
          is_generated = excluded.is_generated,
          transcript_json = excluded.transcript_json,
          transcript_text = excluded.transcript_text,
          fetched_at = excluded.fetched_at
        """,
        (
            video_id,
            transcript.language_code,
            transcript.language,
            1 if transcript.is_generated else 0,
            json.dumps(transcript.segments, ensure_ascii=False),
            transcript.text,
            fetched_at,
        ),
    )


def fetch_missing_transcripts(
    connection: sqlite3.Connection,
    *,
    languages: tuple[str, ...],
    video_id: str | None = None,
    refresh: bool = False,
) -> int:
    rows = reviewed_restaurant_rows(
        connection,
        video_id=video_id,
        missing_transcript_only=not refresh,
    )
    count = 0
    for row in rows:
        current_video_id = str(row["video_id"])
        try:
            transcript = fetch_transcript(current_video_id, languages)
        except Exception as exc:  # noqa: BLE001 - transcript availability varies by video.
            print(f"Skipped transcript {current_video_id}: {exc}")
            continue
        upsert_transcript(connection, current_video_id, transcript, now_iso())
        count += 1
    return count


def load_story_review_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("reviews") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError(f"{path} must contain a reviews list")
    return [validate_story_review_item(item, path) for item in items]


def validate_story_review_item(item: Any, path: Path) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"{path} contains a non-object review item")
    required = ("video_id", "story_hook", "story_intro", "tasting_flow")
    missing = [key for key in required if not str(item.get(key, "")).strip()]
    if missing:
        video_id = item.get("video_id", "<unknown>")
        raise ValueError(f"{path} review {video_id} missing required fields: {', '.join(missing)}")
    evidence = item.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError(f"{path} review {item['video_id']} evidence must be an object")
    return item


def apply_story_reviews(
    connection: sqlite3.Connection,
    input_path: Path,
    *,
    video_id: str | None = None,
) -> int:
    items = load_story_review_items(input_path)
    if video_id:
        items = [item for item in items if str(item["video_id"]) == video_id]

    count = 0
    for item in items:
        current_video_id = str(item["video_id"])
        exists = connection.execute(
            "select 1 from mention_candidates where external_id = ?",
            (current_video_id,),
        ).fetchone()
        if exists is None:
            raise RuntimeError(f"No mention candidate found for video_id={current_video_id}")
        connection.execute(
            """
            insert into video_story_reviews (
              external_id,
              story_intro,
              tasting_flow,
              story_hook,
              reviewer,
              evidence_json,
              generated_at
            )
            values (?, ?, ?, ?, ?, ?, ?)
            on conflict(external_id) do update set
              story_intro = excluded.story_intro,
              tasting_flow = excluded.tasting_flow,
              story_hook = excluded.story_hook,
              reviewer = excluded.reviewer,
              evidence_json = excluded.evidence_json,
              generated_at = excluded.generated_at
            """,
            (
                current_video_id,
                str(item["story_intro"]).strip(),
                str(item["tasting_flow"]).strip(),
                str(item["story_hook"]).strip(),
                str(item.get("reviewer") or "codex"),
                json.dumps(item.get("evidence", {}), ensure_ascii=False),
                str(item.get("generated_at") or now_iso()),
            ),
        )
        count += 1
    return count


def missing_story_review_rows(connection: sqlite3.Connection, *, limit: int | None = None) -> list[sqlite3.Row]:
    sql = """
        select
          v.video_id,
          v.source,
          v.title,
          v.reviewed_restaurant_names,
          length(t.transcript_text) as transcript_length
        from video_pipeline_status v
        left join video_transcripts t on t.external_id = v.video_id
        left join video_story_reviews sr on sr.external_id = v.video_id
        where v.review_decision = 'restaurant_intro'
          and sr.external_id is null
        order by v.published_at desc, v.mention_candidate_id desc
    """
    params: tuple[Any, ...] = ()
    if limit is not None:
        sql += " limit ?"
        params = (limit,)
    return list(connection.execute(sql, params).fetchall())


def process_stories(
    sqlite_path: Path,
    *,
    input_path: Path = DEFAULT_INPUT,
    languages: tuple[str, ...] = DEFAULT_LANGUAGES,
    video_id: str | None = None,
    refresh: bool = False,
    fetch_only: bool = False,
    apply_only: bool = False,
) -> StoryProcessResult:
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        ensure_pipeline_schema(connection)
        fetched_count = 0
        if not apply_only:
            fetched_count = fetch_missing_transcripts(
                connection,
                languages=languages,
                video_id=video_id,
                refresh=refresh,
            )
        applied_count = 0
        if not fetch_only:
            applied_count = apply_story_reviews(connection, input_path, video_id=video_id)
        return StoryProcessResult(
            fetched_transcript_count=fetched_count,
            applied_review_count=applied_count,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube transcripts and apply Codex-authored story reviews."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--video-id", help="Process only one video id.")
    parser.add_argument("--refresh", action="store_true", help="Refresh already stored transcripts.")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch transcripts; do not apply story reviews.")
    parser.add_argument("--apply-only", action="store_true", help="Only apply story reviews; do not fetch transcripts.")
    parser.add_argument("--list-missing", action="store_true", help="List restaurant videos still missing Codex story reviews.")
    parser.add_argument("--limit", type=int, default=20, help="Limit for --list-missing output.")
    parser.add_argument(
        "--languages",
        default="ko,en",
        help="Comma-separated transcript language preference list. Default: ko,en",
    )
    args = parser.parse_args()

    languages = tuple(item.strip() for item in args.languages.split(",") if item.strip())
    with sqlite3.connect(args.sqlite) as connection:
        connection.row_factory = sqlite3.Row
        ensure_pipeline_schema(connection)
        if args.list_missing:
            for row in missing_story_review_rows(connection, limit=args.limit):
                print(
                    f"{row['video_id']}\t{row['source']}\t{row['title']}\t"
                    f"transcript_length={row['transcript_length'] or 0}"
                )
            return 0

    result = process_stories(
        args.sqlite,
        input_path=args.input,
        languages=languages or DEFAULT_LANGUAGES,
        video_id=args.video_id,
        refresh=args.refresh,
        fetch_only=args.fetch_only,
        apply_only=args.apply_only,
    )
    print(f"Fetched transcripts: {result.fetched_transcript_count}")
    print(f"Applied Codex story reviews: {result.applied_review_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
