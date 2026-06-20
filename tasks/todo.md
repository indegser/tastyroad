# Task Log

Use this file for active non-trivial work. Keep entries short and checkable.

## Current Task - 2026-06-21

- [x] Move Tastyroad skill boundaries to YouTube collection, video restaurant mapping, and site release.
- [x] Remove the user-facing `tastyroad-data-pipeline` skill surface.
- [x] Update docs, references, and scripts to use the purpose-specific skill paths.
- [x] Validate the revised skill metadata and focused Python entry points.
- [x] Record the skill-boundary lesson.
- [x] Add the review result.

### Review

- Removed the user-facing `tastyroad-data-pipeline` skill and moved mapping status/promotion/backlog scripts under `$tastyroad-map-video-restaurants`.
- Kept YouTube collection under `$tastyroad-youtube-channel-collect` and updated README, AGENTS, references, and e2e imports to use purpose-specific paths.
- Fixed `process_pipeline_backlog.py --dry-run` so it opens SQLite read-only and does not resolve `naver.me` links.
- Verified skill metadata with `quick_validate.py`, Python syntax/imports with `py_compile`, read-only backlog dry-run, and `pnpm run build`.
