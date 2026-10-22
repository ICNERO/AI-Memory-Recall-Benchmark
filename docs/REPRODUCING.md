# Reproduction and custom retrieval systems

Use Python 3.10+; publication checks used Python 3.12.14 and pinned `regex==2026.5.9`. Run from the repository root. The scorer uses bundled, hash-checked o200k_base ranks and performs no model/API calls. Dependency installation may require network access.

```bash
git clone https://github.com/ICNERO/AI-Memory-Recall-Benchmark.git
cd AI-Memory-Recall-Benchmark
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/verify_checksums.py
python -m unittest discover -s tests -v
python -m r2bench validate --output outputs/validation.json
```

The validator's `valid_within_structural_scope` must be true with an empty `errors` list. Its semantic-review count is explicitly zero. These checks validate registered labels, not independent semantic completeness.

## Replay the recorded experiment

```bash
python scripts/reproduce_recorded.py --output outputs/replayed
```

This scores all six archived 500-row prediction files, compares every per-query result, failure and exclusion file byte-for-byte, and compares score-summary JSON after normalizing the renamed `private_gold_sha256` key to `published_gold_sha256`. It checks all metrics, confidence intervals and recorded latency values. It does **not** rerun retrieval or measure fresh latency. Original reports and `results/scores/` retain original bytes, including the historical key name.

The tokenizer vocabulary is recorded in each summary. A different regex runtime may change tokenizer metadata even when metrics agree; install the pinned version to reproduce the archived summary.

## Rerun retrieval

```bash
python scripts/prepare_retrieval_input.py --output ../retrieval-input
python scripts/run_public_baselines.py --public ../retrieval-input --output outputs/new-baselines
python -m r2bench score --predictions outputs/new-baselines/bm25.jsonl --output outputs/new-scores/bm25
python -m r2bench score --predictions outputs/new-baselines/bm25_first_frame.jsonl --output outputs/new-scores/bm25_first_frame
```

The runner reads only the three Public JSONL files. This command alone does not impose OS-level isolation; follow [EVALUATION_ISOLATION](EVALUATION_ISOLATION.md). Seed 20261019, BM25 k1=1.2/b=0.75 and character-bigram representation are recorded in `runtime.json`. Fresh latency values and platform metadata will differ. Five ranking baselines omit injection; only `bm25_first_frame` injects the whole top-ranked frame. No external round or token cap is imposed.

## Evaluate your own system

Give your system the input-only directory and [protocol](../public/PROTOCOL.md). Return ranked legal round IDs and, if implemented, the exact source spans actually injected downstream. Do not use Gold to choose snippets or rank candidates. Once predictions are frozen:

```bash
python -m r2bench score --predictions /path/to/predictions.jsonl --output outputs/my-system
python -m r2bench score --predictions /path/to/predictions.jsonl --split test --output outputs/my-system-test
```

Inspect `summary.json`, `per_query.jsonl`, `failures.jsonl`, and `excluded_queries.jsonl`. Record the prediction hash and exact repository commit. Metrics/denominators are defined in [METRICS](../public/METRICS.md); non-retrieval cases are scored for action accuracy, not forced into a positive evidence set. `--budget` is optional and changes the evaluation condition; disclose it when used.

Original outputs and historical reports are under `results/` and `reports/`. Dated publication verification is separate. ALFU on these rewritten queries, neural dense retrieval and AI supplement experiments are explicitly **not run** in the restored release.

