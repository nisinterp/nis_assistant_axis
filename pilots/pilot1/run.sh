#!/bin/bash
# Pilot stage 1 on the GPU instance: 3 seeds x 7 conditions x 4 slot samples, 3 neutral turns + slot, no probes.
# Run from the project root as uploaded to /workspace/exp (experiment/, prompts/, pilots/).
# Afterwards copy results/pilots/pilot1/ back and run pilots/pilot1/analyze.py (it also runs here, stdlib only).
set -e
cd /workspace/exp
export HF_HOME=/workspace/.hf_home

/venv/main/bin/python experiment/generate.py --prompts prompts/prompts.json --out results/pilots/pilot1 \
    --pre 3 --post 0 --seeds 3 --slot-samples 4 \
    --conditions emo_grief emo_fear emo_anger meta_hedging meta_phenomenology meta_consciousness control
/workspace/p3venv/bin/python experiment/project.py --repo /workspace/assistant-axis --run results/pilots/pilot1
python3 pilots/pilot1/analyze.py results/pilots/pilot1
