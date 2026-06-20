#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_agent_reviews import DEFAULT_INPUT as DEFAULT_RESTAURANT_REVIEWS
from process_video_stories import (
    DEFAULT_LANGUAGES,
    DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS,
    DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS,
    MIN_STORY_INTRO_CHARS,
    MIN_TASTING_FLOW_CHARS,
    STORY_QUALITY_POLICY_VERSION,
    fetch_transcript,
    is_youtube_block_error,
    validate_story_review_quality,
)
from process_video_stories import DEFAULT_INPUT as DEFAULT_STORY_REVIEWS
from promote_verified_places import DEFAULT_INPUT_DIR as DEFAULT_VERIFIED_DIR


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_WORK_DIR = Path("data/work")
STORY_REVIEW_PROMPT_VERSION = "story-review-v3"

STAGES = {
    "place_extraction",
    "restaurant_triage",
    "transcript_fetch",
    "story_review",
    "place_verification",
}


@dataclass(frozen=True)
class StageTask:
    stage: str
    video_id: str
    source: str
    title: str
    reason: str
    input_artifacts: list[str]
    output_artifact: str


@dataclass(frozen=True)
class WorkerResult:
    stage: str
    video_id: str
    status: str
    output_artifact: str
    error: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def connect_readonly(path: Path) -> sqlite3.Connection:
    uri = f"file:{path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def task_output(work_dir: Path, video_id: str, filename: str) -> str:
    return str(work_dir / "videos" / video_id / filename)


def restaurant_triage_tasks(
    connection: sqlite3.Connection,
    *,
    work_dir: Path,
    limit: int,
) -> list[StageTask]:
    rows = connection.execute(
        """
        select
          c.video_id,
          s.name as source,
          c.title
        from youtube_videos c
        join sources s on s.id = c.source_id
        left join agent_video_reviews r on r.external_id = c.video_id
        where r.external_id is null
        order by c.published_at desc, c.id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [
        StageTask(
            stage="restaurant_triage",
            video_id=str(row["video_id"]),
            source=str(row["source"]),
            title=str(row["title"]),
            reason="collected video has no agent_video_reviews row",
            input_artifacts=["data/tastyroad.sqlite:youtube_videos"],
            output_artifact=task_output(work_dir, str(row["video_id"]), "restaurant_review.json"),
        )
        for row in rows
    ]


def transcript_fetch_tasks(
    connection: sqlite3.Connection,
    *,
    work_dir: Path,
    limit: int,
) -> list[StageTask]:
    rows = connection.execute(
        """
        select
          v.video_id,
          v.source,
          v.title
        from video_pipeline_status v
        left join video_transcripts t on t.external_id = v.video_id
        where v.review_decision = 'restaurant_intro'
          and t.external_id is null
        order by v.published_at desc, v.youtube_video_id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [
        StageTask(
            stage="transcript_fetch",
            video_id=str(row["video_id"]),
            source=str(row["source"]),
            title=str(row["title"]),
            reason="restaurant_intro video has no stored transcript",
            input_artifacts=["data/tastyroad.sqlite:video_pipeline_status"],
            output_artifact=task_output(work_dir, str(row["video_id"]), "transcript.json"),
        )
        for row in rows
    ]


def story_review_tasks(
    connection: sqlite3.Connection,
    *,
    work_dir: Path,
    limit: int,
) -> list[StageTask]:
    rows = connection.execute(
        """
        select
          v.video_id,
          v.source,
          v.title,
          case
            when r.external_id is null then 'transcript exists but video_story_reviews row is missing'
            when length(trim(r.story_intro)) < ? then 'existing story_intro is below current quality floor'
            when length(trim(r.tasting_flow)) < ? then 'existing tasting_flow is below current quality floor'
            when r.reviewer = 'codex-story-agent' then 'existing story came from legacy story agent batch'
            else 'existing story needs current policy refresh'
          end as reason
        from video_pipeline_status v
        join video_transcripts t on t.external_id = v.video_id
        left join video_story_reviews r on r.external_id = v.video_id
        where v.review_decision = 'restaurant_intro'
          and (
            r.external_id is null
            or length(trim(r.story_intro)) < ?
            or length(trim(r.tasting_flow)) < ?
            or r.reviewer = 'codex-story-agent'
          )
        order by v.published_at desc, v.youtube_video_id desc
        limit ?
        """,
        (
            MIN_STORY_INTRO_CHARS,
            MIN_TASTING_FLOW_CHARS,
            MIN_STORY_INTRO_CHARS,
            MIN_TASTING_FLOW_CHARS,
            limit,
        ),
    ).fetchall()
    return [
        StageTask(
            stage="story_review",
            video_id=str(row["video_id"]),
            source=str(row["source"]),
            title=str(row["title"]),
            reason=str(row["reason"]),
            input_artifacts=[
                "data/tastyroad.sqlite:video_pipeline_status",
                "data/tastyroad.sqlite:video_transcripts",
            ],
            output_artifact=task_output(work_dir, str(row["video_id"]), "story_review.json"),
        )
        for row in rows
    ]


def place_verification_tasks(
    connection: sqlite3.Connection,
    *,
    work_dir: Path,
    limit: int,
) -> list[StageTask]:
    rows = connection.execute(
        """
        select
          video_id,
          source,
          title,
          mapping_status
        from video_pipeline_status
        where review_decision = 'restaurant_intro'
          and mapping_status in ('mapping_pending', 'mapping_partial')
        order by published_at desc, youtube_video_id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [
        StageTask(
            stage="place_verification",
            video_id=str(row["video_id"]),
            source=str(row["source"]),
            title=str(row["title"]),
            reason=f"mapping status is {row['mapping_status']}",
            input_artifacts=[
                "data/tastyroad.sqlite:video_pipeline_status",
                "data/tastyroad.sqlite:place_resolution_candidates",
            ],
            output_artifact=task_output(work_dir, str(row["video_id"]), "place_verification.json"),
        )
        for row in rows
    ]


def place_extraction_tasks(
    connection: sqlite3.Connection,
    *,
    work_dir: Path,
    limit: int,
) -> list[StageTask]:
    rows = connection.execute(
        """
        select
          video_id,
          source,
          title,
          mapping_status
        from video_pipeline_status
        where review_decision = 'restaurant_intro'
          and mapping_status in ('mapping_pending', 'mapping_partial')
        order by published_at desc, youtube_video_id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [
        StageTask(
            stage="place_extraction",
            video_id=str(row["video_id"]),
            source=str(row["source"]),
            title=str(row["title"]),
            reason=f"place candidates needed before verification; mapping status is {row['mapping_status']}",
            input_artifacts=[
                "data/tastyroad.sqlite:video_pipeline_status",
                "data/work/videos/{video_id}/story_review.json",
            ],
            output_artifact=task_output(work_dir, str(row["video_id"]), "place_candidates.json"),
        )
        for row in rows
    ]


def plan_tasks(
    sqlite_path: Path,
    *,
    work_dir: Path,
    limit: int,
    stage: str | None = None,
    video_id: str | None = None,
) -> list[StageTask]:
    if stage is not None and stage not in STAGES:
        raise ValueError(f"Unknown stage {stage!r}; expected one of {sorted(STAGES)}")

    planners = {
        "place_extraction": place_extraction_tasks,
        "restaurant_triage": restaurant_triage_tasks,
        "transcript_fetch": transcript_fetch_tasks,
        "story_review": story_review_tasks,
        "place_verification": place_verification_tasks,
    }

    with connect_readonly(sqlite_path) as connection:
        selected = [stage] if stage else list(planners.keys())
        if video_id:
            row = connection.execute(
                """
                select
                  c.video_id,
                  s.name as source,
                  c.title
                from youtube_videos c
                join sources s on s.id = c.source_id
                where c.video_id = ?
                """,
                (video_id,),
            ).fetchone()
            if row is None:
                return []
            filenames = {
                "place_extraction": "place_candidates.json",
                "place_verification": "place_verification.json",
                "restaurant_triage": "restaurant_review.json",
                "story_review": "story_review.json",
                "transcript_fetch": "transcript.json",
            }
            return [
                StageTask(
                    stage=current_stage,
                    video_id=str(row["video_id"]),
                    source=str(row["source"]),
                    title=str(row["title"]),
                    reason="forced by --video-id",
                    input_artifacts=[f"data/tastyroad.sqlite:{current_stage}"],
                    output_artifact=task_output(
                        work_dir,
                        str(row["video_id"]),
                        filenames[current_stage],
                    ),
                )
                for current_stage in selected
            ]
        tasks: list[StageTask] = []
        for current_stage in selected:
            tasks.extend(planners[current_stage](connection, work_dir=work_dir, limit=limit))
    return tasks


def render_text(tasks: list[StageTask]) -> str:
    if not tasks:
        return "No stage tasks are currently planned."
    lines = []
    for task in tasks:
        lines.append(
            f"{task.stage}\t{task.video_id}\t{task.source}\t{task.reason}\t{task.title}"
        )
    return "\n".join(lines)


def run_payload(sqlite_path: Path, work_dir: Path, tasks: list[StageTask]) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "run_id": now_compact(),
        "generated_at": generated_at,
        "sqlite_path": str(sqlite_path),
        "work_dir": str(work_dir),
        "task_count": len(tasks),
        "tasks": [asdict(task) for task in tasks],
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def list_items(payload: Any, key: str) -> list[dict[str, Any]]:
    items = payload.get(key, []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def find_item_by_video_id(items: list[dict[str, Any]], video_id: str) -> dict[str, Any] | None:
    for item in items:
        current_video_id = str(item.get("video_id") or item.get("external_id") or "").strip()
        if current_video_id == video_id:
            return item
    return None


def load_verified_payloads(input_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    if not input_dir.exists():
        return []
    payloads = []
    for path in sorted(input_dir.glob("*.json")):
        payload = load_json(path)
        if isinstance(payload, dict):
            payloads.append((path, payload))
    return payloads


def verified_items_for_video(input_dir: Path, video_id: str) -> tuple[str, list[dict[str, Any]], list[str]]:
    verified_at = ""
    matched_items: list[dict[str, Any]] = []
    sources: list[str] = []
    for path, payload in load_verified_payloads(input_dir):
        items = [
            item for item in list_items(payload, "items")
            if str(item.get("video_id") or "").strip() == video_id
        ]
        if items:
            verified_at = str(payload.get("verified_at") or verified_at)
            matched_items.extend(items)
            sources.append(str(path))
    return verified_at, matched_items, sources


def video_context(sqlite_path: Path, video_id: str) -> dict[str, Any]:
    with connect_readonly(sqlite_path) as connection:
        row = connection.execute(
            """
            select
              c.video_id,
              s.name as source,
              s.trust_tier,
              c.title,
              c.url,
              c.thumbnail_url,
              c.published_at,
              c.description,
              c.duration_seconds,
              c.tags,
              c.chapters,
              c.raw_restaurant_name_candidates
            from youtube_videos c
            join sources s on s.id = c.source_id
            where c.video_id = ?
            """,
            (video_id,),
        ).fetchone()
    if row is None:
        return {"video_id": video_id}
    return {
        "video_id": str(row["video_id"]),
        "source": str(row["source"]),
        "trust_tier": str(row["trust_tier"]),
        "title": str(row["title"]),
        "url": str(row["url"]),
        "thumbnail_url": str(row["thumbnail_url"] or ""),
        "published_at": str(row["published_at"]),
        "description": str(row["description"] or ""),
        "duration_seconds": row["duration_seconds"],
        "tags": parse_json_value(row["tags"], []),
        "chapters": parse_json_value(row["chapters"], []),
        "raw_restaurant_name_candidates": parse_json_value(
            row["raw_restaurant_name_candidates"],
            [],
        ),
    }


def parse_json_value(raw_value: Any, default: Any) -> Any:
    try:
        return json.loads(str(raw_value or ""))
    except json.JSONDecodeError:
        return default


def transcript_context(sqlite_path: Path, work_dir: Path, video_id: str) -> dict[str, Any]:
    artifact_path = work_dir / "videos" / video_id / "transcript.json"
    artifact = load_json(artifact_path)
    if isinstance(artifact, dict) and artifact.get("status") == "succeeded":
        output = artifact.get("output")
        if isinstance(output, dict):
            return {
                "source": str(artifact_path),
                "language_code": output.get("language_code"),
                "language": output.get("language"),
                "is_generated": output.get("is_generated"),
                "text": output.get("text", ""),
                "segments": output.get("segments", []),
            }

    with connect_readonly(sqlite_path) as connection:
        row = connection.execute(
            """
            select language_code, language, is_generated, transcript_text, transcript_json
            from video_transcripts
            where external_id = ?
            """,
            (video_id,),
        ).fetchone()
    if row is None:
        return {"source": "", "text": "", "segments": []}
    return {
        "source": "data/tastyroad.sqlite:video_transcripts",
        "language_code": str(row["language_code"]),
        "language": str(row["language"]),
        "is_generated": bool(row["is_generated"]),
        "text": str(row["transcript_text"] or ""),
        "segments": parse_json_value(row["transcript_json"], []),
    }


def story_context(sqlite_path: Path, work_dir: Path, video_id: str) -> dict[str, Any]:
    artifact_path = work_dir / "videos" / video_id / "story_review.json"
    artifact = load_json(artifact_path)
    if isinstance(artifact, dict) and artifact.get("status") == "succeeded":
        output = artifact.get("output")
        if isinstance(output, dict) and isinstance(output.get("review"), dict):
            return {"source": str(artifact_path), **output["review"]}

    with connect_readonly(sqlite_path) as connection:
        row = connection.execute(
            """
            select story_hook, story_intro, tasting_flow, evidence_json
            from video_story_reviews
            where external_id = ?
            """,
            (video_id,),
        ).fetchone()
    if row is None:
        return {"source": ""}
    return {
        "source": "data/tastyroad.sqlite:video_story_reviews",
        "story_hook": str(row["story_hook"]),
        "story_intro": str(row["story_intro"]),
        "tasting_flow": str(row["tasting_flow"]),
        "evidence": parse_json_value(row["evidence_json"], {}),
    }


def pending_agent_artifact(
    task: StageTask,
    *,
    prompt: str,
    context: dict[str, Any],
    expected_output: dict[str, Any],
    input_artifacts: list[str],
) -> dict[str, Any]:
    return stage_artifact(
        task,
        status="needs_agent",
        output={
            "prompt": prompt,
            "context": context,
            "expected_output": expected_output,
        },
        input_artifacts=input_artifacts,
    )


def render_json_block(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def render_task_md(payload: dict[str, Any]) -> str:
    output = payload.get("output") if isinstance(payload.get("output"), dict) else {}
    context = output.get("context", {})
    expected_output = output.get("expected_output", {})
    prompt = str(output.get("prompt") or "")
    return f"""# {payload.get("stage")} Task

## Video

- Video ID: `{payload.get("video_id")}`
- Source: {payload.get("source")}
- Title: {payload.get("title")}

## Instructions

{prompt}

## Operating Rules

- Work from this Markdown task and the supporting `context.json`.
- Do not write to SQLite.
- Put human-readable reasoning and evidence in `result.md`.
- Put reducer-ready structured output in `result.json`.
- If evidence is weak, use `uncertain`, `needs_review`, or `rejected` rather than inventing facts.
- Preserve the expected JSON shape unless there is a documented reason not to.

## Context Summary

```json
{render_json_block(context)}
```

## Required JSON Output

Write this shape to `result.json`:

```json
{render_json_block(expected_output)}
```
"""


def render_result_md_template(payload: dict[str, Any]) -> str:
    return f"""# {payload.get("stage")} Result

## Decision

TBD

## Evidence

- TBD

## Notes

- Video ID: `{payload.get("video_id")}`
- Artifact: `{payload.get("stage")}`
"""


def write_agent_workspace(output_path: Path, payload: dict[str, Any]) -> None:
    output = payload.get("output") if isinstance(payload.get("output"), dict) else {}
    workspace_dir = output_path.parent
    write_text(workspace_dir / "task.md", render_task_md(payload))
    write_payload(workspace_dir / "context.json", output.get("context", {}))
    write_text(workspace_dir / "result.md", render_result_md_template(payload))
    write_payload(workspace_dir / "result.json", output.get("expected_output", {}))

    payload.setdefault("input", {})
    if isinstance(payload["input"], dict):
        payload["input"]["workspace"] = {
            "task": str(workspace_dir / "task.md"),
            "context": str(workspace_dir / "context.json"),
            "result_markdown": str(workspace_dir / "result.md"),
            "result_json": str(workspace_dir / "result.json"),
        }


def write_needs_agent_artifact(output_path: Path, payload: dict[str, Any]) -> None:
    write_agent_workspace(output_path, payload)
    write_payload(output_path, payload)


def restaurant_triage_prompt() -> str:
    return (
        "Decide whether this YouTube video is a restaurant-introduction video. "
        "Return only structured JSON matching expected_output. Do not mark a video "
        "as restaurant_intro unless the video appears to introduce at least one real place."
    )


def story_review_prompt() -> str:
    return (
        "Run a writer-critic-revision loop for a Korean story review from the transcript. "
        "Treat transcript/video dialogue as the material for public prose. Treat metadata, "
        "descriptions, map links, addresses, source URLs, and verification notes only as "
        "private provenance for evidence. Never mention the data source, description field, "
        "metadata, map provider, address, source link, or verification process in story_hook, "
        "story_intro, or tasting_flow. Put those details only in evidence.provenance when needed. "
        "Writer: first extract the factual tasting order as a list before writing prose. "
        "Then find why the host chose this place, prior memories or relationships, stated "
        "owner/store context, and what the restaurant is proud of. Critic: be strict and "
        "do not pass quickly. Run at least three closed-loop critic rounds. Rounds 1 and "
        "2 must be revise rounds with concrete required_changes, and the writer must respond "
        "to each round before the next critique. The final round may pass only if every check "
        "is true and issues is empty. Reject if tasting_flow does not say what was eaten in "
        "order, if public prose contains provenance/source-tracing language, if the prose repeats "
        "the same idea, if subjects are vague, if Korean sentences are awkward, or if the writing "
        "uses padded phrases. Prefer plain, clear Korean: short sentences, concrete nouns, no "
        "decoration, no grand claims. Do not imitate any named writer; aim for clean civic prose. "
        "Never use generic template text such as '자막 기준으로', "
        "'한 끼 후보', '메뉴의 첫인상', '쪽에 가깝다', or '매력으로 남는다'. Return only "
        "structured JSON matching expected_output."
    )


def prompt_version_for_stage(stage: str) -> str | None:
    if stage == "story_review":
        return STORY_REVIEW_PROMPT_VERSION
    return None


def place_extraction_prompt() -> str:
    return (
        "Extract candidate places from the video metadata, transcript, and story review. "
        "Separate uncertain candidates from verified places. Return only structured JSON."
    )


def place_verification_prompt() -> str:
    return (
        "Verify extracted place candidates against Naver Map evidence. Return a restaurant "
        "item only when you have a concrete Naver place ID, entry URL, name, and address. "
        "Do not invent addresses, place IDs, or provider links. Return only structured JSON "
        "matching expected_output."
    )


def stage_artifact(
    task: StageTask,
    *,
    status: str,
    output: Any,
    input_artifacts: list[str] | None = None,
    error: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "stage": task.stage,
        "status": status,
        "video_id": task.video_id,
        "source": task.source,
        "title": task.title,
        "generated_at": now_iso(),
        "worker": {
            "name": task.stage,
            "implementation": "tastyroad-data-pipeline.agent_pipeline",
            "prompt_version": prompt_version_for_stage(task.stage),
            "model": None,
        },
        "input": {
            "input_artifacts": input_artifacts or task.input_artifacts,
        },
        "output": output,
        "error": error,
    }


def transcript_artifact(task: StageTask, transcript: Any, *, languages: tuple[str, ...]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "stage": "transcript_fetch",
        "status": "succeeded",
        "video_id": task.video_id,
        "source": task.source,
        "title": task.title,
        "fetched_at": now_iso(),
        "worker": {
            "name": "transcript_fetch",
            "implementation": "tastyroad-data-pipeline.agent_pipeline",
            "prompt_version": None,
            "model": None,
        },
        "input": {
            "languages": list(languages),
            "input_artifacts": task.input_artifacts,
        },
        "output": {
            "language_code": transcript.language_code,
            "language": transcript.language,
            "is_generated": transcript.is_generated,
            "segments": transcript.segments,
            "text": transcript.text,
            "text_length": len(transcript.text),
            "segment_count": len(transcript.segments),
        },
        "error": None,
    }


def failed_artifact(task: StageTask, error: Exception, *, languages: tuple[str, ...]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "stage": task.stage,
        "status": "failed",
        "video_id": task.video_id,
        "source": task.source,
        "title": task.title,
        "fetched_at": now_iso(),
        "worker": {
            "name": task.stage,
            "implementation": "tastyroad-data-pipeline.agent_pipeline",
            "prompt_version": None,
            "model": None,
        },
        "input": {
            "languages": list(languages),
            "input_artifacts": task.input_artifacts,
        },
        "output": None,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        },
    }


def run_seed_item_task(
    task: StageTask,
    *,
    output_path: Path,
    item: dict[str, Any] | None,
    output_key: str,
    input_artifacts: list[str],
    refresh: bool,
) -> WorkerResult:
    if output_path.exists() and not refresh:
        return WorkerResult(task.stage, task.video_id, "skipped_existing", str(output_path))
    if item is None:
        error = {"type": "MissingSeed", "message": f"No seed item found for video_id={task.video_id}"}
        write_payload(
            output_path,
            stage_artifact(task, status="failed", output=None, input_artifacts=input_artifacts, error=error),
        )
        return WorkerResult(task.stage, task.video_id, "failed", str(output_path), error["message"])
    write_payload(
        output_path,
        stage_artifact(
            task,
            status="succeeded",
            output={output_key: item},
            input_artifacts=input_artifacts,
        ),
    )
    return WorkerResult(task.stage, task.video_id, "succeeded", str(output_path))


def run_restaurant_triage_task(
    task: StageTask,
    *,
    sqlite_path: Path,
    reviews_input: Path,
    refresh: bool,
) -> WorkerResult:
    output_path = Path(task.output_artifact)
    if output_path.exists() and not refresh:
        return WorkerResult(task.stage, task.video_id, "skipped_existing", str(output_path))
    items = list_items(load_json(reviews_input), "reviews")
    item = find_item_by_video_id(items, task.video_id)
    if item is None:
        context = video_context(sqlite_path, task.video_id)
        write_needs_agent_artifact(
            output_path,
            pending_agent_artifact(
                task,
                prompt=restaurant_triage_prompt(),
                context=context,
                expected_output={
                    "video_id": task.video_id,
                    "decision": "restaurant_intro | not_restaurant | uncertain",
                    "confidence": 0.0,
                    "restaurant_names": [],
                    "detected_restaurant_count": 0,
                    "reason": "",
                    "reviewer": "agent",
                    "reviewed_at": now_iso(),
                },
                input_artifacts=["data/tastyroad.sqlite:youtube_videos"],
            ),
        )
        return WorkerResult(task.stage, task.video_id, "needs_agent", str(output_path))
    return run_seed_item_task(
        task,
        output_path=output_path,
        item=item,
        output_key="review",
        input_artifacts=[str(reviews_input)],
        refresh=refresh,
    )


def run_transcript_fetch_task(
    task: StageTask,
    *,
    languages: tuple[str, ...],
    refresh: bool,
) -> WorkerResult:
    output_path = Path(task.output_artifact)
    if output_path.exists() and not refresh:
        return WorkerResult(
            stage=task.stage,
            video_id=task.video_id,
            status="skipped_existing",
            output_artifact=str(output_path),
        )

    try:
        transcript = fetch_transcript(task.video_id, languages)
        write_payload(output_path, transcript_artifact(task, transcript, languages=languages))
        return WorkerResult(
            stage=task.stage,
            video_id=task.video_id,
            status="succeeded",
            output_artifact=str(output_path),
        )
    except Exception as error:  # noqa: BLE001 - transcript availability varies by video.
        write_payload(output_path, failed_artifact(task, error, languages=languages))
        return WorkerResult(
            stage=task.stage,
            video_id=task.video_id,
            status="failed",
            output_artifact=str(output_path),
            error=str(error),
        )


def run_story_review_task(
    task: StageTask,
    *,
    sqlite_path: Path,
    work_dir: Path,
    story_input: Path,
    refresh: bool,
) -> WorkerResult:
    output_path = Path(task.output_artifact)
    if output_path.exists() and not refresh:
        existing = load_json(output_path)
        worker = existing.get("worker") if isinstance(existing, dict) else {}
        current_prompt = (
            isinstance(worker, dict)
            and worker.get("prompt_version") == STORY_REVIEW_PROMPT_VERSION
        )
        if current_prompt:
            output = existing.get("output") if isinstance(existing, dict) else {}
            review = output.get("review") if isinstance(output, dict) else None
            if existing.get("status") == "succeeded" and isinstance(review, dict):
                try:
                    validate_story_review_quality(review, str(output_path))
                except ValueError:
                    pass
                else:
                    return WorkerResult(task.stage, task.video_id, "skipped_existing", str(output_path))
            elif existing.get("status") in {"needs_agent", "claimed"}:
                return WorkerResult(task.stage, task.video_id, "skipped_existing", str(output_path))
    items = list_items(load_json(story_input), "reviews")
    item = find_item_by_video_id(items, task.video_id)
    if item is None:
        context = {
            "video": video_context(sqlite_path, task.video_id),
            "transcript": transcript_context(sqlite_path, work_dir, task.video_id),
        }
        write_needs_agent_artifact(
            output_path,
            pending_agent_artifact(
                task,
                prompt=story_review_prompt(),
                context=context,
                expected_output={
                    "video_id": task.video_id,
                    "story_hook": "",
                    "story_intro": "",
                    "tasting_flow": "",
                    "reviewer": "agent",
                    "evidence": {
                        "quality_policy_version": STORY_QUALITY_POLICY_VERSION,
                        "host_reason": "",
                        "store_context": "",
                        "tasting_order": [],
                        "transcript_support": [],
                        "provenance": {
                            "public_story_sources": ["transcript"],
                            "private_verification_sources": [],
                            "notes": "",
                        },
                    },
                    "critic_rounds": [
                        {
                            "round": 1,
                            "decision": "revise",
                            "checks": {
                                "tasting_order_present": False,
                                "tasting_order_matches_transcript": False,
                                "host_reason_specific": False,
                                "store_context_specific": False,
                                "plain_korean": False,
                                "clear_subjects": False,
                                "no_duplicate_context": False,
                                "no_generic_phrasing": False,
                                "no_public_provenance": False,
                            },
                            "issues": [],
                            "required_changes": [],
                            "writer_response": "",
                        },
                        {
                            "round": 2,
                            "decision": "revise",
                            "checks": {
                                "tasting_order_present": False,
                                "tasting_order_matches_transcript": False,
                                "host_reason_specific": False,
                                "store_context_specific": False,
                                "plain_korean": False,
                                "clear_subjects": False,
                                "no_duplicate_context": False,
                                "no_generic_phrasing": False,
                                "no_public_provenance": False,
                            },
                            "issues": [],
                            "required_changes": [],
                            "writer_response": "",
                        },
                        {
                            "round": 3,
                            "decision": "pass | revise | reject",
                            "checks": {
                                "tasting_order_present": False,
                                "tasting_order_matches_transcript": False,
                                "host_reason_specific": False,
                                "store_context_specific": False,
                                "plain_korean": False,
                                "clear_subjects": False,
                                "no_duplicate_context": False,
                                "no_generic_phrasing": False,
                                "no_public_provenance": False,
                            },
                            "issues": [],
                            "required_changes": [],
                            "writer_response": "",
                        },
                    ],
                    "revision_history": [
                        {
                            "role": "writer",
                            "summary": "initial draft and extracted tasting order",
                        },
                        {
                            "role": "critic",
                            "summary": "round 1 critique and required changes",
                        },
                        {
                            "role": "writer",
                            "summary": "revision after round 1",
                        },
                        {
                            "role": "critic",
                            "summary": "round 2 critique and required changes",
                        },
                        {
                            "role": "writer",
                            "summary": "revision after round 2 and final critic response",
                        },
                    ],
                    "generated_at": now_iso(),
                },
                input_artifacts=[
                    "data/tastyroad.sqlite:youtube_videos",
                    "data/work/videos/{video_id}/transcript.json",
                    "data/tastyroad.sqlite:video_transcripts",
                ],
            ),
        )
        return WorkerResult(task.stage, task.video_id, "needs_agent", str(output_path))
    return run_seed_item_task(
        task,
        output_path=output_path,
        item=item,
        output_key="review",
        input_artifacts=[str(story_input)],
        refresh=refresh,
    )


def run_place_extraction_task(
    task: StageTask,
    *,
    sqlite_path: Path,
    work_dir: Path,
    verified_dir: Path,
    refresh: bool,
) -> WorkerResult:
    output_path = Path(task.output_artifact)
    if output_path.exists() and not refresh:
        return WorkerResult(task.stage, task.video_id, "skipped_existing", str(output_path))
    _verified_at, items, sources = verified_items_for_video(verified_dir, task.video_id)
    if not items:
        write_needs_agent_artifact(
            output_path,
            pending_agent_artifact(
                task,
                prompt=place_extraction_prompt(),
                context={
                    "video": video_context(sqlite_path, task.video_id),
                    "story_review": story_context(sqlite_path, work_dir, task.video_id),
                    "transcript": transcript_context(sqlite_path, work_dir, task.video_id),
                },
                expected_output={
                    "video_id": task.video_id,
                    "candidates": [
                        {
                            "name": "",
                            "region": "",
                            "address_hint": "",
                            "category": "",
                            "confidence": 0.0,
                            "evidence": [],
                            "status": "candidate | needs_review",
                        }
                    ],
                },
                input_artifacts=[
                    "data/tastyroad.sqlite:youtube_videos",
                    "data/work/videos/{video_id}/story_review.json",
                    "data/work/videos/{video_id}/transcript.json",
                ],
            ),
        )
        return WorkerResult(task.stage, task.video_id, "needs_agent", str(output_path))

    candidates = [
        {
            "name": item.get("display_name") or item.get("resolved_name"),
            "resolved_name": item.get("resolved_name"),
            "region": item.get("region"),
            "address_hint": item.get("address"),
            "category": item.get("category"),
            "confidence": item.get("confidence"),
            "evidence_url": item.get("evidence_url"),
            "notes": item.get("notes"),
        }
        for item in items
    ]
    write_payload(
        output_path,
        stage_artifact(
            task,
            status="succeeded",
            output={"candidates": candidates},
            input_artifacts=sources or [str(verified_dir)],
        ),
    )
    return WorkerResult(task.stage, task.video_id, "succeeded", str(output_path))


def run_place_verification_task(
    task: StageTask,
    *,
    sqlite_path: Path,
    work_dir: Path,
    verified_dir: Path,
    refresh: bool,
) -> WorkerResult:
    output_path = Path(task.output_artifact)
    if output_path.exists() and not refresh:
        return WorkerResult(task.stage, task.video_id, "skipped_existing", str(output_path))
    verified_at, items, sources = verified_items_for_video(verified_dir, task.video_id)
    if not items:
        candidates_artifact = load_json(work_dir / "videos" / task.video_id / "place_candidates.json")
        write_needs_agent_artifact(
            output_path,
            pending_agent_artifact(
                task,
                prompt=place_verification_prompt(),
                context={
                    "video": video_context(sqlite_path, task.video_id),
                    "place_candidates_artifact": candidates_artifact,
                },
                expected_output={
                    "verified_at": now_iso(),
                    "items": [
                        {
                            "video_id": task.video_id,
                            "resolved_name": "",
                            "display_name": "",
                            "local_name": None,
                            "country_code": "",
                            "region": "",
                            "address": "",
                            "phone": None,
                            "category": "",
                            "map_provider": "naver_map",
                            "naver_map_id": "",
                            "map_url": "",
                            "evidence_url": "",
                            "confidence": 0.0,
                            "status": "metadata_verified | needs_review | rejected",
                            "notes": "",
                        }
                    ],
                },
                input_artifacts=[
                    "data/work/videos/{video_id}/place_candidates.json",
                    "data/tastyroad.sqlite:restaurants",
                    "data/tastyroad.sqlite:place_links",
                ],
            ),
        )
        return WorkerResult(task.stage, task.video_id, "needs_agent", str(output_path))
    write_payload(
        output_path,
        stage_artifact(
            task,
            status="succeeded",
            output={"verified_at": verified_at or now_iso(), "items": items},
            input_artifacts=sources or [str(verified_dir)],
        ),
    )
    return WorkerResult(task.stage, task.video_id, "succeeded", str(output_path))


def run_tasks(
    tasks: list[StageTask],
    *,
    languages: tuple[str, ...],
    refresh: bool,
    sqlite_path: Path,
    work_dir: Path,
    reviews_input: Path,
    story_input: Path,
    verified_dir: Path,
    transcript_request_delay_seconds: float = DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS,
    max_consecutive_transcript_blocks: int = DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS,
) -> list[WorkerResult]:
    results: list[WorkerResult] = []
    consecutive_transcript_blocks = 0
    for index, task in enumerate(tasks, start=1):
        if task.stage == "restaurant_triage":
            results.append(
                run_restaurant_triage_task(
                    task,
                    sqlite_path=sqlite_path,
                    reviews_input=reviews_input,
                    refresh=refresh,
                )
            )
        elif task.stage == "transcript_fetch":
            result = run_transcript_fetch_task(task, languages=languages, refresh=refresh)
            results.append(result)
            if result.error and is_youtube_block_error(result.error):
                consecutive_transcript_blocks += 1
                if (
                    max_consecutive_transcript_blocks > 0
                    and consecutive_transcript_blocks >= max_consecutive_transcript_blocks
                ):
                    print(
                        "Stopping transcript fetch after "
                        f"{consecutive_transcript_blocks} consecutive YouTube block errors.",
                        flush=True,
                    )
                    break
            elif result.status == "succeeded":
                consecutive_transcript_blocks = 0
            has_more_transcript_tasks = any(
                pending_task.stage == "transcript_fetch" for pending_task in tasks[index:]
            )
            if transcript_request_delay_seconds > 0 and has_more_transcript_tasks:
                print(
                    f"Waiting {transcript_request_delay_seconds:g}s before the next transcript request...",
                    flush=True,
                )
                time.sleep(transcript_request_delay_seconds)
        elif task.stage == "story_review":
            results.append(
                run_story_review_task(
                    task,
                    sqlite_path=sqlite_path,
                    work_dir=work_dir,
                    story_input=story_input,
                    refresh=refresh,
                )
            )
        elif task.stage == "place_extraction":
            results.append(
                run_place_extraction_task(
                    task,
                    sqlite_path=sqlite_path,
                    work_dir=work_dir,
                    verified_dir=verified_dir,
                    refresh=refresh,
                )
            )
        elif task.stage == "place_verification":
            results.append(
                run_place_verification_task(
                    task,
                    sqlite_path=sqlite_path,
                    work_dir=work_dir,
                    verified_dir=verified_dir,
                    refresh=refresh,
                )
            )
        else:
            raise ValueError(f"Running stage {task.stage!r} is not implemented")
    return results


def render_results(results: list[WorkerResult]) -> str:
    if not results:
        return "No stage tasks were run."
    lines = []
    for result in results:
        suffix = f"\t{result.error}" if result.error else ""
        lines.append(
            f"{result.stage}\t{result.video_id}\t{result.status}\t{result.output_artifact}{suffix}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan stage-based multi-agent pipeline tasks without mutating SQLite."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--stage", choices=sorted(STAGES))
    parser.add_argument("--video-id", help="Force a task for one existing YouTube video.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run planned worker tasks.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Overwrite existing work artifacts when running worker tasks.",
    )
    parser.add_argument(
        "--languages",
        default=",".join(DEFAULT_LANGUAGES),
        help="Comma-separated transcript language preference list.",
    )
    parser.add_argument("--reviews-input", type=Path, default=DEFAULT_RESTAURANT_REVIEWS)
    parser.add_argument("--story-input", type=Path, default=DEFAULT_STORY_REVIEWS)
    parser.add_argument("--verified-dir", type=Path, default=DEFAULT_VERIFIED_DIR)
    parser.add_argument(
        "--request-delay",
        type=float,
        default=DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS,
        help=(
            "Seconds to wait between transcript requests. "
            f"Default: {DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS:g}"
        ),
    )
    parser.add_argument(
        "--max-consecutive-blocks",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS,
        help=(
            "Stop transcript fetching after this many consecutive YouTube block errors. "
            f"Default: {DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS}"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a run plan JSON file, for example data/work/runs/latest.json.",
    )
    args = parser.parse_args()

    tasks = plan_tasks(
        args.sqlite,
        work_dir=args.work_dir,
        limit=args.limit,
        stage=args.stage,
        video_id=args.video_id,
    )
    payload = run_payload(args.sqlite, args.work_dir, tasks)

    if args.output:
        write_payload(args.output, payload)

    if args.run:
        if not args.stage:
            raise ValueError("--run requires --stage so one worker type runs at a time")
        languages = tuple(
            language.strip() for language in args.languages.split(",") if language.strip()
        )
        if not languages:
            raise ValueError("--languages must include at least one language code")
        results = run_tasks(
            tasks,
            languages=languages,
            refresh=args.refresh,
            sqlite_path=args.sqlite,
            work_dir=args.work_dir,
            reviews_input=args.reviews_input,
            story_input=args.story_input,
            verified_dir=args.verified_dir,
            transcript_request_delay_seconds=args.request_delay,
            max_consecutive_transcript_blocks=args.max_consecutive_blocks,
        )
        run_result_payload = {
            **payload,
            "results": [asdict(result) for result in results],
        }
        if args.format == "json":
            print(json.dumps(run_result_payload, ensure_ascii=False, indent=2))
        else:
            print(render_results(results))
        return 0

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(tasks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
