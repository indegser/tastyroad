# Lessons

Durable lessons for future coding agents in this repository.

Add an entry when the user corrects the agent or when a repeated mistake pattern is discovered. Keep lessons actionable, dated, and specific enough to change future behavior.

## 2026-06-21

- Trigger: The repository had no `AGENTS.md` or `CODEX.md`, so future agents had no project-local operating memory.
  Rule: Before non-trivial work, read `AGENTS.md` and relevant entries in this file, then track the task in `tasks/todo.md`.
- Trigger: The user clarified that Claude will not be used in this repository.
  Rule: Do not add or rely on Claude-specific files; keep persistent agent guidance in `AGENTS.md` and `CODEX.md`.
- Trigger: The user clarified that public web listing should not depend on story review completion.
  Rule: Treat collected YouTube video plus verified Naver Map restaurant mapping with a non-empty `naver_map_id` as the public listing gate; story fields are optional display content only.
- Trigger: The agent treated `tastyroad-data-pipeline` as a user-facing workflow because scripts lived there, then changed positions too reactively under user challenge.
  Rule: Build a working model before planning; separate current implementation facts from product/workflow design, and route Tastyroad work by user intent to purpose-specific skills.
- Trigger: The user asked to verify and deploy `김사원세끼` videos, but the agent only processed the latest two unreviewed videos.
  Rule: For source-level mapping requests, define and report the full source scope first; do not silently narrow work to latest videos or current backlog rows.
- Trigger: Tastyroad deployment runs repeatedly reported the Vercel app team-scope 403 before falling back to the CLI.
  Rule: For Tastyroad release status checks, skip the Vercel MCP deployment list and use the locally authenticated Vercel CLI for same-SHA deployment lookup by default.
