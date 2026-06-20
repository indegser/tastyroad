# Task Log

Use this file for active non-trivial work. Keep entries short and checkable.

## Current Task - 2026-06-21

- [x] Inspect the latest unmapped/unreviewed `김사원세끼` videos.
- [x] Verify every listed restaurant against a numeric Naver Map place ID.
- [x] Promote verified places into `restaurants` and `youtube_video_restaurants`.
- [x] Verify DB mapping status and required Naver IDs.
- [x] Run the production build before release.
- [x] Add the review result.

### Review

- Added `김사원세끼` reviews for `jNE63WCLQlk` and `EJ1rPCr0SCQ`.
- Verified and promoted 별난오리 (`38275504`), 금릉슈퍼 (`18682367`), and 일등집 (`1678099688`) from Naver Map entry URLs.
- Confirmed both videos are `mapping_verified`, no restaurant row has a blank `naver_map_id`, and `pnpm run build` passes.
