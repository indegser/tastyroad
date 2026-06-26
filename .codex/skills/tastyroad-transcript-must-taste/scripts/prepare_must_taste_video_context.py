#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from must_taste_schema import DEFAULT_SQLITE


CHUNK_SIZE = 80
CHUNK_OVERLAP = 8
DEFAULT_MAX_BLOCK_CHARS = 420
DEFAULT_MAX_BLOCK_SEGMENTS = 16
DEFAULT_GAP_SECONDS = 2.5

TRANSCRIPT_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "tastyroad-youtube-transcript-ingest"
    / "scripts"
)
sys.path.insert(0, str(TRANSCRIPT_SCRIPTS))

try:
    from transcript_blob_store import load_segments_blob
except ImportError as exc:  # pragma: no cover - defensive when skill layout changes.
    raise SystemExit(
        "Could not import transcript helpers from tastyroad-youtube-transcript-ingest."
    ) from exc


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a video-level must-taste context with compact transcript blocks. "
            "This script only reads SQLite/transcript storage and writes work artifacts."
        )
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-block-chars", type=positive_int, default=DEFAULT_MAX_BLOCK_CHARS)
    parser.add_argument(
        "--max-block-segments",
        type=positive_int,
        default=DEFAULT_MAX_BLOCK_SEGMENTS,
    )
    parser.add_argument("--gap-seconds", type=non_negative_float, default=DEFAULT_GAP_SECONDS)
    return parser.parse_args()


def timestamp_label(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def default_output_dir(video_id: str) -> Path:
    return Path("data/work/must_taste_video") / video_id


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_context_hash(
    video_id: str,
    transcript_track_id: int,
    segments: list[dict[str, Any]],
) -> str:
    payload = {
        "video_id": video_id,
        "transcript_track_id": transcript_track_id,
        "segments": [
            {
                "segment_index": int(segment["segment_index"]),
                "start_seconds": float(segment["start_seconds"]),
                "text": str(segment["text"]),
            }
            for segment in segments
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def chunk_count(segment_count: int) -> int:
    if segment_count <= 0:
        return 0
    chunks = 0
    start = 0
    while start < segment_count:
        end = min(segment_count, start + CHUNK_SIZE)
        chunks += 1
        if end == segment_count:
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def load_video_context(connection: sqlite3.Connection, video_id: str) -> dict[str, Any]:
    row = connection.execute(
        """
        select
          pt.id as transcript_track_id,
          pt.youtube_video_id,
          pt.video_id,
          pt.source_name,
          pt.language_code,
          pt.language,
          pt.is_generated,
          pt.provider,
          pt.segment_count,
          pt.storage_provider,
          pt.segments_blob_path,
          pt.blob_uploaded_at,
          pt.fetched_at,
          y.title,
          y.url,
          y.published_at
        from preferred_youtube_transcripts pt
        join youtube_videos y on y.id = pt.youtube_video_id
        where pt.video_id = ?
        """,
        (video_id,),
    ).fetchone()
    if row is None:
        raise SystemExit(
            f"No preferred transcript found for {video_id}. "
            "Run $tastyroad-youtube-transcript-ingest first."
        )

    restaurants = [
        {
            "restaurant_id": int(restaurant["restaurant_id"]),
            "display_name": str(restaurant["display_name"]),
            "canonical_name": str(restaurant["canonical_name"]),
            "address": str(restaurant["address"]),
            "naver_map_id": str(restaurant["naver_map_id"]),
            "mapping_status": str(restaurant["status"]),
        }
        for restaurant in connection.execute(
            """
            select
              r.id as restaurant_id,
              r.display_name,
              r.canonical_name,
              r.address,
              r.naver_map_id,
              yvr.status
            from youtube_video_restaurants yvr
            join restaurants r on r.id = yvr.restaurant_id
            where yvr.youtube_video_id = ?
              and yvr.status in ('verified', 'metadata_verified')
              and coalesce(r.naver_map_id, '') != ''
            order by r.display_name
            """,
            (int(row["youtube_video_id"]),),
        ).fetchall()
    ]
    if not restaurants:
        raise SystemExit(f"No verified restaurant mappings found for {video_id}.")

    segments = [
        {
            "segment_index": int(segment["segment_index"]),
            "timestamp": timestamp_label(float(segment["start_seconds"])),
            "start_seconds": float(segment["start_seconds"]),
            "end_seconds": float(segment["end_seconds"]),
            "duration_seconds": float(segment["duration_seconds"]),
            "text": str(segment["text"]),
        }
        for segment in connection.execute(
            """
            select segment_index, start_seconds, end_seconds, duration_seconds, text
            from youtube_transcript_segments
            where track_id = ?
            order by segment_index
            """,
            (int(row["transcript_track_id"]),),
        ).fetchall()
    ]

    if not segments and row["segments_blob_path"]:
        segments = [
            {
                "segment_index": int(segment["segment_index"]),
                "timestamp": timestamp_label(float(segment["start_seconds"])),
                "start_seconds": float(segment["start_seconds"]),
                "end_seconds": float(segment["end_seconds"]),
                "duration_seconds": float(segment["duration_seconds"]),
                "text": str(segment["text"]),
            }
            for segment in load_segments_blob(
                str(row["segments_blob_path"]),
                storage_provider=str(row["storage_provider"]),
            )
        ]

    if not segments:
        raise SystemExit(f"Preferred transcript for {video_id} has no timed segments.")

    transcript_track_id = int(row["transcript_track_id"])
    return {
        "context_hash": make_context_hash(str(row["video_id"]), transcript_track_id, segments),
        "video": {
            "youtube_video_id": int(row["youtube_video_id"]),
            "video_id": str(row["video_id"]),
            "source_name": str(row["source_name"]),
            "title": str(row["title"]),
            "url": str(row["url"]),
            "published_at": str(row["published_at"]),
        },
        "restaurants": restaurants,
        "transcript": {
            "track_id": transcript_track_id,
            "language_code": str(row["language_code"]),
            "language": str(row["language"]),
            "is_generated": bool(row["is_generated"]),
            "provider": str(row["provider"]),
            "storage_provider": str(row["storage_provider"]),
            "segments_blob_path": str(row["segments_blob_path"]),
            "blob_uploaded_at": str(row["blob_uploaded_at"]),
            "segment_count": int(row["segment_count"]),
            "fetched_at": str(row["fetched_at"]),
            "segments": segments,
        },
    }


def build_blocks(
    segments: list[dict[str, Any]],
    *,
    max_block_chars: int,
    max_block_segments: int,
    gap_seconds: float,
) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    def flush() -> None:
        if not current:
            return
        block_id = f"block_{len(blocks) + 1:04d}"
        text = " ".join(str(segment["text"]).strip() for segment in current if str(segment["text"]).strip())
        blocks.append(
            {
                "block_id": block_id,
                "segment_index_start": int(current[0]["segment_index"]),
                "segment_index_end": int(current[-1]["segment_index"]),
                "timestamp_start": str(current[0]["timestamp"]),
                "timestamp_end": str(current[-1]["timestamp"]),
                "start_seconds": float(current[0]["start_seconds"]),
                "end_seconds": float(current[-1]["end_seconds"]),
                "segment_count": len(current),
                "text": text,
                "segment_indices": [int(segment["segment_index"]) for segment in current],
            }
        )
        current.clear()

    for segment in segments:
        if current:
            previous_end = float(current[-1]["end_seconds"])
            gap = float(segment["start_seconds"]) - previous_end
            current_text_len = sum(len(str(entry["text"])) for entry in current)
            next_len = current_text_len + len(str(segment["text"])) + 1
            if (
                gap > gap_seconds
                or len(current) >= max_block_segments
                or next_len > max_block_chars
            ):
                flush()
        current.append(segment)
    flush()
    return blocks


def write_task(
    path: Path,
    *,
    context_path: Path,
    blocks_path: Path,
    segment_lookup_path: Path,
    restaurant_windows_path: Path,
    shared_events_path: Path,
    review_prompt_path: Path,
) -> None:
    path.write_text(
        "\n".join(
            [
                "# Video-Level Must-Taste Scout Task",
                "",
                f"- Read `{context_path}` and `{blocks_path}` first.",
                f"- Use `{segment_lookup_path}` only when exact segment text is needed.",
                f"- Write restaurant boundaries to `{restaurant_windows_path}`.",
                f"- Write shared video candidate-finding events to `{shared_events_path}`.",
                f"- Use `{review_prompt_path}` when reviewing candidates; one model call may emit both `evidence_skeptic` and `visitor_judge` review objects.",
                "",
                "Workflow:",
                "",
                "1. Identify the transcript range for each restaurant in `context.restaurants` using block timestamps, restaurant names, menu mentions, arrivals, ordering, eating, and transition language.",
                "2. Keep boundaries conservative. If a transition is ambiguous, include overlap buffers and explain the uncertainty in the window note.",
                "3. Run candidate finding once across the video blocks. Each event must cite `block_id` plus exact `segment_index` after checking the segment lookup.",
                "4. Split events into normal pair-level `data/work/must_taste/<video_id>/<restaurant_id>/attention_events.jsonl` files only when the event belongs to that restaurant window.",
                "5. Finish every pair with the existing candidate aggregation, candidate reviews, arbiter result, and `apply_must_taste_result.py --dry-run` validation.",
                "",
                "Do not write SQLite from this video-level workflow. Final applies remain single-process through the batch apply script.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_review_prompt(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Combined Candidate Review Prompt",
                "",
                "For each candidate, emit two review objects in one JSON response:",
                "",
                "- `evidence_skeptic`: transcript grounding, overclaiming risk, wrong-restaurant risk, and whether evidence is stronger than mention/order/eating alone.",
                "- `visitor_judge`: whether the menu and quote would help a visitor choose this restaurant over another one.",
                "",
                "Each review object must still match the existing `candidate_reviews.json` contract: `candidate_id`, `reviewer`, `verdict`, `score`, `drivers`, `reason`, `risk`, and `cited_event_ids`.",
                "",
                "Use `verdict: fail` for weak mentions, ordinary ordering, flat ingredient labels, or events outside the restaurant window. Use `borderline` only when the evidence is real but probably not enough for a final item.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def prepare(
    sqlite_path: Path,
    video_id: str,
    output_dir: Path | None,
    max_block_chars: int,
    max_block_segments: int,
    gap_seconds: float,
) -> None:
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        context = load_video_context(connection, video_id)

    target_dir = output_dir or default_output_dir(video_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    context_path = target_dir / "video_context.json"
    blocks_path = target_dir / "blocks.json"
    segment_lookup_path = target_dir / "segment_lookup.json"
    restaurant_windows_path = target_dir / "restaurant_windows.json"
    shared_events_path = target_dir / "video_attention_events.jsonl"
    task_path = target_dir / "task.md"
    review_prompt_path = target_dir / "combined_candidate_review.md"

    segments = context["transcript"].pop("segments")
    blocks = build_blocks(
        segments,
        max_block_chars=max_block_chars,
        max_block_segments=max_block_segments,
        gap_seconds=gap_seconds,
    )
    context["artifacts"] = {
        "blocks_path": str(blocks_path),
        "segment_lookup_path": str(segment_lookup_path),
        "restaurant_windows_path": str(restaurant_windows_path),
        "shared_events_path": str(shared_events_path),
        "task_path": str(task_path),
        "combined_candidate_review_prompt_path": str(review_prompt_path),
    }
    context["compression"] = {
        "segment_count": len(segments),
        "block_count": len(blocks),
        "pairwise_chunk_count_if_run_per_restaurant": chunk_count(len(segments))
        * len(context["restaurants"]),
        "video_once_chunk_count": chunk_count(len(segments)),
        "max_block_chars": max_block_chars,
        "max_block_segments": max_block_segments,
        "gap_seconds": gap_seconds,
    }

    write_json(context_path, context)
    write_json(
        blocks_path,
        {
            "video_id": context["video"]["video_id"],
            "transcript_track_id": context["transcript"]["track_id"],
            "context_hash": context["context_hash"],
            "block_count": len(blocks),
            "blocks": blocks,
        },
    )
    write_json(
        segment_lookup_path,
        {
            "video_id": context["video"]["video_id"],
            "transcript_track_id": context["transcript"]["track_id"],
            "context_hash": context["context_hash"],
            "segments": segments,
        },
    )
    write_json(
        restaurant_windows_path,
        {
            "video_id": context["video"]["video_id"],
            "transcript_track_id": context["transcript"]["track_id"],
            "context_hash": context["context_hash"],
            "windows": [],
            "status": "pending_agent_boundary_review",
        },
    )
    shared_events_path.write_text("", encoding="utf-8")
    write_task(
        task_path,
        context_path=context_path,
        blocks_path=blocks_path,
        segment_lookup_path=segment_lookup_path,
        restaurant_windows_path=restaurant_windows_path,
        shared_events_path=shared_events_path,
        review_prompt_path=review_prompt_path,
    )
    write_review_prompt(review_prompt_path)

    print(f"video_id={context['video']['video_id']}")
    print(f"restaurant_count={len(context['restaurants'])}")
    print(f"segment_count={len(segments)}")
    print(f"block_count={len(blocks)}")
    print(
        "pairwise_chunk_count_if_run_per_restaurant="
        f"{context['compression']['pairwise_chunk_count_if_run_per_restaurant']}"
    )
    print(f"video_once_chunk_count={context['compression']['video_once_chunk_count']}")
    print(f"output_dir={target_dir}")


def main() -> int:
    args = parse_args()
    prepare(
        args.sqlite,
        args.video_id,
        args.output_dir,
        args.max_block_chars,
        args.max_block_segments,
        args.gap_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
