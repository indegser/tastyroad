#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from must_taste_schema import DEFAULT_SQLITE


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


CHUNK_SIZE = 80
CHUNK_OVERLAP = 8
DEFAULT_WINDOW_RADIUS = 8
DEFAULT_OUTPUT = Path("data/work/must_taste/prefilter_benchmark.json")
SIGNAL_TERMS = [
    "추천",
    "또 갈",
    "또갈",
    "또 올",
    "또올",
    "또 오",
    "다시 오",
    "재방문",
    "무조건",
    "먹어야",
    "시켜야",
    "꼭",
    "맛있",
    "맛잇",
    "맛난",
    "맛도",
    "대박",
    "미쳤",
    "장난",
    "최고",
    "1등",
    "일등",
    "1티어",
    "상위권",
    "처음 먹",
    "처음 먹어",
    "처음이에",
    "다르",
    "차별",
    "특별",
    "시그니처",
    "대표",
    "잡내",
    "풍미",
    "고소",
    "꼬소",
    "바삭",
    "쫄깃",
    "녹아",
    "육즙",
    "기깔",
    "기똥",
    "끝내",
    "좋다",
    "좋아",
    "괜찮",
    "매력",
    "퀄리티",
    "유명",
    "먹어 봐",
    "먹어봐",
    "해 보세요",
    "해봐",
    "proud to recommend",
    "recommend",
    "delicious",
    "tasty",
    "best",
    "amazing",
    "crispy",
    "juicy",
    "love it",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark a low-cost transcript prefilter against stored must-taste rows. "
            "This script is read-only for SQLite and writes comparison artifacts only."
        )
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--source-name", default="성시경의 먹을텐데")
    parser.add_argument("--window-radius", type=int, default=DEFAULT_WINDOW_RADIUS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--max-examples", type=int, default=30)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def chunk_count(segment_count: int) -> int:
    if segment_count <= 0:
        return 0
    if segment_count <= CHUNK_SIZE:
        return 1
    step = CHUNK_SIZE - CHUNK_OVERLAP
    return 1 + math.ceil((segment_count - CHUNK_SIZE) / step)


def expand_indices(indices: set[int], segment_count: int, radius: int) -> set[int]:
    expanded: set[int] = set()
    for index in indices:
        start = max(0, index - radius)
        end = min(segment_count - 1, index + radius)
        expanded.update(range(start, end + 1))
    return expanded


def compact_ranges(indices: set[int]) -> list[dict[str, int]]:
    if not indices:
        return []
    sorted_indices = sorted(indices)
    ranges = []
    start = previous = sorted_indices[0]
    for index in sorted_indices[1:]:
        if index == previous + 1:
            previous = index
            continue
        ranges.append({"start": start, "end": previous, "count": previous - start + 1})
        start = previous = index
    ranges.append({"start": start, "end": previous, "count": previous - start + 1})
    return ranges


def source_scope(connection: sqlite3.Connection, source_name: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        select
          yv.id as youtube_pk,
          yv.video_id,
          yv.title,
          pt.id as transcript_track_id,
          pt.segment_count,
          count(yvr.restaurant_id) as restaurant_count
        from youtube_videos yv
        join sources s on s.id = yv.source_id
        join preferred_youtube_transcripts pt on pt.youtube_video_id = yv.id
        join youtube_video_restaurants yvr on yvr.youtube_video_id = yv.id
        join restaurants r on r.id = yvr.restaurant_id
        where s.name = ?
          and yvr.status in ('verified', 'metadata_verified')
          and coalesce(r.naver_map_id, '') != ''
        group by yv.id, yv.video_id, yv.title, pt.id, pt.segment_count
        order by yv.published_at desc, yv.id desc
        """,
        (source_name,),
    ).fetchall()
    return [dict(row) for row in rows]


def gold_rows(connection: sqlite3.Connection, source_name: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        select
          i.restaurant_id,
          i.youtube_video_id,
          i.video_id,
          i.rank,
          i.item_name,
          i.reason,
          i.repaired_reason,
          i.segment_index,
          i.start_seconds,
          i.timestamp_label,
          i.evidence_text,
          yv.title,
          pt.id as transcript_track_id,
          pt.segment_count
        from video_must_taste_items i
        join youtube_videos yv on yv.id = i.youtube_video_id
        join sources s on s.id = yv.source_id
        join preferred_youtube_transcripts pt on pt.youtube_video_id = yv.id
        where s.name = ?
        order by yv.published_at desc, yv.id desc, i.restaurant_id, i.rank
        """,
        (source_name,),
    ).fetchall()
    return [dict(row) for row in rows]


def transcript_track_rows(
    connection: sqlite3.Connection,
    track_ids: set[int],
) -> dict[int, sqlite3.Row]:
    if not track_ids:
        return {}
    placeholders = ",".join("?" for _ in track_ids)
    rows = connection.execute(
        f"""
        select
          id,
          video_id,
          segment_count,
          storage_provider,
          segments_blob_path
        from preferred_youtube_transcripts
        where id in ({placeholders})
        """,
        tuple(sorted(track_ids)),
    ).fetchall()
    return {int(row["id"]): row for row in rows}


def load_segments(
    connection: sqlite3.Connection,
    track_row: sqlite3.Row,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        select segment_index, start_seconds, end_seconds, duration_seconds, text
        from youtube_transcript_segments
        where track_id = ?
        order by segment_index
        """,
        (int(track_row["id"]),),
    ).fetchall()
    if rows:
        return [dict(row) for row in rows]
    blob_path = normalize_text(track_row["segments_blob_path"])
    if not blob_path:
        return []
    return [
        {
            "segment_index": int(segment["segment_index"]),
            "start_seconds": float(segment["start_seconds"]),
            "end_seconds": float(segment["end_seconds"]),
            "duration_seconds": float(segment["duration_seconds"]),
            "text": str(segment["text"]),
        }
        for segment in load_segments_blob(
            blob_path,
            storage_provider=normalize_text(track_row["storage_provider"]),
        )
    ]


def signal_indices(segments: list[dict[str, Any]]) -> set[int]:
    matched: set[int] = set()
    for segment in segments:
        index = int(segment["segment_index"])
        text = normalize_text(segment["text"])
        if any(term in text for term in SIGNAL_TERMS):
            matched.add(index)
    return matched


def menu_indices(segments: list[dict[str, Any]], menu_item: str) -> set[int]:
    menu = normalize_text(menu_item)
    if not menu:
        return set()
    aliases = {menu, menu.replace(" ", "")}
    if len(menu) >= 4:
        aliases.add(menu[:2])
    matched: set[int] = set()
    for segment in segments:
        text = normalize_text(segment["text"])
        compact_text = text.replace(" ", "")
        if any(alias and (alias in text or alias in compact_text) for alias in aliases):
            matched.add(int(segment["segment_index"]))
    return matched


def pct(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) * 100.0 / float(denominator), 2)


def benchmark(args: argparse.Namespace) -> dict[str, Any]:
    connection = sqlite3.connect(args.sqlite)
    connection.row_factory = sqlite3.Row

    scope = source_scope(connection, args.source_name)
    gold = gold_rows(connection, args.source_name)
    track_ids = {int(row["transcript_track_id"]) for row in scope}
    track_ids.update(int(row["transcript_track_id"]) for row in gold)
    tracks = transcript_track_rows(connection, track_ids)
    segments_by_track = {
        track_id: load_segments(connection, track)
        for track_id, track in tracks.items()
    }

    video_window_indices: dict[int, set[int]] = {}
    video_signal_indices: dict[int, set[int]] = {}
    for row in scope:
        track_id = int(row["transcript_track_id"])
        segments = segments_by_track.get(track_id, [])
        signals = signal_indices(segments)
        video_signal_indices[track_id] = signals
        video_window_indices[track_id] = expand_indices(
            signals,
            len(segments),
            args.window_radius,
        )

    item_results = []
    missed_signal = []
    missed_signal_or_menu = []
    recovered_signal = 0
    recovered_signal_or_menu = 0
    pair_recovery: dict[tuple[str, int], list[bool]] = defaultdict(list)
    pair_recovery_or_menu: dict[tuple[str, int], list[bool]] = defaultdict(list)

    for row in gold:
        track_id = int(row["transcript_track_id"])
        segments = segments_by_track.get(track_id, [])
        segment_index = int(row["segment_index"])
        signal_window = video_window_indices.get(track_id, set())
        menu_window = expand_indices(
            menu_indices(segments, str(row["item_name"])),
            len(segments),
            args.window_radius,
        )
        signal_hit = segment_index in signal_window
        signal_or_menu_hit = segment_index in (signal_window | menu_window)
        if signal_hit:
            recovered_signal += 1
        if signal_or_menu_hit:
            recovered_signal_or_menu += 1
        pair_key = (str(row["video_id"]), int(row["restaurant_id"]))
        pair_recovery[pair_key].append(signal_hit)
        pair_recovery_or_menu[pair_key].append(signal_or_menu_hit)
        result = {
            "video_id": row["video_id"],
            "restaurant_id": int(row["restaurant_id"]),
            "rank": int(row["rank"]),
            "item_name": row["item_name"],
            "segment_index": segment_index,
            "timestamp_label": row["timestamp_label"],
            "signal_hit": signal_hit,
            "signal_or_menu_hit": signal_or_menu_hit,
            "reason": row["reason"],
            "repaired_reason": row["repaired_reason"],
            "evidence_text": row["evidence_text"],
            "title": row["title"],
        }
        item_results.append(result)
        if not signal_hit and len(missed_signal) < args.max_examples:
            missed_signal.append(result)
        if not signal_or_menu_hit and len(missed_signal_or_menu) < args.max_examples:
            missed_signal_or_menu.append(result)

    scoped_pairs = sum(int(row["restaurant_count"]) for row in scope)
    segments_once = sum(int(row["segment_count"]) for row in scope)
    pairwise_segments = sum(
        int(row["segment_count"]) * int(row["restaurant_count"])
        for row in scope
    )
    chunks_once = sum(chunk_count(int(row["segment_count"])) for row in scope)
    pairwise_chunks = sum(
        chunk_count(int(row["segment_count"])) * int(row["restaurant_count"])
        for row in scope
    )
    signal_window_segments = sum(len(indices) for indices in video_window_indices.values())
    signal_chunks = sum(
        chunk_count(window_range["count"])
        for indices in video_window_indices.values()
        for window_range in compact_ranges(indices)
    )

    pair_values = list(pair_recovery.values())
    pair_values_or_menu = list(pair_recovery_or_menu.values())
    summary = {
        "source_name": args.source_name,
        "window_radius": args.window_radius,
        "signal_terms": SIGNAL_TERMS,
        "scoped_videos": len(scope),
        "scoped_pairs": scoped_pairs,
        "gold_pairs": len(pair_values),
        "gold_items": len(gold),
        "segments_once": segments_once,
        "pairwise_segments": pairwise_segments,
        "signal_window_segments_once": signal_window_segments,
        "segments_reduction_vs_pairwise_percent": pct(
            pairwise_segments - signal_window_segments,
            pairwise_segments,
        ),
        "chunks_once": chunks_once,
        "pairwise_chunks": pairwise_chunks,
        "video_once_chunks_reduction_vs_pairwise_percent": pct(
            pairwise_chunks - chunks_once,
            pairwise_chunks,
        ),
        "signal_window_chunk_estimate": signal_chunks,
        "chunks_reduction_vs_pairwise_percent": pct(
            pairwise_chunks - signal_chunks,
            pairwise_chunks,
        ),
        "signal_item_recall_percent": pct(recovered_signal, len(gold)),
        "signal_or_gold_menu_item_recall_percent": pct(recovered_signal_or_menu, len(gold)),
        "signal_pair_any_recall_percent": pct(
            sum(1 for values in pair_values if any(values)),
            len(pair_values),
        ),
        "signal_pair_all_recall_percent": pct(
            sum(1 for values in pair_values if all(values)),
            len(pair_values),
        ),
        "signal_or_gold_menu_pair_all_recall_percent": pct(
            sum(1 for values in pair_values_or_menu if all(values)),
            len(pair_values_or_menu),
        ),
        "videos_missing_segments": [
            {"track_id": track_id, "expected_segment_count": int(tracks[track_id]["segment_count"])}
            for track_id, segments in segments_by_track.items()
            if not segments
        ],
    }
    return {
        "summary": summary,
        "missed_signal_examples": missed_signal,
        "missed_signal_or_gold_menu_examples": missed_signal_or_menu,
        "item_results": item_results,
        "video_windows": [
            {
                "transcript_track_id": int(row["transcript_track_id"]),
                "video_id": row["video_id"],
                "title": row["title"],
                "restaurant_count": int(row["restaurant_count"]),
                "segment_count": int(row["segment_count"]),
                "signal_count": len(video_signal_indices.get(int(row["transcript_track_id"]), set())),
                "window_segment_count": len(video_window_indices.get(int(row["transcript_track_id"]), set())),
                "window_ranges": compact_ranges(
                    video_window_indices.get(int(row["transcript_track_id"]), set())
                ),
            }
            for row in scope
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        f"# Must-Taste Prefilter Benchmark - {summary['source_name']}",
        "",
        "## Summary",
        "",
        f"- Scoped videos: {summary['scoped_videos']}",
        f"- Scoped restaurant-video pairs: {summary['scoped_pairs']}",
        f"- Gold pairs/items: {summary['gold_pairs']} pairs / {summary['gold_items']} items",
        f"- Pairwise whole-transcript chunks: {summary['pairwise_chunks']}",
        f"- Video-once whole-transcript chunks: {summary['chunks_once']}",
        f"- Video-once chunk reduction: {summary['video_once_chunks_reduction_vs_pairwise_percent']}%",
        f"- Signal-window chunk estimate: {summary['signal_window_chunk_estimate']}",
        f"- Estimated chunk reduction: {summary['chunks_reduction_vs_pairwise_percent']}%",
        f"- Signal item recall: {summary['signal_item_recall_percent']}%",
        f"- Signal pair all-item recall: {summary['signal_pair_all_recall_percent']}%",
        f"- Signal or gold-menu diagnostic item recall: {summary['signal_or_gold_menu_item_recall_percent']}%",
        "",
        "## Missed Signal Examples",
        "",
    ]
    for item in report["missed_signal_examples"]:
        lines.extend(
            [
                f"- `{item['video_id']}` / restaurant `{item['restaurant_id']}` / rank {item['rank']} / {item['item_name']} / {item['timestamp_label']}",
                f"  - reason: {item['reason']}",
                f"  - evidence: {item['evidence_text']}",
            ]
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = benchmark(args)
    write_json(args.output, report)
    if args.markdown_output:
        write_markdown(args.markdown_output, report)
    summary = report["summary"]
    print(f"source_name={summary['source_name']}")
    print(f"scoped_videos={summary['scoped_videos']}")
    print(f"scoped_pairs={summary['scoped_pairs']}")
    print(f"gold_items={summary['gold_items']}")
    print(f"pairwise_chunks={summary['pairwise_chunks']}")
    print(f"video_once_chunks={summary['chunks_once']}")
    print(
        "video_once_chunks_reduction_vs_pairwise_percent="
        f"{summary['video_once_chunks_reduction_vs_pairwise_percent']}"
    )
    print(f"signal_window_chunk_estimate={summary['signal_window_chunk_estimate']}")
    print(f"chunks_reduction_vs_pairwise_percent={summary['chunks_reduction_vs_pairwise_percent']}")
    print(f"signal_item_recall_percent={summary['signal_item_recall_percent']}")
    print(f"signal_pair_all_recall_percent={summary['signal_pair_all_recall_percent']}")
    print(f"output={args.output}")
    if args.markdown_output:
        print(f"markdown_output={args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
