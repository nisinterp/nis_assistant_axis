#!/usr/bin/env python3
"""Experiment A: generate conversations with a block of k trigger (or control) turns, plus probes.

Each conversation is `pre` neutral turns, a block of k turns, then `post` neutral turns:

    family_k{k}:  pre  + families[family][:k]   + post      e.g. grief_k2
    control_k{k}: pre  + controls[seed][:k]     + post

Neutral pre/post messages come from --prompts (prompts/prompts.json); blocks and the probe
question from --blocks (prompts/triggers_final.json).

Sharing: at every turn, conversations whose history (all messages so far, incl. the new user
message) is identical get ONE reply, copied to all of them. This shares the pre-slot turns
within a seed, and also the first trigger turns between doses (grief_k1/k2/k3 share turn
pre+1), so dose comparisons are exact up to where the conversations diverge. Conversations
of different lengths advance together, one turn at a time, in one vLLM batch per turn.

Probes are asked on copies of the history at points relative to the block:
    pre  = last neutral turn before the block      end = last block turn
    N    = N turns after the block (e.g. 1, 2, 5, 10)
Identical probe histories are also generated once (e.g. the 'pre' probe within a seed).

Context safeguard: if a conversation's prompt plus --max-tokens would exceed --max-model-len,
that conversation stops there (field `stopped_at` = the turn it could not generate) instead
of crashing the whole batch; probes at or after that turn, or whose own prompt is too long,
are skipped and listed in the log.

Usage:
    python experiment/generate_blocks.py --prompts prompts/prompts.json \
        --blocks prompts/triggers_final.json --out results/experiment_a/expA --seeds 10 --pre 3 --post 10 \
        --families grief phenomenology --doses 1 2 3 --probe-points pre end 1 2 5 10
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import CHAT_KWARGS, MODEL, Generator  # noqa: E402

logger = logging.getLogger("generate_blocks")


def build_conversations(prompts, blocks, args, stage):
    """Build one empty conversation per (seed, family or control, dose k) with its full list of user messages."""
    seeds = prompts["seeds"][:args.seeds]
    convs = []
    for s in seeds:
        if s["id"] not in blocks["controls"]:
            raise ValueError(f"no control block for seed {s['id']}")
        if len(s["pre"]) < args.pre or len(s["post"]) < args.post:
            raise ValueError(f"seed {s['id']} has too few pre/post messages")
        arms = [(f, blocks["families"][f]) for f in args.families] + [("control", blocks["controls"][s["id"]])]
        for family, block in arms:
            for k in args.doses:
                if len(block) < k:
                    raise ValueError(f"{family} block for {s['id']} has {len(block)} < {k} messages")
                user = s["pre"][:args.pre] + block[:k] + s["post"][:args.post]
                cond = f"{family}_k{k}"
                convs.append({
                    "id": f"{stage}/{s['id']}/{cond}", "stage": stage, "seed": s["id"], "condition": cond,
                    "family": family, "k": k, "sample": 0,
                    "block_start": args.pre + 1, "block_end": args.pre + k,
                    "slot_turn": args.pre + 1, "n_turns": len(user),
                    "user_messages": user, "messages": [], "turns": [],
                })
    return convs


def probe_turn(conv, point):
    """Turn number after which a probe point is asked ('pre', 'end', or N turns after the block)."""
    if point == "pre":
        return conv["block_start"] - 1
    if point == "end":
        return conv["block_end"]
    return conv["block_end"] + int(point)


def generate_deduped(gen, histories):
    """One reply per distinct history; returns replies aligned with `histories`."""
    keys = [json.dumps(h) for h in histories]
    unique = list(dict.fromkeys(keys))
    replies = gen.reply([json.loads(k) for k in unique])
    by_key = dict(zip(unique, replies))
    return [by_key[k] for k in keys], len(unique)


def main():
    """Parse arguments, generate all conversations turn by turn (deduplicating shared histories), then the probes."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--blocks", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stage", default=None, help="label stored in every row (default: out dir name)")
    parser.add_argument("--seeds", type=int, required=True, help="use the first N seeds")
    parser.add_argument("--pre", type=int, required=True)
    parser.add_argument("--post", type=int, required=True)
    parser.add_argument("--families", nargs="+", required=True)
    parser.add_argument("--doses", type=int, nargs="+", required=True, help="block lengths k")
    parser.add_argument("--probe-points", nargs="*", default=[], help="pre, end, and/or turns after the block")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-model-len", type=int, default=40960)
    parser.add_argument("--sampling-seed", type=int, default=0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    stage = args.stage or args.out.name
    prompts = json.loads(args.prompts.read_text())
    blocks = json.loads(args.blocks.read_text())
    convs = build_conversations(prompts, blocks, args, stage)
    for c in convs:
        for pt in args.probe_points:
            if not 1 <= probe_turn(c, pt) <= c["n_turns"]:
                raise ValueError(f"{c['id']}: probe point {pt} is outside the conversation")

    args.out.mkdir(parents=True, exist_ok=True)
    config = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}
    config.update(stage=stage, chat_kwargs=CHAT_KWARGS, probe=blocks["probe"],
                  conditions=sorted({c["condition"] for c in convs}))
    (args.out / "config.json").write_text(json.dumps(config, indent=2))

    gen = Generator(args.model, args.max_tokens, args.temperature, args.max_model_len, args.sampling_seed)
    budget = args.max_model_len - args.max_tokens

    def fits(history):
        """True if the prompt for this history leaves room for a full --max-tokens reply in the context."""
        return len(gen.tokenizer.encode(gen.prompt(history), add_special_tokens=False)) <= budget

    t0 = time.time()
    for t in range(1, max(c["n_turns"] for c in convs) + 1):
        active = [c for c in convs if c["n_turns"] >= t and "stopped_at" not in c]
        for c in active:
            c["messages"].append({"role": "user", "content": c["user_messages"][t - 1]})
        for c in [c for c in active if not fits(c["messages"])]:
            c["messages"].pop()
            c["stopped_at"] = t
            logger.warning("%s: stopped before turn %d (prompt + %d reply tokens > %d)",
                           c["id"], t, args.max_tokens, args.max_model_len)
        active = [c for c in active if "stopped_at" not in c]
        if not active:
            break
        replies, n_unique = generate_deduped(gen, [c["messages"] for c in active])
        for c, r in zip(active, replies):
            c["messages"].append({"role": "assistant", "content": r["text"]})
            c["turns"].append({"turn": t, "user": c["user_messages"][t - 1], "reply": r["text"],
                               "finish_reason": r["finish_reason"], "n_tokens": r["n_tokens"],
                               "is_slot": t == c["slot_turn"],
                               "is_block": c["block_start"] <= t <= c["block_end"],
                               "rel": t - c["block_end"]})
        logger.info("turn %d: %d conversations, %d generated, %d cut off", t, len(active), n_unique,
                    sum(r["finish_reason"] == "length" for r in replies))

    with open(args.out / "conversations.jsonl", "w") as f:
        for c in convs:
            row = {k: v for k, v in c.items() if k != "user_messages"}
            f.write(json.dumps(row) + "\n")

    jobs, skipped = [], []
    for c in convs:
        for pt in args.probe_points:
            t = probe_turn(c, pt)
            hist = c["messages"][:2 * t] + [{"role": "user", "content": blocks["probe"]}]
            if t > len(c["turns"]) or not fits(hist):
                skipped.append(f"{c['id']}/probe_{pt}")
            else:
                jobs.append((c, pt, t))
    if skipped:
        logger.warning("skipped %d probes (conversation stopped early or prompt too long): %s",
                       len(skipped), ", ".join(skipped))
    if jobs:
        histories = [c["messages"][:2 * t] + [{"role": "user", "content": blocks["probe"]}] for c, _, t in jobs]
        replies, n_unique = generate_deduped(gen, histories)
        with open(args.out / "probes.jsonl", "w") as f:
            for (c, pt, t), r in zip(jobs, replies):
                f.write(json.dumps({
                    "id": f"{c['id']}/probe_{pt}", "conversation_id": c["id"], "stage": stage,
                    "seed": c["seed"], "condition": c["condition"], "family": c["family"], "k": c["k"],
                    "sample": 0, "point": pt, "turn": t, "rel": t - c["block_end"],
                    "question": blocks["probe"], "reply": r["text"],
                    "finish_reason": r["finish_reason"], "n_tokens": r["n_tokens"],
                }) + "\n")
        logger.info("probes: %d (%d generated)", len(jobs), n_unique)

    logger.info("wrote %d conversations, %d probes to %s in %.0fs", len(convs), len(jobs), args.out, time.time() - t0)


if __name__ == "__main__":
    main()
