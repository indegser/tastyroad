Use $tastyroad-regular-source-automation.
Use $tastyroad-site-release for the final production release.

Run the recurring Tastyroad source maintenance workflow for all enabled YouTube sources.
Use a dedicated automation worktree.

Always run the non-dry deterministic runner so YouTube is actually queried:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py
```

Never use `--dry-run` to decide that there are no new videos. Dry-run only plans commands and reports `new_video_detection.status=not_checked`.

Read `data/work/regular_source_automation/latest.json`.

If `new_video_count=0`, there are no tracked changes, and all work queues are empty, archive the run with a short no-op report.

For every item in `work_queues.map_verification`, use `$tastyroad-map-video-restaurants`. A `mapping_pending` or `mapping_partial` result is a hard blocker. A metadata-poor `mapping_review` item may remain a warning only after a concrete web-search review records that no safe place match is available. Verified restaurants require a numeric Naver place ID.

For every item in `work_queues.transcript_ingest`, use `$tastyroad-youtube-transcript-ingest`. Transcript failures remain warnings after a concrete retry.

For every item in `work_queues.must_taste_validation`, use the complete `$tastyroad-transcript-must-taste` workflow. Validate every result with `apply_must_taste_result.py --dry-run` before the single-process apply. Insufficient transcript evidence may produce zero items and remains a warning.

After review work, recalculate the original release scope without collecting again:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py \
  --skip-collect \
  --skip-map \
  --skip-naver-resolution \
  --skip-transcripts \
  --scope-report data/work/regular_source_automation/<original-report>.json
```

Release only when the scoped report has:

- `gates.deploy_ready=true`,
- zero hard mapping blockers (`mapping_pending` or `mapping_partial`),
- SQLite `integrity_check=ok`,
- no public verified restaurant with a blank Naver place ID,
- no failed non-transcript maintenance command.

Then run `pnpm run build`, commit only intended tracked files, integrate the intended commit into production `main`, push `main`, wait for the matching GitHub-triggered Vercel deployment to reach `READY`, and verify the production restaurants API. Do not use direct `vercel deploy`.

Report new video IDs, mapping decisions, taste-menu results, transcript warnings, production commit, deployment URL/status, and production API verification.
