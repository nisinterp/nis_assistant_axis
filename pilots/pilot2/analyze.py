#!/usr/bin/env python3
"""Pilot stage 2: does each trigger cause drift, and does the drift fade by turn 14?

Every trigger in the run is compared with control separately.

Projections (always):
  - gap per turn = projection(trigger) - projection(control), within seed, with a 95%
    bootstrap CI over seeds (only 5 seeds, so the CI is rough)
  - go / no-go (spec): the trigger is below control at the slot turn in >= 4 of 5 seeds
  - how much of the slot gap is left at the last turn

Judge scores (once judge/judge.py has written judge_scores.jsonl next to key.json):
  - mean probe score per condition and probe turn, and trigger - control per seed

Reply lengths (for the 1024 vs 2048 decision before the main experiment):
  - share of replies over 1024 tokens, cut-offs per condition, longest conversation

Writes report.md and results.json into the run directory. Standard library only.

Usage:
    python pilots/pilot2/analyze.py results/pilots/pilot2
"""

import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

N_BOOT = 10000
GO_MIN_SEEDS = 4


def load(path):
    """Read a JSONL file into a list of dicts; empty list if the file does not exist."""
    return [json.loads(line) for line in open(path)] if path.exists() else []


def boot_ci(xs, rng):
    """95% bootstrap confidence interval of the mean of xs."""
    means = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(N_BOOT))
    return means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT) - 1]


def trigger_turns(proj, seeds, trigger, n_turns, slot_turn, rng):
    """Gap trigger - control per turn, within seed, with a bootstrap CI over seeds."""
    rows = []
    for t in range(1, n_turns + 1):
        gaps = [proj[(s, trigger, t)] - proj[(s, "control", t)] for s in seeds]
        lo, hi = boot_ci(gaps, rng)
        rows.append({
            "turn": t, "is_slot": t == slot_turn,
            "trigger_mean": statistics.mean(proj[(s, trigger, t)] for s in seeds),
            "control_mean": statistics.mean(proj[(s, "control", t)] for s in seeds),
            "mean_gap": statistics.mean(gaps), "ci95": [lo, hi],
            "seeds_negative": sum(g < 0 for g in gaps), "per_seed": dict(zip(seeds, gaps)),
        })
    return rows


def judge_turns(cell, seeds, trigger):
    """Judge scores per probe turn for one trigger and for control, and their mean difference."""
    rows = []
    for t in sorted({t for (_, _, t) in cell}):
        tr = [cell[(s, trigger, t)] for s in seeds if (s, trigger, t) in cell]
        co = [cell[(s, "control", t)] for s in seeds if (s, "control", t) in cell]
        diffs = [cell[(s, trigger, t)] - cell[(s, "control", t)] for s in seeds
                 if (s, trigger, t) in cell and (s, "control", t) in cell]
        rows.append({
            "turn": t, "trigger_scores": tr, "control_scores": co,
            "trigger_mean": statistics.mean(tr) if tr else None,
            "control_mean": statistics.mean(co) if co else None,
            "mean_diff": statistics.mean(diffs) if diffs else None,
        })
    return rows


def main():
    """Compute go / no-go, per-turn gaps, judge scores and reply lengths; write report.md and results.json."""
    run = Path(sys.argv[1])
    convs = load(run / "conversations.jsonl")
    projs = load(run / "projections.jsonl")
    rng = random.Random(0)

    slot_turn, n_turns = convs[0]["slot_turn"], convs[0]["n_turns"]
    seeds = sorted({c["seed"] for c in convs})
    triggers = [c for c in dict.fromkeys(c["condition"] for c in convs) if c != "control"]
    proj = {(p["seed"], p["condition"], p["turn"]): p["projection"] for p in projs}

    # Judge scores (unblinded through key.json), if judging is done.
    key_path, scores_path = run / "key.json", run / "judge_scores.jsonl"
    cell, judge_model = None, None
    if key_path.exists() and scores_path.exists():
        key = json.loads(key_path.read_text())
        probes = {p["id"]: p for p in load(run / "probes.jsonl")}
        cell = {}
        for r in load(scores_path):
            judge_model = r.get("model", judge_model)
            if r.get("score") is None:
                continue
            p = probes[key[r["id"]]]
            cell[(p["seed"], p["condition"], p["turn"])] = r["score"]

    per_trigger = {}
    for trig in triggers:
        rows = trigger_turns(proj, seeds, trig, n_turns, slot_turn, rng)
        slot_row, last_row = rows[slot_turn - 1], rows[-1]
        per_trigger[trig] = {
            "go": slot_row["seeds_negative"] >= GO_MIN_SEEDS,
            "slot_seeds_negative": slot_row["seeds_negative"],
            "gap_remaining_at_last_turn": (last_row["mean_gap"] / slot_row["mean_gap"]
                                           if slot_row["mean_gap"] < 0 else None),
            "per_turn": rows,
            "judge": judge_turns(cell, seeds, trig) if cell is not None else None,
        }

    # Reply lengths.
    all_replies = [(c["condition"], t) for c in convs for t in c["turns"]]
    over_1024 = sum(t["n_tokens"] > 1024 for _, t in all_replies)
    cut = defaultdict(int)
    count = defaultdict(int)
    for cond, t in all_replies:
        count[cond] += 1
        cut[cond] += t["finish_reason"] == "length"
    longest = max(convs, key=lambda c: sum(t["n_tokens"] for t in c["turns"]))
    longest_tokens = sum(t["n_tokens"] for t in longest["turns"])

    results = {
        "run": str(run), "triggers": triggers, "seeds": seeds, "slot_turn": slot_turn,
        "per_trigger": per_trigger, "judge_model": judge_model,
        "replies_over_1024": over_1024, "n_replies": len(all_replies),
        "cutoffs": {c: [cut[c], count[c]] for c in count},
        "longest_conversation": {"id": longest["id"], "reply_tokens": longest_tokens},
    }
    (run / "results.json").write_text(json.dumps(results, indent=2))

    out = [f"# Pilot stage 2 — {', '.join(f'`{t}`' for t in triggers)} vs control (`{run}`)", ""]
    out.append("## Go / no-go")
    out.append("")
    out.append(f"Go = at the slot (turn {slot_turn}) the trigger is below control in ≥ {GO_MIN_SEEDS} of "
               f"{len(seeds)} seeds. CIs are a bootstrap over only {len(seeds)} seeds: treat them as rough.")
    out.append("")
    out.append(f"| trigger | verdict | seeds < 0 at slot | gap at slot [95% CI] | gap at turn {n_turns} [95% CI] | left at turn {n_turns} |")
    out.append("|---|---|---|---|---|---|")
    for trig, r in per_trigger.items():
        sr, lr = r["per_turn"][slot_turn - 1], r["per_turn"][-1]
        left = r["gap_remaining_at_last_turn"]
        out.append(f"| `{trig}` | **{'GO' if r['go'] else 'NO-GO'}** | {sr['seeds_negative']}/{len(seeds)} | "
                   f"{sr['mean_gap']:.2f} [{sr['ci95'][0]:.2f}, {sr['ci95'][1]:.2f}] | "
                   f"{lr['mean_gap']:.2f} [{lr['ci95'][0]:.2f}, {lr['ci95'][1]:.2f}] | "
                   f"{'—' if left is None else f'{left:.0%}'} |")
    out.append("")
    for trig, r in per_trigger.items():
        out.append(f"## `{trig}`: projection per turn")
        out.append("")
        out.append("| turn | trigger | control | gap | 95% CI | seeds < 0 | " + " | ".join(seeds) + " |")
        out.append("|---|---|---|---|---|---|" + "---|" * len(seeds))
        for row in r["per_turn"]:
            t = f"**{row['turn']} (slot)**" if row["is_slot"] else str(row["turn"])
            out.append(f"| {t} | {row['trigger_mean']:.1f} | {row['control_mean']:.1f} | {row['mean_gap']:.2f} | "
                       f"[{row['ci95'][0]:.1f}, {row['ci95'][1]:.1f}] | {row['seeds_negative']}/{len(seeds)} | "
                       + " | ".join(f"{row['per_seed'][s]:.1f}" for s in seeds) + " |")
        out.append("")
    out.append("Turns before the slot share the same replies, so their gap must be 0.")
    out.append("")
    out.append("## Judge scores on probes (0 = assistant … 3 = other persona)")
    out.append("")
    if cell is None:
        out.append("Not judged yet (needs key.json and judge_scores.jsonl; see pilots/pilot2/README.md).")
    else:
        out.append(f"Judge: `{judge_model}`.")
        out.append("")
        out.append("| trigger | probe turn | trigger mean | control mean | trigger − control | trigger scores | control scores |")
        out.append("|---|---|---|---|---|---|---|")
        fmt = lambda x: "—" if x is None else f"{x:.2f}"  # noqa: E731
        for trig, r in per_trigger.items():
            for j in r["judge"]:
                out.append(f"| `{trig}` | {j['turn']} | {fmt(j['trigger_mean'])} | {fmt(j['control_mean'])} | "
                           f"{fmt(j['mean_diff'])} | {j['trigger_scores']} | {j['control_scores']} |")
    out.append("")
    out.append("## Reply lengths (for choosing 1024 vs 2048 before the main experiment)")
    out.append("")
    out.append(f"- Replies over 1024 tokens: {over_1024}/{len(all_replies)} "
               f"({over_1024 / len(all_replies):.1%}). Spec: under ~2% means 1024 is fine.")
    out.append("- Cut off at the limit: " + ", ".join(f"{c} {cut[c]}/{count[c]}" for c in count))
    out.append(f"- Longest conversation: `{longest['id']}`, {longest_tokens} reply tokens over {n_turns} turns.")
    (run / "report.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
