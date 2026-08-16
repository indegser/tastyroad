#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional


ROOT = Path.cwd()
DB_PATH = ROOT / "data" / "tastyroad.sqlite"
TARGET_CONFIG_PATH = ROOT / "data" / "naver_map_list_target.json"
SYNC_STATE_PATH = ROOT / "data" / "naver_map_list_synced_ids.json"
DEFAULT_FAILURE_LOG_PATH = ROOT / "data" / "work" / "naver_map_sync_failures.json"
DEFAULT_RESULT_PATH = ROOT / "data" / "work" / "naver_map_sync_result.json"
DEFAULT_FAILURE_ARTIFACTS_DIR = ROOT / "data" / "work" / "naver_map_sync_failures"
DEFAULT_LIST_NAME = "Tastyroad"
DEFAULT_CDP_PORT = 9222
DEFAULT_BROWSER_BACKEND = "agent-browser"
DEFAULT_AGENT_BROWSER_SESSION = "tastyroad-naver-map-sync"
DEFAULT_AGENT_BROWSER_MAX_OUTPUT = 60000
DEFAULT_MAX_LIST_SIZE = 1000
DEFAULT_ATTEMPTS = 3

SELECTOR_POLL_MS = 150
PLACE_FRAME_HOST = "pcmap.place.naver.com"
SAVE_MODAL_CHECKBOX_SELECTOR = "button.swt-save-group-info[role='checkbox']"
SAVE_MODAL_SAVE_SELECTOR = "button.swt-save-btn"
SAVE_MODAL_CLOSE_SELECTOR = "button.swt-close-btn"
PLACE_SAVE_SELECTOR = 'a[href="#bookmark"][role="button"]'


@dataclass(frozen=True)
class Place:
    id: int
    name: str
    url: str


@dataclass(frozen=True)
class AgentBrowserConfig:
    session: str
    session_name: str
    profile: Optional[Path]
    provider: Optional[str]
    headed: bool
    max_output: int


@dataclass(frozen=True)
class BrowserRef:
    role: str
    name: str
    ref: str
    line_index: int


CheckboxState = Literal["selected", "unselected"]


class PermanentSyncError(RuntimeError):
    pass


class BrowserAuthUnavailable(RuntimeError):
    pass


class PlacePageNotFound(PermanentSyncError):
    pass


class PlaceNameMismatch(PermanentSyncError):
    pass


class ListCapacityReached(PermanentSyncError):
    pass


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


def load_places(
    skip_ids: set[int],
    source_name: Optional[str] = None,
    restaurant_ids: set[int] | None = None,
) -> list[Place]:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            PUBLIC_RESTAURANTS_SQL,
            {"source_name": source_name},
        ).fetchall()

    places = []
    for restaurant_id, name, url in rows:
        if restaurant_ids is not None and restaurant_id not in restaurant_ids:
            continue
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


def load_synced_ids(list_name: str, path: Path = SYNC_STATE_PATH) -> set[int]:
    if not path.exists():
        return set()
    with path.open() as file:
        state = json.load(file)
    if state.get("list_name") != list_name:
        return set()
    return {int(restaurant_id) for restaurant_id in state.get("restaurant_ids", [])}


def load_state_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    with path.open() as file:
        state = json.load(file)
    return {int(restaurant_id) for restaurant_id in state.get("restaurant_ids", [])}


def save_synced_ids(list_name: str, restaurant_ids: set[int], path: Path) -> None:
    payload = {
        "list_name": list_name,
        "restaurant_ids": sorted(restaurant_ids),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    tmp_path.replace(path)


def load_failure_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    with path.open() as file:
        failures = json.load(file)
    return {int(failure["id"]) for failure in failures if "id" in failure}


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    tmp_path.replace(path)


def load_failures(path: Path) -> list[dict[str, object]]:
    if path.exists():
        with path.open() as file:
            value = json.load(file)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def record_failure(
    path: Path,
    place: Place,
    error: Exception,
    attempts: int,
    screenshot_path: Optional[Path],
) -> None:
    failures = [
        failure
        for failure in load_failures(path)
        if int(failure.get("id") or 0) != place.id
    ]
    failures.append(
        {
            "id": place.id,
            "name": place.name,
            "url": place.url,
            "error": str(error),
            "attempts": attempts,
            "permanent": isinstance(error, PermanentSyncError),
            "screenshot": str(screenshot_path) if screenshot_path else None,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    save_json(path, failures)


def clear_failure(path: Path, restaurant_id: int) -> None:
    if not path.exists():
        return
    failures = [
        failure
        for failure in load_failures(path)
        if int(failure.get("id") or 0) != restaurant_id
    ]
    save_json(path, failures)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_place_name(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", normalize_text(value).casefold())


def place_name_matches(expected: str, page_text: str) -> bool:
    normalized_expected = normalize_place_name(expected)
    normalized_page = normalize_place_name(page_text)
    return bool(normalized_expected and normalized_expected in normalized_page)


def list_name_pattern(list_name: str) -> re.Pattern[str]:
    return re.compile(
        rf"^(?:(?:비공개|일부 공개|전체 공개)\s*)?"
        rf"폴더명\s*{re.escape(list_name)}\s*장소수\s*[\d,]+\s*선택(?:해제)?됨$"
    )


def parse_list_count(text: str) -> int:
    match = re.search(r"장소수\s*([\d,]+)", normalize_text(text))
    if not match:
        raise RuntimeError(f"target list count is unavailable: {normalize_text(text)!r}")
    return int(match.group(1).replace(",", ""))


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


def target_list_checkbox(frame, list_name: str):
    candidates = frame.locator(SAVE_MODAL_CHECKBOX_SELECTOR)
    pattern = list_name_pattern(list_name)
    for index in range(candidates.count()):
        locator = candidates.nth(index)
        try:
            if not locator.is_visible(timeout=100):
                continue
            text = normalize_text(locator.inner_text(timeout=300))
        except Exception:
            continue
        if not pattern.fullmatch(text):
            continue
        state = checkbox_state_from_selector(locator, text)
        if state:
            return locator, state, parse_list_count(text)
    return None


def wait_for_target_list(
    frame,
    list_name: str,
    timeout_ms: int,
    settle_ms: int = 700,
):
    deadline = time.time() + timeout_ms / 1000
    first_seen_at: Optional[float] = None
    while time.time() < deadline:
        target = target_list_checkbox(frame, list_name)
        if target:
            if first_seen_at is None:
                first_seen_at = time.time()
            if (time.time() - first_seen_at) * 1000 >= settle_ms:
                return target
        else:
            first_seen_at = None
        frame.page.wait_for_timeout(SELECTOR_POLL_MS)
    return None


def wait_for_target_list_state(
    frame,
    list_name: str,
    expected: CheckboxState,
    timeout_ms: int,
) -> bool:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        target = target_list_checkbox(frame, list_name)
        if target and target[1] == expected:
            return True
        frame.page.wait_for_timeout(SELECTOR_POLL_MS)
    return False


def find_place_frame(page):
    return next((frame for frame in page.frames if PLACE_FRAME_HOST in frame.url), None)


def assert_place_loaded(page, place: Place, require_place_name: bool):
    deadline = time.time() + 10
    frame = None
    text = ""
    login_visible = False
    while time.time() < deadline:
        frame = find_place_frame(page)
        try:
            login_visible = page.locator("a").filter(
                has_text=re.compile(r"내정보\s*보기")
            ).first.is_visible(timeout=200)
        except Exception:
            login_visible = False
        if frame is None:
            page.wait_for_timeout(SELECTOR_POLL_MS)
            continue
        try:
            text = frame.locator("body").inner_text(timeout=500)
        except Exception:
            text = ""
        if "요청하신 페이지를 찾을 수 없습니다" in text:
            raise PlacePageNotFound("Naver place page not found")
        if login_visible and (not require_place_name or place_name_matches(place.name, text)):
            return frame
        page.wait_for_timeout(SELECTOR_POLL_MS)
    if not login_visible:
        raise RuntimeError("Naver login marker missing")
    if frame is None:
        raise RuntimeError("Naver place frame not loaded")
    if require_place_name and not place_name_matches(place.name, text):
        raise PlaceNameMismatch(f"Naver place name mismatch: expected {place.name!r}")
    raise RuntimeError("Naver place page not loaded")


def open_save_modal(frame, list_name: str):
    modal_save = frame.locator(SAVE_MODAL_SAVE_SELECTOR).first
    try:
        modal_open = modal_save.is_visible(timeout=100)
    except Exception:
        modal_open = False
    if modal_open:
        target = wait_for_target_list(frame, list_name, 5000)
        if target:
            return target
    save_control = frame.locator(PLACE_SAVE_SELECTOR).first
    save_control.wait_for(state="visible", timeout=5000)
    save_control.click(timeout=4000)
    target = wait_for_target_list(frame, list_name, 5000)
    if not target:
        raise RuntimeError(f"save modal target list not found: {list_name}")
    return target


def close_save_modal(frame) -> None:
    close_button = frame.locator(SAVE_MODAL_CLOSE_SELECTOR).first
    if close_button.is_visible(timeout=300):
        close_button.click(timeout=3000)
        close_button.wait_for(state="hidden", timeout=3000)


def add_place_playwright(
    frame,
    place: Place,
    list_name: str,
    max_list_size: int,
) -> str:
    checkbox, state, list_count = open_save_modal(frame, list_name)
    if state == "selected":
        close_save_modal(frame)
        return "already"
    if list_count >= max_list_size:
        close_save_modal(frame)
        raise ListCapacityReached(
            f"target list {list_name!r} is full: {list_count}/{max_list_size}"
        )

    checkbox.locator(".swt-save-group-check-area").click(timeout=4000)
    if not wait_for_target_list_state(frame, list_name, "selected", 3000):
        raise RuntimeError("target checkbox did not become selected")

    save_button = frame.locator(SAVE_MODAL_SAVE_SELECTOR).first
    save_button.wait_for(state="visible", timeout=3000)
    save_button.click(timeout=4000)
    save_button.wait_for(state="hidden", timeout=5000)

    verified_checkbox, verified_state, _verified_count = open_save_modal(frame, list_name)
    if verified_state != "selected":
        raise RuntimeError("target checkbox selection did not persist after save")
    close_save_modal(frame)
    return "saved"


def agent_browser_base_command(config: AgentBrowserConfig) -> list[str]:
    command = [
        "agent-browser",
        "--session",
        config.session,
        "--session-name",
        config.session_name,
        "--max-output",
        str(config.max_output),
    ]
    if config.profile is not None:
        command.extend(["--profile", str(config.profile)])
    if config.provider:
        command.extend(["--provider", config.provider])
    if config.headed:
        command.append("--headed")
    return command


def run_agent_browser(config: AgentBrowserConfig, *args: str) -> str:
    command = [*agent_browser_base_command(config), *args]
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        message = normalize_text(completed.stderr or completed.stdout)
        raise RuntimeError(f"agent-browser {' '.join(args)} failed: {message}")
    return completed.stdout


def agent_browser_open(config: AgentBrowserConfig, url: str) -> None:
    run_agent_browser(config, "open", url)


def agent_browser_wait(config: AgentBrowserConfig, milliseconds: int) -> None:
    run_agent_browser(config, "wait", str(milliseconds))


def agent_browser_snapshot(config: AgentBrowserConfig) -> str:
    return run_agent_browser(config, "snapshot", "-i")


def agent_browser_click(config: AgentBrowserConfig, ref: str) -> None:
    run_agent_browser(config, "click", f"@{ref}")


def snapshot_has_naver_login(snapshot: str) -> bool:
    logged_in = "내 프로필 이미지 내정보 보기" in snapshot
    login_link = re.search(r'link\s+"로그인"', snapshot) is not None
    return logged_in and not login_link


def assert_agent_browser_logged_in(config: AgentBrowserConfig) -> None:
    agent_browser_open(config, "https://map.naver.com")
    agent_browser_wait(config, 2500)
    snapshot = agent_browser_snapshot(config)
    if snapshot_has_naver_login(snapshot):
        return
    raise BrowserAuthUnavailable(
        "Naver login marker missing; open https://nid.naver.com/nidlogin.login "
        "in the configured browser session, log in, then retry."
    )


def parse_browser_refs(snapshot: str) -> list[BrowserRef]:
    pattern = re.compile(
        r'^\s*-\s+(?P<role>button|link|checkbox)\s+"(?P<name>.*?)"\s+\[ref=(?P<ref>[^\]]+)\]'
    )
    refs: list[BrowserRef] = []
    for index, line in enumerate(snapshot.splitlines()):
        match = pattern.search(line)
        if not match:
            continue
        refs.append(
            BrowserRef(
                role=match.group("role"),
                name=normalize_text(match.group("name")),
                ref=match.group("ref"),
                line_index=index,
            )
        )
    return refs


def first_browser_ref(
    snapshot: str,
    *,
    role: str | None = None,
    name_pattern: re.Pattern[str],
    after_line_index: int | None = None,
) -> BrowserRef | None:
    for ref in parse_browser_refs(snapshot):
        if role and ref.role != role:
            continue
        if after_line_index is not None and ref.line_index <= after_line_index:
            continue
        if name_pattern.search(ref.name):
            return ref
    return None


def target_list_checkbox_from_snapshot(
    snapshot: str,
    list_name: str,
) -> tuple[BrowserRef, CheckboxState, int] | None:
    pattern = list_name_pattern(list_name)
    for ref in parse_browser_refs(snapshot):
        if ref.role != "checkbox":
            continue
        if not pattern.fullmatch(ref.name):
            continue
        if "선택해제됨" in ref.name:
            return ref, "unselected", parse_list_count(ref.name)
        if "선택됨" in ref.name:
            return ref, "selected", parse_list_count(ref.name)
    return None


def wait_for_target_list_agent_browser(
    config: AgentBrowserConfig,
    list_name: str,
    timeout_ms: int,
    settle_ms: int = 700,
) -> tuple[BrowserRef, CheckboxState, int] | None:
    deadline = time.time() + timeout_ms / 1000
    first_seen_at: Optional[float] = None
    latest_target: tuple[BrowserRef, CheckboxState, int] | None = None
    while time.time() < deadline:
        snapshot = agent_browser_snapshot(config)
        target = target_list_checkbox_from_snapshot(snapshot, list_name)
        if target:
            latest_target = target
            if first_seen_at is None:
                first_seen_at = time.time()
            if (time.time() - first_seen_at) * 1000 >= settle_ms:
                return latest_target
        else:
            first_seen_at = None
            latest_target = None
        agent_browser_wait(config, SELECTOR_POLL_MS)
    return latest_target


def wait_for_target_list_state_agent_browser(
    config: AgentBrowserConfig,
    list_name: str,
    expected: CheckboxState,
    timeout_ms: int,
) -> bool:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        snapshot = agent_browser_snapshot(config)
        target = target_list_checkbox_from_snapshot(snapshot, list_name)
        if target and target[1] == expected:
            return True
        agent_browser_wait(config, SELECTOR_POLL_MS)
    return False


def assert_place_loaded_agent_browser(
    config: AgentBrowserConfig,
    place: Place,
    require_place_name: bool,
) -> None:
    deadline = time.time() + 10
    latest_snapshot = ""
    while time.time() < deadline:
        latest_snapshot = agent_browser_snapshot(config)
        if "요청하신 페이지를 찾을 수 없습니다" in latest_snapshot:
            raise PlacePageNotFound("Naver place page not found")
        logged_in = snapshot_has_naver_login(latest_snapshot)
        login_link = re.search(r'link\s+"로그인"', latest_snapshot) is not None
        if logged_in and (not require_place_name or place_name_matches(place.name, latest_snapshot)):
            return
        if login_link and not logged_in:
            raise BrowserAuthUnavailable("Naver login marker missing")
        agent_browser_wait(config, SELECTOR_POLL_MS)
    if not snapshot_has_naver_login(latest_snapshot):
        raise BrowserAuthUnavailable("Naver login marker missing")
    if require_place_name and not place_name_matches(place.name, latest_snapshot):
        raise PlaceNameMismatch(f"Naver place name mismatch: expected {place.name!r}")
    raise RuntimeError("Naver place page not loaded")


def open_save_modal_agent_browser(
    config: AgentBrowserConfig,
    list_name: str,
) -> tuple[BrowserRef, CheckboxState, int]:
    target = wait_for_target_list_agent_browser(config, list_name, 600)
    if target:
        return target
    snapshot = agent_browser_snapshot(config)
    save_ref = first_browser_ref(
        snapshot,
        name_pattern=re.compile(r"^저장$"),
    )
    if save_ref is None:
        raise RuntimeError("place save button not found")
    agent_browser_click(config, save_ref.ref)
    target = wait_for_target_list_agent_browser(config, list_name, 5000)
    if not target:
        raise RuntimeError(f"save modal target list not found: {list_name}")
    return target


def close_save_modal_agent_browser(config: AgentBrowserConfig) -> None:
    snapshot = agent_browser_snapshot(config)
    close_ref = first_browser_ref(
        snapshot,
        role="button",
        name_pattern=re.compile(r"^(닫기|취소)$"),
    )
    if close_ref is not None:
        agent_browser_click(config, close_ref.ref)
        agent_browser_wait(config, 700)


def add_place_agent_browser(
    config: AgentBrowserConfig,
    place: Place,
    list_name: str,
    max_list_size: int,
) -> str:
    checkbox, state, list_count = open_save_modal_agent_browser(config, list_name)
    if state == "selected":
        close_save_modal_agent_browser(config)
        return "already"
    if list_count >= max_list_size:
        close_save_modal_agent_browser(config)
        raise ListCapacityReached(
            f"target list {list_name!r} is full: {list_count}/{max_list_size}"
        )

    agent_browser_click(config, checkbox.ref)
    if not wait_for_target_list_state_agent_browser(config, list_name, "selected", 3000):
        raise RuntimeError("target checkbox did not become selected")

    snapshot = agent_browser_snapshot(config)
    save_button = first_browser_ref(
        snapshot,
        role="button",
        name_pattern=re.compile(r"^저장$"),
        after_line_index=checkbox.line_index,
    ) or first_browser_ref(
        snapshot,
        role="button",
        name_pattern=re.compile(r"^저장$"),
    )
    if save_button is None:
        raise RuntimeError("save modal action button not found")
    agent_browser_click(config, save_button.ref)
    agent_browser_wait(config, 1200)

    _verified_checkbox, verified_state, _verified_count = open_save_modal_agent_browser(
        config,
        list_name,
    )
    if verified_state != "selected":
        raise RuntimeError("target checkbox selection did not persist after save")
    close_save_modal_agent_browser(config)
    return "saved"


def process_place_agent_browser(
    config: AgentBrowserConfig,
    place: Place,
    list_name: str,
    require_place_name: bool,
    max_list_size: int,
) -> str:
    agent_browser_open(config, place.url)
    agent_browser_wait(config, 2500)
    assert_place_loaded_agent_browser(config, place, require_place_name=require_place_name)
    return add_place_agent_browser(config, place, list_name, max_list_size)


def capture_failure_screenshot_agent_browser(
    config: AgentBrowserConfig,
    place: Place,
    directory: Path,
) -> Optional[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{place.id}.png"
    try:
        run_agent_browser(config, "screenshot", str(path))
    except Exception:
        return None
    return path


def capture_failure_screenshot(page, place: Place, directory: Path) -> Optional[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{place.id}.png"
    try:
        page.screenshot(path=str(path), full_page=False, timeout=5000)
    except Exception:
        return None
    return path


def process_place(
    page,
    place: Place,
    list_name: str,
    require_place_name: bool,
    max_list_size: int,
) -> str:
    page.goto(place.url, wait_until="domcontentloaded", timeout=35000)
    frame = assert_place_loaded(page, place, require_place_name=require_place_name)
    return add_place_playwright(frame, place, list_name, max_list_size)


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


def assert_cdp_logged_in(page) -> None:
    page.goto("https://map.naver.com", wait_until="domcontentloaded", timeout=35000)
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            logged_in = page.locator("a").filter(
                has_text=re.compile(r"내정보\s*보기")
            ).first.is_visible(timeout=200)
        except Exception:
            logged_in = False
        try:
            login_link = page.locator("a").filter(
                has_text=re.compile(r"^로그인$")
            ).first.is_visible(timeout=200)
        except Exception:
            login_link = False
        if logged_in and not login_link:
            return
        if login_link and not logged_in:
            break
        page.wait_for_timeout(SELECTOR_POLL_MS)
    raise BrowserAuthUnavailable(
        "Naver login marker missing; log in to the connected browser session, then retry."
    )


def write_result(
    path: Path,
    *,
    status: str,
    browser_backend: str,
    target_list: str,
    source: str,
    restaurant_ids: list[int],
    planned: int,
    processed: int = 0,
    saved: int = 0,
    already: int = 0,
    failed_ids: list[int] | None = None,
    remaining: int = 0,
    synced_count: int = 0,
    failure_log: Path | None = None,
    auth_message: str | None = None,
) -> None:
    failed_ids = failed_ids or []
    payload = {
        "status": status,
        "browser_backend": browser_backend,
        "target_list": target_list,
        "source": source,
        "restaurant_ids": restaurant_ids,
        "planned": planned,
        "processed": processed,
        "saved": saved,
        "already": already,
        "failed": len(failed_ids),
        "failed_ids": failed_ids,
        "remaining": remaining,
        "synced_count": synced_count,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    if failure_log is not None:
        payload["failure_log"] = str(failure_log)
    if auth_message:
        payload["auth_message"] = auth_message
    save_json(path, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add public Tastyroad restaurants to the fixed Naver Map saved list."
    )
    parser.add_argument(
        "--browser-backend",
        choices=["agent-browser", "cdp"],
        default=DEFAULT_BROWSER_BACKEND,
        help="Browser control backend. agent-browser uses a persistent Codex browser session; cdp attaches to an existing Chromium CDP port.",
    )
    parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    parser.add_argument(
        "--agent-browser-session",
        default=DEFAULT_AGENT_BROWSER_SESSION,
        help="Persistent agent-browser session ID for Naver Map sync.",
    )
    parser.add_argument(
        "--agent-browser-session-name",
        default=DEFAULT_AGENT_BROWSER_SESSION,
        help="Human-readable agent-browser session name.",
    )
    parser.add_argument(
        "--agent-browser-profile",
        type=Path,
        help="Optional agent-browser profile directory to reuse.",
    )
    parser.add_argument(
        "--agent-browser-provider",
        help="Optional agent-browser provider override.",
    )
    parser.add_argument(
        "--agent-browser-headed",
        action="store_true",
        help="Open the agent-browser session headed for interactive login or debugging.",
    )
    parser.add_argument(
        "--agent-browser-max-output",
        type=int,
        default=DEFAULT_AGENT_BROWSER_MAX_OUTPUT,
        help="Maximum output bytes requested from agent-browser commands.",
    )
    parser.add_argument("--list-name", default=default_list_name())
    parser.add_argument(
        "--source-name",
        help="Only process restaurants mapped to this exact sources.name value.",
    )
    parser.add_argument(
        "--restaurant-id",
        type=int,
        action="append",
        default=[],
        help="Only process this restaurant ID. Repeatable.",
    )
    parser.add_argument(
        "--sync-state",
        type=Path,
        default=SYNC_STATE_PATH,
        help="State file for IDs confirmed in the target list.",
    )
    parser.add_argument(
        "--exclude-state",
        type=Path,
        action="append",
        default=[],
        help="State file whose restaurant IDs should be excluded. Repeatable.",
    )
    parser.add_argument("--skip-id", type=int, action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--chunk-size",
        type=int,
        help="Process at most this many places in one browser session, then exit cleanly.",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=DEFAULT_ATTEMPTS,
        help="Maximum attempts per place for transient navigation or UI failures.",
    )
    parser.add_argument(
        "--retry-delay-ms",
        type=int,
        default=700,
        help="Base delay between transient retries; multiplied by the attempt number.",
    )
    parser.add_argument(
        "--max-list-size",
        type=int,
        default=DEFAULT_MAX_LIST_SIZE,
        help="Stop before adding to a target list at this visible Naver count.",
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
        "--result-json",
        type=Path,
        default=DEFAULT_RESULT_PATH,
        help="Write a structured completion, partial-failure, or interruption summary.",
    )
    parser.add_argument(
        "--failure-artifacts-dir",
        type=Path,
        default=DEFAULT_FAILURE_ARTIFACTS_DIR,
        help="Capture a screenshot only after a place exhausts all attempts.",
    )
    parser.add_argument(
        "--no-require-place-name",
        action="store_true",
        help="Do not require the restaurant display name to appear in the Naver page text.",
    )
    parser.add_argument(
        "--skip-login-preflight",
        action="store_true",
        help="Skip the upfront Naver login marker check. Use only for manual browser debugging.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Plan the requested IDs and verify the browser login marker, then exit without saving places.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.attempts < 1:
        raise RuntimeError("--attempts must be at least 1")
    if args.retry_delay_ms < 0:
        raise RuntimeError("--retry-delay-ms cannot be negative")
    if args.max_list_size < 1:
        raise RuntimeError("--max-list-size must be at least 1")
    if args.agent_browser_max_output < 1:
        raise RuntimeError("--agent-browser-max-output must be at least 1")

    agent_browser_config = AgentBrowserConfig(
        session=args.agent_browser_session,
        session_name=args.agent_browser_session_name,
        profile=args.agent_browser_profile,
        provider=args.agent_browser_provider,
        headed=args.agent_browser_headed,
        max_output=args.agent_browser_max_output,
    )

    synced_ids = load_synced_ids(args.list_name, args.sync_state)
    skip_ids = set(args.skip_id)
    if not args.include_synced:
        skip_ids.update(synced_ids)
    for exclude_state in args.exclude_state:
        skip_ids.update(load_state_ids(exclude_state))
    if not args.retry_failures:
        skip_ids.update(load_failure_ids(args.failure_log))

    requested_restaurant_ids = set(args.restaurant_id) if args.restaurant_id else None
    places = load_places(
        skip_ids,
        source_name=args.source_name,
        restaurant_ids=requested_restaurant_ids,
    )
    if args.limit is not None:
        places = places[: args.limit]
    if args.chunk_size is not None:
        places = places[: args.chunk_size]

    source_scope = args.source_name or "all"
    restaurant_scope = (
        ",".join(str(restaurant_id) for restaurant_id in sorted(requested_restaurant_ids))
        if requested_restaurant_ids is not None
        else "all"
    )
    print(
        f"target_list={args.list_name} source={source_scope} restaurants={restaurant_scope} "
        f"places={len(places)} attempts={args.attempts} control={args.browser_backend}"
    )
    if not places:
        write_result(
            args.result_json,
            status="complete",
            browser_backend=args.browser_backend,
            target_list=args.list_name,
            source=source_scope,
            restaurant_ids=sorted(requested_restaurant_ids or []),
            planned=0,
            remaining=0,
            synced_count=len(synced_ids),
        )
        return 0

    playwright = None
    browser = None
    saved = 0
    already = 0
    failures: list[int] = []
    processed = 0
    interrupted = False
    capacity_reached = False
    page = None
    try:
        if args.browser_backend == "cdp":
            playwright, browser = connect_browser(args.cdp_port)
            context = browser.contexts[0]
            page = context.new_page()
        if not args.skip_login_preflight:
            try:
                if args.browser_backend == "cdp":
                    if page is None:
                        raise RuntimeError("CDP page was not initialized")
                    assert_cdp_logged_in(page)
                else:
                    assert_agent_browser_logged_in(agent_browser_config)
            except BrowserAuthUnavailable as exc:
                write_result(
                    args.result_json,
                    status="auth_blocked",
                    browser_backend=args.browser_backend,
                    target_list=args.list_name,
                    source=source_scope,
                    restaurant_ids=sorted(requested_restaurant_ids or []),
                    planned=len(places),
                    processed=0,
                    saved=0,
                    already=0,
                    failed_ids=[],
                    remaining=len(places),
                    synced_count=len(synced_ids),
                    failure_log=args.failure_log,
                    auth_message=str(exc),
                )
                print(
                    f"status=auth_blocked planned={len(places)} remaining={len(places)} "
                    f"result={args.result_json} message={exc}",
                    flush=True,
                )
                return 0
        if args.preflight_only:
            write_result(
                args.result_json,
                status="preflight_ready",
                browser_backend=args.browser_backend,
                target_list=args.list_name,
                source=source_scope,
                restaurant_ids=sorted(requested_restaurant_ids or []),
                planned=len(places),
                processed=0,
                saved=0,
                already=0,
                failed_ids=[],
                remaining=len(places),
                synced_count=len(synced_ids),
                failure_log=args.failure_log,
            )
            print(
                f"status=preflight_ready planned={len(places)} remaining={len(places)} "
                f"result={args.result_json}",
                flush=True,
            )
            return 0
        for index, place in enumerate(places, start=1):
            started = time.time()
            print(f"[{index}/{len(places)}] {place.name} ({place.id})", flush=True)
            final_error: Optional[Exception] = None
            attempts_used = 0
            result = ""
            for attempt in range(1, args.attempts + 1):
                attempts_used = attempt
                try:
                    if args.browser_backend == "cdp":
                        if page is None:
                            raise RuntimeError("CDP page was not initialized")
                        result = process_place(
                            page,
                            place,
                            args.list_name,
                            require_place_name=not args.no_require_place_name,
                            max_list_size=args.max_list_size,
                        )
                    else:
                        result = process_place_agent_browser(
                            agent_browser_config,
                            place,
                            args.list_name,
                            require_place_name=not args.no_require_place_name,
                            max_list_size=args.max_list_size,
                        )
                    final_error = None
                    break
                except PermanentSyncError as exc:
                    final_error = exc
                    break
                except BrowserAuthUnavailable as exc:
                    final_error = exc
                    break
                except Exception as exc:
                    final_error = exc
                    if attempt >= args.attempts:
                        break
                    delay_ms = args.retry_delay_ms * attempt
                    print(
                        f"[{index}/{len(places)}] retry={attempt + 1}/{args.attempts} "
                        f"after={delay_ms}ms error={exc}",
                        flush=True,
                    )
                    if args.browser_backend == "cdp":
                        if page is not None:
                            page.wait_for_timeout(delay_ms)
                    else:
                        agent_browser_wait(agent_browser_config, delay_ms)

            if final_error is None:
                synced_ids.add(place.id)
                save_synced_ids(args.list_name, synced_ids, args.sync_state)
                clear_failure(args.failure_log, place.id)
                if result == "saved":
                    saved += 1
                else:
                    already += 1
                elapsed = time.time() - started
                processed += 1
                print(
                    f"[{index}/{len(places)}] {result}; synced_count={len(synced_ids)} "
                    f"elapsed={elapsed:.1f}s",
                    flush=True,
                )
                continue

            if isinstance(final_error, BrowserAuthUnavailable):
                remaining_after_auth_block = len(places) - processed
                write_result(
                    args.result_json,
                    status="auth_blocked",
                    browser_backend=args.browser_backend,
                    target_list=args.list_name,
                    source=source_scope,
                    restaurant_ids=sorted(requested_restaurant_ids or []),
                    planned=len(places),
                    processed=processed,
                    saved=saved,
                    already=already,
                    failed_ids=[],
                    remaining=remaining_after_auth_block,
                    synced_count=len(synced_ids),
                    failure_log=args.failure_log,
                    auth_message=str(final_error),
                )
                print(
                    f"[{index}/{len(places)}] AUTH_BLOCKED {place.id}: {final_error}",
                    flush=True,
                )
                print(
                    f"status=auth_blocked saved={saved} already={already} "
                    f"remaining={remaining_after_auth_block} result={args.result_json}",
                    flush=True,
                )
                return 0

            if args.browser_backend == "cdp":
                screenshot_path = (
                    capture_failure_screenshot(page, place, args.failure_artifacts_dir)
                    if page is not None
                    else None
                )
            else:
                screenshot_path = capture_failure_screenshot_agent_browser(
                    agent_browser_config,
                    place,
                    args.failure_artifacts_dir,
                )
            record_failure(
                args.failure_log,
                place,
                final_error,
                attempts_used,
                screenshot_path,
            )
            failures.append(place.id)
            processed += 1
            print(
                f"[{index}/{len(places)}] ERROR {place.id} "
                f"attempts={attempts_used}: {final_error}",
                flush=True,
            )
            if isinstance(final_error, ListCapacityReached):
                capacity_reached = True
                break
    except KeyboardInterrupt:
        interrupted = True
        print(
            f"interrupted processed={processed} saved={saved} already={already} "
            f"failed={len(failures)}",
            flush=True,
        )
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if playwright is not None:
            try:
                playwright.stop()
            except Exception:
                pass

    remaining = max(0, len(places) - processed)
    if interrupted:
        status = "interrupted"
    elif capacity_reached:
        status = "capacity_reached"
    elif failures:
        status = "partial"
    else:
        status = "complete"
    result_payload = {
        "status": status,
        "browser_backend": args.browser_backend,
        "target_list": args.list_name,
        "source": source_scope,
        "restaurant_ids": sorted(requested_restaurant_ids or []),
        "planned": len(places),
        "processed": processed,
        "saved": saved,
        "already": already,
        "failed": len(failures),
        "failed_ids": failures,
        "remaining": remaining,
        "synced_count": len(synced_ids),
        "failure_log": str(args.failure_log),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json(args.result_json, result_payload)
    print(
        f"status={status} saved={saved} already={already} failed={len(failures)} "
        f"remaining={remaining} result={args.result_json}",
        flush=True,
    )
    if interrupted:
        return 130
    if failures or capacity_reached:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrupted before browser session started", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
