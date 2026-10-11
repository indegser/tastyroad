# Subtitle voice repair — 2026-10-11

## Scope and decisions

All 3,223 stored menu display quotes were audited across video formats. Three disjoint audit partitions covered every row ID exactly once; source comparisons used stored raw reasons and evidence packs. All proposed repairs and disputed cases received a separate semantic review. The sequential arbiter accepted 161 copy repairs across 94 videos and 119 restaurants; 3,062 menu rows were preserved byte-for-byte. Fourteen proposed changes were rejected as unnecessary direct-speech rewrites. Existing formal source speech and the normal newest-video controls are unchanged.

The earlier Tsujihan diagnosis and prompt experiments are in the parent report. The release includes the narrowly scoped skill/prompt guidance and a manifest-driven repair helper. No ban on formal endings, Shorts-wide replacement, menu reselection, schema change, or public-site code change was introduced.

## Evidence and limits

`manifest.json` records before/after text, raw source, source quote, frozen row fingerprints, review decisions and complete audit IDs. The three audit/review artifacts retain rejected and disputed decisions. English-caption cases use faithful Korean direct speech so the public language remains Korean. The arbiter also verified final conservative trims for 1501/2398 after the independent reviewer read their longer drafts; other draft changes 3553/3562 match the reviewer's final revisions.

Item 1508 previously had a course-highlight summary unsupported by its stored fragments. Its display is now the clear anticipatory source quote “맛있겠다.” rather than an invented tasting assessment. Its existing menu selection and evidence are preserved. Other potential ASR or grounding issues recorded in doubt reviews are separate from narrator-voice drift and remain unchanged; this is not a fresh extraction or a claim that every legacy recommendation has been revalidated.

## Verification

All reviewers finished before the helper dry-run and sequential apply. All 13 SQLite tables and schema were compared with the frozen baseline: only the 161 display fields and their JSON mirrors changed. IDs, menus, ranks, raw reasons, transcript tracks, timestamps, review/evidence data, other tables, and unaffected rows are unchanged. SQLite integrity is OK. Nine focused unit tests, skill validation, and production build passed. The lexical residual cross-check found three source-authentic reporting/formal expressions, all preserved; the screen was not used as an automatic style gate.

See `verification.json` for counts, hashes and current public projection coverage. Production is released through GitHub main and Vercel after the Supabase availability gate; deployment outcome is recorded in tasks/todo.md.
