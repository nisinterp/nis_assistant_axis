#!/bin/bash
# Experiment A on the GPU instance. 5 seeds x 9 conditions:
#   grief_k{1,2,3}, phenomenology_k{1,2,3}, control_k{1,2,3}
# 3 neutral turns + block of k turns + 10 neutral turns (14-16 turns),
# probes at: before the block, end of block, and 1, 2, 5, 10 turns after it (270 probes).
# Run from the project root as uploaded to /workspace/exp (experiment/, prompts/).
# Before running: make sure Vast's built-in vLLM service is stopped (supervisorctl stop vllm).
set -e
cd /workspace/exp
export HF_HOME=/workspace/.hf_home

/venv/main/bin/python experiment/generate_blocks.py --prompts prompts/prompts.json \
    --blocks prompts/triggers_final.json --out results/experiment_a/expA --seeds 5 --pre 3 --post 10 \
    --families grief phenomenology --doses 1 2 3 --probe-points pre end 1 2 5 10
/workspace/p3venv/bin/python experiment/project.py --repo /workspace/assistant-axis --run results/experiment_a/expA \
    --probes --verify-probes 3
python3 experiment/analyze.py results/experiment_a/expA
