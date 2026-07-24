#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.parse import urlparse

SKILLS_DIR = Path(__file__).resolve().parents[2]
YOUTUBE_SCRIPTS = SKILLS_DIR / "tastyroad-youtube-channel-collect" / "scripts"
sys.path.insert(1, str(YOUTUBE_SCRIPTS))

from collect_youtube import DEFAULT_SQLITE, fetch_video_details
from pipeline_schema import ensure_pipeline_schema


MAP_URL_RE = re.compile(r"https?://(?:naver\.me|maps\.app\.goo\.gl|www\.google\.com/maps)[^\s)]+")
NAVER_PLACE_ID_RE = re.compile(r"(?:/entry/place/|/place/)(\d+)")
NAVER_SHARE_ID_RE = re.compile(r"[?&](?:id|pinId)=(\d+)")
NAVER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
DOMESTIC_ADDRESS_RE = re.compile(
    r"^(서울|경기|인천|부산|대구|대전|광주|울산|세종|제주|강원|충북|충남|전북|전남|경북|경남)"
)
ADDRESS_HINT_RE = re.compile(
    r"(서울|경기|인천|부산|대구|대전|광주|울산|세종|제주|강원|충북|충남|전북|전남|경북|경남|"
    r"도로|길|읍|면|동|구|시|군|로\s?\d|Carrer|Rue|Via|Av\.|Avenue|Pl\.|Plaça|Dr,|홍콩|중국|"
    r"스페인|프랑스|이탈리아|Tokyo|Japan|Madrid|Barcelona|Paris|Roma|Wan Chai)"
)
OVERSEAS_HINT_RE = re.compile(
    r"(도쿄|오사카|일본|싱가포르|독일|베를린|홍콩|중국|스페인|프랑스|이탈리아|"
    r"Tokyo|Osaka|Japan|Singapore|Berlin|Germany|Hong Kong|Madrid|Barcelona|Paris|Roma|"
    r"Wan Chai|Rangoon|Bukit|Raffles|Killiney|Neil Rd)",
    re.IGNORECASE,
)
NON_RESTAURANT_TITLE_RE = re.compile(
    r"(#shorts|매주 금요일|프로필사진|봉사활동|몸무게|체력|피자마루 신메뉴|광고|리뷰😂|성심당 약|"
    r"먹방계|쇼핑법|영어공부|멕시코인은|치킨 맞히기|강아지|쿡방의 저주|솔직한 리뷰|"
    r"주접과 조롱|딸기|월드콘|장비보다|심란한)"
)
NON_RESTAURANT_INFO_RE = re.compile(
    r"(김사원\s*세끼|김사원세끼|픽스|시크릿|한정특가|이벤트|노포\s*투어|구매\s*링크)"
)
NON_PLACE_BRACKET_RE = re.compile(
    r"(최자로드\s*시즌|CHOIZA\s*ROAD|Video Source Support|매주\s*\([^)]*\)\s*오후|미식\s*에세이)",
    re.IGNORECASE,
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


def normalize_place_name(value: str) -> str:
    return clean(re.sub(r"^\d+\.\s*", "", value))


def is_address(value: str) -> bool:
    if re.search(r"(매주|공개|시즌|에세이)", value):
        return False
    return bool(ADDRESS_HINT_RE.search(value)) and not value.startswith(("http://", "https://"))


def is_domestic_address(value: str) -> bool:
    return bool(DOMESTIC_ADDRESS_RE.search(clean(value)))


def is_overseas_place(place: Place, context: str = "") -> bool:
    if is_domestic_address(place.address):
        return False
    return bool(OVERSEAS_HINT_RE.search(f"{place.name} {place.address} {context}"))


def is_naver_map_url(url: str) -> bool:
    return "naver.me" in url or "map.naver.com" in url


def is_real_naver_place_url(url: str) -> bool:
    return "naver.me" in url or "/p/entry/place/" in url or "/place/" in url


def extract_naver_map_id(url: str) -> str:
    match = NAVER_PLACE_ID_RE.search(url) or NAVER_SHARE_ID_RE.search(url)
    return match.group(1) if match else ""


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def normalize_naver_place_url(url: str) -> str:
    naver_map_id = extract_naver_map_id(url)
    if naver_map_id:
        return f"https://map.naver.com/p/entry/place/{naver_map_id}?placePath=%2Fhome"
    return url


def resolve_naver_map_url(url: str) -> str:
    if not re.match(r"https?://naver\.me/", url):
        return normalize_naver_place_url(url)
    url = re.sub(r"^http://naver\.me/", "https://naver.me/", url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": NAVER_USER_AGENT,
            "Accept": "text/html,*/*",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        },
    )
    opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        with opener.open(request, timeout=15) as response:
            return normalize_naver_place_url(response.geturl())
    except urllib.error.HTTPError as error:
        if 300 <= error.code < 400:
            location = error.headers.get("Location", "")
            if location.startswith("/"):
                parsed = urlparse(url)
                location = f"{parsed.scheme}://{parsed.netloc}{location}"
            return normalize_naver_place_url(location)
        raise


def resolve_naver_map_details(url: str) -> tuple[str, str]:
    naver_map_id = extract_naver_map_id(url)
    if naver_map_id:
        return naver_map_id, url
    if not re.match(r"https?://naver\.me/", url):
        return "", url
    try:
        resolved_url = resolve_naver_map_url(url)
    except Exception as error:  # noqa: BLE001 - naver.me redirects can fail transiently.
        print(f"warning: failed to resolve Naver map URL {url}: {error}")
        return "", url
    return extract_naver_map_id(resolved_url), resolved_url


def map_provider(url: str, country_code: str) -> str:
    if is_naver_map_url(url):
        return "naver_map"
    return "naver_map"


def search_url(provider: str, query: str) -> str:
    encoded = quote(query)
    if provider == "naver_map":
        return f"https://map.naver.com/p/search/{encoded}"
    if provider == "kakao_map":
        return f"https://map.kakao.com/?q={encoded}"
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"


def infer_country(address: str, name: str = "") -> str:
    value = f"{address} {name}"
    if any(token in value for token in ("스페인", "Barcelona", "Madrid")):
        return "ES"
    if any(token in value for token in ("프랑스", "Paris", "Rue ")):
        return "FR"
    if any(token in value for token in ("이탈리아", "Roma", "Via ")):
        return "IT"
    if "홍콩" in value or "Wan Chai" in value:
        return "HK"
    if "중국" in value or "Dongcheng" in value:
        return "CN"
    if any(token in value for token in ("Tokyo", "Japan", "일본", "도쿄", "오사카")):
        return "JP"
    if any(token in value for token in ("Singapore", "싱가포르", "Rangoon", "Lau Pa Sat")):
        return "SG"
    if any(token in value for token in ("Berlin", "Germany", "독일")):
        return "DE"
    return "KR" if address.strip() else ""


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
        name = normalize_place_name(match.group(2))
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
        name = normalize_place_name(match.group(1))
        if name in {"식당정보", "BGM 정보", "BGM정보", "구매 링크", "사진 출처", "사진출처"}:
            continue
        if NON_PLACE_BRACKET_RE.search(name):
            continue
        if NON_RESTAURANT_INFO_RE.search(name):
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
        name = normalize_place_name(lines[cursor])
        if name.startswith("[") and name.endswith("]"):
            continue
        if NON_RESTAURANT_INFO_RE.search(name):
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


def parse_pin_name_lines(description: str) -> list[Place]:
    places: list[Place] = []
    for line in description.splitlines():
        if "📍" not in line:
            continue
        for raw_name in line.split("📍", 1)[1].split("|"):
            name = normalize_place_name(re.sub(r"^#", "", raw_name.strip()))
            name = re.sub(r"\s+#.*$", "", name).strip()
            name = re.sub(
                r"^(?:월요일|화요일|수요일|목요일|금요일|토요일|일요일),\s*",
                "",
                name,
            ).strip()
            if name and name not in {"도쿄"}:
                places.append(Place(name=name, notes="핀 식당정보"))
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
    result: list[Place] = []
    for parser in (
        parse_company_blocks,
        parse_numbered_blocks,
        parse_bracket_blocks,
        parse_plain_store_info,
        parse_pin_name_lines,
        parse_pin_lines,
    ):
        for place in parser(description):
            normalized_name = normalize_place_name(place.name)
            if not normalized_name:
                continue
            alias_index = next(
                (
                    index
                    for index, existing in enumerate(result)
                    if (
                        normalized_name == existing.name
                        or normalized_name.endswith(f" {existing.name}")
                        or existing.name.endswith(f" {normalized_name}")
                    )
                    and (
                        not place.address
                        or not existing.address
                        or place.address == existing.address
                    )
                ),
                None,
            )
            normalized_place = Place(
                name=normalized_name,
                address=place.address,
                phone=place.phone,
                category=place.category,
                map_url=place.map_url,
                notes=place.notes,
            )
            if alias_index is None:
                result.append(normalized_place)
                continue
            existing = result[alias_index]
            preferred_name = (
                normalized_name
                if len(normalized_name) < len(existing.name)
                else existing.name
            )
            result[alias_index] = Place(
                name=preferred_name,
                address=existing.address or normalized_place.address,
                phone=existing.phone or normalized_place.phone,
                category=existing.category or normalized_place.category,
                map_url=existing.map_url or normalized_place.map_url,
                notes=existing.notes or normalized_place.notes,
            )
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
        update youtube_videos
        set
          description = ?,
          duration_seconds = coalesce(?, duration_seconds),
          thumbnail_url = coalesce(nullif(?, ''), thumbnail_url),
          tags = ?,
          chapters = ?
        where video_id = ?
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


def place_search_values(place: Place) -> tuple[str, str, str, float]:
    provider = "naver_map"
    query = clean(f"{place.name} {place.address}")
    map_url = place.map_url if is_real_naver_place_url(place.map_url) else ""
    confidence = 0.9 if place.address else 0.45
    return provider, query, map_url, confidence


def upsert_place_resolution_candidate(
    connection: sqlite3.Connection,
    youtube_video_id: int,
    video_url: str,
    place: Place,
    now: str,
    *,
    status: str,
) -> None:
    provider, query, map_url, confidence = place_search_values(place)
    connection.execute(
        """
        insert into place_resolution_candidates (
          youtube_video_id, search_provider, query, result_name,
          result_address, result_phone, result_category, result_url,
          result_rank, confidence, status, evidence_json, searched_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(youtube_video_id, search_provider, query, result_url) do update set
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
            youtube_video_id,
            provider,
            query,
            place.name,
            place.address,
            place.phone,
            place.category,
            map_url,
            1,
            confidence,
            status,
            json.dumps(
                {
                    "source": "video_metadata",
                    "notes": place.notes,
                    "video_url": video_url,
                    "missing_address": not bool(place.address.strip()),
                },
                ensure_ascii=False,
            ),
            now,
        ),
    )


def upsert_mapping(connection: sqlite3.Connection, youtube_video_id: int, video_url: str, place: Place, now: str) -> bool:
    if not place.address.strip():
        raise ValueError(f"Cannot promote {place.name!r} without a verified address")
    if is_overseas_place(place):
        raise ValueError(f"Cannot promote overseas place {place.name!r} in Naver-only mode")

    country_code = infer_country(place.address, place.name)
    region = infer_region(place.address)
    provider, _query, map_url, confidence = place_search_values(place)
    naver_map_id, resolved_map_url = resolve_naver_map_details(map_url)

    if not naver_map_id:
        upsert_place_resolution_candidate(
            connection,
            youtube_video_id,
            video_url,
            place,
            now,
            status="needs_review",
        )
        return False

    existing = connection.execute(
        "select id from restaurants where naver_map_id = ?",
        (naver_map_id,),
    ).fetchone()
    if existing is None:
        existing = connection.execute(
            """
            select id from restaurants
            where country_code = ? and address = ? and canonical_name = ?
            """,
            (country_code, place.address, place.name),
        ).fetchone()

    if existing is not None:
        restaurant_id = int(existing[0])
        connection.execute(
            """
            update restaurants
            set
              naver_map_id = ?,
              display_name = ?,
              local_name = ?,
              region = ?,
              phone = coalesce(nullif(?, ''), phone),
              category = coalesce(nullif(?, ''), category),
              updated_at = ?
            where id = ?
            """,
            (
                naver_map_id,
                place.name,
                place.name,
                region,
                place.phone,
                place.category,
                now,
                restaurant_id,
            ),
        )
    else:
        connection.execute(
            """
            insert into restaurants (
              naver_map_id, canonical_name, display_name, local_name, country_code, region,
              address, phone, category, created_at, updated_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                naver_map_id,
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
                "select id from restaurants where naver_map_id = ?",
                (naver_map_id,),
            ).fetchone()[0]
        )

    upsert_place_resolution_candidate(
        connection,
        youtube_video_id,
        video_url,
        place,
        now,
        status="selected",
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
            resolved_map_url,
            video_url,
            confidence,
            "metadata_verified",
            place.notes,
            now,
        ),
    )

    connection.execute(
        """
        insert into youtube_video_restaurants (
          restaurant_id, youtube_video_id, confidence, status, verified_at
        )
        values (?, ?, ?, ?, ?)
        on conflict(restaurant_id, youtube_video_id) do update set
          confidence = excluded.confidence,
          status = excluded.status,
          verified_at = excluded.verified_at
        """,
        (restaurant_id, youtube_video_id, confidence, "metadata_verified", now),
    )
    return True


def process_backlog(
    sqlite_path: Path,
    dry_run: bool = False,
    enrich_missing_metadata: bool = True,
    source: str = "",
) -> dict[str, int]:
    now = datetime.now(timezone.utc).isoformat()
    counts = {
        "reviewed": 0,
        "metadata_refreshed": 0,
        "mapped_places": 0,
        "places_needing_address": 0,
        "places_needing_naver_map_id": 0,
        "skipped_overseas_places": 0,
        "not_restaurant_or_uncertain": 0,
    }
    connection_target = f"file:{sqlite_path}?mode=ro" if dry_run else str(sqlite_path)
    with sqlite3.connect(connection_target, uri=dry_run) as connection:
        if not dry_run:
            ensure_pipeline_schema(connection)
        rows = connection.execute(
            """
            select
              v.youtube_video_id,
              v.video_id,
              v.title,
              v.url,
              v.review_status,
              v.mapping_status,
              c.description
            from video_pipeline_status v
            join youtube_videos c on c.id = v.youtube_video_id
            where v.mapping_status != 'mapping_verified'
              and (? = '' or v.source = ?)
            order by v.published_at desc, v.youtube_video_id desc
            """,
            (source, source),
        ).fetchall()

        for youtube_video_id, video_id, title, video_url, review_status, _mapping_status, description in rows:
            description_text = str(description or "")
            places = extract_places(description_text)
            if enrich_missing_metadata and should_refresh_metadata(str(review_status), str(title), description_text, places):
                try:
                    description_text = refresh_candidate_metadata(connection, str(video_id), str(video_url))
                    places = extract_places(description_text)
                    counts["metadata_refreshed"] += 1
                except Exception as error:
                    print(f"warning: failed to refresh metadata for {video_id}: {error}")

            context = f"{title}\n{description_text}"
            overseas_places = [
                place for place in places if is_overseas_place(place, context)
            ]
            places = [
                place for place in places if not is_overseas_place(place, context)
            ]
            counts["skipped_overseas_places"] += len(overseas_places)

            if str(review_status) == "unreviewed" or (
                places and str(review_status).startswith("reviewed_restaurant")
            ):
                counts["reviewed"] += 1
                if not dry_run:
                    upsert_review(connection, str(video_id), places, str(title), now)

            if places:
                for place in places:
                    if place.address.strip():
                        if dry_run:
                            _provider, _query, map_url, _confidence = place_search_values(place)
                            mapped = bool(extract_naver_map_id(map_url))
                        else:
                            mapped = upsert_mapping(connection, int(youtube_video_id), str(video_url), place, now)
                        if mapped:
                            counts["mapped_places"] += 1
                        else:
                            counts["places_needing_naver_map_id"] += 1
                    else:
                        if not dry_run:
                            upsert_place_resolution_candidate(
                                connection,
                                int(youtube_video_id),
                                str(video_url),
                                place,
                                now,
                                status="needs_review",
                            )
                        counts["places_needing_address"] += 1
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
    parser.add_argument(
        "--source",
        default="",
        help="Limit processing to one source display name, for example 김사원세끼.",
    )
    args = parser.parse_args()

    counts = process_backlog(
        args.sqlite,
        dry_run=args.dry_run,
        enrich_missing_metadata=not args.skip_enrich_missing_metadata,
        source=args.source,
    )
    for key, value in counts.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
