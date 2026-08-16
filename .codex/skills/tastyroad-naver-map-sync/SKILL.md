---
name: tastyroad-naver-map-sync
description: Sync Tastyroad's verified public restaurant records into a fixed Naver Map saved-place list through the user's logged-in Edge browser extension session, with agent-browser and CDP fallback paths. Use when Codex needs to create or reuse the Tastyroad Naver Map list, add newly mapped restaurants, verify saved-list counts, avoid re-saving already synced restaurants, or operate the Naver Map saved-list workflow without repo-level scripts.
---

# Tastyroad Naver Map Sync

## Overview

Use this skill from the Tastyroad repo root to keep the private Naver Map saved lists
named `Tastyroad` and `Tastyroad 2` aligned with public Tastyroad restaurants that
have verified Naver place URLs.

Preferred control surface: use the Codex Edge browser extension connector against the
user's real Edge profile. The Edge extension path is the normal path for saved-list
writes because it reuses the user's Naver login state and avoids CDP profile-copy
login drift.

Fallback surfaces, in order:

1. The bundled `agent-browser` runner with persistent session `tastyroad-naver-map-sync`.
2. Legacy Playwright CDP only when the user explicitly asks for CDP troubleshooting.

Fallback is not an automatic write path. It must pass the runner's login preflight
first. If the result status is `auth_blocked`, do not retry place saves, do not create
failure rows for the restaurants, and ask the user to restore the Edge connector or log
in to the configured browser session.

This skill builds on `naver-map-lists`: use that skill first when saved-list creation
or visual troubleshooting is needed.

## Required Context

Check these repo data files:

- `data/naver_map_list_target.json`: canonical list name and visibility.
- `data/naver_map_list_synced_ids.json`: restaurant IDs already confirmed in the Naver list.
- `data/naver_map_list_synced_ids_2.json`: restaurant IDs already confirmed in the overflow
  `Tastyroad 2` list.
- `data/tastyroad.sqlite`: public restaurant source data.

The repeatable runner is bundled at:

```bash
.codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py
```

## Workflow

1. Prefer Edge extension connector and confirm Naver login.

When the Browser/Chrome skills are available, use `chrome:control-chrome` with the
explicit Edge selector. If Edge is not connected, diagnose the extension/native-host
state through that skill's troubleshooting guidance. Do not switch to CDP just because
Edge is logged out.

Open or claim an Edge tab at:

```text
https://map.naver.com
```

Logged in means the page snapshot shows `내 프로필 이미지 내정보 보기` and does not show
the user-link `로그인`.

If Edge is logged out, open:

```text
https://nid.naver.com/nidlogin.login
```

Ask the user to log in directly in Edge, then re-check the login marker before any
saved-list write.

2. Build the release-scoped work list from repository state.

For release-scoped sync, start from the report's `release_scope_restaurant_ids`.
Before touching Naver UI, exclude IDs already present in:

- `data/naver_map_list_synced_ids.json`
- `data/naver_map_list_synced_ids_2.json` when targeting `Tastyroad 2`
- the current failure log unless the user asked to retry failures

For `Tastyroad 2`, always keep the original-list exclude-state behavior:

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py \
  --limit 0 \
  --list-name "Tastyroad 2" \
  --sync-state data/naver_map_list_synced_ids_2.json \
  --exclude-state data/naver_map_list_synced_ids.json
```

Use SQLite or the bundled script's selection logic to identify only unsynced requested
IDs. Do not reprocess already-recorded IDs just to confirm them; Naver's save modal uses
toggles.

3. Save through Edge extension UI.

For each planned place:

- Navigate the Edge tab to the verified Naver place URL.
- Require the Naver login marker.
- Inspect the `pcmap.place.naver.com` iframe and require the expected restaurant name.
- Open the place save control.
- Locate the exact saved-list row for `Tastyroad 2` or the requested list. The row text
  contains `폴더명`, exact list name, `장소수`, and `선택됨`/`선택해제됨`.
- If the row is already `선택됨`, close the modal and record the restaurant as synced.
- If the row is `선택해제됨`, click only that row, click the modal save button, then
  verify either the page text says `저장 폴더 <list> 에 저장됨` or reopening the modal
  shows the target row as `선택됨`.
- After every confirmed save, update only the matching sync-state JSON.

Use these stable selectors when constructing Edge Playwright locators:

```text
iframe[src*="pcmap.place.naver.com"]
a[href="#bookmark"][role="button"][aria-pressed]
button.swt-save-group-info[role="checkbox"]
button.swt-save-btn
button.swt-close-btn
```

4. Write result artifacts and report.

For Edge extension runs, write an ignored result artifact under `data/work/` that mirrors
the script result shape:

```json
{
  "status": "complete",
  "browser_backend": "edge-extension",
  "target_list": "Tastyroad 2",
  "restaurant_ids": [],
  "planned": 0,
  "processed": 0,
  "saved": 0,
  "already": 0,
  "failed": 0,
  "failed_ids": [],
  "remaining": 0,
  "synced_count": 0
}
```

Capture screenshots only for final evidence or failure diagnosis. When final state
matters, verify the Naver modal row text, e.g. `폴더명 Tastyroad 2 장소수 667 선택됨`.

5. Fallback: use the bundled `agent-browser` runner only when Edge extension is unavailable.

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

Before a release-scoped fallback write, run the built-in preflight for the exact planned
IDs. This must happen before any save attempt:

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py \
  --preflight-only \
  --list-name "Tastyroad 2" \
  --sync-state data/naver_map_list_synced_ids_2.json \
  --exclude-state data/naver_map_list_synced_ids.json \
  --restaurant-id=123 \
  --result-json data/work/naver_map_sync_preflight.json
```

Continue to the write command only when the result JSON has
`"status": "preflight_ready"`. If it has `"status": "auth_blocked"`, no restaurant
was attempted and no sync-state should change; report the browser-login blocker and stop
the Naver sync step.

Open the saved-place panel and verify the target list.

```bash
agent-browser \
  --session tastyroad-naver-map-sync \
  --session-name tastyroad-naver-map-sync \
  screenshot /private/tmp/tastyroad-naver-list.png
```

Verify the requested list appears with private visibility. If it does not exist, create it
as a private list using `naver-map-lists`.

Run the bundled sync script.

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

Use chunking for large fallback runs so browser/Naver tab crashes do not poison a long batch:

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

For a fallback release-scoped sync, pass each verified restaurant ID from the release
report. The runner applies sync-state, exclude-state, and failure-log skips before
opening the browser session, so a fully recorded release scope exits as a no-op. The
runner also performs the same login preflight by default before the save loop; do not
use `--skip-login-preflight` except for manual UI debugging after an explicit user
request:

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
refreshing the browser login session. Login-preflight blockers are different: they write
`status: auth_blocked`, do not record restaurant failures, and exit before retries. The
structured run summary is written to `data/work/naver_map_sync_result.json`; partial
runs exit with status 2.

6. Verify the final count in Naver Map and capture a screenshot when reporting completion.

## Safety Rules

- Do not recreate a repo-root Naver sync script.
- Do not toggle already-synced places. Naver's save modal uses toggles, so reprocessing a saved restaurant can remove it from the target list.
- Do not add screenshot-color or coordinate-click control paths. Screenshots are failure evidence only.
- Before a bulk run after Naver UI changes, verify the Edge connector snapshot exposes an exact `저장` control and the target saved-list checkbox. For fallback script runs, verify the `agent-browser` snapshot exposes the same controls. For CDP fallback, verify that the place frame exposes `a[href="#bookmark"]` and the modal exposes `button.swt-save-group-info[role="checkbox"]`.
- Do not write directly to SQLite during map sync.
- Do not use CDP when the Edge extension connector is available but logged out; ask the user to log into Edge and resume.
- Do not let a recurring automation attempt fallback saves when preflight reports
  `auth_blocked`. Restore Edge connector/login first, then rerun only the unsynced IDs.
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
