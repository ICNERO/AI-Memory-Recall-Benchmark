#!/usr/bin/env python3
"""Reassemble the exact v0.5.2 author Gold from GitHub-safe shards.

Standard library only. The expected SHA-256 binds the shards to the frozen Gold.
This does not certify semantic annotation completeness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA256 = "c592213c8d5144cf26cd88eb543f119c4691c944ac4237df6fcaa9987eaf607c"
EXPECTED_RECORDS = 500
EXPECTED_SHARDS = 20


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    root = args.root.resolve()
    folder = root / "gold"
    shards = sorted((folder / "shards").glob("gold_???_???.jsonl"))
    if len(shards) != EXPECTED_SHARDS:
        raise SystemExit(f"Expected {EXPECTED_SHARDS} shards, found {len(shards)}")
    raw = b"".join(p.read_bytes() for p in shards)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"Gold SHA mismatch: {digest}")
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    if len(records) != EXPECTED_RECORDS or len({r["query_id"] for r in records}) != EXPECTED_RECORDS:
        raise SystemExit("Gold record count or query identity invalid")
    destination = folder / "gold.jsonl"
    destination.write_bytes(raw)
    positions = []
    for g in records:
        for e in g["evidence_units"]:
            for index, span in enumerate(e["spans"]):
                positions.append({
                    "query_id": g["query_id"],
                    "evidence_id": e["evidence_id"],
                    "claim_ids": e["claim_ids"],
                    "span_index": index,
                    "message_id": span["message_id"],
                    "round_id": span["round_id"],
                    "conversation_id": span["conversation_id"],
                    "role": span["role"],
                    "start": span["start"],
                    "end": span["end"],
                    "text": span["text"],
                    "text_sha256": span["text_sha256"],
                })
    (folder / "evidence_positions.jsonl").write_text(
        "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in positions),
        encoding="utf-8",
    )
    print(json.dumps({
        "gold_records": len(records),
        "positive_spans": len(positions),
        "gold_sha256": digest,
        "gold_path": str(destination),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
