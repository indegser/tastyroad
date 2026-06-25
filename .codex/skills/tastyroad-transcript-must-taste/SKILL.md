---
name: tastyroad-transcript-must-taste
description: Run a multi-pass, transcript-grounded "must taste" recommendation pipeline for a specific Tastyroad restaurant mention in a YouTube video. Use when Codex needs to read timed YouTube captions from the object-storage-backed transcript archive referenced by data/tastyroad.sqlite, scan the whole transcript with parallel attention-scout passes, aggregate repeated and high-attention menu candidates, run evidence/visitor review passes, choose only genuinely recommended menu items for one restaurant, store expanded raw subtitle context plus source-preserving repaired display copy, and validate/store source-backed rows in video_must_taste_items by restaurant_id and youtube_video_id. Do not use this for one-shot exact-three filling, video-level Top 3, generated ad-copy reasons, story reviews, prose essays, restaurant mapping, or caption fetching.
---

# Tastyroad Transcript Must-Taste

## Overview

Use this skill after `$tastyroad-youtube-transcript-ingest` has stored timed captions. Captions may live in Supabase Storage or Vercel Blob with SQLite metadata, or in the legacy SQLite segment cache. The output is not a story and not video-level: it is a multi-pass artifact pipeline that scans the whole transcript, surfaces attention events, aggregates menu candidates, reviews each candidate, rejects weak candidates, and stores zero to three genuinely recommended transcript-supported menu items for one target restaurant.

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
- `context.json` is the source of transcript truth for extraction; it may have been assembled from `youtube_transcript_segments` or from the `segments_blob_path` object archive using the row's `storage_provider`.
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
      "reason": "감자의 맛을 흉내 낸 감자튀김이 아니다 이거는 정말 감자 그 자체를 정말 바삭하게 튀겨서 상위권 감자튀김이다",
      "repaired_reason": "감자의 맛을 흉내 낸 감자튀김이 아니라, 정말 감자 그 자체를 바삭하게 튀겨서 상위권 감자튀김이다.",
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
- For each selected item, first build a source-fragment pack from `evidence` plus `supporting_evidence` in transcript order. Add nearby same-restaurant support fragments when the strongest praise is split across subtitle/ASR boundaries.
- Choose `reason` by running a flexible source-window selector over that source-fragment pack. The selector picks raw material only; it does not repair ASR, polish text, or write public copy.
- Source-window selector prompt:
  - `너는 맛집 영상 자막에서 공개용 추천 문구의 원문 재료를 고르는 편집자다. 목표는 보정문을 쓰는 것이 아니라, 보정하기 좋은 selected_raw_reason을 고르는 것이다.`
  - `입력은 menu_item, 기존 reason, context_fragments다. context_fragments는 evidence/supporting_evidence 자막 조각이다.`
  - `메뉴의 맛, 추천, 특징을 가장 잘 보여주는 자막 구간만 고른다.`
  - `가격, 주문 전환부, 배경 설명, 잡담은 맛/추천 문장을 살리는 데 필요할 때만 포함한다.`
  - `너무 짧아서 주어/대상이 사라지면 주변 문맥을 조금 붙인다.`
  - `너무 넓어서 여러 주장이나 배경이 섞이면 줄인다.`
  - `끝이 조금 끊겨 보여도 다음 조각이 가격, 주문, 새 메뉴, 배경, 다른 주장으로 넘어가면 무리하게 붙이지 않는다. 그런 꼬리는 subtitle editor가 덜어낼 수 있는 가장 가까운 원문을 둔다.`
  - `ASR 오류, 띄어쓰기, 끊긴 문장을 고치지 않는다. 원문을 요약하거나 새 문장으로 만들지 않는다.`
  - `애매하면 더 많이 가져오지 말고, 가장 직접적인 맛 평가 구간을 고른다. selected_raw_reason은 context_fragments의 문구를 필요한 만큼 이어 붙인 원문이어야 한다.`
- Store `reason` as the selected expanded raw subtitle context copied from the selected source fragments in order. It is the auditable raw source, not public polished copy. Keep it one line, join fragments with ordinary spaces/punctuation, do not insert separators such as `/`, do not repair ASR, and do not summarize it.
- Store `repaired_reason` as the public display copy by running a flexible subtitle editor pass over `reason`. This is not a gate and not a rule checklist; it is a short editing task.
- Editor pass prompt:
  - `너는 맛집 영상 자막을 공개용 짧은 인용문으로 다듬는 편집자다. 목표는 원문을 새로 쓰는 것이 아니라, 사람이 읽을 때 어색하지 않게 아주 가볍게 보정하는 것이다.`
  - `입력은 menu_item과 raw_reason이다. raw_reason은 ASR/자막 조각이 이어진 원문이다.`
  - `원문의 말투, 순서, 표현, 감탄, 평가의 세기를 최대한 유지한다. 어색한 자막 끊김, 띄어쓰기, 반복어, 명백한 ASR 오류만 자연스럽게 고친다.`
  - `설명문, 요약문, 광고문처럼 바꾸지 않는다. 원문에 없는 평가나 결론을 덧붙이지 않는다.`
  - `모든 정보를 살리려 하지 않는다. 불확실한 ASR이나 어색한 꼬리는 추측해서 고치지 말고 덜어낸다.`
  - `맛집 목록에 붙는 짧은 인용문이므로 메뉴의 맛/추천/특징에 직접 도움이 되는 부분을 중심으로 남긴다. 가격, 주문 전환부, 배경 설명은 그 문장을 살리는 데 필요할 때만 남긴다.`
  - `끊긴 조각을 억지로 완성하지 말고, 자연스럽게 읽히는 범위만 남긴다. 같은 조건이나 연결 표현이 겹치면 원문 표현을 유지한 채 어색한 반복만 덜어낸다.`
  - `문장이 꼭 완전한 서술문일 필요는 없다. 자막 인용처럼 자연스러우면 된다.`
  - `애매하면 더 많이 고치지 말고 원문에 가깝게 둔다. 출력은 repaired_reason 문자열 하나만 낸다.`
- Do not over-trim the source context. Include enough words so the subject and claim remain understandable, even if that means using multiple supporting evidence lines.
- Do not coin idioms, polish slogans, add restaurant-level claims such as `맛있는 집`, or convert the copy into marketing/ad prose.
- Use `quality.check` and `review.decision_reason` for explanatory judgment; keep `reason` and `repaired_reason` as subtitle-grounded source text.
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
- each item has non-empty `menu_item`, one-line expanded raw subtitle context `reason`, one-line source-preserving display copy `repaired_reason`, and an `evidence` object.
- each non-empty item has `quality.score >= 80`, at least one supported quality signal, and a one-line `quality.check`.
- each non-empty item has `review.score >= 82`, `review.verdict: "pass"`, at least one supported review driver, one-line `decision_reason`, and one-line `risk`.
- quality signals do not rely on mention/order/eating alone.
- `reason` is copied from `evidence.text` plus `supporting_evidence[].text` in source order.
- `repaired_reason` is present, one line, and display-length.
- `evidence.segment_index`, `timestamp`, `start_seconds`, and `text` match a real transcript segment exactly.
- optional `supporting_evidence` entries also match real transcript segments exactly.
- `rejected_candidates` accounts for every candidate not selected.

Read `references/must-taste-db.md` when you need schema details or SQL examples.
