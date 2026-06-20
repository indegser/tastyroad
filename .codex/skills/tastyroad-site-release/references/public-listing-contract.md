# Public Listing Contract

Tastyroad public cards must be a strict subset of verified pipeline data.

## Eligibility

A restaurant can render publicly only when all of these are true:

- the source video has `agent_video_reviews.decision = 'restaurant_intro'`
- the source video has a `video_story_reviews` row
- `story_intro` is at least 240 trimmed characters
- `tasting_flow` is at least 180 trimmed characters
- either `story_hook` or `story_intro` is non-empty
- the restaurant is connected through `mentions`
- the restaurant has a `place_links` row with a verified map URL

Map verification alone is not enough for public listing. Story without verified map promotion is not enough either.

## Verification

After a local build, verify the generated or dynamic home route:

```bash
python3 .codex/skills/tastyroad-site-release/scripts/verify_public_listing_contract.py
```

After production deploy:

```bash
python3 .codex/skills/tastyroad-site-release/scripts/verify_public_listing_contract.py --url https://taste.indegser.com
```

The verifier compares expected public restaurant count from SQLite with rendered `video-card` and `story-section` counts.

## Vercel Prebuilt Packaging

When using `vercel build --prod`, copy the SQLite DB into every function bundle before deploy:

```bash
python3 .codex/skills/tastyroad-site-release/scripts/prepare_vercel_output.py
```
