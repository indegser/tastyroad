# Tastyroad Agent Guide

This file is the canonical operating guide for coding agents in this repository. External system, developer, and user instructions override this file.

## Default Loop

For every non-trivial task, use this loop:

1. Read this file, then read `tasks/lessons.md` for accumulated project lessons.
2. Inspect the relevant code, data, docs, and skill instructions before deciding.
3. Write or update `tasks/todo.md` with a short checklist for the current task.
4. Implement in small, scoped changes that match the existing repository patterns.
5. Mark checklist items complete as work progresses.
6. Verify with the narrowest reliable command first, then broader checks when risk warrants it.
7. Add a short review/result note to `tasks/todo.md`.
8. If the user corrected the agent or a mistake pattern was discovered, update `tasks/lessons.md` with a reusable rule.

For trivial questions or read-only checks, answer directly and skip task files unless the user asks for persistent notes.

## Self-Learning Rules

- Treat `tasks/lessons.md` as durable memory for this repository.
- Add lessons only when they are actionable and likely to prevent a repeated mistake.
- Keep each lesson short, dated, and tied to a concrete trigger.
- Rewrite stale or noisy lessons instead of endlessly appending.
- At the start of a related future task, apply relevant lessons before changing files.

Lesson format:

```md
## YYYY-MM-DD

- Trigger: What happened or what correction was given.
  Rule: What future agents should do differently.
```

## Planning

- Before making a plan, build a working model of the request:
  - Frame what the user is trying to accomplish and what would count as done.
  - Separate observed facts from assumptions and unknowns.
  - Locate the source of truth before judging behavior or architecture.
  - Consider whether there is a simpler or more principled path before choosing.
  - Make a decision first; let the checklist reflect that decision.
  - Preserve intellectual friction: test user pushback against facts instead of agreeing or disagreeing reflexively.
- Use `tasks/todo.md` for tasks with three or more steps, architecture decisions, data pipeline changes, releases, or risky edits.
- The plan should be concrete and checkable, not a long essay.
- If implementation reveals the plan is wrong, stop, update the plan, and continue from the corrected plan.
- Do not wait for approval after writing a plan unless the user explicitly asked to review the plan first.

## Autonomous Worktree Management

Use this policy for non-trivial coding, data, release, pipeline, or documentation tasks so concurrent conversations can proceed without routine `stash`/`checkout` churn.

Before editing files:

- Run `git status --short --branch`, `git branch --show-current`, and `git worktree list`.
- Treat the main checkout at `/Users/indegser/Github/tastyroad` and the `main` branch as shared coordination space unless the task is already clearly scoped to that checkout.
- If the current checkout has unrelated changes, is on an unrelated branch, or is the shared main checkout, create or reuse a task-specific worktree under `../tastyroad-worktrees/<short-task-slug>`.
- Use branch names like `codex/<short-task-slug>`, based on a short kebab-case summary of the request.
- Base new worktrees on `origin/main` unless the user names a different base.
- Reuse an existing task worktree only when its path/branch matches the current request and its dirty state is clean or clearly belongs to the same task.
- If a matching worktree has ambiguous dirty changes, preserve it and create a suffixed worktree instead of overwriting or cleaning it.

While working:

- Do all edits, verification, commits, and task-specific commands inside the chosen worktree.
- Record the chosen worktree path and branch in `tasks/todo.md` for non-trivial tasks.
- After creating or reusing a task-specific worktree that needs Vercel-managed env vars, provision that worktree's local env from the linked main checkout: `vercel env pull <worktree>/.env.local --yes --cwd /Users/indegser/Github/tastyroad`. Do this instead of running `vercel env pull` from an unlinked worktree. If overwriting local env would be unsafe, preserve the existing file and report the blocker.
- Do not use `git stash` as routine context switching between concurrent tasks.
- Do not switch branches in a dirty worktree just to reach another task.
- Respect an explicit user-provided path or branch over this default routing.
- Skip worktree creation for trivial read-only checks and direct answers.

## Worktree Cleanup Policy

When the agent created a task-specific worktree, clean it up automatically only after the task is safely published or released.

- On ordinary "push" requests, commit only intended changes, push the task branch, then remove the local task worktree only if `git status --short` is clean and all local commits are pushed to the branch upstream.
- On "deploy" or "release" requests, first follow `$tastyroad-site-release`. Remove the local task worktree only after local validation, GitHub push, Vercel deployment, and deployed-site verification all succeed.
- For the default `배포해` production path, do not silently deploy a feature branch as production. Integrate the intended changes into `main` through the release workflow, or use a preview deployment only when the user explicitly asks for preview.
- Remove only the extra worktree directory created under `../tastyroad-worktrees/`; do not delete remote branches automatically.
- Do not delete local branches for open PRs, unmerged work, failed checks, failed deployment verification, uncommitted changes, or unpushed commits unless the user explicitly asks.
- If cleanup is unsafe, leave the worktree in place and report the path plus the blocking condition.

## Verification

- Do not call work complete until behavior has been checked.
- Prefer repository commands and skills over ad hoc scripts.
- Use `pnpm run build` for app build verification when relevant.
- For Tastyroad data, release, YouTube collection, transcript ingest, transcript must-taste extraction, or Naver Map workflows, read and follow the matching `.codex/skills` instructions before running commands.
- Record what was verified in the final response and, for non-trivial work, in `tasks/todo.md`.

## Skill Design Defaults

When creating or updating Tastyroad skills, first decide whether the workflow should be script-centered, agent-centered, or hybrid.

- Default to script-centered workflows for data movement, storage, schema changes, DB writes, release steps, external UI side effects, idempotent batch operations, and validation gates.
- Use agent-centered stages only when the hard part is broad context exploration, subjective judgment, candidate discovery, semantic review, or conflict resolution across messy artifacts.
- Prefer hybrid designs for complex data workflows: scripts prepare context and perform final writes; agents scout, review, and arbitrate ambiguous evidence through explicit artifacts.
- Do not let parallel agents mutate shared DBs, production services, saved lists, or deployment state. Have them write review artifacts, then use a sequential arbiter and deterministic script for state changes.
- Require lineage and validation contracts whenever agent judgment feeds a write step: record inputs, candidates, accepted/rejected decisions, evidence, and failure reasons before applying changes.
- Keep `SKILL.md` concise. Put long prompts, schemas, and examples into `references/`, and put repeated deterministic operations into `scripts/`.

## Recurring Automation Defaults

- For recurring Tastyroad source checks, use Codex app Automation with a repo-local skill and a dedicated automation worktree.
- Do not default to GitHub Actions for scheduled Tastyroad maintenance unless the user explicitly asks for GitHub Actions or Codex Automation is unavailable.
- Route recurring source maintenance through `$tastyroad-regular-source-automation`.
- Treat deployment as gated: unresolved mapping, transcript, or must-taste blockers should produce a Triage finding instead of an automatic release.

## Repository Context

- This is a Next.js project for a source-backed Korean restaurant listing.
- Repeated task logic lives under purpose-specific `.codex/skills`, not root-level `scripts/`.
- User-facing Tastyroad workflow skills are:
  - `$tastyroad-regular-source-automation`: Codex Automation orchestration for recurring all-source checks, deterministic safe updates, gate reports, and release handoff.
  - `$tastyroad-youtube-channel-collect`: YouTube collection and refresh.
  - `$tastyroad-youtube-transcript-ingest`: Webshare-backed YouTube transcript download and SQLite track/segment storage.
  - `$tastyroad-transcript-must-taste`: Restaurant-scoped, multi-pass transcript must-taste extraction with whole-transcript coverage, attention candidates, candidate reviews, rejection tracking, quality validation, and SQLite storage.
  - `$tastyroad-map-video-restaurants`: `mapping_pending`/`needs_review` inspection, agent-assisted candidate/place review for ambiguous mappings, Naver place ID verification, and `restaurants`/`youtube_video_restaurants` writes.
  - `$tastyroad-site-release`: build, commit/push, and Vercel deployment verification.
- Do not reintroduce a generic `tastyroad-data-pipeline` user-facing skill; route work by user intent to the purpose-specific skill that owns it.
- App data and artifacts live under `data/`.
- Public site code lives under `app/`, `lib/`, and `public/`.
- Existing README sections for data, skills, agents, and build commands are part of the operating contract.

## Engineering Preferences

- Keep changes minimal and local to the requested behavior.
- Use existing local patterns before introducing new abstractions.
- Prefer structured parsers and project utilities over brittle string manipulation.
- Preserve user changes in the worktree.
- Use `rg`/`rg --files` for search when available.
- Before presenting a non-trivial solution, ask whether there is a simpler or more elegant implementation that fits the current codebase.

## Source Note

This guide adapts the public "Boris Cherny's CLAUDE.md" workflow pattern: plan first, use focused parallel work when helpful, verify before done, and capture corrections as durable lessons. It is rewritten for this Tastyroad repository and Codex-compatible operation.
