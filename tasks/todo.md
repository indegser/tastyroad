# Task Log

Use this file for active non-trivial work. Keep entries short and checkable.

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
