---
name: tastyroad-regular-source-automation
description: Orchestrate recurring Tastyroad source maintenance through Codex app Automation. Use when setting up or running scheduled checks for all enabled YouTube sources, collecting new videos, ingesting missing transcripts, performing deterministic map-candidate resolution, preparing must-taste work queues, deciding whether release gates pass, invoking the Tastyroad release workflow after hard publishing gates are clean, and syncing newly published verified restaurants into the user's Naver Map saved list after production verification.
---

# Tastyroad Regular Source Automation

## Overview

Use this skill for Codex app Automation runs that keep Tastyroad current across all enabled YouTube sources. This is a hybrid workflow:

- Scripts handle repeatable source collection, transcript ingestion, deterministic map candidate resolution, gate checks, and reports.
- Codex handles ambiguous Naver place verification and transcript-grounded must-taste extraction by using the owning Tastyroad skills.
- Deployment happens after hard publishing gates pass and `$tastyroad-site-release` has been followed. Missing transcripts or missing must-taste rows are follow-up warnings, not release blockers, because verified mapped restaurants should still be visible on the web.
- Naver Map saved-list sync happens after the production deployment and API verification succeed, using `$tastyroad-naver-map-sync`. The normal control path is the Codex Edge browser extension against the user's logged-in Microsoft Edge profile; `agent-browser` is the first fallback, and CDP is only for explicit legacy troubleshooting. Naver sync failures are post-release operational warnings; do not roll back or hide already verified public restaurants because the browser login, Naver UI state, or list capacity failed.

Prefer a Codex app **standalone project automation** on a dedicated worktree. Do not use GitHub Actions for recurring Tastyroad checks unless the user explicitly asks for it or Codex Automation is unavailable.

## Automation Prompt

Use a thin bootstrap prompt when creating or updating the Codex app Automation. The repository's
`scripts/automation_prompt.md` is the durable, versioned runbook. Keeping the Automation prompt
as a bootstrap prevents it from drifting whenever source collection, transcript, must-taste,
mapping, release, or Naver sync workflows improve in the repository:

```text
Use $tastyroad-regular-source-automation.

Fetch origin and run from a clean dedicated worktree based on the current origin/main. Preserve and report any unrelated local changes instead of stashing, overwriting, or cleaning them.

After synchronization, reread AGENTS.md, tasks/lessons.md,
.codex/skills/tastyroad-regular-source-automation/SKILL.md, and
.codex/skills/tastyroad-regular-source-automation/scripts/automation_prompt.md
from that updated checkout. Treat the repository runbook and every owning skill it invokes as
the authoritative current workflow; they supersede details cached in this Automation prompt.

Execute the complete repository runbook. Record the origin/main commit used. If the checkout
cannot safely reach current origin/main, stop and report the exact sync blocker before maintenance.
```

Do not copy the full current runbook into the Codex Automation configuration. Update the
versioned repository runbook and owning skills when behavior changes; the next scheduled run
inherits those improvements after synchronizing to `origin/main`.

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
7. After the production deployment reaches `READY` and the production API returns HTTP 200 with an `items` array, follow `$tastyroad-naver-map-sync` to add the final report's `release_scope_restaurant_ids` to the private Naver Map saved list. Prefer the Edge browser extension connector and confirm the Naver login marker before writes. Pass each ID as `--restaurant-id=<id>` when using the fallback runner. Use `Tastyroad 2` with `data/naver_map_list_synced_ids_2.json` and `--exclude-state data/naver_map_list_synced_ids.json` unless the user has explicitly changed the list partitioning.

## Rules

- Treat a non-`Available` Supabase Marketplace resource as a hard external-resource blocker; do not retry application builds as a substitute for restoring it.
- Do not deploy from a scheduled automation when any hard publishing gate is blocked.
- Do deploy verified mapped restaurants even when transcript or must-taste warnings remain.
- Do not add restaurants without numeric `naver_map_id`.
- Do not apply must-taste rows unless `apply_must_taste_result.py --dry-run` passes and the extraction followed `$tastyroad-transcript-must-taste`.
- Do not let parallel agents write SQLite, Naver Map saved lists, or deployment state.
- Keep automation work in a dedicated worktree. Preserve unresolved artifacts under ignored `data/work/`.
- Run Naver Map saved-list sync only after production deployment verification succeeds; treat Naver browser-login, UI, and list-capacity failures as post-release warnings unless the user explicitly asks to block release on saved-list sync.
- Do not fall back to CDP just because Edge is logged out. Ask the user to log into Naver in Edge, then resume the Edge extension sync.
- Report no-op runs briefly; report blocked runs with exact video IDs and the next skill/command.
