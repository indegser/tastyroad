---
name: tastyroad-youtube-transcript-ingest
description: Download YouTube captions for collected Tastyroad videos through the existing youtube_transcript_api/Webshare proxy method, archive raw tracks plus timed segments in object storage, and store transcript metadata in data/tastyroad.sqlite. Use when fetching missing transcripts, refreshing transcript coverage for a source or video, checking transcript DB status, exporting transcript text, archiving existing SQLite transcripts to Supabase Storage, migrating legacy Vercel Blob-backed rows, or preparing transcript data for later must-taste extraction.
---

# Tastyroad YouTube Transcript Ingest

## Overview

Use this skill from the Tastyroad repo root to make YouTube captions a reusable object-storage-backed data asset. This skill only fetches and stores transcripts; do not generate must-taste selections, summaries, prose, or restaurant mappings here.

The fetch method is the existing one: `youtube_transcript_api.YouTubeTranscriptApi` with `WebshareProxyConfig` from `.env.local`/environment variables, falling back to generic proxy env vars when present.

The storage method is object storage for raw provider payloads and normalized timed segments, with SQLite retaining transcript metadata, fetch attempts, text export cache, and object pathnames. Supabase Storage is the canonical target when `--storage-provider supabase_storage` or `TRANSCRIPT_STORAGE_PROVIDER=supabase_storage` is set. Vercel Blob support remains only for explicit legacy recovery when the Blob store is active. Use the private `tastyroad-transcripts` bucket unless the task explicitly requires a different target.

## Workflow

1. Check current coverage:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/transcript_status.py
```

2. Fetch missing transcripts for one source. `--source` may be the source key from `data/sources/youtube_sources.json` or the DB source name:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/fetch_transcripts.py --source <source_key> --missing-only --storage-provider supabase_storage --request-delay 1
```

By default, successful fetches upload:

- `transcripts/raw/<video_id>/<language>-<manual|generated>-<content_hash>.json.gz`
- `transcripts/segments/<video_id>/<language>-<manual|generated>-<content_hash>.jsonl.gz`

and store only metadata plus joined transcript text in SQLite. For a local fallback without object storage, pass `--storage sqlite`. For a transition copy in both places, pass `--storage both`.

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

6. Archive existing SQLite transcript payloads to object storage before pruning the DB:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/archive_existing_transcripts.py --missing-only --storage-provider supabase_storage --dry-run
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/archive_existing_transcripts.py --missing-only --storage-provider supabase_storage --prune-sqlite-payload
```

7. Archive legacy `video_transcripts` rows into object-storage-backed `youtube_transcript_tracks` when old timed captions exist outside the new transcript tables:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/archive_legacy_video_transcripts.py --source <source_key> --storage-provider supabase_storage --missing-tracks-only --dry-run
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/archive_legacy_video_transcripts.py --source <source_key> --storage-provider supabase_storage --missing-tracks-only --drop-legacy-table-if-archived
```

8. Migrate legacy Vercel Blob-backed track metadata to Supabase Storage:

```bash
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/migrate_vercel_blob_to_supabase.py --env-file <pulled_env> --dry-run
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/migrate_vercel_blob_to_supabase.py --env-file <pulled_env> --payload-sqlite <historical_sqlite_with_segments> --dry-run
python3 .codex/skills/tastyroad-youtube-transcript-ingest/scripts/migrate_vercel_blob_to_supabase.py --env-file <pulled_env> --payload-sqlite <historical_sqlite_with_segments>
```

Use `--payload-sqlite` when the Vercel Blob store is suspended and direct `vercel blob get` returns 403, but a historical tracked SQLite database still contains `raw_json` and `youtube_transcript_segments`.

## Rules

- Store successful transcript payloads in Supabase Storage unless a task explicitly targets legacy Vercel Blob recovery. Keep `youtube_transcript_tracks` as the source of truth for metadata, preferred-track ranking, content hash, object pathnames, fetch time, and export text.
- Do not add new large raw transcript blobs to Git or to public site runtime data.
- `youtube_transcript_segments` is now a compatibility/cache table. New object-storage-only fetches may leave it empty; downstream consumers must use `segments_blob_path` and `storage_provider` when needed.
- `video_transcripts` is legacy-only. If it contains timed caption rows that are not represented in `youtube_transcript_tracks`, use the legacy archive script to create object-storage-backed tracks before dropping the table. If existing tracks point at a suspended provider, migrate them to Supabase before deleting any remaining recoverable payload source.
- Store failures in `youtube_transcript_fetch_attempts`; do not delete failed evidence just because a later retry may succeed.
- Prefer Korean, then English by passing `--languages ko,en` unless the task needs a different order.
- Use a request delay for source-scale runs. Stop on repeated YouTube block errors instead of pushing through a bad proxy path.
- Keep transcript ingestion separate from `$tastyroad-transcript-must-taste`, `$tastyroad-youtube-channel-collect`, and `$tastyroad-map-video-restaurants`; those skills own must-taste extraction, video metadata, and restaurant mapping, not transcript storage.

## References

Read `references/transcript-db.md` when you need schema details, environment variables, or SQL query examples.
