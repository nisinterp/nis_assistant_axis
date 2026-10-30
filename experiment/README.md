# Experiment A (revised): recovery after k trigger turns

Design and rationale: `spec.md`, "Step 3. Full Experiment A (revised)". 5 seeds × 9 conditions
(`grief_k1..3`, `phenomenology_k1..3`, `control_k1..3`); each conversation is 3 neutral turns,
a block of k trigger or control turns, then 10 neutral turns. Probes are asked before the block,
at its end, and 1, 2, 5 and 10 turns after it.

Messages: `prompts/prompts.json` (neutral pre/post messages) and `prompts/triggers_final.json`
(trigger blocks, matched control blocks, probe question).

## Steps

1. **GPU** (instance, ~30–35 min). Upload `experiment/` and `prompts/` to
   `/workspace/exp`, make sure Vast's built-in model server is stopped
   (`supervisorctl stop vllm`, and kill any leftover `vllm serve` process), then:
   ```
   bash experiment/run_a.sh
   ```
   This generates the conversations and probes, projects every turn and every probe reply
   (`--verify-probes 3` logs cached vs. direct projections for 3 probes; they should agree to
   about 0.01), and writes `results/experiment_a/expA/report.md`. Copy `results/experiment_a/expA/` back, then the GPU can be stopped.

2. **Figures** (local): `python experiment/plot.py results/experiment_a/expA` → `recovery.png`, `probes.png`.

3. **Blind and judge** (local, Message Batch, ~$0.05; needs `ANTHROPIC_API_KEY`):
   ```
   python experiment/blind.py results/experiment_a/expA --sheet-n 0
   .venv/bin/python judge/judge.py --judge-backend anthropic --model claude-haiku-5-5 \
       --in results/experiment_a/expA/judge_in.jsonl --out results/experiment_a/expA/judge_scores.jsonl
   python experiment/analyze.py results/experiment_a/expA
   ```
   Use `claude-sonnet-5-5` instead if the pilot-2 judge check failed.

4. **Read the transcripts** (optional): `python experiment/export_transcripts.py results/experiment_a/expA --probes`.
