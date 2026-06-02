# Design Review Loop

This document defines an LLM-centered design review workflow for the public
site. It is intentionally not a scoring script. The loop should behave like a
human product designer reviewing a real screen: look, judge, explain the issue,
make a small change, and look again.

## Goal

Use this workflow after meaningful UI changes, especially typography, layout,
content hierarchy, mobile readability, and list/card density changes.

The expected output is not a numeric grade. The expected output is:

- a visual judgment grounded in screenshots
- a short list of concrete issues
- one small design patch at a time
- a new screenshot after the patch
- a final decision to stop or continue

## Operating Model

```text
local app
  -> agent-browser screenshot
  -> LLM visual review
  -> targeted code edit
  -> build/check
  -> agent-browser screenshot
  -> LLM visual review
```

The LLM owns the judgment. Browser automation only provides evidence. Build and
type checks only prove that the page still runs.

## Reviewer Role

The reviewer should act like a pragmatic product designer, not a linter.

Review from the user's visual experience first:

- What catches the eye first?
- Is that the intended primary object?
- Can the screen be scanned in 3 seconds?
- Does the mobile layout feel dense, sparse, or balanced?
- Are secondary details visibly secondary?
- Does link styling communicate clickability without taking over?
- Does long Korean text read comfortably?
- Is spacing helping the hierarchy or just consuming room?

Avoid generic advice. Every finding should refer to something visible in the
current screenshot.

## Loop Budget

Default to 3 loops.

Stop earlier when:

- the main hierarchy is correct
- no visible overlap or truncation problem remains
- remaining comments are taste-level rather than usability-level
- another pass would only churn small style values

Continue beyond 3 loops only when a visible regression remains.

## Viewports

Always review mobile first for this site because the primary experience is a
vertical list.

Default viewports:

- mobile: `590 x 1280`
- narrow mobile: `390 x 844`
- desktop: `1120 x 900`

Use dark mode only when the change touches color, contrast, or theme behavior.

## Review Dimensions

### Hierarchy

Check whether the restaurant name is the strongest card element. Channel,
upload time, video title, and story should step down clearly.

### Typography

Check Korean readability:

- line height
- paragraph density
- overly long link lines
- font weight contrast
- title size relative to metadata

### Interaction Cues

Links must look clickable, but not dominate the card unless the link is the
primary action. For this site, restaurant identity is primary and video link is
secondary.

### Rhythm

Cards should have a repeatable rhythm. A story card can be taller, but it should
not feel like a different component unless the content deserves it.

### Content Fit

Long titles, emoji, Latin restaurant names, and Korean body text should wrap
without crowding the index column or creating awkward isolated marks.

## Per-Loop Procedure

1. Start or reuse the local server.
2. Capture the relevant viewport with `agent-browser`.
3. Inspect the screenshot visually.
4. Write a concise review:
   - `What works`
   - `Issues`
   - `Patch intent`
   - `Stop/continue decision`
5. Make the smallest code change that addresses the top issue.
6. Run the project check.
7. Capture again.
8. Compare against the previous screenshot.

Do not make several subjective style changes at once unless they are tightly
coupled, such as link color and underline behavior.

## Prompt Template

Use this prompt after each screenshot:

```text
Review this screen as a product designer.

Intent:
- The page should be a restaurant-first latest list.
- Restaurant name is primary.
- Channel is secondary.
- Video title is a small but obvious link.
- Verified/status metadata should not be visible.
- Story text should appear only when present and should be readable.

Look at the screenshot, then answer:
1. What is the first thing the eye reads?
2. Does the hierarchy match the intent?
3. What is the most important visible problem?
4. What is the smallest patch that would improve it?
5. Should we stop or run another loop?

Do not give a numeric score. Do not list theoretical best practices unless they
apply to this screenshot.
```

## Result Template

Each loop should leave a short note in the conversation or in a Markdown review
file:

```text
Loop N

Viewport:
Screenshot:

What works:
Issues:
Patch:
Decision:
```

## Current Site Notes

For the current list design, the common failure mode is letting the YouTube
title become visually dominant again. If the link is blue, bold, underlined, and
two lines long, it can overpower the restaurant name even when the DOM hierarchy
is correct.

Prefer:

- restaurant name as the strongest text
- channel and upload time combined as subdued metadata
- video title as a smaller secondary link
- story body with comfortable line height and slightly softened color

