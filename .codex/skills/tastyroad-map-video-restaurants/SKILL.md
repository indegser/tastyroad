---
name: tastyroad-map-video-restaurants
description: Find and update Tastyroad restaurants from collected YouTube videos by inspecting mapping_pending or needs_review rows, using agent-assisted candidate scouting and place verification when mapping evidence is ambiguous or multi-place, verifying concrete Naver Map place IDs, and applying verified rows into data/tastyroad.sqlite restaurants plus youtube_video_restaurants. Use when mapping one video or a batch of videos from youtube_videos, repairing mapping_backlog, replacing search-only map URLs, resolving Naver place candidates, or adding Naver map IDs for extracted restaurants.
---

# Tastyroad Map Video Restaurants

## Overview

Use this skill to turn collected YouTube videos into verified Tastyroad restaurant mappings. A restaurant row is valid only when it has a numeric `naver_map_id` from a concrete Naver Map place entry.

This is the owner for `mapping_pending`, `mapping_partial`, and `place_resolution_candidates.status = 'needs_review'` work. Do not route restaurant mapping through a generic data-pipeline skill.

This is a hybrid skill. Use agents for ambiguous evidence review, candidate discovery, and Naver place match judgment. Use scripts for backlog inspection, deterministic candidate generation, final promotion, and DB verification.

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

3. Prepare mapping evidence from the video row, description, transcript, must-taste artifacts, and existing work artifacts under `data/work/`. Read `references/tastyroad-restaurant-mapping.md` before editing mapping files or applying DB changes.

4. For ambiguous, batch, or multi-place work, run the agent-assisted review flow:

- **Candidate scouts**: split videos or evidence sources across workers/subagents when available. Extract every real restaurant/place, cite the exact source text or URL, and explicitly reject non-restaurant/place mentions.
- **Naver place verifiers**: review each candidate against concrete Naver Map place entries. Compare name, address, category, phone, source description, transcript context, and any existing `place_resolution_candidates` row.
- **Conflict reviewer**: check for missed restaurants in multi-place videos, duplicate names, wrong branches, search-only URLs, stale `naver.me` links, and candidates that only match by name.
- **Sequential arbiter**: decide the final `verified_places` items and unresolved candidates. Every accepted item needs a numeric Naver place ID; every rejected or unresolved candidate needs a short reason.

Use subagents only for scout/verifier/reviewer stages. Do not let parallel agents write SQLite, edit `data/verified_places`, or toggle external map state.

For a single direct official description block with an unambiguous concrete Naver place entry, concise manual verification is acceptable; still preserve enough evidence in the final notes.

5. Accept only a specific place entry with a numeric ID, normally visible in a URL like `https://map.naver.com/p/entry/place/<naver_map_id>`.
6. If only a Naver search URL exists, do not insert into `restaurants`; leave a `place_resolution_candidates` row with `needs_review` or record the unresolved candidate in the review artifact.
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

## Review Artifact Contract

For agent-assisted mapping, keep review artifacts under `data/work/map_video_restaurants/<video_id>/` or an equivalent ignored work path:

- `candidate_scouts.jsonl`: one JSON object per candidate or rejected non-place mention, with `video_id`, `candidate_id`, candidate name, evidence source, exact evidence text or URL, optional timestamp, and a short scope note.
- `place_verifications.json`: root object with `video_id` and `verifications`; every candidate should have a verifier decision, concrete Naver result fields when found, and `verdict` of `verified`, `needs_review`, or `reject`.
- `conflict_review.json`: list missed-place risks, duplicate/branch risks, rejected candidates, unresolved candidates, and the recommended final items.

The final `data/verified_places/*.json` file is the only promotion input. Review artifacts explain the judgment but do not replace the verified places output contract.

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
- Agent outputs are evidence and review material, not authorization to write. Final writes must go through `promote_verified_places.py` and the DB verification commands above.
