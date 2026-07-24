---
name: tastyroad-youtube-channel-collect
description: Collect, audit, and troubleshoot Tastyroad YouTube channel video sources. Use when adding or updating sources in data/sources/youtube_sources.json, running full-channel YouTube collection instead of the RSS latest-window collector, finding youtube_videos rows missing from data/tastyroad.sqlite or data/raw/youtube/*.json, resolving YouTube channel IDs from handles, or deciding which sources need full-channel coverage.
---

# Tastyroad YouTube Channel Collect

## Overview

Use this skill from the Tastyroad repo root for YouTube source work. The repository no longer owns collection scripts; run the bundled scripts in this skill.

The key distinction is that normal collection reads the YouTube RSS feed and only sees the latest window, while full-channel collection uses `yt-dlp --flat-playlist` to enumerate every video on a channel or, when configured, a source-specific `playlist_url`.

## Workflow

1. Inspect the configured source in `data/sources/youtube_sources.json`.
   - If YouTube exposes the source as a show playlist rather than the channel `/videos` tab, set `playlist_url` on the source and run full-channel collection.
   - If one source spans multiple official playlists, set `playlist_urls` to collect them with the channel or primary playlist under the same source key.
2. For complete channel coverage, run:

```bash
python3 .codex/skills/tastyroad-youtube-channel-collect/scripts/collect_youtube.py --source <source_key> --full-channel --reuse-existing --workers 4
```

If YouTube is returning repeated HTTP 429 responses during per-video detail
enrichment, stop the detail requests and preserve the official playlist
IDs/titles first:

```bash
python3 .codex/skills/tastyroad-youtube-channel-collect/scripts/collect_youtube.py \
  --source <source_key> --full-channel --reuse-existing --skip-details
```

Rows without detail fields remain retryable in a later `--reuse-existing` run.

3. For a normal latest-window refresh, run:

```bash
python3 .codex/skills/tastyroad-youtube-channel-collect/scripts/collect_youtube.py --source <source_key>
```

4. If the user asks which videos are not collected, run the bundled audit script:

```bash
python3 .codex/skills/tastyroad-youtube-channel-collect/scripts/audit_missing_videos.py --source <source_key>
```

5. If a source uses a handle URL and lacks `channel_id`, resolve it with:

```bash
python3 .codex/skills/tastyroad-youtube-channel-collect/scripts/resolve_youtube_channel_id.py "https://www.youtube.com/@handle"
```

## Data Checks

Use `data/tastyroad.sqlite` as the authoritative local DB. Collected videos live in `youtube_videos`; restaurant mappings live separately in `youtube_video_restaurants`. `data/raw/youtube/<source_key>.json` mirrors the latest collection output for that source.

Use `--workers 4` as a conservative default. Increase only when YouTube requests are stable; high worker counts can increase rate-limit failures. `--missing-only` is accepted as an alias for `--reuse-existing`. Reuse skips complete enriched rows, but rows missing detail fields such as `published_at` or `duration_seconds` remain retryable.

For transcript download/storage, use `$tastyroad-youtube-transcript-ingest`. For restaurant mapping status, Naver place ID verification, or `mapping_pending` / `needs_review` work, use `$tastyroad-map-video-restaurants`.

## Audit Output

The audit script writes ignored work files by default:

- `data/work/<source_key>_full_channel_videos.tsv`
- `data/work/<source_key>_missing_videos.tsv`

The missing TSV includes `playlist_index`, `video_id`, `upload_date`, `title`, and `url`. `upload_date` may be `NA` for flat playlist entries because YouTube does not always expose it without per-video enrichment.

## References

Read `references/tastyroad-youtube-data.md` when you need the DB tables, common SQL queries, or command examples for manual audits.
