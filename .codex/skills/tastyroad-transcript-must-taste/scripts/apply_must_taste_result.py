#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from must_taste_schema import DEFAULT_SQLITE, ensure_must_taste_schema


SPACE_RE = re.compile(r"\s+")
REASON_MAX_CHARS = 360
REPAIRED_REASON_MAX_CHARS = 280
QUALITY_MIN_SCORE = 80
REVIEW_MIN_SCORE = 82
QUALIFYING_SIGNALS = {
    "explicit_recommendation",
    "repeat_visit",
    "differentiator",
    "strong_praise",
    "signature_menu",
    "unique_preparation_with_praise",
    "host_must_order",
}
VISIT_DRIVERS = {
    "would_pick_restaurant_for_this",
    "differentiated_from_common_versions",
    "explicit_ordering_advice",
    "strong_host_praise",
    "signature_or_specialty",
}
ATTENTION_EVENT_TYPES = QUALIFYING_SIGNALS | {
    "repeat_mention",
    "ordering_advice",
}
REQUIRED_REVIEWERS = {"evidence_skeptic", "visitor_judge"}
def normalize_text(value: object) -> str:
    return SPACE_RE.sub(" ", str(value or "")).strip()


def timestamp_label(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def validate_reason_text(rank: int, reason: str) -> None:
    if len(reason) > REASON_MAX_CHARS:
        raise ValueError(f"rank {rank}: reason must be concise expanded transcript context.")


def validate_repaired_reason_text(
    rank: int,
    repaired_reason: str,
    raw_reason: str | None = None,
) -> None:
    if len(repaired_reason) > REPAIRED_REASON_MAX_CHARS:
        raise ValueError(f"rank {rank}: repaired_reason is too long for display.")


def validate_reason_quote(
    rank: int,
    reason: str,
    evidence_texts: list[str],
) -> None:
    normalized_reason = normalize_text(reason)
    joined_evidence = normalize_text(" ".join(evidence_texts))
    if normalized_reason in joined_evidence:
        return
    raise ValueError(
        f"rank {rank}: reason must be copied from evidence/supporting_evidence in source order."
    )


def validate_quality(rank: int, quality: object) -> dict[str, Any]:
    if not isinstance(quality, dict):
        raise ValueError(f"rank {rank}: quality object is required.")

    score = quality.get("score")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise ValueError(f"rank {rank}: quality.score must be a number.")
    score_value = int(score)
    if score_value < QUALITY_MIN_SCORE or score_value > 100:
        raise ValueError(
            f"rank {rank}: quality.score must be between {QUALITY_MIN_SCORE} and 100."
        )

    signals = quality.get("signals")
    if not isinstance(signals, list) or not signals:
        raise ValueError(f"rank {rank}: quality.signals must be a non-empty list.")
    normalized_signals = []
    for signal in signals:
        signal_text = normalize_text(signal)
        if signal_text not in QUALIFYING_SIGNALS:
            raise ValueError(
                f"rank {rank}: unsupported quality signal {signal_text!r}. "
                "Mention/order/eating alone is not a qualifying signal."
            )
        normalized_signals.append(signal_text)

    check = normalize_text(quality.get("check"))
    if not check:
        raise ValueError(f"rank {rank}: quality.check is required.")
    if "\n" in str(quality.get("check") or ""):
        raise ValueError(f"rank {rank}: quality.check must be one line.")

    return {
        "score": score_value,
        "signals": normalized_signals,
        "check": check,
    }


def validate_review(rank: int, review: object) -> dict[str, Any]:
    if not isinstance(review, dict):
        raise ValueError(f"rank {rank}: review object is required.")

    score = review.get("score")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise ValueError(f"rank {rank}: review.score must be a number.")
    score_value = int(score)
    if score_value < REVIEW_MIN_SCORE or score_value > 100:
        raise ValueError(
            f"rank {rank}: review.score must be between {REVIEW_MIN_SCORE} and 100."
        )

    verdict = normalize_text(review.get("verdict"))
    if verdict != "pass":
        raise ValueError(f"rank {rank}: review.verdict must be 'pass'.")

    drivers = review.get("drivers")
    if not isinstance(drivers, list) or not drivers:
        raise ValueError(f"rank {rank}: review.drivers must be a non-empty list.")
    normalized_drivers = []
    for driver in drivers:
        driver_text = normalize_text(driver)
        if driver_text not in VISIT_DRIVERS:
            raise ValueError(f"rank {rank}: unsupported review driver {driver_text!r}.")
        normalized_drivers.append(driver_text)

    decision_reason = normalize_text(review.get("decision_reason"))
    if not decision_reason:
        raise ValueError(f"rank {rank}: review.decision_reason is required.")
    if "\n" in str(review.get("decision_reason") or ""):
        raise ValueError(f"rank {rank}: review.decision_reason must be one line.")

    risk = normalize_text(review.get("risk"))
    if not risk:
        raise ValueError(f"rank {rank}: review.risk is required.")
    if "\n" in str(review.get("risk") or ""):
        raise ValueError(f"rank {rank}: review.risk must be one line.")

    return {
        "score": score_value,
        "verdict": verdict,
        "drivers": normalized_drivers,
        "decision_reason": decision_reason,
        "risk": risk,
    }


def validate_evidence_object(
    rank: int,
    evidence: object,
    segments: dict[int, Any],
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(evidence, dict):
        raise ValueError(f"rank {rank}: {field_name} object is required.")

    segment_index = evidence.get("segment_index")
    if not isinstance(segment_index, int):
        raise ValueError(f"rank {rank}: {field_name}.segment_index must be an integer.")
    segment = segments.get(segment_index)
    if segment is None:
        raise ValueError(f"rank {rank}: {field_name}.segment_index {segment_index} is not in context.")

    start_seconds = float(evidence.get("start_seconds"))
    expected_start = float(segment["start_seconds"])
    if abs(start_seconds - expected_start) > 0.05:
        raise ValueError(
            f"rank {rank}: {field_name}.start_seconds {start_seconds} "
            f"does not match segment {segment_index}."
        )

    timestamp = normalize_text(evidence.get("timestamp"))
    expected_timestamp = timestamp_label(expected_start)
    if timestamp != expected_timestamp:
        raise ValueError(
            f"rank {rank}: {field_name}.timestamp must be {expected_timestamp!r} "
            f"for segment {segment_index}."
        )

    evidence_text = normalize_text(evidence.get("text"))
    expected_text = normalize_text(segment["text"])
    if evidence_text != expected_text:
        raise ValueError(
            f"rank {rank}: {field_name}.text must exactly match context segment text."
        )

    return {
        "segment_index": segment_index,
        "start_seconds": expected_start,
        "end_seconds": float(segment["end_seconds"]),
        "timestamp": expected_timestamp,
        "evidence_text": expected_text,
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def resolve_artifact_path(result_path: Path | None, value: object) -> Path:
    raw_path = normalize_text(value)
    if not raw_path:
        raise ValueError("Pipeline artifact path is required.")
    path = Path(raw_path)
    if path.is_absolute() or path.exists() or result_path is None:
        return path
    return result_path.parent / path


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"Missing pipeline artifact: {path}")
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number} must be a JSON object.")
        rows.append(row)
    return rows


def load_json_artifact(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Missing pipeline artifact: {path}")
    return load_json(path)


def validate_pipeline_artifacts(
    context: dict[str, Any],
    result: dict[str, Any],
    result_path: Path | None,
    segments: dict[int, Any],
) -> dict[str, Any]:
    pipeline = result.get("pipeline")
    if not isinstance(pipeline, dict):
        raise ValueError("result.pipeline is required.")

    artifact_paths = {
        key: resolve_artifact_path(result_path, pipeline.get(key))
        for key in (
            "coverage_path",
            "chunks_path",
            "attention_events_path",
            "candidates_path",
            "reviews_path",
        )
    }
    expected_artifact_names = {
        "coverage_path": "coverage.json",
        "chunks_path": "chunks.json",
        "attention_events_path": "attention_events.jsonl",
        "candidates_path": "menu_candidates.json",
        "reviews_path": "candidate_reviews.json",
    }
    for key, expected_name in expected_artifact_names.items():
        if artifact_paths[key].name != expected_name:
            raise ValueError(f"result.pipeline.{key} must point to {expected_name}.")

    video = context.get("video") or {}
    restaurant = context.get("restaurant") or {}
    transcript = context.get("transcript") or {}
    video_id = str(video.get("video_id") or "")
    restaurant_id = int(restaurant.get("id") or 0)
    transcript_track_id = int(transcript.get("track_id") or 0)
    context_hash = normalize_text(context.get("context_hash"))
    if not context_hash:
        raise ValueError("context.context_hash is required.")
    segment_indices = set(segments)

    coverage = load_json_artifact(artifact_paths["coverage_path"])
    if coverage.get("video_id") != video_id:
        raise ValueError("coverage.video_id does not match context.")
    if int(coverage.get("restaurant_id") or 0) != restaurant_id:
        raise ValueError("coverage.restaurant_id does not match context.")
    if int(coverage.get("transcript_track_id") or 0) != transcript_track_id:
        raise ValueError("coverage.transcript_track_id does not match context.")
    if normalize_text(coverage.get("context_hash")) != context_hash:
        raise ValueError("coverage.context_hash does not match context.")
    if int(coverage.get("segment_count") or 0) != len(segments):
        raise ValueError("coverage.segment_count does not match context transcript.")
    if coverage.get("all_segments_covered") is not True:
        raise ValueError("coverage must confirm all transcript segments were covered.")
    if coverage.get("missing_segment_indices"):
        raise ValueError("coverage has missing transcript segments.")

    chunks_doc = load_json_artifact(artifact_paths["chunks_path"])
    if chunks_doc.get("video_id") != video_id:
        raise ValueError("chunks.video_id does not match context.")
    if int(chunks_doc.get("restaurant_id") or 0) != restaurant_id:
        raise ValueError("chunks.restaurant_id does not match context.")
    if int(chunks_doc.get("transcript_track_id") or 0) != transcript_track_id:
        raise ValueError("chunks.transcript_track_id does not match context.")
    if normalize_text(chunks_doc.get("context_hash")) != context_hash:
        raise ValueError("chunks.context_hash does not match context.")
    chunks = chunks_doc.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("chunks artifact must contain non-empty chunks.")
    if int(coverage.get("chunk_count") or 0) != len(chunks):
        raise ValueError("coverage.chunk_count does not match chunks artifact.")
    covered_by_chunks = {
        int(line["segment_index"])
        for chunk in chunks
        if isinstance(chunk, dict)
        for line in chunk.get("lines", [])
        if isinstance(line, dict) and "segment_index" in line
    }
    if covered_by_chunks != segment_indices:
        raise ValueError("chunks artifact does not cover every transcript segment exactly as a set.")

    events = load_jsonl(artifact_paths["attention_events_path"])
    event_by_id: dict[str, dict[str, Any]] = {}
    candidate_event_ids: dict[str, set[str]] = {}
    candidate_event_segments: dict[str, set[int]] = {}
    for event in events:
        if event.get("video_id") != video_id:
            raise ValueError("attention event video_id does not match context.")
        if int(event.get("restaurant_id") or 0) != restaurant_id:
            raise ValueError("attention event restaurant_id does not match context.")
        if int(event.get("transcript_track_id") or 0) != transcript_track_id:
            raise ValueError("attention event transcript_track_id does not match context.")
        if normalize_text(event.get("context_hash")) != context_hash:
            raise ValueError("attention event context_hash does not match context.")
        event_id = normalize_text(event.get("event_id"))
        candidate_id = normalize_text(event.get("candidate_id"))
        event_type = normalize_text(event.get("event_type"))
        if not event_id or event_id in event_by_id:
            raise ValueError(f"Invalid or duplicate attention event_id {event_id!r}.")
        if not candidate_id:
            raise ValueError(f"attention event {event_id}: candidate_id is required.")
        if event_type not in ATTENTION_EVENT_TYPES:
            raise ValueError(f"attention event {event_id}: unsupported event_type {event_type!r}.")
        scope_note = normalize_text(event.get("restaurant_scope_note"))
        if not scope_note:
            raise ValueError(f"attention event {event_id}: restaurant_scope_note is required.")
        if "\n" in str(event.get("restaurant_scope_note") or ""):
            raise ValueError(f"attention event {event_id}: restaurant_scope_note must be one line.")
        score = event.get("attention_score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or score < 0 or score > 100:
            raise ValueError(f"attention event {event_id}: attention_score must be 0..100.")
        evidence = validate_evidence_object(
            0,
            {
                "segment_index": event.get("segment_index"),
                "timestamp": event.get("timestamp"),
                "start_seconds": event.get("start_seconds"),
                "text": event.get("text"),
            },
            segments,
            f"attention_event[{event_id}]",
        )
        event_by_id[event_id] = event
        candidate_event_ids.setdefault(candidate_id, set()).add(event_id)
        candidate_event_segments.setdefault(candidate_id, set()).add(int(evidence["segment_index"]))

    candidates_doc = load_json_artifact(artifact_paths["candidates_path"])
    if candidates_doc.get("video_id") != video_id:
        raise ValueError("menu_candidates.video_id does not match context.")
    if int(candidates_doc.get("restaurant_id") or 0) != restaurant_id:
        raise ValueError("menu_candidates.restaurant_id does not match context.")
    if int(candidates_doc.get("transcript_track_id") or 0) != transcript_track_id:
        raise ValueError("menu_candidates.transcript_track_id does not match context.")
    if normalize_text(candidates_doc.get("context_hash")) != context_hash:
        raise ValueError("menu_candidates.context_hash does not match context.")
    candidates = candidates_doc.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("menu_candidates artifact must contain a candidates list.")
    candidate_by_id: dict[str, dict[str, Any]] = {}
    candidate_declared_event_ids: dict[str, set[str]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Each menu candidate must be an object.")
        candidate_id = normalize_text(candidate.get("candidate_id"))
        if not candidate_id or candidate_id in candidate_by_id:
            raise ValueError(f"Invalid or duplicate candidate_id {candidate_id!r}.")
        event_ids = candidate.get("event_ids")
        if not isinstance(event_ids, list) or not event_ids:
            raise ValueError(f"candidate {candidate_id}: event_ids must be non-empty.")
        missing_events = {normalize_text(event_id) for event_id in event_ids} - set(event_by_id)
        if missing_events:
            raise ValueError(f"candidate {candidate_id}: unknown event_ids {sorted(missing_events)}.")
        declared_event_ids = {normalize_text(event_id) for event_id in event_ids}
        mismatched_events = [
            event_id
            for event_id in declared_event_ids
            if normalize_text(event_by_id[event_id].get("candidate_id")) != candidate_id
        ]
        if mismatched_events:
            raise ValueError(
                f"candidate {candidate_id}: event_ids belong to another candidate "
                f"{sorted(mismatched_events)}."
            )
        if not normalize_text(candidate.get("menu_item")):
            raise ValueError(f"candidate {candidate_id}: menu_item is required.")
        attention_score = candidate.get("attention_score")
        if (
            not isinstance(attention_score, (int, float))
            or isinstance(attention_score, bool)
            or attention_score < 0
            or attention_score > 100
        ):
            raise ValueError(f"candidate {candidate_id}: attention_score must be 0..100.")
        candidate_by_id[candidate_id] = candidate
        candidate_declared_event_ids[candidate_id] = declared_event_ids
    unaggregated_candidates = set(candidate_event_ids) - set(candidate_by_id)
    if unaggregated_candidates:
        raise ValueError(
            "Every attention event must be represented in menu_candidates. "
            f"Missing candidate_ids: {sorted(unaggregated_candidates)}."
        )
    for candidate_id, event_ids in candidate_event_ids.items():
        missing_from_candidate = event_ids - candidate_declared_event_ids.get(candidate_id, set())
        if missing_from_candidate:
            raise ValueError(
                f"candidate {candidate_id}: menu_candidates is missing attention events "
                f"{sorted(missing_from_candidate)}."
            )

    reviews_doc = load_json_artifact(artifact_paths["reviews_path"])
    if reviews_doc.get("video_id") != video_id:
        raise ValueError("candidate_reviews.video_id does not match context.")
    if int(reviews_doc.get("restaurant_id") or 0) != restaurant_id:
        raise ValueError("candidate_reviews.restaurant_id does not match context.")
    if int(reviews_doc.get("transcript_track_id") or 0) != transcript_track_id:
        raise ValueError("candidate_reviews.transcript_track_id does not match context.")
    if normalize_text(reviews_doc.get("context_hash")) != context_hash:
        raise ValueError("candidate_reviews.context_hash does not match context.")
    reviews = reviews_doc.get("reviews")
    if not isinstance(reviews, list):
        raise ValueError("candidate_reviews artifact must contain a reviews list.")
    reviews_by_candidate: dict[str, dict[str, dict[str, Any]]] = {}
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError("Each candidate review must be an object.")
        candidate_id = normalize_text(review.get("candidate_id"))
        reviewer = normalize_text(review.get("reviewer"))
        if candidate_id not in candidate_by_id:
            raise ValueError(f"review references unknown candidate_id {candidate_id!r}.")
        if not reviewer:
            raise ValueError(f"review for {candidate_id}: reviewer is required.")
        if reviewer in reviews_by_candidate.get(candidate_id, {}):
            raise ValueError(f"Duplicate review for {candidate_id}/{reviewer}.")
        score = review.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or score < 0 or score > 100:
            raise ValueError(f"review for {candidate_id}/{reviewer}: score must be 0..100.")
        verdict = normalize_text(review.get("verdict"))
        if verdict not in {"pass", "fail", "borderline"}:
            raise ValueError(f"review for {candidate_id}/{reviewer}: invalid verdict.")
        if not normalize_text(review.get("reason")):
            raise ValueError(f"review for {candidate_id}/{reviewer}: reason is required.")
        cited_event_ids = review.get("cited_event_ids")
        if not isinstance(cited_event_ids, list) or not cited_event_ids:
            raise ValueError(
                f"review for {candidate_id}/{reviewer}: cited_event_ids must be non-empty."
            )
        cited_ids = {normalize_text(event_id) for event_id in cited_event_ids}
        unknown_citations = cited_ids - set(event_by_id)
        if unknown_citations:
            raise ValueError(
                f"review for {candidate_id}/{reviewer}: unknown cited_event_ids "
                f"{sorted(unknown_citations)}."
            )
        wrong_candidate_citations = [
            event_id
            for event_id in cited_ids
            if normalize_text(event_by_id[event_id].get("candidate_id")) != candidate_id
        ]
        if wrong_candidate_citations:
            raise ValueError(
                f"review for {candidate_id}/{reviewer}: cited_event_ids belong to another "
                f"candidate {sorted(wrong_candidate_citations)}."
            )
        reviews_by_candidate.setdefault(candidate_id, {})[reviewer] = review
    for candidate_id in candidate_by_id:
        missing_reviewers = REQUIRED_REVIEWERS - set(reviews_by_candidate.get(candidate_id, {}))
        if missing_reviewers:
            raise ValueError(
                f"candidate {candidate_id} is missing reviews from {sorted(missing_reviewers)}."
            )

    return {
        "paths": {key: str(path) for key, path in artifact_paths.items()},
        "coverage": coverage,
        "candidate_by_id": candidate_by_id,
        "candidate_event_segments": candidate_event_segments,
        "reviews_by_candidate": reviews_by_candidate,
    }


def validate_result(
    context: dict[str, Any],
    result: dict[str, Any],
    result_path: Path | None = None,
) -> list[dict[str, Any]]:
    video = context.get("video") or {}
    restaurant = context.get("restaurant") or {}
    transcript = context.get("transcript") or {}
    video_id = str(video.get("video_id") or "")
    restaurant_id = int(restaurant.get("id") or 0)

    if result.get("video_id") != video_id:
        raise ValueError(f"result.video_id must be {video_id!r}.")
    if result.get("restaurant_id") != restaurant_id:
        raise ValueError(f"result.restaurant_id must be {restaurant_id!r}.")
    context_hash = normalize_text(context.get("context_hash"))
    if result.get("context_hash") != context_hash:
        raise ValueError("result.context_hash must match context.context_hash.")

    segments = {
        int(segment["segment_index"]): segment
        for segment in transcript.get("segments", [])
        if isinstance(segment, dict) and "segment_index" in segment
    }
    if not segments:
        raise ValueError("context transcript has no segments.")
    pipeline_artifacts = validate_pipeline_artifacts(context, result, result_path, segments)

    items = result.get("items")
    if not isinstance(items, list):
        raise ValueError("result.items must be a list.")
    if len(items) > 3:
        raise ValueError("result.items must contain at most three quality-gated items.")
    if len(items) == 0:
        if result.get("insufficient_evidence") is not True:
            raise ValueError(
                "Empty result.items must set insufficient_evidence to true."
            )
        if not normalize_text(result.get("insufficient_evidence_reason")):
            raise ValueError("insufficient_evidence_reason is required for empty results.")

    normalized_items = []
    seen_ranks = set()
    seen_menu_items = set()
    seen_candidate_ids = set()

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each result item must be an object.")

        rank = item.get("rank")
        if not isinstance(rank, int) or rank not in {1, 2, 3}:
            raise ValueError("Each item.rank must be 1, 2, or 3.")
        if rank in seen_ranks:
            raise ValueError(f"Duplicate rank: {rank}")
        seen_ranks.add(rank)

        candidate_id = normalize_text(item.get("candidate_id"))
        if not candidate_id:
            raise ValueError(f"rank {rank}: candidate_id is required.")
        if candidate_id in seen_candidate_ids:
            raise ValueError(f"rank {rank}: duplicate candidate_id {candidate_id!r}.")
        if candidate_id not in pipeline_artifacts["candidate_by_id"]:
            raise ValueError(f"rank {rank}: candidate_id {candidate_id!r} is not in candidates.")
        seen_candidate_ids.add(candidate_id)

        menu_item = normalize_text(item.get("menu_item"))
        reason = normalize_text(item.get("reason"))
        repaired_reason = normalize_text(item.get("repaired_reason"))
        if not menu_item:
            raise ValueError(f"rank {rank}: menu_item is required.")
        if menu_item.casefold() in seen_menu_items:
            raise ValueError(f"rank {rank}: duplicate menu_item {menu_item!r}.")
        seen_menu_items.add(menu_item.casefold())
        if not reason:
            raise ValueError(f"rank {rank}: reason is required.")
        if "\n" in str(item.get("reason") or ""):
            raise ValueError(f"rank {rank}: reason must be one line.")
        validate_reason_text(rank, reason)
        if not repaired_reason:
            raise ValueError(f"rank {rank}: repaired_reason is required.")
        if "\n" in str(item.get("repaired_reason") or ""):
            raise ValueError(f"rank {rank}: repaired_reason must be one line.")
        validate_repaired_reason_text(rank, repaired_reason, reason)

        quality = validate_quality(rank, item.get("quality"))
        review = validate_review(rank, item.get("review"))
        primary_evidence = validate_evidence_object(rank, item.get("evidence"), segments, "evidence")
        supporting_evidence = item.get("supporting_evidence", [])
        if supporting_evidence is None:
            supporting_evidence = []
        if not isinstance(supporting_evidence, list):
            raise ValueError(f"rank {rank}: supporting_evidence must be a list when present.")
        normalized_supporting_evidence = [
            validate_evidence_object(rank, entry, segments, "supporting_evidence")
            for entry in supporting_evidence
        ]
        source_evidence = sorted(
            [primary_evidence] + normalized_supporting_evidence,
            key=lambda entry: int(entry["segment_index"]),
        )
        validate_reason_quote(
            rank,
            reason,
            [entry["evidence_text"] for entry in source_evidence],
        )
        selected_segments = {int(primary_evidence["segment_index"])}
        selected_segments.update(int(entry["segment_index"]) for entry in normalized_supporting_evidence)
        candidate_segments = pipeline_artifacts["candidate_event_segments"].get(candidate_id, set())
        if not selected_segments & candidate_segments:
            raise ValueError(
                f"rank {rank}: evidence segments must overlap attention events for candidate {candidate_id}."
            )

        candidate_reviews = pipeline_artifacts["reviews_by_candidate"].get(candidate_id, {})
        missing_reviewers = REQUIRED_REVIEWERS - set(candidate_reviews)
        if missing_reviewers:
            raise ValueError(
                f"rank {rank}: candidate {candidate_id} is missing reviews from {sorted(missing_reviewers)}."
            )
        for reviewer in REQUIRED_REVIEWERS:
            candidate_review = candidate_reviews[reviewer]
            if normalize_text(candidate_review.get("verdict")) != "pass":
                raise ValueError(f"rank {rank}: {reviewer} did not pass candidate {candidate_id}.")
            if int(candidate_review.get("score") or 0) < REVIEW_MIN_SCORE:
                raise ValueError(f"rank {rank}: {reviewer} score is below {REVIEW_MIN_SCORE}.")

        normalized_items.append(
            {
                "rank": rank,
                "candidate_id": candidate_id,
                "menu_item": menu_item,
                "reason": reason,
                "repaired_reason": repaired_reason,
                "quality": quality,
                "review": review,
                "segment_index": primary_evidence["segment_index"],
                "start_seconds": primary_evidence["start_seconds"],
                "end_seconds": primary_evidence["end_seconds"],
                "timestamp": primary_evidence["timestamp"],
                "evidence_text": primary_evidence["evidence_text"],
                "supporting_evidence": normalized_supporting_evidence,
            }
        )

    expected_ranks = set(range(1, len(items) + 1))
    if seen_ranks != expected_ranks:
        raise ValueError(f"Ranks must be sequential starting at 1: {sorted(expected_ranks)}.")

    rejected_candidates = result.get("rejected_candidates")
    if not isinstance(rejected_candidates, list):
        raise ValueError("result.rejected_candidates must be a list.")
    rejected_ids = set()
    for rejected in rejected_candidates:
        if not isinstance(rejected, dict):
            raise ValueError("Each rejected candidate must be an object.")
        candidate_id = normalize_text(rejected.get("candidate_id"))
        if candidate_id not in pipeline_artifacts["candidate_by_id"]:
            raise ValueError(f"rejected candidate references unknown candidate_id {candidate_id!r}.")
        if candidate_id in rejected_ids:
            raise ValueError(f"Duplicate rejected candidate_id {candidate_id!r}.")
        if not normalize_text(rejected.get("menu_item")):
            raise ValueError(f"rejected candidate {candidate_id}: menu_item is required.")
        if not normalize_text(rejected.get("reason")):
            raise ValueError(f"rejected candidate {candidate_id}: reason is required.")
        if "\n" in str(rejected.get("reason") or ""):
            raise ValueError(f"rejected candidate {candidate_id}: reason must be one line.")
        rejected_ids.add(candidate_id)
    all_candidate_ids = set(pipeline_artifacts["candidate_by_id"])
    if seen_candidate_ids | rejected_ids != all_candidate_ids:
        missing = sorted(all_candidate_ids - seen_candidate_ids - rejected_ids)
        raise ValueError(f"Every candidate must be selected or rejected. Missing: {missing}")
    if seen_candidate_ids & rejected_ids:
        raise ValueError("A candidate cannot be both selected and rejected.")

    return sorted(normalized_items, key=lambda entry: entry["rank"])


def apply_result(
    sqlite_path: Path,
    context_path: Path,
    result_path: Path,
    reviewer: str,
    dry_run: bool,
) -> None:
    context = load_json(context_path)
    result = load_json(result_path)
    items = validate_result(context, result, result_path)

    video = context["video"]
    restaurant = context["restaurant"]
    transcript = context["transcript"]
    generated_at = normalize_text(result.get("generated_at")) or datetime.now(timezone.utc).isoformat()

    if dry_run:
        connection_target = f"file:{sqlite_path.resolve()}?mode=ro"
        connection_options = {"uri": True}
    else:
        connection_target = sqlite_path
        connection_options = {}

    with sqlite3.connect(connection_target, **connection_options) as connection:
        if not dry_run:
            ensure_must_taste_schema(connection)
        row = connection.execute(
            "select id from youtube_videos where video_id = ?",
            (video["video_id"],),
        ).fetchone()
        if row is None:
            raise ValueError(f"Video {video['video_id']!r} is not in youtube_videos.")
        youtube_video_id = int(row[0])

        if int(video["youtube_video_id"]) != youtube_video_id:
            raise ValueError("context youtube_video_id does not match database.")

        restaurant_id = int(restaurant["id"])
        mapped = connection.execute(
            """
            select 1
            from youtube_video_restaurants
            where restaurant_id = ?
              and youtube_video_id = ?
              and status in ('verified', 'metadata_verified')
            """,
            (restaurant_id, youtube_video_id),
        ).fetchone()
        if mapped is None:
            raise ValueError("context restaurant_id is not a verified mapping for this video.")

        if dry_run:
            print(
                json.dumps(
                    {
                        "video_id": video["video_id"],
                        "restaurant_id": restaurant_id,
                        "restaurant_name": restaurant["display_name"],
                        "items": items,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        connection.execute(
            """
            delete from video_must_taste_items
            where restaurant_id = ?
              and youtube_video_id = ?
            """,
            (restaurant_id, youtube_video_id),
        )
        for item in items:
            evidence_json = {
                "source": transcript.get("storage_provider") or "youtube_transcript_segments",
                "context_path": str(context_path),
                "result_path": str(result_path),
                "language_code": transcript.get("language_code", ""),
                "is_generated": bool(transcript.get("is_generated")),
                "segments_blob_path": transcript.get("segments_blob_path", ""),
                "quality": item["quality"],
                "review": item["review"],
                "candidate_id": item["candidate_id"],
                "repaired_reason": item["repaired_reason"],
                "pipeline": result.get("pipeline", {}),
                "rejected_candidates": result.get("rejected_candidates", []),
                "supporting_evidence": item["supporting_evidence"],
            }
            connection.execute(
                """
                insert into video_must_taste_items (
                  restaurant_id,
                  youtube_video_id,
                  video_id,
                  rank,
                  item_name,
                  reason,
                  repaired_reason,
                  segment_index,
                  start_seconds,
                  end_seconds,
                  timestamp_label,
                  evidence_text,
                  transcript_track_id,
                  reviewer,
                  generated_at,
                  evidence_json
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    restaurant_id,
                    youtube_video_id,
                    video["video_id"],
                    item["rank"],
                    item["menu_item"],
                    item["reason"],
                    item["repaired_reason"],
                    item["segment_index"],
                    item["start_seconds"],
                    item["end_seconds"],
                    item["timestamp"],
                    item["evidence_text"],
                    int(transcript["track_id"]),
                    reviewer,
                    generated_at,
                    json.dumps(evidence_json, ensure_ascii=False, sort_keys=True),
                ),
            )

    print(
        f"Stored {len(items)} must-taste items for "
        f"{restaurant['display_name']} ({video['video_id']}) in {sqlite_path}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and store transcript-grounded must-taste recommendations."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--reviewer", default="codex")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apply_result(args.sqlite, args.context, args.result, args.reviewer, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
