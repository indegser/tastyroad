# Task Log

Use this file for active non-trivial work. Keep entries short and checkable.

## Current Task - 2026-08-19 - Regular source maintenance run (second daily check)

Worktree: `/Users/indegser/.codex/worktrees/a976/tastyroad`
Branch: detached automation checkout at `origin/main`
Starting `origin/main`: `c76e2e95607aeae3f4edf88e1be7de9b2429c9fd`
Preserved unrelated checkouts: ten dirty task worktrees were audited and left untouched; no changes were stashed, cleaned, switched, or overwritten.

- [x] Read automation memory, fetch origin, and synchronize the clean dedicated checkout to current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and repository runbook from the synchronized checkout.
- [x] Pass the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic maintenance runner and inspect the exact report/work queues.
- [x] Read and follow every owning skill required by mapping, transcript, or must-taste queues.
- [x] Recalculate the original release scope and verify all publishing gates.
- [x] If deploy-ready with tracked changes, repeat Supabase gate, build, release through `main`, and verify production API.
- [x] Run exact release-scope Naver Map sync after production verification, observing the hard authentication preflight.
- [x] Record final verification, release/sync outcome, and automation memory.

Result so far: Started from `origin/main` `c76e2e95607aeae3f4edf88e1be7de9b2429c9fd`. Live collection found 0 new video IDs, refreshed metadata for existing videos, and filled missing description/duration/tags for 백반기행 video `8vjUAuf31dQ`. The original work queue contained 25 historical must-taste pairs. Full transcript-grounded review and combined dry-run validation covered all 25; 14 pairs were applied sequentially with 18 menu items and 11 were recorded as insufficient evidence. Final scoped report `data/work/regular_source_automation/regular_source_automation_20260818T221644Z.json` is deploy-ready with 0 blockers, 25 non-blocking historical must-taste warnings, and an empty release scope.

Verification so far: Pre-maintenance and immediate pre-release Supabase checks found `supabase-aqua-engine` Available. SQLite integrity is `ok`; blank and nonnumeric Naver ID counts are both 0; exact post-apply verification found all 14 selected pairs and 18 expected menu items, with no rows for the 11 insufficient pairs. `git diff --check`, `pnpm install --frozen-lockfile`, and `pnpm run build` passed.

Release/sync review: Pushed production maintenance commit `88575348188e0392beab7b6dc04e3c13796a8e58`; GitHub-triggered deployment `https://tastyroad-au5kv15uw-jaekwon-hans-projects.vercel.app` reached `READY`. The production restaurants API returned HTTP 200 with an `items` array and exposed representative new menus for restaurants `458`, `461`, `1959`, and `2108`. Final `release_scope_restaurant_ids` was empty, so the Naver Map `Tastyroad 2` step completed as a zero-place no-op: planned/processed/saved/failed were all 0 and no browser or saved-list write was attempted. Result artifact: `data/work/naver_map_sync_result_20260819_second.json`.

## Current Task - 2026-08-19 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260819`
Branch: `codex/regular-source-maintenance-20260819`
Starting `origin/main`: `ec34ed9789c38c65f582483f2b9ddea2c39354e7`
Preserved unrelated checkouts: ten dirty task worktrees were audited and left untouched; no changes were stashed, cleaned, or overwritten.

- [x] Read automation memory, fetch origin, and create a clean dedicated worktree at current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and repository runbook from the synchronized checkout.
- [x] Pull the worktree environment safely and pass the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic maintenance runner and inspect the exact report/work queues.
- [x] Read and follow every owning skill required by mapping, transcript, or must-taste queues.
- [x] Recalculate the original release scope and verify all publishing gates.
- [x] If deploy-ready, repeat Supabase gate, build, release through `main`, and verify production API.
- [x] Attempt exact release-scope Naver Map sync after production verification; stop safely on authentication preflight failure.
- [x] Record final verification and release/sync outcome; update automation memory after the final published commit.

Result so far: Started from `origin/main` `ec34ed9789c38c65f582483f2b9ddea2c39354e7`. Live collection found 10 new video IDs and ingested all 10 transcript tracks. Mapping review verified seven video-place links covering eight release-scope restaurants (`1354`, `1416`, `2176`-`2181`); the two 최자로드 홍어 shorts remain non-blocking reviewed-uncertain warnings because no concrete venue could be verified. Nine restaurant-video must-taste reviews stored 14 transcript-grounded menu items. Final scoped report `data/work/regular_source_automation/regular_source_automation_20260818T151705Z.json` is deploy-ready with 0 blockers, 2 warnings, and empty transcript/must-taste queues. Pre-maintenance and pre-release Supabase checks found `supabase-aqua-engine` Available; SQLite integrity is `ok`; blank and nonnumeric Naver ID counts are 0; `git diff --check`, `pnpm install --frozen-lockfile`, and `pnpm run build` passed.

Release/sync review: Maintenance commit `373005a70ae76ed28473d5bc1f06277d4bf9b4a9` was pushed to `main`; Vercel production deployment `tastyroad-nnefld3eb-jaekwon-hans-projects.vercel.app` reached `READY`, and `https://taste.indegser.com/api/restaurants` returned HTTP 200 with an items array containing all eight release-scope restaurants. The Edge extension was installed and enabled but Edge was not running. The exact fallback preflight skipped already-synced `1354` and `1416`, then returned `auth_blocked` for planned IDs `2176`-`2181`; processed/saved/failed were all 0 and both sync-state files remained unchanged. Result artifact: `data/work/naver_map_sync_preflight_20260819.json`.

## Current Task - 2026-08-16 - Regular source maintenance preflight test

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-preflight-test-20260816`
Branch: `codex/regular-source-preflight-test-20260816`
Starting `origin/main`: `bd1be6e35aedd7b432bd6ad4bba36c7a9e664ba3`
Preserved unrelated checkouts: shared main and all existing task worktrees were left untouched.

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Verify Naver hardening commits `f8129bf` and `bd1be6e` are present.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, automation skill, repository runbook, and automation memory.
- [x] Pull the worktree environment and pass the pre-maintenance Supabase Marketplace gate.
- [x] Run non-dry deterministic source maintenance and inspect its report/work queues.
- [x] Use every owning skill required by mapping, transcript, or must-taste queues. (25 exact must-taste pairs; no mapping/transcript items.)
- [x] Recalculate the original release scope and verify publishing gates.
- [x] If deploy-ready, repeat Supabase gate, build, release through `main`, and verify production API.
- [x] Run Naver sync through Edge when available; otherwise require exact-ID fallback preflight before any write.
- [x] Record final verification, release, sync, or blocker notes.

Result so far: Live collection found 0 new video IDs but refreshed metadata for already-known videos. The original work queue contained 25 legacy must-taste pairs. Full transcript-grounded review and combined dry-run validation passed for all 25; 11 pairs were applied sequentially (19 menu items) and 14 were recorded as insufficient evidence. The recalculated report is `data/work/regular_source_automation/regular_source_automation_20260816T025710Z.json`, with `deploy_ready=true`, zero hard blockers, and non-blocking legacy must-taste warnings. Pre-maintenance and pre-release Supabase Marketplace checks both found `supabase-aqua-engine` Available. SQLite integrity is `ok`, verified blank Naver ID count is 0, `git diff --check` passed, and `pnpm run build` passed.

Release/sync note: Pushed production maintenance commit `b7d9ee7fdcdc7b992d0f619365388e754883217a`; Vercel deployment `https://tastyroad-fba8cny1m-jaekwon-hans-projects.vercel.app` reached `READY`. `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned HTTP 200 with an `items` array, restaurant `2175` remained live, and restaurant `2090` exposed the new `오리 혀구이` must-taste item. The exact-ID fallback Naver preflight for unsynced `2175`, `Tastyroad 2`, `data/naver_map_list_synced_ids_2.json`, and the original-list exclude state returned `status=auth_blocked`, `processed=0`, `saved=0`, `failed=0`, and no failure row. No write command or place-level retry was attempted. This is a no-write post-release operational blocker until the configured browser session is logged into Naver.

## Current Task - 2026-08-16 - Harden Naver sync preflight

Worktree: `/Users/indegser/Github/tastyroad-worktrees/naver-sync-hard-preflight`
Branch: `codex/naver-sync-hard-preflight`
Starting `origin/main`: `ccead1f18324f149c3a003e659a3a0c8cfd2a32d`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` was clean on `main` and behind `origin/main`; existing older worktrees were left untouched.

- [x] Read `AGENTS.md`, `tasks/lessons.md`, `$tastyroad-naver-map-sync`, and automation runbook.
- [x] Inspect current Naver sync runner and tests.
- [x] Add a login/connector preflight that exits before save attempts when the browser is not authenticated.
- [x] Update automation and Naver sync docs so fallback cannot be used as an automatic write path without preflight.
- [x] Verify syntax/tests/no-op behavior.
- [x] Commit and push the hardening change so the next scheduled run inherits it.
- [x] Record result notes.

Result note: Added a hard login preflight to `$tastyroad-naver-map-sync` fallback runner. For planned places, the runner now checks Naver login before any save loop; unauthenticated sessions write `status: auth_blocked`, `failed: 0`, `failed_ids: []`, and exit without per-place retries or failure-log rows. Added `--preflight-only` so the regular source automation can verify exact release-scope IDs before fallback writes, and updated `$tastyroad-regular-source-automation` plus `automation_prompt.md` to continue only when the result is `preflight_ready`. Added a durable lesson for this failure mode.

Verification note: `python3 -m py_compile .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py`, `python3 -m unittest discover -s .codex/skills/tastyroad-naver-map-sync/tests -p 'test_*.py'`, `git diff --check`, and a live fallback preflight for `2175` passed. The live preflight returned `status=auth_blocked` with `failed=0` and no `2175` failure-log row, proving logged-out fallback sessions no longer create daily restaurant-level sync failures.

## Current Task - 2026-08-16 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260816`
Branch: `codex/regular-source-maintenance-20260816`
Starting `origin/main`: `71f90c812846b21d65fac131c1680aac10856db2`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` was clean on `main`; existing older worktrees were left untouched.

- [x] Read automation memory and inspect repository/worktree state.
- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, automation skill, and repository automation prompt.
- [x] Pull worktree env from linked main checkout when safe.
- [x] Run pre-maintenance Supabase Marketplace gate.
- [x] Run non-dry deterministic source maintenance.
- [x] Inspect latest report and work queues.
- [x] Use owning skills for any mapping, transcript, or must-taste queues.
- [x] Recalculate scoped gates after review work when needed.
- [ ] If deploy-ready, repeat Supabase gate, build, release, verify production API, and sync Naver Map.
- [ ] Record final verification, release, sync, or blocker notes.

## Current Task - 2026-08-16 - Retry Naver sync login

Worktree: `/Users/indegser/Github/tastyroad-worktrees/naver-sync-login-retry`
Branch: `codex/naver-sync-login-retry`
Starting `origin/main`: `24e18a182a54b14277583bf9f0c0a60eff26d215`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` was clean on `main`; existing older worktrees were left untouched.

- [x] Read `AGENTS.md`, `tasks/lessons.md`, and `$tastyroad-naver-map-sync`.
- [x] Create a clean dedicated worktree from current `origin/main`.
- [x] Connect to the real Edge extension session and verify Naver login marker.
- [x] Retry unsynced `Tastyroad 2` IDs `2170`-`2174`.
- [x] Investigate login-retention mitigation for recurring syncs.
- [x] Record result, verification, and any follow-up rule.

Result note: Connected to the real Microsoft Edge extension session and verified Naver Map login via `내 프로필 이미지 내정보 보기` with no `로그인` link. Saved `2170` 은용골농장가든, `2171` 백년지기삼계탕평촌점, `2172` 서문통닭삼계탕, `2173` 농민백암순대 역삼직영점, and `2174` 원미막국수 to `Tastyroad 2`; the modal count moved from 684 to 689 and each row was re-opened as `선택됨`. Updated `data/naver_map_list_synced_ids_2.json` with `2170`-`2174` and wrote ignored result artifact `data/work/naver_map_sync_result_20260816_edge_extension.json`.

Login-retention note: Official Naver help points to cookie persistence as the main cause of repeated device/login prompts: private browsing cannot use login-state retention, repeated device registration can happen when cookies are deleted, and browser settings/cleaner tools that delete cookies on close reset saved browser state. A one-hour Naver Map heartbeat may help idle sessions, but it should run only against the real Edge profile after cookie retention is confirmed; it will not fix isolated `agent-browser`/CDP profiles or cookie deletion on browser close.

Verification note: Re-opened each saved place through the real Edge extension session and confirmed the `Tastyroad 2` row was `선택됨` after save; final modal count was 689. Verified with Naver sync script compile, Naver sync unit tests, synced-state JSON check for `2170`-`2174`, and `git diff --check`. Added a durable lesson for future login failures.

## Current Task - 2026-08-15 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260815`
Branch: `codex/regular-source-maintenance-20260815`
Starting `origin/main`: `15467c0dd4ea13b18eb07fe392d0042620f3f9c9`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` was clean on `main`; existing older worktrees were left untouched.

- [x] Read automation memory and inspect repository/worktree state.
- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, automation skill, and repository automation prompt.
- [x] Run pre-maintenance Supabase Marketplace gate and pull worktree env.
- [x] Run non-dry deterministic source maintenance.
- [x] Inspect latest report and work queues.
- [x] Use owning skills for any mapping, transcript, or must-taste queues.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase gate, build, release, verify production API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

Result note: Non-dry collection found 6 new videos: `GYLjHXuY3sk`, `MQUZqkpMKE8`, `QqH6q21AlsQ`, `09hE12SFKGE`, `_l9-6Gis-C4`, and `hkO4YGBZINY`. Web/transcript mapping review promoted 12 verified video-place links across 10 existing/new restaurants, while `09hE12SFKGE` remained a reviewed-uncertain no-safe-Naver-ID warning and `QqH6q21AlsQ` remained a reviewed-uncertain no-concrete-place warning. Transcript queue is empty. Must-taste dry-runs passed and stored 12 transcript-grounded items, one per mapped video/restaurant pair. Final scoped gate report `data/work/regular_source_automation/regular_source_automation_20260814T222039Z.json` is deploy-ready with 0 blockers and 2 non-blocking mapping warnings.
Verification so far: Supabase Marketplace `supabase-aqua-engine` was `Available` before maintenance and before release, SQLite `pragma integrity_check` returned `ok`, verified-mapping blank Naver ID count was `0`, `git diff --check` passed, `pnpm install --frozen-lockfile` completed, and `pnpm run build` passed.
Release/sync note: Pushed production data commit `38d0837`, verified Vercel deployment `tastyroad-8xds9f409-jaekwon-hans-projects.vercel.app` as `READY`, and confirmed `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returns HTTP 200 with an `items` array. Production search for `원미막국수` returned new restaurant `2174` with the `약밥닭` must-taste item. Naver Map sync to `Tastyroad 2` was a post-release operational warning: state/exclude checks skipped `1206`, `1442`, `1889`, `1941`, `1970`, `1982`, and `2017`; unsynced IDs `2170`, `2171`, `2172`, `2173`, and `2174` failed after three attempts each because the fallback browser session showed `Naver login marker missing`.

## Current Task - 2026-08-14 - Regular source maintenance latest

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260814-latest`
Branch: `codex/regular-source-maintenance-20260814-latest`
Starting `origin/main`: `38f1d327d6b44f79d1dffb753da970c1fde958de`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` was clean at `origin/main`; existing older worktrees were left untouched.

- [x] Read automation memory and synchronize to current `origin/main`.
- [x] Create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, automation runbook, and automation prompt.
- [x] Pull local env and run pre-maintenance Supabase Marketplace gate.
- [x] Run non-dry deterministic source maintenance.
- [x] Inspect latest report and work queues.
- [x] Use owning skills for any mapping, transcript, or must-taste queues.
- [x] Recalculate scoped gates if review work changes state.
- [x] If deploy-ready, build, release to production, verify API, and sync Naver Map.
- [x] Record review notes and update automation memory.

Result note: Added 또간집 EP.105/106, verified 6 restaurant mappings, and stored 6 transcript-grounded must-taste items. Scoped gate report `data/work/regular_source_automation/regular_source_automation_20260814T052514Z.json` is deploy-ready with 0 blockers and 0 warnings. Local checks so far: Supabase Marketplace Available, SQLite `pragma integrity_check` OK, `git diff --check`, and `pnpm run build`.
Release/sync note: Pushed production commit `f157b43`, verified Vercel deployment `tastyroad-jriex58zu-jaekwon-hans-projects.vercel.app` as Ready, and confirmed production API returns new restaurants with must-taste items. Synced 신규 IDs 2165-2169 to Naver Map `Tastyroad 2` through the Edge extension; list count moved from 667 to 672.

## Current Task - 2026-08-14 - Prefer Edge extension for Naver sync

Worktree: `/Users/indegser/Github/tastyroad-worktrees/naver-sync-edge-extension-runbook`
Branch: `codex/naver-sync-edge-extension-runbook`
Starting `origin/main`: `5d32be3052db878a8e2e41a810c4ee9b0e5354dd`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` is clean and already at `origin/main`; older worktrees were left untouched.

- [x] Read `AGENTS.md`, `tasks/lessons.md`, `$tastyroad-naver-map-sync`, automation runbook, and commit workflow.
- [x] Create a clean dedicated worktree from current `origin/main`.
- [x] Update Naver sync skill to prefer Edge browser extension connector.
- [x] Update UI notes and regular automation docs to match the new default.
- [x] Record a durable lesson for future Naver sync runs.
- [x] Verify docs and script syntax.
- [x] Commit, push, and fast-forward `main`.
- [x] Record review notes.

### Review

- Updated `$tastyroad-naver-map-sync` so future saved-list writes prefer the Codex Edge browser extension connected to the user's logged-in Microsoft Edge profile.
- Kept the bundled `agent-browser` runner as the first fallback and limited CDP to explicit legacy troubleshooting.
- Updated Naver UI notes, the regular source automation runbook, and the automation bootstrap prompt so scheduled runs inherit the Edge extension default after syncing to `origin/main`.
- Added a durable lesson to avoid reverting to CDP or copied profiles when Edge is merely logged out.
- Verified with `python3 -m py_compile .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py`, `python3 -m unittest discover -s .codex/skills/tastyroad-naver-map-sync/tests -p 'test_*.py'`, `python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py --limit 0 --result-json data/work/naver_map_sync_result_edge_runbook_limit0.json`, and `git diff --check`.

## Current Task - 2026-08-14 - Retry Naver sync with agent-browser

Worktree: `/Users/indegser/Github/tastyroad-worktrees/retry-naver-sync-agent-browser`
Branch: `codex/retry-naver-sync-agent-browser`
Starting `origin/main`: `1974781a4edb80eaeb99662b65695d1ad064ddb1`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` is clean and on `main`; older worktrees were left untouched.

- [x] Read `AGENTS.md`, `tasks/lessons.md`, `$tastyroad-naver-map-sync`, and `agent-browser`.
- [x] Create a clean dedicated worktree from current `origin/main`.
- [x] Confirm the Edge extension Naver session is logged in; Naver Map snapshot shows `내 프로필 이미지 내정보 보기`.
- [x] Retry recent failed `Tastyroad 2` sync IDs `2154`-`2164`.
- [x] Inspect result/failure logs and sync-state changes.
- [x] Commit/push tracked sync-state changes if new saves are confirmed.
- [x] Record review notes.

### Review

- Attempted to verify login in the new default `agent-browser` session `tastyroad-naver-map-sync`; snapshot showed `link "로그인"` and no `내 프로필 이미지 내정보 보기`.
- Also checked `agent-browser --auto-connect` and Codex in-app Browser; both were logged out from Naver Map.
- Opened the persistent `agent-browser` session headed at `https://nid.naver.com/nidlogin.login`; retry is blocked until the user logs in there.
- 2026-08-14T04:28:25Z: Rechecked without CDP. The `agent-browser` session still showed `link "로그인"`. Codex in-app Browser also showed `link "로그인"` and no profile marker, so opened the visible Codex in-app Browser at `https://nid.naver.com/nidlogin.login` for user login.
- 2026-08-14T04:32:13Z: User chose Edge extension path. Connected to Edge via Codex browser extension successfully, verified Edge Naver Map still shows `link "로그인"` and no `내 프로필 이미지 내정보 보기`, found no other logged-in Edge Naver tabs, and opened Edge at `https://nid.naver.com/nidlogin.login` for user login. No sync write attempted.
- 2026-08-14T04:40:32Z: After user logged into Edge, retried IDs `2154`-`2164` through the Edge extension path. `2154` was already selected; `2155`-`2164` saved successfully. Final Naver modal verification showed `폴더명 Tastyroad 2 장소수 667 선택됨`.
- Updated `data/naver_map_list_synced_ids_2.json` from 656 to 667 IDs and wrote ignored result/screenshot artifacts under `data/work/`.

## Current Task - 2026-08-14 - Naver sync agent-browser backend

Worktree: `/Users/indegser/Github/tastyroad-worktrees/naver-sync-agent-browser`
Branch: `codex/naver-sync-agent-browser`
Starting `origin/main`: `de11759ffa4e360e6ceb2d5478edd1486d9247c4`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` is clean but behind `origin/main`; older automation worktrees were left untouched.

- [x] Read `AGENTS.md`, `tasks/lessons.md`, Browser skill, and `$tastyroad-naver-map-sync`.
- [x] Create a clean dedicated worktree from current `origin/main`.
- [x] Inspect existing sync script and tests.
- [x] Add an `agent-browser` sync backend that does not require CDP.
- [x] Update skill docs/run examples to make the new backend the default.
- [x] Verify parser/unit behavior and Python syntax.
- [x] Record review notes.

### Review

- Changed `.codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py` so the default `--browser-backend` is `agent-browser`, using persistent session `tastyroad-naver-map-sync`; legacy Playwright CDP remains available via `--browser-backend cdp --cdp-port 9222`.
- Added accessibility-snapshot parsing for exact saved-list checkbox detection, including visibility prefixes such as `비공개`, and kept sync-state/failure-log protection unchanged.
- Updated `$tastyroad-naver-map-sync`, its UI notes, and `$tastyroad-regular-source-automation` wording so the recurring workflow no longer directs agents to Edge/CDP by default.
- Verified with `python3 -m py_compile`, `python3 -m unittest discover -s .codex/skills/tastyroad-naver-map-sync/tests -p 'test_*.py'`, `python3 .codex/skills/tastyroad-naver-map-sync/scripts/sync_naver_map_list.py --limit 0 --result-json data/work/naver_map_sync_result_agent_browser_limit0.json`, and `git diff --check`.

## Current Task - 2026-08-14 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260814`
Branch: `codex/regular-source-maintenance-20260814`
Starting `origin/main`: `5cbac2da28aca1f0dfd132920609478044f475f5`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Pull worktree env from the linked main checkout when safe.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `5cbac2da28aca1f0dfd132920609478044f475f5` in a fresh worktree; preserved unrelated dirty state in `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 6 new videos: `nAwNndsdMHI`, `4GB8IKBMjfk`, `4yE5QUtxEWQ`, `JPCqnlxtqRs`, `MewsT49A2vE`, and `Wx0ZFhrxa2I`.
- Web-search mapping review promoted 6 Baekban links: existing `삼정면옥` (`1344`) for 냉면/수육 clips, existing `아미각` (`1343`), and new `올뱅이식당` (`2162`), `들림횟집` (`2163`), and `수영식당` (`2164`).
- Recorded one non-blocking no-safe-place mapping warning for ChoiJaRoad short `nAwNndsdMHI`; search results and transcript did not identify a concrete restaurant/place.
- Transcript retry stored Supabase Storage captions for `4yE5QUtxEWQ` after the initial runner hit a 429; transcript queue is empty.
- Must-taste dry-runs passed and stored 7 items across 6 mapped video/restaurant pairs: `평양냉면`, `돼지고기 수육`, `올갱이 전골`, `올갱이 해장국`, `돼지 두루치기`, `송어회`, and `송어 매운탕`.
- Final scoped gate report `regular_source_automation_20260813T221119Z.json` had `deploy_ready=true`, zero blockers, and one non-blocking mapping warning.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm install --frozen-lockfile`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `0b927301d79d6aa56331a99f075bcbbdbec46a3f` deployed at `https://tastyroad-pe7tsn0ib-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`; production API first returned restaurant `2164`.
- Naver Map sync for `Tastyroad 2` was a post-release operational warning: `1343` and `1344` were skipped before planning, while `2162`, `2163`, and `2164` failed after three retries each because Edge CDP showed `Naver login marker missing`.

## Current Task - 2026-08-13 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260812`
Branch: `codex/regular-source-maintenance-20260812`
Starting `origin/main`: `da9522337d03ea6047514a17b881ccf81c2f350d`
Preserved unrelated checkout: shared main checkout `/Users/indegser/Github/tastyroad` is clean but behind `origin/main` and was left untouched.

- [x] Fetch origin and confirm a clean dedicated worktree at current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt from the updated checkout.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read `data/work/regular_source_automation/latest.json` and work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `da9522337d03ea6047514a17b881ccf81c2f350d`; shared main checkout was clean but behind and was left untouched.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 7 new videos: `P8n0JZlrKjU`, `CMG-LKsjka8`, `R0FO8FRk1e4`, `SPX29_gJucA`, `ZTJctBAGrlg`, `eZzoCXPL7sI`, and `nUcH48fi3rA`.
- Web-search mapping review promoted 6 video-place links: existing `마당집추어탕` (`1426`) plus new `명랑식당` (`2159`), `오리고기의 신세계 포뜰오리` (`2160`), and `걸구쟁이네` (`2161`).
- Recorded one non-blocking no-restaurant mapping warning for `P8n0JZlrKjU`; transcript is a Sapporo convenience-store/hotel-room tasting, not a restaurant visit.
- Transcript ingest stored Supabase Storage captions for all 7 release-scope videos.
- Must-taste dry-runs passed and stored 10 items: `소고기 특수부위`, `오리 가슴살과 다리살`, `참새맛살`, `오리 껍데기`, `추어튀김`, `추어탕`, `빙떡`, `곤드레나물`, `두부장아찌`, and `무밥`.
- Final scoped gate report `regular_source_automation_20260812T221316Z.json` had `deploy_ready=true`, zero blockers, and one non-blocking mapping warning.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `c44393fa69ad791ab67006011ea8e1df48fc1c75` deployed at `https://tastyroad-bx6dd2hpt-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`.
- Naver Map sync for `Tastyroad 2` was a post-release operational warning: `1426` was skipped by state, while `2159`, `2160`, and `2161` failed after three retries each because Edge CDP showed Naver `로그인` and no profile marker.

## Current Task - 2026-08-12 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260812`
Branch: `codex/regular-source-maintenance-20260812`
Starting `origin/main`: `0c52e60a053981b24bad19b868c07ee295ca40a4`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Pull worktree env from the linked main checkout when safe.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `0c52e60a053981b24bad19b868c07ee295ca40a4` in a fresh worktree; preserved unrelated state in `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 5 new videos: `hG2MQdzD9Z0` from `최자로드`, plus `2y__6oKjGis`, `n3SN4NtMEUQ`, `alr9gEsgQNQ`, and `hZsoTvJ3B00` from `식객 허영만의 백반기행`.
- Web-search mapping review promoted 4 Baekban mappings: new `하누&카누 횡성점` (`2158`), existing `이모네 칼국수` (`1836`), existing `까무하우스` (`1837`), and existing `삼정` (`1838`).
- Recorded a non-blocking no-safe-match mapping warning for `hG2MQdzD9Z0`; exact-title/source searches, metadata, and transcript retry did not provide a concrete restaurant name/address/place.
- Transcript ingest stored Supabase Storage captions for the 4 mapped Baekban videos; `hG2MQdzD9Z0` transcript fetch hit Google/YouTube 429 and remained outside release scope.
- Must-taste dry-runs passed and stored 9 items: `한우빵`, `장칼국수`, `겉절이`, `밥 말기`, `더덕구이`, `곤드레비빔밥`, `샤토브리앙`, `토시살`, and `알등심`.
- Final scoped gate report `regular_source_automation_20260811T221606Z.json` had `deploy_ready=true`, zero blockers, and one non-blocking mapping warning.
- Verification before commit passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm install --frozen-lockfile`, and `pnpm run build`.
- Production data commit `3e8871b96a1f5ce7de4f7de867e2667614211b9f` deployed at `https://tastyroad-dd7fs9kqk-jaekwon-hans-projects.vercel.app`; production API `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned HTTP 200 with an `items` array.
- Naver Map sync for `Tastyroad 2` was a post-release operational warning: `1836` and `1838` were already recorded in list 2, `1837` was covered by the original-list exclude state, and new restaurant `2158` failed after three retries because the Edge CDP session showed Naver `로그인` and no profile marker.

## Current Task - 2026-08-11 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260811`
Branch: `codex/regular-source-maintenance-20260811`
Starting `origin/main`: `f9058161273f339c7fc010e46348cbac220c09f8`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Pull worktree env from the linked main checkout when safe.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `f9058161273f339c7fc010e46348cbac220c09f8` in a fresh worktree; preserved unrelated state in `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 10 new videos: `iOB0R7YMQ4o`, `5FRg8kdUsd8`, `Fr--n68WaZ8`, `FrIqc4vawO8`, `SMQ9drW3T90`, `_y4zQm2bOpM`, `d_GfGWRyJYM`, `nqfil2mhMCI`, `qU_czrCHD-Q`, and `r3KhubDAmY4`.
- Web-search mapping review promoted 8 Baekban mappings: `풍미당` (`2154`), `옥천장금이맛집` (`2155`), `강가가든` (`2156`), existing `바다횟집` (`1684`), existing `장수칼국수` (`1685`), and `남도호해물포차` (`2157`).
- Recorded non-blocking no-safe-match mapping warnings for `iOB0R7YMQ4o` and `5FRg8kdUsd8`; searches did not produce a concrete restaurant name/address/place match.
- Transcript ingest stored Supabase Storage captions for the 8 mapped Baekban videos; transcript fetch for the 2 unmapped Shorts hit Google/YouTube 429 and remained irrelevant to release scope.
- Must-taste dry-runs passed and stored 13 items: `비빔쫄면`, `김밥`, `물쫄면`, `삼백초참옻닭`, `찹쌀죽`, `도리뱅뱅`, `민물매운탕`, `가자미회`, `가자미회비빔`, `곰치국`, `칼국수`, `남도호세트`, and `숙성회`.
- Final scoped gate report `regular_source_automation_20260810T221539Z.json` had `deploy_ready=true`, zero blockers, and two non-blocking mapping warnings.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm install --frozen-lockfile`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `490558b24ff72327f36921fa4eb5b88dab6561c7` deployed at `https://tastyroad-5ehwxe443-jaekwon-hans-projects.vercel.app`; production API first returned restaurant `2157`.
- Naver Map sync for `Tastyroad 2` was a post-release operational warning: `1684` and `1685` were already recorded, but `2154`, `2155`, `2156`, and `2157` failed after three retries each because the copied Edge CDP profile showed the Naver `로그인` link and no login marker.

## Current Task - 2026-08-10 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260810`
Branch: `codex/regular-source-maintenance-20260810`
Starting `origin/main`: `9d3ec93960fdb66a8ce8a9070dc33011714f5c65`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Pull worktree env from the linked main checkout when safe.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `9d3ec93960fdb66a8ce8a9070dc33011714f5c65` in a fresh worktree; preserved unrelated state in `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 2 new videos: `dmluoNbxMVs` from `최자로드` and `dIqoDXoBCiA` from `식객 허영만의 백반기행`.
- Web-search mapping review linked `dmluoNbxMVs` to existing `함경도찹쌀순대` (`1280`, Naver `21037816`) and `dIqoDXoBCiA` to existing `화산숯불` (`1527`, Naver `12787545`).
- Transcript ingest stored Supabase Storage captions for both release-scope videos.
- Must-taste dry-runs passed and stored 6 items: `순대국밥`, `찹쌀순대`, `머리고기`, `갈비살 소금구이`, `양념 소갈비`, and `육회`.
- Final scoped gate report `regular_source_automation_20260809T221428Z.json` had `deploy_ready=true`, zero blockers, zero warnings, and empty work queues.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm install --frozen-lockfile`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `a2c8aa9bb10d0908a876b654e48441091ce85a05` deployed at `https://tastyroad-70mwvz4ob-jaekwon-hans-projects.vercel.app`; production API first returned restaurant `1280`.
- Naver Map sync for `Tastyroad 2` completed as a state-based no-op with `planned=0`, `saved=0`, `failed=0`, `remaining=0`; `1280` is covered by the original-list exclude state and `1527` is already recorded in `data/naver_map_list_synced_ids_2.json`.

## Current Task - 2026-08-09 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260809`
Branch: `codex/regular-source-maintenance-20260809`
Starting `origin/main`: `27eaeee70539245c5a36ec3a87edbf9b9d2982cb`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `27eaeee70539245c5a36ec3a87edbf9b9d2982cb` in a fresh worktree; preserved unrelated state in `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found no new videos; release scope was empty (`release_scope_video_ids=[]`, `release_scope_restaurant_ids=[]`).
- Refreshed existing source metadata/raw snapshots and `data/tastyroad.sqlite`; final report `regular_source_automation_20260808T220427Z.json` had `deploy_ready=true`, zero blockers, and 25 historical must-taste backlog warnings.
- No mapping or transcript queues were present. The must-taste queue was read through `$tastyroad-transcript-must-taste`; because it was global backlog with no release scope, it remained follow-up triage rather than a publishing blocker.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm install --frozen-lockfile`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production metadata refresh commit `9af9de732dbb178f3d0059e43b4802d0b2f489d8` deployed at `https://tastyroad-g5pwjrqa6-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`.
- Naver Map sync was skipped because the release scope contained no restaurant IDs.

## Current Task - 2026-08-08 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260808`
Branch: `codex/regular-source-maintenance-20260808`
Starting `origin/main`: `9cdd290ed472bb7e5fc00bd743c4807d88d88cd4`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Pull worktree env from the linked main checkout when safe.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `9cdd290ed472bb7e5fc00bd743c4807d88d88cd4` in a fresh worktree; preserved unrelated state in `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 17 new videos across `성시경의 먹을텐데`, `김사원세끼`, `홍석천이원일`, `최자로드`, `전현무계획`, and `식객 허영만의 백반기행`.
- Mapping review promoted 10 release-scope restaurants: existing `삼릉고향손칼국수` (`1526`) and `이천식당` (`1640`), plus new `스시화` (`2146`), `당케올레국수` (`2147`), `혼차롱식개집` (`2148`), `한라산아래첫마을 영농조합법인` (`2149`), `돈지식당` (`2150`), `부평막국수` (`2151`), `오향가` (`2152`), and `무쉬` (`2153`).
- Recorded non-blocking no-safe-match mapping warnings for 5 metadata-poor ChoiJaRoad clips: `FE4U7P4fVxs`, `iiEay5X54AA`, `eSPhEZInrf8`, `Z_wFGX0zD34`, and `gofQ5e1hHPk`.
- Transcript retry stored captions for `6-Po2FRHULk`, `wkSchiyC1vg`, and `k5t0yY9VhHU`; transcript queue is empty.
- Must-taste dry-runs passed and stored 24 items across the 12 release-scope video/restaurant pairs.
- Final scoped gate report `regular_source_automation_20260808T150529Z.json` had `deploy_ready=true`, zero blockers, and five non-blocking mapping warnings.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `91b58ec19aea97b24eeb4a6aceabbf6b5366564f` deployed at `https://tastyroad-huzyeydip-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`; production API first returned restaurant `1526`.
- Naver Map sync for `Tastyroad 2` completed with `saved=2`, `already=6`, `failed=0`, `remaining=0`, and synced count `656`; release restaurants `2146` through `2153` are recorded in `data/naver_map_list_synced_ids_2.json`.

## Current Task - 2026-08-02 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260802`
Branch: `codex/regular-source-maintenance-20260802`
Starting `origin/main`: `37566f99ab030256c76705a64407ac57eba7ec40`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Pull worktree env from the linked main checkout when safe.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `37566f99ab030256c76705a64407ac57eba7ec40` in a fresh worktree; the shared main checkout was clean but behind, and the older automation worktree had unrelated local state.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 2 new videos from `식객 허영만의 백반기행`: `KJngNRGMAZY` and `VEQ3p_wfDv8`.
- Web-search mapping review linked `KJngNRGMAZY` to existing `조박사토종순대국` (`927`, Naver `13157155`) and `VEQ3p_wfDv8` to existing `신천생태찌개` (`1608`, Naver `1683030629`).
- Transcript ingest stored Supabase Storage captions for both release-scope videos.
- Must-taste dry-runs passed and stored 4 items: `순대국`, `생태찌개`, `대구전`, and `냄비밥`.
- Final scoped gate report `regular_source_automation_20260801T221209Z.json` had `deploy_ready=true`, zero blockers, and zero warnings.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm run build`, Vercel production `Ready`, and production API HTTP 200 with an `items` array.
- Production data commit `9256c0080584fefc93065a7ca287078edd12c5ed` deployed at `https://tastyroad-1faoe3d1b-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`; production API first returned restaurant `927`.
- Naver Map sync for `Tastyroad 2` completed as a no-op with `planned=0`, `saved=0`, `failed=0`, `remaining=0`; `927` was already in the original-list exclude state and `1608` was already in the `Tastyroad 2` state.

## Current Task - 2026-08-01 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260801`
Branch: `codex/regular-source-maintenance-20260801`
Starting `origin/main`: `8e16f0ec5ec295b3faeae0cd79e1ca29fff40179`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `8e16f0ec5ec295b3faeae0cd79e1ca29fff40179` in a fresh worktree because `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` had unrelated local state.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 7 new videos: `JT_90k23UMU`, `BqBHWiw7nl4`, `BAt6_9dQjQM`, `QVIlBz4agtc`, `8FtDYze3oUg`, `34W3xZANOoI`, and `btaRTZeiYqg`.
- Mapping review promoted 5 release-scope restaurants: new `홍복` (`2142`), new `송돝` (`2143`), existing `명화식당` (`1664`), existing `바다식당` (`1665`), and corrected new `만복분식` (`2145`).
- Removed the initially promoted wrong `경남횟집` mapping for `8FtDYze3oUg` after transcript review showed the clip is the 인천 분식 segment, then promoted `만복분식` instead.
- Recorded non-blocking no-safe-match mapping warnings for `BAt6_9dQjQM` and `QVIlBz4agtc`; `QVIlBz4agtc` points to a Tokyo place outside the current Korean Naver publish scope.
- Transcript retry stored captions for `JT_90k23UMU`, `8FtDYze3oUg`, `34W3xZANOoI`, and `btaRTZeiYqg`; `BqBHWiw7nl4` remained a concrete Google/YouTube 429 transcript warning.
- Must-taste dry-runs passed and stored 11 items: `양장피`, `군만두`, `마파두부`, `군만두`, `쫄면`, `돈가스`, `굴떡국`, `굴전`, `생굴`, `멍게젓갈`, and `갓 지은 밥`.
- Final scoped gate report `regular_source_automation_20260731T222246Z.json` had `deploy_ready=true`, zero blockers, and three non-blocking warnings.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `c16752d410f7a86f7968dad0fa17009aab10e5a0` deployed at `https://tastyroad-7t87b0mcq-jaekwon-hans-projects.vercel.app`; production API first returned restaurant `2145`.
- Naver Map sync for `Tastyroad 2` completed with `saved=0`, `already=3`, `failed=0`, `remaining=0`, and synced count `648`; release restaurants `2142`, `2143`, and `2145` are recorded in `data/naver_map_list_synced_ids_2.json`.

## Current Task - 2026-07-31 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260731`
Branch: `codex/regular-source-maintenance-20260731`
Starting `origin/main`: `b1300ccb44c781e7d536a349a6a66918a37d3da4`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `b1300ccb44c781e7d536a349a6a66918a37d3da4` in a fresh worktree because `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` had unrelated local state.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 5 new videos: `tpJB840wYP4`, `JRcUOiWBgnQ`, `LAQ1-XChfwc`, `UNO80SjwS7k`, and `ZxTn-3o4EoY`.
- Web-search mapping review verified `양지바위횟집` (`1606`) for `LAQ1-XChfwc`/`JRcUOiWBgnQ`, new `강화가든` (`2140`) for `ZxTn-3o4EoY`/`UNO80SjwS7k`, and new `용무있습니까 상암점` (`2141`) for `tpJB840wYP4`.
- Transcript retry stored captions for `JRcUOiWBgnQ` and `UNO80SjwS7k`; all release-scope videos now have preferred transcripts.
- Must-taste dry-runs passed and stored 8 items: `대구 연잎찜`, `생대구탕`, `대구알젓갈`, `모자반 굴 반찬`, `한우 등심`, `막장찌개`, `한우 등심`, and `쌈채소와 호박잎쌈`.
- `tpJB840wYP4` was validator-confirmed insufficient evidence for must-taste because the transcript discusses origin/background without tasting or ordering evidence.
- Final scoped gate report `regular_source_automation_20260730T221412Z.json` had `deploy_ready=true`, zero blockers, and one non-blocking must-taste warning.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `55b5c5903173eb3ddd3b1e51db9a522a08224948` deployed at `https://tastyroad-kv58kk490-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`.
- Naver Map sync for `Tastyroad 2` completed with `saved=1`, `already=1`, `failed=0`, `remaining=0`, and synced count `645`; release restaurants `1606`, `2140`, and `2141` are recorded in `data/naver_map_list_synced_ids_2.json`.

## Current Task - 2026-07-30 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260730`
Branch: `codex/regular-source-maintenance-20260730`
Starting `origin/main`: `c424d88b512c995aad838e50ba11cc7dd9556818`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `c424d88b512c995aad838e50ba11cc7dd9556818` in a fresh worktree because `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` had unrelated local state.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 6 new videos: `JytO5EGNTAg`, `L9Pgo7k71y0`, `HOgM9-3nTpQ`, `bY1dyJsIMqQ`, `kfY8YqhasWs`, and `SFjAqjwq2mY`.
- Web-search mapping review promoted three restaurant mappings: `진이네떡볶이` (`1927`), `경기돌섬횟집` (`1447`), and new `딸부자막국수` (`2139`).
- Mapping warnings remain for `L9Pgo7k71y0`, `SFjAqjwq2mY`, and `kfY8YqhasWs` after concrete review found no safe numeric Naver place match.
- Transcript retry stored captions for `HOgM9-3nTpQ` and `JytO5EGNTAg`; `bY1dyJsIMqQ` remained a concrete YouTube 429 transcript warning.
- Must-taste dry-runs passed and stored 4 items: `떡볶이`, `물회`, `감자떡`, and `방건조 열기`.
- Final scoped gate report `regular_source_automation_20260729T221627Z.json` had `deploy_ready=true`, zero blockers, and four non-blocking warnings.
- Verification so far: SQLite integrity `ok`, blank public Naver ID count `0`, no failed non-transcript commands, `git diff --check`, and `pnpm run build` passed.
- Production data commit `f88a23bf79aa1615bedf1a9e0a38b33ea73d2642` deployed at `https://tastyroad-f1kei2bfp-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`; production API returned HTTP 200 with an `items` array.
- Naver Map sync for `Tastyroad 2` completed with `saved=1`, `failed=0`, `remaining=0`, and synced count `643`; release restaurants `1447`, `1927`, and `2139` are recorded in `data/naver_map_list_synced_ids_2.json`.

## Current Task - 2026-07-29 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260729`
Branch: `codex/regular-source-maintenance-20260729`
Starting `origin/main`: `a6d2dd12ab63993726ed52effeb0307d2107dc5e`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `a6d2dd12ab63993726ed52effeb0307d2107dc5e` in a fresh worktree because `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` had unrelated local state.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 4 new videos: `d3wjoCC2TCM`, `9zE0r8zga5A`, `KAOE_jCSXO8`, and `fhMpyrTDROE`.
- Mapping review verified 6 release-scope restaurants: `장안곱창` (`2134`), `만원의 행복` (`2135`), `두꺼비식당` (`2136`), `우리소가든` (`2137`), `연화37` (`2138`), and existing `신촌고기창고` (`1558`).
- Transcript retry stored captions for `d3wjoCC2TCM`, `9zE0r8zga5A`, and `fhMpyrTDROE`; `KAOE_jCSXO8` remained a concrete YouTube 429 transcript warning after retry.
- Must-taste dry-runs passed and stored 7 items: `수구레전골`, `두부조림`, `수구레무침`, `생맥주`, `크림치즈 프레즐`, `왕노가리`, and `뼈삼겹살`.
- The 3 `9zE0r8zga5A` restaurant pairs were validator-confirmed insufficient evidence because the Shorts names places but has no ordering or tasting segments.
- Final scoped gate report `regular_source_automation_20260728T221912Z.json` had `deploy_ready=true`, zero blockers, and four non-blocking warnings.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `f413f0e4029d81bbb52d6f8574830ca182a53c3f` deployed at `https://tastyroad-2yr91y5bj-jaekwon-hans-projects.vercel.app`; Naver sync state commit `c3cce04f10722eb7b61b712887876a0c1cb404ee` deployed at `https://tastyroad-bb01todb1-jaekwon-hans-projects.vercel.app`.
- Naver Map sync for `Tastyroad 2` completed with `saved=1`, `already=4`, `failed=0`, `remaining=0`, and synced count `642`; `1558` was already covered by the original list exclude state.

## Current Task - 2026-07-28 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260728`
Branch: `codex/regular-source-maintenance-20260728`
Starting `origin/main`: `51fa9881b8aa9b6160a217749d65bc5dd9442dda`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping, transcript, or must-taste queues if present.
- [x] Recalculate scoped gates after review work when needed.
- [x] If deploy-ready, repeat Supabase preflight, build, release to production, verify API, and sync Naver Map.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `51fa9881b8aa9b6160a217749d65bc5dd9442dda` in a fresh worktree because `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` had unrelated local state.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 5 new videos: `Y2KQPixDCtI`, `U0on9EkI6BU`, `kyB2W5RL1NE`, `XZeGC2dMqUk`, and `7an2KlTEPko`.
- Web-search mapping review promoted four Baekban clips to existing verified restaurants: `이로운밥상` (`1557`) and `아저씨네낙지찜` (`744`); `Y2KQPixDCtI` was recorded as reviewed non-restaurant/no safe place match.
- Transcript retry stored Korean Supabase Storage captions for `U0on9EkI6BU`, `kyB2W5RL1NE`, and `7an2KlTEPko`; `XZeGC2dMqUk` remained a concrete 429 transcript warning.
- Must-taste validation dry-runs passed and stored six items: `연근 유자무침`, `부추전`, `표고버섯 엿장조림`, `연잎밥`, `낙지찜`, and `볶음밥`.
- Final scoped gate report `regular_source_automation_20260727T221700Z.json` had `deploy_ready=true`, zero blockers, and one non-blocking transcript warning.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with an `items` array.
- Production data commit `d41c5ee4d9bba9523c2999880626c8bc6d9b2c61` deployed at `https://tastyroad-65h7e5o4f-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`.
- Naver Map sync for `Tastyroad 2` planned zero writes because release restaurants `744` and `1557` were already covered by existing sync/exclude state.

## Current Task - 2026-07-27 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260727`
Branch: `codex/regular-source-maintenance-20260727`
Starting `origin/main`: `83961943ba3a3e8f2f192600c34f42105e78733e`
Preserved unrelated checkout: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` (`tasks/todo.md` modified, branch ahead 24)

- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, the automation skill, and the repository automation prompt.
- [x] Run the pre-maintenance Supabase Marketplace gate.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read the latest report and any work queues.
- [x] Use owning skills for mapping review and two verified Baekban restaurant mappings.
- [x] Recalculate scoped gates after review work when needed.
- [x] Run release validation checks: SQLite integrity, blank Naver ID check, `git diff --check`, Supabase preflight, and `pnpm run build`.
- [x] Release to production, verify API, and sync Naver Map if deploy-ready.
- [x] Record final verification, release, sync, or blocker notes.

### Review

- Started from `origin/main` `83961943ba3a3e8f2f192600c34f42105e78733e` in a fresh worktree because `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation` had unrelated local state.
- Pre-maintenance and pre-release Supabase Marketplace checks both passed: `supabase-aqua-engine` was `Available`.
- Non-dry collection found 3 new videos: `BUemPiRa-xo`, `JEicSm1MRpA`, and `tkDMzerjlvU`.
- Web-search mapping review left `BUemPiRa-xo` as an accepted no-place warning and mapped `JEicSm1MRpA` to `돈불리제담` plus `tkDMzerjlvU` to `꼬끄더그릴`.
- Transcript retry succeeded for both Baekban videos after pulling `.env.local`; must-taste dry-runs passed and stored three items for each restaurant.
- Final scoped gate report `regular_source_automation_20260726T221349Z.json` had `deploy_ready=true`, zero blockers, and one mapping-review warning.
- Verification passed: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, `pnpm run build`, Vercel production `READY`, and production API HTTP 200 with `items` plus `mustTasteItems`.
- Production commit `04db7c0d05a42f4e458b05655f85b65e551c0c95` deployed at `https://tastyroad-fc1nsfqpd-jaekwon-hans-projects.vercel.app` with alias `https://taste.indegser.com`.
- Naver Map sync for `Tastyroad 2` planned zero writes because restaurants `1536` and `1537` were already recorded in the excluded original `Tastyroad` sync state.

## Current Task - 2026-07-26 - Keep daily automation aligned with repository improvements

Worktree: `/Users/indegser/Github/tastyroad-worktrees/automation-follow-main`
Branch: `codex/automation-follow-main`

- [x] Inspect the active automation prompt, repository runbook, and dedicated automation checkout.
- [x] Make the active Automation prompt a stable bootstrap instead of a copied runbook.
- [x] Require every run to synchronize safely to current `origin/main`.
- [x] Require fresh reads of the repository runbook and owning skills after synchronization.
- [x] Update the active automation configuration.
- [x] Verify the prompt contract and record the result.

### Review

- Replaced active automation `tastyroad-regular-source-maintenance-2`'s copied full runbook with a stable bootstrap that fetches `origin`, uses a clean worktree at current `origin/main`, rereads repository guidance, and delegates to the versioned runbook.
- The repository runbook now explicitly supersedes cached Automation details and requires the starting `origin/main` commit in each run report.
- Owning skills are reread after synchronization, so later must-taste, transcript, mapping, release, and Naver sync improvements propagate without manually rewriting the active Automation prompt.
- Verification passed: six focused automation tests, Python compilation, `git diff --check`, active schedule/status/target preservation, and direct inspection of the rewritten TOML structure.

## Current Task - 2026-07-26 - Cache restaurant browsing on Vercel CDN

Worktree: `/Users/indegser/Github/tastyroad-worktrees/restaurant-cdn-cache`
Branch: `codex/restaurant-cdn-cache`
Target: production `main`

- [x] Read repository lessons and Vercel/Next.js cache guidance.
- [x] Confirm production page and API responses currently miss the CDN cache.
- [x] Add Vercel-only response caching for restaurant pages and API results.
- [x] Keep free-text search on a shorter cache lifetime.
- [x] Verify header routing, production build, and local page behavior.
- [x] Commit, integrate into `main`, push, and verify production cache hits.
- [x] Record before/after response timings and remaining tradeoffs.

### Review

- Added Vercel-only CDN caching to both the server-rendered restaurant page and
  `/api/restaurants`, while keeping browser responses on immediate revalidation.
- Browsing/filter/pagination responses use a 1-hour fresh TTL plus 1-day stale
  revalidation; URLs containing free-text `q` use 1 minute plus 5 minutes.
- `pnpm run build`, `git diff --check`, four local cache-header checks, and browser
  channel-filter navigation with 20 cards and no Next.js error overlay passed.
- Production deployment `tastyroad-47mrihe2c-jaekwon-hans-projects.vercel.app`
  reached `READY`; repeated page, API, and search requests changed from `MISS` to `HIT`.
- Eight cached production runs measured p50 at 13.8ms for a channel API response,
  15.4ms for the server-rendered channel page, and 14.3ms for free-text search.
- Distinct channels and page numbers retained independent totals, page values, and first
  restaurant IDs, confirming query-specific cache separation.

## Current Task - 2026-07-26 - Scope regular automation work

Worktree: `/Users/indegser/Github/tastyroad-worktrees/automation-scope-optimizations`
Branch: `codex/automation-scope-optimizations`

- [x] Read repository guidance, lessons, automation memory, and owning skill.
- [x] Limit mapping backlog processing to release-scope video IDs.
- [x] Limit Naver Map sync to release-scope restaurant IDs and no-op when already synced.
- [x] Preserve `collected_at` for unchanged reused YouTube candidates.
- [x] Add focused tests and run narrow verification.
- [x] Record final behavior and verification results.

### Review

- The regular runner now passes each newly discovered video ID to both metadata
  backlog processing and Naver candidate resolution.
- Final scoped reports expose `release_scope_restaurant_ids`; Naver sync accepts
  repeatable `--restaurant-id` arguments and exits before Edge when all requested
  IDs are already covered by sync/exclude/failure state.
- Reused RSS and flat-playlist candidates preserve their original `collected_at`,
  eliminating timestamp-only raw JSON and SQLite updates.
- Verification passed: 13 focused tests, Python compilation, `git diff --check`,
  scoped mapping smoke checks, and a real no-browser Naver no-op for restaurant 463.
- The Codex automation update API was unavailable (`No handler registered`), so
  the active automation prompt was not changed before these code changes are
  integrated into `main`.

## Current Task - 2026-07-26 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`
Branch: `codex/regular-source-automation`
Target: production `main`

- [x] Read repository guide, lessons, automation memory, and required Tastyroad skills.
- [x] Fast-forward the dedicated automation worktree to current `origin/main`.
- [x] Run pre-maintenance Vercel integration gate and confirm `supabase-aqua-engine` is `Available`.
- [x] Run the non-dry deterministic source maintenance runner.
- [x] Read `data/work/regular_source_automation/latest.json` and classify work queues.
- [x] Process mapping, transcript, and must-taste queues with owning skills where needed.
- [x] Recalculate scoped release gates without collecting again.
- [ ] If gates pass, repeat Supabase preflight, build, integrate to `main`, push, and verify Vercel production.
- [ ] After production API verification, sync new verified restaurants to Naver Map `Tastyroad 2`.
- [ ] Record final verification, release, sync, or blocker notes.

### Review

- Pre-maintenance Supabase Marketplace gate passed: `supabase-aqua-engine` was `Available`.
- Non-dry runner found one new video: `baekban_gihaeng` / `V_t70Etmrl8`.
- Web-search-assisted mapping review matched the clip to existing restaurant `무한쌈밥집` (`restaurant_id=463`, Naver place ID `18760353`) and promoted the new video mapping.
- Transcript ingest succeeded for `V_t70Etmrl8` with Korean captions in Supabase Storage.
- Must-taste workflow prepared full transcript coverage, validator dry-ran against a temp SQLite copy, and stored one item: `우삼겹`.
- Final scoped gate report: `deploy_ready=true`, zero blockers, zero warnings, all scoped work queues empty.
- Verification so far: SQLite integrity `ok`, blank public Naver ID count `0`, `git diff --check`, and `pnpm run build` passed.

## Current Task - 2026-07-26 - Improve Naver Map sync reliability

Worktree: `/Users/indegser/Github/tastyroad-worktrees/improve-naver-map-sync`
Branch: `codex/improve-naver-map-sync`

- [x] Confirm the current Naver saved-list DOM and existing sync contracts.
- [x] Replace safe-mode screenshot/coordinate control with scoped Playwright locators.
- [x] Add persisted-save verification, transient retries, resolved failure cleanup, capacity guard, and clean interruption.
- [x] Add deterministic tests and run a small logged-in browser verification.
- [x] Record exact results and remaining tradeoffs.

### Review

- Scoped every save action to the `pcmap.place.naver.com` frame and the modal's exact `Tastyroad 2` checkbox; removed screenshot-color, fixed-coordinate, and blind-mode control paths.
- Added a 700ms DOM-settle window because Naver first renders list rows as unselected before asynchronously applying membership state.
- Added three-attempt transient retries, permanent error classification, stale failure cleanup after success, final-failure-only screenshots, structured result JSON, non-zero partial/capacity exits, and clean interruption summaries.
- Added a visible 1,000-place capacity guard and exact list-name matching so `Tastyroad` cannot be confused with `Tastyroad 2`.
- Live verification reconciled already-saved `유즈라멘`, persisted and re-open-verified `차린한식`, and confirmed `Tastyroad 2` at 637 visible places. The source now has 39 restaurants left for a later sync run.
- Verification passed: four unit tests, Python compilation, `git diff --check`, dry no-op, real already/saved flows, capacity-stop flow, and visible-list count audit.

## Current Task - 2026-07-26 - Add a public restaurant read database

Worktree: `/Users/indegser/Github/tastyroad-worktrees/restaurant-query-performance`
Branch: `codex/restaurant-query-performance`

- [x] Confirm the performance branch is pushed and based on current `origin/main`.
- [x] Capture full-response hashes for listing, filters, search, and later pages.
- [x] Build a deterministic public-only SQLite artifact from the source database.
- [x] Move filtering, facet counts, totals, and pagination into indexed SQL queries.
- [x] Compare response hashes and tune the new query path in measured iterations.
- [x] Verify build output tracing and browser navigation.
- [x] Commit, push, and record final performance/size results.

### Review

- `pnpm run build` now atomically derives `data/tastyroad-public.sqlite` from the tracked
  source DB before Next.js builds; the generated DB contains 1,730 public rows and is
  4.37MB versus the 49MB source DB.
- Runtime filtering, totals, facet counts, ordering, and `LIMIT/OFFSET` pagination execute
  against indexed public columns. Production output traces include only the public DB.
- Seven full API response SHA-256 hashes matched the pre-change implementation exactly,
  covering unfiltered pages 1/2, filtered pages 1/4, multi-source, region, and search.
- Three measured query iterations reduced repeated-search p50 from 33.2ms in the first SQL
  version to 9.8ms through one-time substring matching, bounded LRU reuse, prepared statements,
  and SQLite mmap/cache settings.
- Seven fresh-process runs measured cold-request median at 141.1ms versus 236.8ms before the
  public DB change (40% faster). Warm representative p50 remained 9.4-11.1ms.
- SQL pagination stayed flat at page 2/50/80 (10.2/9.5/8.8ms p50); page 999 correctly clamped
  to page 87 and returned the final 10 rows.
- Browser verification passed for channel selection and page 2 navigation with 20 cards and
  no Next.js error overlay.
- Production release merged the performance branch into current `main`, passed the build and
  Supabase availability gate, and deployed through GitHub integration. Production verification
  returned HTTP 200 for the home page, the default API, and channel-filter page 2.

## Current Task - 2026-07-26 - Tune restaurant filtering performance

Worktree: `/Users/indegser/Github/tastyroad-worktrees/restaurant-query-performance`
Branch: `codex/restaurant-query-performance`

- [x] Read repository lessons and the Next.js App Router skill.
- [x] Create a dedicated worktree from current `origin/main`.
- [x] Establish a repeatable baseline for representative filter/search requests.
- [x] Run five measured optimization iterations, preserving response semantics.
- [x] Compare representative API totals, first-page IDs, and facet cardinalities.
- [x] Verify the production build and browser navigation behavior.
- [x] Record benchmark results, tradeoffs, and remaining risks.

### Review

- Reused the immutable deployment SQLite connection and materialized restaurant rows per
  server instance instead of reopening, aggregating, normalizing, and parsing every request.
- Built search documents lazily per restaurant and combined result/facet calculation into one
  pass; rejected eager search indexing after measurement showed a cold-request regression.
- Replaced internal filter and pagination anchors with non-prefetching Next.js `Link` navigation.
- Production-server warm p50 across default/source/multi-source/region/search requests improved
  from 92.6/82.0/53.5/111.7/86.5ms to 10.3/10.8/9.3/9.0/8.4ms.
- Baseline and final API checks matched totals, first 20 restaurant IDs, and facet cardinalities
  for all five representative requests.
- `pnpm run build`, browser content/error checks, and a live channel-filter navigation passed.
- Remaining tradeoff: the first request in a new server instance still performs the full source
  query (261ms locally on the latest 51MB DB); a generated public read model is deferred until production cold-start
  telemetry shows that this remaining cost warrants the added release-pipeline complexity.

## Current Task - 2026-07-25 - Sync unsynced Naver Map places

Worktree: `/Users/indegser/Github/tastyroad-worktrees/naver-map-sync-unsynced`
Branch: `codex/naver-map-sync-unsynced`
Target: `Tastyroad 2` private Naver Map list

- [x] Read repository lessons and Naver Map sync/list skills.
- [x] Create a dedicated worktree from current `origin/main`.
- [x] Inspect unsynced candidate scope and verify Edge/CDP Naver login.
- [x] Run safe chunked sync for all usable unsynced public verified restaurants.
- [x] Verify final state/count and capture/report evidence.
- [x] Commit intended Naver sync-state update for push.

### Review

- Edge CDP login was available and the initial unsynced candidate scope was 38 restaurants for `Tastyroad 2` after excluding the full first list state.
- Saved 3 restaurants to `Tastyroad 2`: `1926 합천삼가명품한우`, `677 참고 영상 식당1` (`영덕물회집`), and `678 참고 영상 식당2` (`광영수산 구로점`).
- Final `data/naver_map_list_synced_ids_2.json` count is 469; a final safe scope check returned `places=0`.
- Left 35 unresolved Naver failures in `data/work/naver_map_sync_failures.json`: mostly deleted/changed Naver place pages, plus unsafe ID/name mismatches for `즐거운술상` and `흑산도 소라`.

## Current Task - 2026-07-25 - Add Naver Map sync to automation

Worktree: `/Users/indegser/Github/tastyroad-worktrees/automation-naver-map-sync`
Branch: `codex/automation-naver-map-sync`
Target: production `main`

- [x] Read repository lessons and relevant automation/Naver Map skills.
- [x] Inspect active Codex automation prompt and Naver sync state files.
- [x] Update durable automation prompt to run Naver Map sync after production verification.
- [x] Update active Codex app automation with the same Naver Map sync step.
- [x] Validate, commit, push, and record the result.

### Review

- Active automation `tastyroad-regular-source-maintenance-2` now invokes `$tastyroad-naver-map-sync` after production API verification succeeds.
- The Naver sync target defaults to private list `Tastyroad 2` with `data/naver_map_list_synced_ids_2.json`, excluding first-list state from `data/naver_map_list_synced_ids.json`.
- Naver Map failures are recorded as post-release warnings; they do not roll back a verified production release.
- Successful Naver sync should commit and push only the changed `data/naver_map_list_synced_ids*.json` state files after deployment.

## Current Task - 2026-07-25 - Add 홍석천이원일 YouTube source

Worktree: `/Users/indegser/Github/tastyroad-worktrees/add-hong-won-channel`
Branch: `codex/add-hong-won-channel`
Target: production `main`, then private Naver Map lists

- [x] Read repository guidance, lessons, and the YouTube collection skill.
- [x] Verify the official channel ID and estimate the full-channel scope.
- [x] Add the source with focused non-restaurant title filtering.
- [x] Run full-channel collection and audit source coverage.
- [x] Provision the task worktree environment and confirm Supabase is `Available`.
- [x] Fetch missing transcripts for the full source and audit failures.
- [x] Review every video, verify concrete Naver place IDs, and promote valid mappings.
- [x] Run the full transcript-grounded must-taste workflow for eligible mapped pairs.
- [x] Verify source gates, SQLite integrity, and the production build.
- [ ] Commit intended changes, integrate into `main`, push, and verify Vercel production.
- [ ] Sync newly public source restaurants into the available private Naver Map lists and verify counts. (Paused at the user's request after 166 new registrations; 41 remain.)
- [ ] Record the final result and clean up the task worktree if safe.

### Review

- Added enabled source `hongseokcheon_leewonil` for official channel `UCIP3hSJruPL4dIi95lsuCZA`.
- Excluded the channel-introduction video and collected 232 unique videos: 224 eligible `/videos` entries plus 8 current RSS-only Shorts.
- Repeated per-video detail failures triggered the documented safe fallback; all official IDs/titles were preserved, 15 RSS rows have publication dates, and missing detail fields remain retryable.
- Full-channel audit reports `remote_total=224`, `local_collected=232`, and `missing=0`.
- Updated the audit helper to invoke the available `yt_dlp` Python module consistently with the collector.
- Stored preferred timed transcripts for 231 of 232 videos; `ZSFq3JO1a_o` has captions disabled by YouTube.
- Promoted 260 verified video-place mappings across 180 videos and 230 restaurants, all with numeric Naver place IDs.
- Applied 226 transcript-supported restaurant-video results with 341 must-taste items; 33 eligible pairs remain intentionally empty for insufficient direct evidence.
- Added 166 new source restaurants to private Naver Map list `Tastyroad 2`; 19 source restaurants were already in `Tastyroad`, four were already in `Tastyroad 2`, and 41 remain after the user asked to prioritize deployment.
- Verification passed: SQLite integrity, zero blank Naver IDs, Python compilation, `git diff --check`, `pnpm run build`, and immediate pre-release Supabase Marketplace status `Available`.

## Current Task - 2026-07-25 - Regular source maintenance automation

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260725`
Branch: `codex/regular-source-maintenance-20260725`
Target: production `main` if gates pass

- [x] Read repository guide, lessons, automation memory, and required Tastyroad skills.
- [x] Create a dedicated automation worktree from fresh `origin/main`.
- [x] Confirm pre-maintenance Supabase Marketplace status is `Available`.
- [x] Run the non-dry deterministic all-source maintenance runner.
- [x] Inspect `latest.json` and process scoped mapping/transcript/must-taste queues.
- [x] Recalculate the original release scope and verify hard data gates.
- [x] Repeat Supabase preflight, build, commit, integrate to `main`, push, and verify Vercel production if deploy-ready.
- [x] Record the final result and preserve or clean up the worktree according to the release outcome.

### Review

- Pre-maintenance Supabase Marketplace check: `supabase-aqua-engine` was `Available`.
- The real non-dry run found one new `전현무계획` video: `kkUsuZQoHJU`.
- Web-search-assisted mapping review verified `합천삼가명품한우` at Naver place ID `32063978`.
- Transcript ingestion succeeded for `kkUsuZQoHJU` with 241 Korean timed segments in Supabase Storage.
- Full must-taste workflow stored two validated items: `한우 특수부위 모둠` and `갈비`.
- Final scoped gate: `deploy_ready=true`, zero blockers, zero warnings, and empty work queues.
- Verification passed: SQLite integrity, blank Naver ID check, `git diff --check`, and `pnpm run build`.
- Immediate pre-push Supabase Marketplace check: `supabase-aqua-engine` was `Available`.
- Commit `46f8a33` was fast-forwarded to `main`, pushed, deployed through GitHub/Vercel, and production API verification returned HTTP 200 with an `items` array.

## Current Task - 2026-07-25 - Continue Baekban Gihaeng in Tastyroad 2

Worktree: `/Users/indegser/Github/tastyroad-worktrees/baekban-naver-sync-2`
Branch: `codex/baekban-naver-sync-2`
Target: production `main`

- [x] Read repository lessons and the Naver Map sync/list, browser, and release skills.
- [x] Add separate multi-list sync-state support and verify the remaining source scope.
- [x] Create and verify the private Naver Map list `Tastyroad 2`.
- [x] Sync the remaining verified Baekban Gihaeng restaurants in safe chunks.
- [x] Verify final list count, remaining exceptions, and capture a screenshot.
- [x] Validate, commit, deploy through `main`, and verify production.

### Review

- Created `Tastyroad 2` as a private Naver Map list and confirmed 466 visible saved places.
- The two list state files cover 647 of 649 verified Baekban Gihaeng restaurants without restaurant-ID overlap: 181 in `Tastyroad`, 466 in `Tastyroad 2`.
- Naver reports deleted/unavailable pages for the two remaining exceptions: `베쓰 푸틴` (1647) and `하조대순대국전문점` (1751).
- Added explicit per-list state and cross-list exclusion options, plus a direct modal-save-button preference for reliable confirmation.
- Final Naver Map screenshot: `/private/tmp/tastyroad-2-final-466.png`.
- Verification passed: Python compile, source-scoped dry-run, SQLite integrity, `git diff --check`, and `pnpm run build`; the connected Supabase resource was `Available` before release.

## Current Task - 2026-07-24 - Sync Baekban Gihaeng to Naver Map and deploy

Worktree: `/Users/indegser/Github/tastyroad-worktrees/baekban-naver-sync`
Branch: `codex/baekban-naver-sync`
Target: production `main`

- [x] Read repository lessons and the Naver Map sync/list, browser, and release skills.
- [x] Confirm Edge CDP login, private `Tastyroad` list, and current candidate scope.
- [x] Sync verified Baekban Gihaeng restaurants until the external list capacity is reached.
- [x] Verify the final saved-list count and capture a screenshot.
- [x] Validate the sync-state changes and production build.

### Review

- Confirmed the logged-in Edge CDP session and private `Tastyroad` list at 839 saved places.
- Added a source-scoped sync option so unrelated unsynced restaurants are not processed.
- The source scope contains 649 verified restaurants; 19 were already present in local sync state and 630 were initial candidates.
- Naver Map stopped accepting selections when the UI count reached exactly 1,000. The local sync state now covers 181 Baekban Gihaeng restaurants, leaving 468 for a second-list decision.
- Final capacity screenshot: `/private/tmp/baekban-naver-list-capacity.png`.
- Verification passed: source-scoped dry-run, Python compile, SQLite integrity, `git diff --check`, and `pnpm run build`.

## Current Task - 2026-07-24 - Release Naver Map sync update

Worktree: `/Users/indegser/Github/tastyroad-worktrees/naver-map-list-sync-20260724`
Branch: `codex/naver-map-list-sync-20260724`
Target: production `main`

- [x] Read release guidance and confirm Supabase is `Available`.
- [x] Confirm clean `main`, `origin/main`, and the intended task commit.
- [x] Run the production build in the task worktree.
- [x] Fast-forward the intended commit into `main` and push GitHub.
- [x] Wait for the matching Vercel production deployment to reach `READY`.
- [x] Verify the production restaurants API.
- [x] Record the result and remove the clean task worktree.

### Review

- Supabase Marketplace resource `supabase-aqua-engine` was `Available`.
- `pnpm run build` passed before release.
- Naver Map sync commits were fast-forwarded into production `main` and pushed through GitHub.
- Vercel deployment `tastyroad-6oqvrl7aj-jaekwon-hans-projects.vercel.app` reached `READY` for commit `5b68ead`.
- `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned HTTP 200 with an `items` array and `total=892`.

## Current Task - 2026-07-24 - Sync verified restaurants to Naver Map

Worktree: `/Users/indegser/Github/tastyroad-worktrees/naver-map-list-sync-20260724`
Branch: `codex/naver-map-list-sync-20260724`

- [x] Read repository guidance, lessons, and Naver Map sync/list skills.
- [x] Inspect the target config, sync state, worktrees, and CDP availability.
- [x] Launch the copied Edge CDP profile and verify Naver login.
- [x] Verify the private `Tastyroad` list and current count.
- [x] Run safe chunked sync for all usable unsynced public verified restaurants.
- [x] Verify final list count, sync-state coverage, and capture a screenshot.
- [x] Record the final review/result.

### Review

- Naver Map login marker was present and the target `Tastyroad` list remained private.
- Fixed the runner's place-load check to inspect the `pcmap.place.naver.com` frame as well as the main map document.
- Safely added 68 places; the Naver list count increased from 771 to 839 and local synced IDs increased from 789 to 857.
- Left 35 candidates unsynced: 31 deleted/unavailable Naver place links and 4 clear or unresolved place-name mismatches.
- Final screenshot: `/private/tmp/tastyroad-naver-list-final-20260724.png`.
- Verification passed: Python compile, safe/blind `--limit 0`, `git diff --check`, final candidate audit, and visual private-list/count check.

## Current Task - 2026-07-24 - Collect and process Baekban Gihaeng

Worktree: `/Users/indegser/Github/tastyroad-worktrees/baekban-full-pipeline`
Branch: `codex/baekban-full-pipeline`

- [x] Read repository lessons and the collection, transcript, mapping, and must-taste skills.
- [x] Enable the `baekban_gihaeng` source and estimate the current collection scope.
- [x] Collect eligible videos and verify raw/SQLite coverage.
- [x] Fetch missing timed transcripts into Supabase Storage and verify coverage/failures.
- [x] Review broadcast evidence, verify Naver place IDs, and promote valid restaurant mappings.
- [x] Run the full transcript-grounded must-taste workflow for eligible mapped pairs.
- [x] Verify SQLite integrity, exact pair coverage, and scoped diffs.
- [x] Record final results and any unresolved exceptions.

### Review

- Official full-channel audit found 1,151 eligible `백반기행` videos.
- Per-video detail enrichment hit YouTube HTTP 429, so the collector now has a documented `--skip-details` fallback that preserves official playlist IDs/titles and leaves incomplete rows retryable.
- Collected all 1,151 IDs/titles into `data/raw/youtube/baekban_gihaeng.json` and `data/tastyroad.sqlite`; five RSS rows retained published dates while the remaining detail fields await a later safe enrichment retry.
- Official TV CHOSUN episode metadata covers 353 episodes; review artifacts now cover candidate discovery for episodes 1-353.
- Completed Naver place review for episodes 1-164 and 247-353; the currently verified artifacts yield 411 unique video-place mappings before conflict retries and the remaining 165-246 review.
- Stored preferred timed transcripts for 1,148 of 1,151 collected videos in Supabase Storage; all transient block/SSL failures succeeded on retry, while `-Md73_s5cDk`, `YTEI-4ydH_8`, and `mxIuruH15LA` have captions disabled by YouTube.
- Promoted 691 audited video-place mappings covering 690 collected videos and 649 restaurants; every promoted restaurant has a numeric Naver place ID.
- Full-transcript taste review exposed and corrected two otherwise plausible metadata mappings: `TsHJcaRs914` now maps to 진미본가, and `bwFDXCcq22A` now maps to 울진참가자미.
- Applied 445 transcript-supported restaurant-video taste results with 473 menu items after five reviewed rounds. Of 690 mapped pairs with transcripts, 245 remain intentionally empty because the full multi-pass review found insufficient direct recommendation evidence.
- Final checks passed: all 691 mappings retain numeric Naver IDs, SQLite integrity is `ok`, modified Python scripts compile, `git diff --check` is clean, and `pnpm run build` succeeds.

## Current Task - 2026-07-24 - Harden and publish daily automation spec

Worktree: `/Users/indegser/Github/tastyroad-worktrees/harden-daily-automation`
Branch: `codex/harden-daily-automation`
Target: production `main`

- [x] Confirm the active and legacy Codex automation states.
- [x] Pause the legacy dry-run-first automation.
- [x] Add Supabase `Available` preflight checks to the active automation.
- [x] Mirror the checks in the repository skill, durable prompt, agent guide, and lessons.
- [x] Validate the scoped changes.
- [x] Commit, push, integrate into `main`, and update the local checkout.

### Review

- The active Codex automation now checks Supabase before maintenance and immediately before release.
- The legacy dry-run-first automation is paused.
- The repository skill, durable automation prompt, agent guide, and lessons carry the same external-resource hard gate.
- `git diff --check` and `pnpm run build` passed; `pnpm lint` is unavailable because the repository has no lint script.
- Commit `c72b0b2` was pushed on `codex/harden-daily-automation`, fast-forwarded into `main`, and pushed to GitHub.

## Current Task - 2026-07-24 - Release after Supabase recovery

Worktree: `/Users/indegser/Github/tastyroad-worktrees/release-after-supabase-restore`
Branch: `codex/release-after-supabase-restore`
Target: production `main`

- [x] Confirm the connected Supabase resource recovered to `Available`.
- [x] Read repository lessons and the regular automation/release skills.
- [x] Run the non-dry recurring maintenance and inspect scoped map/taste gates.
- [x] Resolve any hard publishing blockers and recalculate the release gate.
- [x] Verify SQLite integrity and `pnpm run build`.
- [x] Commit intended changes, integrate into `main`, and push GitHub.
- [x] Wait for the matching Vercel deployment and verify the production API.
- [x] Record the final release result and clean up the worktree if safe.

### Review

- The real daily collection found one new `최자로드` video: `zjWA1VFKH2Q`.
- Supabase transcript ingest succeeded with 28 Korean timed segments.
- Verified `싱싱뽈락회 수성못점` against Naver place ID `16154308` and promoted the video mapping.
- The full-transcript must-taste workflow validated and stored one item, `볼락회 쌈`.
- Final scoped gate: `deploy_ready=true`, zero blockers, zero warnings, and empty map/transcript/must-taste queues.
- SQLite integrity returned `ok`; `git diff --check` and `pnpm run build` passed.
- Commit `3a17f35` was fast-forwarded to `main` and pushed through GitHub.
- Vercel production deployment `tastyroad-18c5zq8r9-jaekwon-hans-projects.vercel.app` reached `READY`.
- `https://taste.indegser.com/api/restaurants` returned HTTP 200 and exposed restaurant `1294` with Naver place ID `16154308` and the `볼락회 쌈` must-taste item.

## Current Task - 2026-07-24 - Make daily maintenance deterministic and release-complete

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`
Branch: `codex/regular-source-automation`
Target: production `main`

- [x] Read repository guide, lessons, and collection/map/transcript/must-taste/release skills.
- [x] Confirm the false no-op root cause and inspect the current automation runner/prompt.
- [x] Fix `yt-dlp` invocation and prevent dry-run reports from claiming zero new videos without collection.
- [x] Add explicit mapping, transcript, and must-taste work queues plus deterministic release gates.
- [x] Add regression tests and update the durable automation prompt/skill.
- [x] Run actual latest collection and resolve new-video map verification.
- [x] Ingest available transcripts and validate/apply taste menu results for newly mapped pairs.
- [x] Verify SQLite integrity, release gates, and `pnpm run build`.
- [ ] Commit intended changes, integrate into `main`, push, and verify Vercel production.
- [x] Update the active daily automation and record final results.

### Review

- Actual non-dry collection found 22 release-scope videos across the five enabled sources.
- Verified and promoted seven restaurants with numeric Naver place IDs: 시미베, 일선화, 만천리상회 서울청담점, 밥도사술도사, 주차매점, 대성 콩국수, and 덕합반점.
- Locally retried transcripts and validator-applied one source-grounded must-taste item for six new restaurant-video pairs; 만천리상회 remains a transcript warning because the premiere was not playable yet.
- Final scoped gate report: `deploy_ready=true`, zero blockers, 17 warnings (16 metadata-poor mapping reviews and one not-yet-playable transcript).
- Verification passed: three runner regression tests, Python compile checks, SQLite integrity, `git diff --check`, and `pnpm run build`.
- Active automation `tastyroad-regular-source-maintenance-2` now runs the real non-dry collection, scoped map/transcript/must-taste review, gated `main` release, and production API verification every day at 07:00.
- GitHub `main` was pushed, but three matching Vercel production attempts stopped at 0 ms with `BUILD_FAILED: Resource provisioning failed`; production verification remains incomplete and the task worktree is intentionally preserved.

## Current Task - 2026-07-24 - Add production release to daily automation

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`
Branch: `codex/regular-source-automation`

- [x] Read repository guide, lessons, `$tastyroad-regular-source-automation`, and `$tastyroad-site-release`.
- [x] Inspect the active Codex automation and repository state.
- [x] Update the active routine with an explicit GitHub-to-Vercel production release sequence.
- [x] Verify the saved automation remains active on the daily schedule.
- [x] Record the result and release safety gates.

### Review

- Updated active automation `tastyroad-regular-source-maintenance-2` to invoke both `$tastyroad-regular-source-automation` and `$tastyroad-site-release`.
- The routine now builds, commits only intended tracked changes, integrates them into production `main`, pushes through GitHub, waits for the matching Vercel deployment to become `READY`, and verifies the production restaurants API.
- Production release remains gated by mapping completion, numeric Naver IDs, successful non-transcript maintenance, SQLite integrity, and `pnpm run build`.
- Transcript and must-taste gaps remain warnings and do not prevent verified mapped restaurants from being published.
- No-op runs do not create empty commits or deployments; failures preserve the worktree and report the exact blocker.
- The schedule remains active daily at 07:00 local time.
- The Codex app automation API returned a missing-handler error during this update, so the persisted automation TOML was updated directly and checked for the expected id, active status, schedule, release skill, main push, Vercel READY wait, and production API verification text.

## Current Task - 2026-07-24 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`
Branch: `codex/regular-source-automation`

- [x] Read repository guide, lessons, automation memory, and `$tastyroad-regular-source-automation`.
- [x] Rebase the automation worktree onto current `origin/main`.
- [x] Run the deterministic automation dry-run with the required Python scripts path.
- [x] Run the non-dry maintenance runner only if the dry-run shows new videos or actionable work.
- [x] Read `data/work/regular_source_automation/latest.json` and classify blockers vs warnings.
- [x] Verify release gates and deploy only if hard gates are clean.
- [x] Record the final run result and update automation memory.

### Review

- Dry-run command: `export PATH="/Users/indegser/Library/Python/3.9/bin:$PATH"; python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py --dry-run`.
- Result: `0` new videos across enabled sources (`성시경의 먹을텐데`, `김사원세끼`, `또간집`, `최자로드`, `전현무계획`).
- Hard publishing gates: clean (`deploy_ready=true`, `blocker_count=0`).
- Follow-up warnings: `25` existing must-taste gaps (`김사원세끼` 16, `전현무계획` 8, `또간집` 1).
- No non-dry maintenance run, build, or deployment was performed because no source count changed and no new verified mapped restaurants were collected.

## Current Task - 2026-07-11 - Naver sync selector-first controls

Worktree: `/Users/indegser/Github/tastyroad-worktrees/naver-map-selector-sync`
Branch: `codex/naver-map-selector-sync`

- [x] Read repository guide, lessons, and Naver sync skill instructions.
- [x] Create a task-specific worktree from `origin/main`.
- [x] Add selector-first Naver save-modal controls with coordinate fallback.
- [x] Update Naver sync skill docs for selector-first behavior.
- [x] Verify syntax and dry-run behavior.
- [x] Record result notes.

### Review

- Added selector-first control lookup for the place save button, target `Tastyroad` checkbox, modal save button, edit-list button, and modal close button.
- Kept the existing screenshot/coordinate path as fallback because Naver Map still does not expose every save-list UI state reliably.
- Adjusted `blind` mode so selector-success paths save once and do not run the legacy double-click coordinate recovery sequence.
- Updated the Naver sync skill docs and lessons to describe selector-first behavior.
- Verification: `python3 -m py_compile`, safe `--limit 0`, blind `--limit 0`, blind/include-synced guard, selector HTML smoke, and `git diff --check` passed.

## Current Task - 2026-07-10 - ChoiJaRoad taste and Naver sync

Worktree: `/Users/indegser/Github/tastyroad-worktrees/choizaroad-taste-naver-sync`
Branch: `codex/choizaroad-taste-naver-sync`

- [x] Read repository guide, lessons, and transcript/taste/Naver sync skill instructions.
- [x] Create a task-specific worktree from `origin/main` and provision `.env.local`.
- [x] Inspect `최자로드` public pair, transcript, must-taste, and Naver sync coverage.
- [x] Fetch missing transcripts needed for `최자로드` public mapped restaurants.
- [x] Run/apply transcript-grounded must-taste results for eligible `최자로드` pairs.
- [x] Sync newly public `최자로드` restaurants to the Naver Map `Tastyroad` list.
- [x] Verify SQLite integrity, taste coverage, Naver sync count, build, and production deployment if data changed.
- [x] Record final review/result notes.

### Notes

- `최자로드` public scope: `33` verified restaurant-video pairs, `31` videos, `33` restaurants.
- Preferred transcripts already existed for all `33` pairs, so no transcript fetch was needed.
- Applied `33` validator-passing must-taste rows, one representative item per pair; final `최자로드` must-taste remaining count is `0`.
- Naver sync-state now records all `33` `최자로드` restaurant IDs (`1257`-`1286`, plus prior reused rows).
- Naver Map UI screenshot `/private/tmp/choizaroad-naver-list-final.png` shows private `Tastyroad` list count `767` after safe verification and manual save of `마마리마켓`.
- Verification so far: must-taste batch dry-run/apply, SQLite integrity `ok`, Naver sync-state `choi_missing=0`, `git diff --check`, and `pnpm run build`.

### Review

- Applied `33` transcript-grounded `최자로드` must-taste rows to `video_must_taste_items`; final production API check returned `source=최자로드 total=33` and a must-taste reason for the first item.
- Synced/verified all `33` `최자로드` public restaurants against the Naver Map private `Tastyroad` list; local sync-state now records `789` total IDs and `choi_missing=0`.
- Naver UI count for `Tastyroad` showed `767` in `/private/tmp/choizaroad-naver-list-final.png`; safe re-verification opened all `33` ChoiJaRoad places and either observed the Tastyroad checkbox already selected or selected/saved it.
- Production deployment `tastyroad-qz7t1s79f-jaekwon-hans-projects.vercel.app` reached `READY` for commit `8530d08`; aliases include `https://taste.indegser.com`.

## Current Task - 2026-07-10 - Add ChoiJaRoad channel and deploy

Worktree: `/Users/indegser/Github/tastyroad-worktrees/add-choijaroad-channel`
Branch: `codex/add-choijaroad-channel`

- [x] Read repository guide, lessons, and relevant YouTube collection/release instructions.
- [x] Create a task-specific worktree from `origin/main`.
- [x] Confirm current `최자로드` source, collection, and public mapping state.
- [x] Refresh `최자로드` collection if needed.
- [x] Map verified `최자로드` restaurant rows with numeric Naver place IDs.
- [x] Verify SQLite/public API/build.
- [x] Commit, integrate to `main`, push, and verify production deployment.
- [x] Record final review/result notes.

### Notes

- `최자로드` source was already configured, but public rows were `0` because no verified restaurant mappings existed.
- Full-channel collection initially pruned RSS/Shorts-only recent rows; patched the collector to merge RSS latest candidates into full-channel output.
- Refreshed `choizaroad` to `161` collected videos.
- Applied `33` Naver-ID-verified `최자로드` restaurants from `data/verified_places/choizaroad_pin_verified_places.json`.
- Left `스시702` unresolved because Naver search returned a mismatched `참치플러스 분당본점` result.
- Verification so far: collector/parser/promoter `py_compile`, `process_pipeline_backlog.py --dry-run --source 최자로드 --skip-enrich-missing-metadata`, selected candidate count `33`, SQLite integrity `ok`, local production API `source=최자로드` returned `total=33`, `git diff --check`, and `pnpm run build`.

### Review

- Added/preserved `161` collected `최자로드` videos and `33` public verified restaurant mappings.
- Patched full-channel collection so RSS/Shorts latest rows are merged before pruning.
- Patched mapping helpers to prefer `📍` place lines, reject ChoiJaRoad season/schedule blocks, and let promotion refresh corrected addresses on existing rows.
- Production deployment `tastyroad-duma3r82x-jaekwon-hans-projects.vercel.app` reached `READY` for commit `4bebdd8`.
- Production alias check: `https://taste.indegser.com/api/restaurants?source=최자로드&limit=5&includeFacets=true` returned `total=33`, first item `도쿄 멘친테이 혼포`, and source facet `최자로드: 33`.

## Current Task - 2026-07-10 - Update Naver sync script

Worktree: `/Users/indegser/Github/tastyroad-worktrees/sync-naver-verified-restaurants`
Branch: `codex/sync-naver-verified-restaurants`

- [x] Re-read `$tastyroad-naver-map-sync` and inspect current runner.
- [x] Replace brittle `agent-browser` single-command clicks with a persistent CDP runner.
- [x] Add safe/blind modes, chunking, and failure logging for reruns.
- [x] Update skill docs for Edge 150 non-default profile and current UI verification.
- [x] Verify compile and dry-run behavior.
- [x] Record result notes.

### Review

- Replaced the Naver sync runner's repeated `agent-browser --cdp` subprocess calls with a persistent Playwright `connect_over_cdp` session.
- Added `--mode safe` as the default screenshot-verified checkbox path and `--mode blind` for unsynced-ID recovery when screenshot capture is unstable.
- Added `--chunk-size`, `--failure-log`, `--retry-failures`, and `--no-require-place-name` options so large syncs can be resumed without reprocessing known failures.
- Added a guard blocking `--mode blind --include-synced`, because Naver saved-list controls are toggles.
- Updated `$tastyroad-naver-map-sync` docs for Edge 150's non-default user-data-dir requirement and current coordinate verification.
- Verification: `python3 -m py_compile`, safe `--limit 0`, blind `--limit 0`, blind/include-synced guard, and `git diff --check` all passed.

## Current Task - 2026-07-10 - Sync verified restaurants to Naver Map

Worktree: `/Users/indegser/Github/tastyroad-worktrees/sync-naver-verified-restaurants`
Branch: `codex/sync-naver-verified-restaurants`

- [x] Read AGENTS.md, lessons, `$tastyroad-naver-map-sync`, and `naver-map-lists`.
- [x] Create a task-specific worktree from `origin/main`.
- [x] Inspect Naver Map target/synced data and script verification commands.
- [x] Confirm Edge CDP and Naver login/list state.
- [x] Run the Naver Map sync for all unsynced verified restaurants.
- [x] Verify final saved-list count and capture evidence.
- [x] Record final result notes.

### Notes

- Edge 150 blocks CDP on the default profile directory, so a local CDP-only profile copy is running from `/tmp/tastyroad-edge-cdp-profile`.
- CDP is available on port `9222`; user completed Naver login and Naver Map shows `내정보 보기`.
- Verified target list exists as private `Tastyroad`; visible count was `39`, then first test save changed local synced state to `40`.
- Current UI target-list checkbox coordinate is approximately `(416, 617)`, not the older script coordinate.

### Review

- Naver Map `Tastyroad` list is still private and now shows `750` saved places in the UI screenshot `/private/tmp/tastyroad-naver-list-after-sync.png`.
- Source scope was `854` eligible verified public restaurant rows. Local sync state now records `759` restaurant IDs as attempted/synced.
- `95` rows remained unsynced because their Naver place page did not load through the logged-in Map UI; details are in `/private/tmp/tastyroad-naver-sync-failures.json`.
- Because Edge 150 blocks default-profile CDP, sync ran through `/tmp/tastyroad-edge-cdp-profile` with a copied logged-in session.
- The bundled script coordinates did not fit the current UI, so the run used temporary Playwright chunk runners under `/tmp`.

## Current Task - 2026-07-10 - Soften automation release gates

Worktree: `/Users/indegser/Github/tastyroad-worktrees/automation-release-soft-gates`
Branch: `codex/automation-release-soft-gates`

- [x] Read repository guide, lessons, and `$tastyroad-regular-source-automation`.
- [x] Confirm public site can show mapped restaurants without must-taste rows.
- [x] Change regular-source gate logic so transcript/must-taste gaps are warnings, not deployment blockers.
- [x] Update automation prompt/docs to deploy mapped restaurants even when transcript or must-taste follow-up remains.
- [x] Verify runner behavior and syntax.
- [x] Record review/result notes.

### Review

- Changed the regular source runner so transcript gaps, transcript command failures, and missing must-taste rows are reported under `gates.warnings` instead of `gates.blockers`.
- `deploy_ready` now depends on hard publishing blockers only: missing SQLite, mapping blockers, and non-transcript command failures.
- Updated `$tastyroad-regular-source-automation`, its durable automation prompt, `AGENTS.md`, and `README.md` to say verified mapped restaurants should be released even when transcript/must-taste follow-up remains.
- Updated the live Codex Automation prompt at `~/.codex/automations/tastyroad-regular-source-maintenance/automation.toml`.
- Also applied the runner/prompt policy change to the live automation worktree `/Users/indegser/Github/tastyroad-worktrees/tastyroad-automation-runner`, because the daily schedule executes from that checkout.
- Verification: `python3 -m py_compile` passed in both the canonical change worktree and the live automation worktree. Dry-run in the canonical worktree returned `deploy_ready=true`, `blocker_count=0`, `warning_count=25`. Dry-run in the live automation worktree returned `deploy_ready=true`, `blocker_count=0`, `warning_count=25`.

## Current Task - 2026-07-10 - Jun Hyun-moo Plan must-taste current run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/junhyunmoo-must-taste-20260710`
Branch: `codex/junhyunmoo-must-taste-20260710`

- [x] Read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Create a task-specific worktree from `origin/main` and provision `.env.local`.
- [x] Inspect current `전현무계획` verified-map and transcript/taste coverage.
- [x] Plan missing must-taste pairs from verified restaurants with preferred transcripts.
- [x] Run must-taste semantic artifacts for planned pairs.
- [x] Apply validator-passing results sequentially to SQLite.
- [x] Verify coverage, SQLite integrity, and build risk.
- [x] Record review/result notes.

### Notes

- Worker assignment: batches `001`-`010` only, in this worktree on branch `codex/junhyunmoo-must-taste-20260710`.
- This worker must not write final `data/tastyroad.sqlite`; validate with `/tmp/junhyunmoo_must_taste_001_010_dryrun.sqlite`.
- Batch 001-010 scope is 20 video units and 22 restaurant-video pairs.
- Worker checklist:
  - [x] Read repository guide, relevant lessons, and `$tastyroad-transcript-must-taste`.
  - [x] Inspect assigned batch files and validator shape.
  - [x] Review assigned transcript blocks and restaurant windows.
  - [x] Write video-level attention artifacts for batches 001-010.
  - [x] Write pair-level attention/candidates/reviews/results for all 22 pairs.
  - [x] Dry-run validate every pair against temp SQLite.
  - [x] Write `batch_001_done.json` through `batch_010_done.json`.
  - [x] Record worker result counts and blockers.

#### Worker 001-010 Review

- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for 20 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for 22 assigned restaurant-video pairs.
- Result: 19 success rows and 3 insufficient_evidence rows.
- Wrote `/tmp/junhyunmoo_must_taste_20260710_batches/batch_001_done.json` through `batch_010_done.json`.
- Verification: each assigned pair passed `apply_must_taste_result.py --dry-run --sqlite /tmp/junhyunmoo_must_taste_001_010_dryrun.sqlite`; tracked SQLite was not used for worker validation.

- Current public `전현무계획` scope is 196 `verified`/`metadata_verified` restaurant-video pairs with Naver IDs.
- 186 pairs have preferred transcripts and are planned under `/tmp/junhyunmoo_must_taste_20260710_batches` as 160 video units / 80 batches.
- 10 public pairs currently lack a preferred transcript and are outside this must-taste run until transcript ingest succeeds.
- Prepared 160 video-level contexts under `data/work/must_taste_video/` and 186 pair contexts under `data/work/must_taste/`.
- The older 2026-07-04 result artifacts are not reusable because their `context_hash` values differ from the current prepared contexts.
- Semantic workers completed all 80 batches: 164 success pairs and 22 insufficient-evidence pairs.

### Review

- Applied 164 validator-passing `전현무계획` restaurant-video pairs to `video_must_taste_items`, creating 295 item rows.
- Left 22 transcript-scoped public pairs without must-taste rows because the transcript did not support a visitor-useful menu recommendation for the target restaurant.
- Final coverage: 196 public `verified`/`metadata_verified` pairs, 186 transcript-scoped pairs, 164 pairs with must-taste rows, 295 item rows, and 22 transcript-scoped insufficient-evidence pairs.
- Verification: all 164 success artifacts passed final batch dry-run before apply, final sequential apply passed, SQLite `pragma integrity_check` returned `ok`, and `pnpm run build` passed.

### Worker 031-040

- Assignment: batches `031`-`040` only, in this shared worktree on branch `codex/junhyunmoo-must-taste-20260710`.
- This worker must not write final `data/tastyroad.sqlite`; validate with `/tmp/junhyunmoo_must_taste_031_040_dryrun.sqlite`.
- Batch 031-040 scope is 20 video units and 27 restaurant-video pairs.
- Worker checklist:
  - [x] Read repository guide, relevant lessons, and `$tastyroad-transcript-must-taste`.
  - [x] Inspect assigned batch files and validator shape.
  - [x] Review assigned transcript blocks and restaurant windows.
  - [x] Write video-level attention artifacts for batches 031-040.
  - [x] Write pair-level attention/candidates/reviews/results for all 27 pairs.
  - [x] Dry-run validate every pair against temp SQLite.
  - [x] Write `batch_031_done.json` through `batch_040_done.json`.
  - [x] Record worker result counts and blockers.

#### Worker 031-040 Review

- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for 20 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for 27 assigned restaurant-video pairs.
- Result: 26 success rows and 1 insufficient_evidence row (`b5XBTA1iycw` / `1226` 물레방아 즉석구이).
- Wrote `/tmp/junhyunmoo_must_taste_20260710_batches/batch_031_done.json` through `batch_040_done.json`.
- Verification: each assigned pair passed `apply_must_taste_result.py --dry-run --sqlite /tmp/junhyunmoo_must_taste_031_040_dryrun.sqlite`; logs are under `/tmp/junhyunmoo_must_taste_20260710_batches/validation_logs_031_040_tmp_sqlite`. Temp SQLite `pragma integrity_check` returned `ok`.

### Worker slice: batches 021-030

- [x] Confirm assigned batch scope and artifact paths.
- [x] Rebuild current-context artifacts for videos with older semantic references.
- [x] Scout and write artifacts for videos without older references.
- [x] Dry-run validate every assigned pair with `/tmp/junhyunmoo_must_taste_021_030_dryrun.sqlite`.
- [x] Write `/tmp/junhyunmoo_must_taste_20260710_batches/batch_021_done.json` through `batch_030_done.json`.
- [x] Record worker result counts and blockers.

#### Worker 021-030 Review

- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for 20 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for 20 assigned restaurant-video pairs.
- Result: 20 success rows, 0 insufficient_evidence rows, 0 failures; selected 44 total must-taste items.
- Wrote `/tmp/junhyunmoo_must_taste_20260710_batches/batch_021_done.json` through `batch_030_done.json`.
- Verification: each assigned pair passed `apply_must_taste_result.py --dry-run --sqlite /tmp/junhyunmoo_must_taste_021_030_dryrun.sqlite`; logs are under `/tmp/junhyunmoo_must_taste_20260710_batches/validation_logs_021_030_tmp_sqlite`. Temp SQLite `pragma integrity_check` returned `ok`.

### Batch 011-020 Worker Checklist

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs, pair count, and worktree status.
- [x] Build reviewed video attention events for batches `011`-`020`.
- [x] Build pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair against `/tmp/junhyunmoo_must_taste_011_020_dryrun.sqlite`.
- [x] Write `/tmp/junhyunmoo_must_taste_20260710_batches/batch_011_done.json` through `batch_020_done.json`.
- [x] Record result counts and blockers.

### Batch 011-020 Review

- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for the 20 assigned video units.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for all 21 assigned restaurant-video pairs.
- Result count: 16 success rows and 5 insufficient_evidence rows (`RruvMQwvCnM/1193`, `dHAyBfp5HDc/1214`, `NxEQmGdw7i4/1214`, `ZnOOL_3yH9U/1214`, `qdLvZJ38Yn0/1193`).
- Wrote `/tmp/junhyunmoo_must_taste_20260710_batches/batch_011_done.json` through `batch_020_done.json`.
- Verification: every assigned pair passed `apply_must_taste_result.py --dry-run --sqlite /tmp/junhyunmoo_must_taste_011_020_dryrun.sqlite`; logs are under `/tmp/junhyunmoo_must_taste_20260710_batches/validation_logs_011_020_tmp_sqlite`; temp SQLite integrity check returned `ok`. No final batch apply was run.

### Batch 041-050 Worker Checklist

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs, pair count, worktree, and dirty DB constraint.
- [x] Review prepared video contexts, transcript blocks, and pair contexts for batches `041`-`050`.
- [x] Write video-level candidate-finding artifacts for batches `041`-`050`.
- [x] Write pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair against `/tmp/junhyunmoo_must_taste_041_050_dryrun.sqlite`.
- [x] Write `/tmp/junhyunmoo_must_taste_20260710_batches/batch_041_done.json` through `batch_050_done.json`.
- [x] Record result counts and blockers.

#### Review

- Assigned scope: 10 batch files, 20 video units, 24 restaurant-video pairs.
- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for all 20 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for all 24 pairs.
- Result counts: 19 `success`, 5 `insufficient_evidence`, 0 validation failures, 39 selected items.
- `insufficient_evidence`: `XRR49kXAfWg`/`1226`, `qTTpxnmXOgU`/`1228`, `pHXLUniqwto`/`923`, `U2bSMzgau6A`/`1231`, `6Cqu-Qi9ZRA`/`1231`.
- Verification: each pair passed `python3 .codex/skills/tastyroad-transcript-must-taste/scripts/apply_must_taste_result.py --dry-run --sqlite /tmp/junhyunmoo_must_taste_041_050_dryrun.sqlite --context <context> --result <result>`; temp SQLite integrity check returned `ok`.
- Wrote completion files `/tmp/junhyunmoo_must_taste_20260710_batches/batch_041_done.json` through `batch_050_done.json`.
- No final batch apply was run; tracked `data/tastyroad.sqlite` was not used as the validation target.

### Batch 051-060 Worker Checklist

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs, pair count, worktree, and dirty DB constraint.
- [x] Review prepared video contexts, transcript blocks, and pair contexts for batches `051`-`060`.
- [x] Write video-level candidate-finding artifacts for batches `051`-`060`.
- [x] Write pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair against `/tmp/junhyunmoo_must_taste_051_060_dryrun.sqlite`.
- [x] Write `/tmp/junhyunmoo_must_taste_20260710_batches/batch_051_done.json` through `batch_060_done.json`.
- [x] Record result counts and blockers.

#### Review

- Assigned scope: 10 batch files, 20 video units, 20 restaurant-video pairs.
- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for all 20 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for all 20 pairs.
- Result counts: 16 `success`, 4 `insufficient_evidence`, 0 validation failures.
- `insufficient_evidence`: `BF1pXahJP4Y`/`1231`, `CjZlzIIWuVY`/`1238`, `rXbo46oOfx4`/`1242`, `mriRGK3jlhU`/`1240`.
- Verification: each pair passed `python3 .codex/skills/tastyroad-transcript-must-taste/scripts/apply_must_taste_result.py --sqlite /tmp/junhyunmoo_must_taste_051_060_dryrun.sqlite --dry-run --context <context> --result <result>`.
- Wrote completion files `/tmp/junhyunmoo_must_taste_20260710_batches/batch_051_done.json` through `batch_060_done.json`.
- No final batch apply was run; tracked `data/tastyroad.sqlite` was not used as the validation target.

### Batch 061-070 Worker Checklist

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs, pair count, worktree, and dirty DB constraint.
- [x] Review prepared video contexts, transcript blocks, and pair contexts for batches `061`-`070`.
- [x] Write video-level candidate-finding artifacts for batches `061`-`070`.
- [x] Write pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair against `/tmp/junhyunmoo_must_taste_061_070_dryrun.sqlite`.
- [x] Write `/tmp/junhyunmoo_must_taste_20260710_batches/batch_061_done.json` through `batch_070_done.json`.
- [x] Record result counts and blockers.

#### Batch 061-070 Review

- Wrote semantic artifacts for 30 assigned restaurant-video pairs only.
- Result counts: 27 `success`, 3 `insufficient_evidence`, 0 validation failures; selected 40 total menu items.
- Insufficient evidence pairs: `T5vlcx2b8PU`/738 영광보쌈, `_zyhRAjCu5s`/1250 송골횟집, `3XO045-Eb6I`/1250 송골횟집.
- Validation command pattern: `python3 .codex/skills/tastyroad-transcript-must-taste/scripts/apply_must_taste_result.py --dry-run --sqlite /tmp/junhyunmoo_must_taste_061_070_dryrun.sqlite --context <context> --result <result>`.
- Completion files written: `/tmp/junhyunmoo_must_taste_20260710_batches/batch_061_done.json` through `batch_070_done.json`.
- No final batch apply was run.

### Batch 071-080 Worker Checklist

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs, pair count, worktree, and dirty DB constraint.
- [x] Review prepared video contexts, transcript blocks, and pair contexts for batches `071`-`080`.
- [x] Write video-level candidate-finding artifacts for batches `071`-`080`.
- [x] Write pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair against `/tmp/junhyunmoo_must_taste_071_080_dryrun.sqlite`.
- [x] Write `/tmp/junhyunmoo_must_taste_20260710_batches/batch_071_done.json` through `batch_080_done.json`.
- [x] Record result counts and blockers.

#### Review

- Assigned scope: 10 batch files, 20 video units, 22 restaurant-video pairs.
- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for all 20 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for all 22 pairs.
- Result counts: 21 `success`, 1 `insufficient_evidence`, 0 validation failures; the insufficient pair is `cVqviRXBivM` / `1252`.
- Verification: every assigned pair passed `python3 .codex/skills/tastyroad-transcript-must-taste/scripts/apply_must_taste_result.py --sqlite /tmp/junhyunmoo_must_taste_071_080_dryrun.sqlite --dry-run --context <context> --result <result>`, and `/tmp/junhyunmoo_must_taste_071_080_dryrun.sqlite` returned SQLite `pragma integrity_check = ok`.
- Wrote completion files `/tmp/junhyunmoo_must_taste_20260710_batches/batch_071_done.json` through `batch_080_done.json`.
- No final batch apply was run; tracked `data/tastyroad.sqlite` was not used as the validation target.

## Current Task - 2026-07-10 - Deploy Junhyunmoo web recovery

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`
Target: production `main`

- [x] Read AGENTS.md, lessons, and `$tastyroad-site-release`.
- [x] Inspect main and the `map-web-search-test` worktree.
- [x] Integrate verified `전현무계획` web-search mapping recovery changes into main.
- [x] Verify SQLite, scripts, and app build on main.
- [x] Commit and push production main.
- [x] Verify Vercel deployment and production API.
- [x] Clean up the released task worktree if safe.
- [x] Record final release notes.

### Review

- Released `b0898d6 data: publish junhyunmoo web recovery` to production through the GitHub-to-Vercel integration.
- Published the updated map skill/agent workflow, promotion-script review-status fix, `data/tastyroad.sqlite`, and 5 `junhyunmoo_web_recovery_*_20260709_places.json` lineage files.
- Final local data check before release: `전현무계획` `mapping_verified=170`, `not_applicable=109`; blank restaurant `naver_map_id` count is `0`; SQLite `pragma integrity_check` returned `ok`.
- Verification: `python3 -m py_compile`, `git diff --check`, and `pnpm run build` passed on main.
- Vercel production deployment `tastyroad-o11fm6u32-jaekwon-hans-projects.vercel.app` reached `READY`, and `https://taste.indegser.com/api/restaurants?source=전현무계획&limit=1&includeFacets=true` returned HTTP 200 with an `items` array.
- Cleanup: left `/Users/indegser/Github/tastyroad-worktrees/map-web-search-test` in place because it still has uncommitted local changes, even though the intended release changes are integrated into `main`.

## Current Task - 2026-07-09 - Improve region facets

Worktree: `/Users/indegser/Github/tastyroad-worktrees/map-filter-gyeonggi`
Branch: `codex/map-filter-gyeonggi`

- [x] Read AGENTS.md, lessons, and relevant Next.js UI guidance.
- [x] Create a task-specific worktree from `origin/main`.
- [x] Inspect region normalization, facet query, and filter UI.
- [x] Reframe region clustering as administrative 시도 instead of intermediate 권역.
- [x] Keep 시군구 as the detailed region facet for dense drill-down.
- [x] Verify facet behavior and app build.
- [x] Record final review/result notes.

### Review

- Replaced intermediate region clusters with administrative 시도 values such as `서울`, `경기`, and `부산`.
- The region facet now drills from `경기` into 시군구 values such as `경기 남양주시`, `경기 성남시`, and `경기 수원시`.
- Current verified 경기 rows group as `경기:54`, with `경기 남양주시:3` visible in the 시군구 facet.
- Added `pnpm-workspace.yaml` with `sharp` build approval so `pnpm run build` remains repeatable under the current pnpm policy.
- Verification: DB-backed 경기 facet grouping check passed, local page/API checks showed `경기 → 경기 남양주시`, `git diff --check` passed, and `pnpm run build` passed.

## Current Task - 2026-07-09 - Resolve gates and deploy source update

Worktree: `/Users/indegser/Github/tastyroad-worktrees/run-regular-source-now`
Branch: `codex/run-regular-source-now`
Target: production `main`

- [x] Read AGENTS.md, lessons, and transcript/must-taste/release skills.
- [x] Reuse the existing source-run worktree with pending collected data.
- [x] Retry transcript blockers and confirm remaining transcript gate state.
- [x] Generate and apply transcript-grounded must-taste rows for remaining pairs.
- [x] Re-run the regular source automation gate report.
- [x] Build, commit, integrate to `main`, push, and verify Vercel production.
- [x] Clean up the task worktree if safe.
- [x] Record final verification/result notes.

### Review

- Resolved the pending 2026-07-05 manual source-run gate for the original 33 collected videos: transcript retry added tracks for `6255xH_Ygs4` and `Yr4FcPy6YPk`; the remaining transcript-disabled videos are reviewed `not_applicable`/unmapped, so the regular-source gate now skips them instead of blocking release.
- Added transcript-grounded must-taste rows for `샐러드킹` (`iJOvdh_LAgY`), `5 오마카세` (`tZmWw9l-Thc`), and `만리향` (`Wj_7fiFawMQ`), with 3 items per restaurant-video pair.
- Verification: must-taste dry-runs passed before apply; SQLite `pragma integrity_check` returned `ok`; original 33-video gate recalculation returned `deploy_ready=true`; `python3 -m py_compile` passed for the regular-source automation runner; `git diff --check` passed; `pnpm run build` passed after approving the worktree-local `sharp` build script.
- Production release: committed `90abf1d data: publish regular source update`, fast-forwarded `main`, pushed to GitHub, Vercel deployment `tastyroad-bcy0zpxom-jaekwon-hans-projects.vercel.app` reached `READY`, and `https://taste.indegser.com/api/restaurants?source=김사원세끼&limit=50&includeFacets=true` returned `샐러드킹` and `5 오마카세` with must-taste items.
- Cleanup: removed `/Users/indegser/Github/tastyroad-worktrees/run-regular-source-now` after the release commit was integrated into `main` and pushed.

## Current Task - 2026-07-09 - Deploy collected source update

Worktree: `/Users/indegser/Github/tastyroad-worktrees/run-regular-source-now`
Branch: `codex/run-regular-source-now`
Target: production `main`

- [x] Read `$tastyroad-site-release` and release lessons.
- [x] Inspect `main`, worktrees, and the pending source-automation run.
- [x] Check the pending automation gate before production release.
- [x] Confirm current `main` deployment status and production API response.
- [x] Record blocked release result.

### Review

- Pending collected source update is not deployable yet: `data/work/regular_source_automation/latest.json` has `deploy_ready=false` with 9 blockers.
- Blockers are 6 transcript items and 3 must-taste items (`iJOvdh_LAgY` / 샐러드킹, `tZmWw9l-Thc` / 5 오마카세, `Wj_7fiFawMQ` / 만리향).
- No commit, push, or production deployment was attempted for the pending data changes.
- Current `main` SHA `0f8dd51` already has Vercel production deployment `tastyroad-q96dx3fgf-jaekwon-hans-projects.vercel.app` in `READY`.
- Production API verification passed: `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned an `items` array.

## Current Task - 2026-07-05 - Manual regular source run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/run-regular-source-now`
Branch: `codex/run-regular-source-now`

- [x] Read repository guide, lessons, and `$tastyroad-regular-source-automation`.
- [x] Create a fresh task-specific worktree from `origin/main`.
- [x] Provision `.env.local` from the linked main checkout.
- [x] Run the regular source automation dry-run.
- [x] Run deterministic collection to query enabled sources.
- [x] Inspect latest automation report and blockers.
- [x] Record verification/result notes.

### Review

- Manual regular source run completed at `2026-07-04T16:38:20Z` (`2026-07-05 01:38:20 KST`) in `/Users/indegser/Github/tastyroad-worktrees/run-regular-source-now`.
- New videos collected: 33 total: `성시경의 먹을텐데` 2, `김사원세끼` 2, `또간집` 15, `최자로드` 14, `전현무계획` 0.
- Transcript ingestion ran for all enabled sources; `전현무계획` backfilled 261 transcript tracks and left 18 failed attempts, mostly 429/retry blockers.
- Release gate is blocked: 6 transcript blockers and 3 must-taste blockers remain, so no deployment was attempted.
- Verification: `pragma integrity_check` returned `ok`.

## Current Task - 2026-07-04 - Broadcast sources production release

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`
Target: production `main`

- [x] Read repository guide, lessons, and `$tastyroad-site-release`.
- [x] Merge `전현무계획` and disabled `백반기행` source settings into `main`.
- [x] Upsert `전현무계획` collected videos into the current `main` SQLite DB without replacing unrelated DB changes.
- [x] Apply verified `전현무계획` place mappings and review rows on `main`.
- [x] Verify mapped counts, blank Naver IDs, and SQLite integrity.
- [x] Run production build verification.
- [x] Commit and push `main`.
- [x] Verify Vercel production deployment and public API response.

### Review

- Added `전현무계획` as an enabled official MBN source and kept `식객 허영만의 백반기행` disabled after the user correction.
- Collected `전현무계획` into 279 video rows; metadata is complete for 272 rows, with 7 detail-enrichment failures remaining from the 2024-05-24 cluster.
- Applied 45 verified `전현무계획` video mappings across 27 restaurants using official MBN records plus concrete Naver place IDs.
- Verification before build: `전현무계획` status is 45 `mapping_verified` and 234 `not_ready_for_mapping`; blank restaurant `naver_map_id` count is 0; SQLite `pragma integrity_check` returned `ok`.
- Production release: `pnpm run build` passed, commit `8e3f311` reached Vercel `READY`, and `https://taste.indegser.com/api/restaurants?source=전현무계획&limit=3&includeFacets=true` returned `전현무계획` restaurants.

## Current Task - 2026-06-26 - Regular source automation

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-automation`
Branch: `codex/regular-source-automation`

- [x] Read repository guide, lessons, and relevant source/transcript/map/must-taste/release skills.
- [x] Create a task-specific worktree and provision local env from the linked main checkout.
- [x] Inspect existing pipeline scripts and DB status to identify safe automation boundaries.
- [x] Record the Codex Automation preference as a durable lesson.
- [x] Add a regular source automation skill/script that orchestrates all enabled channels.
- [x] Add a Codex Automation prompt/entrypoint for periodic new-video checks.
- [x] Document required secrets, review gates, and deployment behavior.
- [x] Verify scripts, dry-run behavior, and app build where relevant.
- [x] Record review/result notes.

### Review

- Added `$tastyroad-regular-source-automation` as the Codex app Automation entrypoint for recurring all-source maintenance.
- Added an executable deterministic runner that plans/runs enabled-source collection, deterministic mapping candidate handling, transcript ingestion, gate checks, and ignored JSON reports under `data/work/regular_source_automation/`.
- Added a reusable Codex Automation prompt at `.codex/skills/tastyroad-regular-source-automation/scripts/automation_prompt.md`.
- Updated `AGENTS.md`, `README.md`, and `tasks/lessons.md` so future recurring checks default to Codex app Automation with a dedicated worktree instead of GitHub Actions.
- Registered the local Codex app Automation at `~/.codex/automations/tastyroad-regular-source-maintenance/automation.toml`, enabled daily at 07:00 local time, using `/Users/indegser/Github/tastyroad` as the cwd.
- Verification: `python3 -m py_compile` passed for the new runner, `quick_validate.py` passed for the new skill, runner `--dry-run` produced a report, skip-mode non-dry gate calculation produced a report without external collection/DB writes, and `git diff --check` passed. App build was not run because no app runtime code changed.

## Current Task - 2026-06-26 - Ddoganjip must-taste batches 031-036

Worktree: `/Users/indegser/Github/tastyroad-worktrees/ddoganjip-must-taste-backfill`
Branch: `codex/ddoganjip-must-taste-backfill`

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs and prepared artifact locations.
- [x] Build video-level restaurant windows and shared attention events for batches `031`-`036`.
- [x] Build pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair result without writing SQLite.
- [x] Write batch completion files for `031`-`036`.
- [x] Record result counts and blockers.

### Notes

- Assigned scope: `/tmp/ddoganjip_must_taste_batches/batch_031.json` through `batch_036.json`, totaling 12 video units and 38 restaurant-video pairs.
- Worker stage is dry-run only; do not run SQLite apply without `--dry-run`.

### Review

- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for all 12 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for all 38 assigned restaurant-video pairs.
- Result: 36 success rows and 2 insufficient_evidence rows (`F7PN-1EmJbI` / `894` 제주객주리조림, `u9Y3hZ9UP9I` / `902` 대복추어탕).
- Wrote `/tmp/ddoganjip_must_taste_batches/batch_031_done.json` through `batch_036_done.json`.
- Verification: each assigned pair passed `apply_must_taste_result.py --dry-run` against `/tmp/ddoganjip_must_taste_031_036_dryrun.sqlite`; full logs are under `/tmp/ddoganjip_must_taste_batches/validation_logs_031_036_tmp_sqlite`. The tracked SQLite file is clean.

## Current Task - 2026-06-26 - Ddoganjip must-taste batches 001-006

Worktree: `/Users/indegser/Github/tastyroad-worktrees/ddoganjip-must-taste-backfill`
Branch: `codex/ddoganjip-must-taste-backfill`

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch scope and prepared artifact locations.
- [x] Write video-level restaurant windows and attention events for batches 001-006.
- [x] Write pair-level attention, candidates, reviews, and results for assigned pairs.
- [x] Dry-run validate every assigned pair without writing SQLite.
- [x] Write batch_001_done.json through batch_006_done.json.
- [x] Record review/result notes.

### Notes

- Assigned scope: `/tmp/ddoganjip_must_taste_batches/batch_001.json` through `batch_006.json`, totaling 12 video units and 41 restaurant-video pairs.
- Worker stage is dry-run only; do not run SQLite apply without `--dry-run`.

### Review

- Result: 40 success rows and 1 insufficient_evidence row (`vAKeY1t_bLI` / `1029` 류정닭개장).
- Wrote reviewed `restaurant_windows.json` and `video_attention_events.jsonl` for all 12 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for all 41 assigned restaurant-video pairs.
- Wrote `/tmp/ddoganjip_must_taste_batches/batch_001_done.json` through `batch_006_done.json`.
- Verification: each assigned pair passed `apply_must_taste_result.py --dry-run` with `--sqlite /tmp/ddoganjip_must_taste_dryrun.sqlite`; `data/tastyroad.sqlite` is not modified.

## Current Task - 2026-06-26 - Ddoganjip must-taste batches 019-024

Worktree: `/Users/indegser/Github/tastyroad-worktrees/ddoganjip-must-taste-backfill`
Branch: `codex/ddoganjip-must-taste-backfill`

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs and worktree status.
- [x] Build video-level restaurant windows and shared attention events for batches `019`-`024`.
- [x] Build pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair result without writing SQLite.
- [x] Write batch completion files for `019`-`024`.
- [x] Record result counts and blockers.

### Notes

- Assigned scope: `/tmp/ddoganjip_must_taste_batches/batch_019.json` through `batch_024.json`, totaling 12 video units and 36 restaurant-video pairs.
- Worker stage is dry-run only; do not run SQLite apply without `--dry-run`.

### Review

- Wrote restaurant windows and shared video attention events for 12 assigned videos.
- Wrote pair-level attention events, menu candidates, separate evidence_skeptic/visitor_judge reviews, and result artifacts for 36 restaurant-video pairs.
- Result count: 36 success rows, 0 insufficient_evidence rows, 0 failures, 48 total selected items.
- Verification: every pair passed `apply_must_taste_result.py --dry-run` against `/tmp/ddoganjip_must_taste_dryrun.sqlite`; collector dry-run over the six done files passed with `dry_run_ok=36` and `apply_skipped=true`.

## Current Task - 2026-06-26 - Ddoganjip must-taste batches 025-030

Worktree: `/Users/indegser/Github/tastyroad-worktrees/ddoganjip-must-taste-backfill`
Branch: `codex/ddoganjip-must-taste-backfill`

- [x] Read AGENTS.md, relevant must-taste lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs, prepared artifacts, and worktree status.
- [x] Build video-level restaurant windows and shared attention events for batches `025`-`030`.
- [x] Build pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair result without writing SQLite.
- [x] Write batch completion files for `025`-`030`.
- [x] Record result counts and blockers.

### Notes

- Assigned scope: `/tmp/ddoganjip_must_taste_batches/batch_025.json` through `batch_030.json`, totaling 12 video units and 38 restaurant-video pairs.
- Worker stage is dry-run only; do not run SQLite apply without `--dry-run`.

### Review

- Wrote video-level `restaurant_windows.json` and `video_attention_events.jsonl` for 12 assigned videos.
- Wrote pair-level `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, and `result.json` for all 38 assigned restaurant-video pairs.
- Completion files written: `/tmp/ddoganjip_must_taste_batches/batch_025_done.json` through `batch_030_done.json`.
- Results: 37 success rows with one item each, 1 insufficient-evidence row (`htg6NcCa3UE` / restaurant `842`) because transcript evidence names a different 곱창 restaurant than the assigned mapped restaurant.
- Verification: all 38 results passed `apply_must_taste_result.py --dry-run` against `/tmp/ddoganjip_must_taste_dryrun.sqlite`; no final SQLite apply was run.

## Current Task - 2026-06-26 - Ddoganjip must-taste backfill

Worktree: `/Users/indegser/Github/tastyroad-worktrees/ddoganjip-must-taste-backfill`
Branch: `codex/ddoganjip-must-taste-backfill`

- [x] Read repository guide, lessons, `$tastyroad-site-release`, and `$tastyroad-transcript-must-taste`.
- [x] Deploy must-taste workflow improvements to production from `main`.
- [x] Create a dedicated data backfill worktree and provision `.env.local`.
- [x] Plan `또간집` missing verified-map plus preferred-transcript pairs with video grouping.
- [x] Prepare video-level compact contexts and pair-level validation contexts.
- [x] Process assigned semantic worker batches 013-018 only and write dry-run completion files.
- [x] Run semantic candidate-finding/review/arbiter artifacts for all planned pairs.
- [x] Apply only validation-passing results sequentially to SQLite.
- [x] Verify coverage, DB integrity, and build.
- [x] Deploy updated taste data.

### Notes

- Production deploy commit for workflow improvements: `b7323c9 tools: optimize must-taste backfill workflow`.
- Final DB writes must be single-process through `apply_must_taste_batch.py`; worker stages must not write SQLite.
- Planned scope: `276` missing restaurant-video pairs grouped into `88` video units and `44` two-video batches under `/tmp/ddoganjip_must_taste_batches`.
- Prepared contexts: `88` video-level compact contexts and `276` pair-level validation contexts generated with no failures.
- Current blocker: semantic candidate-finding/review/arbiter work needs explicit permission to use parallel worker agents for the 44 planned batches; deterministic preparation is complete.
- Final extraction result: all `44` planned batches / `276` pairs produced validator-compatible result artifacts.
- Applied result: `269` success pairs were applied sequentially to SQLite; `7` pairs were left without taste because they did not pass the quality/restaurant-scope gate.
- Final `또간집` coverage: `287` scoped verified-map transcript pairs, `280` pairs with must-taste rows, `344` item rows, `7` remaining insufficient-evidence pairs.
- Remaining insufficient pairs: `vAKeY1t_bLI/1029`, `V-NzxlwdBPk/989`, `wV3fFBdJ-OA/1035`, `htg6NcCa3UE/842`, `F7PN-1EmJbI/894`, `u9Y3hZ9UP9I/902`, `9F9a_fFx45o/912`.
- Verification: `apply_must_taste_batch.py` dry-run passed for `269` success pairs before apply; actual sequential apply stored `269` pairs; SQLite `integrity_check` returned `ok`; coverage query returned `scoped_pairs=287`, `pairs_with_items=280`, `item_rows=344`; `pnpm run build` passed after worktree-local install with temporary `sharp` build approval.
- Deployment: committed `3b2ca27 data: fill ddoganjip must-taste items`, pushed `main`, Vercel production deployment `tastyroad-h4qzsodv1-jaekwon-hans-projects.vercel.app` reached `READY`, and `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned an `items` array.
- Assigned worker scope in this session: batches `013`-`018` only, using existing prepared video and pair contexts, writing only scoped artifact files plus `/tmp/ddoganjip_must_taste_batches/batch_013_done.json` through `batch_018_done.json`.
- Assigned worker scope in this session: video-grouped batches `007`-`012` only, `12` videos and `39` restaurant-video pairs. Write only the corresponding `data/work/must_taste_video/<video_id>/`, `data/work/must_taste/<video_id>/<restaurant_id>/`, and `/tmp/ddoganjip_must_taste_batches/batch_00{7..9}_done.json` / `batch_01{0..2}_done.json` artifacts; run `apply_must_taste_result.py --dry-run` only.

### Batch 007-012 Worker Checklist

- [x] Read AGENTS.md, relevant lessons, and `$tastyroad-transcript-must-taste`.
- [x] Confirm assigned batch inputs and worktree status.
- [x] Build video-level restaurant windows and shared attention events for batches `007`-`012`.
- [x] Build pair-level attention events, candidates, reviews, and result artifacts.
- [x] Dry-run validate every pair result without writing SQLite.
- [x] Write batch completion files for `007`-`012`.
- [x] Record result counts and blockers.

### Batch 007-012 Review

- Wrote restaurant windows and shared video attention events for 12 assigned videos.
- Wrote pair-level attention events, menu candidates, separate evidence_skeptic/visitor_judge reviews, and result artifacts for 39 restaurant-video pairs.
- Result count: 37 success rows, 2 insufficient_evidence rows, 0 failures.
- Insufficient evidence rows: `V-NzxlwdBPk` / `989` 시전돌곱창, `wV3fFBdJ-OA` / `1035` 심학산닭갈비.
- Verification: every assigned pair passed `apply_must_taste_result.py --dry-run` against `/tmp/ddoganjip_must_taste_dryrun_007_012.sqlite`; worker did not run the non-dry-run apply command.

### Batch 013-018 Review

- Wrote restaurant windows and shared video attention events for 12 assigned videos.
- Wrote pair-level attention events, menu candidates, separate evidence_skeptic/visitor_judge reviews, and result artifacts for 35 restaurant-video pairs.
- Result count: 35 success rows, 0 insufficient_evidence rows, 0 failures, 54 total selected items.
- Wrote `/tmp/ddoganjip_must_taste_batches/batch_013_done.json` through `batch_018_done.json`.
- Verification: every assigned pair passed `apply_must_taste_result.py --dry-run`; worker did not run the non-dry-run apply command.

## Current Task - 2026-06-26 - Must-taste video context compression

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-batch-orchestration`
Branch: `codex/must-taste-batch-orchestration`

- [x] Read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Add a video-level context preparation script with compact transcript blocks and restaurant metadata.
- [x] Add worker instructions for restaurant boundary finding, shared candidate-finding, and combined candidate reviews.
- [x] Smoke test on a 또간집 video and compare block count/input size against segment chunks.
- [x] Verify scripts and update task notes.

### Notes

- Goal: preserve full-transcript coverage but reduce worker input by grouping ASR segments into auditable blocks.
- Final pair artifacts and SQLite writes must still use the existing pair-level `apply_must_taste_result.py` validator.

### Review

- Added `prepare_must_taste_video_context.py`, a read-only video-level context builder that writes compact `blocks.json`, full `segment_lookup.json`, `video_context.json`, `restaurant_windows.json`, `video_attention_events.jsonl`, `task.md`, and `combined_candidate_review.md`.
- Smoke-tested `또간집` video `9LdSGv5wHec`: `1425` transcript segments became `104` compact blocks; the video has `4` restaurants, so pairwise scout would be `80` chunks while video-once scout is `20` chunks. `blocks.json` was `100K`; full `segment_lookup.json` stayed separate at `304K`.
- Updated the skill docs so video-grouped workers prepare compact video context first, use block input for boundary/shared candidate-finding, and may emit both candidate review perspectives from one combined call while preserving the existing `candidate_reviews.json` contract.
- Verification: video context smoke test passed; Python compile passed for must-taste scripts; `git diff --check` passed; `pnpm run build` passed.

## Current Task - 2026-06-26 - Must-taste low-cost quality benchmark

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-batch-orchestration`
Branch: `codex/must-taste-batch-orchestration`

- [x] Read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Inspect the existing batch orchestration changes before editing.
- [x] Add a read-only benchmark that uses `성시경의 먹을텐데` stored must-taste rows as gold quality comparison.
- [x] Measure candidate-window recall and token/chunk savings against the current pairwise whole-transcript workflow.
- [x] Update the must-taste skill docs with the benchmark-first optimization path.
- [x] Verify scripts and record results.

### Notes

- Goal: reduce token/time cost without repeating the unsafe heuristic-only DB write pattern.
- Quality comparison: existing Sung Si-kyung rows are treated as gold; a low-cost prefilter is acceptable only if it keeps high recall for stored evidence segments.
- Finding: signal-window prefilter is not yet worth adopting. With conservative range-based chunk accounting on Sung Si-kyung, signal recall was `95.26%` item / `91.11%` pair-all and the fragmented windows estimated `1562` chunks versus `1236` current pairwise chunks.
- Finding: video-once whole-transcript scouting is the safe optimization. Sung Si-kyung only saves `5.10%` because most videos have one restaurant, but `또간집` saves `68.93%` chunks (`3441` pairwise -> `1069` video-once) while preserving full-transcript scout coverage.

### Review

- Added `benchmark_must_taste_prefilter.py` to compare proposed low-cost transcript windows against stored must-taste rows without writing SQLite.
- Extended `plan_must_taste_batches.py` with `--group-by-video`, producing `videos.json` and video-grouped batches for multi-restaurant sources.
- Updated `$tastyroad-transcript-must-taste` bulk workflow to require Sung Si-kyung benchmark checks before risky prefilters and to route `또간집` through video-first scouting.
- Verification: `python3 -m py_compile` passed for must-taste scripts; grouped `또간집` planning produced `276` missing pairs as `88` video units / `44` batches; `git diff --check` passed; `pnpm run build` passed.

## Current Task - 2026-06-26 - Must-taste batch orchestration improvement

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-batch-orchestration`
Branch: `codex/must-taste-batch-orchestration`

- [x] Read repository guide, lessons, `$skill-creator`, and `$tastyroad-transcript-must-taste`.
- [x] Add a script to plan missing transcript-backed must-taste pairs into worker-sized batch files.
- [x] Add a script to collect done/retry files, dry-run validate, and apply all successful artifacts sequentially.
- [x] Update the must-taste skill docs to route large backfills through the scripts.
- [x] Verify scripts with focused checks plus build.
- [x] Record review/result notes.

### Notes

- Improvement target: reduce manual wave handling and prevent DB writes while workers are still running.
- Design: keep semantic 후보 찾기/후보 검토/최종 선택 agent-centered, but move batch planning and final validation/apply into deterministic scripts.

### Review

- Added `plan_must_taste_batches.py` to query verified-map plus preferred-transcript pairs for a source, write `pairs.json`, and split work into `batch_001.json` style worker inputs.
- Added `apply_must_taste_batch.py` to collect completion files, let `retry_*_done.json` override earlier insufficient rows, dry-run every selected artifact, and optionally apply all rows sequentially with a zero-missing coverage check.
- Updated `$tastyroad-transcript-must-taste` with a bulk backfill workflow that keeps agents on semantic stages only and keeps final SQLite writes single-process.
- Verification: Python compile passed for all must-taste scripts; `quick_validate.py` passed for the skill; planning produced 0 missing and 180 include-existing Sung Si-kyung pairs as expected; empty done-dir apply dry-run reported current coverage 180/180/422/0; `git diff --check` and `pnpm run build` passed.

## Current Task - 2026-06-26 - Skill agent design guidelines

Worktree: `/Users/indegser/Github/tastyroad-worktrees/skill-agent-guidelines`
Branch: `codex/skill-agent-guidelines`

- [x] Read repository guide, lessons, and `skill-creator`.
- [x] Inspect current Tastyroad skills and mapping skill resources.
- [x] Add repository skill-design guidance for script-centered vs agent-centered workflows.
- [x] Update `$tastyroad-map-video-restaurants` to use an agent-assisted mapping review flow while keeping deterministic writes.
- [x] Verify skill metadata and markdown consistency.
- [x] Record review/result notes.

### Review

- Added `AGENTS.md` skill design defaults so future skill creation starts by choosing script-centered, agent-centered, or hybrid architecture.
- Reworked `$tastyroad-map-video-restaurants` as a hybrid workflow: subagents may scout candidates, verify Naver places, and review conflicts, while final `verified_places` promotion and DB checks remain deterministic.
- Updated README, skill UI metadata, and lessons to match the new guidance.
- Verification: `quick_validate.py .codex/skills/tastyroad-map-video-restaurants` passed and `git diff --check` passed.

## Current Task - 2026-06-26 - Sung Si-kyung transcript-to-taste gap closure

Worktree: `/Users/indegser/Github/tastyroad-worktrees/sungsikyung-must-taste-fill`
Branch: `codex/sungsikyung-must-taste-fill`

- [x] Read repository guide, lessons, `$tastyroad-transcript-must-taste`, and `$tastyroad-map-video-restaurants`.
- [x] Confirm the missing scope and whether it is taste-eligible.
- [x] Promote verified Naver place IDs for Sung Si-kyung transcript-backed videos without mappings.
- [x] Attempt must-taste extraction for newly mapped transcript-backed restaurant-video pairs.
- [x] Apply only semantically valid must-taste results to `data/tastyroad.sqlite`.
- [x] Verify the final transcript-without-taste count, DB integrity, and app build.
- [x] Record review/result notes.
- [x] Continue with official must-taste extraction for mapped/no-taste pairs in reviewable batches.
- [x] Run remaining 152 mapped transcript-backed pairs through parallel `$tastyroad-transcript-must-taste` batches until pair count is 0.

### Notes

- Current source scope: `성시경의 먹을텐데` has 195 videos with preferred transcripts.
- The 176 videos with transcript but no must-taste rows all have no verified restaurant mapping yet (`has_map=0`, `has_taste=0`), while the 19 mapped transcript videos already have must-taste rows.
- Therefore closing the gap requires map verification first; `video_must_taste_items` cannot be written without a `restaurant_id`.
- Resolved 161 of 179 domestic `needs_review` candidates through Naver mobile search address matching and promoted them. Post-promotion, 161 transcript-backed mapped restaurant-video pairs need must-taste rows; 23 captioned videos still have no verified map row.
- Attempted deterministic transcript-signal extraction for all 161 newly mapped pairs. The generated artifacts passed structural validator dry-runs, but spot checks showed semantic false positives from ordering-only, comparison, and wrong-restaurant transcript moments. Removed the attempted `codex-transcript-signal` rows and did not keep the unsafe generator.
- Continuation target after pushing/merging the mapping commit: first reduce the 161 mapped transcript-backed restaurant-video pairs without taste using the full artifact workflow; leave the 23 no-map captioned videos for separate map verification.
- Continuation batch progress: applied validated must-taste rows for 압구정진주 한남직영점, 우래옥, 뱃고동, 돈푸짐감자탕, and 상무암뽕순대국밥. Current remaining mapped transcript-backed pairs without taste: 152.
- Current completion target: no `성시경의 먹을텐데` pair with verified map plus preferred transcript may remain without a stored `video_must_taste_items` row.
- Final official extraction batch processed 152 mapped transcript-backed pairs through `$tastyroad-transcript-must-taste`; the 3 initially insufficient 신림정 pairs were retried and converted to transcript-backed success artifacts.
- Final DB application dry-ran and applied all 152 selected result artifacts. `성시경의 먹을텐데` verified-map plus preferred-transcript coverage is now 180 pairs with 180 pairs having must-taste rows, 422 total Sung Si-kyung must-taste items, and 0 remaining pairs without taste.

### Review

- Promoted 161 Naver Map place IDs for transcript-backed `성시경의 먹을텐데` videos, raising verified map coverage to 180 links across 172 videos and 171 restaurants.
- Rejected the unsafe deterministic transcript-signal attempt, then ran the official transcript-grounded must-taste workflow for the remaining 152 mapped transcript-backed pairs.
- Applied 152 validation-passing result artifacts to `data/tastyroad.sqlite`; the final query for verified-map plus preferred-transcript `성시경의 먹을텐데` pairs without must-taste rows returned 0.
- Verification: all 152 final artifacts passed `apply_must_taste_result.py --dry-run`; final coverage is 180 scoped pairs / 180 pairs with items / 422 items / 0 remaining pairs without taste; SQLite `pragma integrity_check` returned `ok`; `git diff --check` passed; `pnpm run build` passed.

## Current Task - 2026-06-25 - Sung Si-kyung must-taste full rerun

Worktree: `/Users/indegser/Github/tastyroad-worktrees/sungsikyung-must-taste-rerun`
Branch: `codex/sungsikyung-must-taste-rerun`

- [x] Read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Scope all current `성시경의 먹을텐데` restaurant-video pairs with usable transcripts and existing must-taste rows.
- [x] Regenerate full must-taste artifacts for the entire current Sung Si-kyung scope, including already stored pairs.
- [x] Apply only validation-passing rerun results to `data/tastyroad.sqlite`.
- [x] Verify DB integrity, coverage counts, generated artifacts, and app build.
- [x] Record review/result notes.

### Review

- Regenerated full `$tastyroad-transcript-must-taste` artifacts for all 19 current transcript-backed `성시경의 먹을텐데` restaurant-video pairs, including pairs that already had stored rows.
- Replaced the previous 33 stored Sung Si-kyung must-taste rows with 52 validation-passing rows, keeping every pair at 2-3 selected items and preserving rejected-candidate lineage in `evidence_json`.
- Verified all 19 `apply_must_taste_result.py --dry-run` runs before actual apply.
- Verification: Sung Si-kyung view coverage is `restaurant_video_pairs=19`, `items=52`; SQLite `pragma integrity_check` returned `ok`; `git diff --check` passed; `pnpm run build` passed after `pnpm install --frozen-lockfile` restored the worktree's missing `node_modules`.

## Current Task - 2026-06-25 - Must-taste selector prompt final test

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-context-tests`
Branch: `codex/must-taste-context-tests`

- [x] Re-read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Inspect the current source-window/editor prompt and previous two-agent comparison output.
- [x] Update the source-window selection prompt without adding new style gates.
- [x] Re-run the DB-backed two-agent test on the same broader sample.
- [x] Produce a side-by-side comparison against existing reason and the previous run.
- [x] Record final findings and verification.

### Review

- Adopted the balanced two-agent direction: source-window selector chooses focused raw subtitle context, then subtitle editor lightly repairs it into `repaired_reason`.
- Tested a wider "do not cut too short" selector on the same 30-row DB sample. It pulled in price/order/background too often; previous balanced output beat it in 14 rows, with the wider prompt better in only 3 and similar in 13.
- Tested a narrower selector on the later 15-row half. It collapsed back to short/flat snippets such as `상위권 감자튀김이다` and `근데 고기가 대박이야`, so it is not adopted.
- Final skill prompt keeps the balanced selector and adds only a small caution not to force adjacent fragments when the next fragment shifts into price, order, a new menu, background, or a different claim.
- Comparison artifact: `/tmp/tastyroad_input_selector_test/adopted_selector_comparison.md`.
- Verification: `python3 -m py_compile` for must-taste scripts and `git diff --check` passed.

## Current Task - 2026-06-25 - Must-taste repair quality tightening

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-context-tests`
Branch: `codex/must-taste-context-tests`

- [x] Re-read current must-taste skill and relevant lessons after user rejection.
- [x] Tighten the repair workflow so `pass` means publishable complete Korean copy, not merely close enough.
- [x] Add broader validation for incomplete clauses and duplicated structures without overfitting only one sample.
- [x] Re-run blind `codex exec` and compare publishable pass rate.
- [x] Run a broader DB-backed sample comparing existing reason against subtitle-editor repaired copy.
- [x] Record broader-sample findings.
- [x] Record the revised result.

### Review

- Tightened the skill away from late-stage "repair a broken joined fragment" behavior and back toward the simpler successful behavior: choose a coherent source context window first, then minimally repair only awkward ASR/subtitle boundaries.
- Removed `repair_quality_gate` from the final result contract. The model should not self-label copy quality; final items must simply provide a validator-passing `repaired_reason`.
- Added stronger source-preserving repair instructions for complete Korean copy, connective/adverbial joins, and repeated conditional scaffolding.
- Re-ran blind `codex exec` as `source_preserving_blind_codex_output_v5.json`; repaired copy quality improved, but the result confirmed self-gating labels were the wrong abstraction.
- Final decision: use deterministic validation plus source-context reselection/retry; if a candidate cannot produce publishable repaired copy, move it to `rejected_candidates`.
- Verification: Python compile, `git diff --check`, focused repaired-text validation, SQLite integrity/schema check, and `pnpm run build` passed.
- Re-ran source-context-window blind tests after removing model self-gating. The "complete sentence" wording caused unsupported predicate completions (`않습니다`, `들어갑니다`, `입니다`), so the skill now allows natural quote-like phrases and prefers deletion/narrowing over invented finite endings.
- Final validator comparison on the three source-window runs: v1 passed 8/11, v2 passed 10/11, v3 passed 10/11. Remaining failures were exactly unsupported predicate completion or stranded connector endings, which should force source supplement/retry rather than publishing.
- Latest verification: Python compile, `git diff --check`, and focused repaired-text validator cases passed.
- Reworked the repaired-copy direction away from accumulated allow/deny gates and into a prompt-only subtitle editor pass. `apply_must_taste_result.py` now only checks `repaired_reason` structurally for display length; style is produced by the editor prompt.
- Ran prompt-only editor tests on the same 11 samples. The best behavior came from giving the editor a curated raw `reason`; giving it the widest raw context made it pull in setup/price/noisy tails. Final direction: arbiter chooses a focused raw source context, then the subtitle editor prompt lightly repairs it.
- Latest verification after the prompt-only rewrite: Python compile and `git diff --check` passed.
- Ran a broader DB-backed sample of 30 rows across 김사원세끼, 성시경의 먹을텐데, and 또간집, comparing existing stored `reason` with subtitle-editor output from evidence/supporting context.
- Broader sample result: prompt-only repair improves many overly short existing reasons, but blindly joining all supporting evidence often over-expands the copy, especially for 김사원세끼 rows with price/setup/context fragments. This confirms the editor prompt is useful only after a focused source-window selection step.
- Verification: parsed the generated sample/output/comparison JSON files and `git diff --check` passed.

## Current Task - 2026-06-25 - Must-taste source-preserving skill rewrite

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-context-tests`
Branch: `codex/must-taste-context-tests`

- [x] Re-read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Inspect current skill, generated pass prompts, validation, DB reference, and public display path.
- [x] Update the skill contract so raw expanded transcript context and source-preserving repaired display text are separate fields.
- [x] Add fragment-selection and repair-quality gates to generated task/pass prompts.
- [x] Run a fresh blind `codex exec` test using the rewritten skill guidance.
- [x] Record the blind test result and remaining risk.

### Review

- Changed the must-taste contract so `reason` is expanded raw transcript context and `repaired_reason` is the source-preserving public display copy.
- Updated `SKILL.md`, generated pass/task prompts, DB reference, validation/storage, SQLite schema, and the public restaurant query fallback to display `repaired_reason` when present.
- Added validator gates for analyst-style prose, dangling final fragments, mid-sentence clipped fragments, and duplicated conditionals such as `주문하시면 ... 드시면`.
- Ran blind `codex exec` tests from `/tmp` with only the rewritten prompt as input. The corrected prompt eliminated `/` separators in raw `reason` and avoided analyst-summary phrases, but the model still self-labeled several broken copies as `pass`.
- Focused validator check on the last blind output passed 7/11 and rejected 4/11: clipped `계란까지`, clipped `미나리와 함께`, duplicated `주문하시면 ... 드시면`, and clipped `먹으러`/`살짝` style fragments. This confirms the skill must rely on validation/retry, not prompt compliance alone.
- Verification: Python compile, `git diff --check`, SQLite integrity/schema check, and `pnpm run build` passed after installing worktree-local dependencies.

## Current Task - 2026-06-25 - Must-taste context quote experiments

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-context-tests`
Branch: `codex/must-taste-context-tests`

- [x] Run a blind `codex exec` prompt test without previous repaired outputs in the input.
- [x] Re-test a source-preserving repair prompt against the same examples.
- [x] Validate the generalized normalization prompt against the prior hand-made normalized examples.
- [x] Compare direct context quotes with lightly naturalized context copy.
- [x] Read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Create an isolated worktree for analysis artifacts.
- [x] Inspect stored must-taste rows, evidence JSON, and transcript context availability.
- [x] Generate real-data samples for several quote/context expansion directions.
- [x] Compare which direction improves variety without inventing unsupported claims.
- [x] Record review/result notes.

### Review

- Created `data/work/must_taste_context_reason_samples.md` with 11 real-data samples comparing current reason, full evidence segment, supporting-evidence pack, and compact direct-fragment candidates.
- Current DB has 94 must-taste rows; 66 rows have `evidence_text` longer than `reason`, and 89 rows already have `evidence_json.supporting_evidence`, so more context can often be shown without re-extraction.
- The safest direction is not failing flat rows, but rendering/storing a second context layer from existing support lines while keeping public claims as direct subtitle fragments.
- Reverted an unintended SQLite change caused by a failed context-preparation attempt and tightened the reusable lesson about running context/schema helpers against tracked DBs.
- Added `data/work/must_taste_context_copy_comparison.md` comparing direct subtitle context against lightly naturalized copy for the same 11 samples.
- Naturalized copy is consistently better for browsing when ASR breaks fragment sentences, but it should be stored/displayed as normalized context rather than direct quote because it repairs ASR and sentence boundaries.
- Added `data/work/must_taste_normalization_prompt_validation.md` to validate the generalized prompt against the previous hand-made normalized examples.
- Prompt validation returned 10 pass, 1 pass-with-caution, 0 fail; add a small guardrail to prefer natural browsing copy over meta-reporting phrases like `반응입니다` when a direct grounded sentence is available.
- Added `data/work/must_taste_source_preserving_prompt_test.md` with the corrected source-preserving prompt and actual outputs for the same 11 examples.
- Corrected test result: 11 pass, 0 caution, 0 fail. The key prompt change is to repair the expanded subtitle quote with minimal edits, not summarize evidence into analyst prose.
- Added `data/work/must_taste_blind_codex_prompt_eval.md` after running separate `codex exec` blind tests with no previous repaired outputs in the prompt.
- Blind result: prompt-only repair avoids analyst-summary drift, but is not reliable enough for publishable copy; it leaves clipped endings, duplicated conditional structures, and unrelated asides. Skill change should include source-fragment completeness and repair-quality gates.

## Current Task - 2026-06-25 - Production release compact address label

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`
Target: production `main`

- [x] Read repository guide, lessons, and release workflow.
- [x] Fast-forward `main` to the verified compact address preview branch.
- [x] Verify production build.
- [x] Push `main` and verify production Vercel deployment.
- [x] Clean up the merged preview worktree if safe.
- [x] Record review/result notes.

### Review

- Released the compact address row and smaller `지도` action label to production by fast-forwarding `main` through the verified preview commits.
- Production deployment reached `READY` through the GitHub integration.
- Verified `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned an item with thumbnail and upload metadata.
- Verified production HTML includes the address map link and thumbnail link, and fetched production CSS confirms `.map-link-label` uses the smaller `0.64rem` style with a reduced arrow.
- Removed `/Users/indegser/Github/tastyroad-worktrees/compact-address` after confirming it was clean, pushed, and merged into `main`.

## Current Task - 2026-06-25 - Compact restaurant address row

Worktree: `/Users/indegser/Github/tastyroad-worktrees/compact-address`
Branch: `codex/compact-address`
Target: Vercel preview

- [x] Read repository guide, lessons, and relevant Next.js/browser guidance.
- [x] Inspect current restaurant card address rendering and spacing.
- [x] Make the address consume less vertical space without losing the map action.
- [x] Verify build and mobile/desktop layout.
- [x] Tighten the `지도` action label size after focused feedback.
- [ ] Push and verify preview deployment.
- [ ] Record review/result notes.

## Current Task - 2026-06-25 - Production release latest-video cards

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`
Target: production `main`

- [x] Read repository guide, lessons, and release workflow.
- [x] Fast-forward `main` to the verified latest-video card preview branch.
- [x] Verify production build.
- [x] Push `main` and verify production Vercel deployment.
- [x] Clean up the merged preview worktree if safe.
- [x] Record review/result notes.

### Review

- Released the latest-video restaurant card design to production by fast-forwarding `main` through the verified preview commits.
- Production deployment `tastyroad-ic8ml0b6w-jaekwon-hans-projects.vercel.app` reached `READY`.
- Verified `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned an item with `sourceThumbnailUrl` and `sourcePublishedAt`.
- Verified production HTML for `1966정원` includes thumbnail links, video title links, and YouTube-style relative upload age, with no visible `추천 이유` or `먼저 맛볼 메뉴` labels.
- Removed `/Users/indegser/Github/tastyroad-worktrees/latest-video-sort` after confirming it was clean, pushed, and merged into `main`.

## Current Task - 2026-06-25 - Tune thumbnail card typography

Worktree: `/Users/indegser/Github/tastyroad-worktrees/latest-video-sort`
Branch: `codex/latest-video-sort`
Target: Vercel preview

- [x] Read repository guide, lessons, Next.js guidance, and release workflow.
- [x] Inspect current thumbnail-card typography and spacing.
- [x] Tune type scale, line height, and vertical rhythm without changing content structure.
- [x] Verify build and mobile/desktop browser layout.
- [x] Commit, push, and verify updated Vercel preview.
- [x] Record review/result notes.

### Review

- Tuned the compact thumbnail-card typography around the existing structure: slightly smaller restaurant names, quieter source/address metadata, tighter video title rhythm, and a more balanced recommendation block.
- Kept the small-thumbnail design, YouTube title/thumbnail click targets, YouTube-style relative upload age, and label-free must-taste rows intact.
- Verification: `git diff --check`, `pnpm run build`, local mobile/desktop browser checks, zero browser console errors, and authenticated Vercel preview API/HTML checks passed.

## Current Task - 2026-06-25 - Small thumbnail restaurant cards preview

Worktree: `/Users/indegser/Github/tastyroad-worktrees/latest-video-sort`
Branch: `codex/latest-video-sort`
Target: Vercel preview

- [x] Read repository guide, lessons, Next.js guidance, browser guidance, and release workflow.
- [x] Reuse the existing latest-video-sort worktree for the related listing change.
- [x] Add representative video thumbnail and upload metadata to restaurant results.
- [x] Implement the small-thumbnail card layout without redundant visible labels.
- [x] Verify build, local API, and mobile/desktop browser layout.
- [x] Commit, push, and verify the Vercel preview deployment.
- [x] Record review/result notes.

### Review

- Changed restaurant cards to a compact small-thumbnail layout: video title and thumbnail link to YouTube, source metadata shows YouTube-style relative upload age, and address links keep only a compact `지도` action.
- Added representative video thumbnail and upload timestamp fields to restaurant results while preserving latest representative video sorting.
- Kept must-taste rows visible as rank, menu, timestamp, and quote without adding visible labels such as `추천 이유`.
- Verification: `git diff --check`, `pnpm run build`, local API sample, local mobile/desktop browser checks, zero browser console errors, and authenticated Vercel preview API/HTML checks passed.

## Current Task - 2026-06-25 - Sort restaurants by latest video upload

Worktree: `/Users/indegser/Github/tastyroad-worktrees/latest-video-sort`
Branch: `codex/latest-video-sort`

- [x] Read repository guide and lessons.
- [x] Create an isolated worktree for the listing sort change.
- [x] Inspect restaurant query and rendering flow.
- [x] Change default restaurant ordering to latest representative video upload.
- [x] Verify query ordering and app build.
- [x] Record review/result notes.

### Review

- Changed the public restaurant query to sort by each restaurant's latest representative YouTube upload timestamp, then representative video row id, then restaurant id.
- Kept the existing per-restaurant representative video selection unchanged: each restaurant still uses its newest verified mention.
- Verification: `git diff --check`, direct SQLite first-page sample, `pnpm run build`, and local API check at `/api/restaurants?limit=8` passed.

## Current Task - 2026-06-25 - Document worktree env provisioning

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`

- [x] Read repository guide and lessons for worktree/Vercel env rules.
- [x] Add worktree `.env.local` provisioning guidance to `AGENTS.md`.
- [x] Verify markdown diff and record review notes.

### Review

- Added a worktree env provisioning rule to `AGENTS.md`: when a task worktree needs Vercel-managed env vars, write `<worktree>/.env.local` using `vercel env pull <worktree>/.env.local --yes --cwd /Users/indegser/Github/tastyroad`.
- The rule explicitly avoids running `vercel env pull` from an unlinked worktree and tells agents to preserve existing env files when overwrite safety is unclear.
- Verification: `git diff --check` passed for `AGENTS.md`, `tasks/todo.md`, and `tasks/lessons.md`.

## Current Task - 2026-06-25 - Add Webshare proxy env to Vercel

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`
Target: Vercel project `tastyroad`

- [x] Read repository guide, lessons, and Vercel env guidance.
- [x] Confirm local Webshare proxy variables are present without printing values.
- [x] Add Webshare proxy variables to Vercel Production, Preview, and Development.
- [x] Verify Vercel lists the Webshare proxy variables.
- [x] Pull Vercel Development env into local `.env.local`.
- [x] Record review/result notes.

### Review

- Added `WEBSHARE_PROXY_USERNAME`, `WEBSHARE_PROXY_PASSWORD`, `WEBSHARE_PROXY_DOMAIN`, `WEBSHARE_PROXY_PORT`, and `WEBSHARE_PROXY_RETRIES_WHEN_BLOCKED` to Vercel project `tastyroad`.
- Scope is Production, Preview, and Development for all five variables.
- Verification: `vercel env ls` lists all five Webshare proxy variables in all three environments as encrypted.
- Local `.env.local` was refreshed from Vercel Development and now includes Supabase, Blob, Postgres, Vercel OIDC, and Webshare proxy variables; values were not printed.

## Current Task - 2026-06-25 - Vercel Blob transcript migration to Supabase

Worktree: `/Users/indegser/Github/tastyroad-worktrees/vercel-blob-to-supabase-latest`
Branch: `codex/vercel-blob-to-supabase-latest`

- [x] Read repository guide, lessons, transcript ingest skill, and storage schema notes.
- [x] Create an isolated worktree for the data migration.
- [x] Add a focused Vercel Blob to Supabase Storage migration script.
- [x] Pull runtime env to a temporary untracked file and validate object read/write access.
- [x] Dry-run the migration against the 356 Vercel-backed transcript tracks.
- [x] Run the migration and update SQLite metadata only after each object pair copies.
- [x] Verify storage split, sample transcript reads, DB integrity, and build.
- [x] Record review/result notes.

### Review

- Direct Vercel Blob read with the pulled project token failed with 403 because the old `tastyroad-transcripts` store is suspended.
- Recovered the source payloads from historical SQLite at commit `2fd4de3`, which still had 390 raw transcript tracks and 117,030 timed segment rows.
- Reconstructed and uploaded the 356 remaining Vercel-backed transcript tracks into Supabase Storage using the same object pathnames, then updated `youtube_transcript_tracks.storage_provider` after each raw/segment pair uploaded and read-back verification passed.
- Transcript storage is now all Supabase: `youtube_transcript_tracks` has 566 `supabase_storage` rows and 0 `vercel_blob` rows; preferred transcripts also show 566 Supabase-backed rows.
- Rebased the work onto latest `origin/main` content before the final migration run, preserving the 94 existing `video_must_taste_items` rows from `d88b89e`.
- Verified Supabase segment downloads for `1HExH6cy5BQ`, `jNE63WCLQlk`, and dash-prefixed `-BBY9hij2UI`; SQLite `pragma integrity_check` returned `ok`.
- Updated README and transcript skill docs to mark Supabase Storage as canonical and Vercel Blob as legacy recovery only.
- Verification: transcript status, Python compile, `git diff --check`, and `pnpm run build` passed after installing worktree-local dependencies. The old Vercel Blob store still exists remotely with 780 objects and remains suspended; it was not emptied or deleted.

## Current Task - 2026-06-25 - Address map link release follow-up

Worktree: `/Users/indegser/Github/tastyroad-worktrees/address-map-link`
Branch: `codex/address-map-link`
Target: production `main`

- [x] Record the user's preview-branch default for remote UI review.
- [x] Add a reusable lesson for the Vercel task-worktree auto-link pitfall.
- [x] Update the Tastyroad release skill to require linked `tastyroad` cwd for Vercel project-context commands.
- [x] Commit and push the follow-up prevention changes.
- [x] Merge the preview branch into `main` and push.
- [x] Verify the production Vercel deployment and site response.
- [x] Clean up the task worktree if safe.

### Review

- Merged `codex/address-map-link` into `main` with fast-forward commits through `cca6361`.
- Production deployment `tastyroad-mz0y2hefv-jaekwon-hans-projects.vercel.app` reached `READY`.
- Verified `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned HTTP 200 with one item and a `mapUrl`.
- Verified production HTML contains `.address-map-link` and `지도에서 보기`, with zero restaurant-card `<dt>지역</dt>` or `<dt>지도</dt>` rows.
- Removed `/Users/indegser/Github/tastyroad-worktrees/address-map-link` after confirming it was clean and pushed.

## Current Task - 2026-06-24 - Address map link cleanup

Worktree: `/Users/indegser/Github/tastyroad-worktrees/address-map-link`
Branch: `codex/address-map-link`

- [x] Read repository guide, lessons, and Next.js skill guidance.
- [x] Create an isolated worktree for the public listing UI change.
- [x] Inspect restaurant card metadata rendering and related styles.
- [x] Remove redundant visible region metadata from restaurant cards.
- [x] Combine address display with the map link where a map URL exists.
- [x] Verify build/layout and record review notes.

### Review

- Removed the visible restaurant-card `지역` row and the separate `지도` row.
- Changed the `주소` row so map-verified restaurants expose one address link with `지도에서 보기`; restaurants without a map URL still show plain address text.
- Added compact wrapping styles for the address/map link and an explicit accessible label.
- Verification: `git diff --check`, `pnpm run build`, agent-browser desktop/mobile checks, no browser error overlay, no `지역`/`지도` card rows, address map links present, and no mobile horizontal overflow.

## Current Task - 2026-06-24 - Must-taste label weed removal

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`
Target: production `main`

- [x] Read repository guide, lessons, Next.js guidance, browser guidance, and release workflow.
- [x] Inspect current must-taste markup and visible label styles.
- [x] Remove the visible must-taste section label while keeping an accessibility label.
- [x] Update the reusable lesson away from visible must-taste titles.
- [x] Verify desktop/mobile layout and build.
- [x] Prepare intended changes for production release.

### Review

- Removed the visible must-taste title; the section now relies on rank-led menu rows, transcript quotes, and grouping.
- Kept accessibility context with `aria-label="추천 메뉴"` on the section.
- Removed unused `.section-label` styling.
- Verification before release: desktop and mobile agent-browser checks for `?q=1966정원`, no old visible title text, no mobile overflow, `git diff --check`, and `pnpm run build`.

## Current Task - 2026-06-24 - Must-taste layout tune

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`

- [x] Read repository guide, lessons, and relevant browser/Next.js skill guidance.
- [x] Inspect current must-taste rendering and data cases with two or more items.
- [x] Verify the awkward layout in browser on desktop and mobile.
- [x] Tighten the must-taste item layout without changing data semantics.
- [x] Verify build and browser layout after the change.
- [x] Record review/result notes.
- [x] Iterate on the visual treatment and naming for the must-taste section.
- [x] Re-check two-item examples after each design pass.
- [x] Finalize the design and verify build/browser layout.

### Review

- Root cause: the restaurant-card divider selector `.restaurant-list li + li` also matched nested must-taste `<li>` elements, so the second menu inherited a large top gap, border, and inset shadow.
- Changed restaurant list spacing/divider rules to direct-child selectors (`.restaurant-list > li`) so nested lists use only their own compact spacing.
- Verification: desktop and mobile agent-browser screenshots for `?q=1966정원`, DOM checks confirmed no nested border/padding/box-shadow, mobile overflow check passed, `git diff --check` passed, and `pnpm run build` passed.
- Iterated the presentation into a compact rank-led menu block with transcript quote text and subtle separators between multiple items.
- Rechecked two-item examples `1966정원` and `학곡리막국수닭갈비` on mobile, plus the desktop `1966정원` view; no horizontal overflow.

## Current Task - 2026-06-24 - Design weed cleanup

Worktree: `/Users/indegser/Github/tastyroad`
Branch: `main`

- [x] Read repository guide, lessons, and Next.js skill guidance.
- [x] Inspect visible copy and current facet/search layout.
- [x] Remove redundant instructional labels and repeated explanatory text.
- [x] Update facet UX documentation with the weed-removal principle.
- [x] Verify build and browser layout.
- [x] Record review/result notes.
### Review

- Removed visible redundant labels from the public listing: the facet rail no longer says `필터`, active chips no longer say `적용됨` or repeat field labels, the result section no longer shows a visible `맛집 목록` heading, and the search placeholder no longer repeats `검색`.
- Kept accessibility context through `aria-label`s and a visually hidden result heading.
- Added the weed-removal principle to `docs/facet-ux-philosophy.md` and a reusable lesson in `tasks/lessons.md`.
- Verification: `git diff --check`, `pnpm run build`, agent-browser PC/mobile screenshots, active condition chip check, and mobile overflow check.
- Release prep: `origin/main` was fetched, the branch was confirmed even with `origin/main`, and `pnpm run build` passed before the production commit.

## Current Task - 2026-06-24 - Sung Si-kyung must-taste continuation

Worktree: `/Users/indegser/Github/tastyroad-worktrees/sungsikyung-legacy-must-taste`
Branch: `codex/sungsikyung-legacy-must-taste`

- [x] Re-read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Scope remaining Sung Si-kyung transcript-backed restaurant-video pairs missing must-taste rows.
- [x] Extract validated must-taste artifacts for the next high-confidence Sung Si-kyung pairs.
- [x] Apply passing results to `data/tastyroad.sqlite`.
- [x] Verify stored rows, DB integrity, and app build after updates.
- [x] Record review/result notes.

### Review

- Completed must-taste extraction for the 7 remaining transcript-backed `성시경의 먹을텐데` restaurant-video pairs: `무교동 유정낙지`, `철길왕갈비살`, `별미곱창`, `망원역 몽골생소금구이`, `을지로 인천집`, `부흥축산`, and `남영동 까치네`.
- Added 12 validated must-taste rows, bringing the Sung Si-kyung scope to 19/19 transcript-backed pairs with rows and 33 total items.
- Stored results only after `apply_must_taste_result.py --dry-run` passed for all 7 artifact chains.
- Verification: SQLite `pragma integrity_check` returned `ok`; Sung Si-kyung coverage query returned `total_pairs=19`, `pairs_with_items=19`, `items=33`; `git diff --check` passed; `pnpm run build` passed.

## Current Task - 2026-06-24 - Supabase transcript archive migration

Worktree: `/Users/indegser/Github/tastyroad-worktrees/sungsikyung-legacy-must-taste`
Branch: `codex/sungsikyung-legacy-must-taste`

- [x] Read repository guide, lessons, transcript ingest skill, and Vercel/Supabase storage context.
- [x] Confirm Supabase integration env is present locally and create the private `tastyroad-transcripts` bucket.
- [x] Add Supabase Storage as a transcript object storage provider.
- [x] Update transcript read paths to use `storage_provider` for Blob/Supabase selection.
- [x] Archive legacy `video_transcripts` rows into Supabase Storage with existing unavailable provider rows replaced.
- [x] Drop the fully archived legacy table and vacuum SQLite if safe.
- [x] Verify DB integrity, storage split, Supabase transcript reads, and must-taste context preparation.
- [x] Record review/result notes.

### Review

- Added Supabase Storage support to the transcript object archive helper while preserving Vercel Blob reads/writes through `storage_provider`.
- Added `SUPABASE_STORAGE_BUCKET=tastyroad-transcripts` and `TRANSCRIPT_STORAGE_PROVIDER=supabase_storage` as non-sensitive Vercel env vars in Production, Preview, and Development, then pulled them into local `.env.local`.
- Archived all 210 legacy `video_transcripts` rows to the private Supabase `tastyroad-transcripts` bucket with `--replace-existing`, including the previously Vercel-backed Sung Si-kyung rows, then dropped the fully archived legacy table.
- Vacuumed `data/tastyroad.sqlite`; tracked DB size dropped from 22MB after migration to 11MB.
- Prepared must-taste context/coverage/chunks/task artifacts for all 19 transcript-backed Sung Si-kyung restaurant-video mappings.
- Stored 3 validated must-taste items for `대포항회집` / `OJl_XAXANH0`: `광어회`, `해삼`, `생선찜`.
- Verification: Supabase `transcripts/segments` listing returned 210 objects; Sung Si-kyung transcript coverage is 195/210 videos, all 195 Supabase-backed; `video_transcripts` table count is 0; SQLite `pragma integrity_check` returned `ok`; Python compile, `git diff --check`, and `pnpm run build` passed.

## Current Task - 2026-06-24 - Remaining map-verified transcript ingest

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-map-verified`
Branch: `codex/must-taste-map-verified`

- [x] Read repository guide, lessons, and `$tastyroad-youtube-transcript-ingest`.
- [x] Reuse the existing map-verified must-taste worktree for the same data pipeline task.
- [x] Scope remaining map-verified videos missing preferred transcripts.
- [x] Fetch missing transcripts through the Webshare/youtube_transcript_api path.
- [x] Scope newly transcript-backed restaurant-video pairs for must-taste extraction.
- [x] Run or queue must-taste extraction for newly eligible pairs.
- [x] Verify stored transcripts/results and record review notes.

### Review

- Started from 388 map-verified videos without preferred transcripts; fetched 387 successfully through the Webshare-backed `youtube_transcript_api` workflow.
- Map-verified transcript coverage is now 390/391 videos and 645/646 restaurant-video pairs. The sole remaining video is `lz91mB8kxB4` (`김사원세끼`, `청량리 고흥아줌매`), which returned `TranscriptsDisabled`.
- Preferred transcript storage now has 390 tracks and 117030 preferred timed segments for the map-verified scope.
- Scoped 634 transcript-backed map-verified restaurant-video pairs that still have no `video_must_taste_items` rows, generated must-taste context/task/coverage/chunk/pass artifacts for all 634 under `data/work/must_taste/`, and wrote `data/work/must_taste/map_verified_missing_queue.json`.
- Verification: queued context check returned `queued_pairs=634`, `missing_required_files=0`, `bad_coverage_files=0`; SQLite `pragma integrity_check` returned `ok`; `git diff --check` and `pnpm run build` passed.
- Actual menu result rows were not fabricated for the 634 newly queued pairs; the strict must-taste pass artifacts still need attention events, candidates, reviews, arbiter results, and `apply_must_taste_result.py` validation before DB writes.

## Current Task - 2026-06-24 - Map-verified must-taste extraction

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-map-verified`
Branch: `codex/must-taste-map-verified`

- [x] Read repository guide, lessons, and `$tastyroad-transcript-must-taste`.
- [x] Create isolated worktree for the map-verified must-taste extraction run.
- [x] Scope map-verified restaurant-video pairs with stored preferred transcripts and current must-taste coverage.
- [x] Prepare transcript contexts for missing scoped pairs.
- [x] Run the must-taste extraction passes and apply validated results.
- [x] Verify stored rows and record review/result notes.

### Review

- Scoped 646 map-verified restaurant-video pairs; 11 currently have stored preferred transcripts and are eligible for `$tastyroad-transcript-must-taste` without running transcript ingest.
- Prepared context/coverage/chunk artifacts and generated full must-taste artifact chains for all 11 eligible pairs.
- Stored validated menu results for all 11 transcript-backed map-verified pairs; pairs missing items is now 0.
- Re-ran the existing 3 pairs as well as the 8 missing pairs. `1.5닭갈비 본점` now keeps only `닭갈비`; the previous `볶음밥` row used a later same-video restaurant segment and was removed.
- Verification: all 11 `apply_must_taste_result.py --dry-run` checks passed, SQLite `pragma integrity_check` returned `ok`, scoped coverage query returned `transcript_pairs=11`, `pairs_with_items=11`, `pairs_missing_items=0`, and `pnpm run build` passed after installing dependencies from the frozen lockfile.

## Current Task - 2026-06-24 - Deploy facet UX

Worktree: `/Users/indegser/Github/tastyroad-worktrees/horizontal-facets`
Branch: `codex/horizontal-facets`
Target: production `main`

- [x] Read release skill and inspect local release state.
- [x] Fetch `origin/main` before integration.
- [ ] Commit only the facet UX and documentation changes.
- [ ] Integrate the release commit into `main` and push.
- [ ] Verify the matching Vercel deployment and production alias.
- [ ] Clean up the task worktree if safe.
- [ ] Record release result notes.

## Current Task - 2026-06-24 - PC side-rail facet UX

Worktree: `/Users/indegser/Github/tastyroad-worktrees/horizontal-facets`
Branch: `codex/horizontal-facets`

- [x] Read repository guide, lessons, and Next.js skill guidance.
- [x] Reuse the existing facet UX worktree and inspect current changes.
- [x] Rework desktop facets into a 29CM-style left rail while keeping compact mobile facets.
- [x] Document the facet UX philosophy and device split.
- [x] Verify build and browser layout.
- [x] Record review/result notes.

### Review

- Reintroduced the desktop two-column explorer layout with a 29CM-style left facet rail and results on the right.
- Kept mobile on compact `가나다 | 지역 | 채널` folded facets, with opened options rendered as a full-width panel without horizontal overflow.
- Added `docs/facet-ux-philosophy.md` covering search-first behavior, PC left-rail rationale, mobile compact facets, and rules for adding future facets.
- Updated the repository lesson for the PC/mobile facet split.
- Verification: `git diff --check`, `pnpm run build`, agent-browser PC screenshot, PC region facet open/apply, mobile initial state, mobile region facet open, and mobile overflow check.

## Current Task - 2026-06-24 - Horizontal collapsed facets

Worktree: `/Users/indegser/Github/tastyroad-worktrees/horizontal-facets`
Branch: `codex/horizontal-facets`

- [x] Read repository guide, lessons, and Next.js skill guidance.
- [x] Create isolated worktree for the horizontal facet UX change.
- [x] Inspect current search/facet page and styles.
- [x] Replace the vertical facet rail with horizontal collapsed categories.
- [x] Verify build and browser layout.
- [x] Record review/result notes.

### Review

- Changed the public facet UX from a vertical side rail to compact horizontal collapsed categories: `가나다`, `지역`, `채널`.
- Kept all facet groups closed by default, including when filters are active; active filters remain visible as chips above the facet bar.
- Merged region cluster and detail region controls into one `지역` category, with detail regions appearing after a region cluster is selected.
- Verification: `pnpm run build`, `git diff --check`, agent-browser desktop/mobile screenshots, initial closed state, opened region facet, region link navigation, no console errors, and no mobile horizontal overflow.

## Current Task - 2026-06-24 - Restaurant search facets

Worktree: `/Users/indegser/Github/tastyroad-worktrees/restaurant-search-facets`
Branch: `codex/restaurant-search-facets`

- [x] Read repository guide, lessons, and Next.js skill guidance.
- [x] Create isolated worktree for the search/facet UI work.
- [x] Inspect current restaurant query and page patterns.
- [x] Add restaurant-name 가나다 facet support to the data/query types.
- [x] Redesign the public page around search, active filters, and scalable facet groups.
- [x] Verify build and browser behavior.

- [x] Record review/result notes.

### Review

- Added public search UI backed by the existing `q` restaurant search parameter.
- Added `nameInitial` 가나다 facet support, with doubled Korean initials grouped into the base initial bucket.
- Reworked the public page into a search bar, active filter chips, a scalable details-based facet panel, and a two-column desktop layout.
- Verification: `pnpm run build`, `git diff --check`, API smoke check for `nameInitial`, agent-browser desktop/mobile screenshots, search submit, initial facet, region/detail facet, no console errors, and no mobile horizontal overflow.

## Current Task - 2026-06-24 - Transcript must-taste top3 skill

Worktree: `/Users/indegser/Github/tastyroad-worktrees/transcript-top3-skill`
Branch: `codex/transcript-top3-skill`

- [x] Convert must-taste storage and UI from video-level to restaurant-video-level.
- [x] Generate restaurant-scoped Top 3 for the first three visible site cards.
- [x] Verify schema, API, and build after restaurant-scoped results are stored.
- [x] Convert must-taste display reasons from generated phrases to direct subtitle quotes.
- [x] Tighten must-taste reasons so the phrase does not add claims beyond the cited transcript evidence.
- [x] Change must-taste extraction from exact Top 3 filling to max-3 quality-gated recommendations.
- [x] Add a visitor-persuasiveness review gate and tighten stored reasons.
- [x] Add multi-pass whole-transcript artifact pipeline with coverage, scouts, candidates, reviews, and rejections.

- [x] Read repository guide, lessons, and `$skill-creator`.
- [x] Create isolated worktree for the transcript Top 3 skill work.
- [x] Inspect and remove the old story review agents/pipeline surfaces.
- [x] Add a repo-local skill for transcript-grounded must-taste Top 3 extraction.
- [x] Update docs and app/data contracts away from story review fields.
- [x] Verify skill validation, script syntax, focused schema/query checks, and app build.
- [x] Record review/result notes.

### Review

- Added `$tastyroad-transcript-must-taste` with context preparation, strict result validation, and `video_must_taste_items` SQLite storage for transcript-grounded must-taste recommendations.
- Removed story review agents, story review JSON inputs, story table creation, and app story display/query fields.
- Updated public app cards/API to expose restaurant-scoped `mustTasteItems` from `video_must_taste_items`.
- Updated README, AGENTS, lessons, transcript ingest guidance, mapping guidance, and Naver Map sync gating to avoid story review dependencies.
- Generated and stored quality-gated recommendation rows for `1.5닭갈비 본점`, `1966정원 천성항점`, and `1969양동통닭 본점`; `1966정원 천성항점` now stores two items instead of forcing a third.
- Added visitor-persuasiveness review scoring and drivers; `우동사리` and `튀김 닭발` were excluded because they were weaker restaurant-selection reasons.
- Updated must-taste reason rules so public `reason` is a short direct subtitle quote rather than a generated explanatory sentence.
- Tightened reason guidance and the first three stored results to avoid unsupported inferred qualities such as freshness, scenery, or market atmosphere.
- Re-applied the first three visible site cards with visitor-facing reasons.
- Added whole-transcript coverage/chunk artifacts, attention event scouting, target-restaurant scope notes, candidate aggregation, per-candidate evidence/visitor reviews, and required rejection lineage before final application.
- Tightened validation so selected items must reference reviewed candidates, candidate evidence must overlap attention events, every attention event must be aggregated into a candidate, every review must cite candidate events, and every non-selected candidate must be rejected.
- Replaced awkward/high-inference reason phrases with direct subtitle quotes.
- Switched public `reason` from generated copy to short direct subtitle quotes and rendered them with quotation marks on the site.
- Expanded over-trimmed direct quotes when needed, e.g. `진짜 0.1도 안나요` -> `닭갈비구이 내 진짜 0.1도 안나요`, so the displayed quote keeps its subject.
- Verification: skill validation passed, Python compile passed, low-quality item rejection passed, weak visitor-review rejection passed, generated reason rejection passed, missing rejection/scope/candidate/review-citation lineage checks failed as expected, SQLite integrity check returned `ok`, old `video_story_reviews` table count is 0, same-video non-target restaurants have 0 must-taste rows, API returned restaurant-specific quality-gated `mustTasteItems`, and `pnpm run build` passed.

## Current Task - 2026-06-22 - YouTube transcript ingest skill

Worktree: `/Users/indegser/Github/tastyroad-worktrees/youtube-transcript-ingest-skill`
Branch: `codex/youtube-transcript-ingest-skill`

- [x] Read repository guide, lessons, and `$skill-creator`.
- [x] Create isolated worktree for the transcript ingest skill work.
- [x] Create a repo-local transcript ingest skill scaffold.
- [x] Implement Webshare-backed YouTube transcript DB ingest scripts using the existing fetch method.
- [x] Clean transcript ownership out of the existing collection/mapping pipeline schema.
- [x] Update README/skill guidance for the new transcript workflow.
- [x] Verify skill validation, script syntax, schema creation, and focused dry runs.
- [x] Record review/result notes.

### Review

- Added `$tastyroad-youtube-transcript-ingest` with Webshare-backed `youtube_transcript_api` fetch logic, transcript schema creation, source/video dry-run selection, status reporting, and preferred transcript text export.
- Added `youtube_transcript_jobs`, `youtube_transcript_tracks`, `youtube_transcript_segments`, `youtube_transcript_fetch_attempts`, `preferred_youtube_transcripts`, and `youtube_transcript_status` to `data/tastyroad.sqlite`; no transcript rows were fetched during this task.
- Removed `video_transcripts` ownership from the existing YouTube collection and restaurant mapping pipeline schemas. The old `video_story_reviews` display path was removed later by the 2026-06-24 transcript must-taste task.
- Updated README, AGENTS, and YouTube collection skill guidance so transcript ingest routes to the new skill.
- Verification: skill validation passed, Python compile passed, transcript status/dry-run worked for `ttoganjip`, temporary pipeline schema checks confirmed no `video_transcripts` table creation, `git diff --check` passed, and SQLite integrity check returned `ok`.

## Current Task - 2026-06-21 - 또간집 지도 검증

- [x] Read repository guide, lessons, and map verification skill.
- [x] Create isolated worktree `/Users/indegser/Github/tastyroad-worktrees/ddoganjip-map-verification` on `codex/ddoganjip-map-verification`.
- [x] Scope all collected `또간집` videos and current mapping readiness.
- [x] Generate or inspect restaurant/place candidates from video metadata and external source-backed listings.
- [x] Verify concrete Naver Map place IDs and promote valid mappings.
- [x] Verify residual statuses, blank Naver ID checks, and app build.
- [x] Record review/result notes.

### Notes

- Direct Naver HTTP search requests fell into ncaptcha/no-result flows.
- Logged-in Edge CDP works for Naver Map search and place detail extraction; sample EP.103 IDs verified: `다락가든=17341605`, `홍가네순대=13416013`, `팔복순대 논산본점=21019320`, `함지박=17333463`.

### Review

- Promoted 287 `또간집` video-place mappings with numeric Naver Map IDs across the source.
- Final source status: `mapping_verified=90`, `not_applicable=9`, `mapping_partial=1`.
- The only partial video is EP.74 신림: `목포수산` and `오삼숙이` are mapped, while transcript-mentioned `별장` remains `needs_review` because its historical Naver ID resolves to a deleted/unavailable detail page.
- Verification: no restaurant has a blank `naver_map_id`, no Naver place link is a search URL, and `pnpm run build` passed after installing dependencies from the frozen lockfile.

## Current Task - 2026-06-21 - 최자로드 채널 영상 수집

Worktree: `/Users/indegser/Github/tastyroad-worktrees/choizaroad-source-collection`
Branch: `codex/choizaroad-source-collection`

- [x] Read repository guide, lessons, and YouTube collection skill.
- [x] Confirm the official `최자로드` channel and channel ID.
- [x] Add the `최자로드` source configuration without disturbing existing sources.
- [x] Run full-channel collection for the new source.
- [x] Verify DB/raw output counts and record the result.

### Review

- Added `choizaroad` as an A-tier YouTube source for the official `CHOIZA ROAD - 최자로드` channel (`UCYdUe6y0F8TQS6siNVS7QMw`).
- Collected 34 restaurant-focused videos into `data/raw/youtube/choizaroad.json` and `data/tastyroad.sqlite`; the 2 audit misses are intentional exclusions: `배부른 소리` and `커밍순`.
- Verification: source JSON validation passed, raw JSON has 34/34 complete detail rows, DB has 34 `최자로드` videos with 0 incomplete detail rows, and `pnpm run build` passed after installing dependencies in the new worktree.

## Current Task - 2026-06-21 - 최자로드 레거시 시즌 판단

- [x] Re-read repository guide, lessons, and YouTube collection skill.
- [x] Inventory legacy `최자로드` playlists and overlap with the official channel.
- [x] Decide whether to collect legacy seasons as the same source or separate sources.
- [x] Implement the chosen collection shape and collect legacy videos if warranted.
- [x] Verify DB/raw output counts and record the result.

### Review

- Decision: keep legacy `최자로드` seasons under the same `choizaroad` source, not separate per-season sources, because they are the same program and separate sources would fragment mapping/status display.
- Added `playlist_urls` support so a source can collect its channel plus multiple official playlists; updated the audit script to use the same title filters and skip unavailable titleless playlist entries.
- Collected 147 `최자로드` videos across the official channel plus regular seasons 1-9. Excluded non-restaurant/utility items: `배부른 소리`, `커밍순`, `Epilogue`/`에필로그`, `BTS`, and `미공개컷`; skipped 15 titleless unavailable playlist entries.
- Verification: missing-video audit is `remote_total=147`, `local_collected=147`, `missing=0`; raw/DB have 0 incomplete detail rows; Python compile, JSON validation, and `pnpm run build` passed.

## Current Task - 2026-06-21 - Agent worktree policy

- [x] Read repository guide and accumulated lessons.
- [x] Inspect existing worktree, branch, release, and task guidance.
- [x] Add autonomous worktree creation/reuse policy to `AGENTS.md`.
- [x] Add push/deploy cleanup rules for agent-created worktrees.
- [x] Verify the instruction update and record the result.

### Review

- Added autonomous worktree creation/reuse rules to `AGENTS.md`, including branch/path conventions, reuse conditions, and no-routine-stash guidance.
- Added cleanup rules for successful push/deploy flows and connected `$tastyroad-site-release` to the worktree policy.
- Verification: `git diff --check` passed, and targeted `rg` confirmed the new worktree, cleanup, release, and lesson guidance is present.

## Current Task - 2026-06-21

- [x] Scope the full remaining `김사원세끼` source mapping work.
- [x] Make metadata-backed mapping safe to run for only `김사원세끼`.
- [x] Promote every restaurant with verified numeric Naver Map IDs.
- [x] Inspect and resolve any residual unmapped `김사원세끼` videos.
- [x] Verify DB mapping status, required Naver IDs, and app build.
- [x] Add the review result.

### Review

- Added source-scoped `김사원세끼` mapping support and safer parsing for numbered/bracket metadata.
- Promoted all Naver-ID-verifiable `김사원세끼` places: 280 videos are `mapping_verified`, 3 are `not_applicable`, 1 remains `mapping_pending` (`한일상회`, no verified Naver place ID), and 1 remains `mapping_partial` (`맛나분식`, no verified Naver place ID/address).
- Confirmed no restaurant has a blank `naver_map_id`, no public Naver place link is a search URL, and `pnpm run build` passes.

## Current Task - 2026-06-21 - 또간집 채널 영상 수집

- [x] Read repository guide, lessons, and YouTube collection skill.
- [x] Confirm the official YouTube channel and channel ID for `또간집`.
- [x] Add the `또간집` source configuration without disturbing existing sources.
- [x] Run full-channel collection for the new source.
- [x] Verify DB/raw output counts and record the result.

### Review

- Added `ttoganjip` as a playlist-backed YouTube source and collected 100 official playlist videos into `data/raw/youtube/ttoganjip.json` and `data/tastyroad.sqlite`.
- Verification: JSON validation, Python compile check, missing-video audit (`remote_total=100`, `local_collected=100`, `missing=0`), source count query, and `pnpm run build` all passed.
- Note: YouTube initially returned HTTP 429 for `9F9a_fFx45o` detail enrichment; this was resolved in the follow-up retry task below.

## Current Task - 2026-06-21 - Vercel 배포 상태 조회 안내 제거

- [x] Read repository guide, lessons, and release skill.
- [x] Identify why deploy runs repeatedly report the Vercel app team-scope 403 fallback.
- [x] Update release guidance to use local authenticated Vercel CLI as the primary deployment-status path.
- [x] Add a reusable lesson for future release runs.
- [x] Verify the instruction change and record the result.

### Review

- Updated `$tastyroad-site-release` so deployment status lookup skips the Vercel MCP deployment list and uses the locally authenticated Vercel CLI as the normal path.
- Verification: confirmed the old MCP-first/team-scope fallback wording is absent from the release skill and the CLI-first wording is present.

## Current Task - 2026-06-21 - 또간집 실패 enrich 재시도

- [x] Identify incomplete `또간집` video metadata rows.
- [x] Update reuse logic so incomplete rows are retried instead of skipped.
- [x] Retry failed enrichments without stopping on 429.
- [x] Verify incomplete row count and record the result.

### Review

- Updated full-channel reuse logic so rows missing enriched detail fields are retried instead of skipped.
- Retried `ttoganjip`; `9F9a_fFx45o` is now enriched with `published_at=2023-02-03T09:28:11+00:00`, `duration_seconds=1220`, and description text.
- Verification: Python compile passed, `또간집` incomplete detail count is 0, missing-video audit is `remote_total=100`, `local_collected=100`, `missing=0`, raw JSON has 100/100 complete detail rows, and `pnpm run build` passed.

## 2026-06-24 - Vercel Blob transcript workflow

- [x] Worktree: `/Users/indegser/github/tastyroad-worktrees/vercel-blob-transcripts`
- [x] Branch: `codex/vercel-blob-transcripts`
- [x] Read agent guide, lessons, Vercel storage guidance, and transcript skills.
- [x] Create and connect private Vercel Blob store for Tastyroad transcripts.
- [x] Add Blob-backed transcript storage helpers and SQLite metadata columns.
- [x] Update transcript ingest/export/status scripts and skill docs.
- [x] Update must-taste context preparation to read Blob-backed segments.
- [x] Verify schema migration, dry runs, Blob helper behavior, and build.

Result note: Created private Vercel Blob store `tastyroad-transcripts` (`store_0Bd8YrIAPENYUcGE`) and connected it to the `tastyroad` Vercel project. Added `BLOB_STORE_ID` for production, preview, and development, and verified private Blob upload/download/delete with both Vercel CLI and the new Python helper. Updated transcript ingest to store raw/segment payloads in Blob by default, keep SQLite metadata, support existing SQLite cache fallback, and provide an archive/prune script for existing transcript payloads. Verification: Python compile, temp-DB schema migration, fetch dry-run, archive dry-run, fake upsert paths, must-taste context smoke test, Blob helper healthcheck, `git diff --check`, and `pnpm run build` passed. `data/tastyroad.sqlite` was restored to no diff; no Blob test files remain.

## 2026-06-24 - Archive existing transcripts to Vercel Blob

- [x] Worktree: `/Users/indegser/Github/tastyroad-worktrees/blob-transcript-archive`
- [x] Branch: `codex/blob-transcript-archive`
- [x] Read agent guide, lessons, and `$tastyroad-youtube-transcript-ingest` instructions.
- [x] Link the worktree to the `tastyroad` Vercel project.
- [x] Pull/check Blob env and dry-run the full archive scope.
- [x] Archive existing SQLite transcript payloads to Vercel Blob and prune SQLite raw/segment payloads.
- [x] Vacuum and audit `data/tastyroad.sqlite` size/table distribution.
- [x] Verify transcript status/export, must-taste context fallback, Blob object counts, and app build.

Result note: Archived 390 existing `youtube_transcript_tracks` into the private Vercel Blob `tastyroad-transcripts` store, writing 780 Blob objects totaling 8.3MB. Pruned SQLite raw/segment payloads and ran `VACUUM`, reducing `data/tastyroad.sqlite` from 54,206,464 bytes (52MB displayed) to 19,509,248 bytes (19MB displayed). `youtube_transcript_segments` now has 0 rows, all 390 tracks have distinct `raw_blob_path` and `segments_blob_path`, and `transcript_status.py` reports archived tracks as `vercel_blob`. The legacy `video_transcripts` table remains because it contains 176 old 성시경 transcript rows without corresponding `youtube_transcript_tracks`; it is not referenced by current code but was preserved rather than dropped. Verification: archive dry-run returned target_count 0 after migration, SQLite `integrity_check` returned `ok`, Blob store reported 780 objects / 8.3MB, transcript export worked, must-taste context was rebuilt from Blob-backed segments for `fPsMKDTzqaI`/restaurant 2 with full coverage, Python compile passed, `git diff --check` passed, and `pnpm run build` passed.

## 2026-06-24 - Reuse Sung Si-kyung legacy transcripts for must-taste

- [x] Worktree: `/Users/indegser/Github/tastyroad-worktrees/sungsikyung-legacy-must-taste`
- [x] Branch: `codex/sungsikyung-legacy-must-taste`
- [x] Read agent guide, lessons, release, transcript ingest, and must-taste skill instructions.
- [x] Inspect legacy `video_transcripts` structure and decide whether it can become timed Blob-backed tracks.
- [x] Add a safe migration path for reusable legacy Sung Si-kyung transcripts into Vercel Blob.
- [x] Scope mapped Sung Si-kyung restaurant/video pairs that can now run must-taste.
- [ ] Run the legacy archive after Vercel Blob store `tastyroad-transcripts` is active.
- [ ] Run the `$tastyroad-transcript-must-taste` workflow for a focused verified subset after Blob reads are available.
- [ ] Verify DB integrity, Blob archive status, must-taste validation, and build.

Result note: Added `archive_legacy_video_transcripts.py` to convert reusable timed rows from `video_transcripts` into Blob-backed `youtube_transcript_tracks`, and fixed `transcript_blob_store.py` for the current Vercel CLI auth flag order (`vercel blob --rw-token ... put/list/get`). Dry-run selected the expected 176 성시경 legacy rows. Actual archive and must-taste context preparation are blocked because Vercel reports Blob store `tastyroad-transcripts` (`store_0Bd8YrIAPENYUcGE`) as `Status: Suspended`, `Billing State: Inactive`; `blob put` and `blob get` fail while `blob list-stores` shows 780 existing objects / 8.3MB.

## Current Task - 2026-06-25 - Fill remaining must-taste and deploy

- [x] Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-fill-release`
- [x] Branch: `codex/must-taste-fill-release`
- [x] Read agent guide, lessons, `$tastyroad-transcript-must-taste`, and `$tastyroad-site-release`.
- [x] Scope current transcript-backed public restaurant-video pairs missing must-taste rows.
- [x] Restore transcript archive environment access for the task worktree without committing secrets.
- [x] Prepare must-taste contexts for the selected remaining pairs.
- [x] Generate full skill artifacts and apply only validation-passing must-taste results.
- [x] Verify DB integrity, coverage counts, and app build.
- [ ] Commit/push through the production release flow and verify the deployed site.

Result note: Added 45 validation-passing must-taste rows for 20 Supabase-backed 김사원세끼 restaurant-video pairs. Total must-taste coverage is now 50 restaurant-video pairs and 94 menu items. The remaining transcript-backed missing scope is 595 Vercel Blob-backed pairs, currently blocked by Blob 403 reads during context preparation. Verification so far: all 20 `apply_must_taste_result.py --dry-run` checks passed, actual apply stored the rows, SQLite `integrity_check` returned `ok`, and `pnpm run build` passed.
## Current Task - 2026-07-26 - Must-taste token reduction with quality benchmark

Worktree: `/Users/indegser/Github/tastyroad-worktrees/must-taste-token-quality-benchmark`
Branch: `codex/must-taste-token-quality-benchmark`

- [x] Inspect the current must-taste workflow, prior token findings, and existing prefilter benchmark.
- [x] Add a frozen DB-backed baseline exporter for previously completed videos.
- [x] Add deterministic candidate-vs-baseline quality comparison and blind review artifacts.
- [x] Add Codex session token accounting for before/after comparisons.
- [x] Update the video-first workflow to minimize repeated whole-transcript turns without weakening coverage.
- [x] Verify scripts against stored results and representative existing artifacts.
- [x] Record final review/result notes.

### Review

- Added a two-semantic-response video workflow: one full compact-block candidate-finding response, then one candidate-local combined review/final-selection response. `materialize_must_taste_video_bundle.py` deterministically expands exact segment metadata, writes ordinary pair artifacts, and runs the existing validator without writing SQLite.
- Added DB-backed baseline export, deterministic menu/evidence/copy comparison, automatic thresholds, blind A/B review artifacts for changed pairs, and Codex rollout token accounting. Token reports can be attached to the same quality comparison.
- Exported a 30-pair/68-item Sung Si-kyung baseline successfully. A four-video/seven-item existing-result comparison passed with 100% menu recall, 100% exact/near evidence recall, all candidate artifacts valid, and no blind-review differences.
- Re-materialized an existing video through the compact bundle path, passed the normal result validator, passed DB dry-run, and matched its frozen baseline at 100%.
- Historical rollout telemetry reproduced the prior pairwise-to-video-first improvement: pair-normalized logical input `1,268,870 -> 92,013` (`92.75%` lower), uncached input `52,742 -> 5,491` (`89.59%` lower), and output `15,884 -> 895` (`94.37%` lower). This is the comparison baseline for measuring the new two-response workflow, not a claim about a new production run.
- Fixed `apply_must_taste_result.py --dry-run` to open SQLite read-only. A direct tracked-DB dry-run preserved the exact SHA-256 before and after.
- Verification: four unit tests, Python compilation for all must-taste scripts, compact video context generation, bundle materialization, normal artifact validation, quality comparison pass/fail smoke tests, tracked-DB read-only hash check, and `git diff --check`.

## Follow-up - 2026-07-26 - Three-video semantic A/B trial

- [x] Limit the trial to three representative existing videos.
- [x] Freeze their current DB results before fresh extraction.
- [x] Run the new two-response semantic workflow without reading old result artifacts.
- [x] Materialize and validate every pair.
- [x] Compare menu/evidence/copy quality and review every changed pair blindly.
- [x] Record token and quality findings.

### Follow-up Review

- Tested 3 videos covering 5 restaurant-video pairs and 8 frozen baseline items; the fresh workflow selected 9 items and every materialized pair passed the normal validator.
- Automatic comparison found 75% item-level menu recall, 60% all-items-per-pair recall, and 100% exact/near evidence recall. The four changed pairs therefore required qualitative review instead of automatic promotion.
- Blind option review preferred the fresh candidate for all four changed pairs: it added strongly supported `선지국`, removed weaker/mixed `물가자미회` and `아구찜 볶음밥`, and surfaced three independently praised 참치 options. Public copy was consistently shorter and clearer.
- The reviewer was the same agent that produced the fresh artifacts, so this is a controlled blind-to-assignment check, not an independent human review.
- Conservative semantic-input accounting (one old full pair context versus new full-video blocks plus findings, prompt, and ±8 exact segments) was `591,352 -> 210,574` characters, 64.4% lower. With ±4 exact segments it was 69.0% lower. These are context-volume estimates, not isolated Codex billing telemetry.

## Follow-up - 2026-07-26 - Adopt A/B quality findings

- [x] Keep the two-response video workflow as the preferred grouped-video path.
- [x] Add broad-course/component overlap guidance to combined final selection.
- [x] Require every rank, including rank 3, to meet the same strong evidence standard.
- [x] Verify prompt generation, focused tests, compilation, and repository diff.

### Adoption Review

- The combined review/final-selection prompt now rejects broad course/set plus component recommendations when they reuse substantially the same tasting evidence, unless they represent distinct visitor choices with distinct support.
- Rank 2 and rank 3 are no longer treated as slots to fill; every selected item must independently meet the rank-1 evidence standard, and overlap/weakness decisions must remain visible in `rejected_candidates`.
- Verification passed: five focused unit tests, all must-taste script compilation, and `git diff --check`.
## Current Task - 2026-08-17 - Regular source maintenance run

Worktree: `/Users/indegser/Github/tastyroad-worktrees/regular-source-maintenance-20260817`
Branch: `codex/regular-source-maintenance-20260817`
Starting `origin/main`: `d3b995b0c43c249acd8aa633261618327706ed64`
Preserved unrelated checkouts: shared main checkout and all existing worktrees were left untouched; the starting automation checkout was clean and detached at the same commit.

- [x] Read automation memory and inspect repository/worktree state.
- [x] Fetch origin and create a clean dedicated worktree from current `origin/main`.
- [x] Reread `AGENTS.md`, `tasks/lessons.md`, automation skill, and repository automation prompt.
- [x] Pull worktree env from the linked main checkout and run pre-maintenance Supabase gate.
- [x] Run the non-dry deterministic maintenance runner and inspect the scoped work queues.
- [x] Follow every owning skill required by mapping, transcript, and must-taste queues.
- [x] Recalculate the original release scope and verify hard publishing gates.
- [x] If deploy-ready, repeat Supabase gate, build, release, verify production API, and sync Naver Map.
- [x] Record final verification, release/sync outcome, and automation memory.

Result so far: Started from `origin/main` `d3b995b0c43c249acd8aa633261618327706ed64`. Live collection found zero new video IDs and refreshed metadata for four known videos. The original work queue had no mapping or transcript items and 25 must-taste pairs: 14 previously reviewed insufficient-evidence artifacts revalidated cleanly, and 11 newly surfaced 김사원세끼 pairs completed the full transcript workflow. The 11 pairs produced 28 items and passed individual and combined dry-runs before sequential apply. Scoped report `data/work/regular_source_automation/regular_source_automation_20260816T221820Z.json` has `deploy_ready=true` with zero blockers; remaining must-taste backlog is non-blocking follow-up work.

Verification so far: Supabase Marketplace `supabase-aqua-engine` was `Available` before maintenance and immediately before release. SQLite integrity is `ok`; verified restaurants with blank or nonnumeric Naver IDs are both `0`; `git diff --check`, `pnpm install --frozen-lockfile`, and `pnpm run build` passed. Ten unrelated dirty worktrees were audited and left untouched.

Release/sync note: Pushed production maintenance commit `44ac4c97a559e0ad165a775ba7b8cbc989571666`; GitHub-triggered Vercel deployment `https://tastyroad-jhcgjc6rt-jaekwon-hans-projects.vercel.app` reached `READY` and serves the production aliases. `https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true` returned HTTP 200 with an `items` array, and live checks confirmed the new 구복만두 and 뒤푸리 menu recommendations. The final report's release-scope restaurant list is empty, so the Naver Map phase completed as a zero-place no-op (`planned=0`, `processed=0`, `saved=0`, `failed=0`) without opening a browser or attempting a save.
