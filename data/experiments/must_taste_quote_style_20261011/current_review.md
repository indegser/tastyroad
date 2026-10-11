# Combined Candidate Review Prompt

For each candidate, emit two review objects in one JSON response:

- `evidence_skeptic`: transcript grounding, overclaiming risk, wrong-restaurant risk, and whether evidence is stronger than mention/order/eating alone.
- `visitor_judge`: whether the menu and quote would help a visitor choose this restaurant over another one.

Each review object must still match the existing `candidate_reviews.json` contract: `candidate_id`, `reviewer`, `verdict`, `score`, `drivers`, `reason`, `risk`, and `cited_event_ids`.

Use `verdict: fail` for weak mentions, ordinary ordering, flat ingredient labels, or events outside the restaurant window. Use `borderline` only when the evidence is real but probably not enough for a final item.

Final-selection rules:

- Select zero to three items; never fill the second or third slot merely because space remains.
- Every selected item must independently give a visitor a strong reason to choose the restaurant.
- Avoid overlapping recommendations from the same course or plate. When a broad course/set candidate and one of its component cuts or dishes rely on substantially the same tasting evidence, keep only the more specific, stronger, visitor-useful candidate.
- Keep both a broad course and a component only when each has distinct transcript evidence and communicates a genuinely different choice a visitor can make.
- A third item needs the same strong standard as rank 1: explicit recommendation, repeat-visit intent, signature/differentiating value, or unusually strong praise. Mild positive tasting language is insufficient.
- Put every valid but non-selected overlapping or weaker candidate in `rejected_candidates` with the concrete duplication or evidence-strength reason.
