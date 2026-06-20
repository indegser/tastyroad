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

2. Open the saved-place panel and verify the target list.

```bash
agent-browser --cdp 9222 screenshot /private/tmp/tastyroad-naver-list.png
```

Verify `Tastyroad` appears with private visibility. If it does not exist, create it as a private list using `naver-map-lists`.

3. Run the bundled sync script.

```bash
python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py
```

The runner skips IDs in `data/naver_map_list_synced_ids.json`, so normal re-runs should be no-ops unless new public restaurants were added.

4. Verify the final count in Naver Map and capture a screenshot when reporting completion.

## Safety Rules

- Do not recreate a repo-root Naver sync script.
- Do not toggle already-synced places. Naver's save modal uses toggles, so reprocessing a saved restaurant can remove it from the target list.
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
```
