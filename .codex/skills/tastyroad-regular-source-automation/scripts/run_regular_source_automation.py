#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG = Path("data/sources/youtube_sources.json")
DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_REPORT_DIR = Path("data/work/regular_source_automation")
COLLECT_SCRIPT = Path(".codex/skills/tastyroad-youtube-channel-collect/scripts/collect_youtube.py")
MAP_BACKLOG_SCRIPT = Path(".codex/skills/tastyroad-map-video-restaurants/scripts/process_pipeline_backlog.py")
NAVER_RESOLVE_SCRIPT = Path(".codex/skills/tastyroad-map-video-restaurants/scripts/resolve_naver_search_candidates.py")
PROMOTE_PLACES_SCRIPT = Path(".codex/skills/tastyroad-map-video-restaurants/scripts/promote_verified_places.py")
TRANSCRIPT_SCRIPT = Path(".codex/skills/tastyroad-youtube-transcript-ingest/scripts/fetch_transcripts.py")


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    enabled: bool


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    skipped: bool = False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def load_sources(config_path: Path) -> list[Source]:
    payload = json.loads(repo_path(config_path).read_text(encoding="utf-8"))
    sources: list[Source] = []
    for item in payload.get("sources", []):
        if str(item.get("type", "youtube")) != "youtube":
            continue
        sources.append(
            Source(
                key=str(item["key"]),
                name=str(item["name"]),
                enabled=bool(item.get("enabled", True)),
            )
        )
    return [source for source in sources if source.enabled]


def run_command(name: str, command: list[str], *, dry_run: bool) -> CommandResult:
    if dry_run:
        return CommandResult(name=name, command=command, returncode=0, stdout="", stderr="", skipped=True)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )
    return CommandResult(
        name=name,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def table_exists(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "select 1 from sqlite_master where type in ('table', 'view') and name = ?",
        (name,),
    ).fetchone()
    return row is not None


def count_rows(connection: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> int:
    row = connection.execute(query, params).fetchone()
    return int(row[0] or 0) if row else 0


def snapshot_source_video_ids(sqlite_path: Path, sources: list[Source]) -> dict[str, set[str]]:
    path = repo_path(sqlite_path)
    if not path.exists():
        return {source.key: set() for source in sources}
    with sqlite3.connect(path) as connection:
        snapshots: dict[str, set[str]] = {}
        for source in sources:
            rows = connection.execute(
                """
                select v.video_id
                from youtube_videos v
                join sources s on s.id = v.source_id
                where s.name = ?
                """,
                (source.name,),
            ).fetchall()
            snapshots[source.key] = {str(row[0]) for row in rows}
        return snapshots


def source_counts(snapshot: dict[str, set[str]]) -> dict[str, int]:
    return {source_key: len(video_ids) for source_key, video_ids in snapshot.items()}


def select_new_videos(sqlite_path: Path, new_ids_by_source: dict[str, set[str]]) -> list[dict[str, Any]]:
    path = repo_path(sqlite_path)
    if not path.exists():
        return []
    all_new_ids = {video_id for ids in new_ids_by_source.values() for video_id in ids}
    if not all_new_ids:
        return []
    placeholders = ",".join("?" for _ in all_new_ids)
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            f"""
            select s.name, v.video_id, v.title, v.url, v.published_at, v.collected_at
            from youtube_videos v
            join sources s on s.id = v.source_id
            where v.video_id in ({placeholders})
            order by datetime(v.published_at), v.id
            """,
            tuple(all_new_ids),
        ).fetchall()
    result: list[dict[str, Any]] = []
    for source_name, video_id, title, url, published_at, collected_at in rows:
        source_key = next((key for key, name in SOURCE_NAME_BY_KEY.items() if name == source_name), "")
        if not source_key or str(video_id) not in new_ids_by_source.get(source_key, set()):
            continue
        result.append(
            {
                "source": source_name,
                "source_key": source_key,
                "video_id": video_id,
                "title": title,
                "url": url,
                "published_at": published_at,
                "collected_at": collected_at,
            }
        )
    return result


def load_scope_video_ids(report_path: Path | None) -> list[str]:
    if report_path is None:
        return []
    payload = json.loads(repo_path(report_path).read_text(encoding="utf-8"))
    video_ids = payload.get("release_scope_video_ids")
    if video_ids is None:
        video_ids = [item.get("video_id") for item in payload.get("new_videos", [])]
    return sorted({str(video_id) for video_id in video_ids if video_id})


def gate_status(sqlite_path: Path, new_video_ids: list[str]) -> dict[str, Any]:
    path = repo_path(sqlite_path)
    if not path.exists():
        blockers = [{"type": "sqlite_missing", "path": str(path)}]
        return {
            "deploy_ready": False,
            "blocker_count": len(blockers),
            "warning_count": 0,
            "blockers": blockers,
            "warnings": [],
        }
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    params = tuple(new_video_ids)
    placeholders = ",".join("?" for _ in new_video_ids)
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        integrity = str(connection.execute("pragma integrity_check").fetchone()[0])
        if integrity != "ok":
            blockers.append({"type": "sqlite_integrity", "result": integrity})

        if table_exists(connection, "restaurants") and table_exists(connection, "youtube_video_restaurants"):
            blank_naver_count = count_rows(
                connection,
                """
                select count(distinct r.id)
                from restaurants r
                join youtube_video_restaurants yvr on yvr.restaurant_id = r.id
                where yvr.status in ('verified', 'metadata_verified')
                  and trim(coalesce(r.naver_map_id, '')) = ''
                """,
            )
            if blank_naver_count:
                blockers.append({"type": "blank_naver_map_id", "restaurant_count": blank_naver_count})

        if table_exists(connection, "video_pipeline_status") and new_video_ids:
            for row in connection.execute(
                f"""
                select video_id, source, title, mapping_status, review_status
                from video_pipeline_status
                where video_id in ({placeholders})
                  and mapping_status in ('mapping_pending', 'mapping_partial')
                order by published_at desc
                """,
                params,
            ):
                blockers.append({"type": "mapping", **dict(row)})
            for row in connection.execute(
                f"""
                select video_id, source, title, mapping_status, review_status
                from video_pipeline_status
                where video_id in ({placeholders})
                  and review_status = 'reviewed_uncertain'
                  and mapping_status = 'not_applicable'
                order by published_at desc
                """,
                params,
            ):
                warnings.append({"type": "mapping_review", **dict(row)})

        if table_exists(connection, "preferred_youtube_transcripts") and new_video_ids:
            transcript_missing = connection.execute(
                f"""
                select v.video_id, s.name as source, v.title
                from youtube_videos v
                join sources s on s.id = v.source_id
                left join video_pipeline_status ps on ps.video_id = v.video_id
                where v.video_id in ({placeholders})
                  and coalesce(ps.mapping_status, 'not_ready_for_mapping') != 'not_applicable'
                  and not exists (
                    select 1 from preferred_youtube_transcripts p
                    where p.youtube_video_id = v.id
                  )
                order by datetime(v.published_at) desc
                """,
                params,
            ).fetchall()
            for row in transcript_missing:
                warnings.append({"type": "transcript", **dict(row)})

        if table_exists(connection, "preferred_youtube_transcripts") and table_exists(connection, "video_must_taste_items"):
            must_taste_query = """
                select
                  v.video_id,
                  s.name as source,
                  v.title,
                  r.id as restaurant_id,
                  r.display_name
                from youtube_videos v
                join sources s on s.id = v.source_id
                join youtube_video_restaurants yvr on yvr.youtube_video_id = v.id
                join restaurants r on r.id = yvr.restaurant_id
                join preferred_youtube_transcripts p on p.youtube_video_id = v.id
                where yvr.status in ('verified', 'metadata_verified')
                  and trim(coalesce(r.naver_map_id, '')) != ''
                  and not exists (
                    select 1 from video_must_taste_items m
                    where m.youtube_video_id = v.id
                      and m.restaurant_id = r.id
                  )
            """
            if new_video_ids:
                must_taste_query += f" and v.video_id in ({placeholders})"
                must_taste_rows = connection.execute(must_taste_query, params).fetchall()
            else:
                must_taste_query += " order by datetime(v.published_at) desc limit 25"
                must_taste_rows = connection.execute(must_taste_query).fetchall()
            for row in must_taste_rows:
                warnings.append({"type": "must_taste", **dict(row)})

    return {
        "deploy_ready": not blockers,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "blockers": blockers,
        "warnings": warnings,
    }


def work_queues(gates: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    findings = [*gates.get("blockers", []), *gates.get("warnings", [])]
    return {
        "map_verification": [
            item for item in findings if item.get("type") in {"mapping", "mapping_review"}
        ],
        "transcript_ingest": [item for item in findings if item.get("type") == "transcript"],
        "must_taste_validation": [item for item in findings if item.get("type") == "must_taste"],
    }


def write_report(report_dir: Path, report: dict[str, Any]) -> Path:
    path = repo_path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = path / f"regular_source_automation_{stamp}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest_path = path / "latest.json"
    latest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report_path


def command_payload(result: CommandResult) -> dict[str, Any]:
    return {
        "name": result.name,
        "command": result.command,
        "returncode": result.returncode,
        "skipped": result.skipped,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


SOURCE_NAME_BY_KEY: dict[str, str] = {}
SOURCE_AFTER_IDS: dict[str, set[str]] = {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run recurring Tastyroad source maintenance stages.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--scope-report",
        type=Path,
        help="Recalculate gates for the release_scope_video_ids from an earlier non-dry report.",
    )
    parser.add_argument("--full-channel", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--transcript-request-delay", type=float, default=1.0)
    parser.add_argument("--skip-collect", action="store_true")
    parser.add_argument("--skip-map", action="store_true")
    parser.add_argument("--skip-transcripts", action="store_true")
    parser.add_argument("--skip-naver-resolution", action="store_true")
    args = parser.parse_args()

    sources = load_sources(args.config)
    global SOURCE_NAME_BY_KEY
    SOURCE_NAME_BY_KEY = {source.key: source.name for source in sources}

    before_ids = snapshot_source_video_ids(args.sqlite, sources)
    commands: list[CommandResult] = []

    for source in sources:
        if not args.skip_collect:
            command = [
                sys.executable,
                str(COLLECT_SCRIPT),
                "--source",
                source.key,
                "--reuse-existing",
                "--workers",
                str(args.workers),
            ]
            if args.full_channel:
                command.append("--full-channel")
            commands.append(run_command(f"collect:{source.key}", command, dry_run=args.dry_run))

    global SOURCE_AFTER_IDS
    SOURCE_AFTER_IDS = snapshot_source_video_ids(args.sqlite, sources)
    new_ids_by_source = {
        source.key: SOURCE_AFTER_IDS.get(source.key, set()) - before_ids.get(source.key, set())
        for source in sources
    }
    new_videos = [] if args.dry_run else select_new_videos(args.sqlite, new_ids_by_source)
    discovered_video_ids = [str(item["video_id"]) for item in new_videos]
    scoped_video_ids = load_scope_video_ids(args.scope_report)
    release_scope_video_ids = sorted({*discovered_video_ids, *scoped_video_ids})

    scoped_source_keys = {
        source_key for source_key, video_ids in new_ids_by_source.items() if video_ids
    }
    scoped_sources = [source for source in sources if source.key in scoped_source_keys]

    if not args.skip_map:
        for source in scoped_sources:
            commands.append(
                run_command(
                    f"map:process-backlog:{source.key}",
                    [
                        sys.executable,
                        str(MAP_BACKLOG_SCRIPT),
                        "--source",
                        source.name,
                    ],
                    dry_run=args.dry_run,
                )
            )

    if not args.skip_naver_resolution:
        for source in scoped_sources:
            output = Path("data/work/regular_source_automation") / f"{source.key}_resolved_places.json"
            unresolved = Path("data/work/regular_source_automation") / f"{source.key}_unresolved_places.json"
            commands.append(
                run_command(
                    f"map:resolve-naver:{source.key}",
                    [
                        sys.executable,
                        str(NAVER_RESOLVE_SCRIPT),
                        "--source",
                        source.name,
                        "--output",
                        str(output),
                        "--unresolved-output",
                        str(unresolved),
                        "--all-candidates",
                    ],
                    dry_run=args.dry_run,
                )
            )
            if not args.dry_run and repo_path(output).exists():
                commands.append(
                    run_command(
                        f"map:promote-resolved:{source.key}",
                        [sys.executable, str(PROMOTE_PLACES_SCRIPT), "--input", str(output)],
                        dry_run=False,
                    )
                )

    if not args.skip_transcripts:
        if release_scope_video_ids:
            transcript_command = [
                sys.executable,
                str(TRANSCRIPT_SCRIPT),
                "--missing-only",
                "--storage-provider",
                "supabase_storage",
                "--request-delay",
                str(args.transcript_request_delay),
            ]
            transcript_command.extend(
                f"--video-id={video_id}" for video_id in release_scope_video_ids
            )
            commands.append(
                run_command(
                    "transcripts:release_scope",
                    transcript_command,
                    dry_run=args.dry_run,
                )
            )

    failed_commands = [command_payload(result) for result in commands if result.returncode != 0]
    gates = gate_status(args.sqlite, release_scope_video_ids)
    if failed_commands:
        gates.setdefault("blockers", [])
        gates.setdefault("warnings", [])
        for item in failed_commands:
            failed_item = {"type": "command_failed", "name": item["name"], "returncode": item["returncode"]}
            if str(item["name"]).startswith("transcripts:"):
                gates["warnings"].append(failed_item)
            else:
                gates["blockers"].append(failed_item)
        gates["deploy_ready"] = not gates["blockers"]
        gates["blocker_count"] = len(gates["blockers"])
        gates["warning_count"] = len(gates["warnings"])

    report = {
        "checked_at": now_iso(),
        "dry_run": args.dry_run,
        "collection_performed": not args.dry_run and not args.skip_collect,
        "new_video_detection": {
            "status": "not_checked" if args.dry_run else "completed",
            "reason": (
                "Dry-run plans commands but does not query YouTube; it cannot determine whether new videos exist."
                if args.dry_run
                else ""
            ),
        },
        "full_channel": args.full_channel,
        "sources": [source.__dict__ for source in sources],
        "before_counts": source_counts(before_ids),
        "after_counts": source_counts(SOURCE_AFTER_IDS),
        "new_ids_by_source": {key: sorted(values) for key, values in new_ids_by_source.items() if values},
        "new_video_count": None if args.dry_run else len(new_videos),
        "new_videos": new_videos,
        "release_scope_video_ids": release_scope_video_ids,
        "commands": [command_payload(result) for result in commands],
        "gates": gates,
        "work_queues": work_queues(gates),
        "next_actions": next_actions(gates),
    }
    report_path = write_report(args.report_dir, report)
    print(json.dumps({"report": str(report_path.relative_to(REPO_ROOT)), **report}, ensure_ascii=False, indent=2))
    return 1 if failed_commands else 0


def next_actions(gates: dict[str, Any]) -> list[str]:
    blockers = gates.get("blockers", [])
    warnings = gates.get("warnings", [])
    findings = [*blockers, *warnings]
    if not blockers:
        actions = ["Follow $tastyroad-site-release if data changed and pnpm run build passes."]
        if warnings:
            actions.append("Keep transcript and must-taste warnings as follow-up Triage; they do not block mapped restaurants from release.")
        return actions
    actions: list[str] = []
    if any(item.get("type") == "mapping" for item in blockers):
        actions.append("Use $tastyroad-map-video-restaurants for mapping blockers.")
    if any(item.get("type") == "transcript" for item in findings):
        actions.append("Use $tastyroad-youtube-transcript-ingest for transcript warnings.")
    if any(item.get("type") == "must_taste" for item in findings):
        actions.append("Use $tastyroad-transcript-must-taste for must-taste warnings.")
    if any(item.get("type") == "command_failed" for item in blockers):
        actions.append("Inspect failed command stdout/stderr in the JSON report before continuing.")
    if any(item.get("type") == "command_failed" for item in warnings):
        actions.append("Inspect failed transcript command stdout/stderr; transcript failures are follow-up warnings.")
    return actions


if __name__ == "__main__":
    raise SystemExit(main())
