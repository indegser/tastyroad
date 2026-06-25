# Must-Taste DB Reference

## Source Tables

Use `preferred_youtube_transcripts` from `$tastyroad-youtube-transcript-ingest`. Timed segments may come from the legacy `youtube_transcript_segments` cache or from the object storage item referenced by `segments_blob_path` and `storage_provider`.

The must-taste skill does not fetch captions. If `prepare_must_taste_context.py` reports that no preferred transcript exists, run transcript ingest first.

`prepare_must_taste_context.py` first reads `youtube_transcript_segments`. If no cached rows exist, it downloads and expands `segments_blob_path` from the private `tastyroad-transcripts` Supabase Storage bucket based on `storage_provider`. The generated `context.json` is the extraction source of truth either way.

## Work Artifacts

Prepared and generated artifacts live under `data/work/must_taste/<video_id>/<restaurant_id>/`.

- `coverage.json`: proves every transcript segment was available to scout passes.
- `chunks.json`: deterministic chunk list for whole-transcript scout coverage.
- `attention_events.jsonl`: source-backed attention moments with exact segment evidence and a target-restaurant scope note.
- `menu_candidates.json`: candidate menu aggregation from attention events, including repeated/high-attention signals.
- `candidate_reviews.json`: at least `evidence_skeptic` and `visitor_judge` reviews per candidate.
- `result.json`: final zero-to-three selected candidates plus `rejected_candidates` for every non-selected candidate.

Every artifact must share `video_id`, `restaurant_id`, `transcript_track_id`, and `context_hash`. `apply_must_taste_result.py` rejects stale or incomplete artifact chains.

## Output Table

`video_must_taste_items`: one row per ranked, quality-gated recommendation for one restaurant mention in one video. A restaurant-video pair can have zero to three rows.

Important columns:

- `restaurant_id`: target restaurant card.
- `youtube_video_id`, `video_id`: source video identity.
- `rank`: sequential rank from 1 to 3 when recommendations exist.
- `item_name`: menu item chosen from transcript evidence after passing the quality and visitor-review gates.
- `reason`: expanded raw subtitle context copied from cited primary/supporting transcript evidence in source order. This is the auditable raw source, not public polished copy.
- `repaired_reason`: source-preserving repaired display copy derived from `reason` by the subtitle editor prompt. It should feel like a lightly edited subtitle quote, not a summary, explanation, ad phrase, or generated review.
- `segment_index`, `start_seconds`, `end_seconds`, `timestamp_label`: timed evidence location.
- `evidence_text`: exact transcript segment text copied from `context.json`.
- `transcript_track_id`: preferred transcript track used for extraction.
- `evidence_json`: provenance for context/result paths, transcript language, `candidate_id`, pipeline artifact paths, rejected candidates, quality score/signals/check, visitor review score/drivers, and optional supporting evidence.

## Useful Queries

Recommendations for one restaurant/video pair:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select rank, item_name, repaired_reason, reason as raw_reason, timestamp_label, evidence_text from video_must_taste_items where restaurant_id=<restaurant_id> and video_id='<video_id>' order by rank;"
```

Coverage:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select source, count(*) as restaurant_videos_with_recommendations from video_must_taste_top3 group by source order by source;"
```

Recent stored results:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select restaurant_id, video_id, rank, item_name, timestamp_label, generated_at from video_must_taste_items order by generated_at desc, restaurant_id, video_id, rank limit 30;"
```
