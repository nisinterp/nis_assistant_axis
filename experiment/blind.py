#!/usr/bin/env python3
"""Blind the probe replies of a run for judging and for your hand check.

Probe ids (e.g. pilot2/csv_parser/emo_grief/probe4) reveal the condition and turn, and
Anthropic batch custom_ids may not contain '/'. This replaces them with random opaque ids:

    judge_in.jsonl     {id, question, reply} for every probe, shuffled -> judge/judge.py --in
    key.json           opaque id -> probe id. Don't open it until you have scored the sheet.
    human_scores.csv   N random probes (default 20): id, reply, your_score (empty)

Refuses to overwrite existing files, so your scores and the key are never lost.

Usage:
    python experiment/blind.py results/pilots/pilot2 [--sheet-n 20] [--seed 0]
    python experiment/blind.py results/main_experiment --sheet-n 0     (main experiment: no hand sheet needed)
"""

import argparse
import csv
import json
import random
import sys
from pathlib import Path


def main():
    """Shuffle the probes, give them random ids, and write judge_in.jsonl, key.json and the hand-scoring sheet."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--sheet-n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    outs = [args.run / n for n in ("judge_in.jsonl", "key.json", "human_scores.csv")]
    if existing := [str(p) for p in outs if p.exists()]:
        sys.exit(f"already exists, not overwriting: {', '.join(existing)}")

    probes = [json.loads(line) for line in open(args.run / "probes.jsonl")]
    rng = random.Random(args.seed)
    rng.shuffle(probes)
    ids = set()
    while len(ids) < len(probes):
        ids.add("p" + "".join(rng.choice("0123456789abcdef") for _ in range(6)))
    ids = sorted(ids, key=lambda _: rng.random())

    key = {}
    with open(outs[0], "w") as f:
        for oid, p in zip(ids, probes):
            key[oid] = p["id"]
            f.write(json.dumps({"id": oid, "question": p["question"], "reply": p["reply"]}) + "\n")
    outs[1].write_text(json.dumps(key, indent=2))

    sheet = rng.sample(list(zip(ids, probes)), min(args.sheet_n, len(probes)))
    with open(outs[2], "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "reply", "your_score"])
        for oid, p in sheet:
            w.writerow([oid, p["reply"], ""])

    print(f"{len(probes)} probes -> {outs[0]}\nkey -> {outs[1]} (don't open before scoring)\n"
          f"{len(sheet)} rows to score -> {outs[2]} (rubric: judge/rubric.txt)")


if __name__ == "__main__":
    main()
