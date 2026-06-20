# Task Log

Use this file for active non-trivial work. Keep entries short and checkable.

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
