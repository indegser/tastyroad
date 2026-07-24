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
`agent-browser` calls. It skips IDs in `data/naver_map_list_synced_ids.json`, so normal
re-runs should be no-ops unless new public restaurants were added.

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

Default `--mode safe` verifies the `Tastyroad` checkbox before clicking, which avoids
toggling an already selected place off. It first tries selector/text/ARIA patterns for the
place save button, target list checkbox, and modal actions; when Naver does not expose the
modal reliably, it falls back to the verified screenshot/coordinate path.

If Naver screenshot capture hangs or the safe checker is too brittle, use `--mode blind`
only for IDs that are not already recorded as synced:

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py --mode blind --chunk-size 25
```

Failures are recorded in ignored `data/work/naver_map_sync_failures.json` and skipped on
subsequent runs. Use `--retry-failures` after refreshing Edge/CDP or changing mode.

4. Verify the final count in Naver Map and capture a screenshot when reporting completion.

## Safety Rules

- Do not recreate a repo-root Naver sync script.
- Do not toggle already-synced places. Naver's save modal uses toggles, so reprocessing a saved restaurant can remove it from the target list.
- Do not combine `--mode blind` with `--include-synced`; the script blocks this.
- Before a bulk run after Naver UI changes, manually verify that selector-first detection can see the target checkbox or that the current modal coordinates still match by screenshot. Current coordinate fallbacks assume a 1280x900 CSS-pixel desktop layout.
- Do not write directly to SQLite during map sync.
- If `agent-browser` loses the Naver tab, recreate a Naver tab with CDP:

```bash
curl -s -X PUT 'http://127.0.0.1:9222/json/new?https://map.naver.com'
agent-browser --cdp 9222 tab list
```

## Verification Commands

```bash
python3 -m py_compile .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py --limit 0
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py --mode blind --limit 0
```
