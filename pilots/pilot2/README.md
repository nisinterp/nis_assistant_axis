# Pilot stage 2: does the drift fade at all?

Spec: Experiment A, step 2. 5 seeds × 2 conditions (the best trigger from pilot 1, and control).
Each conversation is 3 neutral turns + slot + 10 neutral turns = 14 turns. Probes at turns 3, 4 and 14 give 30 probe replies.
All messages come from `prompts/prompts.json`: the first 5 seeds, `pre[0:3]`, the seed's control, and `post[0:10]`.

## Steps

1. **GPU** (instance, ~20 min). Pass the trigger chosen from `results/pilots/pilot1/report.md`:
   ```
   bash pilots/pilot2/run.sh emo_grief
   ```
   This generates the conversations and probes, projects every turn, and writes `results/pilots/pilot2/report.md` with the go / no-go verdict (no judge scores yet). After this the GPU can be turned off.

2. **Blind** (local). Replaces probe ids with random ones so neither the judge nor you can see the condition or turn:
   ```
   python experiment/blind.py results/pilots/pilot2
   ```
   It writes `judge_in.jsonl`, `key.json` (don't open it yet) and `human_scores.csv` (20 random probes).

3. **Score the 20 rows yourself** in `results/pilots/pilot2/human_scores.csv` (`your_score` 0–3, rubric in `judge/rubric.txt`), before looking at any judge output.

4. **Judge** (local, Message Batch, ~$0.01; needs `ANTHROPIC_API_KEY`):
   ```
   .venv/bin/python judge/judge.py --judge-backend anthropic --model claude-haiku-5-5 \
       --in results/pilots/pilot2/judge_in.jsonl --out results/pilots/pilot2/judge_scores.jsonl
   ```

5. **Judge check on real replies.** Spec: Haiku must be within 1 point of you on ≥ 18/20; otherwise use Sonnet for full A.
   ```
   .venv/bin/python judge/compare.py --judge results/pilots/pilot2/judge_scores.jsonl \
       --human results/pilots/pilot2/human_scores.csv --replies results/pilots/pilot2/judge_in.jsonl --levels "" \
       --min-exact 0 --min-within1 0.9 --title "Pilot 2 judge check" --out results/pilots/pilot2/judge_check.md
   ```

6. **Final report** with judge scores added:
   ```
   python pilots/pilot2/analyze.py results/pilots/pilot2
   ```

## Go / no-go (spec)

- **Go:** at the slot turn, the trigger is below control in ≥ 4 of 5 seeds. Also look at how much of the gap is left at turn 14.
- **No-go:** no clear drop. Stop and write up the negative result.

The report also shows the share of replies over 1024 tokens. That is the spec's check for whether full A can use a 1024 reply limit.
