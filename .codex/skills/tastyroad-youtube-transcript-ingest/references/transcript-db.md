# Transcript DB Reference

## Environment

The fetch script loads `.env.local` from the repo root before reading process env.

Webshare variables:

```bash
WEBSHARE_PROXY_USERNAME=
WEBSHARE_PROXY_PASSWORD=
WEBSHARE_PROXY_LOCATIONS=kr,jp
WEBSHARE_PROXY_RETRIES_WHEN_BLOCKED=10
WEBSHARE_PROXY_DOMAIN=p.webshare.io
WEBSHARE_PROXY_PORT=80
```

Fallback generic proxy variables:

```bash
YT_TRANSCRIPT_HTTP_PROXY=
YT_TRANSCRIPT_HTTPS_PROXY=
```

The Python environment must provide `youtube_transcript_api`.

Vercel Blob variables:

```bash
BLOB_READ_WRITE_TOKEN=
VERCEL_OIDC_TOKEN=
BLOB_STORE_ID=
VERCEL_BLOB_SCOPE=jaekwon-hans-projects
```

Local and pipeline scripts use the official `vercel blob` CLI through `transcript_blob_store.py`. A static `BLOB_READ_WRITE_TOKEN` is enough for local/off-Vercel scripts. If using OIDC, `VERCEL_OIDC_TOKEN` and `BLOB_STORE_ID` must both be present.

Supabase Storage variables:

```bash
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=tastyroad-transcripts
TRANSCRIPT_STORAGE_PROVIDER=supabase_storage
```

The Tastyroad transcript bucket/store is private and named `tastyroad-transcripts`. Supabase Storage is the current canonical archive target; Vercel Blob rows remain readable when that store is active.

## Tables

`youtube_transcript_jobs`: One row per fetch run, including scope, requested language order, final status, and stats.

`youtube_transcript_tracks`: One successful transcript track per `(youtube_video_id, language_code, is_generated, provider)`. `content_hash` detects unchanged content. New object-storage-backed rows store provider-neutral object pathnames and sizes in `raw_blob_path`, `segments_blob_path`, `raw_blob_size`, `segments_blob_size`, `storage_provider`, `blob_uploaded_at`, and `blob_metadata_json`. `transcript_text` remains a small export cache. `raw_json` is a compatibility field and should stay `[]` for object-storage-only rows.

`youtube_transcript_segments`: Compatibility/cache table for normalized timed rows. New object-storage-only rows may not have SQLite segment rows; downstream scripts should read `segments_blob_path` with `storage_provider` when this table has no rows.

`youtube_transcript_fetch_attempts`: One row per attempted video fetch. Store failed attempts here with `error_type` and `error_message`.

`video_transcripts`: Legacy timed-caption table retained only during migration. If rows remain here, archive them with `archive_legacy_video_transcripts.py` so `youtube_transcript_tracks` owns the metadata and object storage owns raw/segment payloads. Drop this table only after every legacy row has an object-storage-backed track. Use `--replace-existing` before dropping if existing tracks point at a suspended provider.

## Views

`preferred_youtube_transcripts`: One preferred track per video. Ranking is:

1. Korean manual
2. Korean auto-generated
3. English manual
4. English auto-generated
5. Any other manual
6. Any other auto-generated

`youtube_transcript_status`: Per-video coverage status joined with source/video metadata and the latest fetch attempt.

## Useful Queries

Coverage by source:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select source, transcript_status, count(*) from youtube_transcript_status group by source, transcript_status order by source, transcript_status;"
```

Recent failures:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select video_id, error_type, substr(error_message, 1, 120) as error, attempted_at from youtube_transcript_fetch_attempts where status='failed' order by attempted_at desc limit 20;"
```

Timed transcript sample:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select s.segment_index, s.start_seconds, s.text from preferred_youtube_transcripts p join youtube_transcript_segments s on s.track_id=p.id where p.video_id='<video_id>' order by s.segment_index limit 20;"
```

Object-storage-backed timed transcript path:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select video_id, storage_provider, segments_blob_path, segments_blob_size from preferred_youtube_transcripts where video_id='<video_id>';"
```

Legacy rows still outside the new transcript tables:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select s.name as source, count(*) as legacy_rows from video_transcripts vt join youtube_videos y on y.video_id=vt.external_id join sources s on s.id=y.source_id where not exists (select 1 from youtube_transcript_tracks t where t.youtube_video_id=y.id) group by s.name;"
```

Preferred full text length:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select video_id, language_code, is_generated, segment_count, length(transcript_text) as text_length from preferred_youtube_transcripts order by fetched_at desc limit 20;"
```

Storage split:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select storage_provider, count(*) as tracks, round(sum(segments_blob_size + raw_blob_size) / 1024.0 / 1024.0, 2) as blob_mb from preferred_youtube_transcripts group by storage_provider;"
```
