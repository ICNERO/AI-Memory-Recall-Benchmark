# Public inputs and evaluator-only answers

This is an **open-Gold, non-blind diagnostic benchmark**. Input isolation prevents direct answer access during a run. It cannot undo prior exposure, training contamination or tuning on public test answers.

| Consumer | Permitted benchmark material |
|---|---|
| Retrieval system | `public/histories.jsonl`, `public/rounds.jsonl`, `public/queries.jsonl` only |
| Evaluation driver | Public inputs plus split IDs to select queries; never forwards expected actions or evidence IDs |
| Offline scorer | Predictions, Public, `gold/`, scoring code and frozen tokenizer |
| Auditor | Full repository including source mappings, reports and archived experiments |

Create an input-only directory **outside the repository**:

```bash
python scripts/prepare_retrieval_input.py --output ../retrieval-input
```

Run the tested system in a separate process/container/account with only this directory mounted read-only, its own system code/model, and a writable predictions directory. Do not mount the repository or `.git`, Gold, reports, source mappings, previous outputs or the original ZIPs. Restrict network access so the system cannot download answers from this public repository. A directory name is not an access-control boundary. The preparation script copies files; it does not create an OS sandbox.

The full input bundle contains multiple simulated users. For **each query**, the driver/system must restrict historical access to `allowed_frame_ids` and message timestamps at or before `query_at`. Do not expose another environment's history to an agent for that query. Use `query_timezone` and the supplied simulated clock instead of the machine's current time. Include the legal `current_context`; it is part of the query, not an answer annotation.

Write predictions without consulting evaluator-only material, freeze predictions (record SHA-256), then run the scorer separately. For train/dev/test evaluation, the evaluator may select the corresponding query IDs from `gold/splits.json`; the tested system must not receive Gold or source evidence positions. The scorer's `--split test` selects the scoring population, not a sandbox or a new hidden test.

Report the data/scorer commit, split, prediction hash, model/version, retrieval parameters, input access policy, prior exposure and which splits were used for development. Do not tune on test Gold and describe the result as unseen-answer generalization. Pre-existing models' exposure is often unknown; report it as unknown rather than certifying absence. Independent blind comparisons require separately collected unseen data.

Use one JSON object per query as described in [PROTOCOL](../public/PROTOCOL.md). `candidate_results` measures ranking; `final_injection` measures the actual selected source text. A ranker may omit injection and receives no injection measurement. Explicit empty injection is measured as empty. Missing queries remain failures in the scoring denominator. `CLARIFY` and `ABSTAIN` are predicted decisions, never input fields. Unicode offsets are code-point offsets in the exact frozen source; do not normalize or rewrite text.

