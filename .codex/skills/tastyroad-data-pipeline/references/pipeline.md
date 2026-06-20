# Tastyroad Pipeline Reference

## Data Model

The local SQLite database is `data/tastyroad.sqlite`.

Core flow:

```text
YouTube source config
  -> mention_candidates
  -> agent_video_reviews
  -> video_transcripts
  -> video_story_reviews
  -> place_resolution_candidates
  -> restaurants/place_links/mentions
```

The public site must read SQLite only. Pipeline scripts in this skill are the only deterministic writers.

## Important Files

- `data/sources/youtube_sources.json`: YouTube source configuration.
- `data/raw/youtube/*.json`: latest collection mirrors.
- `data/agent_reviews/video_reviews.json`: reviewed video triage decisions.
- `data/story_reviews/*.json`: Codex story reviews.
- `data/verified_places/*.json`: verified place promotion input.
- `data/work/videos/{video_id}/`: agent task and result artifacts.

## Agent Stages

- `restaurant_triage`: classify collected videos as `restaurant_intro`, `not_restaurant`, or `uncertain`.
- `transcript_fetch`: fetch transcript segments and transcript text.
- `story_review`: create public story fields and evidence JSON from transcripts.
- `place_extraction`: extract candidate place mentions.
- `place_verification`: verify selected map/place entities.

Only successful artifacts should be imported with:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/reduce_agent_artifacts.py --apply
```

## Common Commands

Status:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/pipeline_status.py
```

Full refresh:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/update_pipeline.py
```

Single transcript retry:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/agent_pipeline.py --stage transcript_fetch --run --refresh --video-id VIDEO_ID
python3 .codex/skills/tastyroad-data-pipeline/scripts/reduce_agent_artifacts.py --stage transcript_fetch --apply
```

Story review:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/agent_pipeline.py --stage story_review --run --limit 1
python3 .codex/skills/tastyroad-data-pipeline/scripts/reduce_agent_artifacts.py --stage story_review --apply
```

Place promotion:

```bash
python3 .codex/skills/tastyroad-data-pipeline/scripts/promote_verified_places.py
```

## Story Quality Gate

Story review imports require:

- `story_hook`, `story_intro`, and `tasting_flow`
- transcript-grounded `evidence`
- actual tasting order in `evidence.tasting_order`
- at least three critic rounds
- final critic decision `pass`
- no generic provenance text in public story prose

The reducer and story processor enforce these checks before writing SQLite.
