#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

from pipeline_schema import ensure_pipeline_schema


DEFAULT_CONFIG = Path("data/sources/youtube_sources.json")
DEFAULT_OUTPUT_DIR = Path("data/raw/youtube")
DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
VIDEO_DETAIL_RETRIES = 5
VIDEO_DETAIL_RETRY_BACKOFF_SECONDS = 5
LATEST_PLAYLIST_LIMIT = 15

ATOM_NS = "{http://www.w3.org/2005/Atom}"
YT_NS = "{http://www.youtube.com/xml/schemas/2015}"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"


@dataclass(frozen=True)
class YoutubeSource:
    key: str
    name: str
    type: str
    trust_tier: str
    official_url: str
    enabled: bool
    channel_id: str | None
    feed_url: str | None
    playlist_url: str | None
    playlist_urls: list[str]
    title_include_any: list[str]
    title_exclude_any: list[str]
    title_cleanup_patterns: list[str]

    @property
    def resolved_feed_url(self) -> str:
        if self.feed_url:
            return self.feed_url
        if self.channel_id:
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        raise ValueError(f"{self.key} must define channel_id or feed_url")

    @property
    def resolved_channel_id(self) -> str:
        if self.channel_id:
            return self.channel_id
        match = re.search(r"channel_id=([^&]+)", self.resolved_feed_url)
        return match.group(1) if match else ""

    @property
    def resolved_full_channel_url(self) -> str:
        return self.resolved_full_channel_urls[0]

    @property
    def resolved_full_channel_urls(self) -> list[str]:
        urls: list[str] = []
        if self.playlist_url:
            urls.append(self.playlist_url)
        else:
            urls.append(f"https://www.youtube.com/channel/{self.resolved_channel_id}/videos")
        urls.extend(self.playlist_urls)
        return dedupe(urls)


@dataclass(frozen=True)
class YoutubeVideo:
    source_key: str
    source: str
    channel_id: str
    video_id: str
    title: str
    url: str
    thumbnail_url: str
    published_at: str
    updated_at: str
    description: str
    duration_seconds: int | None
    tags: list[str]
    chapters: list[dict[str, Any]]
    restaurant_name_candidates: list[str]
    collected_at: str


def load_sources(path: Path, only_keys: set[str] | None = None, include_disabled: bool = False) -> list[YoutubeSource]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = [parse_source(item) for item in payload["sources"]]

    if only_keys:
        sources = [source for source in sources if source.key in only_keys]

    if not include_disabled:
        sources = [source for source in sources if source.enabled]

    return sources


def parse_source(item: dict[str, Any]) -> YoutubeSource:
    return YoutubeSource(
        key=item["key"],
        name=item["name"],
        type=item.get("type", "youtube"),
        trust_tier=item.get("trust_tier", "B"),
        official_url=item.get("official_url", ""),
        enabled=bool(item.get("enabled", True)),
        channel_id=item.get("channel_id"),
        feed_url=item.get("feed_url"),
        playlist_url=item.get("playlist_url"),
        playlist_urls=list(item.get("playlist_urls", [])),
        title_include_any=list(item.get("title_include_any", [])),
        title_exclude_any=list(item.get("title_exclude_any", [])),
        title_cleanup_patterns=list(item.get("title_cleanup_patterns", [])),
    )


def collect_source(
    source: YoutubeSource,
    collected_at: str,
    *,
    workers: int = 1,
    existing_candidates: dict[str, YoutubeVideo] | None = None,
) -> list[YoutubeVideo]:
    try:
        candidates = parse_feed(fetch_feed(source.resolved_feed_url), source, collected_at)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        print(
            f"warning: RSS feed unavailable for {source.key}; using recent playlist fallback",
            file=sys.stderr,
        )
        candidates = collect_recent_playlist_candidates(source, collected_at)
    candidates, skip_video_ids = apply_existing_candidates(
        candidates,
        existing_candidates or {},
        collected_at,
    )
    enriched_candidates = enrich_candidates(
        candidates,
        source,
        workers=workers,
        skip_video_ids=skip_video_ids,
    )
    return filter_collectable_full_channel_candidates(enriched_candidates, source)


def collect_recent_playlist_candidates(
    source: YoutubeSource,
    collected_at: str,
) -> list[YoutubeVideo]:
    candidates: list[YoutubeVideo] = []
    seen_video_ids: set[str] = set()
    for full_channel_url in source.resolved_full_channel_urls:
        command = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--dump-json",
            "--flat-playlist",
            "--playlist-end",
            str(LATEST_PLAYLIST_LIMIT),
            "--extractor-args",
            "youtube:lang=ko",
            full_channel_url,
        ]
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
        for line in completed.stdout.splitlines():
            if not line.startswith("{"):
                continue
            item = json.loads(line)
            title = str(item.get("title") or "").strip()
            video_id = str(item.get("id") or "").strip()
            if (
                not video_id
                or video_id in seen_video_ids
                or not title
                or not should_include_title(title, source)
            ):
                continue
            seen_video_ids.add(video_id)
            candidates.append(
                make_candidate_from_yt_dlp_item(
                    item=item,
                    source=source,
                    collected_at=collected_at,
                )
            )
    return candidates


def collect_source_full_channel(
    source: YoutubeSource,
    collected_at: str,
    *,
    workers: int = 1,
    existing_candidates: dict[str, YoutubeVideo] | None = None,
) -> list[YoutubeVideo]:
    try:
        rss_rows = parse_feed(fetch_feed(source.resolved_feed_url), source, collected_at)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        print(f"warning: RSS feed unavailable for {source.key}; continuing full-channel collection", file=sys.stderr)
        rss_rows = []
    rss_candidates = {candidate.video_id: candidate for candidate in rss_rows}
    candidates: list[YoutubeVideo] = []
    existing_candidates = existing_candidates or {}
    skip_video_ids: set[str] = set()
    seen_video_ids: set[str] = set()

    for full_channel_url in source.resolved_full_channel_urls:
        command = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--dump-json",
            "--flat-playlist",
            "--extractor-args",
            "youtube:lang=ko",
            full_channel_url,
        ]
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)

        for line in completed.stdout.splitlines():
            if not line.startswith("{"):
                continue
            item = json.loads(line)
            title = str(item.get("title") or "").strip()
            if not title or not should_include_title(title, source):
                continue

            video_id = str(item.get("id") or "").strip()
            if not video_id or video_id in seen_video_ids:
                continue
            seen_video_ids.add(video_id)

            existing_candidate = existing_candidates.get(video_id)
            fallback_candidate = existing_candidate or rss_candidates.get(video_id)
            candidates.append(
                make_candidate_from_yt_dlp_item(
                    item=item,
                    source=source,
                    collected_at=collected_at,
                    fallback=fallback_candidate,
                )
            )
            if existing_candidate and has_enriched_video_details(existing_candidate):
                skip_video_ids.add(video_id)

    for rss_candidate in rss_candidates.values():
        if rss_candidate.video_id in seen_video_ids:
            continue

        seen_video_ids.add(rss_candidate.video_id)
        existing_candidate = existing_candidates.get(rss_candidate.video_id)
        if existing_candidate is not None:
            candidates.append(
                merge_candidate_with_existing(rss_candidate, existing_candidate, collected_at)
            )
            if has_enriched_video_details(existing_candidate):
                skip_video_ids.add(rss_candidate.video_id)
            continue

        candidates.append(rss_candidate)

    return enrich_candidates(candidates, source, workers=workers, skip_video_ids=skip_video_ids)


def make_candidate_from_yt_dlp_item(
    item: dict[str, Any],
    source: YoutubeSource,
    collected_at: str,
    fallback: YoutubeVideo | None = None,
) -> YoutubeVideo:
    video_id = str(item.get("id") or "").strip()
    title = str(item.get("title") or (fallback.title if fallback else "")).strip()
    url = str(item.get("webpage_url") or item.get("url") or f"https://www.youtube.com/watch?v={video_id}")
    description = str(item.get("description") or (fallback.description if fallback else ""))

    description_candidates = extract_description_candidates(description)
    restaurant_name_candidates = (
        description_candidates
        if description_candidates
        else extract_title_candidates(title, source)
    )

    return YoutubeVideo(
        source_key=source.key,
        source=source.name,
        channel_id=str(item.get("channel_id") or source.resolved_channel_id),
        video_id=video_id,
        title=title,
        url=url,
        thumbnail_url=(
            extract_yt_dlp_thumbnail(item, video_id)
            or (fallback.thumbnail_url if fallback else "")
        ),
        published_at=(
            format_yt_dlp_timestamp(item)
            or (fallback.published_at if fallback else "")
        ),
        updated_at=fallback.updated_at if fallback else "",
        description=description,
        duration_seconds=extract_duration_seconds(item, fallback),
        tags=extract_string_list(item.get("tags"), fallback.tags if fallback else []),
        chapters=extract_chapters(item.get("chapters"), fallback.chapters if fallback else []),
        restaurant_name_candidates=restaurant_name_candidates,
        collected_at=collected_at,
    )


def apply_existing_candidates(
    candidates: list[YoutubeVideo],
    existing_candidates: dict[str, YoutubeVideo],
    collected_at: str,
) -> tuple[list[YoutubeVideo], set[str]]:
    if not existing_candidates:
        return candidates, set()

    merged_candidates: list[YoutubeVideo] = []
    skip_video_ids: set[str] = set()
    for candidate in candidates:
        existing_candidate = existing_candidates.get(candidate.video_id)
        if existing_candidate is None:
            merged_candidates.append(candidate)
            continue

        merged_candidates.append(
            merge_candidate_with_existing(candidate, existing_candidate, collected_at)
        )
        if has_enriched_video_details(existing_candidate):
            skip_video_ids.add(candidate.video_id)

    return merged_candidates, skip_video_ids


def has_enriched_video_details(candidate: YoutubeVideo) -> bool:
    return bool(candidate.published_at) and candidate.duration_seconds is not None


def has_collectable_video_metadata(candidate: YoutubeVideo) -> bool:
    return bool(candidate.published_at)


def filter_collectable_full_channel_candidates(
    candidates: list[YoutubeVideo],
    source: YoutubeSource,
) -> list[YoutubeVideo]:
    filtered: list[YoutubeVideo] = []
    dropped: list[YoutubeVideo] = []
    for candidate in candidates:
        if (
            candidate.title
            and has_collectable_video_metadata(candidate)
            and should_include_title(candidate.title, source)
        ):
            filtered.append(candidate)
        else:
            dropped.append(candidate)

    for candidate in dropped:
        print(
            f"warning: dropped incomplete or excluded {source.key}/{candidate.video_id}",
            file=sys.stderr,
        )
    return filtered


def merge_candidate_with_existing(
    candidate: YoutubeVideo,
    existing_candidate: YoutubeVideo,
    collected_at: str,
) -> YoutubeVideo:
    return YoutubeVideo(
        source_key=candidate.source_key,
        source=candidate.source,
        channel_id=candidate.channel_id or existing_candidate.channel_id,
        video_id=candidate.video_id,
        title=candidate.title or existing_candidate.title,
        url=candidate.url or existing_candidate.url,
        thumbnail_url=candidate.thumbnail_url or existing_candidate.thumbnail_url,
        published_at=candidate.published_at or existing_candidate.published_at,
        updated_at=candidate.updated_at or existing_candidate.updated_at,
        description=candidate.description or existing_candidate.description,
        duration_seconds=(
            candidate.duration_seconds
            if candidate.duration_seconds is not None
            else existing_candidate.duration_seconds
        ),
        tags=candidate.tags or existing_candidate.tags,
        chapters=candidate.chapters or existing_candidate.chapters,
        restaurant_name_candidates=(
            existing_candidate.restaurant_name_candidates
            or candidate.restaurant_name_candidates
        ),
        collected_at=collected_at,
    )


def enrich_candidates(
    candidates: list[YoutubeVideo],
    source: YoutubeSource,
    *,
    workers: int = 1,
    skip_video_ids: set[str] | None = None,
) -> list[YoutubeVideo]:
    skip_video_ids = skip_video_ids or set()
    workers = max(1, workers)
    if workers == 1:
        return enrich_candidates_serial(candidates, source, skip_video_ids)

    return enrich_candidates_parallel(candidates, source, workers, skip_video_ids)


def enrich_candidates_serial(
    candidates: list[YoutubeVideo],
    source: YoutubeSource,
    skip_video_ids: set[str],
) -> list[YoutubeVideo]:
    enriched: list[YoutubeVideo] = []
    for index, candidate in enumerate(candidates, start=1):
        if candidate.video_id in skip_video_ids:
            enriched.append(candidate)
            print(f"{source.key}: reused {index}/{len(candidates)} {candidate.video_id}", flush=True)
            continue

        try:
            item = fetch_video_details(candidate.url)
        except Exception as error:
            print(
                f"warning: failed to enrich {source.key}/{candidate.video_id}: {error}",
                file=sys.stderr,
            )
            enriched.append(candidate)
            continue

        enriched.append(
            make_candidate_from_yt_dlp_item(
                item=item,
                source=source,
                collected_at=candidate.collected_at,
                fallback=candidate,
            )
        )
        print(f"{source.key}: enriched {index}/{len(candidates)} {candidate.video_id}", flush=True)

    return enriched


def enrich_candidates_parallel(
    candidates: list[YoutubeVideo],
    source: YoutubeSource,
    workers: int,
    skip_video_ids: set[str],
) -> list[YoutubeVideo]:
    enriched: list[YoutubeVideo | None] = [None] * len(candidates)
    futures = {}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for index, candidate in enumerate(candidates, start=1):
            if candidate.video_id in skip_video_ids:
                enriched[index - 1] = candidate
                print(f"{source.key}: reused {index}/{len(candidates)} {candidate.video_id}", flush=True)
                continue

            future = executor.submit(fetch_video_details, candidate.url)
            futures[future] = (index, candidate)

        for future in as_completed(futures):
            index, candidate = futures[future]
            try:
                item = future.result()
            except Exception as error:
                print(
                    f"warning: failed to enrich {source.key}/{candidate.video_id}: {error}",
                    file=sys.stderr,
                )
                enriched[index - 1] = candidate
                continue

            enriched[index - 1] = make_candidate_from_yt_dlp_item(
                item=item,
                source=source,
                collected_at=candidate.collected_at,
                fallback=candidate,
            )
            print(f"{source.key}: enriched {index}/{len(candidates)} {candidate.video_id}", flush=True)

    return [
        candidate if enriched_candidate is None else enriched_candidate
        for candidate, enriched_candidate in zip(candidates, enriched)
    ]


def fetch_video_details(url: str) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--dump-json",
        "--skip-download",
        "--no-playlist",
        "--no-warnings",
        "--extractor-args",
        "youtube:lang=ko",
        url,
    ]
    last_error: Exception | None = None
    for attempt in range(VIDEO_DETAIL_RETRIES + 1):
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=45)
        except Exception as error:
            last_error = error
            if attempt < VIDEO_DETAIL_RETRIES:
                time.sleep(VIDEO_DETAIL_RETRY_BACKOFF_SECONDS)
            continue

        for line in completed.stdout.splitlines():
            if line.startswith("{"):
                return json.loads(line)
        last_error = RuntimeError("yt-dlp returned no JSON object")
        if attempt < VIDEO_DETAIL_RETRIES:
            time.sleep(VIDEO_DETAIL_RETRY_BACKOFF_SECONDS)

    if last_error:
        raise last_error
    raise RuntimeError("yt-dlp returned no JSON object")


def fetch_feed(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "tastyroad-rss-collector/0.2 (+https://youtube.com)",
            "Accept": "application/atom+xml, application/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def parse_feed(xml_bytes: bytes, source: YoutubeSource, collected_at: str) -> list[YoutubeVideo]:
    root = ElementTree.fromstring(xml_bytes)
    candidates: list[YoutubeVideo] = []

    for entry in root.findall(f"{ATOM_NS}entry"):
        title = text_or_empty(entry.find(f"{ATOM_NS}title"))
        if not should_include_title(title, source):
            continue

        video_id = text_or_empty(entry.find(f"{YT_NS}videoId"))
        link = entry.find(f"{ATOM_NS}link")
        url = link.attrib.get("href", "") if link is not None else ""
        thumbnail_url = extract_thumbnail_url(entry, video_id)

        candidates.append(
            YoutubeVideo(
                source_key=source.key,
                source=source.name,
                channel_id=source.resolved_channel_id,
                video_id=video_id,
                title=title,
                url=url,
                thumbnail_url=thumbnail_url,
                published_at=text_or_empty(entry.find(f"{ATOM_NS}published")),
                updated_at=text_or_empty(entry.find(f"{ATOM_NS}updated")),
                description="",
                duration_seconds=None,
                tags=[],
                chapters=[],
                restaurant_name_candidates=extract_title_candidates(title, source),
                collected_at=collected_at,
            )
        )

    return candidates


def extract_thumbnail_url(entry: ElementTree.Element, video_id: str) -> str:
    media_group = entry.find(f"{MEDIA_NS}group")
    thumbnail = media_group.find(f"{MEDIA_NS}thumbnail") if media_group is not None else None
    thumbnail_url = thumbnail.attrib.get("url", "") if thumbnail is not None else ""
    if thumbnail_url:
        return thumbnail_url
    if video_id:
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    return ""


def extract_yt_dlp_thumbnail(item: dict[str, Any], video_id: str) -> str:
    thumbnails = item.get("thumbnails")
    if isinstance(thumbnails, list):
        for thumbnail in reversed(thumbnails):
            if isinstance(thumbnail, dict) and thumbnail.get("url"):
                return str(thumbnail["url"])
    if item.get("thumbnail"):
        return str(item["thumbnail"])
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def format_yt_dlp_timestamp(item: dict[str, Any]) -> str:
    timestamp = item.get("timestamp") or item.get("release_timestamp")
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()

    upload_date = str(item.get("upload_date") or item.get("release_date") or "")
    if re.fullmatch(r"\d{8}", upload_date):
        parsed = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)
        return parsed.isoformat()

    return ""


def extract_duration_seconds(item: dict[str, Any], fallback: YoutubeVideo | None = None) -> int | None:
    duration = item.get("duration")
    if isinstance(duration, (int, float)):
        return int(duration)
    return fallback.duration_seconds if fallback else None


def extract_string_list(value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    return [str(item) for item in value if item is not None]


def extract_chapters(value: Any, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return fallback

    chapters: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        chapter: dict[str, Any] = {}
        for key in ("title", "start_time", "end_time"):
            if key in item:
                chapter[key] = item[key]
        if chapter:
            chapters.append(chapter)
    return chapters


def text_or_empty(element: ElementTree.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def should_include_title(title: str, source: YoutubeSource) -> bool:
    title_folded = title.casefold()
    if source.title_include_any and not any(keyword.casefold() in title_folded for keyword in source.title_include_any):
        return False
    if any(keyword.casefold() in title_folded for keyword in source.title_exclude_any):
        return False
    return True


def extract_title_candidates(title: str, source: YoutubeSource) -> list[str]:
    normalized = re.sub(r"\s+", " ", title).strip()
    cleaned = normalized
    for pattern in source.title_cleanup_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

    parts = [
        part.strip(" -_/.,")
        for part in re.split(r"\s*[|lㅣ]\s*|\s{2,}", cleaned)
        if part.strip(" -_/.,")
    ]

    return dedupe(parts or [cleaned] if cleaned else [])


def extract_description_candidates(description: str) -> list[str]:
    lines = [line.strip() for line in description.splitlines()]
    candidates: list[str] = []

    for index, line in enumerate(lines):
        if not line:
            continue

        if line in {"[식당정보]", "식당정보", "*식당정보"}:
            for next_line in lines[index + 1 : index + 5]:
                value = clean_candidate_restaurant_name(next_line)
                if is_candidate_restaurant_name(value):
                    candidates.append(value)
                    break
            continue

        bracket_match = re.fullmatch(r"\[([^\]]{2,40})\]", line)
        if bracket_match:
            value = clean_candidate_restaurant_name(bracket_match.group(1))
            if is_candidate_restaurant_name(value):
                candidates.append(value)
            continue

        numbered_match = re.match(r"^\d+\.\s*(.{2,40})$", line)
        if numbered_match:
            value = clean_candidate_restaurant_name(numbered_match.group(1))
            if is_candidate_restaurant_name(value):
                candidates.append(value)
            continue

        label_match = re.match(r"^(?:상호|식당명)\s*[:：]\s*(.{2,40})$", line)
        if label_match:
            value = clean_candidate_restaurant_name(label_match.group(1))
            if is_candidate_restaurant_name(value):
                candidates.append(value)

    return dedupe(candidates)


def is_candidate_restaurant_name(value: str) -> bool:
    value = clean_candidate_restaurant_name(value)
    if not value:
        return False
    if len(value) > 40:
        return False
    if value.startswith(("http://", "https://", "#")):
        return False
    if "식당X" in value or "식당x" in value:
        return False
    if re.search(r"(주소|위치|전화|영업|예약|가격|메뉴|문의|메일|BGM|정보)$", value, re.IGNORECASE):
        return False
    if re.search(r"(서울|경기|인천|부산|대구|대전|광주|울산|세종|강원|충북|충남|전북|전남|경북|경남|제주).*\d", value):
        return False
    ignored = {
        "식당정보",
        "BGM 정보",
        "김사원 유튜브 전자책",
        "김사원세끼의 노포 투어",
    }
    return value not in ignored


def clean_candidate_restaurant_name(value: str) -> str:
    return re.sub(r"^\d+\.\s*", "", value).strip(" -_/.,")


def dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def load_existing_candidates(
    sqlite_path: Path,
    output_dir: Path,
    source: YoutubeSource,
) -> dict[str, YoutubeVideo]:
    existing = load_existing_candidates_from_json(output_dir / f"{source.key}.json", source)
    existing.update(load_existing_candidates_from_sqlite(sqlite_path, source))
    return existing


def load_existing_candidates_from_json(
    path: Path,
    source: YoutubeSource,
) -> dict[str, YoutubeVideo]:
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"warning: failed to read existing candidates from {path}: {error}", file=sys.stderr)
        return {}

    candidates: dict[str, YoutubeVideo] = {}
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            continue
        candidate = youtube_video_from_mapping(item, source)
        if candidate is not None:
            candidates[candidate.video_id] = candidate
    return candidates


def load_existing_candidates_from_sqlite(
    path: Path,
    source: YoutubeSource,
) -> dict[str, YoutubeVideo]:
    if not path.exists():
        return {}

    try:
        with sqlite3.connect(path) as connection:
            ensure_pipeline_schema(connection)
            rows = connection.execute(
                """
                select
                  c.video_id,
                  c.title,
                  c.url,
                  c.thumbnail_url,
                  c.published_at,
                  c.updated_at,
                  c.description,
                  c.duration_seconds,
                  c.tags,
                  c.chapters,
                  c.raw_restaurant_name_candidates,
                  c.collected_at
                from youtube_videos c
                join sources s on s.id = c.source_id
                where s.name = ?
                """,
                (source.name,),
            ).fetchall()
    except sqlite3.Error as error:
        print(f"warning: failed to read existing candidates from {path}: {error}", file=sys.stderr)
        return {}

    candidates: dict[str, YoutubeVideo] = {}
    for row in rows:
        item = {
            "source_key": source.key,
            "source": source.name,
            "channel_id": source.resolved_channel_id,
            "video_id": row[0],
            "title": row[1],
            "url": row[2],
            "thumbnail_url": row[3],
            "published_at": row[4],
            "updated_at": row[5],
            "description": row[6],
            "duration_seconds": row[7],
            "tags": parse_json_array(row[8]),
            "chapters": parse_json_array(row[9]),
            "restaurant_name_candidates": parse_json_array(row[10]),
            "collected_at": row[11],
        }
        candidate = youtube_video_from_mapping(item, source)
        if candidate is not None:
            candidates[candidate.video_id] = candidate
    return candidates


def youtube_video_from_mapping(
    item: dict[str, Any],
    source: YoutubeSource,
) -> YoutubeVideo | None:
    video_id = str(item.get("video_id") or item.get("external_id") or "").strip()
    if not video_id:
        return None

    tags = extract_string_list(item.get("tags"), [])
    chapters = extract_chapters(item.get("chapters"), [])
    restaurant_name_candidates = extract_string_list(
        item.get("restaurant_name_candidates")
        or item.get("raw_restaurant_name_candidates"),
        [],
    )

    duration_seconds: int | None = None
    duration_value = item.get("duration_seconds")
    if isinstance(duration_value, (int, float)):
        duration_seconds = int(duration_value)

    return YoutubeVideo(
        source_key=str(item.get("source_key") or source.key),
        source=str(item.get("source") or source.name),
        channel_id=str(item.get("channel_id") or source.resolved_channel_id),
        video_id=video_id,
        title=str(item.get("title") or ""),
        url=str(item.get("url") or f"https://www.youtube.com/watch?v={video_id}"),
        thumbnail_url=str(item.get("thumbnail_url") or ""),
        published_at=str(item.get("published_at") or ""),
        updated_at=str(item.get("updated_at") or ""),
        description=str(item.get("description") or ""),
        duration_seconds=duration_seconds,
        tags=tags,
        chapters=chapters,
        restaurant_name_candidates=restaurant_name_candidates,
        collected_at=str(item.get("collected_at") or ""),
    )


def parse_json_array(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, str) or not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def write_json(output_dir: Path, source: YoutubeSource, candidates: list[YoutubeVideo]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{source.key}.json"
    payload = {
        "source_key": source.key,
        "source": source.name,
        "feed_url": source.resolved_feed_url,
        "full_channel_url": source.resolved_full_channel_url,
        "full_channel_urls": source.resolved_full_channel_urls,
        "count": len(candidates),
        "items": [asdict(candidate) for candidate in candidates],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def merge_snapshot_candidates(
    existing_candidates: dict[str, YoutubeVideo],
    candidates: list[YoutubeVideo],
) -> list[YoutubeVideo]:
    merged = dict(existing_candidates)
    merged.update({candidate.video_id: candidate for candidate in candidates})
    return sorted(
        merged.values(),
        key=lambda candidate: (candidate.published_at, candidate.video_id),
        reverse=True,
    )


def write_sqlite(
    path: Path,
    source: YoutubeSource,
    candidates: list[YoutubeVideo],
    *,
    prune_missing: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute("pragma foreign_keys = on")
        ensure_collection_schema(connection)
        source_id = upsert_source(connection, source)
        candidate_video_ids = {candidate.video_id for candidate in candidates}
        for candidate in candidates:
            connection.execute(
                """
                insert into youtube_videos (
                  source_id,
                  video_id,
                  title,
                  url,
                  thumbnail_url,
                  published_at,
                  updated_at,
                  description,
                  duration_seconds,
                  tags,
                  chapters,
                  raw_restaurant_name_candidates,
                  collected_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(source_id, video_id) do update set
                  title = excluded.title,
                  url = excluded.url,
                  thumbnail_url = excluded.thumbnail_url,
                  published_at = case
                    when excluded.published_at != '' then excluded.published_at
                    else youtube_videos.published_at
                  end,
                  updated_at = case
                    when excluded.updated_at != '' then excluded.updated_at
                    else youtube_videos.updated_at
                  end,
                  description = excluded.description,
                  duration_seconds = excluded.duration_seconds,
                  tags = excluded.tags,
                  chapters = excluded.chapters,
                  raw_restaurant_name_candidates = excluded.raw_restaurant_name_candidates,
                  collected_at = excluded.collected_at
                """,
                (
                    source_id,
                    candidate.video_id,
                    candidate.title,
                    candidate.url,
                    candidate.thumbnail_url,
                    candidate.published_at,
                    candidate.updated_at,
                    candidate.description,
                    candidate.duration_seconds,
                    json.dumps(candidate.tags, ensure_ascii=False),
                    json.dumps(candidate.chapters, ensure_ascii=False),
                    json.dumps(candidate.restaurant_name_candidates, ensure_ascii=False),
                    candidate.collected_at,
                ),
            )
        if prune_missing:
            if candidate_video_ids:
                placeholders = ",".join("?" for _ in candidate_video_ids)
                connection.execute(
                    f"""
                    delete from youtube_videos
                    where source_id = ?
                      and video_id not in ({placeholders})
                    """,
                    (source_id, *sorted(candidate_video_ids)),
                )
            else:
                connection.execute(
                    "delete from youtube_videos where source_id = ?",
                    (source_id,),
                )


def ensure_collection_schema(connection: sqlite3.Connection) -> None:
    ensure_pipeline_schema(connection)


def upsert_source(connection: sqlite3.Connection, source: YoutubeSource) -> int:
    now = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """
        insert into sources (name, type, trust_tier, official_url, created_at)
        values (?, ?, ?, ?, ?)
        on conflict(name) do update set
          type = excluded.type,
          trust_tier = excluded.trust_tier,
          official_url = excluded.official_url
        """,
        (source.name, source.type, source.trust_tier, source.official_url, now),
    )
    row = connection.execute("select id from sources where name = ?", (source.name,)).fetchone()
    if row is None:
        raise RuntimeError(f"Failed to load source id for {source.name}")
    return int(row[0])


def collect_sources(
    config_path: Path,
    output_dir: Path,
    sqlite_path: Path,
    only_keys: set[str] | None = None,
    include_disabled: bool = False,
    full_channel: bool = False,
    full_channel_keys: set[str] | None = None,
    workers: int = 1,
    reuse_existing: bool = False,
) -> dict[str, int]:
    collected_at = datetime.now(timezone.utc).isoformat()
    counts: dict[str, int] = {}
    workers = max(1, workers)

    for source in load_sources(config_path, only_keys=only_keys, include_disabled=include_disabled):
        use_full_channel = full_channel or (full_channel_keys is not None and source.key in full_channel_keys)
        existing_candidates = (
            load_existing_candidates(sqlite_path, output_dir, source)
            if reuse_existing
            else {}
        )
        snapshot_existing_candidates = (
            load_existing_candidates_from_json(output_dir / f"{source.key}.json", source)
            if reuse_existing
            else {}
        )
        candidates = (
            collect_source_full_channel(
                source,
                collected_at,
                workers=workers,
                existing_candidates=existing_candidates,
            )
            if use_full_channel
            else collect_source(
                source,
                collected_at,
                workers=workers,
                existing_candidates=existing_candidates,
            )
        )
        snapshot_candidates = (
            candidates
            if use_full_channel
            else merge_snapshot_candidates(snapshot_existing_candidates, candidates)
        )
        output_path = write_json(output_dir, source, snapshot_candidates)
        write_sqlite(sqlite_path, source, candidates, prune_missing=use_full_channel)
        counts[source.key] = len(snapshot_candidates)
        print(
            f"{source.key}: collected {len(candidates)} recent candidates, "
            f"wrote {len(snapshot_candidates)} total -> {output_path}"
        )

    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect YouTube video rows for configured sources.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--source", action="append", help="Source key to collect. Can be passed multiple times.")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--full-channel", action="store_true", help="Collect the full YouTube channel video list with yt-dlp instead of the RSS window.")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel per-video detail fetches.")
    parser.add_argument(
        "--reuse-existing",
        "--missing-only",
        dest="reuse_existing",
        action="store_true",
        help="Reuse existing DB/raw candidate details and only enrich videos that are not already collected.",
    )
    args = parser.parse_args()

    counts = collect_sources(
        config_path=args.config,
        output_dir=args.output_dir,
        sqlite_path=args.sqlite,
        only_keys=set(args.source) if args.source else None,
        include_disabled=args.include_disabled,
        full_channel=args.full_channel,
        workers=args.workers,
        reuse_existing=args.reuse_existing,
    )

    print(f"Updated {args.sqlite}")
    print(f"Total candidates collected: {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
