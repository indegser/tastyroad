#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from agent_inbox import discover_inbox
from agent_pipeline import (
    DEFAULT_SQLITE,
    DEFAULT_WORK_DIR,
    DEFAULT_RESTAURANT_REVIEWS,
    DEFAULT_STORY_REVIEWS,
    DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS,
    DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS,
    DEFAULT_VERIFIED_DIR,
    DEFAULT_LANGUAGES,
    STAGES,
    StageTask,
    WorkerResult,
    plan_tasks,
    render_results,
    render_text,
    run_tasks,
)
from reduce_agent_artifacts import ReductionResult, reduce_artifacts, render_results as render_reductions


STAGE_ORDER = (
    "restaurant_triage",
    "transcript_fetch",
    "story_review",
    "place_extraction",
    "place_verification",
)


@dataclass(frozen=True)
class StageRun:
    stage: str
    planned: list[StageTask]
    worker_results: list[WorkerResult]


@dataclass(frozen=True)
class OrchestrationResult:
    stages: list[StageRun]
    inbox: list[Any]
    reductions: list[ReductionResult]


def selected_stages(stage: str | None) -> list[str]:
    if stage:
        if stage not in STAGES:
            raise ValueError(f"Unknown stage {stage!r}; expected one of {sorted(STAGES)}")
        return [stage]
    return list(STAGE_ORDER)


def orchestrate(
    *,
    sqlite_path: Path,
    work_dir: Path,
    limit: int,
    stage: str | None,
    video_id: str | None,
    run_workers: bool,
    reduce: bool,
    apply: bool,
    refresh: bool,
    languages: tuple[str, ...],
    reviews_input: Path,
    story_input: Path,
    verified_dir: Path,
    transcript_request_delay_seconds: float,
    max_consecutive_transcript_blocks: int,
) -> OrchestrationResult:
    stage_runs: list[StageRun] = []
    for current_stage in selected_stages(stage):
        tasks = plan_tasks(
            sqlite_path,
            work_dir=work_dir,
            limit=limit,
            stage=current_stage,
            video_id=video_id,
        )
        worker_results: list[WorkerResult] = []
        if run_workers and tasks:
            worker_results = run_tasks(
                tasks,
                languages=languages,
                refresh=refresh,
                sqlite_path=sqlite_path,
                work_dir=work_dir,
                reviews_input=reviews_input,
                story_input=story_input,
                verified_dir=verified_dir,
                transcript_request_delay_seconds=transcript_request_delay_seconds,
                max_consecutive_transcript_blocks=max_consecutive_transcript_blocks,
            )
        stage_runs.append(StageRun(current_stage, tasks, worker_results))

    reductions: list[ReductionResult] = []
    if reduce or apply:
        reductions = reduce_artifacts(
            sqlite_path,
            work_dir,
            stage=stage or "all",
            apply=apply,
        )

    return OrchestrationResult(
        stages=stage_runs,
        inbox=discover_inbox(work_dir, stage=stage),
        reductions=reductions,
    )


def render_text_result(result: OrchestrationResult) -> str:
    blocks: list[str] = []
    for stage_run in result.stages:
        blocks.append(f"## {stage_run.stage}")
        blocks.append(render_text(stage_run.planned))
        if stage_run.worker_results:
            blocks.append("")
            blocks.append(render_results(stage_run.worker_results))
        blocks.append("")

    blocks.append("## inbox")
    if result.inbox:
        blocks.extend(
            f"{item.status}\t{item.stage}\t{item.video_id}\t{item.artifact_path}\t{item.title}"
            for item in result.inbox
        )
    else:
        blocks.append("No needs_agent or claimed artifacts found.")

    if result.reductions:
        blocks.append("")
        blocks.append("## reductions")
        blocks.append(render_reductions(result.reductions))
    return "\n".join(blocks).rstrip()


def jsonable_result(result: OrchestrationResult) -> dict[str, Any]:
    return {
        "stages": [
            {
                "stage": stage_run.stage,
                "planned": [asdict(task) for task in stage_run.planned],
                "worker_results": [asdict(worker_result) for worker_result in stage_run.worker_results],
            }
            for stage_run in result.stages
        ],
        "inbox": [asdict(item) for item in result.inbox],
        "reductions": [asdict(reduction) for reduction in result.reductions],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Orchestrate multi-agent pipeline planning, workers, inbox, and reduction."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--stage", choices=sorted(STAGES))
    parser.add_argument("--video-id")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--run-workers", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--reduce", action="store_true", help="Run reducer in dry-run mode.")
    parser.add_argument("--apply", action="store_true", help="Apply reducer writes to SQLite.")
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
        "--languages",
        default=",".join(DEFAULT_LANGUAGES),
        help="Comma-separated transcript language preference list.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    languages = tuple(language.strip() for language in args.languages.split(",") if language.strip())
    if not languages:
        raise ValueError("--languages must include at least one language code")

    result = orchestrate(
        sqlite_path=args.sqlite,
        work_dir=args.work_dir,
        limit=args.limit,
        stage=args.stage,
        video_id=args.video_id,
        run_workers=args.run_workers,
        reduce=args.reduce,
        apply=args.apply,
        refresh=args.refresh,
        languages=languages,
        reviews_input=args.reviews_input,
        story_input=args.story_input,
        verified_dir=args.verified_dir,
        transcript_request_delay_seconds=args.request_delay,
        max_consecutive_transcript_blocks=args.max_consecutive_blocks,
    )

    if args.format == "json":
        print(json.dumps(jsonable_result(result), ensure_ascii=False, indent=2))
    else:
        print(render_text_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
