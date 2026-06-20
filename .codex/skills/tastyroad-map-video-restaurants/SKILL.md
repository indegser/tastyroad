---
name: tastyroad-map-video-restaurants
description: Find restaurants or places mentioned in a collected Tastyroad YouTube video, verify each real venue on Naver Map, require a numeric Naver place ID, write verified place JSON or place_verification artifacts, and apply rows into data/tastyroad.sqlite restaurants plus youtube_video_restaurants. Use when mapping one video or a batch of videos from youtube_videos into restaurant rows, repairing mapping_backlog, replacing search-only map URLs, or adding Naver map IDs for extracted restaurants.
---

# Tastyroad Map Video Restaurants

## Overview

Use this skill to turn collected YouTube videos into verified Tastyroad restaurant mappings. A restaurant row is valid only when it has a numeric `naver_map_id` from a concrete Naver Map place entry.

## Workflow

1. Confirm the video exists in `youtube_videos`.

```bash
sqlite3 -header -column data/tastyroad.sqlite "select id, video_id, title, url from youtube_videos where video_id='<video_id>';"
```

2. Gather evidence from the video row, description, transcript, story review, and existing artifacts under `data/work/videos/<video_id>/`.
3. Extract every real restaurant/place in the video. Keep multi-place videos as N items; do not collapse them into one mapping.
4. Verify each candidate in Naver Map. Accept only a specific place entry with a numeric ID, normally visible in a URL like `https://map.naver.com/p/entry/place/<naver_map_id>`.
5. If only a Naver search URL exists, do not insert into `restaurants`; leave a `place_resolution_candidates` row with `needs_review`.
6. Write verified rows either to `data/verified_places/<source_key>_<video_id>_places.json` and run `python3 .codex/skills/tastyroad-data-pipeline/scripts/promote_verified_places.py --input <file>`, or write `data/work/videos/<video_id>/place_verification.json` and run `python3 .codex/skills/tastyroad-data-pipeline/scripts/reduce_agent_artifacts.py --stage place_verification --apply`.
7. Verify that every inserted restaurant has `naver_map_id` and every mapping uses `youtube_video_restaurants`.

```bash
sqlite3 -header -column data/tastyroad.sqlite "select id, display_name, naver_map_id from restaurants where naver_map_id='';"
sqlite3 -header -column data/tastyroad.sqlite "select video_id, mapped_restaurant_count, mapping_status from video_pipeline_status where video_id='<video_id>';"
```

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
