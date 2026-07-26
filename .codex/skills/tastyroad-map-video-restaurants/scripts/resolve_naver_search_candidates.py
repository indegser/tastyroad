#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_OUTPUT = Path("data/verified_places/sungsikyung_mukeultende_naver_resolved_places.json")
DEFAULT_UNRESOLVED = Path("data/work/sungsikyung_naver_resolution_unresolved.json")
NAVER_SEARCH_URL = "https://m.map.naver.com/search2/search.naver"
USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Mobile/15E148 NAVER(inapp; search; 2000; 12.0.0)"
)


@dataclass(frozen=True)
class Candidate:
    candidate_id: int | str
    youtube_video_id: int
    video_id: str
    title: str
    video_url: str
    query: str
    result_name: str
    result_address: str
    result_phone: str
    result_category: str


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_name(value: str) -> str:
    value = clean(value)
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"\b\d+\s*호점\b", "", value)
    return re.sub(r"[\s·.,'\"`_-]+", "", value).lower()


def normalize_address(value: str) -> str:
    value = clean(value)
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
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = re.sub(r"\b\d+\s*층\b", "", value)
    value = re.sub(r"\b지하\s*\d+\s*층\b", "", value)
    value = re.sub(r"\b[0-9A-Za-z가-힣-]+\s*호\b", "", value)
    return re.sub(r"[\s,./_-]+", "", value).lower()


def address_fragments(value: str) -> list[str]:
    fragments = [value]
    fragments.extend(re.findall(r"\(([^)]{4,})\)", value))
    without_parentheses = re.sub(r"\([^)]*\)", "", value)
    if without_parentheses != value:
        fragments.append(without_parentheses)
    normalized: list[str] = []
    for fragment in fragments:
        normalized_fragment = normalize_address(fragment)
        if len(normalized_fragment) >= 5 and normalized_fragment not in normalized:
            normalized.append(normalized_fragment)
    return normalized


def infer_region(address: str) -> str:
    normalized = clean(address)
    for source, target in (
        ("서울특별시", "서울"),
        ("부산광역시", "부산"),
        ("대구광역시", "대구"),
        ("인천광역시", "인천"),
        ("광주광역시", "광주"),
        ("대전광역시", "대전"),
        ("울산광역시", "울산"),
        ("세종특별자치시", "세종"),
        ("제주특별자치도", "제주"),
        ("강원특별자치도", "강원"),
        ("전북특별자치도", "전북"),
        ("경기도", "경기"),
        ("충청북도", "충북"),
        ("충청남도", "충남"),
        ("전라남도", "전남"),
        ("경상북도", "경북"),
        ("경상남도", "경남"),
    ):
        normalized = normalized.replace(source, target)
    parts = normalized.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else (parts[0] if parts else "")


def load_candidates(
    sqlite_path: Path,
    source: str,
    missing_only: bool,
    limit: int | None,
    video_ids: list[str] | None = None,
) -> list[Candidate]:
    filters = [
        "s.name = ?",
        "p.status = 'needs_review'",
        "trim(p.result_name) != ''",
        "trim(p.result_address) != ''",
    ]
    params: list[Any] = [source]
    scoped_video_ids = sorted(set(video_ids or []))
    if scoped_video_ids:
        placeholders = ",".join("?" for _ in scoped_video_ids)
        filters.append(f"v.video_id in ({placeholders})")
        params.extend(scoped_video_ids)
    if missing_only:
        filters.extend(
            [
                "exists (select 1 from preferred_youtube_transcripts t where t.youtube_video_id = v.id)",
                "not exists (select 1 from video_must_taste_items m where m.youtube_video_id = v.id)",
                """
                not exists (
                  select 1 from youtube_video_restaurants yvr
                  where yvr.youtube_video_id = v.id
                    and yvr.status in ('verified', 'metadata_verified')
                )
                """,
            ]
        )
    limit_sql = "limit ?" if limit else ""
    if limit:
        params.append(limit)
    query = f"""
        select
          p.id,
          p.youtube_video_id,
          v.video_id,
          v.title,
          v.url,
          p.query,
          p.result_name,
          p.result_address,
          coalesce(p.result_phone, ''),
          coalesce(p.result_category, '')
        from place_resolution_candidates p
        join youtube_videos v on v.id = p.youtube_video_id
        join sources s on s.id = v.source_id
        where {' and '.join(filters)}
        order by v.published_at desc, p.result_rank, p.id
        {limit_sql}
    """
    with sqlite3.connect(sqlite_path) as connection:
        rows = connection.execute(query, params).fetchall()
    seen: set[tuple[str, str, str]] = set()
    candidates: list[Candidate] = []
    for row in rows:
        candidate = Candidate(
            candidate_id=int(row[0]),
            youtube_video_id=int(row[1]),
            video_id=str(row[2]),
            title=str(row[3]),
            video_url=str(row[4]),
            query=clean(str(row[5])),
            result_name=clean(str(row[6])),
            result_address=clean(str(row[7])),
            result_phone=clean(str(row[8])),
            result_category=clean(str(row[9])),
        )
        key = (candidate.video_id, candidate.result_name, candidate.result_address)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(candidate)
    return candidates


def load_jsonl_candidates(sqlite_path: Path, input_path: Path, limit: int | None) -> list[Candidate]:
    with sqlite3.connect(sqlite_path) as connection:
        videos = {
            str(row[1]): (int(row[0]), str(row[2]), str(row[3]))
            for row in connection.execute("select id, video_id, title, url from youtube_videos")
        }

    candidates: list[Candidate] = []
    seen: set[tuple[str, str, str]] = set()
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        status = str(item.get("candidate_status") or item.get("verdict") or "candidate")
        if status not in {
            "candidate",
            "needs_review",
            "candidate_only_no_collected_clip_match",
            "candidate_matched_to_collected_clip",
            "candidate_linked",
            "ready_for_place_verification",
            "existing_restaurant_match",
        }:
            continue
        video_ids = item.get("video_ids") or item.get("matched_video_ids") or [item.get("video_id")]
        for video_id_value in video_ids:
            video_id = clean(str(video_id_value or ""))
            if not video_id or video_id not in videos:
                continue
            youtube_video_id, title, video_url = videos[video_id]
            result_name = clean(str(item.get("candidate_name") or item.get("result_name") or ""))
            result_address = clean(
                str(
                    item.get("region_address_clues")
                    or item.get("address_region_clues")
                    or item.get("full_address_clue")
                    or item.get("result_address")
                    or ""
                )
            )
            if not result_name or not result_address:
                continue
            key = (video_id, result_name, result_address)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                Candidate(
                    candidate_id=str(item.get("candidate_id") or f"{input_path.name}:{line_number}"),
                    youtube_video_id=youtube_video_id,
                    video_id=video_id,
                    title=title,
                    video_url=video_url,
                    query=clean(str(item.get("query") or f"{result_name} {result_address}")),
                    result_name=result_name,
                    result_address=result_address,
                    result_phone=clean(str(item.get("result_phone") or item.get("phone") or "")),
                    result_category=clean(
                        str(item.get("result_category") or item.get("category") or "음식점")
                    ),
                )
            )
            if limit and len(candidates) >= limit:
                return candidates
    return candidates


def load_jsonl_candidate_files(
    sqlite_path: Path,
    input_paths: list[Path],
    limit: int | None,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    seen: set[tuple[str, str, str]] = set()
    for input_path in input_paths:
        for candidate in load_jsonl_candidates(sqlite_path, input_path, None):
            key = (candidate.video_id, candidate.result_name, candidate.result_address)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
            if limit and len(candidates) >= limit:
                return candidates
    return candidates


def fetch_search_html(query: str) -> str:
    url = f"{NAVER_SEARCH_URL}?{urllib.parse.urlencode({'query': query})}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def iter_json_values(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_json_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_values(child)


def extract_search_items(html: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for match in re.finditer(r"window\.__RQ_STREAMING_STATE__\.push\((\{.*?\})\);", html, re.DOTALL):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        for value in iter_json_values(payload):
            maybe_items = value.get("items")
            if not isinstance(maybe_items, list):
                continue
            for item in maybe_items:
                if isinstance(item, dict) and item.get("id") and item.get("name"):
                    items.append(item)
    return items


def item_address_fragments(item: dict[str, Any]) -> list[str]:
    fragments: list[str] = []
    for key in ("roadAddress", "address"):
        value = clean(str(item.get(key) or ""))
        if value:
            fragments.append(normalize_address(value))
    full_address = clean(str(item.get("fullAddress") or ""))
    if full_address:
        fragments.append(normalize_address(full_address))
    return [fragment for fragment in fragments if len(fragment) >= 5]


def score_match(candidate: Candidate, item: dict[str, Any]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0
    candidate_name = normalize_name(candidate.result_name)
    item_name = normalize_name(str(item.get("name") or ""))
    if candidate_name and item_name and (candidate_name in item_name or item_name in candidate_name):
        score += 25
        reasons.append("name")

    candidate_addresses = address_fragments(candidate.result_address)
    result_addresses = item_address_fragments(item)
    for candidate_address in candidate_addresses:
        for result_address in result_addresses:
            if (
                candidate_address in result_address
                or result_address in candidate_address
                or (len(candidate_address) >= 8 and candidate_address[-8:] in result_address)
            ):
                score += 70
                reasons.append("address")
                break
        if "address" in reasons:
            break

    candidate_phone = re.sub(r"\D+", "", candidate.result_phone)
    item_phone = re.sub(r"\D+", "", str(item.get("tel") or item.get("virtualTel") or ""))
    if candidate_phone and item_phone and candidate_phone == item_phone:
        score += 10
        reasons.append("phone")

    return score, reasons


def resolve_candidate(candidate: Candidate, delay_seconds: float) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    search_queries = [
        re.sub(r"\([^)]*\)", "", candidate.query).strip(),
        re.sub(r"\([^)]*\)", "", f"{candidate.result_name} {candidate.result_address}").strip(),
        candidate.result_name,
    ]
    deduped_queries = [query for index, query in enumerate(search_queries) if query and query not in search_queries[:index]]
    attempts: list[dict[str, Any]] = []
    for query in deduped_queries:
        if delay_seconds:
            time.sleep(delay_seconds)
        try:
            html = fetch_search_html(query)
            items = extract_search_items(html)
        except Exception as error:  # noqa: BLE001 - network and Naver response failures are non-fatal per row.
            attempts.append({"query": query, "error": str(error)})
            continue
        ranked: list[tuple[int, list[str], dict[str, Any]]] = []
        for item in items:
            score, reasons = score_match(candidate, item)
            ranked.append((score, reasons, item))
        ranked.sort(key=lambda value: value[0], reverse=True)
        attempts.append(
            {
                "query": query,
                "item_count": len(items),
                "top": [
                    {
                        "score": score,
                        "reasons": reasons,
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "roadAddress": item.get("roadAddress"),
                        "address": item.get("address"),
                    }
                    for score, reasons, item in ranked[:3]
                ],
            }
        )
        if ranked and ranked[0][0] >= 70 and "address" in ranked[0][1]:
            best_score, reasons, item = ranked[0]
            address = clean(str(item.get("roadAddress") or item.get("address") or candidate.result_address))
            naver_id = str(item["id"])
            verified = {
                "video_id": candidate.video_id,
                "resolved_name": clean(str(item.get("name") or candidate.result_name)),
                "display_name": clean(str(item.get("name") or candidate.result_name)),
                "local_name": clean(str(item.get("name") or candidate.result_name)),
                "country_code": "KR",
                "region": infer_region(address),
                "address": address,
                "phone": clean(str(item.get("tel") or item.get("virtualTel") or candidate.result_phone)),
                "category": clean(str(item.get("category") or candidate.result_category)),
                "map_provider": "naver_map",
                "naver_map_id": naver_id,
                "map_url": f"https://map.naver.com/p/entry/place/{naver_id}?placePath=%2Fhome",
                "evidence_url": f"{NAVER_SEARCH_URL}?{urllib.parse.urlencode({'query': query})}",
                "confidence": 0.98 if "name" in reasons else 0.93,
                "status": "metadata_verified",
                "notes": (
                    f"Naver mobile search matched candidate address for `{candidate.result_name}` "
                    f"from video metadata; match score {best_score}."
                ),
            }
            debug = {"candidate_id": candidate.candidate_id, "attempts": attempts}
            return verified, debug
    return None, {"candidate_id": candidate.candidate_id, "video_id": candidate.video_id, "attempts": attempts}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve Naver Map /p/search candidates to numeric place IDs.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--source", default="성시경의 먹을텐데")
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        action="append",
        help="Resolve reviewed JSONL candidates instead of loading place_resolution_candidates. Repeat for multiple files.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--unresolved-output", type=Path, default=DEFAULT_UNRESOLVED)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--video-id",
        action="append",
        default=[],
        help="Limit processing to this YouTube video ID. Repeatable.",
    )
    parser.add_argument("--delay-seconds", type=float, default=0.08)
    parser.add_argument(
        "--all-candidates",
        action="store_true",
        help="Resolve all matching needs_review candidates, not only transcript-backed videos missing taste/map rows.",
    )
    args = parser.parse_args()

    candidates = (
        load_jsonl_candidate_files(args.sqlite, args.input_jsonl, args.limit)
        if args.input_jsonl
        else load_candidates(
            args.sqlite,
            args.source,
            missing_only=not args.all_candidates,
            limit=args.limit,
            video_ids=args.video_id,
        )
    )
    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    seen_places: set[tuple[str, str]] = set()
    for index, candidate in enumerate(candidates, start=1):
        verified, debug = resolve_candidate(candidate, args.delay_seconds)
        if verified is None:
            unresolved.append(
                {
                    "video_id": candidate.video_id,
                    "title": candidate.title,
                    "result_name": candidate.result_name,
                    "result_address": candidate.result_address,
                    **debug,
                }
            )
        else:
            key = (verified["video_id"], verified["naver_map_id"])
            if key not in seen_places:
                seen_places.add(key)
                resolved.append(verified)
        if index % 25 == 0:
            print(f"Processed {index}/{len(candidates)} candidates; resolved={len(resolved)} unresolved={len(unresolved)}", file=sys.stderr)

    payload = {
        "source": args.source,
        "verified_at": date.today().isoformat(),
        "items": resolved,
    }
    write_json(args.output, payload)
    write_json(
        args.unresolved_output,
        {
            "source": args.source,
            "checked_at": date.today().isoformat(),
            "candidate_count": len(candidates),
            "resolved_count": len(resolved),
            "unresolved_count": len(unresolved),
            "items": unresolved,
        },
    )
    print(f"Resolved {len(resolved)} of {len(candidates)} candidates")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.unresolved_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
