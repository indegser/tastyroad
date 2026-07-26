Use $tastyroad-regular-source-automation.
Use $tastyroad-site-release for the final production release.
Use $tastyroad-naver-map-sync after production API verification succeeds.

Run the recurring Tastyroad source maintenance workflow for all enabled YouTube sources.
Use a dedicated automation worktree.

Before interpreting or running any maintenance step:

1. Fetch `origin`.
2. Ensure the run checkout is based on the current `origin/main`. Fast-forward a clean dedicated automation worktree, or create a fresh dedicated worktree from `origin/main` when the existing checkout has local changes or cannot fast-forward safely. Never discard, stash, or overwrite unrelated changes.
3. From that updated checkout, reread `AGENTS.md`, `tasks/lessons.md`, this file, and every owning skill invoked by the current work queues. Repository instructions at `origin/main` are the source of truth and supersede workflow details cached in the Codex Automation prompt.
4. Record the starting `origin/main` commit in the run report. Stop and report a checkout-sync blocker if the run cannot safely reach that commit.

The Codex Automation configuration should contain only a stable bootstrap that performs the synchronization and then delegates to this repository runbook. Do not duplicate this full runbook into the Automation configuration; future repository workflow improvements must take effect without another manual Automation prompt rewrite.

Before maintenance, run:

```bash
vercel integration list tastyroad --scope jaekwon-hans-projects
```

Require the connected `supabase-aqua-engine` resource to have status `Available`. If it is suspended, unavailable, missing, or the check fails, stop before data mutation, push, or deployment. Report the exact external-resource blocker and direct the user to the Supabase recovery dashboard. Do not retry application builds as a substitute for restoring the resource.

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

Immediately before push and deployment, repeat the Vercel integration check and require `supabase-aqua-engine` status `Available`.

Then run `pnpm run build`, commit only intended tracked files, integrate the intended commit into production `main`, push `main`, wait for the matching GitHub-triggered Vercel deployment to reach `READY`, and verify the production restaurants API. Do not use direct `vercel deploy`.

Report new video IDs, mapping decisions, taste-menu results, transcript warnings, both Supabase preflight results, production commit, deployment URL/status, and production API verification.
