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

## Tables

`youtube_transcript_jobs`: One row per fetch run, including scope, requested language order, final status, and stats.

`youtube_transcript_tracks`: One successful transcript track per `(youtube_video_id, language_code, is_generated, provider)`. `raw_json` stores the provider segment payload, `transcript_text` stores joined text, and `content_hash` detects unchanged content.

`youtube_transcript_segments`: One normalized timed row per transcript segment. Keep `raw_json` for provider-level details and use `text`, `start_seconds`, `duration_seconds`, and `end_seconds` for downstream processing.

`youtube_transcript_fetch_attempts`: One row per attempted video fetch. Store failed attempts here with `error_type` and `error_message`.

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

Preferred full text length:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select video_id, language_code, is_generated, segment_count, length(transcript_text) as text_length from preferred_youtube_transcripts order by fetched_at desc limit 20;"
```
