---
name: tastyroad-youtube-transcript-ingest
description: Download YouTube captions for collected Tastyroad videos through the existing youtube_transcript_api/Webshare proxy method and store raw transcript tracks plus timed segments in data/tastyroad.sqlite. Use when fetching missing transcripts, refreshing transcript coverage for a source or video, checking transcript DB status, exporting transcript text, or preparing transcript data for later summary/story extraction.
---

# Tastyroad YouTube Transcript Ingest

## Overview

Use this skill from the Tastyroad repo root to make YouTube captions a reusable SQLite data asset. This skill only fetches and stores transcripts; do not generate summaries, story prose, or restaurant mappings here.

The fetch method is the existing one: `youtube_transcript_api.YouTubeTranscriptApi` with `WebshareProxyConfig` from `.env.local`/environment variables, falling back to generic proxy env vars when present.

## Workflow

1. Check current coverage:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/transcript_status.py
```

2. Fetch missing transcripts for one source. `--source` may be the source key from `data/sources/youtube_sources.json` or the DB source name:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/fetch_transcripts.py --source <source_key> --missing-only --request-delay 1
```

3. Fetch or refresh one video:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/fetch_transcripts.py --video-id <youtube_id> --refresh
```

4. Preview a run before touching YouTube:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/fetch_transcripts.py --source <source_key> --missing-only --limit 10 --dry-run
```

5. Export the preferred transcript text for downstream LLM work:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/export_transcript_text.py --video-id <youtube_id>
```

## Rules

- Store successful tracks in `youtube_transcript_tracks` and timed rows in `youtube_transcript_segments`.
- Store failures in `youtube_transcript_fetch_attempts`; do not delete failed evidence just because a later retry may succeed.
- Prefer Korean, then English by passing `--languages ko,en` unless the task needs a different order.
- Use a request delay for source-scale runs. Stop on repeated YouTube block errors instead of pushing through a bad proxy path.
- Keep transcript ingestion separate from `$tastyroad-youtube-channel-collect` and `$tastyroad-map-video-restaurants`; those skills own video metadata and restaurant mapping, not transcript storage.

## References

Read `references/transcript-db.md` when you need schema details, environment variables, or SQL query examples.
