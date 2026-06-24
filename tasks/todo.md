# Task Log

Use this file for active non-trivial work. Keep entries short and checkable.

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
