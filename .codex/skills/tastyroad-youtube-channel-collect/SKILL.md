---
name: tastyroad-youtube-channel-collect
description: Collect, audit, and troubleshoot Tastyroad YouTube channel video sources. Use when adding or updating sources in data/sources/youtube_sources.json, running full-channel YouTube collection instead of the RSS latest-window collector, finding videos missing from data/tastyroad.sqlite or data/raw/youtube/*.json, resolving YouTube channel IDs from handles, or deciding which sources need full-channel pipeline coverage.
---

# Tastyroad YouTube Channel Collect

## Overview

Use this skill for Tastyroad YouTube source work. The key distinction is that normal collection reads the YouTube RSS feed and only sees the latest window, while full-channel collection uses `yt-dlp --flat-playlist` to enumerate every video on a channel.

## Workflow

1. Inspect the configured source in `data/sources/youtube_sources.json`.
2. For complete channel coverage, run:

```bash
python3 scripts/collect_youtube.py --source <source_key> --full-channel --reuse-existing --workers 4
```

3. For a normal latest-window refresh, run:

```bash
python3 scripts/collect_youtube.py --source <source_key>
```

4. If the user asks which videos are not collected, run the bundled audit script:

```bash
python3 .codex/skills/tastyroad-youtube-channel-collect/scripts/audit_missing_videos.py --source <source_key>
```

5. If a source uses a handle URL and lacks `channel_id`, resolve it with:

```bash
python3 scripts/resolve_youtube_channel_id.py "https://www.youtube.com/@handle"
```

## Pipeline Checks

Check `scripts/update_pipeline.py` before assuming scheduled or one-command updates use full-channel collection. Full-channel sources should use `reuse_existing=True` and bounded workers so repeated runs only enrich new videos.

Use `data/tastyroad.sqlite` as the authoritative local DB. `data/raw/youtube/<source_key>.json` mirrors the latest collection output for that source.

Use `--workers 4` as a conservative default. Increase only when YouTube requests are stable; high worker counts can increase rate-limit failures. `--missing-only` is accepted as an alias for `--reuse-existing`.

## Audit Output

The audit script writes ignored work files by default:

- `data/work/<source_key>_full_channel_videos.tsv`
- `data/work/<source_key>_missing_videos.tsv`

The missing TSV includes `playlist_index`, `video_id`, `upload_date`, `title`, and `url`. `upload_date` may be `NA` for flat playlist entries because YouTube does not always expose it without per-video enrichment.

## References

Read `references/tastyroad-youtube-data.md` when you need the DB tables, common SQL queries, or command examples for manual audits.
