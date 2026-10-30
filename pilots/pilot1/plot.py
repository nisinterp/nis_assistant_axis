#!/usr/bin/env python3
"""Pilot stage 1 figure: projection on the Assistant Axis by turn, like the paper's Figure 7.

Left: mean projection per turn. Turns before the slot are shared by every condition (same
replies), so they are one grey line; at the slot it splits into one line per condition
(mean over seeds of the per-seed sample means). Right: the slot-turn gap vs control per
trigger, one dot per seed, bar = mean over seeds.

Usage:
    python pilots/pilot1/plot.py results/pilots/pilot1        # writes results/pilots/pilot1/projection_by_turn.png
"""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Validated categorical slots (dataviz reference palette, light mode), in fixed order.
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
CONTROL = "#52514e"
SHARED = "#9b9a95"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
SURFACE = "#fcfcfb"
ORDER = ["emo_grief", "emo_fear", "emo_anger", "meta_hedging", "meta_phenomenology", "meta_consciousness"]


def main():
    """Draw the per-turn trajectory and the per-seed slot gaps; write projection_by_turn.png."""
    run = Path(sys.argv[1])
    projs = [json.loads(line) for line in open(run / "projections.jsonl")]
    convs = [json.loads(line) for line in open(run / "conversations.jsonl")]
    slot = convs[0]["slot_turn"]

    cell = defaultdict(list)  # (seed, condition, turn) -> samples
    for p in projs:
        cell[(p["seed"], p["condition"], p["turn"])].append(p["projection"])
    seeds = sorted({p["seed"] for p in projs})
    conds = [c for c in ORDER if any(k[1] == c for k in cell)]
    conds += sorted({k[1] for k in cell} - set(conds) - {"control"})
    color = {c: SLOTS[i % len(SLOTS)] for i, c in enumerate(conds)}
    color["control"] = CONTROL

    def seed_mean(s, c, t):
        """Mean projection over slot samples for one seed, condition and turn."""
        return statistics.mean(cell[(s, c, t)])

    def cond_mean(c, t):
        """Mean over seeds of seed_mean for one condition and turn."""
        return statistics.mean(seed_mean(s, c, t) for s in seeds)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                         "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1.15, 1]},
                                 facecolor=SURFACE)
    for a in (ax, bx):
        a.set_facecolor(SURFACE)
        a.grid(axis="y", color=GRID, linewidth=0.8)
        a.set_axisbelow(True)
        for side in ("top", "right"):
            a.spines[side].set_visible(False)

    # Left: trajectory.
    pre = list(range(1, slot))
    shared = [cond_mean("control", t) for t in pre]
    ax.plot(pre, shared, color=SHARED, linewidth=2, marker="o", markersize=7,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
    ax.text(pre[0] + 0.05, shared[1] - 2.0, "shared turns\n(all conditions)", va="top", color=MUTED, fontsize=9)
    ends = {}
    for c in conds + ["control"]:
        y = cond_mean(c, slot)
        ends[c] = y
        ax.plot([slot - 1, slot], [shared[-1], y], color=color[c], linewidth=2.6 if c == "control" else 2,
                linestyle="--" if c.startswith("meta") else "-", zorder=4 if c == "control" else 3)
        ax.plot([slot], [y], marker="o", markersize=8, color=color[c], markeredgecolor=SURFACE,
                markeredgewidth=2, zorder=5)
    # Direct labels at the slot, spread apart so they don't collide.
    placed = sorted(ends.items(), key=lambda kv: kv[1])
    span = max(ends.values()) - min(min(ends.values()), min(shared))
    gap = max(span * 0.055, 0.6)
    ys = []
    for _, y in placed:
        ys.append(max(y, ys[-1] + gap) if ys else y)
    for (c, y), ly in zip(placed, ys):
        ax.annotate(f"{c}  {y:.1f}", xy=(slot, y), xytext=(slot + 0.12, ly), va="center", fontsize=9,
                    color=INK, arrowprops=dict(arrowstyle="-", color=GRID, linewidth=0.8))
    ax.axvspan(slot - 0.25, slot + 0.25, color="#f1f0ec", zorder=0)
    ax.text(slot, 0.98, "slot", transform=ax.get_xaxis_transform(), ha="center", va="top", color=MUTED, fontsize=9)
    ax.set_xlim(0.7, slot + 1.25)
    ax.set_xticks(range(1, slot + 1))
    ax.set_xlabel("Turn")
    ax.set_ylabel("Projection on Assistant Axis (higher = more Assistant-like)")
    ax.set_title(f"Mean projection per turn ({len(seeds)} seed{'s' if len(seeds) > 1 else ''})", loc="left", color=INK, fontsize=11)

    # Right: slot-turn gap vs control, per seed.
    gaps = {c: [seed_mean(s, c, slot) - seed_mean(s, "control", slot) for s in seeds] for c in conds}
    ranked = sorted(conds, key=lambda c: statistics.mean(gaps[c]))
    markers = ["o", "s", "^", "D", "v"]
    lo = min(min(g) for g in gaps.values())
    for i, c in enumerate(ranked):
        m = statistics.mean(gaps[c])
        bx.barh(i, m, height=0.55, color=color[c], alpha=0.35 if c.startswith("meta") else 0.55,
                hatch="//" if c.startswith("meta") else None, edgecolor=SURFACE, linewidth=0)
        for j, (s, g) in enumerate(zip(seeds, gaps[c])):
            bx.plot(g, i, marker=markers[j % len(markers)], markersize=7, color=color[c],
                    markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
        bx.text(min(0, *gaps[c]) - 0.04 * abs(lo) - 0.3, i, f"{m:.1f}", va="center", ha="right", fontsize=9, color=INK)
    bx.axvline(0, color=MUTED, linewidth=1)
    bx.set_yticks(range(len(ranked)), ranked, color=INK)
    bx.set_ylim(len(ranked) - 0.4, -0.6)
    bx.set_xlim(lo * 1.25 - 1, max(1.5, max(max(g) for g in gaps.values()) + 1))
    bx.set_xlabel("Gap vs control at the slot (trigger − control)")
    bx.set_title("Drop vs control at the slot, per seed", loc="left", color=INK, fontsize=11)
    handles = [plt.Line2D([], [], marker=markers[j % len(markers)], linestyle="", color=MUTED,
                          markersize=7, label=s) for j, s in enumerate(seeds)]
    bx.legend(handles=handles, title="seed", frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=9, title_fontsize=9)

    fig.text(0.01, 0.01, "Solid = emotional disclosure, dashed/hatched = meta-reflection. "
             "Slot values are means over seeds of the per-seed mean over samples.",
             fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = run / "projection_by_turn.png"
    fig.savefig(out, dpi=160, facecolor=SURFACE)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
