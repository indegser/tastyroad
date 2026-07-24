#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional


ROOT = Path.cwd()
DB_PATH = ROOT / "data" / "tastyroad.sqlite"
TARGET_CONFIG_PATH = ROOT / "data" / "naver_map_list_target.json"
SYNC_STATE_PATH = ROOT / "data" / "naver_map_list_synced_ids.json"
DEFAULT_FAILURE_LOG_PATH = ROOT / "data" / "work" / "naver_map_sync_failures.json"
DEFAULT_LIST_NAME = "Tastyroad"
DEFAULT_CDP_PORT = 9222

# Coordinate fallbacks verified against the Korean desktop Naver Map UI at 1280x900 CSS pixels.
# Prefer selectors first; Naver does not expose the saved-list modal reliably in every state.
PLACE_SAVE = (377, 104)
TARGET_LIST_CHECK = (416, 617)
MODAL_SAVE = (255, 861)
MODAL_CLOSE = (416, 384)
EDIT_SAVED_LIST = (254, 576)
EDIT_SAVED_LIST_FALLBACKS = ((254, 552), (254, 603))

BUTTON_SELECTOR = "button, a, [role='button']"
CHECKBOX_SELECTOR = "button, label, [role='checkbox'], input[type='checkbox']"
SELECTOR_POLL_MS = 150
SELECTOR_CONTROL_LIMIT = 160


@dataclass(frozen=True)
class Place:
    id: int
    name: str
    url: str


FailureMode = Literal["safe", "blind"]
CheckboxState = Literal["selected", "unselected"]


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
  join youtube_video_restaurants m on m.restaurant_id = r.id
  join youtube_videos c on c.id = m.youtube_video_id
  where trim(r.naver_map_id) != ''
    and m.status in ('verified', 'metadata_verified')
    and (
      :source_name is null
      or exists (
        select 1
        from youtube_video_restaurants source_mapping
        join youtube_videos source_video
          on source_video.id = source_mapping.youtube_video_id
        join sources source
          on source.id = source_video.source_id
        where source_mapping.restaurant_id = r.id
          and source_mapping.status in ('verified', 'metadata_verified')
          and source.name = :source_name
      )
    )
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


def load_places(skip_ids: set[int], source_name: Optional[str] = None) -> list[Place]:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            PUBLIC_RESTAURANTS_SQL,
            {"source_name": source_name},
        ).fetchall()

    places = []
    for restaurant_id, name, url in rows:
        if restaurant_id in skip_ids:
            continue
        if not url or not (
            url.startswith("https://map.naver.com/") or url.startswith("https://naver.me/")
        ):
            raise RuntimeError(f"{restaurant_id} {name} has no usable Naver URL: {url!r}")
        places.append(Place(id=int(restaurant_id), name=str(name), url=str(url)))
    return places


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


def load_failure_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    with path.open() as file:
        failures = json.load(file)
    return {int(failure["id"]) for failure in failures if "id" in failure}


def append_failure(path: Path, place: Place, error: Exception) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    if path.exists():
        with path.open() as file:
            failures = json.load(file)
    if any(int(failure.get("id")) == place.id for failure in failures):
        return
    failures.append(
        {
            "id": place.id,
            "name": place.name,
            "url": place.url,
            "error": str(error),
        }
    )
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w") as file:
        json.dump(failures, file, ensure_ascii=False, indent=2)
        file.write("\n")
    tmp_path.replace(path)


def body_text(page) -> str:
    texts = []
    for frame in page.frames:
        try:
            texts.append(frame.locator("body").first.inner_text(timeout=1800))
        except Exception:
            continue
    return "\n".join(texts)


def click(page, point: tuple[int, int]) -> None:
    page.mouse.click(point[0], point[1])


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def control_text(locator) -> str:
    try:
        value = locator.evaluate(
            """element => {
                const parts = [
                    element.getAttribute("aria-label"),
                    element.getAttribute("title"),
                    element.getAttribute("alt"),
                    element.innerText,
                    element.textContent
                ];
                if (element.matches('[role="checkbox"], input[type="checkbox"]')) {
                    parts.push(element.closest("label")?.innerText);
                    parts.push(element.parentElement?.innerText);
                }
                return parts.filter(Boolean).join(" ");
            }"""
        )
    except Exception:
        return ""
    return normalize_text(str(value))


def visible_control_candidates(page, selector: str, text_pattern: re.Pattern[str]):
    for frame in page.frames:
        try:
            controls = frame.locator(selector)
            count = min(controls.count(), SELECTOR_CONTROL_LIMIT)
        except Exception:
            continue
        for index in range(count):
            locator = controls.nth(index)
            try:
                if not locator.is_visible(timeout=150):
                    continue
                text = control_text(locator)
                if not text_pattern.search(text):
                    continue
                box = locator.bounding_box(timeout=150)
            except Exception:
                continue
            yield locator, text, box


def click_control_by_text(
    page,
    selector: str,
    text_pattern: re.Pattern[str],
    timeout_ms: int,
    *,
    prefer_top: bool = False,
    prefer_bottom: bool = False,
    max_y: Optional[float] = None,
    min_y: Optional[float] = None,
) -> bool:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        candidates = list(visible_control_candidates(page, selector, text_pattern))
        if max_y is not None:
            preferred = [
                candidate
                for candidate in candidates
                if candidate[2] is not None and candidate[2]["y"] <= max_y
            ]
            if preferred:
                candidates = preferred
        if min_y is not None:
            candidates = [
                candidate
                for candidate in candidates
                if candidate[2] is not None and candidate[2]["y"] >= min_y
            ]
        if prefer_top:
            candidates.sort(
                key=lambda candidate: candidate[2]["y"] if candidate[2] is not None else 99999
            )
        elif prefer_bottom:
            candidates.sort(
                key=lambda candidate: candidate[2]["y"] if candidate[2] is not None else -1,
                reverse=True,
            )
        for locator, _text, _box in candidates:
            try:
                locator.click(timeout=1000)
                return True
            except Exception:
                continue
        page.wait_for_timeout(SELECTOR_POLL_MS)
    return False


def click_place_save_control(page) -> bool:
    return click_control_by_text(
        page,
        BUTTON_SELECTOR,
        re.compile(r"(^|\s)(저장|저장하기|저장됨)(\s|$)"),
        900,
        prefer_top=True,
        max_y=260,
    )


def click_edit_saved_list_control(page) -> bool:
    return click_control_by_text(
        page,
        BUTTON_SELECTOR,
        re.compile(r"저장한\s*리스트|리스트\s*(수정|편집)|저장됨"),
        700,
        prefer_top=True,
    )


def click_modal_save_control(page) -> bool:
    return click_control_by_text(
        page,
        BUTTON_SELECTOR,
        re.compile(r"(^|\s)저장(\s|$)"),
        900,
        prefer_bottom=True,
        min_y=400,
    )


def click_modal_close_control(page) -> bool:
    return click_control_by_text(
        page,
        BUTTON_SELECTOR,
        re.compile(r"(^|\s)(닫기|close)(\s|$)|닫기", re.IGNORECASE),
        700,
        prefer_top=True,
    )


def checkbox_state_from_selector(locator, text: str) -> Optional[CheckboxState]:
    normalized = normalize_text(text)
    if "선택해제됨" in normalized:
        return "unselected"
    if "선택됨" in normalized:
        return "selected"

    try:
        if locator.is_checked(timeout=150):
            return "selected"
        return "unselected"
    except Exception:
        pass

    try:
        aria_checked = locator.get_attribute("aria-checked", timeout=150)
    except Exception:
        aria_checked = None
    if aria_checked == "true":
        return "selected"
    if aria_checked == "false":
        return "unselected"
    return None


def target_list_checkbox(page, list_name: str):
    escaped_name = re.escape(list_name)
    pattern = re.compile(
        rf"({escaped_name}.*선택(?:해제)?됨|선택(?:해제)?됨.*{escaped_name}|{escaped_name})"
    )
    for locator, text, _box in visible_control_candidates(page, CHECKBOX_SELECTOR, pattern):
        if list_name not in text:
            continue
        state = checkbox_state_from_selector(locator, text)
        if state:
            return locator, state
    return None


def wait_for_checkbox_selector(page, list_name: str, timeout_ms: int):
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        target = target_list_checkbox(page, list_name)
        if target:
            return target
        page.wait_for_timeout(SELECTOR_POLL_MS)
    return None


def checkbox_state(page) -> Optional[CheckboxState]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("safe mode requires Pillow: python3 -m pip install pillow") from exc

    try:
        png = page.screenshot(full_page=False, timeout=5000)
    except Exception:
        return None

    image = Image.open(BytesIO(png)).convert("RGB")
    device_pixel_ratio = page.evaluate("window.devicePixelRatio") or 1
    x = int(TARGET_LIST_CHECK[0] * device_pixel_ratio)
    y = int(TARGET_LIST_CHECK[1] * device_pixel_ratio)
    if x >= image.width or y >= image.height:
        return None

    pixels = [
        image.getpixel((x + dx, y + dy))
        for dx in range(-8, 9)
        for dy in range(-8, 9)
        if 0 <= x + dx < image.width and 0 <= y + dy < image.height
    ]
    blue = sum(1 for r, g, b in pixels if b > 170 and 50 < g < 190 and r < 90)
    grey = sum(1 for r, g, b in pixels if abs(r - g) < 10 and abs(g - b) < 10 and 145 < r < 230)
    if blue >= 20:
        return "selected"
    if grey >= 20:
        return "unselected"
    return None


def wait_for_checkbox(page, timeout_ms: int) -> Optional[CheckboxState]:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        state = checkbox_state(page)
        if state:
            return state
        page.wait_for_timeout(150)
    return None


def wait_for_checkbox_any(page, list_name: str, timeout_ms: int):
    selector_timeout = min(900, max(250, timeout_ms // 2))
    selector_result = wait_for_checkbox_selector(page, list_name, selector_timeout)
    if selector_result:
        locator, state = selector_result
        return state, locator

    remaining_timeout = max(250, timeout_ms - selector_timeout)
    state = wait_for_checkbox(page, remaining_timeout)
    if state:
        return state, None
    return None


def open_save_modal_safe(page, list_name: str):
    edit_points = (EDIT_SAVED_LIST, *EDIT_SAVED_LIST_FALLBACKS)
    for attempt in range(2):
        if not click_place_save_control(page):
            click(page, PLACE_SAVE)
        checkbox = wait_for_checkbox_any(page, list_name, 1400 if attempt == 0 else 2400)
        if checkbox:
            return checkbox
        if click_edit_saved_list_control(page):
            checkbox = wait_for_checkbox_any(page, list_name, 1100 if attempt == 0 else 1700)
            if checkbox:
                return checkbox
        for point in edit_points:
            click(page, point)
            checkbox = wait_for_checkbox_any(page, list_name, 1100 if attempt == 0 else 1700)
            if checkbox:
                return checkbox
        page.wait_for_timeout(700)
    return None


def add_place_safe(page, place: Place, list_name: str) -> str:
    checkbox = open_save_modal_safe(page, list_name)
    if not checkbox:
        raise RuntimeError("save modal checkbox not detected")
    state, checkbox_locator = checkbox
    if state == "selected":
        if not click_modal_close_control(page):
            click(page, MODAL_CLOSE)
        page.wait_for_timeout(250)
        return "already"

    if checkbox_locator is not None:
        checkbox_locator.click(timeout=1000)
    else:
        click(page, TARGET_LIST_CHECK)
    selected_result = wait_for_checkbox_any(page, list_name, 1400)
    selected = selected_result[0] if selected_result else None
    if selected != "selected":
        raise RuntimeError(f"target checkbox did not become selected: {selected}")
    if not click_modal_save_control(page):
        click(page, MODAL_SAVE)
    page.wait_for_timeout(900)
    return "saved"


def add_place_blind(page, place: Place, list_name: str) -> str:
    # Use only for unsynced IDs. This does not inspect the checkbox state, so it
    # avoids screenshot hangs but relies on the sync-state skip list for toggle safety.
    if not click_place_save_control(page):
        click(page, PLACE_SAVE)
    page.wait_for_timeout(900)
    checkbox = wait_for_checkbox_selector(page, list_name, 500)
    if not checkbox and click_edit_saved_list_control(page):
        page.wait_for_timeout(700)
        checkbox = wait_for_checkbox_selector(page, list_name, 700)
    if checkbox:
        checkbox_locator, _state = checkbox
        checkbox_locator.click(timeout=1000)
        page.wait_for_timeout(350)
        if not click_modal_save_control(page):
            click(page, MODAL_SAVE)
        page.wait_for_timeout(900)
        return "attempted"

    # Legacy coordinate recovery path for UI states where the target list is not
    # exposed to selector/text matching.
    click(page, TARGET_LIST_CHECK)
    page.wait_for_timeout(350)
    if not click_modal_save_control(page):
        click(page, MODAL_SAVE)
    page.wait_for_timeout(900)
    if not click_edit_saved_list_control(page):
        click(page, EDIT_SAVED_LIST)
    page.wait_for_timeout(900)
    checkbox = wait_for_checkbox_selector(page, list_name, 700)
    if checkbox:
        checkbox_locator, _state = checkbox
        checkbox_locator.click(timeout=1000)
    else:
        click(page, TARGET_LIST_CHECK)
    page.wait_for_timeout(350)
    if not click_modal_save_control(page):
        click(page, MODAL_SAVE)
    page.wait_for_timeout(900)
    return "attempted"


def assert_place_loaded(page, place: Place, require_place_name: bool) -> None:
    text = body_text(page)
    if "요청하신 페이지를 찾을 수 없습니다" in text:
        raise RuntimeError("Naver place page not found")
    if "내정보 보기" not in text:
        page.wait_for_timeout(1000)
        text = body_text(page)
    if "내정보 보기" not in text:
        raise RuntimeError("Naver login marker missing")
    if require_place_name and place.name not in text:
        raise RuntimeError("Naver place page not loaded")


def connect_browser(cdp_port: int):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("sync requires Playwright: python3 -m pip install playwright") from exc

    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
    except Exception:
        playwright.stop()
        raise
    return playwright, browser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add public Tastyroad restaurants to the fixed Naver Map saved list."
    )
    parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    parser.add_argument("--list-name", default=default_list_name())
    parser.add_argument(
        "--source-name",
        help="Only process restaurants mapped to this exact sources.name value.",
    )
    parser.add_argument("--skip-id", type=int, action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--chunk-size",
        type=int,
        help="Process at most this many places in one browser session, then exit cleanly.",
    )
    parser.add_argument(
        "--mode",
        choices=("safe", "blind"),
        default="safe",
        help=(
            "safe verifies the target checkbox by selector or screenshot before clicking; "
            "blind skips state verification and should only be used for unsynced IDs."
        ),
    )
    parser.add_argument(
        "--include-synced",
        action="store_true",
        help="Also process restaurant IDs already recorded as synced.",
    )
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        help="Do not skip IDs already present in the failure log.",
    )
    parser.add_argument(
        "--failure-log",
        type=Path,
        default=DEFAULT_FAILURE_LOG_PATH,
        help="JSON file for rows that could not be processed.",
    )
    parser.add_argument(
        "--no-require-place-name",
        action="store_true",
        help="Do not require the restaurant display name to appear in the Naver page text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "blind" and args.include_synced:
        raise RuntimeError("--mode blind cannot be combined with --include-synced")

    synced_ids = load_synced_ids(args.list_name)
    skip_ids = set(args.skip_id)
    if not args.include_synced:
        skip_ids.update(synced_ids)
    if not args.retry_failures:
        skip_ids.update(load_failure_ids(args.failure_log))

    places = load_places(skip_ids, source_name=args.source_name)
    if args.limit is not None:
        places = places[: args.limit]
    if args.chunk_size is not None:
        places = places[: args.chunk_size]

    source_scope = args.source_name or "all"
    print(
        f"target_list={args.list_name} source={source_scope} "
        f"places={len(places)} mode={args.mode}"
    )
    if not places:
        return 0

    playwright, browser = connect_browser(args.cdp_port)
    failures = 0
    try:
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        for index, place in enumerate(places, start=1):
            started = time.time()
            try:
                print(f"[{index}/{len(places)}] {place.name} ({place.id})", flush=True)
                page.goto(place.url, wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(2600)
                assert_place_loaded(page, place, require_place_name=not args.no_require_place_name)
                if args.mode == "safe":
                    result = add_place_safe(page, place, args.list_name)
                else:
                    result = add_place_blind(page, place, args.list_name)
                synced_ids.add(place.id)
                save_synced_ids(args.list_name, synced_ids)
                elapsed = time.time() - started
                print(
                    f"[{index}/{len(places)}] {result}; synced_count={len(synced_ids)} "
                    f"elapsed={elapsed:.1f}s",
                    flush=True,
                )
            except Exception as exc:
                failures += 1
                if "Page crashed" in str(exc) or "Target page" in str(exc):
                    raise RuntimeError(f"Naver tab crashed while processing {place.id} {place.name}") from exc
                append_failure(args.failure_log, place, exc)
                print(f"[{index}/{len(places)}] ERROR {place.id}: {exc}", flush=True)
    finally:
        browser.close()
        playwright.stop()

    if failures:
        print(f"completed_with_failures={failures} failure_log={args.failure_log}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
