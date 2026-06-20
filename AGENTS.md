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

## Verification

- Do not call work complete until behavior has been checked.
- Prefer repository commands and skills over ad hoc scripts.
- Use `pnpm run build` for app build verification when relevant.
- For Tastyroad data, release, YouTube collection, or Naver Map workflows, read and follow the matching `.codex/skills` instructions before running commands.
- Record what was verified in the final response and, for non-trivial work, in `tasks/todo.md`.

## Repository Context

- This is a Next.js project for a source-backed Korean restaurant listing.
- Repeated task logic lives under purpose-specific `.codex/skills`, not root-level `scripts/`.
- User-facing Tastyroad workflow skills are:
  - `$tastyroad-youtube-channel-collect`: YouTube collection and refresh.
  - `$tastyroad-map-video-restaurants`: `mapping_pending`/`needs_review` inspection, Naver place ID verification, and `restaurants`/`youtube_video_restaurants` writes.
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
