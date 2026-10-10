#!/usr/bin/env python3
"""Fill details for newly collected videos from YouTube watch-page metadata."""

from __future__ import annotations

import argparse
import json
import sqlite3
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from collect_youtube import extract_description_candidates, extract_title_candidates, load_sources


def fetch_metadata(video_id: str) -> dict[str, object]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8")
    marker = "var ytInitialPlayerResponse = "
    start = html.find(marker)
    if start < 0:
        raise ValueError("watch page has no player response")
    player, _ = json.JSONDecoder().raw_decode(html[start + len(marker) :])
    details = player.get("videoDetails") or {}
    microformat = (player.get("microformat") or {}).get("playerMicroformatRenderer") or {}
    if details.get("videoId") != video_id:
        raise ValueError("watch page video ID mismatch")
    published = microformat.get("publishDate") or microformat.get("uploadDate")
    if not published:
        raise ValueError("watch page has no publish date")
    return {
        "published_at": datetime.fromisoformat(published).astimezone(timezone.utc).isoformat(),
        "description": str(details.get("shortDescription") or ""),
        "duration_seconds": int(details["lengthSeconds"]) if details.get("lengthSeconds") else None,
        "tags": [str(value) for value in details.get("keywords") or []],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collected-date", required=True, help="UTC YYYY-MM-DD for the current collection")
    parser.add_argument("--sqlite", type=Path, default=Path("data/tastyroad.sqlite"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/youtube"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    sources = {source.name: source for source in load_sources(Path("data/sources/youtube_sources.json"))}
    with sqlite3.connect(args.sqlite) as connection:
        rows = connection.execute(
            """select s.name, v.video_id, v.title, v.published_at, v.description, v.duration_seconds
               from youtube_videos v join sources s on s.id = v.source_id
               where substr(v.collected_at, 1, 10) = ?
                 and (v.published_at = '' or v.description = '' or v.duration_seconds is null)""",
            (args.collected_date,),
        ).fetchall()

    results: dict[tuple[str, str], dict[str, object]] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(fetch_metadata, video_id): (name, video_id) for name, video_id, *_ in rows}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as error:
                print(f"warning: {key[0]}/{key[1]}: {error}")

    with sqlite3.connect(args.sqlite) as connection:
        for name, video_id, title, published_at, description, duration_seconds in rows:
            metadata = results.get((name, video_id))
            if metadata is None:
                continue
            source = sources[name]
            new_description = description or metadata["description"]
            candidates = extract_description_candidates(str(new_description)) or extract_title_candidates(title, source)
            connection.execute(
                """update youtube_videos set published_at = ?, description = ?, duration_seconds = ?,
                   tags = ?, raw_restaurant_name_candidates = ?
                   where video_id = ? and source_id = (select id from sources where name = ?)""",
                (
                    published_at or metadata["published_at"],
                    new_description,
                    duration_seconds if duration_seconds is not None else metadata["duration_seconds"],
                    json.dumps(metadata["tags"], ensure_ascii=False),
                    json.dumps(candidates, ensure_ascii=False),
                    video_id,
                    name,
                ),
            )

    for name, source in sources.items():
        path = args.output_dir / f"{source.key}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for item in payload.get("items", []):
            metadata = results.get((name, item.get("video_id")))
            if metadata is None:
                continue
            item["published_at"] = item.get("published_at") or metadata["published_at"]
            item["description"] = item.get("description") or metadata["description"]
            item["duration_seconds"] = item.get("duration_seconds") or metadata["duration_seconds"]
            item["tags"] = metadata["tags"]
            item["restaurant_name_candidates"] = (
                extract_description_candidates(str(item["description"]))
                or extract_title_candidates(str(item["title"]), source)
            )
            changed = True
        if changed:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"attempted={len(rows)} enriched={len(results)} failed={len(rows) - len(results)}")
    return 0 if len(results) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
