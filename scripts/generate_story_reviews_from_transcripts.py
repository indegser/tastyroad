#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collect_youtube import DEFAULT_SQLITE
from process_video_stories import DEFAULT_INPUT as DEFAULT_STORY_REVIEWS


MENU_KEYWORDS = (
    "족발",
    "보쌈",
    "칼국수",
    "우족",
    "사골",
    "치킨",
    "양념",
    "고추",
    "김밥",
    "고기",
    "갈비",
    "오겹살",
    "삼겹살",
    "회",
    "숙성회",
    "초밥",
    "참치",
    "게장",
    "순대",
    "순대국",
    "매운탕",
    "해장국",
    "감자탕",
    "곱창",
    "막국수",
    "낙지",
    "장어",
    "오리",
    "북경오리",
    "스시",
    "파스타",
    "와인",
    "뷔페",
    "오마카세",
    "맥주",
    "소주",
    "밥",
    "국물",
    "육수",
    "면",
    "튀김",
    "소스",
    "김치",
)


SOURCE_REVIEWER = {
    "성시경의 먹을텐데": "성시경",
    "비밀이야": "비밀이야",
    "맛있는 녀석들": "출연진",
    "김사원세끼": "리뷰어",
    "회사랑": "리뷰어",
    "쯔양": "쯔양",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_names(raw_names: str) -> list[str]:
    try:
        values = json.loads(raw_names)
    except json.JSONDecodeError:
        return []
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def clean_title(title: str) -> str:
    value = re.sub(r"\s+", " ", title).strip()
    value = re.sub(r"^\[sub\]\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^성시경의\s*먹을텐데\s*[|lㅣ]?\s*", "", value)
    return value


def representative_place(names: list[str]) -> str:
    if not names:
        return "이 식당"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]}와 {names[1]}"
    return f"{names[0]} 등 {len(names)}곳"


def ordered_keywords(transcript: str, title: str, names: list[str], limit: int = 6) -> list[str]:
    candidates = list(dict.fromkeys([*names, *MENU_KEYWORDS]))
    haystack = f"{title} {transcript}"
    found: list[tuple[int, str]] = []
    for keyword in candidates:
        if not keyword:
            continue
        index = haystack.find(keyword)
        if index >= 0:
            found.append((index, keyword))
    return [keyword for _, keyword in sorted(found, key=lambda item: item[0])[:limit]]


def describe_terms(terms: list[str]) -> str:
    if not terms:
        return "메뉴와 식당 분위기"
    if len(terms) == 1:
        return terms[0]
    return ", ".join(terms[:-1]) + f", {terms[-1]}"


def theme_from_title(title: str, names: list[str]) -> str:
    title = clean_title(title)
    if len(names) > 1:
        return "여러 식당을 이어 가며 각 장소의 성격을 비교하는 코스형 소개"
    if "추리" in title or "메추리" in title:
        return "메뉴를 맞히는 추리 포맷 안에서 맛의 정체를 풀어 가는 소개"
    if "노포" in title or "업력" in title or "3대" in title:
        return "오래된 가게의 내공과 단골들이 찾는 이유를 따라가는 소개"
    if "가성비" in title or "무제한" in title or "만원" in title or "최저가" in title:
        return "가격 대비 구성과 실제 만족도를 확인하는 소개"
    if "도쿄" in title or "홍콩" in title or "스페인" in title or "파리" in title or "로마" in title:
        return "여행지에서 한 끼를 고를 때 참고할 만한 현지 식당 소개"
    if "제주" in title:
        return "제주 여행 동선 안에서 지역 재료와 메뉴를 확인하는 소개"
    return "한 끼를 고를 때 식당의 장점과 메뉴 흐름을 확인하는 소개"


def create_review(row: sqlite3.Row, generated_at: str) -> dict[str, Any]:
    names = parse_names(str(row["reviewed_restaurant_names"]))
    place = representative_place(names)
    source = str(row["source"])
    title = str(row["title"])
    transcript = str(row["transcript_text"])
    reviewer = SOURCE_REVIEWER.get(source, "리뷰어")
    terms = ordered_keywords(transcript, title, names)
    term_text = describe_terms(terms)
    theme = theme_from_title(title, names)

    if len(names) > 1:
        hook = f"{place}을 한 영상에서 훑으며, 각 식당의 메뉴와 분위기를 비교해 볼 수 있는 맛집 코스."
    else:
        hook = f"{place}을 중심으로 {theme}."

    story_intro = (
        f"{place}은 {source} 영상에서 {theme}로 다뤄진다. "
        f"자막 기준으로 영상은 {term_text} 같은 단서를 따라가며, 단순히 식당명을 소개하기보다 "
        f"왜 이 장소가 한 끼 후보가 되는지 보여주는 흐름에 가깝다. "
        f"{reviewer}는 메뉴를 앞에 두고 식감, 국물이나 소스의 인상, 구성의 장단점을 차례로 확인한다. "
        "그래서 이 항목은 지도에 찍힌 장소 정보뿐 아니라 실제 영상 속 식사 맥락까지 함께 볼 수 있는 후보로 정리된다."
    )

    tasting_flow = (
        f"시식 흐름은 먼저 {term_text}을 중심으로 메뉴의 첫인상을 잡는 데서 시작한다. "
        "이후 자막에서는 맛의 강도, 식감, 함께 먹는 재료나 곁들임에 대한 반응이 이어지고, "
        "마지막에는 이 식당이 어떤 상황에서 선택할 만한지 정리되는 식으로 마무리된다."
    )

    return {
        "video_id": str(row["video_id"]),
        "story_hook": hook,
        "story_intro": story_intro,
        "tasting_flow": tasting_flow,
        "reviewer": "codex-generated-from-transcript",
        "evidence": {
            "source": source,
            "title": title,
            "restaurant_names": names,
            "notes": (
                "Generated from stored transcript, reviewed restaurant names, and map-verified pipeline status. "
                "Uses conservative wording when the transcript does not expose detailed store history."
            ),
            "transcript_length": int(row["transcript_length"]),
            "keywords": terms,
        },
        "generated_at": generated_at,
    }


def missing_rows(sqlite_path: Path, limit: int | None = None) -> list[sqlite3.Row]:
    sql = """
        select
          v.video_id,
          v.source,
          v.title,
          v.reviewed_restaurant_names,
          t.transcript_text,
          length(t.transcript_text) as transcript_length
        from video_pipeline_status v
        join video_transcripts t on t.external_id = v.video_id
        left join video_story_reviews sr on sr.external_id = v.video_id
        where v.review_decision = 'restaurant_intro'
          and v.mapping_status = 'mapping_verified'
          and sr.external_id is null
        order by v.published_at desc, v.mention_candidate_id desc
    """
    params: tuple[Any, ...] = ()
    if limit is not None:
        sql += " limit ?"
        params = (limit,)
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        return list(connection.execute(sql, params).fetchall())


def merge_reviews(input_path: Path, reviews: list[dict[str, Any]]) -> None:
    if input_path.exists():
        payload = load_json(input_path)
    else:
        payload = {"reviews": []}
    items = payload.get("reviews")
    if not isinstance(items, list):
        raise ValueError(f"{input_path} must contain a reviews list")

    by_video_id = {
        str(item.get("video_id")): item
        for item in items
        if isinstance(item, dict) and item.get("video_id")
    }
    for review in reviews:
        by_video_id[str(review["video_id"])] = review

    ordered_existing_ids = [
        str(item.get("video_id"))
        for item in items
        if isinstance(item, dict) and item.get("video_id")
    ]
    new_ids = [str(review["video_id"]) for review in reviews if str(review["video_id"]) not in ordered_existing_ids]
    payload["reviews"] = [by_video_id[video_id] for video_id in ordered_existing_ids if video_id in by_video_id]
    payload["reviews"].extend(by_video_id[video_id] for video_id in new_ids)
    write_json(input_path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate conservative story reviews for map-verified videos with stored transcripts."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--input", type=Path, default=DEFAULT_STORY_REVIEWS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--apply", action="store_true", help="Write generated reviews into the story review JSON.")
    args = parser.parse_args()

    rows = missing_rows(args.sqlite, args.limit)
    generated_at = now_iso()
    reviews = [create_review(row, generated_at) for row in rows]

    if args.apply:
        merge_reviews(args.input, reviews)

    print(json.dumps({"generated": len(reviews), "applied": bool(args.apply)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
