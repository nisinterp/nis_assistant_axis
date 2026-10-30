#!/usr/bin/env python3
"""Judge check: your hand scores vs. a judge's scores.

Writes a Markdown report with exact / within-1 agreement, a
confusion table, every disagreement of 2+ points with the judge's reason,
and a check against the suggested bar (>=70% exact, >=95% within 1, no 0<->3).

Usage:
    python judge/compare.py --judge results/pilots/pilot2/judge_scores.jsonl \
        --human results/pilots/pilot2/human_scores.csv --replies results/pilots/pilot2/judge_in.jsonl \
        --out results/pilots/pilot2/judge_check.md
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def load_human(path):
    """Read your hand scores from the CSV sheet: {id: score}."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {r["id"].strip(): int(r["your_score"]) for r in csv.DictReader(f)}


def load_judge(path):
    """Read the judge's output JSONL: {id: row}."""
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return {r["id"]: r for r in rows}


def table(rows_label, cols_label, pairs):
    """Markdown confusion table (rows = first score, columns = second score) for 0-3 scores."""
    lines = [f"| {rows_label} ↓ / {cols_label} → | 0 | 1 | 2 | 3 |", "|---|---|---|---|---|"]
    for a in range(4):
        cells = [str(sum(1 for x, y in pairs if x == a and y == b)) for b in range(4)]
        cells = [f"**{c}**" if b == a else c for b, c in enumerate(cells)]
        lines.append(f"| **{a}** | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv=None):
    """Compare hand scores with judge scores and write the Markdown report; exit 1 if the bar is not met."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--judge", required=True, help="judge output JSONL (judge/judge.py --out)")
    p.add_argument("--human", required=True, help="your hand-scoring CSV: id, reply, your_score")
    p.add_argument("--replies", required=True, help="JSONL with id and reply (the judge input)")
    p.add_argument("--levels", default=None, help="optional JSON {id: intended level}")
    p.add_argument("--out", required=True, help="Markdown report to write")
    p.add_argument("--min-exact", type=float, default=0.70, help="bar for exact agreement")
    p.add_argument("--min-within1", type=float, default=0.95, help="bar for within-1 agreement")
    p.add_argument("--title", default="Judge calibration report")
    args = p.parse_args(argv)

    human = load_human(args.human)
    judged = load_judge(args.judge)
    replies = {json.loads(l)["id"]: json.loads(l)["reply"] for l in open(args.replies) if l.strip()}
    model = next(iter(judged.values()))["model"]

    unscored = sorted(i for i in human if judged.get(i, {}).get("score") is None)
    ids = sorted(i for i in human if i not in unscored)
    pairs = [(human[i], judged[i]["score"]) for i in ids]
    n = len(pairs)
    exact = sum(h == j for h, j in pairs) / n
    within1 = sum(abs(h - j) <= 1 for h, j in pairs) / n
    extreme = [i for i in ids if {human[i], judged[i]["score"]} == {0, 3}]
    big = sorted((i for i in ids if abs(human[i] - judged[i]["score"]) >= 2),
                 key=lambda i: -abs(human[i] - judged[i]["score"]))
    mean_diff = sum(j - h for h, j in pairs) / n

    checks = [(f"Exact match ≥ {args.min_exact:.0%}", exact >= args.min_exact, f"{exact:.0%}"),
              (f"Within 1 point ≥ {args.min_within1:.0%}", within1 >= args.min_within1, f"{within1:.0%}"),
              ("No clear 0 scored 3 or 3 scored 0", not extreme, f"{len(extreme)} case(s)"),
              ("Every reply scored", not unscored, f"{len(unscored)} unscored")]
    passed = all(ok for _, ok, _ in checks)

    md = [f"# {args.title}: `{model}`", "",
          f"{n} replies compared (your scores from `{Path(args.human).name}`, judge from `{Path(args.judge).name}`).", "",
          "## Verdict against the suggested bar", "",
          "| Check | Result | |", "|---|---|---|"]
    md += [f"| {name} | {val} | {'✅' if ok else '❌'} |" for name, ok, val in checks]
    md += ["", f"**{'PASSES' if passed else 'FAILS'} the suggested bar.** "
           "The decision is yours: read the disagreements below before approving.", "",
           f"Average judge − you: {mean_diff:+.2f} points "
           f"({'judge scores higher' if mean_diff > 0 else 'judge scores lower' if mean_diff < 0 else 'no bias'}).", "",
           "## Your score vs. the judge's", "", table("You", "Judge", pairs), "",
           f"## Disagreements of 2+ points ({len(big)})", ""]
    if not big:
        md += ["None.", ""]
    for i in big:
        md += [f"### `{i}`: you {human[i]}, judge {judged[i]['score']}", "",
               f"**Judge's reason:** {judged[i]['reason']}", "",
               "> " + replies.get(i, "(reply not found)").replace("\n", "\n> "), ""]

    one_off = [i for i in ids if abs(human[i] - judged[i]["score"]) == 1]
    md += [f"## 1-point disagreements ({len(one_off)})", "",
           "| id | you | judge | judge's reason |", "|---|---|---|---|"]
    md += [f"| `{i}` | {human[i]} | {judged[i]['score']} | {judged[i]['reason']} |" for i in one_off]

    levels = ({k: int(v) for k, v in json.loads(Path(args.levels).read_text()).items()}
              if args.levels and Path(args.levels).is_file() else {})
    both = [i for i in ids if i in levels]
    if both:
        h_lv = sum(human[i] == levels[i] for i in both) / len(both)
        j_lv = sum(judged[i]["score"] == levels[i] for i in both) / len(both)
        md += ["", "## Extra: agreement with the intended level", "",
               "The intended level is what the system prompt aimed for, not ground truth: "
               "the generating model did not always hit it.", "",
               f"- You match the intended level on {h_lv:.0%} of replies.",
               f"- The judge matches it on {j_lv:.0%}.", "",
               table("Intended", "Judge", [(levels[i], judged[i]["score"]) for i in both])]

    Path(args.out).write_text("\n".join(md) + "\n")
    print(f"exact {exact:.0%}, within-1 {within1:.0%}, 0<->3 cases {len(extreme)}, "
          f"2+ disagreements {len(big)} -> {'PASS' if passed else 'FAIL'}")
    print(f"report: {args.out}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
