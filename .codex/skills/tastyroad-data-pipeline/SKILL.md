---
name: tastyroad-data-pipeline
description: Run Tastyroad's SQLite-centered data pipeline and multi-agent work queue from bundled skill scripts. Use when Codex needs to refresh YouTube-derived data, apply video reviews, fetch transcripts, generate or reduce story/place artifacts, inspect pipeline status, process mapping backlog, or orchestrate Tastyroad story/place agents without using repo-level scripts.
---

# Tastyroad Data Pipeline

## Overview

Use this skill from the Tastyroad repo root. The repository no longer owns executable pipeline scripts; run the bundled scripts in this skill instead.

## Quick Commands

Inspect pipeline state:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/pipeline_status.py
```

Refresh the SQLite data pipeline:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/update_pipeline.py
```

Plan or run one agent stage:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/agent_pipeline.py --stage story_review --format json
python3 .codex/skills/tastyroad-data-pipeline/scripts/agent_pipeline.py --stage story_review --run --limit 1
```

Orchestrate planning, workers, inbox, and reducer:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/orchestrate_agents.py --limit 1
python3 .codex/skills/tastyroad-data-pipeline/scripts/orchestrate_agents.py --reduce
```

Reduce completed artifacts into SQLite:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/reduce_agent_artifacts.py
python3 .codex/skills/tastyroad-data-pipeline/scripts/reduce_agent_artifacts.py --apply
```

## Workflows

For normal data refresh, run `update_pipeline.py`. It collects configured YouTube sources, applies video triage reviews, fetches transcripts where needed, imports story reviews, and promotes verified place JSON files from `data/verified_places`.

For multi-agent work, use `agent_pipeline.py` to create or run video-scoped stage artifacts under `data/work/videos/{video_id}`. Use `agent_inbox.py` to list `needs_agent` and `claimed` artifacts, `agent_task.py` to claim or complete a single artifact, and `reduce_agent_artifacts.py --apply` as the only writer that imports successful artifacts into SQLite.

For one-command coordination, use `orchestrate_agents.py`. It runs stage planning in order, can run workers, lists inbox state, and can invoke reducer dry-runs or writes.

## Safety Rules

- Do not recreate `scripts/` in the repo root.
- Do not let subagents write directly to `data/tastyroad.sqlite`; route writes through the reducer or promotion scripts in this skill.
- Run all commands from the Tastyroad repo root so relative paths resolve to `data/`.
- When retrying transcript failures, use `--video-id` with `--refresh` to avoid broad unrelated retries.
- Read `references/pipeline.md` when changing stage contracts, reducer behavior, or public-listing eligibility.
