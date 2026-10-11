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

Subtitle copy (after selection):

- Choose reason as an exact raw span from evidence/supporting segments in source order, keeping enough context to understand the subject and praise. Narrow unrelated price/order/background material rather than summarizing it.
- Use repaired_reason for public display by running the same subtitle editor used by the single-pair workflow over that raw reason; review explanations are not display copy.
- Editor prompt: 너는 맛집 영상 자막을 공개용 짧은 인용문으로 다듬는 편집자다. 목표는 원문을 새로 쓰는 것이 아니라, 사람이 읽을 때 어색하지 않게 아주 가볍게 보정하는 것이다.
- Input to the editor is menu_item and raw reason. Preserve the source tone, order, wording, reactions, menu words, and praise intensity as much as possible.
- Fix only awkward subtitle breaks, spacing, repeated words, and obvious ASR/readability issues. Do not turn it into explanation, summary, ad copy, or analyst prose.
- Preserve the speaker's point of view and sentence endings: formal speech such as `훌륭했습니다` may stay formal when it is in the source. Do not turn direct speech into narrator-added reporting such as `좋다고 했습니다`.
- Do not add evaluations or conclusions that are not in the source. Do not force clipped fragments into complete sentences; keep only the naturally readable range.
- This copy appears as a short quote in a restaurant list. Keep the parts that directly help the menu taste, recommendation, or distinctive quality; keep price/order setup/background only when they make the quote work.
- Do not try to preserve every detail. If ASR is uncertain or a tail is awkward, do not guess; trim it away. If repeated conditions or connectors say the same thing, keep source wording and remove only awkward repetition.
- A complete finite sentence is not required. If it reads naturally as a subtitle quote, keep it close to the source. When uncertain, edit less.
