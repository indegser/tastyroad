---
name: tastyroad-transcript-must-taste
description: Run a multi-pass, transcript-grounded "must taste" recommendation pipeline for a specific Tastyroad restaurant mention in a YouTube video. Use when Codex needs to read timed YouTube captions from the Blob-backed transcript archive referenced by data/tastyroad.sqlite, scan the whole transcript with parallel attention-scout passes, aggregate repeated and high-attention menu candidates, run evidence/visitor review passes, choose only genuinely recommended menu items for one restaurant, include short direct subtitle quotes for display, and validate/store source-backed rows in video_must_taste_items by restaurant_id and youtube_video_id. Do not use this for one-shot exact-three filling, video-level Top 3, generated ad-copy reasons, story reviews, prose essays, restaurant mapping, or caption fetching.
---

# Tastyroad Transcript Must-Taste

## Overview

Use this skill after `$tastyroad-youtube-transcript-ingest` has stored timed captions. Captions may live in Vercel Blob with SQLite metadata, or in the legacy SQLite segment cache. The output is not a story and not video-level: it is a multi-pass artifact pipeline that scans the whole transcript, surfaces attention events, aggregates menu candidates, reviews each candidate, rejects weak candidates, and stores zero to three genuinely recommended transcript-supported menu items for one target restaurant.

## Workflow

1. Prepare the timed transcript context:

```bash
python3 .codex/skills/tastyroad-transcript-must-taste/scripts/prepare_must_taste_context.py --video-id <youtube_id>
```

For videos with multiple mapped restaurants, pass the target restaurant:

```bash
python3 .codex/skills/tastyroad-transcript-must-taste/scripts/prepare_must_taste_context.py \
  --video-id <youtube_id> \
  --restaurant-id <restaurant_id>
```

2. Read `data/work/must_taste/<youtube_id>/<restaurant_id>/context.json`, `task.md`, `coverage.json`, `chunks.json`, and the pass prompts under `passes/`.

3. Run the passes in this order:

- **Parallel attention scouts**: split `chunks.json` across workers/subagents when available; write only attention-worthy transcript moments to `attention_events.jsonl`.
- **Candidate aggregation**: merge attention events, aliases, and repeated mentions into `menu_candidates.json`.
- **Parallel candidate reviews**: review each candidate with at least `evidence_skeptic` and `visitor_judge`; write `candidate_reviews.json`.
- **Sequential arbiter**: select zero to three final items and write `result.json`; every non-selected candidate must appear in `rejected_candidates`.

Use subagents only for the scout/review stages. Do deterministic chunking, coverage, lineage validation, candidate/review/rejection completeness, and DB writes with scripts.

Artifact contract:

- Every artifact must carry the same `video_id`, `restaurant_id`, `transcript_track_id`, and `context_hash` from `context.json`.
- `context.json` is the source of transcript truth for extraction; it may have been assembled from `youtube_transcript_segments` or from the `segments_blob_path` Vercel Blob archive.
- `attention_events.jsonl`: one JSON object per attention event; include `event_id`, `chunk_id`, `candidate_id`, `menu_item`, `event_type`, `attention_score`, exact transcript evidence fields, `restaurant_scope_note`, and `note`.
- `menu_candidates.json`: root object with `candidates`; every attention event must be represented by a candidate with the same `candidate_id`, and each candidate must list its `event_ids`.
- `candidate_reviews.json`: root object with `reviews`; every candidate must have `evidence_skeptic` and `visitor_judge` reviews, and each review must cite `cited_event_ids` for that candidate.
- `result.json`: references the pipeline artifact paths, selects zero to three passing candidates, and rejects every non-selected candidate.

4. Create `data/work/must_taste/<youtube_id>/<restaurant_id>/result.json` with this shape:

```json
{
  "video_id": "<youtube_id>",
  "restaurant_id": 123,
  "context_hash": "context_hash_from_context",
  "pipeline": {
    "coverage_path": "data/work/must_taste/<youtube_id>/<restaurant_id>/coverage.json",
    "chunks_path": "data/work/must_taste/<youtube_id>/<restaurant_id>/chunks.json",
    "attention_events_path": "data/work/must_taste/<youtube_id>/<restaurant_id>/attention_events.jsonl",
    "candidates_path": "data/work/must_taste/<youtube_id>/<restaurant_id>/menu_candidates.json",
    "reviews_path": "data/work/must_taste/<youtube_id>/<restaurant_id>/candidate_reviews.json"
  },
  "items": [
    {
      "rank": 1,
      "candidate_id": "candidate_id_from_menu_candidates",
      "menu_item": "자막에 등장한 메뉴명",
      "reason": "상위권 감자튀김이다",
      "quality": {
        "score": 90,
        "signals": ["strong_praise"],
        "check": "감자 그 자체를 바삭하게 튀긴 상위권 감자튀김이라는 자막 근거"
      },
      "review": {
        "score": 88,
        "verdict": "pass",
        "drivers": ["would_pick_restaurant_for_this", "strong_host_praise"],
        "decision_reason": "버거집을 고르는 유저에게 사이드까지 상위권이라는 방문 이유가 됨",
        "risk": "감자튀김만으로 방문할 정도인지 약하면 제외"
      },
      "evidence": {
        "segment_index": 12,
        "timestamp": "03:21",
        "start_seconds": 201.4,
        "text": "context.json의 해당 segment text를 그대로 복사"
      },
      "supporting_evidence": []
    }
  ],
  "rejected_candidates": [
    {
      "candidate_id": "candidate_id_from_menu_candidates",
      "menu_item": "검토했지만 탈락한 메뉴명",
      "reason": "방문 선택 이유로 약하거나 근거가 부족한 이유"
    }
  ]
}
```

5. Validate and store the result:

```bash
python3 .codex/skills/tastyroad-transcript-must-taste/scripts/apply_must_taste_result.py \
  --context data/work/must_taste/<youtube_id>/<restaurant_id>/context.json \
  --result data/work/must_taste/<youtube_id>/<restaurant_id>/result.json
```

## Selection Rules

- Use only transcript segment text from `context.json` as source evidence.
- Select items for the target `restaurant` in `context.json`, not for the whole video.
- Treat the whole transcript scan as mandatory. `coverage.json` and `chunks.json` must prove every segment was available to scout passes.
- Keep attention scouting separate from final selection. Scouts find noteworthy moments; they do not decide final picks.
- Consider both intrinsic attention and repetition. Repeated neutral mentions cannot beat one strong recommendation or differentiator, but repeated attention-worthy moments should raise candidate confidence.
- Preserve lineage: every final item must come from a candidate, every candidate must come from attention event IDs, every selected candidate must pass reviews, and every non-selected candidate must be rejected with a reason.
- For multi-restaurant videos, require each attention event to explain why the cited segment belongs to the target restaurant's portion of the transcript.
- Choose at most three menu items, dishes, drinks, sauces, sides, or course components.
- Do not fill three slots by default. Store fewer than three, or zero, when the transcript does not support three genuinely recommended items.
- Do not qualify an item from mention, order, or eating alone.
- Require `quality.score` of 80 or higher and at least one qualifying signal: `explicit_recommendation`, `repeat_visit`, `differentiator`, `strong_praise`, `signature_menu`, `unique_preparation_with_praise`, or `host_must_order`.
- Treat "this is why I would come back", "this is the differentiator", "top tier", "must order", repeated explicit recommendation, or unusually strong praise as qualifying. Treat casual mentions, neutral ingredient descriptions, and ordinary ordering as insufficient.
- Require a separate `review` gate with `review.score` of 82 or higher, `review.verdict: "pass"`, and at least one visitor decision driver: `would_pick_restaurant_for_this`, `differentiated_from_common_versions`, `explicit_ordering_advice`, `strong_host_praise`, or `signature_or_specialty`.
- Review from a restaurant-selection user's perspective: "Would this menu and quote help me pick this restaurant over another one?" If the answer is only "it sounds fine" or "it was mentioned", reject it.
- Use the timestamp for the segment where that item is ordered, eaten, praised, or recommended.
- Store `reason` as a short direct subtitle quote for display, not generated ad copy. It must be an exact substring of `evidence.text` or `supporting_evidence[].text`.
- Keep `reason` to one line and prefer a quote fragment that contains the strongest transcript signal, such as `닭갈비구이 내 진짜 0.1도 안나요`, `상위권 감자튀김이다`, or `이거 진짜 똥집이다`.
- Do not over-trim the quote. Include enough words from the same evidence line so the subject and claim remain understandable.
- Do not coin idioms, polish slogans, correct ASR text, or create restaurant-level claims such as `맛있는 집`.
- Use `quality.check` and `review.decision_reason` for the explanatory judgment; keep public `reason` as source text.
- Do not add atmosphere, location, freshness, market, scenery, or other quality claims unless that claim appears in transcript evidence.
- If an appealing phrase would require inference, lower the phrase to the literal transcript-backed claim.
- Do not use video title, description, chapters, map data, address, source metadata, restaurant mapping notes, or old story review prose as evidence.
- Do not use transcript segments belonging to another restaurant in the same video.
- Do not invent a third item. If no item passes the quality gate, use `"items": []`, `"insufficient_evidence": true`, and a short `insufficient_evidence_reason`.
- Do not write `story_hook`, `story_intro`, `tasting_flow`, critic rounds, or public story prose.

## Validation Gate

`apply_must_taste_result.py` rejects output unless:

- `video_id` matches the prepared context.
- `restaurant_id` matches the prepared context.
- `context_hash` matches the prepared context.
- `pipeline` paths exist and point to `coverage.json`, `chunks.json`, `attention_events.jsonl`, `menu_candidates.json`, and `candidate_reviews.json`.
- `coverage.json` and `chunks.json` match `video_id`, `restaurant_id`, `transcript_track_id`, `context_hash`, and cover every transcript segment.
- every attention event matches an exact transcript segment and has a valid event type and score.
- every candidate has event IDs that exist in `attention_events.jsonl`.
- every candidate has both `evidence_skeptic` and `visitor_judge` reviews.
- `items` contains zero to three items; non-empty item ranks are sequential starting at 1.
- each item references a candidate from `menu_candidates.json`, and its evidence overlaps that candidate's attention events.
- each item has non-empty `menu_item`, one-line direct subtitle quote `reason`, and an `evidence` object.
- each non-empty item has `quality.score >= 80`, at least one supported quality signal, and a one-line `quality.check`.
- each non-empty item has `review.score >= 82`, `review.verdict: "pass"`, at least one supported review driver, one-line `decision_reason`, and one-line `risk`.
- quality signals do not rely on mention/order/eating alone.
- `reason` is an exact substring of `evidence.text` or `supporting_evidence[].text`.
- `evidence.segment_index`, `timestamp`, `start_seconds`, and `text` match a real transcript segment exactly.
- optional `supporting_evidence` entries also match real transcript segments exactly.
- `rejected_candidates` accounts for every candidate not selected.

Read `references/must-taste-db.md` when you need schema details or SQL examples.
