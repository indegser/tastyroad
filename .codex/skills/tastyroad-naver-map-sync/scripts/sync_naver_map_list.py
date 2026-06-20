#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path.cwd()
DB_PATH = ROOT / "data" / "tastyroad.sqlite"
TARGET_CONFIG_PATH = ROOT / "data" / "naver_map_list_target.json"
SYNC_STATE_PATH = ROOT / "data" / "naver_map_list_synced_ids.json"
DEFAULT_LIST_NAME = "Tastyroad"
DEFAULT_CDP_PORT = 9222

PLACE_SAVE_X = 377
PLACE_SAVE_Y = 104
TARGET_LIST_X = 421
TARGET_LIST_Y = 533
MODAL_SAVE_X = 255
MODAL_SAVE_Y = 860


@dataclass(frozen=True)
class Place:
    id: int
    name: str
    url: str


PUBLIC_RESTAURANTS_SQL = """
with ranked_mentions as (
  select
    r.id,
    r.display_name as name,
    row_number() over (
      partition by r.id
      order by c.published_at desc, c.id desc
    ) as mention_rank
  from restaurants r
  join mentions m on m.restaurant_id = r.id
  join mention_candidates c on c.id = m.mention_candidate_id
  join agent_video_reviews review on review.external_id = c.external_id
  join video_story_reviews story on story.external_id = c.external_id
  where review.decision = 'restaurant_intro'
    and (trim(story.story_hook) != '' or trim(story.story_intro) != '')
    and length(trim(story.story_intro)) >= 240
    and length(trim(story.tasting_flow)) >= 180
),
ranked_links as (
  select
    restaurant_id,
    url,
    row_number() over (
      partition by restaurant_id
      order by
        case provider when 'naver_map' then 0 when 'google_maps' then 1 else 2 end,
        confidence desc,
        verified_at desc
    ) as link_rank
  from place_links
  where provider = 'naver_map'
    and status in ('verified', 'metadata_verified')
    and (url like 'https://map.naver.com/%' or url like 'https://naver.me/%')
    and url not like '%/p/search/%'
)
select ranked_mentions.id, ranked_mentions.name, ranked_links.url
from ranked_mentions
join ranked_links on ranked_links.restaurant_id = ranked_mentions.id
  and ranked_links.link_rank = 1
where ranked_mentions.mention_rank = 1
order by ranked_mentions.name asc, ranked_mentions.id asc
"""


def load_places(skip_ids: set[int]) -> list[Place]:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(PUBLIC_RESTAURANTS_SQL).fetchall()

    places = []
    for restaurant_id, name, url in rows:
        if restaurant_id in skip_ids:
            continue
        if not url or not (
            url.startswith("https://map.naver.com/") or url.startswith("https://naver.me/")
        ):
            raise RuntimeError(f"{restaurant_id} {name} has no usable Naver URL: {url!r}")
        places.append(Place(id=restaurant_id, name=name, url=url))
    return places


def run_browser(cdp_port: int, args: list[str], timeout: float = 40.0) -> str:
    cmd = ["agent-browser", "--cdp", str(cdp_port), *args]
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"{' '.join(cmd)} failed: {detail}")
    return result.stdout.strip()


def default_list_name() -> str:
    if not TARGET_CONFIG_PATH.exists():
        return DEFAULT_LIST_NAME
    with TARGET_CONFIG_PATH.open() as file:
        config = json.load(file)
    return str(config.get("list_name") or DEFAULT_LIST_NAME)


def load_synced_ids(list_name: str) -> set[int]:
    if not SYNC_STATE_PATH.exists():
        return set()
    with SYNC_STATE_PATH.open() as file:
        state = json.load(file)
    if state.get("list_name") != list_name:
        return set()
    return {int(restaurant_id) for restaurant_id in state.get("restaurant_ids", [])}


def save_synced_ids(list_name: str, restaurant_ids: set[int]) -> None:
    payload = {
        "list_name": list_name,
        "restaurant_ids": sorted(restaurant_ids),
    }
    tmp_path = SYNC_STATE_PATH.with_suffix(".json.tmp")
    with tmp_path.open("w") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    tmp_path.replace(SYNC_STATE_PATH)


def click(cdp_port: int, x: int, y: int) -> None:
    run_browser(cdp_port, ["mouse", "move", str(x), str(y)], timeout=10)
    run_browser(cdp_port, ["mouse", "down"], timeout=10)
    run_browser(cdp_port, ["mouse", "up"], timeout=10)


def add_place(cdp_port: int, place: Place, waits: dict[str, str]) -> None:
    run_browser(cdp_port, ["open", place.url], timeout=60)
    run_browser(cdp_port, ["wait", waits["open"]], timeout=float(waits["open"]) / 1000 + 10)
    click(cdp_port, PLACE_SAVE_X, PLACE_SAVE_Y)
    run_browser(cdp_port, ["wait", waits["modal"]], timeout=float(waits["modal"]) / 1000 + 10)
    click(cdp_port, TARGET_LIST_X, TARGET_LIST_Y)
    run_browser(cdp_port, ["wait", waits["select"]], timeout=float(waits["select"]) / 1000 + 10)
    click(cdp_port, MODAL_SAVE_X, MODAL_SAVE_Y)
    run_browser(cdp_port, ["wait", waits["save"]], timeout=float(waits["save"]) / 1000 + 10)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add public Tastyroad restaurants to the fixed Naver Map saved list."
    )
    parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    parser.add_argument("--list-name", default=default_list_name())
    parser.add_argument("--skip-id", type=int, action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--include-synced",
        action="store_true",
        help="Also process restaurant IDs already recorded as synced.",
    )
    parser.add_argument("--open-wait-ms", default="5000")
    parser.add_argument("--modal-wait-ms", default="1500")
    parser.add_argument("--select-wait-ms", default="700")
    parser.add_argument("--save-wait-ms", default="2500")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    synced_ids = load_synced_ids(args.list_name)
    skip_ids = set(args.skip_id)
    if not args.include_synced:
        skip_ids.update(synced_ids)

    places = load_places(skip_ids)
    if args.limit is not None:
        places = places[: args.limit]

    waits = {
        "open": args.open_wait_ms,
        "modal": args.modal_wait_ms,
        "select": args.select_wait_ms,
        "save": args.save_wait_ms,
    }

    print(f"target_list={args.list_name} places={len(places)}")
    for index, place in enumerate(places, start=1):
        print(f"[{index}/{len(places)}] {place.name} ({place.id})", flush=True)
        add_place(args.cdp_port, place, waits)
        synced_ids.add(place.id)
        save_synced_ids(args.list_name, synced_ids)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
