Use $tastyroad-regular-source-automation.

Run the recurring Tastyroad source maintenance workflow for all enabled YouTube sources.
Use a dedicated automation worktree.

First run:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py --dry-run
```

If there are no new videos and no actionable findings, archive the run with a short no-op report.

If there may be new videos, run:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py
```

Then read `data/work/regular_source_automation/latest.json`.

For any unresolved Naver place mapping, transcript warning, or must-taste warning, use the owning Tastyroad skills:

- `$tastyroad-map-video-restaurants` for ambiguous place verification.
- `$tastyroad-youtube-transcript-ingest` for transcript fetch warnings.
- `$tastyroad-transcript-must-taste` for transcript-grounded menu/reason extraction.

Deploy when every hard publishing gate is clean:

- no new collected video remains `mapping_pending` or `mapping_partial`,
- non-transcript maintenance commands did not fail,
- `pnpm run build` passes.

Do not block release only because transcript ingestion failed or a mapped restaurant-video pair lacks must-taste rows. Leave concise Triage warnings with exact source/video IDs and the next command or skill to run, then release verified mapped restaurants so they are visible on the web.
