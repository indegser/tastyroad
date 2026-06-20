---
name: tastyroad-map-video-restaurants
description: Find and update Tastyroad restaurants from collected YouTube videos by inspecting mapping_pending or needs_review rows, verifying concrete Naver Map place IDs, and applying verified rows into data/tastyroad.sqlite restaurants plus youtube_video_restaurants. Use when mapping one video or a batch of videos from youtube_videos, repairing mapping_backlog, replacing search-only map URLs, or adding Naver map IDs for extracted restaurants.
---

# Tastyroad Map Video Restaurants

## Overview

Use this skill to turn collected YouTube videos into verified Tastyroad restaurant mappings. A restaurant row is valid only when it has a numeric `naver_map_id` from a concrete Naver Map place entry.

This is the owner for `mapping_pending`, `mapping_partial`, and `place_resolution_candidates.status = 'needs_review'` work. Do not route restaurant mapping through a generic data-pipeline skill.

## Workflow

1. Inspect mapping backlog and unresolved candidates.

```bash
python3 .codex/skills/tastyroad-map-video-restaurants/scripts/pipeline_status.py
sqlite3 -header -column data/tastyroad.sqlite "select video_id, title, detected_restaurant_count, mapped_restaurant_count, reviewed_restaurant_names from mapping_backlog order by published_at desc limit 20;"
sqlite3 -header -column data/tastyroad.sqlite "select v.video_id, p.query, p.result_name, p.result_address, p.result_url, p.status from place_resolution_candidates p join youtube_videos v on v.id=p.youtube_video_id where p.status='needs_review' order by p.searched_at desc limit 20;"
```

2. Confirm the target video exists in `youtube_videos`.

```bash
sqlite3 -header -column data/tastyroad.sqlite "select id, video_id, title, url from youtube_videos where video_id='<video_id>';"
```

3. Gather evidence from the video row, description, transcript, story review, and existing artifacts under `data/work/videos/<video_id>/`.
4. Extract every real restaurant/place in the video. Keep multi-place videos as N items; do not collapse them into one mapping.
5. Verify each candidate in Naver Map. Accept only a specific place entry with a numeric ID, normally visible in a URL like `https://map.naver.com/p/entry/place/<naver_map_id>`.
6. If only a Naver search URL exists, do not insert into `restaurants`; leave a `place_resolution_candidates` row with `needs_review`.
7. Write verified rows to `data/verified_places/<source_key>_<video_id>_places.json`, then apply them:

```bash
python3 .codex/skills/tastyroad-map-video-restaurants/scripts/promote_verified_places.py --input data/verified_places/<file>.json
```

8. Verify that every inserted restaurant has `naver_map_id` and every mapping uses `youtube_video_restaurants`.

```bash
sqlite3 -header -column data/tastyroad.sqlite "select id, display_name, naver_map_id from restaurants where naver_map_id='';"
sqlite3 -header -column data/tastyroad.sqlite "select video_id, mapped_restaurant_count, mapping_status from video_pipeline_status where video_id='<video_id>';"
```

## Optional Candidate Generation

Use the backlog processor only when you need to derive candidates from collected video metadata before manual Naver place verification:

```bash
python3 .codex/skills/tastyroad-map-video-restaurants/scripts/process_pipeline_backlog.py --dry-run
python3 .codex/skills/tastyroad-map-video-restaurants/scripts/process_pipeline_backlog.py
```

`--dry-run` is read-only and does not resolve `naver.me` links. The write mode may create `needs_review` search candidates. Search URLs are not verified restaurant mappings.

## Output Contract

For `data/verified_places/*.json`, include this shape:

```json
{
  "source": "source display name",
  "verified_at": "2026-06-20",
  "items": [
    {
      "video_id": "youtube_id",
      "resolved_name": "canonical restaurant name",
      "display_name": "public restaurant name",
      "local_name": "optional local name",
      "country_code": "KR",
      "region": "서울 중구",
      "address": "full Naver Map address",
      "phone": "optional phone",
      "category": "restaurant category",
      "map_provider": "naver_map",
      "naver_map_id": "123456789",
      "map_url": "https://map.naver.com/p/entry/place/123456789?placePath=%2Fhome",
      "evidence_url": "source URL that proves the match",
      "confidence": 0.98,
      "status": "verified",
      "notes": "short reason the Naver place matches the video"
    }
  ]
}
```

## Rules

- Never add a `restaurants` row without `naver_map_id`.
- Never use `mentions` or `mention_candidates`; the DB model is `youtube_videos` plus `youtube_video_restaurants`.
- Prefer direct Naver place entry URLs. `naver.me` short URLs are acceptable only after resolving to a numeric Naver place ID.
- Use search URLs only as unresolved candidates, not as public restaurant mappings.
- Read `references/tastyroad-restaurant-mapping.md` before editing mapping files or applying DB changes.
