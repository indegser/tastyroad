#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def infer_region(address: str) -> str:
    replacements = {
        "서울특별시": "서울",
        "부산광역시": "부산",
        "대구광역시": "대구",
        "인천광역시": "인천",
        "광주광역시": "광주",
        "대전광역시": "대전",
        "울산광역시": "울산",
        "세종특별자치시": "세종",
        "제주특별자치도": "제주",
        "강원특별자치도": "강원",
        "전북특별자치도": "전북",
        "경기도": "경기",
        "충청북도": "충북",
        "충청남도": "충남",
        "전라남도": "전남",
        "경상북도": "경북",
        "경상남도": "경남",
    }
    normalized = clean(address)
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    parts = normalized.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else normalized


def first(item: dict[str, Any], nested: dict[str, Any], *keys: str) -> str:
    for key in keys:
        raw_value = item.get(key)
        if isinstance(raw_value, list):
            raw_value = next((value for value in raw_value if clean(value)), "")
        value = clean(raw_value)
        if value:
            return value
        raw_value = nested.get(key)
        if isinstance(raw_value, list):
            raw_value = next((value for value in raw_value if clean(value)), "")
        value = clean(raw_value)
        if value:
            return value
    return ""


def normalize_verification(item: dict[str, Any]) -> list[dict[str, Any]]:
    if item.get("verdict") != "verified":
        return []
    naver = item.get("naver_result") if isinstance(item.get("naver_result"), dict) else {}
    if isinstance(item.get("verified_fields"), dict):
        naver = {**naver, **item["verified_fields"]}
    naver_map_id = first(item, naver, "naver_map_id")
    if not naver_map_id.isdigit():
        raise ValueError(f"Verified candidate lacks numeric Naver ID: {item.get('candidate_id')}")

    resolved_name = first(
        item,
        naver,
        "resolved_name",
        "verified_name",
        "result_name",
        "name",
        "candidate_name",
    )
    address = first(
        item,
        naver,
        "resolved_address",
        "verified_address",
        "verified_road_address",
        "result_address",
        "road_address",
        "address",
    )
    if not resolved_name or not address:
        raise ValueError(f"Verified candidate lacks name/address: {item.get('candidate_id')}")

    video_ids = item.get("video_ids") or [item.get("video_id")]
    results: list[dict[str, Any]] = []
    for raw_video_id in video_ids:
        video_id = clean(raw_video_id)
        if not video_id:
            continue
        map_url = first(item, naver, "map_url", "result_url") or (
            f"https://map.naver.com/p/entry/place/{naver_map_id}?placePath=%2Fhome"
        )
        region = first(item, naver, "resolved_region", "verified_region", "region") or infer_region(address)
        results.append(
            {
                "video_id": video_id,
                "resolved_name": resolved_name,
                "display_name": resolved_name,
                "local_name": resolved_name,
                "country_code": "KR",
                "region": region,
                "address": address,
                "phone": first(item, naver, "phone", "verified_phone", "result_phone"),
                "category": first(item, naver, "category", "verified_category", "result_category")
                or "음식점",
                "map_provider": "naver_map",
                "naver_map_id": naver_map_id,
                "map_url": map_url,
                "evidence_url": first(
                    item,
                    naver,
                    "web_evidence_url",
                    "evidence_url",
                    "verification_evidence",
                ),
                "confidence": 0.98,
                "status": "metadata_verified",
                "notes": first(item, naver, "decision_reason", "reason")
                or "Agent review verified the Naver place name and address.",
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build one promotion input from reviewed Naver place verification artifacts."
    )
    parser.add_argument("--source", required=True)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument(
        "--audit",
        type=Path,
        help="Optional global conflict audit whose exclude_this_video_link decisions must be applied.",
    )
    parser.add_argument(
        "--mapping-audit",
        type=Path,
        action="append",
        default=[],
        help="Mapping audit whose remove_mapping video/place decisions must be applied. Repeatable.",
    )
    parser.add_argument(
        "--recovery",
        type=Path,
        action="append",
        default=[],
        help="Reviewed mismatch recovery artifact containing a verified new_pair. Repeatable.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payloads = [
        json.loads(input_path.read_text(encoding="utf-8"))
        for input_path in args.input
    ]
    video_ids_by_candidate: dict[str, list[str]] = {}
    for payload in payloads:
        verifications = payload.get("verifications") or payload.get("reviews") or []
        for verification in verifications:
            candidate_id = clean(verification.get("candidate_id"))
            video_ids = verification.get("video_ids") or [verification.get("video_id")]
            normalized_video_ids = [clean(video_id) for video_id in video_ids if clean(video_id)]
            if candidate_id and normalized_video_ids:
                video_ids_by_candidate[candidate_id] = normalized_video_ids

    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for payload in payloads:
        verifications = payload.get("verifications") or payload.get("reviews") or []
        for verification in verifications:
            candidate_id = clean(verification.get("candidate_id"))
            reviewed_item = verification
            if not (verification.get("video_ids") or verification.get("video_id")) and candidate_id:
                reviewed_item = {
                    **verification,
                    "video_ids": video_ids_by_candidate.get(candidate_id, []),
                }
            for item in normalize_verification(reviewed_item):
                key = (item["video_id"], item["naver_map_id"])
                if key in seen:
                    continue
                seen.add(key)
                items.append(item)

    excluded_pairs: set[tuple[str, str]] = set()
    if args.audit:
        audit = json.loads(args.audit.read_text(encoding="utf-8"))
        for blocker in audit.get("blockers", []):
            for case in blocker.get("cases", []):
                video_id = clean(case.get("video_id"))
                for candidate in case.get("candidates", []):
                    if candidate.get("decision") == "exclude_this_video_link":
                        excluded_pairs.add((video_id, clean(candidate.get("naver_map_id"))))
        for resolution in audit.get("warning_resolutions", []):
            for excluded in resolution.get("exclude_pairs", []):
                excluded_pairs.add(
                    (clean(excluded.get("video_id")), clean(excluded.get("naver_map_id")))
                )
    for audit_path in args.mapping_audit:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        for item in audit.get("items", []):
            if item.get("verdict") != "remove_mapping":
                continue
            mapping_evidence = item.get("mapping_evidence") or item.get("existing_mapping_evidence") or {}
            excluded_pairs.add(
                (clean(item.get("video_id")), clean(mapping_evidence.get("naver_map_id")))
            )
    if excluded_pairs:
        items = [
            item
            for item in items
            if (item["video_id"], item["naver_map_id"]) not in excluded_pairs
        ]
    seen = {(item["video_id"], item["naver_map_id"]) for item in items}
    for recovery_path in args.recovery:
        recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
        new_pair = recovery.get("new_pair")
        if not isinstance(new_pair, dict):
            raise ValueError(f"Recovery lacks new_pair: {recovery_path}")
        normalized = {
            **new_pair,
            "naver_map_id": clean(new_pair.get("naver_map_id")),
            "confidence": float(new_pair.get("confidence") or 0.98),
            "status": str(new_pair.get("status") or "metadata_verified"),
        }
        if not normalized["naver_map_id"].isdigit():
            raise ValueError(f"Recovery has invalid Naver ID: {recovery_path}")
        key = (clean(normalized.get("video_id")), normalized["naver_map_id"])
        if not key[0]:
            raise ValueError(f"Recovery has no video_id: {recovery_path}")
        if key not in seen:
            seen.add(key)
            items.append(normalized)

    output = {
        "source": args.source,
        "verified_at": date.today().isoformat(),
        "items": items,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {len(items)} verified video-place mappings to {args.output} "
        f"(excluded {len(excluded_pairs)} audited pairs, recoveries {len(args.recovery)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
