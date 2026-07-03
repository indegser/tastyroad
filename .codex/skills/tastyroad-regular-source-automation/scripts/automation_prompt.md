Use $tastyroad-regular-source-automation.

Run the recurring Tastyroad source maintenance workflow for all enabled YouTube sources.
Use a dedicated automation worktree.

First run:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py --dry-run
```

If there are no new videos and no actionable blockers, archive the run with a short no-op report.

If there may be new videos, run:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py
```

Then read `data/work/regular_source_automation/latest.json`.

For any unresolved Naver place mapping or must-taste item, use the owning Tastyroad skills:

- `$tastyroad-map-video-restaurants` for ambiguous place verification.
- `$tastyroad-transcript-must-taste` for transcript-grounded menu/reason extraction.

Deploy only when every gate is clean:

- no new collected video remains `mapping_pending` or `mapping_partial`,
- no mapped transcript-backed restaurant-video pair lacks must-taste rows,
- transcript ingestion did not fail for newly collected videos,
- `pnpm run build` passes.

If any gate remains blocked, do not deploy. Leave a concise Triage finding with exact source/video IDs, blockers, and next command or skill to run.
