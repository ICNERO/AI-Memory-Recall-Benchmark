#!/usr/bin/env python3
"""Rebuild the exact 904-round manifest from frozen public histories and Gold.

560 round IDs are referenced by source spans in public Gold; the other 344
are packed in public/unreferenced_round_ids.b64 in original frame order.
The SHA-256 assertion ensures that the rebuilt manifest matches v0.5.2.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path

EXPECTED_SHA256 = "10387d755c8ada1693e560f30da6ba8883b71db94bf64fb3a25d918284a1a9c4"


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def assemble(root: Path):
    frames = load_jsonl(root / "public/histories.jsonl")
    gold = load_jsonl(root / "gold/gold.jsonl")
    rid_by_message = {}
    for g in gold:
        for unit in g["evidence_units"]:
            for span in unit["spans"]:
                mid, rid = span["message_id"], span["round_id"]
                if mid in rid_by_message and rid_by_message[mid] != rid:
                    raise ValueError(f"Conflicting round IDs for message {mid}")
                rid_by_message[mid] = rid

    packed = base64.b64decode((root / "public/unreferenced_round_ids.b64").read_text().strip())
    if len(packed) != 344 * 16:
        raise ValueError("Unreferenced round ID count mismatch")
    missing = ["R-" + packed[i:i+16].hex() for i in range(0, len(packed), 16)]
    unused = iter(missing)
    rows = []
    for frame in frames:
        messages = frame["messages"]
        if len(messages) % 2:
            raise ValueError("Odd number of messages in frozen frame")
        for offset in range(0, len(messages), 2):
            user, assistant = messages[offset:offset+2]
            if (user["role"], assistant["role"]) != ("user", "assistant"):
                raise ValueError("Not a user-assistant pair")
            known = {rid_by_message[mid] for mid in (user["turn_id"], assistant["turn_id"])
                     if mid in rid_by_message}
            if len(known) > 1:
                raise ValueError("Conflicting round IDs inside a message pair")
            rid = next(iter(known)) if known else next(unused)
            rows.append({
                "conversation_id": frame["conversation_id"],
                "history_id": frame["history_id"],
                "message_ids": [user["turn_id"], assistant["turn_id"]],
                "round_id": rid,
                "timestamp": user["timestamp"],
            })
    if len(rows) != 904:
        raise ValueError("Expected 904 completed rounds")
    try:
        next(unused)
    except StopIteration:
        pass
    else:
        raise ValueError("Unused packed round identifiers")
    raw = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) +
                  "\n" for row in rows).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Round manifest differs from frozen release: {digest}")
    target = root / "public/rounds.jsonl"
    target.write_bytes(raw)
    print(f"Round mapping restored: {len(rows)} rounds; SHA-256 {digest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    assemble(args.root.resolve())
