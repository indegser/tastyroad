#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from apply_must_taste_result import validate_result


DEFAULT_OUTPUT = Path("data/work/must_taste_quality/comparison.json")
DEFAULT_MARKDOWN = Path("data/work/must_taste_quality/comparison.md")
DEFAULT_BLIND_REVIEW = Path("data/work/must_taste_quality/blind_review.json")
DEFAULT_BLIND_KEY = Path("data/work/must_taste_quality/blind_review_key.json")
MENU_MATCH_THRESHOLD = 0.72
NEAR_EVIDENCE_SEGMENTS = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare optimized must-taste result.json artifacts with a frozen baseline. "
            "Changed selections are exported for blind human review."
        )
    )
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--blind-review-output", type=Path, default=DEFAULT_BLIND_REVIEW)
    parser.add_argument("--blind-key-output", type=Path, default=DEFAULT_BLIND_KEY)
    parser.add_argument("--baseline-usage", type=Path)
    parser.add_argument("--candidate-usage", type=Path)
    parser.add_argument("--min-menu-recall", type=float, default=0.90)
    parser.add_argument("--min-pair-all-recall", type=float, default=0.80)
    parser.add_argument("--min-near-evidence-recall", type=float, default=0.85)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def normalize_menu(value: object) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", str(value or "").casefold())


def menu_similarity(left: object, right: object) -> float:
    a = normalize_menu(left)
    b = normalize_menu(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if min(len(a), len(b)) >= 3 and (a in b or b in a):
        return 0.9
    return round(SequenceMatcher(None, a, b).ratio(), 4)


def evidence_segments(item: dict[str, Any], *, baseline: bool) -> set[int]:
    segments: set[int] = set()
    primary = item.get("segment_index") if baseline else (item.get("evidence") or {}).get("segment_index")
    if isinstance(primary, int):
        segments.add(primary)
    if baseline:
        supporting = (item.get("evidence") or {}).get("supporting_evidence") or []
    else:
        supporting = item.get("supporting_evidence") or []
    for entry in supporting:
        if isinstance(entry, dict) and isinstance(entry.get("segment_index"), int):
            segments.add(int(entry["segment_index"]))
    return segments


def evidence_comparison(
    baseline_item: dict[str, Any],
    candidate_item: dict[str, Any],
) -> dict[str, Any]:
    baseline_segments = evidence_segments(baseline_item, baseline=True)
    candidate_segments = evidence_segments(candidate_item, baseline=False)
    if not baseline_segments or not candidate_segments:
        return {"exact": False, "near": False, "distance": None, "score": 0.0}
    distance = min(abs(left - right) for left in baseline_segments for right in candidate_segments)
    return {
        "exact": distance == 0,
        "near": distance <= NEAR_EVIDENCE_SEGMENTS,
        "distance": distance,
        "score": 1.0 if distance == 0 else (0.75 if distance <= NEAR_EVIDENCE_SEGMENTS else 0.0),
    }


def pair_item_score(
    baseline_item: dict[str, Any],
    candidate_item: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    menu_score = menu_similarity(baseline_item.get("menu_item"), candidate_item.get("menu_item"))
    evidence = evidence_comparison(baseline_item, candidate_item)
    score = 0.75 * menu_score + 0.25 * float(evidence["score"])
    return score, {"menu_similarity": menu_score, "evidence": evidence}


def best_item_assignment(
    baseline_items: list[dict[str, Any]],
    candidate_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not baseline_items:
        return []
    choices = [-1, *range(len(candidate_items))]
    best_score = -1.0
    best_assignment: tuple[int, ...] = tuple(-1 for _ in baseline_items)
    for assignment in itertools.product(choices, repeat=len(baseline_items)):
        assigned = [index for index in assignment if index >= 0]
        if len(assigned) != len(set(assigned)):
            continue
        score = 0.0
        for baseline_index, candidate_index in enumerate(assignment):
            if candidate_index >= 0:
                score += pair_item_score(
                    baseline_items[baseline_index],
                    candidate_items[candidate_index],
                )[0]
        if score > best_score:
            best_score = score
            best_assignment = assignment

    matches = []
    for baseline_index, candidate_index in enumerate(best_assignment):
        baseline_item = baseline_items[baseline_index]
        if candidate_index < 0:
            matches.append(
                {
                    "baseline_rank": baseline_item.get("rank"),
                    "baseline_menu_item": baseline_item.get("menu_item"),
                    "candidate_rank": None,
                    "candidate_menu_item": None,
                    "menu_similarity": 0.0,
                    "menu_match": False,
                    "evidence": {"exact": False, "near": False, "distance": None, "score": 0.0},
                }
            )
            continue
        candidate_item = candidate_items[candidate_index]
        _, details = pair_item_score(baseline_item, candidate_item)
        matches.append(
            {
                "baseline_rank": baseline_item.get("rank"),
                "baseline_menu_item": baseline_item.get("menu_item"),
                "candidate_rank": candidate_item.get("rank"),
                "candidate_menu_item": candidate_item.get("menu_item"),
                "menu_similarity": details["menu_similarity"],
                "menu_match": details["menu_similarity"] >= MENU_MATCH_THRESHOLD,
                "evidence": details["evidence"],
            }
        )
    return matches


def result_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.rglob("result.json"))


def load_candidate_results(root: Path) -> tuple[dict[tuple[str, int], dict[str, Any]], list[str]]:
    results: dict[tuple[str, int], dict[str, Any]] = {}
    errors = []
    for path in result_files(root):
        try:
            result = read_json(path)
            key = (str(result["video_id"]), int(result["restaurant_id"]))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        result["_result_path"] = str(path)
        results[key] = result
    return results, errors


def validate_candidate_result(result: dict[str, Any]) -> str | None:
    result_path = Path(str(result["_result_path"]))
    context_path = result_path.parent / "context.json"
    if not context_path.exists():
        return f"missing {context_path}"
    try:
        context = read_json(context_path)
        validation_result = dict(result)
        validation_result.pop("_result_path", None)
        validation_result["pipeline"] = {
            "coverage_path": str(result_path.parent / "coverage.json"),
            "chunks_path": str(result_path.parent / "chunks.json"),
            "attention_events_path": str(result_path.parent / "attention_events.jsonl"),
            "candidates_path": str(result_path.parent / "menu_candidates.json"),
            "reviews_path": str(result_path.parent / "candidate_reviews.json"),
        }
        validate_result(context, validation_result, result_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return str(exc)
    return None


def display_items(items: list[dict[str, Any]], *, baseline: bool) -> list[dict[str, Any]]:
    displayed = []
    for item in items:
        if baseline:
            evidence_text = item.get("evidence_text")
            timestamp = item.get("timestamp")
        else:
            evidence = item.get("evidence") or {}
            evidence_text = evidence.get("text")
            timestamp = evidence.get("timestamp")
        displayed.append(
            {
                "rank": item.get("rank"),
                "menu_item": item.get("menu_item"),
                "raw_reason": item.get("reason"),
                "display_reason": item.get("repaired_reason") or item.get("reason"),
                "timestamp": timestamp,
                "evidence_text": evidence_text,
            }
        )
    return displayed


def blind_assignment(baseline_id: str, pair_key: str) -> bool:
    digest = hashlib.sha256(f"{baseline_id}:{pair_key}".encode("utf-8")).digest()
    return digest[0] % 2 == 0


def pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def token_comparison(
    baseline_path: Path | None,
    candidate_path: Path | None,
) -> dict[str, Any] | None:
    if not baseline_path and not candidate_path:
        return None
    if not baseline_path or not candidate_path:
        raise ValueError("Provide both --baseline-usage and --candidate-usage.")
    baseline = read_json(baseline_path)
    candidate = read_json(candidate_path)
    keys = ("input_tokens", "uncached_input_tokens", "output_tokens", "total_tokens")
    reductions = {}
    for key in keys:
        before = float((baseline.get("per_pair") or {}).get(key) or 0)
        after = float((candidate.get("per_pair") or {}).get(key) or 0)
        reductions[key] = {
            "baseline_per_pair": before,
            "candidate_per_pair": after,
            "reduction_percent": round((before - after) * 100 / before, 2) if before else 0.0,
        }
    return {"baseline": baseline, "candidate": candidate, "per_pair": reductions}


def compare(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    baseline = read_json(args.baseline)
    candidate_results, load_errors = load_candidate_results(args.results_root)
    baseline_pairs = baseline.get("pairs")
    if not isinstance(baseline_pairs, list):
        raise ValueError("baseline.pairs must be a list.")

    pair_reports = []
    blind_rows = []
    blind_key_rows = []
    baseline_item_count = 0
    matched_menu_count = 0
    near_evidence_count = 0
    exact_evidence_count = 0
    candidate_item_count = 0
    complete_pair_count = 0
    repaired_reason_count = 0
    present_pair_count = 0
    validated_pair_count = 0

    for pair in baseline_pairs:
        key = (str(pair["video_id"]), int(pair["restaurant_id"]))
        pair_key = f"{key[0]}:{key[1]}"
        baseline_items = pair.get("items") or []
        candidate = candidate_results.get(key)
        candidate_items = (candidate or {}).get("items") or []
        baseline_item_count += len(baseline_items)
        candidate_item_count += len(candidate_items)
        repaired_reason_count += sum(
            1 for item in candidate_items if str(item.get("repaired_reason") or "").strip()
        )
        if candidate is not None:
            present_pair_count += 1
        validation_error = (
            validate_candidate_result(candidate) if candidate is not None else "candidate missing"
        )
        if validation_error is None:
            validated_pair_count += 1

        matches = best_item_assignment(baseline_items, candidate_items)
        pair_menu_matches = sum(1 for match in matches if match["menu_match"])
        pair_near_evidence = sum(
            1 for match in matches if match["menu_match"] and match["evidence"]["near"]
        )
        pair_exact_evidence = sum(
            1 for match in matches if match["menu_match"] and match["evidence"]["exact"]
        )
        matched_menu_count += pair_menu_matches
        near_evidence_count += pair_near_evidence
        exact_evidence_count += pair_exact_evidence
        pair_complete = len(matches) == pair_menu_matches
        complete_pair_count += int(pair_complete)

        baseline_names = {normalize_menu(item.get("menu_item")) for item in baseline_items}
        candidate_names = {normalize_menu(item.get("menu_item")) for item in candidate_items}
        changed = candidate is None or baseline_names != candidate_names or any(
            not match["evidence"]["exact"] for match in matches if match["menu_match"]
        )
        report = {
            "pair_key": pair_key,
            "video_id": key[0],
            "video_title": pair.get("video_title"),
            "restaurant_id": key[1],
            "restaurant_name": pair.get("restaurant_name"),
            "result_path": (candidate or {}).get("_result_path"),
            "validation_passed": validation_error is None,
            "validation_error": validation_error,
            "baseline_item_count": len(baseline_items),
            "candidate_item_count": len(candidate_items),
            "menu_recall": pct(pair_menu_matches, len(baseline_items)),
            "pair_all_menu_recalled": pair_complete,
            "matches": matches,
            "changed": changed,
        }
        pair_reports.append(report)

        if changed:
            baseline_is_a = blind_assignment(str(baseline["baseline_id"]), pair_key)
            baseline_display = display_items(baseline_items, baseline=True)
            candidate_display = display_items(candidate_items, baseline=False)
            blind_rows.append(
                {
                    "review_id": hashlib.sha256(pair_key.encode("utf-8")).hexdigest()[:12],
                    "video_title": pair.get("video_title"),
                    "restaurant_name": pair.get("restaurant_name"),
                    "option_a": baseline_display if baseline_is_a else candidate_display,
                    "option_b": candidate_display if baseline_is_a else baseline_display,
                    "review": {
                        "menu_selection": "",
                        "evidence_quality": "",
                        "display_copy": "",
                        "overall": "",
                        "notes": "",
                    },
                }
            )
            blind_key_rows.append(
                {
                    "review_id": blind_rows[-1]["review_id"],
                    "pair_key": pair_key,
                    "option_a": "baseline" if baseline_is_a else "candidate",
                    "option_b": "candidate" if baseline_is_a else "baseline",
                }
            )

    pair_count = len(baseline_pairs)
    menu_recall = pct(matched_menu_count, baseline_item_count)
    pair_all_recall = pct(complete_pair_count, pair_count)
    near_evidence_recall = pct(near_evidence_count, max(matched_menu_count, 1))
    thresholds = {
        "min_menu_recall": args.min_menu_recall,
        "min_pair_all_recall": args.min_pair_all_recall,
        "min_near_evidence_recall": args.min_near_evidence_recall,
    }
    automatic_checks = {
        "all_pairs_present": present_pair_count == pair_count,
        "all_candidate_results_validate": validated_pair_count == pair_count,
        "menu_recall": menu_recall >= args.min_menu_recall,
        "pair_all_recall": pair_all_recall >= args.min_pair_all_recall,
        "near_evidence_recall": near_evidence_recall >= args.min_near_evidence_recall,
        "all_candidate_items_have_repaired_reason": repaired_reason_count == candidate_item_count,
    }
    changed_pair_count = sum(1 for pair in pair_reports if pair["changed"])
    summary = {
        "baseline_id": baseline["baseline_id"],
        "baseline_pairs": pair_count,
        "candidate_pairs_present": present_pair_count,
        "baseline_items": baseline_item_count,
        "candidate_items": candidate_item_count,
        "menu_matches": matched_menu_count,
        "menu_recall": menu_recall,
        "pair_all_menu_recall": pair_all_recall,
        "near_evidence_recall": near_evidence_recall,
        "exact_evidence_recall": pct(exact_evidence_count, max(matched_menu_count, 1)),
        "changed_pairs": changed_pair_count,
        "blind_reviews_required": len(blind_rows),
        "automatic_checks": automatic_checks,
        "automatic_gate_pass": all(automatic_checks.values()),
        "release_status": (
            "pass"
            if all(automatic_checks.values()) and not blind_rows
            else "review_required"
        ),
        "thresholds": thresholds,
    }
    report = {
        "schema_version": 1,
        "kind": "must_taste_quality_comparison",
        "summary": summary,
        "token_comparison": token_comparison(args.baseline_usage, args.candidate_usage),
        "result_load_errors": load_errors,
        "pairs": pair_reports,
    }
    blind_review = {
        "schema_version": 1,
        "kind": "must_taste_blind_review",
        "baseline_id": baseline["baseline_id"],
        "instructions": {
            "allowed_values": ["A", "B", "tie", "both_fail"],
            "note": (
                "Judge menu selection, transcript evidence, and display copy independently. "
                "Do not open blind_review_key.json until reviews are complete."
            ),
        },
        "reviews": blind_rows,
    }
    blind_key = {
        "schema_version": 1,
        "kind": "must_taste_blind_review_key",
        "baseline_id": baseline["baseline_id"],
        "assignments": blind_key_rows,
    }
    return report, blind_review, blind_key


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    checks = summary["automatic_checks"]
    lines = [
        "# Must-Taste Quality Comparison",
        "",
        "## Summary",
        "",
        f"- Release status: `{summary['release_status']}`",
        f"- Baseline/candidate pairs: {summary['baseline_pairs']} / {summary['candidate_pairs_present']}",
        f"- Baseline/candidate items: {summary['baseline_items']} / {summary['candidate_items']}",
        f"- Menu recall: {summary['menu_recall']:.2%}",
        f"- Pair all-menu recall: {summary['pair_all_menu_recall']:.2%}",
        f"- Near-evidence recall among menu matches: {summary['near_evidence_recall']:.2%}",
        f"- Exact-evidence recall among menu matches: {summary['exact_evidence_recall']:.2%}",
        f"- Changed pairs requiring blind review: {summary['blind_reviews_required']}",
        "",
        "## Automatic Checks",
        "",
    ]
    lines.extend(f"- [{'x' if passed else ' '}] {name}" for name, passed in checks.items())
    lines.extend(["", "## Changed Pairs", ""])
    changed = [pair for pair in report["pairs"] if pair["changed"]]
    if not changed:
        lines.append("- None")
    for pair in changed:
        lines.append(
            f"- `{pair['pair_key']}` {pair['restaurant_name']} — "
            f"menu recall {pair['menu_recall']:.2%}"
        )
        for match in pair["matches"]:
            lines.append(
                "  - "
                f"{match['baseline_menu_item']} → {match['candidate_menu_item'] or '(missing)'}; "
                f"menu={match['menu_similarity']:.2f}, "
                f"evidence_distance={match['evidence']['distance']}"
            )
    token_report = report.get("token_comparison")
    if token_report:
        lines.extend(["", "## Token Comparison", ""])
        for key, value in token_report["per_pair"].items():
            lines.append(
                f"- {key}: {value['baseline_per_pair']:.2f} → "
                f"{value['candidate_per_pair']:.2f} "
                f"({value['reduction_percent']:.2f}% reduction)"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    report, blind_review, blind_key = compare(args)
    write_json(args.output, report)
    write_json(args.blind_review_output, blind_review)
    write_json(args.blind_key_output, blind_key)
    write_markdown(args.markdown_output, report)
    summary = report["summary"]
    print(f"release_status={summary['release_status']}")
    print(f"menu_recall={summary['menu_recall']:.4f}")
    print(f"pair_all_menu_recall={summary['pair_all_menu_recall']:.4f}")
    print(f"near_evidence_recall={summary['near_evidence_recall']:.4f}")
    print(f"blind_reviews_required={summary['blind_reviews_required']}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
