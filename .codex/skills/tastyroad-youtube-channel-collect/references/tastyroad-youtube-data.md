# Tastyroad YouTube Data Reference

## Important Files

- `data/sources/youtube_sources.json`: configured YouTube sources; each source needs `key`, `name`, `channel_id` or `feed_url`, and cleanup filters.
- `.codex/skills/tastyroad-youtube-channel-collect/scripts/collect_youtube.py`: collector for RSS latest-window and full-channel modes.
- `.codex/skills/tastyroad-data-pipeline/scripts/update_pipeline.py`: orchestrated project update; check `full_channel_keys`.
- `data/raw/youtube/<source_key>.json`: latest collection output per source.
- `data/tastyroad.sqlite`: authoritative local database.

## Useful Queries

List collected channels:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select source, count(*) as video_count, min(published_at) as oldest, max(published_at) as newest from video_pipeline_status group by source order by source;"
```

List collected IDs for one source:

```bash
sqlite3 -noheader data/tastyroad.sqlite "select external_id from mention_candidates join sources on sources.id=mention_candidates.source_id where sources.name='<source_name>' order by external_id;"
```

Show pipeline status for one source:

```bash
sqlite3 -header -column data/tastyroad.sqlite "select published_at, title, url, review_status, mapping_status from video_pipeline_status where source='<source_name>' order by published_at desc;"
```

## Manual Full-Channel Listing

Use this when you need a quick read-only channel inventory:

```bash
yt-dlp --quiet --no-warnings --flat-playlist --extractor-args youtube:lang=ko --print-to-file "%(playlist_index)s\t%(id)s\t%(upload_date)s\t%(title)s\t%(webpage_url)s" /tmp/<source_key>_full.tsv https://www.youtube.com/channel/<channel_id>/videos
```

Compare the resulting video IDs with `mention_candidates.external_id` for the source.

## Fast Collection

Use this for normal full-channel refreshes after a source has already been collected once:

```bash
python3 .codex/skills/tastyroad-youtube-channel-collect/scripts/collect_youtube.py --source <source_key> --full-channel --reuse-existing --workers 4
```

`--reuse-existing` reads existing candidates from `data/tastyroad.sqlite` and `data/raw/youtube/<source_key>.json`, keeps their enriched metadata, and only fetches per-video details for new or missing IDs. `--missing-only` is an alias for the same behavior.
