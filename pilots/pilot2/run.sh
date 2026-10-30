#!/bin/bash
# Pilot stage 2 on the GPU instance: 5 seeds x (chosen triggers from stage 1, control),
# 3 neutral turns + slot + 10 neutral turns = 14 turns, probes at turns 3, 4 and 14.
# Run from the project root as uploaded to /workspace/exp (experiment/, prompts/, pilots/).
# Usage: bash pilots/pilot2/run.sh <trigger> [<trigger> ...]   e.g. bash pilots/pilot2/run.sh meta_phenomenology emo_grief
set -e
[ $# -ge 1 ] || { echo "usage: run.sh <trigger> [<trigger> ...]"; exit 1; }
cd /workspace/exp
export HF_HOME=/workspace/.hf_home

/venv/main/bin/python experiment/generate.py --prompts prompts/prompts.json --out results/pilots/pilot2 \
    --pre 3 --post 10 --seeds 5 --conditions "$@" control --probe-turns 3 4 14
/workspace/p3venv/bin/python experiment/project.py --repo /workspace/assistant-axis --run results/pilots/pilot2
python3 pilots/pilot2/analyze.py results/pilots/pilot2
