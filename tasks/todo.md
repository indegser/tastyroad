# Task Log

Use this file for active non-trivial work. Keep entries short and checkable.

## Current Task - 2026-06-21

- [x] Confirm the current public listing gates in the app query.
- [x] Change public listing eligibility to use collected video + verified Naver Map restaurant mapping.
- [x] Verify the new public count and build the app.

### Review

- Public listing eligibility now ignores story review presence and triage review rows.
- The app lists restaurants with a collected YouTube video mapping, `youtube_video_restaurants.status in ('verified', 'metadata_verified')`, and non-empty `restaurants.naver_map_id`.
- Verified the new SQL count is 39 public restaurants on the current DB and `pnpm run build` passes.
