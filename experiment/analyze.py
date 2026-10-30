#!/usr/bin/env python3
"""Main experiment: does recovery after a block of k trigger turns depend on k?

All gaps are within seed: trigger condition `{family}_k{k}` minus `control_k{k}` at the same
turn (same k, so same turn positions and the same number of turns of history).
`rel` = turns relative to the end of the block (0 = last block turn, 1 = first neutral turn
after it). CIs are bootstrap over seeds.

1. Conversation turns: gap at the end of the block, at rel = 1, 2, 5, 10, and the mean
   residual over rel = 1..10. Dose effect: residual(k=3) - residual(k=1), paired by seed.
2. Probe replies, projected (probe_projections.jsonl): gap per probe point. If coding turns
   are back at control level but probe replies are not, the drift is hidden, not gone.
3. Probe judge scores (once judge_scores.jsonl + key.json exist): same, on the 0-3 scale.
4. Reply lengths and cut-offs.

Writes report.md and results.json into the run directory. Standard library only.

Usage:
    python experiment/analyze.py results/main_experiment
"""

import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

N_BOOT = 10000
CHECK_RELS = [0, 1, 2, 5, 10]


def load(path):
    """Read a JSONL file into a list of dicts; empty list if the file does not exist."""
    return [json.loads(line) for line in open(path)] if path.exists() else []


def summarize(xs, rng):
    """mean, 95% bootstrap CI over seeds, number of seeds below 0."""
    means = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(N_BOOT))
    return {"mean": statistics.mean(xs), "ci": [means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT) - 1]],
            "neg": sum(x < 0 for x in xs), "pos": sum(x > 0 for x in xs), "n": len(xs)}


def fmt(s, digits=2, higher_is_drift=False):
    """Projection gaps: drift = below 0. Judge-score gaps: drift = above 0."""
    if s is None:
        return "—"
    count = f"{s['pos']}/{s['n']} > 0" if higher_is_drift else f"{s['neg']}/{s['n']} < 0"
    return f"{s['mean']:.{digits}f} [{s['ci'][0]:.{digits}f}, {s['ci'][1]:.{digits}f}] ({count})"


def main():
    """Compute gaps vs control for turns, probe projections and judge scores; write report.md and results.json."""
    run = Path(sys.argv[1])
    convs = load(run / "conversations.jsonl")
    rng = random.Random(0)
    seeds = sorted({c["seed"] for c in convs})
    families = sorted({c["family"] for c in convs} - {"control"})
    doses = sorted({c["k"] for c in convs})

    # value[(kind, seed, condition, rel)] for kind in turn / probe / judge
    value = {}
    for p in load(run / "projections.jsonl"):
        value[("turn", p["seed"], p["condition"], p["rel"])] = p["projection"]
    for p in load(run / "probe_projections.jsonl"):
        value[("probe", p["seed"], p["condition"], p["point"])] = p["projection"]
    judged = False
    key_path, scores_path = run / "key.json", run / "judge_scores.jsonl"
    if key_path.exists() and scores_path.exists():
        key = json.loads(key_path.read_text())
        probes = {p["id"]: p for p in load(run / "probes.jsonl")}
        for r in load(scores_path):
            if r.get("score") is not None:
                p = probes[key[r["id"]]]
                value[("judge", p["seed"], p["condition"], p["point"])] = r["score"]
                judged = True

    def gaps(kind, fam, k, rel):
        """Per-seed differences trigger - control for one value kind, family, dose and rel/probe point."""
        xs = [value[(kind, s, f"{fam}_k{k}", rel)] - value[(kind, s, f"control_k{k}", rel)]
              for s in seeds if (kind, s, f"{fam}_k{k}", rel) in value and (kind, s, f"control_k{k}", rel) in value]
        return xs

    def gap_stat(kind, fam, k, rel):
        """summarize() of gaps(), or None if no seed has both values."""
        xs = gaps(kind, fam, k, rel)
        return summarize(xs, rng) if xs else None

    max_rel = max(t["rel"] for c in convs for t in c["turns"])
    probe_points = list(dict.fromkeys(json.loads((run / "config.json").read_text()).get("probe_points", [])))
    results = {"run": str(run), "seeds": seeds, "families": families, "doses": doses, "per_condition": {}}

    out = [f"# Main experiment — recovery after k trigger turns (`{run}`)", "",
           f"{len(seeds)} seeds. Gap = `family_kK` − `control_kK` at the same turn, within seed; "
           "mean [95% bootstrap CI over seeds] (seeds below 0). `rel` = turns after the end of the block.", ""]

    # 1. Conversation turns.
    out += ["## 1. Coding replies after the block", "",
            "| condition | end of block (rel 0) | rel 1 | rel 2 | rel 5 | rel 10 | mean residual, rel 1–10 |",
            "|---|---|---|---|---|---|---|"]
    residual_by_seed = {}
    for fam in families:
        for k in doses:
            row = {r: gap_stat("turn", fam, k, r) for r in CHECK_RELS}
            per_seed = {}
            for s in seeds:
                xs = [value[("turn", s, f"{fam}_k{k}", r)] - value[("turn", s, f"control_k{k}", r)]
                      for r in range(1, max_rel + 1)
                      if ("turn", s, f"{fam}_k{k}", r) in value and ("turn", s, f"control_k{k}", r) in value]
                if xs:
                    per_seed[s] = statistics.mean(xs)
            residual_by_seed[(fam, k)] = per_seed
            resid = summarize(list(per_seed.values()), rng)
            results["per_condition"][f"{fam}_k{k}"] = {
                "turn_gaps": {r: gap_stat("turn", fam, k, r) for r in range(-k - 2, max_rel + 1)},
                "residual": resid,
            }
            out.append(f"| `{fam}_k{k}` | " + " | ".join(fmt(row[r]) for r in CHECK_RELS) + f" | {fmt(resid)} |")
    out.append("")

    out += ["**Dose effect** (paired by seed): residual(k=3) − residual(k=1). Negative = longer drift leaves "
            "more drift behind.", ""]
    if 1 in doses and 3 in doses:
        for fam in families:
            a, b = residual_by_seed[(fam, 3)], residual_by_seed[(fam, 1)]
            d = [a[s] - b[s] for s in seeds if s in a and s in b]
            st = summarize(d, rng)
            results["per_condition"][f"{fam}_dose_effect"] = st
            out.append(f"- `{fam}`: {fmt(st)}")
    out.append("")

    # 2/3. Probes.
    for kind, title in (("probe", "2. Probe replies, projected on the axis"),
                        ("judge", "3. Probe replies, judge score (0 = assistant … 3 = other persona)")):
        out += [f"## {title}", ""]
        if kind == "judge" and not judged:
            out += ["Not judged yet (needs key.json and judge_scores.jsonl; see experiment/README.md).", ""]
            continue
        if kind == "probe" and not any(k[0] == "probe" for k in value):
            out += ["No probe_projections.jsonl (run project.py with --probes).", ""]
            continue
        out += ["Gap vs the matched control at each probe point. The `pre` probe (before the block) is shared "
                "by all conditions of a seed, so its gap is 0 by construction.", "",
                "Probe points: `pre` = before the block, `end` = last block turn, N = N turns after the block.", "",
                "| condition | " + " | ".join(probe_points) + " |",
                "|---|" + "---|" * len(probe_points)]
        for fam in families:
            for k in doses:
                stats = {pt: gap_stat(kind, fam, k, pt) for pt in probe_points}
                results["per_condition"][f"{fam}_k{k}"][f"{kind}_gaps"] = stats
                out.append(f"| `{fam}_k{k}` | " + " | ".join(fmt(stats[pt], higher_is_drift=kind == "judge")
                                                          for pt in probe_points) + " |")
        out.append("")

    # 4. Lengths.
    all_turns = [(c["condition"], t) for c in convs for t in c["turns"]]
    cut, count = defaultdict(int), defaultdict(int)
    for cond, t in all_turns:
        count[cond] += 1
        cut[cond] += t["finish_reason"] == "length"
    longest = max(convs, key=lambda c: sum(t["n_tokens"] for t in c["turns"]))
    over = sum(t["n_tokens"] > 1024 for _, t in all_turns)
    stopped = [f"`{c['id']}` (before turn {c['stopped_at']})" for c in convs if "stopped_at" in c]
    out += ["## 4. Reply lengths", "",
            f"- Conversations stopped early by the context safeguard: {', '.join(stopped) if stopped else 'none'}.",
            f"- Replies over 1024 tokens: {over}/{len(all_turns)} ({over / len(all_turns):.0%}).",
            "- Cut off at the limit: " + ", ".join(f"{c} {cut[c]}/{count[c]}" for c in sorted(count)),
            f"- Longest conversation: `{longest['id']}`, {sum(t['n_tokens'] for t in longest['turns'])} reply tokens."]
    results["cutoffs"] = {c: [cut[c], count[c]] for c in count}

    (run / "results.json").write_text(json.dumps(results, indent=2))
    (run / "report.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
