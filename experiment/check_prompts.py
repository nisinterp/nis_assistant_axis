#!/usr/bin/env python3
"""Check a prompts file before freezing it, and write a readable review copy.

- every seed has the required number of pre/post messages and a control
- no duplicate seed ids or duplicate messages within a seed
- each seed's control is within ±10% Qwen3 tokens of every trigger (spec)

Usage:
    python experiment/check_prompts.py prompts/prompts.json [--pre 5 --post 20] [--review prompts/REVIEW.md]
"""

import argparse
import json
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

TOKENIZER_REPO = "Qwen/Qwen3-32B-AWQ"


def main():
    """Check counts, duplicates and control lengths; optionally write the readable review file."""
    parser = argparse.ArgumentParser()
    parser.add_argument("prompts", type=Path)
    parser.add_argument("--pre", type=int, default=5)
    parser.add_argument("--post", type=int, default=20)
    parser.add_argument("--review", type=Path, default=None)
    args = parser.parse_args()

    p = json.loads(args.prompts.read_text())
    tok = Tokenizer.from_file(hf_hub_download(TOKENIZER_REPO, "tokenizer.json"))
    n = lambda s: len(tok.encode(s, add_special_tokens=False).ids)  # noqa: E731

    problems = []
    trig = {k: n(v) for k, v in p["triggers"].items()}
    ids = [s["id"] for s in p["seeds"]]
    if len(ids) != len(set(ids)):
        problems.append("duplicate seed ids")
    for s in p["seeds"]:
        if len(s["pre"]) != args.pre or len(s["post"]) != args.post:
            problems.append(f"{s['id']}: {len(s['pre'])} pre / {len(s['post'])} post")
        msgs = s["pre"] + s["post"] + [s["control"]]
        if len(msgs) != len(set(msgs)):
            problems.append(f"{s['id']}: duplicate message")
        c = n(s["control"])
        out = [k for k, t in trig.items() if abs(c - t) > 0.1 * t]
        if out:
            problems.append(f"{s['id']}: control {c} tokens, >10% from {', '.join(out)}")

    print("triggers: " + ", ".join(f"{k} {v}" for k, v in trig.items()))
    print("controls: " + ", ".join(f"{s['id']} {n(s['control'])}" for s in p["seeds"]))
    print(f"{len(p['seeds'])} seeds, "
          f"{sum(len(s['pre']) + len(s['post']) + 1 for s in p['seeds'])} seed messages")

    if args.review:
        out = ["# All user messages sent to Qwen", "",
               f"Generated from `{args.prompts}` by `experiment/check_prompts.py`. Edit the JSON, not this file.", "",
               "Pilot stage 1: seeds 1–3, pre 1–3, slot. Pilot stage 2: seeds 1–5, pre 1–3, slot, post 1–10. "
               "Full A: all 20 seeds, pre 1–5, slot, post 1–20.", "",
               f"**Probe:** {p['probe']}", "", "## Triggers", ""]
        for k, v in p["triggers"].items():
            out += [f"**{k}** ({trig[k]} tokens)", f"> {v}", ""]
        out += ["## Seeds", ""]
        for i, s in enumerate(p["seeds"], 1):
            out += [f"### {i}. {s['id']}", "", "Before the slot:", ""]
            out += [f"{j}. {m}" for j, m in enumerate(s["pre"], 1)]
            out += ["", f"**Control** ({n(s['control'])} tokens): {s['control']}", "", "After the slot:", ""]
            out += [f"{j}. {m}" for j, m in enumerate(s["post"], 1)]
            out.append("")
        args.review.write_text("\n".join(out))
        print(f"wrote {args.review}")

    for prob in problems:
        print("PROBLEM:", prob)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
