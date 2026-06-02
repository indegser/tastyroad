#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def claim_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.claim")


def write_claim_lock(path: Path, *, agent: str, force: bool) -> None:
    lock_path = claim_path(path)
    payload = {"agent": agent, "claimed_at": now_iso(), "artifact": str(path)}
    if force and lock_path.exists():
        lock_path.unlink()
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        existing = load_json(lock_path)
        raise RuntimeError(f"{path} is already claimed by {existing.get('agent')}") from error
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def read_claim_lock(path: Path) -> dict[str, Any]:
    lock_path = claim_path(path)
    if not lock_path.exists():
        return {}
    return load_json(lock_path)


def remove_claim_lock(path: Path) -> None:
    lock_path = claim_path(path)
    if lock_path.exists():
        lock_path.unlink()


def assert_claim_owner(path: Path, *, agent: str, force: bool) -> None:
    claim = read_claim_lock(path)
    if not claim and not force:
        raise RuntimeError(f"{path} has no claim lock")
    if claim and claim.get("agent") != agent and not force:
        raise RuntimeError(f"{path} is claimed by {claim.get('agent')!r}, not {agent!r}")


def expected_output_key(stage: str) -> str:
    keys = {
        "restaurant_triage": "review",
        "story_review": "review",
        "place_extraction": "candidates",
        "place_verification": "items",
    }
    if stage not in keys:
        raise ValueError(f"Stage {stage!r} is not claimable")
    return keys[stage]


def claim_artifact(path: Path, *, agent: str, force: bool) -> dict[str, Any]:
    payload = load_json(path)
    status = payload.get("status")
    if status == "claimed" and not force:
        raise RuntimeError(f"{path} is already claimed by {payload.get('claimed_by')}")
    if status != "needs_agent" and not force:
        raise RuntimeError(f"{path} status is {status!r}; expected 'needs_agent'")

    write_claim_lock(path, agent=agent, force=force)
    payload["status"] = "claimed"
    payload["claimed_by"] = agent
    payload["claimed_at"] = now_iso()
    write_json(path, payload)
    return payload


def release_artifact(path: Path, *, agent: str, force: bool) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("status") != "claimed" and not force:
        raise RuntimeError(f"{path} status is {payload.get('status')!r}; expected 'claimed'")
    if payload.get("claimed_by") != agent and not force:
        raise RuntimeError(f"{path} is claimed by {payload.get('claimed_by')!r}, not {agent!r}")
    assert_claim_owner(path, agent=agent, force=force)

    payload["status"] = "needs_agent"
    payload["released_by"] = agent
    payload["released_at"] = now_iso()
    payload.pop("claimed_by", None)
    payload.pop("claimed_at", None)
    write_json(path, payload)
    remove_claim_lock(path)
    return payload


def load_result(path: Path) -> Any:
    payload = load_json(path)
    if "output" in payload:
        return payload["output"]
    return payload


def normalize_completed_output(stage: str, result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise ValueError("Agent result must be a JSON object")

    key = expected_output_key(stage)
    if key in result:
        if stage == "place_verification":
            return {
                "verified_at": str(result.get("verified_at") or now_iso()),
                "items": result["items"],
            }
        return {key: result[key]}

    if stage == "restaurant_triage":
        return {"review": result}
    if stage == "story_review":
        return {"review": result}
    if stage == "place_extraction" and "candidates" in result:
        return {"candidates": result["candidates"]}
    if stage == "place_verification" and "items" in result:
        return {
            "verified_at": str(result.get("verified_at") or now_iso()),
            "items": result["items"],
        }
    raise ValueError(f"Agent result does not match expected output for stage {stage!r}")


def complete_artifact(path: Path, *, result_path: Path | None, agent: str, force: bool) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("status") != "claimed" and not force:
        raise RuntimeError(f"{path} status is {payload.get('status')!r}; expected 'claimed'")
    if payload.get("claimed_by") != agent and not force:
        raise RuntimeError(f"{path} is claimed by {payload.get('claimed_by')!r}, not {agent!r}")
    assert_claim_owner(path, agent=agent, force=force)

    stage = str(payload.get("stage") or "")
    selected_result_path = result_path or path.parent / "result.json"
    payload["status"] = "succeeded"
    payload["completed_by"] = agent
    payload["completed_at"] = now_iso()
    payload["output"] = normalize_completed_output(stage, load_result(selected_result_path))
    payload["result_artifacts"] = {
        "markdown": str(path.parent / "result.md"),
        "json": str(selected_result_path),
    }
    payload["error"] = None
    payload.pop("claimed_by", None)
    payload.pop("claimed_at", None)
    write_json(path, payload)
    remove_claim_lock(path)
    return payload


def fail_artifact(path: Path, *, agent: str, message: str, force: bool) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("status") != "claimed" and not force:
        raise RuntimeError(f"{path} status is {payload.get('status')!r}; expected 'claimed'")
    if payload.get("claimed_by") != agent and not force:
        raise RuntimeError(f"{path} is claimed by {payload.get('claimed_by')!r}, not {agent!r}")
    assert_claim_owner(path, agent=agent, force=force)

    payload["status"] = "failed"
    payload["failed_by"] = agent
    payload["failed_at"] = now_iso()
    payload["error"] = {"type": "AgentFailed", "message": message}
    payload.pop("claimed_by", None)
    payload.pop("claimed_at", None)
    write_json(path, payload)
    remove_claim_lock(path)
    return payload


def summarize(payload: dict[str, Any], path: Path) -> str:
    return "\t".join(
        [
            str(payload.get("status") or ""),
            str(payload.get("stage") or ""),
            str(payload.get("video_id") or ""),
            str(path),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Claim or complete one needs_agent artifact.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("artifact", type=Path)
        subparser.add_argument("--agent", required=True)
        subparser.add_argument("--force", action="store_true")
        subparser.add_argument("--format", choices=("text", "json"), default="text")

    claim_parser = subparsers.add_parser("claim")
    add_common(claim_parser)

    release_parser = subparsers.add_parser("release")
    add_common(release_parser)

    complete_parser = subparsers.add_parser("complete")
    add_common(complete_parser)
    complete_parser.add_argument(
        "--result",
        type=Path,
        help="Result JSON path. Defaults to result.json next to the artifact.",
    )

    fail_parser = subparsers.add_parser("fail")
    add_common(fail_parser)
    fail_parser.add_argument("--message", required=True)

    args = parser.parse_args()

    if args.command == "claim":
        payload = claim_artifact(args.artifact, agent=args.agent, force=args.force)
    elif args.command == "release":
        payload = release_artifact(args.artifact, agent=args.agent, force=args.force)
    elif args.command == "complete":
        payload = complete_artifact(
            args.artifact,
            result_path=args.result,
            agent=args.agent,
            force=args.force,
        )
    elif args.command == "fail":
        payload = fail_artifact(
            args.artifact,
            agent=args.agent,
            message=args.message,
            force=args.force,
        )
    else:
        raise AssertionError(args.command)

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(summarize(payload, args.artifact))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
