---
name: tastyroad-naver-map-sync
description: Sync Tastyroad's verified public restaurant records into a fixed Naver Map saved-place list through the user's logged-in Microsoft Edge session. Use when Codex needs to create or reuse the Tastyroad Naver Map list, add newly mapped restaurants, verify saved-list counts, avoid re-saving already synced restaurants, or operate the Naver Map saved-list workflow without repo-level scripts.
---

# Tastyroad Naver Map Sync

## Overview

Use this skill from the Tastyroad repo root to keep the private Naver Map saved list named `Tastyroad` aligned with public Tastyroad restaurants that have verified Naver place URLs.

This skill builds on `naver-map-lists`: use that skill first when Edge/CDP login, saved-list creation, or visual troubleshooting is needed.

## Required Context

Check these repo data files:

- `data/naver_map_list_target.json`: canonical list name and visibility.
- `data/naver_map_list_synced_ids.json`: restaurant IDs already confirmed in the Naver list.
- `data/tastyroad.sqlite`: public restaurant source data.

The repeatable runner is bundled at:

```bash
.codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py
```

## Workflow

1. Confirm Edge CDP is available and logged into Naver Map.

```bash
curl -s http://127.0.0.1:9222/json/version
agent-browser --cdp 9222 open https://map.naver.com
agent-browser --cdp 9222 wait 5000
agent-browser --cdp 9222 snapshot -i
```

Logged in means the snapshot shows `내 프로필 이미지 내정보 보기`.

Microsoft Edge 150+ may reject remote debugging against the default user data directory. If
`curl` cannot reach `9222` or Edge logs `DevTools remote debugging requires a non-default
data directory`, launch a CDP-only copied profile instead:

```bash
osascript -e 'tell application "Microsoft Edge" to quit'
rm -rf /tmp/tastyroad-edge-cdp-profile
mkdir -p /tmp/tastyroad-edge-cdp-profile
rsync -a --delete \
  --exclude='*/Cache/***' \
  --exclude='*/Code Cache/***' \
  --exclude='*/GPUCache/***' \
  --exclude='*/Service Worker/CacheStorage/***' \
  --exclude='*/Session Storage/***' \
  --exclude='Singleton*' \
  "$HOME/Library/Application Support/Microsoft Edge/" \
  /tmp/tastyroad-edge-cdp-profile/
open -na "Microsoft Edge" --args \
  --remote-debugging-port=9222 \
  --remote-debugging-address=127.0.0.1 \
  --user-data-dir=/tmp/tastyroad-edge-cdp-profile \
  --profile-directory=Default
```

Do not ask for Naver credentials in chat. If the copied profile is logged out, ask the user to
log in directly in the opened Edge window and re-check the login marker.

2. Open the saved-place panel and verify the target list.

```bash
agent-browser --cdp 9222 screenshot /private/tmp/tastyroad-naver-list.png
```

Verify `Tastyroad` appears with private visibility. If it does not exist, create it as a private list using `naver-map-lists`.

3. Run the bundled sync script.

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py
```

The runner uses one persistent Playwright CDP session instead of many single-command
`agent-browser` calls. It scopes every action to the `pcmap.place.naver.com` place frame
and the saved-list modal, and never uses screenshots or coordinates to control the UI.
It skips IDs in `data/naver_map_list_synced_ids.json`, so normal re-runs should be no-ops
unless new public restaurants were added.

Use chunking for large runs so Edge/Naver tab crashes do not poison a long batch:

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py --chunk-size 25
```

For a source-scoped sync, pass the exact `sources.name` value so unrelated
unsynced restaurants are not included:

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py \
  --source-name "식객 허영만의 백반기행" \
  --chunk-size 25
```

For a release-scoped sync, pass each verified restaurant ID from the release
report. The runner applies sync-state, exclude-state, and failure-log skips before
opening Edge, so a fully recorded release scope exits as a no-op:

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py \
  --restaurant-id=123 \
  --restaurant-id=456
```

When one saved list reaches Naver Map's 1,000-place limit, keep each list's
state separate and exclude IDs recorded for earlier lists:

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py \
  --list-name "Tastyroad 2" \
  --sync-state data/naver_map_list_synced_ids_2.json \
  --exclude-state data/naver_map_list_synced_ids.json \
  --source-name "식객 허영만의 백반기행" \
  --chunk-size 25
```

The runner reads the target list's Playwright checkbox state before clicking, verifies
the state again after saving, and records the restaurant ID only after persistence is
confirmed. It retries transient navigation and unstable-element failures three times by
default. It stops before the visible list count reaches the default 1,000-place limit.

Final failures are recorded in ignored `data/work/naver_map_sync_failures.json`, with a
diagnostic screenshot captured only after retries are exhausted. A later success removes
the stale failure entry. Use `--retry-failures` after resolving permanent failures or
refreshing Edge/CDP. The structured run summary is written to
`data/work/naver_map_sync_result.json`; partial runs exit with status 2.

4. Verify the final count in Naver Map and capture a screenshot when reporting completion.

## Safety Rules

- Do not recreate a repo-root Naver sync script.
- Do not toggle already-synced places. Naver's save modal uses toggles, so reprocessing a saved restaurant can remove it from the target list.
- Do not add screenshot-color or coordinate-click control paths. Screenshots are failure evidence only.
- Before a bulk run after Naver UI changes, verify that the place frame exposes `a[href="#bookmark"]` and the modal exposes `button.swt-save-group-info[role="checkbox"]`.
- Do not write directly to SQLite during map sync.
- If `agent-browser` loses the Naver tab, recreate a Naver tab with CDP:

```bash
curl -s -X PUT 'http://127.0.0.1:9222/json/new?https://map.naver.com'
agent-browser --cdp 9222 tab list
```

## Verification Commands

```bash
python3 -m py_compile .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py
python3 -m unittest discover -s .codex/skills/tastyroad-naver-map-sync/tests -p 'test_*.py'
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py --limit 0
```
