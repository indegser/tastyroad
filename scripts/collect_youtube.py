#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

from pipeline_schema import ensure_pipeline_schema


DEFAULT_CONFIG = Path("data/sources/youtube_sources.json")
DEFAULT_OUTPUT_DIR = Path("data/raw/youtube")
DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
VIDEO_DETAIL_RETRIES = 2

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


@dataclass(frozen=True)
class MentionCandidate:
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
        title_include_any=list(item.get("title_include_any", [])),
        title_exclude_any=list(item.get("title_exclude_any", [])),
        title_cleanup_patterns=list(item.get("title_cleanup_patterns", [])),
    )


def collect_source(source: YoutubeSource, collected_at: str) -> list[MentionCandidate]:
    xml_bytes = fetch_feed(source.resolved_feed_url)
    return enrich_candidates(parse_feed(xml_bytes, source, collected_at), source)


def collect_source_full_channel(source: YoutubeSource, collected_at: str) -> list[MentionCandidate]:
    rss_candidates = {
        candidate.video_id: candidate
        for candidate in parse_feed(fetch_feed(source.resolved_feed_url), source, collected_at)
    }
    command = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        "--extractor-args",
        "youtube:lang=ko",
        f"https://www.youtube.com/channel/{source.resolved_channel_id}/videos",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    candidates: list[MentionCandidate] = []

    for line in completed.stdout.splitlines():
        if not line.startswith("{"):
            continue
        item = json.loads(line)
        title = str(item.get("title") or "").strip()
        if not should_include_title(title, source):
            continue

        video_id = str(item.get("id") or "").strip()
        if not video_id:
            continue

        rss_candidate = rss_candidates.get(video_id)
        candidates.append(
            make_candidate_from_yt_dlp_item(
                item=item,
                source=source,
                collected_at=collected_at,
                fallback=rss_candidate,
            )
        )

    return enrich_candidates(candidates, source)


def make_candidate_from_yt_dlp_item(
    item: dict[str, Any],
    source: YoutubeSource,
    collected_at: str,
    fallback: MentionCandidate | None = None,
) -> MentionCandidate:
    video_id = str(item.get("id") or "").strip()
    title = str(item.get("title") or (fallback.title if fallback else "")).strip()
    url = str(item.get("webpage_url") or item.get("url") or f"https://www.youtube.com/watch?v={video_id}")
    description = str(item.get("description") or (fallback.description if fallback else ""))

    return MentionCandidate(
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
        restaurant_name_candidates=extract_title_candidates(title, source),
        collected_at=collected_at,
    )


def enrich_candidates(candidates: list[MentionCandidate], source: YoutubeSource) -> list[MentionCandidate]:
    enriched: list[MentionCandidate] = []
    for index, candidate in enumerate(candidates, start=1):
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


def fetch_video_details(url: str) -> dict[str, Any]:
    command = [
        "yt-dlp",
        "--dump-json",
        "--skip-download",
        "--no-playlist",
        "--no-warnings",
        "--extractor-args",
        "youtube:lang=ko",
        url,
    ]
    last_error: Exception | None = None
    for _attempt in range(VIDEO_DETAIL_RETRIES + 1):
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=45)
        except Exception as error:
            last_error = error
            continue

        for line in completed.stdout.splitlines():
            if line.startswith("{"):
                return json.loads(line)
        last_error = RuntimeError("yt-dlp returned no JSON object")

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


def parse_feed(xml_bytes: bytes, source: YoutubeSource, collected_at: str) -> list[MentionCandidate]:
    root = ElementTree.fromstring(xml_bytes)
    candidates: list[MentionCandidate] = []

    for entry in root.findall(f"{ATOM_NS}entry"):
        title = text_or_empty(entry.find(f"{ATOM_NS}title"))
        if not should_include_title(title, source):
            continue

        video_id = text_or_empty(entry.find(f"{YT_NS}videoId"))
        link = entry.find(f"{ATOM_NS}link")
        url = link.attrib.get("href", "") if link is not None else ""
        thumbnail_url = extract_thumbnail_url(entry, video_id)

        candidates.append(
            MentionCandidate(
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


def extract_duration_seconds(item: dict[str, Any], fallback: MentionCandidate | None = None) -> int | None:
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
    if source.title_include_any and not any(keyword in title for keyword in source.title_include_any):
        return False
    if any(keyword in title for keyword in source.title_exclude_any):
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


def dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def write_json(output_dir: Path, source: YoutubeSource, candidates: list[MentionCandidate]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{source.key}.json"
    payload = {
        "source_key": source.key,
        "source": source.name,
        "feed_url": source.resolved_feed_url,
        "count": len(candidates),
        "items": [asdict(candidate) for candidate in candidates],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_sqlite(path: Path, source: YoutubeSource, candidates: list[MentionCandidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute("pragma foreign_keys = on")
        ensure_collection_schema(connection)
        source_id = upsert_source(connection, source)
        for candidate in candidates:
            connection.execute(
                """
                insert into mention_candidates (
                  source_id,
                  external_id,
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
                on conflict(source_id, external_id) do update set
                  title = excluded.title,
                  url = excluded.url,
                  thumbnail_url = excluded.thumbnail_url,
                  published_at = case
                    when excluded.published_at != '' then excluded.published_at
                    else mention_candidates.published_at
                  end,
                  updated_at = case
                    when excluded.updated_at != '' then excluded.updated_at
                    else mention_candidates.updated_at
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


def ensure_collection_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        create table if not exists sources (
          id integer primary key autoincrement,
          name text not null unique,
          type text not null,
          trust_tier text not null,
          official_url text not null,
          created_at text not null
        );

        create table if not exists mention_candidates (
          id integer primary key autoincrement,
          source_id integer not null references sources(id),
          external_id text not null,
          title text not null,
          url text not null,
          thumbnail_url text not null default '',
          published_at text not null,
          updated_at text not null,
          description text not null default '',
          duration_seconds integer,
          tags text not null default '[]',
          chapters text not null default '[]',
          raw_restaurant_name_candidates text not null,
          collected_at text not null,
          status text not null default 'pending',
          unique(source_id, external_id)
        );
        """
    )
    columns = {
        row[1]
        for row in connection.execute("pragma table_info(mention_candidates)").fetchall()
    }
    if "thumbnail_url" not in columns:
        connection.execute(
            "alter table mention_candidates add column thumbnail_url text not null default ''"
        )
    if "description" not in columns:
        connection.execute(
            "alter table mention_candidates add column description text not null default ''"
        )
    if "duration_seconds" not in columns:
        connection.execute(
            "alter table mention_candidates add column duration_seconds integer"
        )
    if "tags" not in columns:
        connection.execute(
            "alter table mention_candidates add column tags text not null default '[]'"
        )
    if "chapters" not in columns:
        connection.execute(
            "alter table mention_candidates add column chapters text not null default '[]'"
        )
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
) -> dict[str, int]:
    collected_at = datetime.now(timezone.utc).isoformat()
    counts: dict[str, int] = {}

    for source in load_sources(config_path, only_keys=only_keys, include_disabled=include_disabled):
        use_full_channel = full_channel or (full_channel_keys is not None and source.key in full_channel_keys)
        candidates = (
            collect_source_full_channel(source, collected_at)
            if use_full_channel
            else collect_source(source, collected_at)
        )
        output_path = write_json(output_dir, source, candidates)
        write_sqlite(sqlite_path, source, candidates)
        counts[source.key] = len(candidates)
        print(f"{source.key}: collected {len(candidates)} candidates -> {output_path}")

    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect YouTube RSS mention candidates for configured sources.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--source", action="append", help="Source key to collect. Can be passed multiple times.")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--full-channel", action="store_true", help="Collect the full YouTube channel video list with yt-dlp instead of the RSS window.")
    args = parser.parse_args()

    counts = collect_sources(
        config_path=args.config,
        output_dir=args.output_dir,
        sqlite_path=args.sqlite,
        only_keys=set(args.source) if args.source else None,
        include_disabled=args.include_disabled,
        full_channel=args.full_channel,
    )

    print(f"Updated {args.sqlite}")
    print(f"Total candidates collected: {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
