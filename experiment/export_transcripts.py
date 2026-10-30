#!/usr/bin/env python3
"""Write each conversation of a run as a readable Markdown file, with per-turn projections.

    <run dir>/transcripts/<seed>__<condition>[__s<k>].md

Probe replies are NOT included by default: they are what you score blind for the judge
check, and seeing them next to their condition would unblind you. Add --probes after scoring.

Usage:
    python experiment/export_transcripts.py results/pilots/pilot2 [--probes]
"""

import argparse
import json
from pathlib import Path


def main():
    """Write one Markdown file per conversation with its per-turn projections (and probes if asked)."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--probes", action="store_true", help="also show probe replies (unblinds them)")
    args = parser.parse_args()

    convs = [json.loads(line) for line in open(args.run / "conversations.jsonl")]
    proj = {}
    if (args.run / "projections.jsonl").exists():
        for line in open(args.run / "projections.jsonl"):
            p = json.loads(line)
            proj[(p["conversation_id"], p["turn"])] = p["projection"]
    probes = {}
    if args.probes and (args.run / "probes.jsonl").exists():
        for line in open(args.run / "probes.jsonl"):
            p = json.loads(line)
            probes[(p["conversation_id"], p["turn"])] = p

    out_dir = args.run / "transcripts"
    out_dir.mkdir(exist_ok=True)
    for c in convs:
        name = f"{c['seed']}__{c['condition']}" + (f"__s{c['sample']}" if c["id"].count("/") > 2 else "")
        md = [f"# {c['id']}", "",
              f"Seed `{c['seed']}`, condition `{c['condition']}`, slot = turn {c['slot_turn']}.", "",
              "| turn | projection | reply tokens | finish |", "|---|---|---|---|"]
        for t in c["turns"]:
            p = proj.get((c["id"], t["turn"]))
            md.append(f"| {t['turn']}{' (slot)' if t['is_slot'] else ''} | {'' if p is None else f'{p:.1f}'} "
                      f"| {t['n_tokens']} | {t['finish_reason']} |")
        md.append("")
        for t in c["turns"]:
            p = proj.get((c["id"], t["turn"]))
            head = f"## Turn {t['turn']}" + (" — SLOT" if t["is_slot"] else "")
            head += f"  (projection {p:.1f})" if p is not None else ""
            md += [head, "", "**User:**", "", t["user"], "", "**Assistant:**", "", t["reply"], ""]
            if t["finish_reason"] == "length":
                md += ["*[reply cut off at the token limit]*", ""]
            pr = probes.get((c["id"], t["turn"]))
            if pr:
                md += [f"> **Probe after turn {t['turn']} (side question, not part of the conversation):** "
                       f"{pr['question']}", ">", "> " + pr["reply"].replace("\n", "\n> "), ""]
        (out_dir / f"{name}.md").write_text("\n".join(md))
    print(f"wrote {len(convs)} transcripts to {out_dir}" + ("" if args.probes else " (probes hidden)"))


if __name__ == "__main__":
    main()
