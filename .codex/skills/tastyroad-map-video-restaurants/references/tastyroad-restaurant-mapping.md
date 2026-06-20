# Tastyroad Restaurant Mapping Reference

## DB Model

- `youtube_videos`: collected YouTube video rows. The YouTube ID is `video_id`.
- `restaurants`: verified places only. `naver_map_id` is required and must not be blank.
- `youtube_video_restaurants`: M:N mapping table between videos and restaurants.
- `place_resolution_candidates`: unresolved or selected search results. Use this for candidates that lack a numeric Naver place ID.
- `place_links`: provider URLs for verified restaurants. Public Naver links must not be `/p/search/` URLs.

## Required Commands

Inspect one video:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select v.id, v.video_id, s.name as source, v.title, v.url, v.description from youtube_videos v join sources s on s.id=v.source_id where v.video_id='<video_id>';"
```

Inspect mapping status:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select video_id, detected_restaurant_count, mapped_restaurant_count, mapping_status from video_pipeline_status where video_id='<video_id>';"
```

Apply a verified places JSON file:

```bash
python3 .codex/skills/tastyroad-map-video-restaurants/scripts/promote_verified_places.py --input data/verified_places/<file>.json
```

Check required Naver IDs:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select id, display_name, naver_map_id from restaurants where naver_map_id='';"
```

## Naver ID Rules

- Accept IDs parsed from `/entry/place/<digits>` or `/place/<digits>`.
- Resolve `https://naver.me/...` before finalizing; the promotion script can do this, but the JSON should include `naver_map_id` when known.
- Reject Google, Kakao, and generic Naver search URLs for `restaurants`.
- If the video clearly contains a restaurant but no Naver ID is verified yet, write a candidate with `status: "needs_review"` and do not create a restaurant row.

## Quality Checks

- For multi-restaurant videos, create one item per restaurant with the same `video_id`.
- Match by name plus address. Phone/category are supporting evidence, not substitutes for a place ID.
- Keep notes short and factual; do not put public story prose in mapping notes.
- After applying, `select count(*) from restaurants where naver_map_id=''` must return `0`.
