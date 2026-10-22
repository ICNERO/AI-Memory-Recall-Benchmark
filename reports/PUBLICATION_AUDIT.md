# v0.5.2 publication verification — 2026-10-22

This is a packaging and mechanical reproduction check. **New independent semantic reviews: 0.** The dataset stays v0.5.2; no new histories, queries, Gold labels or experimental scores were invented.

## Recovered archives

| Archive | SHA-256 | ZIP CRC and file inventory |
|---|---|---|
| `ALFU-ThoughtRecallBench-R2-v0.5.2.zip` | `ff462854ae5f2fd99455e4b8abf47eebfa0aaede1ba7276adce07449286a59c0` | passed; 115 entries; 114 internal checksum entries matched |
| `ALFU-ThoughtRecallBench-R2-Public-v0.5.2.zip` | `f616640010a95133c43f8b264edc966437188cd80040b2422bbac392252b28ec` | passed; 6 entries |
| `AI-Memory-Recall-Benchmark-GitHub-open-Gold-v0.5.2.zip` | `3d05e0da88c6e25db44bdf990ffe51ea4a3f218dedfd64af851d01e9afb73177` | passed; 40 entries; 39 internal checksum entries matched |

The first two hashes match the prior delivery record supplied by the owner. The third hash is freshly computed for the recovered prepared publication. All six `public/` files in the prepared publication match the full engineering archive; the three frozen JSONL inputs and Gold retain their original bytes. All 3,109 flattened positive source positions match the original message slices, text hashes and complete positive Gold span inventory.

At publication preparation, GitHub main was `118c84e6f87192fdab70794a972cb40dc043b5f4`, containing LICENSE, README, histories and queries. Its histories and queries matched recovered file Git blob hashes exactly. The existing MIT LICENSE is preserved byte-for-byte (Git blob `4be43af4587e00313658030c5663def6caf56159`).

## Contents restored and packaging changes

- Restored the existing open-Gold layout, full Gold, exact offsets, scorer, six baseline implementations, bundled tokenizer, tests and reports.
- Restored 3,000 original predictions, original scored outputs, runtime metadata, reproduction/regression records, `not_run` declarations and original source bibliography/mappings from the full archive. These are evaluator-only materials.
- Added bilingual publication guidance, explicit input isolation, a three-file input exporter, checksum verification and original-experiment replay helpers. Removed the obsolete script that tried to create a new repository.
- Corrected outdated unselected-license text to the already selected MIT license, retaining third-party terms. Corrected a missing requirements filename in the tokenizer error message. The scoring logic is unchanged; the prepared open-Gold package already changed its Gold path and summary hash key from `private` to `gold`/`published`.
- Updated the readable Gold review's former "private answers" heading to "public author answers, evaluator only"; evidence text and labels are unchanged.
- Excluded old parent datasets, nested stage-6 archive, duplicate replay outputs and platform-specific binary dependencies. No missing-content reconstruction was needed for the published benchmark.

## Checks actually executed for publication

1. Current structural validation: 500 queries, 500 Gold, 1,808 messages, 904 rounds, 300/100/100 splits; zero structural errors; 5,084 sufficient sets and 52,354 registered unit-deletion checks. `source_spans=3,118` includes 3,109 positive spans plus 9 related-but-insufficient spans; 10 interpretation witnesses are separate.
2. Existing scoring suite: all 24 synthetic unit tests passed on Python 3.12.14. Tests are not benchmark examples or semantic reviews.
3. Replayed all 3,000 original predictions through the published scorer. All 18 per-query/failure/exclusion files are byte-identical; all six summaries are identical as JSON after the historical `private_gold_sha256` to `published_gold_sha256` key rename. See `replay_2026-10-22.json`. This is 24 file comparisons, not 24 new experiments.
4. Freshly reran all six retrieval baselines using only the exported Public directory. All 3,000 prediction objects match original predictions after removing newly measured `latency_ms`. See `fresh_baselines_2026-10-22.json`. No OS-level sandbox is claimed for this local test.
5. Regex-screened all Public, Gold and source files for email addresses, Chinese mobile-number patterns, identity-card patterns, common GitHub/API credential prefixes and private-key headers. No matches remained outside URLs; phone-like matches were numeric reference identifiers inside source URLs. See `privacy_screen_2026-10-22.json`. This does not establish absence of all personal information; names in bibliographic attribution and synthetic narrative context were not treated as secret credentials.

## Scope not certified

The restored corpus is documented as synthetic conversations, not real private user chat logs. The screening above is not a comprehensive privacy review. Source bibliography and frozen citation markers are preserved; citation markers from old conversations are not live citations in GitHub. Source attribution is not a blanket copyright grant, and this publication did not independently revisit or clear every source paragraph. See `LICENSING.md` for boundaries.

No new independent semantic annotation audit, exhaustive alternative-path proof or complete semantic cross-split leakage certification was performed. Original historical audit claims remain historical. Public Gold makes this an open-answer diagnostic benchmark, not a hidden-answer test; run-time input isolation cannot remove previous answer exposure. No ALFU, dense-neural or AI-supplement experiment was added.

`SHA256SUMS.txt` inventories the final publication files except itself. The repository commit identifies the exact publication; use it in citations and experiment reports.

## Concurrent repository publication

While preparing this release, main advanced to `4792d1ca0e94d62cf0fea7fb22fc7787599971bd` with 20 Gold shards and without the earlier monolithic history file. All 20 shard Git blob hashes were checked against exact consecutive 25-row slices of recovered canonical Gold. They are preserved for compatibility; the canonical scorer reads only `gold/gold.jsonl`. The complete history is restored from its verified source. Publication uses the latest branch head with a non-forced expected-head check.
