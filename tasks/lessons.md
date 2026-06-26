# Lessons

Durable lessons for future coding agents in this repository.

Add an entry when the user corrects the agent or when a repeated mistake pattern is discovered. Keep lessons actionable, dated, and specific enough to change future behavior.

## 2026-06-26

- Trigger: The user questioned why many rows still lacked taste after the agent said it had run the must-taste skill.
  Rule: Report must-taste progress by exact applied restaurant-video pairs and remaining counts; do not imply that preparing contexts or running a small reviewed batch means the full remaining scope has been extracted and stored.
- Trigger: The agent used internal terms like scout/review without clarifying they are stages inside `$tastyroad-transcript-must-taste`, confusing them with separate skills.
  Rule: Describe must-taste work as stages inside the one skill, using plain terms such as candidate-finding stage, candidate-review stage, final-selection stage, and validation/apply script; do not present internal stage labels as separate skills.
- Trigger: A deterministic must-taste extractor passed artifact validation but produced semantic false positives from ordering-only, comparison, and wrong-restaurant transcript moments.
  Rule: Do not apply heuristic-generated must-taste rows just because `apply_must_taste_result.py --dry-run` passes; semantic review or the full skill extraction workflow is required before DB writes.

## 2026-06-25

- Trigger: The user clarified that the oversized address issue was specifically the visible `지도` action text, not the whole address row.
  Rule: For visual feedback on a card sub-element, identify and adjust the named element first instead of broadening the change to adjacent content.
- Trigger: Running `vercel curl` from an unlinked task worktree created and linked an unintended Vercel project named after the worktree.
  Rule: For Vercel commands that need project context beyond `vercel ls/inspect`, run from the linked main checkout or pass a known linked cwd; verify `.vercel/project.json` points to `tastyroad` before commands that can link, create, or mutate projects.
- Trigger: A Vercel Blob CLI failure traceback included the subprocess argv with `--rw-token`.
  Rule: Scripts that invoke CLIs with secrets in argv must suppress exception chaining or redact command arguments before raising/logging errors.

- Trigger: Must-taste selector prompt tests got worse when instructions were tightened around clipped endings.
  Rule: For must-taste `reason`/`repaired_reason`, prefer a balanced source-window selector plus flexible subtitle editor; test prompt changes against DB-backed samples before adding narrow rules, because "not too short" over-expands into setup while "narrowest" collapses back to flat snippets.
- Trigger: Must-taste normalization prompt drifted from source-preserving subtitle repair into analyst-style summary prose.
  Rule: For must-taste display copy, treat repaired text as a minimally edited subtitle quote: preserve source wording/order/voice, only fix fragment boundaries and clear ASR/readability issues, and avoid report phrases such as `반응입니다` unless the source cannot be repaired directly.
- Trigger: Blind `codex exec` testing showed a source-preserving repair prompt can still leave clipped ASR fragments such as dangling endings, duplicated conditionals, and unrelated asides.
  Rule: Must-taste repaired display text needs a flexible subtitle-editor prompt and enough raw context; avoid turning every observed failure into another validation gate.
- Trigger: A blind must-taste repair run self-labeled broken outputs as `pass` even after the prompt named the bad patterns.
  Rule: Do not ask the model to self-label repair quality; keep `repaired_reason` as the editor output and judge examples by reading the copy.
- Trigger: The user rejected a solution that made the skill depend on model self-gating labels instead of the simpler human-like editing behavior that worked initially.
  Rule: Do not put model self-evaluation fields such as `repair_quality_gate` in final must-taste items; final selection should simply require a validator-passing `repaired_reason`, and candidates that cannot produce one after source-context reselection should move to `rejected_candidates`.
- Trigger: A source-window repair retest showed that requiring "complete Korean copy" made the model invent predicates such as `않습니다`, `들어갑니다`, or `입니다` for clipped subtitle tails.
  Rule: For must-taste repaired display copy, allow natural quote-like phrases when they preserve source text better; prefer deleting/narrowing clipped tails over inventing a finite ending not anchored in the raw reason.
- Trigger: The user corrected repeated attempts to add repaired-copy gates and asked for the original flexible thinking as a prompt instead.
  Rule: For must-taste repaired display copy, do not build a pile of allow/deny gates. Use a concise subtitle-editor role prompt: lightly repair the raw subtitle, preserve tone/order/wording, avoid summary/ad prose, and edit less when uncertain.

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
- Trigger: Vercel env vars were added remotely, but the linked main checkout's `.env.local` still lacked the new values for the next agent session.
  Rule: After adding or changing Vercel env vars, run `vercel env pull .env.local --yes` from the linked `tastyroad` checkout when it is safe to overwrite local env, then verify required keys without printing values.
- Trigger: Running a schema helper's `main()` during verification altered tracked `data/tastyroad.sqlite`.
  Rule: For schema smoke tests, copy the DB to `/tmp` and import/call the schema function with an explicit temp path; do not run root-default schema CLIs against tracked data unless updating the DB is intentional.
- Trigger: The user defined design "weeds"/`잔디` as redundant visible words such as labeling an already familiar filter area as `필터` or a menu quote block as `추천 이유`.
  Rule: In Tastyroad UI work, remove visible explanatory labels when the layout/control pattern already carries the meaning; keep accessible labels for assistive technology.
- Trigger: The must-taste list inherited restaurant-card divider spacing because `.restaurant-list li + li` matched nested list items.
  Rule: Scope restaurant list spacing/divider selectors to direct children (`.restaurant-list > li`) so nested content lists keep their own layout.
- Trigger: The user pointed out that even `먼저 맛볼 메뉴` was visible copy repeating the ranked menu block's meaning.
  Rule: Do not show a must-taste section title when rank-led rows, menu names, quotes, and grouping already carry the meaning; keep only an accessibility label and verify a multi-item example.
- Trigger: The user works remotely and cannot reliably inspect local `localhost` URLs shared by agents.
  Rule: For public UI changes, use a feature/preview branch as the default remote review path after local verification; do not ask before pushing a preview branch unless the change is risky or explicitly local-only.
- Trigger: Vercel Blob uploads failed when auth flags were appended after `put`/`list` subcommand arguments.
  Rule: With current Vercel CLI, pass Blob auth flags such as `--rw-token` or `--oidc-token --store-id` immediately after `vercel blob` and before the subcommand.
- Trigger: Vercel Blob became suspended while legacy `video_transcripts` still held recoverable timed captions.
  Rule: Keep transcript object storage provider configurable, prefer the private `tastyroad-transcripts` Supabase Storage bucket for the current archive path, and use `--replace-existing` before dropping legacy rows when existing tracks point at an unavailable provider.
- Trigger: `apply_patch` created generated must-taste artifacts in the shared main checkout while the active task was running in a dedicated worktree.
  Rule: When editing files for a task-specific worktree, pass absolute worktree paths to `apply_patch` or verify the file location before validation; clean up any files accidentally created in the shared checkout.

- Trigger: Running schema/context preparation helpers during verification altered tracked `data/tastyroad.sqlite`.
  Rule: For schema smoke tests or read-only transcript context experiments, copy the DB to `/tmp` or pass an explicit temp path; do not run root-default schema/context CLIs against tracked data unless updating the DB is intentional.
- Trigger: The user defined design "weeds" as redundant visible words such as labeling an already familiar filter area as `필터`.
  Rule: In Tastyroad UI work, remove visible explanatory labels when the layout/control pattern already carries the meaning; keep accessible labels for assistive technology.

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
