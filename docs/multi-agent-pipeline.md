# Multi-Agent Pipeline Plan

This document defines the migration target for turning the current SQLite-centered
collection scripts into a stage-based multi-agent pipeline.

The current production path stays intact:

```text
scripts/update_pipeline.py -> data/tastyroad.sqlite -> Next.js read-only build
```

The first migration goal is not to replace this path. The first goal is to make
stage boundaries explicit, keep agent output auditable, and promote only verified
results through a single writer.

## Philosophy

This system should be built as an LLM-native multi-agent workflow, not only as a
Python batch pipeline.

The operating model is:

```text
Markdown task workspace
  -> what the agent reads, reasons about, and reports against

JSON result contract
  -> what reducers validate and import

Python guardrails
  -> planning, state transitions, claim locks, schema checks, and SQLite writes
```

Markdown is the primary workspace for subagents because the hard parts of this
pipeline are judgment-heavy: deciding whether a video is a restaurant
introduction, explaining the story around a place, extracting ambiguous place
mentions, and verifying whether map evidence is strong enough. Those tasks need
clear written criteria, source context, and room for evidence notes.

JSON is the machine contract. Every completed task must still produce structured
JSON so the reducer can validate it deterministically before any SQLite write.

Python should not become the "agent brain." Python owns the boring but critical
parts: safe task planning, idempotent artifact creation, claim/release/complete
state transitions, reducer validation, and single-writer promotion into SQLite.

In practice, each video-stage workspace should converge toward this shape:

```text
data/work/videos/{video_id}/
  task.md
  context.json
  result.md
  result.json
  restaurant_review.json
  transcript.json
  story_review.json
  place_candidates.json
  place_verification.json
```

The stage JSON files remain the reducer-facing artifacts. The Markdown files are
the agent-facing surface. Future spawned subagents should be handed `task.md`
and supporting context, then write `result.md` for audit and `result.json` for
reduction.

## Principles

- The orchestrator owns task state and decides which worker to spawn.
- Stage workers only read their inputs and write their own artifacts.
- Workers do not write directly to production tables in `data/tastyroad.sqlite`.
- Promotion is the only step allowed to mutate the final SQLite tables.
- Subagents work from Markdown task files, not from ad hoc CLI output.
- Completed subagent work must include both human-readable reasoning/evidence
  and reducer-ready JSON.
- Every agent result must keep raw output, parsed output, evidence, confidence,
  prompt version, model name, status, and error details when applicable.
- The Next.js app remains a read-only consumer of SQLite.

## Stages

```text
source_discovery
  -> video_ingest
  -> restaurant_triage
  -> transcript_fetch
  -> story_review
  -> place_extraction
  -> place_verification
  -> promotion
  -> site_build
```

`source_discovery` and `video_ingest` can keep using the existing YouTube
collection logic at first. The best early agent stages are `restaurant_triage`,
`story_review`, `place_extraction`, and `place_verification` because their
inputs and outputs can be isolated by `video_id`.

## Public Site Contract

`site_build` is a read-only consumer of promoted SQLite data, but it has a hard
public listing contract:

- A public card may be rendered only when the video has both a non-empty
  `video_story_reviews` row and verified map promotion through
  `mentions`/`restaurants`/`place_links`.
- A map-verified item without a story remains valid pipeline data, but it is not
  public web listing data.
- Every rendered public card must include a story block. The rendered
  `video-card` count and `story` count must match.
- Service refresh, web refresh, build, and deploy tasks must preserve this
  contract. Do not treat `mapping_verified` alone as enough for the public site.

The contract is enforced by `scripts/verify_public_listing_contract.py`.
`pnpm run build` verifies local static output, and `pnpm run deploy` verifies
both the prebuilt output and the deployed production URL.

## Artifact Layout

The proposed worker output layout is video-scoped:

```text
data/work/runs/{run_id}.json
data/work/videos/{video_id}/metadata.json
data/work/videos/{video_id}/task.md
data/work/videos/{video_id}/context.json
data/work/videos/{video_id}/result.md
data/work/videos/{video_id}/result.json
data/work/videos/{video_id}/restaurant_review.json
data/work/videos/{video_id}/transcript.json
data/work/videos/{video_id}/story_review.json
data/work/videos/{video_id}/place_candidates.json
data/work/videos/{video_id}/place_verification.json
```

These files are intermediate artifacts. They are useful for audit, retry, and
shadow-mode comparison. The final public data remains `data/tastyroad.sqlite`
until the promotion model is deliberately changed.

## Worker Contracts

### `restaurant_triage`

Input:

- `video_id`
- source name
- title
- description
- raw restaurant name candidates

Output:

- decision: `restaurant_intro`, `not_restaurant`, or `uncertain`
- confidence
- restaurant name candidates
- detected restaurant count
- evidence and reason

Existing importer: `scripts/apply_agent_reviews.py`

### `transcript_fetch`

Input:

- `video_id`
- preferred languages

Output:

- transcript segments
- transcript text
- language metadata
- fetch status or failure reason

Existing code path: `scripts/process_video_stories.py`

### `story_review`

Input:

- transcript
- metadata
- restaurant triage result

Output:

- story hook
- story intro
- tasting flow
- evidence JSON with `host_reason`, `store_context`, and `tasting_order`
- at least three `critic_rounds`
- revision history

Existing importer: `scripts/process_video_stories.py`

Completion gate:

- Writer extracts `evidence.tasting_order` before prose.
- `tasting_flow` must describe what was eaten in order.
- Critic runs at least three closed-loop rounds.
- Round 1 and Round 2 must be `revise` with concrete `required_changes`.
- The writer must answer each round with `writer_response`.
- The final round must be `pass`, have empty `issues`, and set every required
  check to `true`.
- The reducer rejects story artifacts that do not meet this contract.

### `place_extraction`

Input:

- metadata
- transcript
- story review
- restaurant triage result

Output:

- candidate place names
- area/address hints
- evidence snippets
- confidence
- unresolved questions

### `place_verification`

Input:

- place candidates
- existing restaurants and links
- web/map evidence

Output:

- verified place candidates
- provider links
- evidence URL
- confidence
- status: `verified`, `needs_review`, or `rejected`

Existing promotion path: `scripts/promote_verified_places.py`

## Migration Sequence

1. Keep `scripts/update_pipeline.py` and the existing SQLite schema working.
2. Add a planner that reads SQLite status and emits stage tasks without mutating
   data.
3. Store worker artifacts under `data/work/` and compare them against the
   current pipeline in shadow mode.
4. Convert one stage at a time, starting with `restaurant_triage` or
   `story_review`.
5. Only after shadow-mode diff is acceptable, let promotion consume the new
   artifacts.
6. Keep rollback simple: discard `data/work/` artifacts and run the existing
   SQLite pipeline.

## Current Implementation

Implemented workers write only work artifacts. They do not write directly to
SQLite.

The orchestrator ties together planning, optional worker execution, inbox
inspection, and optional reduction. It defaults to read-only planning/inbox
reporting unless `--run-workers`, `--reduce`, or `--apply` is passed.

```bash
python3 scripts/orchestrate_agents.py --limit 1
python3 scripts/orchestrate_agents.py --stage restaurant_triage --video-id 8Mb5_aLiE1g --run-workers --refresh
python3 scripts/orchestrate_agents.py --reduce
pnpm orchestrate:agents --limit 1
```

```bash
python3 scripts/agent_pipeline.py --stage transcript_fetch --limit 5
python3 scripts/agent_pipeline.py --stage transcript_fetch --run --limit 1
pnpm run:transcripts --limit 1
```

The seeded workers convert existing reviewed JSON into stage artifacts. They do
not invent restaurant or place decisions when no seed exists.

```bash
python3 scripts/agent_pipeline.py --stage restaurant_triage --run --limit 1
python3 scripts/agent_pipeline.py --stage story_review --run --limit 1
python3 scripts/agent_pipeline.py --stage place_extraction --run --limit 1
python3 scripts/agent_pipeline.py --stage place_verification --run --limit 1
```

Use `--video-id` to force a task for an already processed video when testing a
worker contract.

```bash
python3 scripts/agent_pipeline.py --stage story_review --video-id bfBmJCPgCmI --run --refresh
python3 scripts/agent_pipeline.py --stage place_verification --video-id d6zoTmkiyf0 --run --refresh
```

Existing artifacts are skipped unless `--refresh` is passed.

```bash
python3 scripts/agent_pipeline.py --stage transcript_fetch --run --refresh --limit 1
```

When no seed data exists, a worker writes a `needs_agent` artifact and renders a
Markdown-first task workspace next to it:

```text
task.md
context.json
result.md
result.json
```

These files are the handoff point for spawned subagents. The subagent reads
`task.md`, uses `context.json` as supporting data, writes human-readable evidence
to `result.md`, and writes reducer-ready structured output to `result.json`.

```bash
python3 scripts/agent_inbox.py
python3 scripts/agent_inbox.py --stage restaurant_triage --format json
pnpm agent:inbox
```

Subagents should claim an artifact before working on it. Completion replaces the
`needs_agent` payload with a `succeeded` payload that the reducer can import.
If `--result` is omitted, `agent_task.py complete` reads `result.json` next to
the artifact.

```bash
python3 scripts/agent_task.py claim data/work/videos/{video_id}/restaurant_review.json --agent agent-1
python3 scripts/agent_task.py complete data/work/videos/{video_id}/restaurant_review.json --agent agent-1
python3 scripts/agent_task.py release data/work/videos/{video_id}/restaurant_review.json --agent agent-1
```

The reducer is the single writer that can import successful transcript artifacts
into SQLite. It defaults to dry-run mode.

```bash
python3 scripts/reduce_agent_artifacts.py
python3 scripts/reduce_agent_artifacts.py --apply
pnpm reduce:agents
```

## Non-Goals For The First Pass

- Do not replace the Next.js data reader.
- Do not let spawned agents write directly to SQLite.
- Do not replace source collection, dedupe, and promotion in one change.
- Do not merge candidate and verified place states.
- Do not treat agent confidence as verification.
