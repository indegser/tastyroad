# Task Log

Use this file for active non-trivial work. Keep entries short and checkable.

## Current Task - 2026-06-25 - Small thumbnail restaurant cards preview

Worktree: `/Users/indegser/Github/tastyroad-worktrees/latest-video-sort`
Branch: `codex/latest-video-sort`
Target: Vercel preview

- [x] Read repository guide, lessons, Next.js guidance, browser guidance, and release workflow.
- [x] Reuse the existing latest-video-sort worktree for the related listing change.
- [x] Add representative video thumbnail and upload metadata to restaurant results.
- [x] Implement the small-thumbnail card layout without redundant visible labels.
- [x] Verify build, local API, and mobile/desktop browser layout.
- [ ] Commit, push, and verify the Vercel preview deployment.
- [ ] Record review/result notes.

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
