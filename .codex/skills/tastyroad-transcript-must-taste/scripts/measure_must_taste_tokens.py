#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path("data/work/must_taste_quality/token_usage.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize Codex rollout token_count events for a must-taste run."
    )
    parser.add_argument("rollouts", nargs="+", type=Path)
    parser.add_argument("--videos", type=int, required=True)
    parser.add_argument("--pairs", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def read_rollout(path: Path) -> dict[str, Any]:
    final_usage: dict[str, int] | None = None
    response_count = 0
    tool_call_count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
        if row.get("type") == "event_msg":
            payload = row.get("payload") or {}
            if payload.get("type") == "token_count":
                info = payload.get("info") or {}
                total = info.get("total_token_usage")
                if isinstance(total, dict):
                    final_usage = {
                        key: int(total.get(key) or 0)
                        for key in (
                            "input_tokens",
                            "cached_input_tokens",
                            "output_tokens",
                            "reasoning_output_tokens",
                            "total_tokens",
                        )
                    }
                response_count += 1
        if row.get("type") == "response_item":
            payload = row.get("payload") or {}
            if payload.get("type") == "function_call":
                tool_call_count += 1
    if final_usage is None:
        raise ValueError(f"{path}: no token_count event found.")
    final_usage["uncached_input_tokens"] = (
        final_usage["input_tokens"] - final_usage["cached_input_tokens"]
    )
    return {
        "path": str(path),
        "usage": final_usage,
        "model_response_count": response_count,
        "tool_call_count": tool_call_count,
    }


def ratio(value: int, denominator: int) -> float:
    return round(value / denominator, 2) if denominator else 0.0


def summarize(args: argparse.Namespace) -> dict[str, Any]:
    if args.videos < 1 or args.pairs < 1:
        raise ValueError("--videos and --pairs must be at least 1.")
    sessions = [read_rollout(path) for path in args.rollouts]
    keys = (
        "input_tokens",
        "cached_input_tokens",
        "uncached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    )
    totals = {
        key: sum(int(session["usage"][key]) for session in sessions)
        for key in keys
    }
    return {
        "schema_version": 1,
        "kind": "must_taste_token_usage",
        "label": args.label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "work_units": {
            "videos": args.videos,
            "pairs": args.pairs,
        },
        "totals": totals,
        "per_video": {
            key: ratio(value, args.videos) for key, value in totals.items()
        },
        "per_pair": {
            key: ratio(value, args.pairs) for key, value in totals.items()
        },
        "model_response_count": sum(
            int(session["model_response_count"]) for session in sessions
        ),
        "tool_call_count": sum(int(session["tool_call_count"]) for session in sessions),
        "sessions": sessions,
    }


def main() -> int:
    args = parse_args()
    report = summarize(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"label={report['label']}")
    print(f"input_tokens={report['totals']['input_tokens']}")
    print(f"cached_input_tokens={report['totals']['cached_input_tokens']}")
    print(f"uncached_input_tokens={report['totals']['uncached_input_tokens']}")
    print(f"output_tokens={report['totals']['output_tokens']}")
    print(f"input_tokens_per_pair={report['per_pair']['input_tokens']}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
