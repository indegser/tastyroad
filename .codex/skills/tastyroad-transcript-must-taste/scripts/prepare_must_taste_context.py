#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from must_taste_schema import DEFAULT_SQLITE, ensure_must_taste_schema


CHUNK_SIZE = 80
CHUNK_OVERLAP = 8

TRANSCRIPT_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "tastyroad-youtube-transcript-ingest"
    / "scripts"
)
sys.path.insert(0, str(TRANSCRIPT_SCRIPTS))

try:
    from transcript_blob_store import load_segments_blob
    from transcript_schema import ensure_transcript_schema
except ImportError as exc:  # pragma: no cover - defensive when skill layout changes.
    raise SystemExit(
        "Could not import transcript helpers from tastyroad-youtube-transcript-ingest."
    ) from exc


def timestamp_label(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def default_output_dir(video_id: str, restaurant_id: int) -> Path:
    return Path("data/work/must_taste") / video_id / str(restaurant_id)


def make_context_hash(
    video_id: str,
    restaurant_id: int,
    transcript_track_id: int,
    segments: list[dict[str, Any]],
) -> str:
    payload = {
        "video_id": video_id,
        "restaurant_id": restaurant_id,
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


def build_chunks(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    start = 0
    while start < len(segments):
        end = min(len(segments), start + CHUNK_SIZE)
        chunk_segments = segments[start:end]
        chunk_id = f"chunk_{len(chunks) + 1:03d}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "segment_index_start": int(chunk_segments[0]["segment_index"]),
                "segment_index_end": int(chunk_segments[-1]["segment_index"]),
                "start_seconds": float(chunk_segments[0]["start_seconds"]),
                "end_seconds": float(chunk_segments[-1]["end_seconds"]),
                "line_count": len(chunk_segments),
                "lines": [
                    {
                        "segment_index": int(segment["segment_index"]),
                        "timestamp": str(segment["timestamp"]),
                        "start_seconds": float(segment["start_seconds"]),
                        "text": str(segment["text"]),
                    }
                    for segment in chunk_segments
                ],
            }
        )
        if end == len(segments):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def build_coverage(
    video_id: str,
    restaurant_id: int,
    transcript_track_id: int,
    context_hash: str,
    segments: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    covered = {
        int(line["segment_index"])
        for chunk in chunks
        for line in chunk["lines"]
    }
    expected = {int(segment["segment_index"]) for segment in segments}
    return {
        "video_id": video_id,
        "restaurant_id": restaurant_id,
        "transcript_track_id": transcript_track_id,
        "context_hash": context_hash,
        "segment_count": len(segments),
        "chunk_count": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "segment_index_start": int(segments[0]["segment_index"]),
        "segment_index_end": int(segments[-1]["segment_index"]),
        "all_segments_covered": covered == expected,
        "missing_segment_indices": sorted(expected - covered),
        "chunk_ranges": [
            {
                "chunk_id": str(chunk["chunk_id"]),
                "segment_index_start": int(chunk["segment_index_start"]),
                "segment_index_end": int(chunk["segment_index_end"]),
            }
            for chunk in chunks
        ],
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_agent_passes(
    pass_dir: Path,
    context_path: Path,
    chunks_path: Path,
    attention_events_path: Path,
    candidates_path: Path,
    reviews_path: Path,
    result_path: Path,
) -> None:
    pass_dir.mkdir(parents=True, exist_ok=True)
    (pass_dir / "01_attention_scout.md").write_text(
        "\n".join(
            [
                "# Pass 1 - Parallel Attention Scout",
                "",
                f"- Read `{context_path}` and `{chunks_path}`.",
                f"- Write JSONL lines to `{attention_events_path}`.",
                "- Split chunks across scout agents when possible; every chunk must be inspected.",
                "- Find attention events, not final menu picks.",
                "- Valid event_type values: explicit_recommendation, repeat_mention, repeat_visit, differentiator, strong_praise, signature_menu, unique_preparation_with_praise, host_must_order, ordering_advice.",
                "- Do not emit neutral mentions, ordinary ordering, or eating-only lines unless connected to a stronger signal.",
                "- Each JSONL line must include video_id, restaurant_id, transcript_track_id, context_hash, event_id, chunk_id, candidate_id, menu_item, event_type, attention_score, segment_index, timestamp, start_seconds, text, restaurant_scope_note, and note.",
                "- Copy text exactly from the transcript line.",
                "- restaurant_scope_note must briefly explain why this segment belongs to the target restaurant's part of the video.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (pass_dir / "02_candidate_aggregator.md").write_text(
        "\n".join(
            [
                "# Pass 2 - Candidate Aggregator",
                "",
                f"- Read `{attention_events_path}`.",
                f"- Write `{candidates_path}`.",
                "- The root object must include video_id, restaurant_id, transcript_track_id, context_hash, and candidates.",
                "- Merge aliases and repeated mentions into menu candidates.",
                "- Preserve event_ids for every candidate.",
                "- Every attention event must be represented by a candidate with the same candidate_id.",
                "- Consider both intensity and repetition: repeated weak mentions alone should not outrank one strong differentiator.",
                "- Each candidate needs candidate_id, menu_item, aliases, event_ids, mention_count, attention_score, signals, summary, and weakness.",
                "- Include weak but plausible candidates so the arbiter can explicitly reject them later.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (pass_dir / "03_candidate_reviews.md").write_text(
        "\n".join(
            [
                "# Pass 3 - Parallel Candidate Reviews",
                "",
                f"- Read `{context_path}`, `{attention_events_path}`, and `{candidates_path}`.",
                f"- Write `{reviews_path}`.",
                "- The root object must include video_id, restaurant_id, transcript_track_id, context_hash, and reviews.",
                "- Run at least two independent reviewer perspectives per candidate: evidence_skeptic and visitor_judge.",
                "- evidence_skeptic checks transcript grounding, overclaiming, and whether evidence is strong enough.",
                "- visitor_judge checks whether this menu would help a real visitor choose this restaurant.",
                "- Each review needs candidate_id, reviewer, verdict, score, drivers, reason, risk, and cited_event_ids.",
                "- cited_event_ids must point to attention events for the same candidate.",
                "- Mark verdict as fail for flat feature labels, weak mentions, or merely interesting sides that would not drive a visit.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (pass_dir / "04_arbiter_result.md").write_text(
        "\n".join(
            [
                "# Pass 4 - Sequential Arbiter",
                "",
                f"- Read `{context_path}`, `{attention_events_path}`, `{candidates_path}`, and `{reviews_path}`.",
                f"- Write final `{result_path}`.",
                "- Select zero to three candidates only after coverage, event, candidate, and review artifacts exist.",
                "- Include pipeline paths in result.pipeline.",
                "- Include rejected_candidates for every candidate that is not selected.",
                "- Final items must include candidate_id, reason, quality, review, evidence, and optional supporting_evidence.",
                "- reason must be a short direct subtitle quote copied from evidence or supporting_evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def resolve_restaurant(
    connection: sqlite3.Connection,
    youtube_video_id: int,
    restaurant_id: int | None,
    restaurant_name: str,
) -> sqlite3.Row:
    params: list[Any] = [youtube_video_id]
    where_clause = ""
    if restaurant_id is not None:
        where_clause = "and r.id = ?"
        params.append(restaurant_id)
    elif restaurant_name:
        where_clause = "and (r.display_name = ? or r.canonical_name = ?)"
        params.extend([restaurant_name, restaurant_name])

    rows = connection.execute(
        f"""
        select
          r.id,
          r.display_name,
          r.canonical_name,
          r.address,
          r.naver_map_id
        from restaurants r
        join youtube_video_restaurants m on m.restaurant_id = r.id
        where m.youtube_video_id = ?
          and m.status in ('verified', 'metadata_verified')
          {where_clause}
        order by r.display_name
        """,
        params,
    ).fetchall()

    if len(rows) == 1:
        return rows[0]

    if not rows and (restaurant_id is not None or restaurant_name):
        raise SystemExit("No matching verified restaurant mapping for this video.")

    choices = "\n".join(
        f"- {row['id']}: {row['display_name']} ({row['address']})" for row in rows
    )
    raise SystemExit(
        "This video has multiple verified restaurant mappings. "
        "Pass --restaurant-id or --restaurant-name.\n"
        f"{choices}"
    )


def load_context(
    sqlite_path: Path,
    video_id: str,
    restaurant_id: int | None,
    restaurant_name: str,
) -> dict[str, Any]:
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        ensure_transcript_schema(connection)
        ensure_must_taste_schema(connection)
        row = connection.execute(
            """
            select
              p.id as transcript_track_id,
              p.youtube_video_id,
              p.video_id,
              p.source_name,
              p.language_code,
              p.language,
              p.is_generated,
              p.provider,
              p.segment_count,
              p.storage_provider,
              p.segments_blob_path,
              p.blob_uploaded_at,
              p.fetched_at,
              y.title,
              y.url,
              y.published_at
            from preferred_youtube_transcripts p
            join youtube_videos y on y.id = p.youtube_video_id
            where p.video_id = ?
            """,
            (video_id,),
        ).fetchone()

        if row is None:
            raise SystemExit(
                f"No preferred transcript found for {video_id}. "
                "Run $tastyroad-youtube-transcript-ingest first."
            )

        restaurant = resolve_restaurant(
            connection,
            int(row["youtube_video_id"]),
            restaurant_id,
            restaurant_name,
        )

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
                (row["transcript_track_id"],),
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
    restaurant_id_value = int(restaurant["id"])
    context_hash = make_context_hash(
        str(row["video_id"]),
        restaurant_id_value,
        transcript_track_id,
        segments,
    )

    return {
        "context_hash": context_hash,
        "video": {
            "youtube_video_id": int(row["youtube_video_id"]),
            "video_id": str(row["video_id"]),
            "source_name": str(row["source_name"]),
            "title": str(row["title"]),
            "url": str(row["url"]),
            "published_at": str(row["published_at"]),
        },
        "restaurant": {
            "id": restaurant_id_value,
            "display_name": str(restaurant["display_name"]),
            "canonical_name": str(restaurant["canonical_name"]),
            "address": str(restaurant["address"]),
            "naver_map_id": str(restaurant["naver_map_id"]),
        },
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
        "output_contract": {
            "path": str(default_output_dir(video_id, int(restaurant["id"])) / "result.json"),
            "pipeline": {
                "coverage_path": str(default_output_dir(video_id, int(restaurant["id"])) / "coverage.json"),
                "chunks_path": str(default_output_dir(video_id, int(restaurant["id"])) / "chunks.json"),
                "attention_events_path": str(default_output_dir(video_id, int(restaurant["id"])) / "attention_events.jsonl"),
                "candidates_path": str(default_output_dir(video_id, int(restaurant["id"])) / "menu_candidates.json"),
                "reviews_path": str(default_output_dir(video_id, int(restaurant["id"])) / "candidate_reviews.json"),
            },
            "shape": {
                "video_id": video_id,
                "restaurant_id": int(restaurant["id"]),
                "context_hash": "context_hash_from_context",
                "pipeline": {
                    "coverage_path": "coverage.json",
                    "chunks_path": "chunks.json",
                    "attention_events_path": "attention_events.jsonl",
                    "candidates_path": "menu_candidates.json",
                    "reviews_path": "candidate_reviews.json",
                },
                "items": [
                    {
                        "rank": 1,
                        "candidate_id": "candidate_id_from_menu_candidates",
                        "menu_item": "자막에 등장한 메뉴명",
                        "reason": "상위권 감자튀김이다",
                        "quality": {
                            "score": 90,
                            "signals": ["strong_praise"],
                            "check": "감자 그 자체를 바삭하게 튀긴 상위권 감자튀김이라는 자막 근거",
                        },
                        "review": {
                            "score": 88,
                            "verdict": "pass",
                            "drivers": [
                                "would_pick_restaurant_for_this",
                                "strong_host_praise",
                            ],
                            "decision_reason": "버거집을 고르는 유저에게 사이드까지 상위권이라는 방문 이유가 됨",
                            "risk": "감자튀김만으로 방문할 정도인지 약하면 제외",
                        },
                        "evidence": {
                            "segment_index": 0,
                            "timestamp": "00:00",
                            "start_seconds": 0.0,
                            "text": "context.json의 해당 segment text를 그대로 복사",
                        },
                        "supporting_evidence": [],
                    }
                ],
                "rejected_candidates": [
                    {
                        "candidate_id": "candidate_id_from_menu_candidates",
                        "menu_item": "검토했지만 탈락한 메뉴명",
                        "reason": "방문 선택 이유로 약하거나 근거가 부족한 이유",
                    }
                ],
            },
        },
    }


def write_task(
    task_path: Path,
    context_path: Path,
    coverage_path: Path,
    chunks_path: Path,
    attention_events_path: Path,
    candidates_path: Path,
    reviews_path: Path,
    result_path: Path,
) -> None:
    task_path.write_text(
        "\n".join(
            [
                "# Must-Taste Recommendation Task",
                "",
                f"- Read `{context_path}`.",
                f"- Confirm whole-transcript coverage in `{coverage_path}`.",
                f"- Use chunks from `{chunks_path}` for parallel scout passes.",
                f"- Write attention events to `{attention_events_path}`.",
                f"- Aggregate menu candidates into `{candidates_path}`.",
                f"- Run evidence_skeptic and visitor_judge reviews into `{reviews_path}`.",
                f"- Write `{result_path}`.",
                "- Every artifact must carry the same video_id, restaurant_id, transcript_track_id, and context_hash.",
                "- Every attention event must be represented in menu_candidates with the same candidate_id.",
                "- Every attention event must include restaurant_scope_note for the target restaurant.",
                "- Every candidate review must cite attention event IDs for that candidate.",
                "- Select at most three menu items for the target restaurant only.",
                "- Do not fill three slots by default; fewer than three is correct when only fewer items pass the quality gate.",
                "- Final result must include pipeline paths, selected items, and rejected_candidates for every non-selected candidate.",
                "- Each item must be grounded in transcript segments.",
                "- Do not qualify an item from mention, order, or eating alone.",
                "- Require quality.score >= 80 and at least one quality signal: explicit_recommendation, repeat_visit, differentiator, strong_praise, signature_menu, unique_preparation_with_praise, or host_must_order.",
                "- Require review.score >= 82, review.verdict='pass', and at least one review driver: would_pick_restaurant_for_this, differentiated_from_common_versions, explicit_ordering_advice, strong_host_praise, or signature_or_specialty.",
                "- Review from a restaurant-selection user's perspective: would this menu and its transcript quote help someone pick this restaurant over another one?",
                "- Use the timestamp from the transcript segment where the item is ordered, eaten, praised, or recommended.",
                "- Do not use video title, description, map data, restaurant metadata, or prior story review prose as evidence.",
                "- Do not use transcript segments for another restaurant in the same video.",
                "- Do not invent a third item. Use fewer than three items, or an empty result with insufficient_evidence=true when nothing passes.",
                "- Keep each reason to one short direct subtitle quote with no newline.",
                "- The reason must be an exact substring of evidence.text or supporting_evidence[].text.",
                "- Do not over-trim the quote; include enough words from the same evidence line so the subject and claim remain understandable.",
                "- Do not coin slogans, correct ASR text, or add atmosphere, location, freshness, market, scenery, or other quality claims.",
                "",
                "Validate and apply with:",
                "",
                "```bash",
                "python3 .codex/skills/tastyroad-transcript-must-taste/scripts/apply_must_taste_result.py "
                f"--context {context_path} --result {result_path}",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def prepare(
    sqlite_path: Path,
    video_id: str,
    restaurant_id: int | None,
    restaurant_name: str,
    output_dir: Path | None,
) -> None:
    context = load_context(sqlite_path, video_id, restaurant_id, restaurant_name)
    target_dir = output_dir or default_output_dir(video_id, int(context["restaurant"]["id"]))
    target_dir.mkdir(parents=True, exist_ok=True)
    context_path = target_dir / "context.json"
    task_path = target_dir / "task.md"
    result_path = target_dir / "result.json"
    coverage_path = target_dir / "coverage.json"
    chunks_path = target_dir / "chunks.json"
    attention_events_path = target_dir / "attention_events.jsonl"
    candidates_path = target_dir / "menu_candidates.json"
    reviews_path = target_dir / "candidate_reviews.json"
    pass_dir = target_dir / "passes"

    context["output_contract"]["path"] = str(result_path)
    context["output_contract"]["pipeline"] = {
        "coverage_path": str(coverage_path),
        "chunks_path": str(chunks_path),
        "attention_events_path": str(attention_events_path),
        "candidates_path": str(candidates_path),
        "reviews_path": str(reviews_path),
    }
    context["output_contract"]["shape"]["pipeline"] = {
        "coverage_path": str(coverage_path),
        "chunks_path": str(chunks_path),
        "attention_events_path": str(attention_events_path),
        "candidates_path": str(candidates_path),
        "reviews_path": str(reviews_path),
    }
    chunks = build_chunks(context["transcript"]["segments"])
    coverage = build_coverage(
        context["video"]["video_id"],
        int(context["restaurant"]["id"]),
        int(context["transcript"]["track_id"]),
        str(context["context_hash"]),
        context["transcript"]["segments"],
        chunks,
    )
    write_json(coverage_path, coverage)
    write_json(
        chunks_path,
        {
            "video_id": context["video"]["video_id"],
            "restaurant_id": int(context["restaurant"]["id"]),
            "transcript_track_id": int(context["transcript"]["track_id"]),
            "context_hash": str(context["context_hash"]),
            "chunks": chunks,
        },
    )
    write_agent_passes(
        pass_dir,
        context_path,
        chunks_path,
        attention_events_path,
        candidates_path,
        reviews_path,
        result_path,
    )
    context_path.write_text(
        json.dumps(context, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_task(
        task_path,
        context_path,
        coverage_path,
        chunks_path,
        attention_events_path,
        candidates_path,
        reviews_path,
        result_path,
    )
    print(f"Wrote {coverage_path}")
    print(f"Wrote {chunks_path}")
    print(f"Wrote {pass_dir}")
    print(f"Wrote {context_path}")
    print(f"Wrote {task_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a timed transcript context for must-taste recommendation extraction."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--restaurant-id", type=int)
    parser.add_argument("--restaurant-name", default="")
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prepare(
        args.sqlite,
        args.video_id,
        args.restaurant_id,
        args.restaurant_name,
        args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
