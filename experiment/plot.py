#!/usr/bin/env python3
"""Experiment A figures.

recovery.png  one panel per family: gap vs matched control per turn, aligned on the end of the
              block (rel 0), one line per dose k, band = 95% bootstrap CI over seeds.
probes.png    same layout for the probe replies (projected).
judge.png     same layout for the probe replies' Haiku scores (higher = more drift, unlike the axis).

Usage:
    python experiment/plot.py results/experiment_a/expA
"""

import json
import random
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DOSE = {1: "#86b6ef", 2: "#3987e5", 3: "#184f95"}  # validated ordinal blue ramp (light -> dark = more turns)
INK, MUTED, GRID, SURFACE, BAND = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb", "#f1f0ec"
N_BOOT = 5000


def ci(xs, rng):
    """95% bootstrap confidence interval of the mean of xs."""
    means = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(N_BOOT))
    return means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT) - 1]


def load(path):
    """Read a JSONL file into a list of dicts; empty list if the file does not exist."""
    return [json.loads(line) for line in open(path)] if path.exists() else []


def figure(rows, run, name, title, ylabel, marker_only=False):
    """Draw one panel per family: mean gap vs matched control per rel, one line per dose, with CI band."""
    rng = random.Random(0)
    val = {(r["seed"], r["condition"], r["rel"]): r["projection"] for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    fams = sorted({r["condition"].rsplit("_k", 1)[0] for r in rows} - {"control"})
    doses = sorted({int(r["condition"].rsplit("_k", 1)[1]) for r in rows})
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                         "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
    fig, axes = plt.subplots(1, len(fams), figsize=(6.5 * len(fams), 5), facecolor=SURFACE, squeeze=False)
    for ax, fam in zip(axes[0], fams):
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.axhline(0, color=MUTED, linewidth=1)
        ax.axvspan(-0.4, 0.4, color=BAND, zorder=0)
        ax.text(0, 0.01, "end of block", transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                color=MUTED, fontsize=9)
        for k in doses:
            rels = sorted({r for (_, c, r) in val if c == f"{fam}_k{k}"})
            xs, m, lo, hi = [], [], [], []
            for r in rels:
                g = [val[(s, f"{fam}_k{k}", r)] - val[(s, f"control_k{k}", r)] for s in seeds
                     if (s, f"{fam}_k{k}", r) in val and (s, f"control_k{k}", r) in val]
                if g:
                    a, b = ci(g, rng)
                    xs.append(r), m.append(statistics.mean(g)), lo.append(a), hi.append(b)
            ax.fill_between(xs, lo, hi, color=DOSE.get(k, MUTED), alpha=0.18, linewidth=0)
            ax.plot(xs, m, color=DOSE.get(k, MUTED), linewidth=0 if marker_only else 2, marker="o", markersize=6,
                    markeredgecolor=SURFACE, markeredgewidth=1.5, label=f"k = {k} trigger turn{'s' if k > 1 else ''}",
                    zorder=3)
        ax.set_title(f"{fam}", loc="left", color=INK, fontsize=11)
        ax.set_xlabel("Turns relative to the end of the trigger block")
        ax.set_ylabel(ylabel)
        ax.legend(frameon=False, loc="lower right", fontsize=9)
    fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=12)
    fig.text(0.01, 0.01, f"{len(seeds)} seeds. Gap = trigger − matched control (same k) at the same turn, "
             "within seed; band = 95% bootstrap CI over seeds.", fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(run / name, dpi=160, facecolor=SURFACE)
    print(f"wrote {run / name}")


def probe_x(row):
    """Probe position on the plot: the shared 'pre' probe sits just before the block."""
    return -1 if row["point"] == "pre" else row["rel"]


def main():
    """Write recovery.png, probes.png and (if judged) judge.png into the run directory."""
    run = Path(sys.argv[1])
    figure(load(run / "projections.jsonl"), run, "recovery.png",
           "Coding replies: gap vs control around the trigger block", "Gap vs control (trigger − control)")
    probes = [{**r, "rel": probe_x(r)} for r in load(run / "probe_projections.jsonl")]
    if probes:
        figure(probes, run, "probes.png", "Probe replies (“how would you describe yourself?”): gap vs control",
               "Probe reply gap vs control", marker_only=False)
    key_path, scores_path = run / "key.json", run / "judge_scores.jsonl"
    if key_path.exists() and scores_path.exists():
        key = json.loads(key_path.read_text())
        by_id = {p["id"]: p for p in load(run / "probes.jsonl")}
        judged = [{**by_id[key[r["id"]]], "projection": r["score"]} for r in load(scores_path) if r.get("score") is not None]
        judged = [{**r, "rel": probe_x(r)} for r in judged]
        figure(judged, run, "judge.png", "Probe replies, Haiku score (0 = assistant … 3 = other persona): gap vs control",
               "Judge score gap vs control (higher = more drift)")


if __name__ == "__main__":
    main()
