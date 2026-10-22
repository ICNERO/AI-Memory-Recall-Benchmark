# Public Gold and exact evidence offsets

This directory is intentionally **PUBLIC**, including evaluation `test` answers. It enables anyone to run the scorer and reproduce results locally. It also means **this is not a blind held-out test**.

| File | Meaning |
|---|---|
| `gold.jsonl` | all 500 complete author Gold records, including necessary relations, source claims, evidence units, alternative minimal sufficient sets, expected actions, and provenance |
| `evidence_positions.jsonl` | 3109 positive evidence span records flattened from `gold.jsonl` |
| `queries_and_gold_review.md` | readable author review for all registered questions |
| `query_scope_status.jsonl` | per-query integrity and review coverage status |
| `splits.json` | assigned train/dev/test for each query |
| `revision_records.jsonl` | version lineage of changed query text/annotations |
| `gold_summary.json` | file-derived counts and original Gold SHA-256 |

### Offset interpretation
`start` is **inclusive** and `end` **exclusive**, using zero-based **Unicode code-point** indices in the unnormalized message `content`. For each entry: `histories[message_id].content[start:end] == text`, and `SHA256(UTF8(text)) == text_sha256`. `round_id` maps through `public/rounds.jsonl`. Evidence `evidence_id` links spans to logical units in `gold.jsonl`; `sufficient_sets` are OR among sets and AND within each set of units.

### Correct scoring
The evaluator reads this public file at `gold/gold.jsonl`. Run `python -m r2bench validate` first; then `python -m r2bench score --predictions PATH --output DIR`. No external LLM or secret file is required. `CLARIFY` and `ABSTAIN` are decisions distinct from retrieving a sufficient evidence path. The existing labels are author constructions; semantic alternative completeness has not been independently certified.

### Non-blind comparison requirement
Annotate all published scores `open-gold` or `non-blind`. Systems tuned on this Gold are not valid held-out comparisons. Use a separately versioned, unpublished dataset for future blind evaluations.

### Compatibility shards

`shards/` preserves the 20 Gold chunks already present in the repository during publication. Their Git blob hashes were verified against consecutive 25-row slices of canonical `gold.jsonl`; together they contain the same 500 records. The scorer uses `gold.jsonl` only. Do not load both representations as separate examples.
