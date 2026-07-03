---
name: tastyroad-regular-source-automation
description: Orchestrate recurring Tastyroad source maintenance through Codex app Automation. Use when setting up or running scheduled checks for all enabled YouTube sources, collecting new videos, ingesting missing transcripts, performing deterministic map-candidate resolution, preparing must-taste work queues, deciding whether release gates pass, and invoking the Tastyroad release workflow only after all data gates are clean.
---

# Tastyroad Regular Source Automation

## Overview

Use this skill for Codex app Automation runs that keep Tastyroad current across all enabled YouTube sources. This is a hybrid workflow:

- Scripts handle repeatable source collection, transcript ingestion, deterministic map candidate resolution, gate checks, and reports.
- Codex handles ambiguous Naver place verification and transcript-grounded must-taste extraction by using the owning Tastyroad skills.
- Deployment happens only after all gates pass and `$tastyroad-site-release` has been followed.

Prefer a Codex app **standalone project automation** on a dedicated worktree. Do not use GitHub Actions for recurring Tastyroad checks unless the user explicitly asks for it or Codex Automation is unavailable.

## Automation Prompt

Use this durable prompt when creating or updating the Codex app Automation:

```text
Use $tastyroad-regular-source-automation.

Run the recurring Tastyroad source maintenance workflow for all enabled YouTube sources.
Use a dedicated automation worktree.

First run the deterministic runner in dry-run/report mode. If there are no new videos and no actionable blockers, archive the run with a short no-op report.
If new videos exist, collect them, ingest missing transcripts, run deterministic map candidate processing, and prepare the must-taste work queue.

For any unresolved Naver place mapping or must-taste item, use the owning Tastyroad skills to resolve it:
- $tastyroad-map-video-restaurants for ambiguous place verification.
- $tastyroad-transcript-must-taste for transcript-grounded menu/reason extraction.

Deploy only when every gate is clean:
- no new collected video remains mapping_pending or mapping_partial,
- no mapped transcript-backed restaurant-video pair lacks must-taste rows,
- transcript ingestion did not fail for newly collected videos,
- pnpm run build passes.

If any gate remains blocked, do not deploy. Leave a concise Triage finding with exact source/video IDs, blockers, and next command or skill to run.
```

Recommended cadence: daily at a stable morning time in Asia/Seoul. Add a weekly or manual full-channel audit run when missed historical uploads are a concern.

## Workflow

1. Inspect the run plan without mutating data:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py --dry-run
```

2. Run the deterministic maintenance stages:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py
```

Use `--full-channel` for a weekly/manual audit:

```bash
python3 .codex/skills/tastyroad-regular-source-automation/scripts/run_regular_source_automation.py --full-channel
```

3. Read the report printed by the runner and the JSON report under `data/work/regular_source_automation/`.

4. If gates are blocked, use the owning skill:

- Mapping blockers: `$tastyroad-map-video-restaurants`
- Transcript blockers: `$tastyroad-youtube-transcript-ingest`
- Must-taste blockers: `$tastyroad-transcript-must-taste`

5. Re-run the deterministic runner after resolving blockers. When the report says `deploy_ready: true`, follow `$tastyroad-site-release`.

## Rules

- Do not deploy from a scheduled automation when any gate is blocked.
- Do not add restaurants without numeric `naver_map_id`.
- Do not apply must-taste rows unless `apply_must_taste_result.py --dry-run` passes and the extraction followed `$tastyroad-transcript-must-taste`.
- Do not let parallel agents write SQLite, Naver Map saved lists, or deployment state.
- Keep automation work in a dedicated worktree. Preserve unresolved artifacts under ignored `data/work/`.
- Report no-op runs briefly; report blocked runs with exact video IDs and the next skill/command.
