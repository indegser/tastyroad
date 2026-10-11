# Video-Level Must-Taste Two-Response Task

- Read `video_context.json` and `blocks.json` first.
- Use `segment_lookup.json` only to resolve exact segment indices around candidate moments.
- Semantic response 1 writes `candidate_findings.json`.
- Semantic response 2 writes `pair_results_bundle.json`.
- Use `combined_candidate_review.md` for the combined reviews in response 2.

Workflow:

1. Response 1 scans every block once for the whole video, identifies conservative restaurant windows, and writes one `pairs` row per restaurant with source-backed `attention_events`.
2. Each attention event includes only semantic fields plus `segment_index`: event_id, candidate_id, menu_item, event_type, attention_score, scope_note, and note. Check the exact segment index in the lookup; deterministic materialization copies timestamp/text/chunk metadata.
3. Response 2 reads the compact findings, then only the narrow segment lookup ranges needed for those candidates. It writes one `pairs` row per restaurant with candidates, both candidate reviews, final items, and rejected_candidates.
4. Final items use `evidence_segment_index` and `supporting_segment_indices`; deterministic materialization copies exact evidence objects. Keep reason source-grounded and repaired_reason source-preserving.
5. Do not reread the full blocks after response 1 and do not write pair artifacts one file at a time.
6. Materialize and validate every ordinary pair artifact in one deterministic command:

```bash
python3 .codex/skills/tastyroad-transcript-must-taste/scripts/materialize_must_taste_video_bundle.py --video-context video_context.json --findings candidate_findings.json --bundle pair_results_bundle.json
```

Findings root: `video_id`, `windows`, `pairs`. Each pair has `restaurant_id` and `attention_events`.
Bundle root: `video_id`, `pairs`. Each pair has `restaurant_id`, `candidates`, `reviews`, `items`, `rejected_candidates`, and optional `insufficient_evidence_reason`.

The two-response budget applies to semantic analysis, not deterministic preparation/validation commands. If restaurant boundaries are genuinely ambiguous, fall back to the ordinary pair workflow and record the reason.
Do not write SQLite from this video-level workflow. Final applies remain single-process through the batch apply script after quality comparison.
