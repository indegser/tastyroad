#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from collect_youtube import DEFAULT_SQLITE
from pipeline_schema import ensure_pipeline_schema
from process_video_stories import (
    TranscriptPayload,
    story_review_evidence,
    upsert_transcript,
    validate_story_review_quality,
)
from promote_verified_places import (
    get_youtube_video_id,
    resolve_naver_map_details,
    upsert_video_restaurant,
    upsert_place_link,
    upsert_place_resolution_candidate,
    upsert_restaurant,
)


DEFAULT_WORK_DIR = Path("data/work")
REDUCIBLE_STAGES = ("restaurant_triage", "transcript_fetch", "story_review", "place_verification")


@dataclass(frozen=True)
class ReductionResult:
    video_id: str
    artifact_path: str
    status: str
    reason: str = ""


def discover_stage_artifacts(work_dir: Path, filename: str) -> list[Path]:
    videos_dir = work_dir / "videos"
    if not videos_dir.exists():
        return []
    return sorted(videos_dir.glob(f"*/{filename}"))


def artifact_filename(stage: str) -> str:
    filenames = {
        "restaurant_triage": "restaurant_review.json",
        "transcript_fetch": "transcript.json",
        "story_review": "story_review.json",
        "place_verification": "place_verification.json",
    }
    return filenames[stage]


def discover_artifacts(work_dir: Path, stage: str) -> list[Path]:
    return discover_stage_artifacts(work_dir, artifact_filename(stage))


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def successful_artifact(path: Path, stage: str) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("schema_version") != 1:
        raise ValueError(f"{path} has unsupported schema_version={payload.get('schema_version')!r}")
    if payload.get("stage") != stage:
        raise ValueError(f"{path} is not a {stage} artifact")
    if payload.get("status") != "succeeded":
        raise ValueError(f"{path} status is {payload.get('status')!r}, not 'succeeded'")
    return payload


def transcript_from_artifact(path: Path) -> tuple[str, str, TranscriptPayload]:
    payload = successful_artifact(path, "transcript_fetch")
    video_id = str(payload.get("video_id") or "").strip()
    fetched_at = str(payload.get("fetched_at") or "").strip()
    output = payload.get("output")
    if not video_id:
        raise ValueError(f"{path} is missing video_id")
    if not fetched_at:
        raise ValueError(f"{path} is missing fetched_at")
    if not isinstance(output, dict):
        raise ValueError(f"{path} is missing output object")

    segments = output.get("segments")
    if not isinstance(segments, list):
        raise ValueError(f"{path} output.segments must be a list")
    text = str(output.get("text") or "")
    if not text.strip():
        raise ValueError(f"{path} output.text is empty")

    transcript = TranscriptPayload(
        language_code=str(output.get("language_code") or ""),
        language=str(output.get("language") or ""),
        is_generated=bool(output.get("is_generated")),
        segments=[segment for segment in segments if isinstance(segment, dict)],
        text=text,
    )
    return video_id, fetched_at, transcript


def review_from_artifact(path: Path) -> tuple[str, dict[str, Any]]:
    payload = successful_artifact(path, "restaurant_triage")
    video_id = str(payload.get("video_id") or "").strip()
    output = payload.get("output")
    if not video_id:
        raise ValueError(f"{path} is missing video_id")
    if not isinstance(output, dict) or not isinstance(output.get("review"), dict):
        raise ValueError(f"{path} is missing output.review")
    return video_id, output["review"]


def story_from_artifact(path: Path) -> tuple[str, dict[str, Any]]:
    payload = successful_artifact(path, "story_review")
    video_id = str(payload.get("video_id") or "").strip()
    output = payload.get("output")
    if not video_id:
        raise ValueError(f"{path} is missing video_id")
    if not isinstance(output, dict) or not isinstance(output.get("review"), dict):
        raise ValueError(f"{path} is missing output.review")
    return video_id, output["review"]


def places_from_artifact(path: Path) -> tuple[str, str, list[dict[str, Any]]]:
    payload = successful_artifact(path, "place_verification")
    video_id = str(payload.get("video_id") or "").strip()
    output = payload.get("output")
    if not video_id:
        raise ValueError(f"{path} is missing video_id")
    if not isinstance(output, dict):
        raise ValueError(f"{path} is missing output object")
    items = output.get("items")
    if not isinstance(items, list):
        raise ValueError(f"{path} output.items must be a list")
    verified_at = str(output.get("verified_at") or payload.get("generated_at") or "")
    if not verified_at:
        raise ValueError(f"{path} is missing verified_at")
    return video_id, verified_at, [item for item in items if isinstance(item, dict)]


def youtube_video_exists(connection: sqlite3.Connection, video_id: str) -> bool:
    row = connection.execute(
        "select 1 from youtube_videos where video_id = ? limit 1",
        (video_id,),
    ).fetchone()
    return row is not None


def upsert_review_from_item(connection: sqlite3.Connection, video_id: str, item: dict[str, Any]) -> None:
    decision = str(item.get("decision") or "").strip()
    if decision not in {"restaurant_intro", "not_restaurant", "uncertain"}:
        raise ValueError(f"Review {video_id} has invalid decision {decision!r}")
    restaurant_names = item.get("restaurant_names", [])
    if not isinstance(restaurant_names, list):
        raise ValueError(f"Review {video_id} restaurant_names must be a list")
    detected_restaurant_count = item.get("detected_restaurant_count")
    if detected_restaurant_count is None:
        detected_restaurant_count = len(restaurant_names)
    detected_restaurant_count = int(detected_restaurant_count)
    if decision == "restaurant_intro" and detected_restaurant_count == 0:
        detected_restaurant_count = max(1, len(restaurant_names))
    connection.execute(
        """
        insert into agent_video_reviews (
          external_id,
          decision,
          confidence,
          restaurant_names,
          detected_restaurant_count,
          reason,
          reviewer,
          reviewed_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(external_id) do update set
          decision = excluded.decision,
          confidence = excluded.confidence,
          restaurant_names = excluded.restaurant_names,
          detected_restaurant_count = excluded.detected_restaurant_count,
          reason = excluded.reason,
          reviewer = excluded.reviewer,
          reviewed_at = excluded.reviewed_at
        """,
        (
            video_id,
            decision,
            float(item.get("confidence", 0)),
            json.dumps([str(name) for name in restaurant_names], ensure_ascii=False),
            detected_restaurant_count,
            str(item.get("reason") or ""),
            str(item.get("reviewer") or "codex"),
            str(item.get("reviewed_at") or item.get("generated_at") or ""),
        ),
    )


def upsert_story_from_item(connection: sqlite3.Connection, video_id: str, item: dict[str, Any]) -> None:
    for key in ("story_hook", "story_intro", "tasting_flow"):
        if not str(item.get(key) or "").strip():
            raise ValueError(f"Story review {video_id} is missing {key}")
    evidence = item.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError(f"Story review {video_id} evidence must be an object")
    validate_story_review_quality({"video_id": video_id, **item}, "story artifact")
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
            video_id,
            str(item["story_intro"]).strip(),
            str(item["tasting_flow"]).strip(),
            str(item["story_hook"]).strip(),
            str(item.get("reviewer") or "codex"),
            json.dumps(story_review_evidence(item), ensure_ascii=False),
            str(item.get("generated_at") or ""),
        ),
    )


def story_signature(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not value:
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def duplicate_story_signatures(story_items: list[tuple[Path, dict[str, Any]]]) -> set[str]:
    signatures = Counter(
        signature
        for _path, item in story_items
        for signature in (story_signature(item, "critic_rounds"), story_signature(item, "revision_history"))
        if signature
    )
    return {signature for signature, count in signatures.items() if count > 1}


def reduce_restaurant_review_artifact(
    connection: sqlite3.Connection,
    artifact_path: Path,
    *,
    apply: bool,
) -> ReductionResult:
    try:
        video_id, item = review_from_artifact(artifact_path)
        if not youtube_video_exists(connection, video_id):
            return ReductionResult(video_id, str(artifact_path), "skipped", "no matching youtube_video")
        if apply:
            upsert_review_from_item(connection, video_id, item)
        return ReductionResult(video_id, str(artifact_path), "applied" if apply else "planned")
    except Exception as error:  # noqa: BLE001
        return ReductionResult("", str(artifact_path), "invalid", f"{type(error).__name__}: {error}")


def reduce_transcript_artifact(
    connection: sqlite3.Connection,
    artifact_path: Path,
    *,
    apply: bool,
) -> ReductionResult:
    try:
        video_id, fetched_at, transcript = transcript_from_artifact(artifact_path)
        if not youtube_video_exists(connection, video_id):
            return ReductionResult(
                video_id=video_id,
                artifact_path=str(artifact_path),
                status="skipped",
                reason="no matching youtube_video",
            )
        if apply:
            upsert_transcript(connection, video_id, transcript, fetched_at)
            status = "applied"
        else:
            status = "planned"
        return ReductionResult(video_id=video_id, artifact_path=str(artifact_path), status=status)
    except Exception as error:  # noqa: BLE001 - reduction should report all artifact problems.
        return ReductionResult(
            video_id="",
            artifact_path=str(artifact_path),
            status="invalid",
            reason=f"{type(error).__name__}: {error}",
        )


def reduce_story_review_artifact(
    connection: sqlite3.Connection,
    artifact_path: Path,
    *,
    apply: bool,
    duplicate_signatures: set[str] | None = None,
) -> ReductionResult:
    try:
        video_id, item = story_from_artifact(artifact_path)
        if not youtube_video_exists(connection, video_id):
            return ReductionResult(video_id, str(artifact_path), "skipped", "no matching youtube_video")
        for key in ("critic_rounds", "revision_history"):
            signature = story_signature(item, key)
            if signature and duplicate_signatures and signature in duplicate_signatures:
                return ReductionResult(video_id, str(artifact_path), "invalid", f"duplicate {key} block in batch")
        if apply:
            upsert_story_from_item(connection, video_id, item)
        return ReductionResult(video_id, str(artifact_path), "applied" if apply else "planned")
    except Exception as error:  # noqa: BLE001
        return ReductionResult("", str(artifact_path), "invalid", f"{type(error).__name__}: {error}")


def reduce_place_verification_artifact(
    connection: sqlite3.Connection,
    artifact_path: Path,
    *,
    apply: bool,
) -> ReductionResult:
    try:
        video_id, verified_at, items = places_from_artifact(artifact_path)
        if not youtube_video_exists(connection, video_id):
            return ReductionResult(video_id, str(artifact_path), "skipped", "no matching youtube_video")
        if apply:
            youtube_video_id = get_youtube_video_id(connection, video_id)
            for item in items:
                naver_map_id, resolved_map_url = resolve_naver_map_details(item)
                resolved_item = {
                    **item,
                    "map_url": resolved_map_url,
                    "resolution_status": "selected" if naver_map_id else "needs_review",
                }
                upsert_place_resolution_candidate(connection, youtube_video_id, resolved_item, verified_at)
                if not naver_map_id:
                    continue
                restaurant_id = upsert_restaurant(connection, resolved_item, verified_at, naver_map_id)
                upsert_place_link(connection, restaurant_id, resolved_item, verified_at)
                upsert_video_restaurant(connection, restaurant_id, youtube_video_id, resolved_item, verified_at)
        return ReductionResult(video_id, str(artifact_path), "applied" if apply else "planned")
    except Exception as error:  # noqa: BLE001
        return ReductionResult("", str(artifact_path), "invalid", f"{type(error).__name__}: {error}")


def reduce_stage(
    connection: sqlite3.Connection,
    work_dir: Path,
    stage: str,
    *,
    apply: bool,
) -> list[ReductionResult]:
    reducers = {
        "restaurant_triage": reduce_restaurant_review_artifact,
        "transcript_fetch": reduce_transcript_artifact,
        "story_review": reduce_story_review_artifact,
        "place_verification": reduce_place_verification_artifact,
    }
    results = []
    duplicate_signatures: set[str] = set()
    if stage == "story_review":
        story_items: list[tuple[Path, dict[str, Any]]] = []
        for artifact_path in discover_artifacts(work_dir, stage):
            try:
                payload = load_json(artifact_path)
                if payload.get("status") != "succeeded":
                    continue
                _video_id, item = story_from_artifact(artifact_path)
                story_items.append((artifact_path, item))
            except Exception:
                continue
        duplicate_signatures = duplicate_story_signatures(story_items)
    for artifact_path in discover_artifacts(work_dir, stage):
        try:
            payload = load_json(artifact_path)
            status = payload.get("status")
            if status != "succeeded":
                video_id = str(payload.get("video_id") or "")
                results.append(
                    ReductionResult(
                        video_id,
                        str(artifact_path),
                        "skipped",
                        f"artifact status is {status!r}",
                    )
                )
                continue
        except Exception:
            pass
        if stage == "story_review":
            results.append(
                reduce_story_review_artifact(
                    connection,
                    artifact_path,
                    apply=apply,
                    duplicate_signatures=duplicate_signatures,
                )
            )
        else:
            results.append(reducers[stage](connection, artifact_path, apply=apply))
    return results


def reduce_artifacts(sqlite_path: Path, work_dir: Path, *, stage: str, apply: bool) -> list[ReductionResult]:
    stages = list(REDUCIBLE_STAGES) if stage == "all" else [stage]
    if apply:
        connection = sqlite3.connect(sqlite_path)
    else:
        connection = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    with connection:
        if apply:
            ensure_pipeline_schema(connection)
        results: list[ReductionResult] = []
        for current_stage in stages:
            results.extend(reduce_stage(connection, work_dir, current_stage, apply=apply))
    return results


def render_results(results: list[ReductionResult]) -> str:
    if not results:
        return "No reducible artifacts found."
    lines = []
    for result in results:
        details = result.reason or result.artifact_path
        video_id = result.video_id or "-"
        lines.append(f"{result.status}\t{video_id}\t{details}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reduce agent work artifacts into SQLite through a single writer."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--stage", choices=("all", *REDUCIBLE_STAGES), default="all")
    parser.add_argument("--apply", action="store_true", help="Apply reductions to SQLite.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    results = reduce_artifacts(args.sqlite, args.work_dir, stage=args.stage, apply=args.apply)

    if args.format == "json":
        print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))
    else:
        print(render_results(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
