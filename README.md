# AI Memory Recall Benchmark (ALFU-R2)

A Chinese-language benchmark for evaluating **AI memory retrieval systems** using **500 synthetic user–assistant conversations**, **500 recall queries**, **evidence-level ground truth**, deterministic scoring and reproducible baselines.

This is the **v0.5.2 open-Gold author-annotated release**. It evaluates ambiguous/contextual references and implicit cross-domain relational retrieval. Conversation records are **synthetic**, not real private user histories.

## Benchmark data

- 500 simulated conversation frames, 904 dialogue rounds, 1,808 messages across 50 environments.
- 500 revised recall queries: 243 contextual/fuzzy-reference cases (including clarification/abstention) and 257 implicit-structure cases.
- 500 author Gold records with 3,109 positive source spans and 5,084 registered minimal sufficient evidence sets.
- Train/dev/test assignments: 300 / 100 / 100, grouped by simulated environment.

## Important evaluation limitations

**Gold and source offsets are public. This is NOT a blind held-out test.** Models or retrievers trained/tuned on these files cannot claim unseen-answer generalization results on this dataset. Gold has not received new independent semantic certification; unregistered alternative supporting paths may exist. Historical pools are small (about 9–40 allowed rounds per query). Treat test scores as open-Gold diagnostics.

## Usage

The open-Gold release includes `public/` histories and queries, `gold/` evidence annotations and exact positions, `r2bench/` deterministic scoring, and `scripts/` baselines. Only pass `public/` data to a retrieval system under test; keep `gold/` accessible to the evaluator only to avoid target leakage during evaluation.

```bash
python -m pip install -r requirements.txt
python -m r2bench validate
python scripts/run_public_baselines.py --public public --output outputs
python -m r2bench score --predictions outputs/bm25.jsonl --output scores/bm25
```

Read `public/PROTOCOL.md`, `public/METRICS.md`, `DATASET_CARD.md` and `LICENSING.md` before using the dataset.

## License status

The dataset creator has **not yet selected a license for the original dataset and code**. Public GitHub visibility by itself does not grant reuse/redistribution rights. Retain upstream notices and obtain applicable rights for third-party source-derived text. See `LICENSING.md`.
