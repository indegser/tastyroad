---
name: tastyroad-naver-map-sync
description: Sync Tastyroad's verified public restaurant records into a fixed Naver Map saved-place list through a persistent Codex-controlled browser session. Use when Codex needs to create or reuse the Tastyroad Naver Map list, add newly mapped restaurants, verify saved-list counts, avoid re-saving already synced restaurants, or operate the Naver Map saved-list workflow without repo-level scripts.
---

# Tastyroad Naver Map Sync

## Overview

Use this skill from the Tastyroad repo root to keep the private Naver Map saved list named `Tastyroad` aligned with public Tastyroad restaurants that have verified Naver place URLs.

This skill builds on `naver-map-lists`: use that skill first when saved-list creation or visual troubleshooting is needed.

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

1. Confirm the persistent `agent-browser` session is logged into Naver Map.

```bash
agent-browser \
  --session tastyroad-naver-map-sync \
  --session-name tastyroad-naver-map-sync \
  --headed \
  open https://map.naver.com

agent-browser \
  --session tastyroad-naver-map-sync \
  --session-name tastyroad-naver-map-sync \
  snapshot -i
```

Logged in means the snapshot shows `내 프로필 이미지 내정보 보기`.
Do not ask for Naver credentials in chat. If the session is logged out, ask the user to
log in directly in the headed `agent-browser` window and re-check the login marker.

2. Open the saved-place panel and verify the target list.

```bash
agent-browser \
  --session tastyroad-naver-map-sync \
  --session-name tastyroad-naver-map-sync \
  screenshot /private/tmp/tastyroad-naver-list.png
```

Verify `Tastyroad` appears with private visibility. If it does not exist, create it as a private list using `naver-map-lists`.

3. Run the bundled sync script.

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py
```

The runner defaults to a persistent `agent-browser` session named
`tastyroad-naver-map-sync`, so it does not require a Chromium CDP port or a copied Edge
profile. It uses accessibility snapshots and element references, and never uses
screenshots or coordinates to control the UI.
It skips IDs in `data/naver_map_list_synced_ids.json`, so normal re-runs should be no-ops
unless new public restaurants were added.

Use `--browser-backend cdp` only as a fallback for legacy CDP troubleshooting:

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py \
  --browser-backend cdp \
  --cdp-port 9222
```

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
refreshing the browser login session. The structured run summary is written to
`data/work/naver_map_sync_result.json`; partial runs exit with status 2.

4. Verify the final count in Naver Map and capture a screenshot when reporting completion.

## Safety Rules

- Do not recreate a repo-root Naver sync script.
- Do not toggle already-synced places. Naver's save modal uses toggles, so reprocessing a saved restaurant can remove it from the target list.
- Do not add screenshot-color or coordinate-click control paths. Screenshots are failure evidence only.
- Before a bulk run after Naver UI changes, verify the `agent-browser` snapshot exposes an exact `저장` control and the target saved-list checkbox. For CDP fallback, verify that the place frame exposes `a[href="#bookmark"]` and the modal exposes `button.swt-save-group-info[role="checkbox"]`.
- Do not write directly to SQLite during map sync.
- If the `agent-browser` session loses the Naver tab, recreate a Naver tab:

```bash
agent-browser \
  --session tastyroad-naver-map-sync \
  --session-name tastyroad-naver-map-sync \
  open https://map.naver.com
```

## Verification Commands

```bash
python3 -m py_compile .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py
python3 -m unittest discover -s .codex/skills/tastyroad-naver-map-sync/tests -p 'test_*.py'
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py --limit 0
```
