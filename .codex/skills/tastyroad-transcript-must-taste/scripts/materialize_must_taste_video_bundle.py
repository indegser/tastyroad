#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from apply_must_taste_result import timestamp_label, validate_result


DEFAULT_PAIRS_ROOT = Path("data/work/must_taste")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize one video's two semantic responses into ordinary pair-level "
            "must-taste artifacts and validate them without writing SQLite."
        )
    )
    parser.add_argument("--video-context", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--pairs-root", type=Path, default=DEFAULT_PAIRS_ROOT)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: object) -> str:
    return " ".join(str(value or "").split())


def pairs_by_restaurant(document: dict[str, Any], label: str) -> dict[int, dict[str, Any]]:
    rows = document.get("pairs")
    if not isinstance(rows, list):
        raise ValueError(f"{label}.pairs must be a list.")
    indexed = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"Each {label}.pairs row must be an object.")
        restaurant_id = int(row.get("restaurant_id") or 0)
        if restaurant_id < 1 or restaurant_id in indexed:
            raise ValueError(f"{label}: invalid or duplicate restaurant_id {restaurant_id}.")
        indexed[restaurant_id] = row
    return indexed


def segment_map(context: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        int(segment["segment_index"]): segment
        for segment in (context.get("transcript") or {}).get("segments", [])
        if isinstance(segment, dict) and isinstance(segment.get("segment_index"), int)
    }


def evidence_from_segment(
    segments: dict[int, dict[str, Any]],
    segment_index: int,
) -> dict[str, Any]:
    segment = segments.get(segment_index)
    if segment is None:
        raise ValueError(f"Unknown transcript segment_index {segment_index}.")
    start_seconds = float(segment["start_seconds"])
    return {
        "segment_index": segment_index,
        "timestamp": timestamp_label(start_seconds),
        "start_seconds": start_seconds,
        "text": str(segment["text"]),
    }


def chunk_for_segment(chunks: list[dict[str, Any]], segment_index: int) -> str:
    for chunk in chunks:
        indices = {
            int(line["segment_index"])
            for line in chunk.get("lines", [])
            if isinstance(line, dict) and isinstance(line.get("segment_index"), int)
        }
        if segment_index in indices:
            return str(chunk["chunk_id"])
    raise ValueError(f"No prepared chunk covers segment_index {segment_index}.")


def enrich_event(
    event: dict[str, Any],
    *,
    video_id: str,
    restaurant_id: int,
    transcript_track_id: int,
    context_hash: str,
    segments: dict[int, dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    segment_index = int(event.get("segment_index"))
    enriched = dict(event)
    enriched.update(evidence_from_segment(segments, segment_index))
    enriched.update(
        {
            "video_id": video_id,
            "restaurant_id": restaurant_id,
            "transcript_track_id": transcript_track_id,
            "context_hash": context_hash,
            "chunk_id": chunk_for_segment(chunks, segment_index),
        }
    )
    scope_note = normalize_text(
        enriched.pop("scope_note", None) or enriched.get("restaurant_scope_note")
    )
    if not scope_note:
        raise ValueError(
            f"restaurant {restaurant_id} event {event.get('event_id')}: scope_note is required."
        )
    enriched["restaurant_scope_note"] = scope_note
    return enriched


def enrich_item(
    item: dict[str, Any],
    segments: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    enriched = dict(item)
    primary_index = enriched.pop("evidence_segment_index", None)
    if primary_index is None:
        evidence = enriched.get("evidence") or {}
        primary_index = evidence.get("segment_index")
    if primary_index is None:
        raise ValueError(f"rank {item.get('rank')}: evidence_segment_index is required.")
    supporting_indices = enriched.pop("supporting_segment_indices", None)
    if supporting_indices is None:
        supporting_indices = [
            entry.get("segment_index")
            for entry in enriched.get("supporting_evidence") or []
            if isinstance(entry, dict)
        ]
    enriched["evidence"] = evidence_from_segment(segments, int(primary_index))
    enriched["supporting_evidence"] = [
        evidence_from_segment(segments, int(index))
        for index in supporting_indices
    ]
    return enriched


def root_document(
    values: list[dict[str, Any]],
    *,
    key: str,
    video_id: str,
    restaurant_id: int,
    transcript_track_id: int,
    context_hash: str,
) -> dict[str, Any]:
    return {
        "video_id": video_id,
        "restaurant_id": restaurant_id,
        "transcript_track_id": transcript_track_id,
        "context_hash": context_hash,
        key: values,
    }


def build_pair_artifacts(
    *,
    context_path: Path,
    findings_pair: dict[str, Any],
    bundle_pair: dict[str, Any],
    stage_dir: Path,
) -> dict[str, Any]:
    context = read_json(context_path)
    video_id = str((context.get("video") or {}).get("video_id") or "")
    restaurant_id = int((context.get("restaurant") or {}).get("id") or 0)
    transcript_track_id = int((context.get("transcript") or {}).get("track_id") or 0)
    context_hash = normalize_text(context.get("context_hash"))
    segments = segment_map(context)
    if not segments:
        raise ValueError(f"{context_path}: transcript segments are missing.")

    pair_dir = context_path.parent
    chunks_doc = read_json(pair_dir / "chunks.json")
    chunks = chunks_doc.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError(f"{pair_dir / 'chunks.json'}: chunks are missing.")

    events_raw = findings_pair.get("attention_events")
    candidates = bundle_pair.get("candidates")
    reviews = bundle_pair.get("reviews")
    items = bundle_pair.get("items")
    rejected = bundle_pair.get("rejected_candidates")
    if not isinstance(events_raw, list):
        raise ValueError(f"restaurant {restaurant_id}: attention_events must be a list.")
    if not isinstance(candidates, list):
        raise ValueError(f"restaurant {restaurant_id}: candidates must be a list.")
    if not isinstance(reviews, list):
        raise ValueError(f"restaurant {restaurant_id}: reviews must be a list.")
    if not isinstance(items, list):
        raise ValueError(f"restaurant {restaurant_id}: items must be a list.")
    if not isinstance(rejected, list):
        raise ValueError(f"restaurant {restaurant_id}: rejected_candidates must be a list.")

    events = [
        enrich_event(
            event,
            video_id=video_id,
            restaurant_id=restaurant_id,
            transcript_track_id=transcript_track_id,
            context_hash=context_hash,
            segments=segments,
            chunks=chunks,
        )
        for event in events_raw
    ]
    enriched_items = [enrich_item(item, segments) for item in items]
    candidates_doc = root_document(
        candidates,
        key="candidates",
        video_id=video_id,
        restaurant_id=restaurant_id,
        transcript_track_id=transcript_track_id,
        context_hash=context_hash,
    )
    reviews_doc = root_document(
        reviews,
        key="reviews",
        video_id=video_id,
        restaurant_id=restaurant_id,
        transcript_track_id=transcript_track_id,
        context_hash=context_hash,
    )

    stage_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pair_dir / "coverage.json", stage_dir / "coverage.json")
    shutil.copy2(pair_dir / "chunks.json", stage_dir / "chunks.json")
    (stage_dir / "attention_events.jsonl").write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )
    write_json(stage_dir / "menu_candidates.json", candidates_doc)
    write_json(stage_dir / "candidate_reviews.json", reviews_doc)
    result = {
        "video_id": video_id,
        "restaurant_id": restaurant_id,
        "context_hash": context_hash,
        "pipeline": {
            "coverage_path": str(stage_dir / "coverage.json"),
            "chunks_path": str(stage_dir / "chunks.json"),
            "attention_events_path": str(stage_dir / "attention_events.jsonl"),
            "candidates_path": str(stage_dir / "menu_candidates.json"),
            "reviews_path": str(stage_dir / "candidate_reviews.json"),
        },
        "items": enriched_items,
        "rejected_candidates": rejected,
    }
    if not enriched_items:
        result["insufficient_evidence"] = True
        result["insufficient_evidence_reason"] = normalize_text(
            bundle_pair.get("insufficient_evidence_reason")
        )
    write_json(stage_dir / "result.json", result)
    validate_result(context, result, stage_dir / "result.json")
    return {
        "context": context,
        "pair_dir": pair_dir,
        "stage_dir": stage_dir,
        "result": result,
        "candidates_doc": candidates_doc,
        "reviews_doc": reviews_doc,
        "events": events,
    }


def final_result(pair: dict[str, Any]) -> dict[str, Any]:
    pair_dir = pair["pair_dir"]
    result = dict(pair["result"])
    result["pipeline"] = {
        "coverage_path": str(pair_dir / "coverage.json"),
        "chunks_path": str(pair_dir / "chunks.json"),
        "attention_events_path": str(pair_dir / "attention_events.jsonl"),
        "candidates_path": str(pair_dir / "menu_candidates.json"),
        "reviews_path": str(pair_dir / "candidate_reviews.json"),
    }
    return result


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    video_context = read_json(args.video_context)
    findings = read_json(args.findings)
    bundle = read_json(args.bundle)
    video_id = str((video_context.get("video") or {}).get("video_id") or "")
    if findings.get("video_id") != video_id or bundle.get("video_id") != video_id:
        raise ValueError("video_id must match across video context, findings, and bundle.")
    windows = findings.get("windows")
    if not isinstance(windows, list):
        raise ValueError("findings.windows must be a list.")

    expected_restaurants = {
        int(restaurant["restaurant_id"])
        for restaurant in video_context.get("restaurants") or []
    }
    finding_pairs = pairs_by_restaurant(findings, "findings")
    bundle_pairs = pairs_by_restaurant(bundle, "bundle")
    if set(finding_pairs) != expected_restaurants:
        raise ValueError("findings.pairs must cover every restaurant in video_context.")
    if set(bundle_pairs) != expected_restaurants:
        raise ValueError("bundle.pairs must cover every restaurant in video_context.")

    staged_pairs = []
    with tempfile.TemporaryDirectory(prefix="must-taste-video-bundle-") as temp_dir:
        temp_root = Path(temp_dir)
        for restaurant_id in sorted(expected_restaurants):
            context_path = args.pairs_root / video_id / str(restaurant_id) / "context.json"
            if not context_path.exists():
                raise ValueError(
                    f"Missing {context_path}. Prepare every pair context before materializing."
                )
            staged_pairs.append(
                build_pair_artifacts(
                    context_path=context_path,
                    findings_pair=finding_pairs[restaurant_id],
                    bundle_pair=bundle_pairs[restaurant_id],
                    stage_dir=temp_root / str(restaurant_id),
                )
            )

        for pair in staged_pairs:
            pair_dir = pair["pair_dir"]
            stage_dir = pair["stage_dir"]
            shutil.copy2(stage_dir / "attention_events.jsonl", pair_dir / "attention_events.jsonl")
            shutil.copy2(stage_dir / "menu_candidates.json", pair_dir / "menu_candidates.json")
            shutil.copy2(stage_dir / "candidate_reviews.json", pair_dir / "candidate_reviews.json")
            write_json(pair_dir / "result.json", final_result(pair))

    artifacts = video_context.get("artifacts") or {}
    windows_path = Path(
        str(
            artifacts.get("restaurant_windows_path")
            or args.video_context.parent / "restaurant_windows.json"
        )
    )
    shared_events_path = Path(
        str(
            artifacts.get("shared_events_path")
            or args.video_context.parent / "video_attention_events.jsonl"
        )
    )
    write_json(
        windows_path,
        {
            "video_id": video_id,
            "transcript_track_id": int(
                (video_context.get("transcript") or {}).get("track_id") or 0
            ),
            "context_hash": normalize_text(video_context.get("context_hash")),
            "windows": windows,
            "status": "reviewed",
        },
    )
    shared_events_path.parent.mkdir(parents=True, exist_ok=True)
    shared_events_path.write_text(
        "".join(
            json.dumps(event, ensure_ascii=False) + "\n"
            for pair in staged_pairs
            for event in pair["events"]
        ),
        encoding="utf-8",
    )

    return {
        "video_id": video_id,
        "pair_count": len(staged_pairs),
        "item_count": sum(len(pair["result"]["items"]) for pair in staged_pairs),
        "validated": True,
        "sqlite_written": False,
    }


def main() -> int:
    args = parse_args()
    report = materialize(args)
    print(f"video_id={report['video_id']}")
    print(f"pairs={report['pair_count']}")
    print(f"items={report['item_count']}")
    print("validated=true")
    print("sqlite_written=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
