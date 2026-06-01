#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from collect_youtube import DEFAULT_SQLITE, fetch_video_details
from pipeline_schema import ensure_pipeline_schema


MAP_URL_RE = re.compile(r"https?://(?:naver\.me|maps\.app\.goo\.gl|www\.google\.com/maps)[^\s)]+")
ADDRESS_HINT_RE = re.compile(
    r"(서울|경기|인천|부산|대구|대전|광주|울산|세종|제주|강원|충북|충남|전북|전남|경북|경남|"
    r"도로|길|읍|면|동|구|시|군|로\s?\d|Carrer|Rue|Via|Av\.|Avenue|Pl\.|Plaça|Dr,|홍콩|중국|"
    r"스페인|프랑스|이탈리아|Tokyo|Japan|Madrid|Barcelona|Paris|Roma|Wan Chai)"
)
NON_RESTAURANT_TITLE_RE = re.compile(
    r"(#shorts|매주 금요일|프로필사진|봉사활동|몸무게|체력|피자마루 신메뉴|광고|리뷰😂|성심당 약|"
    r"먹방계|쇼핑법|영어공부|멕시코인은|치킨 맞히기|강아지|쿡방의 저주|솔직한 리뷰|"
    r"주접과 조롱|딸기|월드콘|장비보다|심란한)"
)


@dataclass(frozen=True)
class Place:
    name: str
    address: str = ""
    phone: str = ""
    category: str = ""
    map_url: str = ""
    notes: str = ""


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" -:：\t")


def is_address(value: str) -> bool:
    return bool(ADDRESS_HINT_RE.search(value)) and not value.startswith(("http://", "https://"))


def map_provider(url: str, country_code: str) -> str:
    if "naver.me" in url or "map.naver.com" in url:
        return "naver_map"
    if "kakao" in url:
        return "kakao_map"
    if "maps.app.goo.gl" in url or "google.com/maps" in url:
        return "google_maps"
    return "naver_map" if country_code == "KR" else "google_maps"


def search_url(provider: str, query: str) -> str:
    encoded = quote(query)
    if provider == "naver_map":
        return f"https://map.naver.com/p/search/{encoded}"
    if provider == "kakao_map":
        return f"https://map.kakao.com/?q={encoded}"
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"


def infer_country(address: str) -> str:
    if any(token in address for token in ("스페인", "Barcelona", "Madrid")):
        return "ES"
    if any(token in address for token in ("프랑스", "Paris", "Rue ")):
        return "FR"
    if any(token in address for token in ("이탈리아", "Roma", "Via ")):
        return "IT"
    if "홍콩" in address or "Wan Chai" in address:
        return "HK"
    if "중국" in address or "Dongcheng" in address:
        return "CN"
    if any(token in address for token in ("Tokyo", "Japan", "일본")):
        return "JP"
    return "KR"


def infer_region(address: str) -> str:
    value = clean(address)
    if not value:
        return ""
    if any(value.startswith(prefix) for prefix in ("서울", "경기", "인천", "부산", "대구", "대전", "광주", "울산", "세종", "제주")):
        parts = value.split()
        return " ".join(parts[:2]) if len(parts) >= 2 else parts[0]
    for token in ("Barcelona", "Madrid", "Paris", "Roma", "Wan Chai", "Dongcheng"):
        if token in value:
            return token
    return value.split(",")[-1].strip() if "," in value else value.split()[0]


def parse_company_blocks(description: str) -> list[Place]:
    places: list[Place] = []
    blocks = re.split(r"\n\s*\(\d+\)\s*\n|\n\s*(?=\*식당정보)", description)
    for block in blocks:
        if "식당명" not in block or "식당위치" not in block:
            continue
        name = field_after(block, r"식당명\s*:\s*(.+)")
        address = field_after(block, r"식당위치\s*:\s*(.+)")
        phone = field_after(block, r"전화번호\s*:\s*(.+)")
        if name:
            places.append(Place(name=name, address=address, phone=phone, notes="회사랑 식당정보"))
    return places


def field_after(block: str, pattern: str) -> str:
    match = re.search(pattern, block)
    return clean(match.group(1)) if match else ""


def parse_numbered_blocks(description: str) -> list[Place]:
    lines = [line.strip() for line in description.splitlines()]
    places: list[Place] = []
    index = 0
    while index < len(lines):
        match = re.match(r"(\d+)\.\s+(.+)", lines[index])
        if not match:
            index += 1
            continue
        name = clean(match.group(2))
        if "식당X" in name:
            index += 1
            continue
        address = ""
        url = ""
        if index + 1 < len(lines) and is_address(lines[index + 1]):
            address = clean(lines[index + 1])
        if index + 2 < len(lines):
            url_match = MAP_URL_RE.search(lines[index + 2])
            url = url_match.group(0) if url_match else ""
        places.append(Place(name=name, address=address, map_url=url, notes="번호 목록 식당정보"))
        index += 1
    return places


def parse_bracket_blocks(description: str) -> list[Place]:
    lines = [line.strip() for line in description.splitlines()]
    places: list[Place] = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"\[(.+?)\]", line)
        if not match:
            continue
        name = clean(match.group(1))
        if name in {"식당정보", "BGM 정보", "구매 링크"}:
            continue
        address = ""
        phone = ""
        url = ""
        for next_line in lines[index + 1 : index + 6]:
            if not next_line or next_line.startswith("#"):
                continue
            if MAP_URL_RE.search(next_line):
                url = MAP_URL_RE.search(next_line).group(0)  # type: ignore[union-attr]
            normalized = re.sub(r"^-?\s*(주소|식당위치)\s*:\s*", "", next_line).strip()
            normalized = re.sub(r"^-?\s*전화번호\s*:\s*", "", normalized).strip()
            if not address and is_address(normalized):
                address = clean(normalized)
            elif not phone and re.search(r"(\+?\d[\d\s-]{6,})", normalized):
                phone = clean(normalized)
        places.append(Place(name=name, address=address, phone=phone, map_url=url, notes="대괄호 식당정보"))
    return places


def parse_plain_store_info(description: str) -> list[Place]:
    lines = [line.strip() for line in description.splitlines()]
    places: list[Place] = []
    for index, line in enumerate(lines):
        if line not in {"* 가게 정보", "* 가게 정보 ", "[식당정보]"}:
            continue
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor]:
            cursor += 1
        if cursor >= len(lines):
            continue
        name = clean(lines[cursor])
        if name.startswith("[") and name.endswith("]"):
            continue
        address = ""
        phone = ""
        url = ""
        for next_line in lines[cursor + 1 : cursor + 6]:
            if MAP_URL_RE.search(next_line):
                url = MAP_URL_RE.search(next_line).group(0)  # type: ignore[union-attr]
            normalized = re.sub(r"^-?\s*(주소|식당위치)\s*:\s*", "", next_line).strip()
            normalized = re.sub(r"^-?\s*전화번호\s*:\s*", "", normalized).strip()
            if not address and is_address(normalized):
                address = clean(normalized)
            elif not phone and re.search(r"(\+?\d[\d\s-]{6,})", normalized):
                phone = clean(normalized)
        if name and not name.startswith("*"):
            places.append(Place(name=name, address=address, phone=phone, map_url=url, notes="일반 식당정보"))
    return places


def parse_pin_lines(description: str) -> list[Place]:
    places: list[Place] = []
    for line in description.splitlines():
        if "📍" not in line:
            continue
        url_match = MAP_URL_RE.search(line)
        if not url_match:
            continue
        name = clean(line.split("📍", 1)[1].split(url_match.group(0), 1)[0])
        if not name or "맛집" in name and len(name) > 25:
            continue
        places.append(Place(name=name, map_url=url_match.group(0), notes="지도 링크 식당정보"))
    return places


def extract_places(description: str) -> list[Place]:
    seen: set[tuple[str, str, str]] = set()
    result: list[Place] = []
    for parser in (
        parse_company_blocks,
        parse_numbered_blocks,
        parse_bracket_blocks,
        parse_plain_store_info,
        parse_pin_lines,
    ):
        for place in parser(description):
            key = (place.name, place.address, place.map_url)
            if place.name and key not in seen:
                seen.add(key)
                result.append(place)
    return result


def should_refresh_metadata(review_status: str, title: str, description: str, places: list[Place]) -> bool:
    if places or description.strip():
        return False
    if review_status == "unreviewed":
        return "맛집" in title or "식당" in title or "먹을텐데" in title
    return review_status.startswith("reviewed_restaurant")


def refresh_candidate_metadata(
    connection: sqlite3.Connection,
    video_id: str,
    video_url: str,
) -> str:
    item = fetch_video_details(video_url)
    description = str(item.get("description") or "")
    connection.execute(
        """
        update mention_candidates
        set
          description = ?,
          duration_seconds = coalesce(?, duration_seconds),
          thumbnail_url = coalesce(nullif(?, ''), thumbnail_url),
          tags = ?,
          chapters = ?
        where external_id = ?
        """,
        (
            description,
            item.get("duration") if isinstance(item.get("duration"), (int, float)) else None,
            str(item.get("thumbnail") or ""),
            json.dumps(item.get("tags") if isinstance(item.get("tags"), list) else [], ensure_ascii=False),
            json.dumps(item.get("chapters") if isinstance(item.get("chapters"), list) else [], ensure_ascii=False),
            video_id,
        ),
    )
    return description


def upsert_review(connection: sqlite3.Connection, video_id: str, places: list[Place], title: str, now: str) -> None:
    if places:
        decision = "restaurant_intro"
        confidence = 0.92
        names = [place.name for place in places]
        reason = "Metadata includes named restaurant/place information."
    elif NON_RESTAURANT_TITLE_RE.search(title):
        decision = "not_restaurant"
        confidence = 0.88
        names = []
        reason = "Metadata indicates short, promo, product, or general eating content without an identifiable venue."
    else:
        decision = "uncertain"
        confidence = 0.5
        names = []
        reason = "No reliable restaurant/place entity could be extracted from metadata."

    connection.execute(
        """
        insert into agent_video_reviews (
          external_id, decision, confidence, restaurant_names,
          detected_restaurant_count, reason, reviewer, reviewed_at
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
            confidence,
            json.dumps(names, ensure_ascii=False),
            len(places),
            reason,
            "metadata_backlog",
            now,
        ),
    )


def upsert_mapping(connection: sqlite3.Connection, mention_candidate_id: int, video_url: str, place: Place, now: str) -> None:
    country_code = infer_country(place.address)
    region = infer_region(place.address)
    provider = map_provider(place.map_url, country_code)
    query = clean(f"{place.name} {place.address}")
    map_url = place.map_url or search_url(provider, query)
    confidence = 0.9 if place.address else 0.76

    connection.execute(
        """
        insert into restaurants (
          canonical_name, display_name, local_name, country_code, region,
          address, phone, category, created_at, updated_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(country_code, address, canonical_name) do update set
          display_name = excluded.display_name,
          local_name = excluded.local_name,
          region = excluded.region,
          phone = coalesce(nullif(excluded.phone, ''), restaurants.phone),
          category = coalesce(nullif(excluded.category, ''), restaurants.category),
          updated_at = excluded.updated_at
        """,
        (
            place.name,
            place.name,
            place.name,
            country_code,
            region,
            place.address,
            place.phone,
            place.category,
            now,
            now,
        ),
    )
    restaurant_id = int(
        connection.execute(
            """
            select id from restaurants
            where country_code = ? and address = ? and canonical_name = ?
            """,
            (country_code, place.address, place.name),
        ).fetchone()[0]
    )

    connection.execute(
        """
        insert into place_resolution_candidates (
          mention_candidate_id, search_provider, query, result_name,
          result_address, result_phone, result_category, result_url,
          result_rank, confidence, status, evidence_json, searched_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(mention_candidate_id, search_provider, query, result_url) do update set
          result_name = excluded.result_name,
          result_address = excluded.result_address,
          result_phone = excluded.result_phone,
          result_category = excluded.result_category,
          confidence = excluded.confidence,
          status = excluded.status,
          evidence_json = excluded.evidence_json,
          searched_at = excluded.searched_at
        """,
        (
            mention_candidate_id,
            provider,
            query,
            place.name,
            place.address,
            place.phone,
            place.category,
            map_url,
            1,
            confidence,
            "selected",
            json.dumps({"source": "video_metadata", "notes": place.notes, "video_url": video_url}, ensure_ascii=False),
            now,
        ),
    )

    connection.execute(
        """
        insert into place_links (
          restaurant_id, provider, url, evidence_url, confidence,
          status, notes, verified_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(restaurant_id, provider, url) do update set
          evidence_url = excluded.evidence_url,
          confidence = excluded.confidence,
          status = excluded.status,
          notes = excluded.notes,
          verified_at = excluded.verified_at
        """,
        (
            restaurant_id,
            provider,
            map_url,
            video_url,
            confidence,
            "metadata_verified",
            place.notes,
            now,
        ),
    )

    connection.execute(
        """
        insert into mentions (
          restaurant_id, mention_candidate_id, confidence, status, verified_at
        )
        values (?, ?, ?, ?, ?)
        on conflict(restaurant_id, mention_candidate_id) do update set
          confidence = excluded.confidence,
          status = excluded.status,
          verified_at = excluded.verified_at
        """,
        (restaurant_id, mention_candidate_id, confidence, "metadata_verified", now),
    )


def process_backlog(sqlite_path: Path, dry_run: bool = False, enrich_missing_metadata: bool = True) -> dict[str, int]:
    now = datetime.now(timezone.utc).isoformat()
    counts = {
        "reviewed": 0,
        "metadata_refreshed": 0,
        "mapped_places": 0,
        "not_restaurant_or_uncertain": 0,
    }
    with sqlite3.connect(sqlite_path) as connection:
        ensure_pipeline_schema(connection)
        rows = connection.execute(
            """
            select
              v.mention_candidate_id,
              v.video_id,
              v.title,
              v.url,
              v.review_status,
              v.mapping_status,
              c.description
            from video_pipeline_status v
            join mention_candidates c on c.id = v.mention_candidate_id
            where v.mapping_status != 'mapping_verified'
            order by v.published_at desc, v.mention_candidate_id desc
            """
        ).fetchall()

        for mention_candidate_id, video_id, title, video_url, review_status, _mapping_status, description in rows:
            description_text = str(description or "")
            places = extract_places(description_text)
            if enrich_missing_metadata and should_refresh_metadata(str(review_status), str(title), description_text, places):
                try:
                    description_text = refresh_candidate_metadata(connection, str(video_id), str(video_url))
                    places = extract_places(description_text)
                    counts["metadata_refreshed"] += 1
                except Exception as error:
                    print(f"warning: failed to refresh metadata for {video_id}: {error}")

            if str(review_status) == "unreviewed":
                counts["reviewed"] += 1
                if not dry_run:
                    upsert_review(connection, str(video_id), places, str(title), now)

            if places:
                for place in places:
                    counts["mapped_places"] += 1
                    if not dry_run:
                        upsert_mapping(connection, int(mention_candidate_id), str(video_url), place, now)
            elif str(review_status) == "unreviewed":
                counts["not_restaurant_or_uncertain"] += 1

        if not dry_run:
            ensure_pipeline_schema(connection)

    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Process collected videos through review and metadata-backed place mapping.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-enrich-missing-metadata",
        action="store_true",
        help="Do not re-fetch YouTube metadata for restaurant-like rows with empty descriptions.",
    )
    args = parser.parse_args()

    counts = process_backlog(
        args.sqlite,
        dry_run=args.dry_run,
        enrich_missing_metadata=not args.skip_enrich_missing_metadata,
    )
    for key, value in counts.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
