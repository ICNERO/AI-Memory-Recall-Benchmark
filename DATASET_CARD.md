# Dataset Card — AI Memory Recall Benchmark, ALFU-R2 v0.5.2

## Overview
Chinese-language synthetic conversation history evidence retrieval. This release has **500 synthetic conversations, 500 new queries and all 500 public author-Gold labels**, including exact evidence positions. Not real user data. Focused on context-dependent/ambiguous references, temporal/event cues and implicit cross-domain relationships.

## Splits and labels
50 simulated user environments and 300/100/100 train/dev/test queries. Labels: 243 context/fuzzy references (3 `CLARIFY`, 1 `ABSTAIN`); 257 implicit structure; 496 ordinary retrieval. The full Gold is public in `gold/gold.jsonl`. Query-local positions are flattened into `gold/evidence_positions.jsonl`. Exact source slices are checked against frozen history texts.

## Status and limitations
- **Open-Gold, non-blind** — all train/dev/test answers are public, unsuitable as an untouched held-out benchmark. Report results as public-answer diagnostic comparisons; for unexposed evaluation prepare a separate private split.
- **Author-reconstructed labels** — v0.5.2 did not receive new independent semantic verification. Potential extra legal evidence paths and semantic leakage have not been exhaustively ruled out. The mechanical checks do not replace content verification.
- **Synthetic, short histories** — 500 frames in 50 environments, roughly 9–40 allowed rounds per query; not demonstrated representative of real long-lived conversational memory.
- **Task** — evidence retrieval is not independent reasoning about completely new problems or ground-truth answer generation.
- **Benchmark usability** — scorer checks the registered source spans and query behavior deterministically. Outputs that include correct round IDs but omit the registered required substrings may not achieve sufficiency.
- **Licensing** — project-owner original material uses the existing MIT license; third-party material retains independent terms. See LICENSING.md.

## Suggested citation
Refer to this GitHub repository as `AI Memory Recall Benchmark (ALFU-ThoughtRecallBench R2 v0.5.2, open Gold)` and include the exact commit hash of the data and scorer used.
