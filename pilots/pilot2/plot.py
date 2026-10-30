#!/usr/bin/env python3
"""Pilot stage 2 figure: projection on the Assistant Axis over the 14 turns.

Left: mean projection per turn for each condition, band = 95% bootstrap CI over seeds.
Right: gap trigger - control per turn (within seed), band = 95% bootstrap CI over seeds,
with 0 = no difference from control. The slot and the probe turns are marked.

Usage:
    python pilots/pilot2/plot.py results/pilots/pilot2        # writes results/pilots/pilot2/projection_by_turn.png
"""

import json
import random
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Same validated slots as pilots/pilot1/plot.py, so a trigger keeps its colour across figures.
COLOR = {"emo_grief": "#2a78d6", "emo_fear": "#eb6834", "emo_anger": "#1baf7a",
         "meta_hedging": "#eda100", "meta_phenomenology": "#e87ba4", "meta_consciousness": "#008300",
         "control": "#52514e"}
INK, MUTED, GRID, SURFACE, BAND = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb", "#f1f0ec"
N_BOOT = 5000


def ci(xs, rng):
    """95% bootstrap confidence interval of the mean of xs."""
    means = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(N_BOOT))
    return means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT) - 1]


def style(a):
    """Apply the shared plot style to one axes."""
    a.set_facecolor(SURFACE)
    a.grid(axis="y", color=GRID, linewidth=0.8)
    a.set_axisbelow(True)
    for side in ("top", "right"):
        a.spines[side].set_visible(False)


def label_ends(ax, ends, x, min_gap):
    """Direct labels at the right end of each line, nudged apart so they don't collide."""
    placed = sorted(ends.items(), key=lambda kv: kv[1])
    ys = []
    for _, y in placed:
        ys.append(max(y, ys[-1] + min_gap) if ys else y)
    for (c, y), ly in zip(placed, ys):
        ax.annotate(c, xy=(x, y), xytext=(x + 0.35, ly), va="center", fontsize=9, color=INK,
                    arrowprops=dict(arrowstyle="-", color=GRID, linewidth=0.8))


def main():
    """Draw projection per turn and gap vs control (projection_by_turn.png), then recovery.png."""
    run = Path(sys.argv[1])
    projs = [json.loads(line) for line in open(run / "projections.jsonl")]
    config = json.loads((run / "config.json").read_text())
    slot, n_turns = config["slot_turn"], config["n_turns"]
    probe_turns = config.get("probe_turns", [])
    proj = {(p["seed"], p["condition"], p["turn"]): p["projection"] for p in projs}
    seeds = sorted({p["seed"] for p in projs})
    conds = list(dict.fromkeys(p["condition"] for p in projs))
    triggers = [c for c in conds if c != "control"]
    turns = list(range(1, n_turns + 1))
    rng = random.Random(0)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                         "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 5.2), facecolor=SURFACE)
    for a in (ax, bx):
        style(a)
        a.axvspan(slot - 0.4, slot + 0.4, color=BAND, zorder=0)
        a.text(slot, 0.99, "slot", transform=a.get_xaxis_transform(), ha="center", va="top",
               color=MUTED, fontsize=9)
        for t in probe_turns:
            a.text(t, 0.0, "▲", transform=a.get_xaxis_transform(), ha="center", va="bottom",
                   color=MUTED, fontsize=7)
        a.set_xticks(turns)
        a.set_xlim(0.6, n_turns + 2.6)
        a.set_xlabel("Turn  (▲ = probe turn)")

    # Left: projection per condition.
    ends = {}
    for c in triggers + ["control"]:
        means, los, his = [], [], []
        for t in turns:
            xs = [proj[(s, c, t)] for s in seeds]
            lo, hi = ci(xs, rng)
            means.append(statistics.mean(xs)), los.append(lo), his.append(hi)
        col = COLOR.get(c, MUTED)
        ax.fill_between(turns, los, his, color=col, alpha=0.12, linewidth=0)
        ax.plot(turns, means, color=col, linewidth=2.6 if c == "control" else 2,
                linestyle="--" if c.startswith("meta") else "-", zorder=3)
        ax.plot(turns, means, linestyle="", marker="o", markersize=5, color=col,
                markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=4)
        ends[c] = means[-1]
    span = ax.get_ylim()[1] - ax.get_ylim()[0]
    label_ends(ax, ends, n_turns, span * 0.05)
    ax.set_ylabel("Projection on Assistant Axis (higher = more Assistant-like)")
    ax.set_title(f"Mean projection per turn ({len(seeds)} seeds, band = 95% CI)", loc="left",
                 color=INK, fontsize=11)

    # Right: gap vs control.
    bx.axhline(0, color=MUTED, linewidth=1)
    ends = {}
    for c in triggers:
        means, los, his = [], [], []
        for t in turns:
            gaps = [proj[(s, c, t)] - proj[(s, "control", t)] for s in seeds]
            lo, hi = ci(gaps, rng)
            means.append(statistics.mean(gaps)), los.append(lo), his.append(hi)
        col = COLOR.get(c, MUTED)
        bx.fill_between(turns, los, his, color=col, alpha=0.15, linewidth=0)
        bx.plot(turns, means, color=col, linewidth=2, linestyle="--" if c.startswith("meta") else "-",
                marker="o", markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
        ends[c] = means[-1]
    span = bx.get_ylim()[1] - bx.get_ylim()[0]
    label_ends(bx, ends, n_turns, span * 0.05)
    bx.set_ylabel("Gap vs control (trigger − control)")
    bx.set_title("Drift relative to control (0 = recovered)", loc="left", color=INK, fontsize=11)

    fig.text(0.01, 0.01, "Solid = emotional disclosure, dashed = meta-reflection. "
             "Turns before the slot are shared, so all conditions coincide there.",
             fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = run / "projection_by_turn.png"
    fig.savefig(out, dpi=160, facecolor=SURFACE)
    print(f"wrote {out}")
    plot_recovery(run, proj, seeds, triggers, slot, n_turns, rng)


def plot_recovery(run, proj, seeds, triggers, slot, n_turns, rng):
    """How fast the gap closes after the slot.

    Left: gap as % of that trigger's slot gap (per seed, then averaged), so triggers of very
    different strength share one 100% -> 0% scale. Right: the raw gap after the slot only,
    zoomed in so residuals of ~1 point are visible.
    """
    after = list(range(0, n_turns - slot + 1))  # turns after the trigger; 0 = the slot itself
    notes = []
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 5.2), facecolor=SURFACE)
    for a in (ax, bx):
        style(a)
        a.axhline(0, color=MUTED, linewidth=1)
    for c in triggers:
        col, ls = COLOR.get(c, MUTED), "--" if c.startswith("meta") else "-"
        gap = {s: [proj[(s, c, slot + k)] - proj[(s, "control", slot + k)] for k in after] for s in seeds}
        # Left: percent of slot gap remaining.
        pct = [[100 * gap[s][k] / gap[s][0] for s in seeds] for k in after]
        m = [statistics.mean(x) for x in pct]
        lo, hi = zip(*(ci(x, rng) for x in pct))
        ax.fill_between(after, lo, hi, color=col, alpha=0.15, linewidth=0)
        ax.plot(after, m, color=col, linestyle=ls, linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=c, zorder=3)
        notes.append(f"{c}: {m[1]:.0f}% left after 1 turn, {m[-1]:.0f}% after {after[-1]}")
        # Right: raw gap after the slot, zoomed.
        ks = after[1:]
        raw = [[gap[s][k] for s in seeds] for k in ks]
        m2 = [statistics.mean(x) for x in raw]
        lo2, hi2 = zip(*(ci(x, rng) for x in raw))
        bx.fill_between(ks, lo2, hi2, color=col, alpha=0.15, linewidth=0)
        bx.plot(ks, m2, color=col, linestyle=ls, linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=c, zorder=3)
        row = 0.04 + 0.05 * triggers.index(c)  # one marker strip per trigger along the bottom
        for k, h in zip(ks, hi2):
            if h < 0:  # CI entirely below 0: still drifted at this turn
                bx.plot(k, row, marker="v", color=col, markersize=7, linestyle="",
                        transform=bx.get_xaxis_transform())
    ax.set_xticks(after)
    ax.set_xlabel("Turns after the trigger (0 = trigger turn)")
    ax.set_ylabel("Gap left, % of the drop at the trigger turn")
    ax.set_title(f"Recovery: share of the drop left ({len(seeds)} seeds, band = 95% CI)", loc="left",
                 color=INK, fontsize=11)
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    ax.text(0.98, 0.78, "\n".join(notes), transform=ax.transAxes, ha="right", va="top", fontsize=9, color=INK)
    bx.set_xticks(after[1:])
    bx.set_xlabel("Turns after the trigger")
    bx.set_ylabel("Gap vs control (trigger − control)")
    bx.set_title("After the trigger, zoomed (▼ = turn where 95% CI is below 0)", loc="left", color=INK, fontsize=11)
    bx.legend(frameon=False, loc="upper right", fontsize=9)
    fig.text(0.01, 0.01, "Solid = emotional disclosure, dashed = meta-reflection. "
             "Gap is computed within each seed, so the shared offset of the axis cancels out.",
             fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = run / "recovery.png"
    fig.savefig(out, dpi=160, facecolor=SURFACE)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
