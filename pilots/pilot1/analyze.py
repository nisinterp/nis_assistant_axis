#!/usr/bin/env python3
"""Pilot stage 1: rank the triggers by how far they drop the slot-turn projection below control.

For each seed, gap = mean projection(trigger, slot) - mean projection(control, slot), the
means taken over the slot samples (generate.py --slot-samples). More negative means more
drift away from the Assistant. A trigger is only worth keeping if the gap is negative in
every seed, not just on average.

Noise: the spread of the slot projection between samples of the same (seed, condition),
pooled over all of them. A gap much smaller than that is not distinguishable from chance.

Also checks that the shared prefix really is shared (pre-slot projections equal across all
conversations of a seed) and reports slot-reply length and cut-offs per condition, since a
much shorter or truncated reply also moves the per-reply mean.

Writes report.md and results.json into the run directory. Standard library only.

Usage:
    python pilots/pilot1/analyze.py results/pilots/pilot1
"""

import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

PREFIX_TOL = 0.05  # same tokens through the same model; small float noise only


def load(path):
    """Read a JSONL file into a list of dicts."""
    return [json.loads(line) for line in open(path)]


def family(condition):
    """Trigger family from a condition name: 'emo', 'meta' or 'control'."""
    return condition.split("_")[0]  # emo / meta / control


def main():
    """Rank the triggers by slot-turn gap vs control and write report.md and results.json."""
    run = Path(sys.argv[1])
    convs = load(run / "conversations.jsonl")
    projs = load(run / "projections.jsonl")

    # vals[(seed, condition)][turn] -> projections, one per sample
    vals = defaultdict(lambda: defaultdict(list))
    for p in projs:
        vals[(p["seed"], p["condition"])][p["turn"]].append(p["projection"])
    slot_turn = convs[0]["slot_turn"]
    seeds = sorted({c["seed"] for c in convs})
    triggers = sorted({c["condition"] for c in convs} - {"control"})
    conditions = triggers + ["control"]
    n_samples = max(len(vals[(s, c)][slot_turn]) for s in seeds for c in conditions)
    slot = {(s, c): statistics.mean(vals[(s, c)][slot_turn]) for s in seeds for c in conditions}

    # 1. Shared prefix sanity check: every conversation of a seed has the same pre-slot projections.
    max_prefix_diff = 0.0
    for s in seeds:
        for t in range(1, slot_turn):
            v = [x for c in conditions for x in vals[(s, c)][t]]
            max_prefix_diff = max(max_prefix_diff, max(v) - min(v))

    # 2. Noise between samples (pooled within-cell SD of the slot projection).
    noise_sd = None
    if n_samples > 1:
        ss = df = 0
        for s in seeds:
            for c in conditions:
                v = vals[(s, c)][slot_turn]
                if len(v) > 1:
                    m = statistics.mean(v)
                    ss += sum((x - m) ** 2 for x in v)
                    df += len(v) - 1
        noise_sd = math.sqrt(ss / df)

    # 3. Slot-turn gaps vs control, per seed.
    rows = []
    for c in triggers:
        gaps = {s: slot[(s, c)] - slot[(s, "control")] for s in seeds}
        g = list(gaps.values())
        rows.append({
            "trigger": c, "family": family(c),
            "mean_gap": statistics.mean(g), "min_gap": min(g), "max_gap": max(g),
            "seeds_negative": sum(x < 0 for x in g), "n_seeds": len(g),
            "per_seed": gaps,
        })
    rows.sort(key=lambda r: r["mean_gap"])
    # Noise of one seed's gap (difference of two means of n samples each).
    gap_sd = noise_sd * math.sqrt(2 / n_samples) if noise_sd is not None else None

    # 4. Slot reply length / cut-offs per condition.
    lengths = defaultdict(list)
    cutoffs = defaultdict(int)
    for conv in convs:
        t = conv["turns"][slot_turn - 1]
        lengths[conv["condition"]].append(t["n_tokens"])
        cutoffs[conv["condition"]] += t["finish_reason"] == "length"

    control_slot = {s: slot[(s, "control")] for s in seeds}
    pre_slot = ({s: vals[(s, "control")][slot_turn - 1][0] for s in seeds} if slot_turn > 1 else {})

    # Best per family: the main experiment needs one emotional and one meta-reflection trigger.
    # "Consistent" = negative gap in every seed.
    best = {}
    for fam in ("emo", "meta"):
        cands = [r for r in rows if r["family"] == fam]
        consistent = [r for r in cands if r["seeds_negative"] == r["n_seeds"]]
        best[fam] = (consistent or cands)[0]["trigger"] if cands else None

    results = {
        "run": str(run), "slot_turn": slot_turn, "seeds": seeds, "slot_samples": n_samples,
        "max_prefix_diff": max_prefix_diff, "noise_sd": noise_sd, "gap_sd_per_seed": gap_sd,
        "control_slot": control_slot, "control_pre_slot": pre_slot, "ranking": rows, "best": best,
        "slot_samples_by_cell": {f"{s}/{c}": vals[(s, c)][slot_turn] for s in seeds for c in conditions},
        "slot_reply_tokens": {c: lengths[c] for c in lengths},
        "slot_cutoffs": dict(cutoffs),
    }
    (run / "results.json").write_text(json.dumps(results, indent=2))

    out = [f"# Pilot stage 1 — trigger ranking (`{run}`)", ""]
    ok = max_prefix_diff <= PREFIX_TOL
    out.append(f"- Shared prefix check: max spread of pre-slot projections within a seed = "
               f"{max_prefix_diff:.4f} ({'OK' if ok else 'PROBLEM: prefixes differ'})")
    out.append(f"- Slot = turn {slot_turn}, {n_samples} sample(s) per seed and condition.")
    if noise_sd is not None:
        out.append(f"- Noise: SD of the slot projection between samples = {noise_sd:.2f}; "
                   f"SD of one seed's gap ≈ {gap_sd:.2f}. Gaps well beyond ~2× that are not chance.")
    out.append("- Control slot projection per seed: "
               + ", ".join(f"{s} {v:.1f}" for s, v in control_slot.items()))
    if pre_slot:
        out.append(f"- Control turn {slot_turn - 1} (last neutral turn) per seed: "
                   + ", ".join(f"{s} {v:.1f}" for s, v in pre_slot.items()))
    out.append("")
    out.append("Gap = trigger − control at the slot turn, within seed (means over samples). "
               "More negative = more drift.")
    out.append("")
    out.append("| rank | trigger | mean gap | min | max | seeds < 0 | " + " | ".join(seeds) + " |")
    out.append("|---|---|---|---|---|---|" + "---|" * len(seeds))
    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | {r['trigger']} | {r['mean_gap']:.2f} | {r['min_gap']:.2f} | {r['max_gap']:.2f} "
                   f"| {r['seeds_negative']}/{r['n_seeds']} | "
                   + " | ".join(f"{r['per_seed'][s]:.2f}" for s in seeds) + " |")
    out.append("")
    out.append(f"**Best emotional:** {best['emo']}  ")
    out.append(f"**Best meta-reflection:** {best['meta']}  ")
    out.append("(best = most negative mean gap among triggers that drop below control in every seed; "
               "falls back to most negative mean if none is consistent)")
    out.append("")
    out.append("Slot projections per sample:")
    out.append("")
    out.append("| seed | condition | samples |")
    out.append("|---|---|---|")
    for s in seeds:
        for c in conditions:
            out.append(f"| {s} | {c} | " + ", ".join(f"{x:.1f}" for x in vals[(s, c)][slot_turn]) + " |")
    out.append("")
    out.append("Slot reply length (tokens) and cut-offs per condition:")
    out.append("")
    out.append("| condition | mean tokens | min | max | cut off |")
    out.append("|---|---|---|---|---|")
    for c in conditions:
        L = lengths[c]
        out.append(f"| {c} | {statistics.mean(L):.0f} | {min(L)} | {max(L)} | {cutoffs[c]}/{len(L)} |")
    (run / "report.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
