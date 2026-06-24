# Lessons

Durable lessons for future coding agents in this repository.

Add an entry when the user corrects the agent or when a repeated mistake pattern is discovered. Keep lessons actionable, dated, and specific enough to change future behavior.

## 2026-06-25

- Trigger: Running `vercel curl` from an unlinked task worktree created and linked an unintended Vercel project named after the worktree.
  Rule: For Vercel commands that need project context beyond `vercel ls/inspect`, run from the linked main checkout or pass a known linked cwd; verify `.vercel/project.json` points to `tastyroad` before commands that can link, create, or mutate projects.

## 2026-06-24

- Trigger: The user clarified that transcript post-processing should extract must-taste Top 3 items, not story prose.
  Rule: Retire `story_hook`/`story_intro`/`tasting_flow` workflows; require each must-taste item to cite an exact transcript segment and timestamp, and do not use metadata or old story prose as source evidence.
- Trigger: A video-level Top 3 design would attach the same items to every restaurant in multi-restaurant videos.
  Rule: Store and display must-taste Top 3 by restaurant-video pair (`restaurant_id` plus `youtube_video_id`), not by video alone.
- Trigger: The user corrected must-taste reasons that read like verb-ending explanatory sentences.
  Rule: Do not use generated sentence-style explanations for public display; after later correction, prefer direct subtitle quotes in `reason`.
- Trigger: The user questioned must-taste reasons that added qualities not directly supported by the cited transcript.
  Rule: Do not add atmosphere, location, freshness, market, scenery, or quality claims to `reason` unless the cited segment or immediate neighboring transcript context directly supports them.
- Trigger: The user noticed the must-taste extractor was filling three slots from weak mentions.
  Rule: Treat must-taste as maximum three quality-gated recommendations; never fill a third slot from mention/order/eating alone, and require a score plus strong signal such as explicit recommendation, repeat-visit intent, differentiator, or strong praise.
- Trigger: The user found literal transcript-backed reasons too flat for restaurant choice.
  Rule: Add a visitor-persuasiveness review gate for candidate selection; keep its judgment in `review`, not necessarily in the displayed `reason`.
- Trigger: The user clarified that natural must-taste extraction needs repeated analysis over the whole transcript, not a single pass that reacts to mentions.
  Rule: Require `coverage.json`, `chunks.json`, `attention_events.jsonl`, `menu_candidates.json`, `candidate_reviews.json`, target-restaurant scope notes, and `rejected_candidates` lineage before applying results; do not accept one-shot `result.json` outputs.
- Trigger: The user flagged awkward reason phrases such as `추천이 바로 꽂힌` and `볶음밥까지 너무 맛있는 집`.
  Rule: Avoid coined slogans or restaurant-level claims such as `맛있는 집`; if generated phrases feel awkward, use direct subtitle quotes instead.
- Trigger: The user found even low-inference generated reason phrases awkward and suggested quoting subtitles directly.
  Rule: Store public `reason` as a short exact quote from `evidence` or `supporting_evidence`; keep generated judgment in `quality.check` and `review.decision_reason`, not in the displayed text.
- Trigger: The user pointed out that over-trimmed quotes like `진짜 0.1도 안나요` lose their subject.
  Rule: Direct subtitle quotes should be long enough to keep the subject and claim understandable while remaining an exact evidence substring.
- Trigger: After exploring 29CM, the user clarified that Tastyroad should use a PC left-rail facet UX while keeping mobile-friendly compact facets.
  Rule: Treat public listing facets by device: PC may use a persistent e-commerce-style left rail, while mobile should keep compact folded chip/sheet-style entry points; document the rationale when this architecture changes.
- Trigger: Re-running must-taste extraction for map-verified restaurants found an existing item whose evidence segment belonged to a later restaurant in the same multi-restaurant video.
  Rule: Before preserving existing must-taste rows in multi-restaurant videos, verify the cited segment belongs to the target restaurant portion; re-run or reject stale items that only pass by using another restaurant's segment.
- Trigger: Must-taste context preparation failed for YouTube IDs that begin with `-` because argparse treated the ID as another option.
  Rule: When passing YouTube IDs to repo CLIs from loops, use `--video-id=<id>` rather than `--video-id <id>` so dash-prefixed video IDs are handled correctly.
- Trigger: Vercel Blob CLI upload failed after store creation because local env had `VERCEL_OIDC_TOKEN` without `BLOB_STORE_ID`.
  Rule: For Tastyroad Blob workflows, ensure `BLOB_STORE_ID` is present in Vercel project env and local `.env.local`; OIDC requires both `VERCEL_OIDC_TOKEN` and `BLOB_STORE_ID`.
- Trigger: Running a schema helper's `main()` during verification altered tracked `data/tastyroad.sqlite`.
  Rule: For schema smoke tests, copy the DB to `/tmp` and import/call the schema function with an explicit temp path; do not run root-default schema CLIs against tracked data unless updating the DB is intentional.
- Trigger: The user defined design "weeds" as redundant visible words such as labeling an already familiar filter area as `필터`.
  Rule: In Tastyroad UI work, remove visible explanatory labels when the layout/control pattern already carries the meaning; keep accessible labels for assistive technology.
- Trigger: The must-taste list inherited restaurant-card divider spacing because `.restaurant-list li + li` matched nested list items.
  Rule: Scope restaurant list spacing/divider selectors to direct children (`.restaurant-list > li`) so nested content lists keep their own layout.
- Trigger: The user pointed out that even `먼저 맛볼 메뉴` was visible copy repeating the ranked menu block's meaning.
  Rule: Do not show a must-taste section title when rank-led rows, menu names, quotes, and grouping already carry the meaning; keep only an accessibility label and verify a multi-item example.
- Trigger: The user works remotely and cannot reliably inspect local `localhost` URLs shared by agents.
  Rule: For public UI changes, use a feature/preview branch as the default remote review path after local verification; do not ask before pushing a preview branch unless the change is risky or explicitly local-only.

## 2026-06-22

- Trigger: The user clarified that new transcript ingestion should ignore legacy story compatibility but keep the existing Webshare/youtube_transcript_api fetch path.
  Rule: For Tastyroad transcript work, separate storage/schema redesign from the fetch mechanism; reuse the existing Webshare-backed youtube_transcript_api method unless explicitly told otherwise.

## 2026-06-21

- Trigger: The repository had no `AGENTS.md` or `CODEX.md`, so future agents had no project-local operating memory.
  Rule: Before non-trivial work, read `AGENTS.md` and relevant entries in this file, then track the task in `tasks/todo.md`.
- Trigger: The user clarified that Claude will not be used in this repository.
  Rule: Do not add or rely on Claude-specific files; keep persistent agent guidance in `AGENTS.md` and `CODEX.md`.
- Trigger: The user clarified that public web listing should not depend on story review completion.
  Rule: Treat collected YouTube video plus verified Naver Map restaurant mapping with a non-empty `naver_map_id` as the public listing gate; story fields are optional display content only.
- Trigger: The agent treated `tastyroad-data-pipeline` as a user-facing workflow because scripts lived there, then changed positions too reactively under user challenge.
  Rule: Build a working model before planning; separate current implementation facts from product/workflow design, and route Tastyroad work by user intent to purpose-specific skills.
- Trigger: The user asked to verify and deploy `김사원세끼` videos, but the agent only processed the latest two unreviewed videos.
  Rule: For source-level mapping requests, define and report the full source scope first; do not silently narrow work to latest videos or current backlog rows.
- Trigger: Tastyroad deployment runs repeatedly reported the Vercel app team-scope 403 before falling back to the CLI.
  Rule: For Tastyroad release status checks, skip the Vercel MCP deployment list and use the locally authenticated Vercel CLI for same-SHA deployment lookup by default.
- Trigger: A YouTube full-channel collection left one row with blank detail metadata after a 429 and later skipped it as already collected.
  Rule: Treat rows without enriched detail fields such as `published_at` or `duration_seconds` as retryable, and continue the collection run even when individual enrich attempts hit 429.
- Trigger: Concurrent repository conversations made branch switching require repeated manual stash/checkout decisions.
  Rule: Let agents route non-trivial tasks into dedicated `../tastyroad-worktrees/<slug>` worktrees and clean up only after clean, pushed, and verified outcomes.
