---
name: tastyroad-site-release
description: Deploy the Tastyroad Next.js site through the GitHub-to-Vercel integration. Use when Codex is in the Tastyroad repo and the user says "배포해", asks to deploy/release, asks for a GitHub-based deployment, or needs the Vercel deployment response/status after pushing commits. Prefer git push plus Vercel status lookup over local `vercel deploy`.
---

# Tastyroad Site Release

## Overview

Use this skill from the Tastyroad repo root to release the site through the GitHub integration that triggers Vercel. The normal production path is: validate locally, commit the intended changes, push `main` to GitHub, then fetch the Vercel deployment result for that commit.

## Project Facts

- GitHub repo: `indegser/tastyroad`
- Production branch: `main`
- Vercel project: `tastyroad`
- Vercel scope: `jaekwon-hans-projects`
- Production aliases include `https://taste.indegser.com` and `https://tastyroad-flame.vercel.app`
- Local Vercel project IDs live in `.vercel/project.json`. Do not commit `.vercel/`.

## Release Workflow

1. Inspect local state.

```bash
git status --short --branch
git remote -v
git fetch origin main
```

If local `main` is behind `origin/main`, fast-forward with `git pull --ff-only` before releasing. If the branch diverged or the dirty files are ambiguous, stop and explain the conflict instead of forcing a merge.

2. Validate locally.

```bash
pnpm run build
```

3. Commit only the intended release changes.

Use `git diff --stat`, `git diff --name-only`, and targeted `git add <path>` commands. Do not silently stage unrelated dirty files. Never stage `.env*`, `.vercel/`, `.next/`, `node_modules/`, `out/`, `data/work/`, or transient SQLite sidecar files.

If there are no local changes, check whether the current `HEAD` already has a READY Vercel deployment and report that instead of creating an empty commit or using local deploy.

4. Push through GitHub.

For the default Korean request `배포해`, treat the target as production and push `main`:

```bash
sha=$(git rev-parse HEAD)
git push origin main
```

If the user explicitly asks for a preview deployment, push the feature branch instead and report the preview deployment. Do not switch branches or deploy `main` from a non-`main` branch without making the target clear.

5. Get the Vercel deployment response for the pushed commit.

Prefer the Vercel MCP deployment list when available. Read `.vercel/project.json` for `projectId` and `orgId`/team ID, then list deployments and match `meta.githubCommitSha` to `sha`.

If the Vercel MCP is unavailable or returns a team scope 403, use the authenticated local Vercel CLI without asking the user again:

```bash
vercel ls tastyroad --scope jaekwon-hans-projects --format=json --meta githubCommitSha="$sha"
vercel inspect "<deployment-url>" --scope jaekwon-hans-projects --wait --timeout 5m --format=json
```

Poll every 10-15 seconds for up to 5 minutes until the matching deployment reaches `READY`, `ERROR`, or `CANCELED`. If multiple deployments match the same SHA, choose the newest deployment for the target environment. For failures, fetch build logs:

```bash
vercel inspect "<deployment-url>" --scope jaekwon-hans-projects --logs
```

6. Verify the deployed site.

Check the production alias for production releases and the deployment URL for previews:

```bash
curl -fsS "https://taste.indegser.com/api/restaurants?limit=1&includeFacets=true"
```

For protected preview URLs, use the Vercel MCP web fetch tool if available. Confirm the response is HTTP 200 and contains an `items` array.

## Safety Rules

- Do not use `vercel deploy`, `vercel --prod`, `vercel build`, or `vercel deploy --prebuilt` for the normal release path. Use those only if the user explicitly asks for direct Vercel CLI deployment or approves a fallback after GitHub integration fails.
- Do not commit generated build output or local Vercel metadata.
- Do not force-push, reset, or rewrite release history.
- If local build, GitHub push, or Vercel deployment fails, stop and report the failing command plus the shortest useful error summary.

## Report Format

End with a concise result:

```text
Deploy Result
- URL: <deployment-url>
- Alias: <production-alias-or-preview-url>
- Target: production | preview
- Status: READY | ERROR | CANCELED | BUILDING
- Commit: <short-sha> <commit message>
- Source: GitHub integration
- Build duration: <seconds if available>
- Vercel response: <HTTP status and endpoint checked>
```
