---
name: tastyroad-map-video-restaurants
description: Find and update Tastyroad restaurants from collected YouTube videos by inspecting mapping_pending, needs_review, reviewed_uncertain, or not_applicable rows, using web-search-assisted candidate scouting when video metadata lacks concrete restaurant info, verifying concrete Naver Map place IDs, and applying verified rows into data/tastyroad.sqlite restaurants plus youtube_video_restaurants. Use when mapping one video or a batch of videos from youtube_videos, repairing mapping_backlog, replacing search-only map URLs, resolving Naver place candidates, adding Naver map IDs for extracted restaurants, or recovering broadcast clips whose food/location clues were missed by metadata-only review.
---

# Tastyroad Map Video Restaurants

## Overview

Use this skill to turn collected YouTube videos into verified Tastyroad restaurant mappings. A restaurant row is valid only when it has a numeric `naver_map_id` from a concrete Naver Map place entry.

This is the owner for `mapping_pending`, `mapping_partial`, `reviewed_uncertain`/`not_applicable` rows with food or location clues, and `place_resolution_candidates.status = 'needs_review'` work. Do not route restaurant mapping through a generic data-pipeline skill.

This is a hybrid skill. Use agents for ambiguous evidence review, web search candidate discovery, and Naver place match judgment. Use scripts for backlog inspection, deterministic metadata candidate generation, final promotion, and DB verification.

For broadcast sources, lack of structured YouTube metadata or useful captions is not enough to mark a food-title video as non-place. If the title has menu, region, episode, or "맛집/식당/위치" clues, run web search candidate discovery before closing it as unresolved.

## Workflow

1. Inspect mapping backlog and unresolved candidates.

```bash
python3 .codex/skills/tastyroad-map-video-restaurants/scripts/pipeline_status.py
sqlite3 -header -column data/tastyroad.sqlite "select video_id, title, detected_restaurant_count, mapped_restaurant_count, reviewed_restaurant_names from mapping_backlog order by published_at desc limit 20;"
sqlite3 -header -column data/tastyroad.sqlite "select v.video_id, p.query, p.result_name, p.result_address, p.result_url, p.status from place_resolution_candidates p join youtube_videos v on v.id=p.youtube_video_id where p.status='needs_review' order by p.searched_at desc limit 20;"
sqlite3 -header -column data/tastyroad.sqlite "select source, video_id, title, review_status, mapping_status from video_pipeline_status where review_status in ('reviewed_uncertain', 'reviewed_not_restaurant') or mapping_status = 'not_applicable' order by published_at desc limit 20;"
```

2. Confirm the target video exists in `youtube_videos`.

```bash
sqlite3 -header -column data/tastyroad.sqlite "select id, video_id, title, url from youtube_videos where video_id='<video_id>';"
```

3. Prepare mapping evidence from the video row, description, transcript, must-taste artifacts, external web search results when metadata is sparse, and existing work artifacts under `data/work/`. Read `references/tastyroad-restaurant-mapping.md` before editing mapping files or applying DB changes.

4. If the metadata/caption evidence does not name a restaurant but the title has food, region, episode, or broadcast cues, run web search candidate discovery before Naver verification:

- Generate queries from source name, season/episode, region, distinctive menu words, and terms such as `식당`, `맛집`, `촬영지`, `위치`, and `방송`.
- Search the web first, not only the video description or transcript. Prefer official broadcast pages and detailed posts that name the restaurant, address, phone, or menu context.
- Treat captions as supporting evidence for segment scope, not as the primary discovery source for broadcast clips.
- Record each accepted or rejected web candidate with the query, URL, extracted restaurant name/address/menu, and the reason it does or does not match the target video.

5. Before creating a new restaurant candidate, check whether the web candidate already exists in `restaurants`:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select id, display_name, address, naver_map_id from restaurants where display_name like '%<name>%' or address like '%<address-fragment>%';"
```

If an existing row has the same restaurant, address/region, menu context, and numeric `naver_map_id`, reuse it in the final verified places output for the new video instead of doing a new place search.

6. For ambiguous, batch, or multi-place work, run the agent-assisted review flow:

- **Candidate scouts**: split videos or evidence sources across workers/subagents when available. Extract every real restaurant/place, cite the exact source text or URL, and explicitly reject non-restaurant/place mentions.
- **Web search scouts**: for metadata-poor broadcast clips, use search queries built from source, season, episode, region, title/menu words, and "식당/맛집/위치/촬영지"; capture both positive candidates and explicit no-match results.
- **Existing DB match reviewers**: compare web candidates to `restaurants` before Naver lookup. Reuse existing rows only when name plus address/region/menu/episode context align and the row already has a numeric `naver_map_id`.
- **Naver place verifiers**: review each candidate against concrete Naver Map place entries. Compare name, address, category, phone, source description, transcript context, and any existing `place_resolution_candidates` row.
- **Conflict reviewer**: check for missed restaurants in multi-place videos, duplicate names, wrong branches, search-only URLs, stale `naver.me` links, and candidates that only match by name.
- **Sequential arbiter**: decide the final `verified_places` items and unresolved candidates. Every accepted item needs a numeric Naver place ID; every rejected or unresolved candidate needs a short reason.

Use subagents only for scout/verifier/reviewer stages. Do not let parallel agents write SQLite, edit `data/verified_places`, or toggle external map state.

For a single direct official description block with an unambiguous concrete Naver place entry, concise manual verification is acceptable; still preserve enough evidence in the final notes.

7. Accept only a specific place entry with a numeric ID, normally visible in a URL like `https://map.naver.com/p/entry/place/<naver_map_id>`.
8. If only a Naver search URL exists, do not insert into `restaurants`; leave a `place_resolution_candidates` row with `needs_review` or record the unresolved candidate in the review artifact.
9. Write verified rows to `data/verified_places/<source_key>_<video_id>_places.json`, then apply them:

```bash
python3 .codex/skills/tastyroad-map-video-restaurants/scripts/promote_verified_places.py --input data/verified_places/<file>.json
```

10. Verify that every inserted restaurant has `naver_map_id` and every mapping uses `youtube_video_restaurants`.

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

Metadata candidate generation is insufficient for broadcast clips whose descriptions omit restaurant names. For those rows, use the web search candidate discovery flow above and keep review artifacts before creating the final verified places file.

## Web Search Recovery Heuristics

Use web search recovery when a row is already `reviewed_uncertain`, `reviewed_not_restaurant`, or `not_applicable`, but the title still contains credible restaurant clues such as a dish, neighborhood/region, episode label, "맛집", "식당", "노포", "구이", "짬짜면", or similar menu/location words.

Do not map a video from a generic episode-level search result alone. The candidate must match the target clip by at least two of: restaurant name, address/region, distinctive menu, episode/season, title words, official broadcast context, or an already mapped sibling video from the same source.

Special or compilation videos can contain several places. Do not force a single mapping for `스페셜`, `총집합`, or multi-menu titles; either map every clearly identified place or leave unresolved candidates with reasons.

## Review Artifact Contract

For agent-assisted mapping, keep review artifacts under `data/work/map_video_restaurants/<video_id>/` or an equivalent ignored work path:

- `candidate_scouts.jsonl`: one JSON object per candidate or rejected non-place mention, with `video_id`, `candidate_id`, candidate name, evidence source, exact evidence text or URL, optional timestamp, and a short scope note.
- `web_search_candidates.jsonl`: one JSON object per search-derived candidate or no-match result, with `video_id`, `query`, `url`, candidate name, address/menu clues, evidence summary, and match rationale.
- `existing_restaurant_matches.json`: root object with `video_id` and `matches`; include matched `restaurant_id`, `naver_map_id`, compared fields, verdict, and reason before reusing an existing restaurant row.
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
