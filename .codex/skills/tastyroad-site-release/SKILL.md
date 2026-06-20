---
name: tastyroad-site-release
description: Verify, package, and deploy the Tastyroad Next.js site using bundled skill scripts. Use when Codex needs to check the public listing contract, copy SQLite into Vercel prebuilt function bundles, run a local or production listing verification, or prepare a Tastyroad release without repo-level scripts.
---

# Tastyroad Site Release

## Overview

Use this skill from the Tastyroad repo root. The public site reads `data/tastyroad.sqlite`; the release scripts live inside this skill, not in the repo root.

## Public Listing Contract

A public card may render only when the video has both:

- a valid `video_story_reviews` row with story text above the quality floor
- verified map promotion through `mentions`, `restaurants`, and `place_links`

Verify the contract locally after a build:

```bash
python3 .codex/skills/tastyroad-site-release/scripts/verify_public_listing_contract.py
```

Verify production:

```bash
python3 .codex/skills/tastyroad-site-release/scripts/verify_public_listing_contract.py --url https://taste.indegser.com
```

## Release Flow

1. Refresh data with `$tastyroad-data-pipeline` if the SQLite DB needs updates.
2. Run `pnpm run build`.
3. Run the local public listing verifier from this skill.
4. For Vercel prebuilt deployment, copy SQLite into function bundles:

```bash
python3 .codex/skills/tastyroad-site-release/scripts/prepare_vercel_output.py
```

5. Deploy with the Vercel CLI or Vercel plugin, then run production verification.

## Safety Rules

- Do not add release scripts back to the repo root.
- Do not deploy before the local public listing verifier passes.
- After deployment, verify the production URL before reporting completion.
- Read `references/public-listing-contract.md` when changing eligibility logic or card rendering rules.
