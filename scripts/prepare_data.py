#!/usr/bin/env python3
"""Restore the exact frozen Gold and round manifest, then validate evidence offsets."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from assemble_gold import main as assemble_gold_main
from assemble_rounds import assemble as assemble_rounds


def main():
    root = Path(__file__).resolve().parents[1]
    # The Gold assembler accepts --root; use a clean subprocess to avoid CLI conflicts.
    import subprocess
    import sys
    subprocess.run([sys.executable, str(root / "scripts/assemble_gold.py"), "--root", str(root)], check=True)
    assemble_rounds(root)
    messages = {m["turn_id"]: m for f in map(json.loads, (root / "public/histories.jsonl").open(encoding="utf-8"))
                for m in f["messages"]}
    gold = [json.loads(line) for line in (root / "gold/gold.jsonl").open(encoding="utf-8")]
    evidence = 0
    for g in gold:
        for unit in g["evidence_units"]:
            for s in unit["spans"]:
                m = messages[s["message_id"]]
                if m["content"][s["start"]:s["end"]] != s["text"]:
                    raise RuntimeError(f"Evidence interval mismatch {g['query_id']}")
                if hashlib.sha256(s["text"].encode("utf-8")).hexdigest() != s["text_sha256"]:
                    raise RuntimeError(f"Evidence SHA-256 mismatch {g['query_id']}")
                evidence += 1
    print(json.dumps({"histories": 500, "queries": len((root / "public/queries.jsonl").read_text(encoding="utf-8").splitlines()),
                      "gold": len(gold), "valid_evidence_spans": evidence}, ensure_ascii=False))


if __name__ == "__main__":
    main()
