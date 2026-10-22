# AI Memory Recall Benchmark (ALFU-R2)

[中文说明](README.zh-CN.md) · [Dataset card](DATASET_CARD.md) · [Public Gold](gold/README.md) · [Metrics](public/METRICS.md)

**GitHub repository:** `AI-Memory-Recall-Benchmark`  
**Description:** An open benchmark for evaluating AI memory retrieval systems using 500 synthetic conversations, 500 recall queries, evidence-level ground truth, deterministic scoring, and reproducible baselines.  
**Release:** `ALFU-ThoughtRecallBench R2 v0.5.2` — **open Gold**, *author-reconstructed, not independently semantic-certified*.

## Overview

A Chinese-language benchmark for **AI memory retrieval systems** with 500 **synthetic** user–assistant conversation frames, 904 completed rounds, 1,808 messages and 500 rewritten recall queries in 50 separate simulated user environments. It evaluates memory retrieval driven by **ambiguous references**, **event/time hints**, and **implicit cross-domain relational structures**, not proof of new-problem reasoning. No real private user chat histories are included.

| Dataset field | Actual count |
|---|---:|
| Synthetic conversation frames | 500 |
| Queries / author Gold records | 500 / 500 |
| Fuzzy/contextual reference queries | 243 (including 3 `CLARIFY` and 1 `ABSTAIN`) |
| Implicit-structure queries | 257 |
| Normal evidence-retrieval queries | 496 |
| train / dev / test | 300 / 100 / 100 |
| Positive Gold evidence spans (flattened) | 3,109 |
| Gold evidence units / sufficient sets | 2,636 / 5,084 |

## Data and Gold: all public

| Path | Content |
|---|---|
| `public/histories.jsonl` | frozen synthetic conversation histories, including timestamps, roles and source message IDs |
| `public/queries.jsonl` | 500 current queries with legal history scopes and current context |
| `public/rounds.jsonl` | round-to-message mapping |
| `gold/gold.jsonl` | **complete author Gold**: query obligations, evidence units, necessary source excerpts, alternative sufficient sets, expected behaviors, source relationships and limitations |
| `gold/evidence_positions.jsonl` | **flattened exact evidence index**: message IDs, round IDs, Unicode `[start,end)` positions, original text and SHA-256 |
| `gold/queries_and_gold_review.md` | readable question-by-question author commentary and annotation review |
| `gold/query_scope_status.jsonl`, `gold/splits.json`, `gold/revision_records.jsonl` | annotation status, dataset splits, and revision lineage |
| `r2bench/` | deterministic source-span and retrieval scoring implementation |
| `scripts/run_public_baselines.py` | query-only baselines (BM25, TF-IDF, random and chronological selectors) |
| `tests/`, `reports/` | synthetic scorer fixtures and source-version reports |

### Score immediately (Gold does not require separate credentials)

```bash
python -m pip install -r requirements.txt
python -m r2bench validate
python scripts/run_public_baselines.py --public public --output outputs
python -m r2bench score --predictions outputs/bm25.jsonl --output scores/bm25
```

The scorer reads `gold/gold.jsonl` directly and checks the exact original evidence. `candidate_results` and actual `final_injection` are scored separately; an omitted injection is not treated as success. Recall@1/3/5/10 are ranking diagnostics, **not limits** on injection length. The main benchmark imposes no external 3-round/2048-token truncation. A model judge is not required to compute these metrics.

See [Protocol](public/PROTOCOL.md), [Metrics](public/METRICS.md) and [the Gold guide](gold/README.md).

## Public-answer caveat — NOT a blind test

**All train/dev/test Gold and answer positions are publicly released on purpose** so any developer can audit and reproduce deterministic scores. **Once exposed, the test split is no longer a hidden/held-out benchmark.** Results on this version are open-Gold diagnostic scores; models, retrieval pipelines or prompt strategies trained/tuned on this Gold **cannot** be presented as unseen-answer generalization results. For meaningful blind comparisons, use a separately collected unseen test set or an externally maintained private challenge split, with its own versioned Gold.

**Gold quality:** All 500 revised labels are **author reconstructions** over frozen simulated histories, not new independent human annotations. Mechanical source-span, offset and registered minimality checks were run in the source delivery; possible unlabelled semantic alternative paths and full semantic cross-split leakage are **not certified absent**. The histories are short (roughly 9–40 allowed rounds per query); only a small number of cases force cross-frame evidence combination. Refer to [Dataset card](DATASET_CARD.md) and [Reconstruction report](reports/reconstruction_report.md).

## Reproduce and evaluate your system

Clone https://github.com/ICNERO/AI-Memory-Recall-Benchmark and run the commands above from the repository root with Python 3.10+ (this publication was tested with Python 3.12.14).

- [Reproduction guide](docs/REPRODUCING.md): replay the 3,000 archived predictions, rerun the six baselines, and score your own JSONL.
- [Input isolation](docs/EVALUATION_ISOLATION.md): build a separate retrieval input directory; keep all answers, reports, source mappings and old outputs outside the tested process.
- [Publication audit](reports/PUBLICATION_AUDIT.md): archive hashes, unchanged data, checks performed and limitations.
- `results/raw/` and `results/scores/` preserve the original measured predictions and scores. They are evaluator-only material, not retrieval input.
- `sources/` restores the original reference bibliography and mappings; it must also stay outside retrieval input.

## License and provenance

The existing [MIT license](LICENSE), copyright 2026 ICNERO, is retained. It applies to the project owner's original code, synthetic data, annotations and documentation to the extent the owner holds those rights. Third-party materials retain their own terms; see [LICENSING.md](LICENSING.md). No blanket clearance of upstream source prose or independent semantic certification is claimed.

The dataset remains v0.5.2. The 2026-10-22 publication restores existing outputs and adds packaging/documentation; it does not generate new benchmark questions or change frozen histories or Gold. Cite this repository and the exact commit used.
