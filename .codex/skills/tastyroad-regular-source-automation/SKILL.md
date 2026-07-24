---
name: tastyroad-regular-source-automation
description: Orchestrate recurring Tastyroad source maintenance through Codex app Automation. Use when setting up or running scheduled checks for all enabled YouTube sources, collecting new videos, ingesting missing transcripts, performing deterministic map-candidate resolution, preparing must-taste work queues, deciding whether release gates pass, and invoking the Tastyroad release workflow after hard publishing gates are clean.
---

# Tastyroad Regular Source Automation

## Overview

Use this skill for Codex app Automation runs that keep Tastyroad current across all enabled YouTube sources. This is a hybrid workflow:

- Scripts handle repeatable source collection, transcript ingestion, deterministic map candidate resolution, gate checks, and reports.
- Codex handles ambiguous Naver place verification and transcript-grounded must-taste extraction by using the owning Tastyroad skills.
- Deployment happens after hard publishing gates pass and `$tastyroad-site-release` has been followed. Missing transcripts or missing must-taste rows are follow-up warnings, not release blockers, because verified mapped restaurants should still be visible on the web.

Prefer a Codex app **standalone project automation** on a dedicated worktree. Do not use GitHub Actions for recurring Tastyroad checks unless the user explicitly asks for it or Codex Automation is unavailable.

## Automation Prompt

Use this durable prompt when creating or updating the Codex app Automation:

```text
Use $tastyroad-regular-source-automation.

Run the recurring Tastyroad source maintenance workflow for all enabled YouTube sources.
Use a dedicated automation worktree.

Always run the non-dry deterministic runner so YouTube is actually queried. Do not use `--dry-run` to decide that there are no new videos: dry-run plans commands but skips collection and therefore reports `new_video_detection.status=not_checked`.

If the actual run reports no new videos, no tracked changes, and empty work queues, archive the run with a short no-op report.
If new videos exist, collect them, ingest missing transcripts, run deterministic map candidate processing, and process the explicit mapping/transcript/must-taste work queues.

For every queued Naver place mapping, transcript warning, or must-taste warning, use the owning Tastyroad skill:
- $tastyroad-map-video-restaurants for ambiguous place verification.
- $tastyroad-youtube-transcript-ingest for transcript fetch warnings.
- $tastyroad-transcript-must-taste for transcript-grounded menu/reason extraction.

Deploy when every hard publishing gate is clean:
- no new collected video remains mapping_pending or mapping_partial,
- every verified public restaurant has a numeric Naver place ID,
- SQLite integrity_check returns ok,
- non-transcript maintenance commands did not fail,
- pnpm run build passes.

Recalculate the original release scope after semantic review with `--scope-report <original-report>`. Do not lose the new-video scope merely because a later run collects zero additional IDs.

Follow `$tastyroad-site-release` completely: commit intended changes, integrate them into production main, push main through GitHub, wait for the matching Vercel deployment to reach READY, and verify the production API.

Do not block release only because transcript ingestion failed or a mapped restaurant-video pair has validator-confirmed insufficient taste evidence. Leave concise Triage warnings with exact source/video IDs, then release verified mapped restaurants so they are visible on the web.
```

Recommended cadence: daily at a stable morning time in Asia/Seoul. Add a weekly or manual full-channel audit run when missed historical uploads are a concern.

## Workflow

1. Optional: inspect the run plan without mutating data. This cannot detect new videos:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py --dry-run
```

2. Always run the deterministic maintenance stages for the scheduled check:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py
```

Use `--full-channel` for a weekly/manual audit:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py --full-channel
```

3. Read the report and the explicit `work_queues` under `data/work/regular_source_automation/`.

4. If gates are blocked, use the owning skill:

- Mapping blockers: `$tastyroad-map-video-restaurants`
- Transcript warnings: `$tastyroad-youtube-transcript-ingest`
- Must-taste warnings: `$tastyroad-transcript-must-taste`

5. Recalculate the original scope after resolving review work:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py \
  --skip-collect --skip-map --skip-naver-resolution --skip-transcripts \
  --scope-report data/work/regular_source_automation/<original-report>.json
```

6. When the scoped report says `deploy_ready: true`, run `pnpm run build` and follow `$tastyroad-site-release`; transcript failures or validator-confirmed insufficient taste evidence can remain as follow-up warnings.

## Rules

- Do not deploy from a scheduled automation when any hard publishing gate is blocked.
- Do deploy verified mapped restaurants even when transcript or must-taste warnings remain.
- Do not add restaurants without numeric `naver_map_id`.
- Do not apply must-taste rows unless `apply_must_taste_result.py --dry-run` passes and the extraction followed `$tastyroad-transcript-must-taste`.
- Do not let parallel agents write SQLite, Naver Map saved lists, or deployment state.
- Keep automation work in a dedicated worktree. Preserve unresolved artifacts under ignored `data/work/`.
- Report no-op runs briefly; report blocked runs with exact video IDs and the next skill/command.
