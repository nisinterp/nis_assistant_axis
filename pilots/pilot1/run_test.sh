#!/bin/bash
# Smoke test before pilot stage 1: 1 seed (csv_parser), emo_grief vs control,
# 3 neutral turns + slot, 4 slot samples each. Same code path as run.sh.
set -e
cd /workspace/exp
export HF_HOME=/workspace/.hf_home

/venv/main/bin/python experiment/generate.py --prompts prompts/prompts.json --out results/pilots/pilot1_test \
    --pre 3 --post 0 --seeds 1 --slot-samples 4 --conditions emo_grief control
/workspace/p3venv/bin/python experiment/project.py --repo /workspace/assistant-axis --run results/pilots/pilot1_test
python3 pilots/pilot1/analyze.py results/pilots/pilot1_test
