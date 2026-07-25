#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("data/sources/youtube_sources.json")
DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_OUTPUT_DIR = Path("data/work")


def load_source(config_path: Path, source_key: str) -> dict[str, Any]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    for source in payload.get("sources", []):
        if source.get("key") == source_key:
            return source
    raise SystemExit(f"Source not found in {config_path}: {source_key}")


def channel_urls(source: dict[str, Any]) -> list[str]:
    playlist_url = str(source.get("playlist_url") or "")
    urls: list[str] = []

    if playlist_url:
        urls.append(playlist_url)
    else:
        channel_id = source.get("channel_id")
        if channel_id:
            urls.append(f"https://www.youtube.com/channel/{channel_id}/videos")

        feed_url = str(source.get("feed_url") or "")
        marker = "channel_id="
        if not urls and marker in feed_url:
            channel_id = feed_url.split(marker, 1)[1].split("&", 1)[0]
            if channel_id:
                urls.append(f"https://www.youtube.com/channel/{channel_id}/videos")

        official_url = str(source.get("official_url") or "")
        if not urls and "playlist?list=" in official_url:
            urls.append(official_url)
        if not urls and "/channel/" in official_url:
            urls.append(official_url.rstrip("/") + "/videos")

    urls.extend(str(url) for url in source.get("playlist_urls", []) if str(url))
    deduped = list(dict.fromkeys(urls))
    if deduped:
        return deduped

    raise SystemExit(f"Source {source.get('key')} needs playlist_url, playlist_urls, channel_id, or channel feed_url for full-channel audit")


def fetch_full_channel(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_video_ids: set[str] = set()

    for url in channel_urls(source):
        command = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--quiet",
            "--no-warnings",
            "--flat-playlist",
            "--extractor-args",
            "youtube:lang=ko",
            "--dump-json",
            url,
        ]
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
        except subprocess.CalledProcessError as error:
            if error.stderr:
                print(error.stderr.strip(), file=sys.stderr)
            raise SystemExit(f"yt-dlp failed with exit code {error.returncode}")

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
            rows.append(
                {
                    "playlist_index": len(rows) + 1,
                    "video_id": video_id,
                    "upload_date": item.get("upload_date") or "NA",
                    "title": title,
                    "url": item.get("webpage_url") or item.get("url") or f"https://www.youtube.com/watch?v={video_id}",
                }
            )

    return rows


def should_include_title(title: str, source: dict[str, Any]) -> bool:
    title_include_any = list(source.get("title_include_any", []))
    title_exclude_any = list(source.get("title_exclude_any", []))
    title_folded = title.casefold()
    if title_include_any and not any(keyword.casefold() in title_folded for keyword in title_include_any):
        return False
    if any(keyword.casefold() in title_folded for keyword in title_exclude_any):
        return False
    return True


def load_collected_ids(sqlite_path: Path, source_name: str) -> set[str]:
    with sqlite3.connect(sqlite_path) as connection:
        rows = connection.execute(
            """
            select c.video_id
            from youtube_videos c
            join sources s on s.id = c.source_id
            where s.name = ?
            """,
            (source_name,),
        ).fetchall()
    return {str(row[0]) for row in rows}


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["playlist_index", "video_id", "upload_date", "title", "url"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit missing Tastyroad YouTube channel videos.")
    parser.add_argument("--source", required=True, help="Source key from data/sources/youtube_sources.json")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    source = load_source(args.config, args.source)
    source_name = str(source.get("name") or args.source)
    full_rows = fetch_full_channel(source)
    collected_ids = load_collected_ids(args.sqlite, source_name)
    missing_rows = [row for row in full_rows if row["video_id"] not in collected_ids]

    full_path = args.output_dir / f"{args.source}_full_channel_videos.tsv"
    missing_path = args.output_dir / f"{args.source}_missing_videos.tsv"
    write_tsv(full_path, full_rows)
    write_tsv(missing_path, missing_rows)

    print(f"source: {source_name} ({args.source})")
    print(f"remote_total: {len(full_rows)}")
    print(f"local_collected: {len(collected_ids)}")
    print(f"missing: {len(missing_rows)}")
    print(f"full_channel_file: {full_path}")
    print(f"missing_file: {missing_path}")

    for row in missing_rows[:10]:
        print(
            f"{row['playlist_index']}\t{row['video_id']}\t{row['upload_date']}\t{row['title']}\t{row['url']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
