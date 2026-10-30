#!/usr/bin/env python3
"""Generate conversations (and probe replies) with vLLM.

Every conversation is `pre` neutral turns, one slot turn (a trigger or the
seed's control message), then `post` neutral turns. The pre-slot turns are
generated once per seed and copied into each condition. All conversations move
forward one turn at a time in one vLLM batch. Probes run afterwards on copies
of the history and are saved to a separate file.

Turns are numbered from 1; the slot is turn pre + 1.

With --slot-samples k, each (seed, condition) is run k times from the slot on (same
shared prefix, independent sampling), so the noise of a single reply can be measured.
Conversation ids then end in /s0 ... /s{k-1}.

Usage:
    python experiment/generate.py --prompts prompts/prompts.json --out results/pilots/pilot2 \
        --pre 3 --post 10 --seeds 5 --conditions meta_phenomenology emo_grief control --probe-turns 3 4 14
"""

import argparse
import json
import logging
import time
from pathlib import Path

MODEL = "Qwen/Qwen3-32B-AWQ"
CHAT_KWARGS = {"enable_thinking": False}

logger = logging.getLogger("generate")


def load_prompts(path, conditions, n_seeds, pre, post):
    """Load the prompts file and check the conditions exist and every seed has enough pre/post messages."""
    prompts = json.loads(Path(path).read_text())
    seeds = prompts["seeds"][:n_seeds] if n_seeds else prompts["seeds"]
    for c in conditions:
        if c != "control" and c not in prompts["triggers"]:
            raise ValueError(f"unknown condition {c!r}")
    for s in seeds:
        if len(s["pre"]) < pre or len(s["post"]) < post:
            raise ValueError(f"seed {s['id']} has {len(s['pre'])} pre / {len(s['post'])} post messages")
    return prompts, seeds


def slot_message(prompts, seed, condition):
    """User message for the slot turn: the seed's control message, or the named trigger."""
    return seed["control"] if condition == "control" else prompts["triggers"][condition]


def check_control_lengths(tokenizer, prompts, seeds, conditions):
    """Spec: controls are within ±10% of the trigger's token count. Warn only."""
    for s in seeds:
        n_control = len(tokenizer.encode(s["control"]))
        for c in conditions:
            if c == "control":
                continue
            n_trigger = len(tokenizer.encode(prompts["triggers"][c]))
            if abs(n_control - n_trigger) > 0.1 * n_trigger:
                logger.warning("seed %s: control %d tokens vs %s %d tokens (>10%% apart)",
                               s["id"], n_control, c, n_trigger)


class Generator:
    """Wraps a vLLM engine and generates one reply per conversation history."""
    def __init__(self, model, max_tokens, temperature, max_model_len, seed):
        """Load the model into vLLM (prefix caching on, so shared history is computed once)."""
        from vllm import LLM, SamplingParams

        self.llm = LLM(model=model, max_model_len=max_model_len, seed=seed,
                       gpu_memory_utilization=0.9, enable_prefix_caching=True)
        self.tokenizer = self.llm.get_tokenizer()
        self.params = SamplingParams(temperature=temperature, max_tokens=max_tokens)

    def prompt(self, history):
        """Render a message history as a prompt string with Qwen's chat template (thinking off)."""
        return self.tokenizer.apply_chat_template(
            history, tokenize=False, add_generation_prompt=True, **CHAT_KWARGS
        )

    def reply(self, histories):
        """One reply per history, all in one batch."""
        outputs = self.llm.generate([self.prompt(h) for h in histories], self.params)
        return [
            {"text": o.outputs[0].text, "finish_reason": o.outputs[0].finish_reason,
             "n_tokens": len(o.outputs[0].token_ids)}
            for o in outputs
        ]


def run_turn(gen, convs, user_texts, turn):
    """Add one user message to each conversation, generate all replies in one batch, and record the turn."""
    for conv, text in zip(convs, user_texts):
        conv["messages"].append({"role": "user", "content": text})
    replies = gen.reply([c["messages"] for c in convs])
    for conv, text, r in zip(convs, user_texts, replies):
        conv["messages"].append({"role": "assistant", "content": r["text"]})
        conv["turns"].append({"turn": turn, "user": text, "reply": r["text"],
                              "finish_reason": r["finish_reason"], "n_tokens": r["n_tokens"],
                              "is_slot": turn == conv["slot_turn"]})
    logger.info("turn %d: %d replies, %d cut off", turn, len(replies),
                sum(r["finish_reason"] == "length" for r in replies))


def main():
    """Parse arguments, generate the shared prefix, then every condition's slot and post-slot turns, then the probes."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stage", default=None, help="label stored in every row (default: out dir name)")
    parser.add_argument("--pre", type=int, required=True, help="neutral turns before the slot")
    parser.add_argument("--post", type=int, required=True, help="neutral turns after the slot")
    parser.add_argument("--conditions", nargs="+", required=True, help="trigger names and/or 'control'")
    parser.add_argument("--seeds", type=int, default=None, help="use the first N seeds (default: all)")
    parser.add_argument("--probe-turns", type=int, nargs="*", default=[])
    parser.add_argument("--slot-samples", type=int, default=1,
                        help="independent conversations per (seed, condition) from the slot on")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-model-len", type=int, default=32768)
    parser.add_argument("--sampling-seed", type=int, default=0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    stage = args.stage or args.out.name
    slot_turn = args.pre + 1
    n_turns = args.pre + 1 + args.post
    for t in args.probe_turns:
        if not 1 <= t <= n_turns:
            raise ValueError(f"probe turn {t} outside 1..{n_turns}")

    prompts, seeds = load_prompts(args.prompts, args.conditions, args.seeds, args.pre, args.post)
    args.out.mkdir(parents=True, exist_ok=True)
    config = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}
    config.update(stage=stage, slot_turn=slot_turn, n_turns=n_turns, chat_kwargs=CHAT_KWARGS)
    (args.out / "config.json").write_text(json.dumps(config, indent=2))

    gen = Generator(args.model, args.max_tokens, args.temperature, args.max_model_len, args.sampling_seed)
    check_control_lengths(gen.tokenizer, prompts, seeds, args.conditions)
    t0 = time.time()

    # Shared prefix: one conversation per seed for the pre-slot turns.
    prefixes = [{"messages": [], "turns": [], "slot_turn": slot_turn} for _ in seeds]
    for i in range(args.pre):
        run_turn(gen, prefixes, [s["pre"][i] for s in seeds], i + 1)

    convs = []
    for s, prefix in zip(seeds, prefixes):
        for c in args.conditions:
            for k in range(args.slot_samples):
                suffix = f"/s{k}" if args.slot_samples > 1 else ""
                convs.append({
                    "id": f"{stage}/{s['id']}/{c}{suffix}", "stage": stage, "seed": s["id"],
                    "condition": c, "sample": k, "slot_turn": slot_turn, "n_turns": n_turns,
                    "messages": json.loads(json.dumps(prefix["messages"])),
                    "turns": json.loads(json.dumps(prefix["turns"])),
                })

    seed_by_id = {s["id"]: s for s in seeds}
    run_turn(gen, convs, [slot_message(prompts, seed_by_id[c["seed"]], c["condition"]) for c in convs], slot_turn)
    for i in range(args.post):
        run_turn(gen, convs, [seed_by_id[c["seed"]]["post"][i] for c in convs], slot_turn + 1 + i)

    with open(args.out / "conversations.jsonl", "w") as f:
        for c in convs:
            f.write(json.dumps(c) + "\n")

    # Probes: history up to and including turn t, plus the probe question, on a copy.
    jobs = [(c, t) for c in convs for t in args.probe_turns]
    if jobs:
        histories = [c["messages"][:2 * t] + [{"role": "user", "content": prompts["probe"]}] for c, t in jobs]
        replies = gen.reply(histories)
        with open(args.out / "probes.jsonl", "w") as f:
            for (c, t), r in zip(jobs, replies):
                f.write(json.dumps({
                    "id": f"{c['id']}/probe{t}", "conversation_id": c["id"], "stage": stage,
                    "seed": c["seed"], "condition": c["condition"], "sample": c["sample"], "turn": t,
                    "question": prompts["probe"], "reply": r["text"],
                    "finish_reason": r["finish_reason"], "n_tokens": r["n_tokens"],
                }) + "\n")

    logger.info("wrote %d conversations, %d probes to %s in %.0fs",
                len(convs), len(jobs), args.out, time.time() - t0)


if __name__ == "__main__":
    main()
