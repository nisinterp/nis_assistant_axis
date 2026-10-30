#!/usr/bin/env python3
"""Score probe replies 0-3 with an LLM judge.

Input JSONL rows need `id`, `question`, `reply`. Only `question` and `reply`
reach the judge; every other field (condition, turn, ...) is dropped.

Usage:
    python judge/judge.py --list-free
    python judge/judge.py --judge-backend openrouter --model <id>:free \
        --in results/pilots/pilot2/judge_in.jsonl --out /tmp/scores_openrouter.jsonl
    python judge/judge.py --judge-backend anthropic --model claude-haiku-5-5 \
        --in results/main_experiment/judge_in.jsonl --out results/main_experiment/judge_scores.jsonl
"""

import argparse
import json
import logging
import random
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
DEFAULT_RUBRIC = Path(__file__).resolve().parent / "rubric.txt"

logger = logging.getLogger("judge")


class JudgeOutputError(ValueError):
    """The judge's reply is not a valid {"score": 0-3, "reason": str} object."""


# ---------------------------------------------------------------- shared core

def load_rubric(path=DEFAULT_RUBRIC):
    """Read the rubric template and check it has exactly one {question} and one {answer} placeholder."""
    text = Path(path).read_text()
    for placeholder in ("{question}", "{answer}"):
        if text.count(placeholder) != 1:
            raise ValueError(f"rubric must contain {placeholder} exactly once")
    return text


def build_prompt(rubric, question, answer):
    # str.replace, not str.format: the rubric contains literal JSON braces.
    """Fill the rubric template with the probe question and the model's answer."""
    return rubric.replace("{question}", question).replace("{answer}", answer)


def parse_judgment(text):
    """Return {"score", "reason"} or raise JudgeOutputError."""
    if not text or not text.strip():
        raise JudgeOutputError("empty output")
    s = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", s, re.DOTALL)
    if fence:
        s = fence.group(1)
    try:
        obj = json.loads(s)
    except json.JSONDecodeError as e:
        raise JudgeOutputError(f"not JSON: {e}") from None
    if not isinstance(obj, dict):
        raise JudgeOutputError("JSON is not an object")
    score = obj.get("score")
    if isinstance(score, bool) or not isinstance(score, int):
        raise JudgeOutputError(f"score is not an integer: {score!r}")
    if not 0 <= score <= 3:
        raise JudgeOutputError(f"score out of range: {score}")
    reason = obj.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise JudgeOutputError("missing reason")
    return {"score": score, "reason": reason.strip()}


def load_items(path):
    """Read input rows, keeping only the fields the judge may see."""
    items = []
    with open(path) as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            missing = {"id", "question", "reply"} - row.keys()
            if missing:
                raise ValueError(f"{path}:{n} missing fields {sorted(missing)}")
            items.append({"id": row["id"], "question": row["question"], "reply": row["reply"]})
    ids = [it["id"] for it in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path} has duplicate ids")
    return items


def judge_one(call, prompt, max_attempts=3):
    """Ask the judge until it returns a valid answer, at most max_attempts times.

    `call(prompt) -> str` is the backend. Never raises on bad output: after the
    last failed attempt the record has score None and an error message.
    """
    raws = []
    for attempt in range(1, max_attempts + 1):
        raw = call(prompt)
        raws.append(raw)
        try:
            result = parse_judgment(raw)
            return {**result, "raw": raw, "attempts": attempt, "error": None}
        except JudgeOutputError as e:
            logger.warning("unparseable judge output (attempt %d/%d): %s | %r",
                           attempt, max_attempts, e, (raw or "")[:200])
            error = str(e)
    return {"score": None, "reason": None, "raw": raws, "attempts": max_attempts,
            "error": f"unparseable after {max_attempts} attempts: {error}"}


def already_done(out_path):
    """IDs with a valid score in out_path, for resuming. Drops unscored rows so they are retried."""
    path = Path(out_path)
    if not path.exists():
        return set()
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    kept = [r for r in rows if r.get("score") is not None]
    if len(kept) != len(rows):
        path.write_text("".join(json.dumps(r) + "\n" for r in kept))
    return {r["id"] for r in kept}


def run(items, call, rubric, out_path, prompts_path, backend, model,
        seed=0, max_attempts=3):
    """Judge items one at a time with call(prompt) (OpenRouter backend), resuming from out_path; returns out_path."""
    items = list(items)
    random.Random(seed).shuffle(items)
    done = already_done(out_path)
    todo = [it for it in items if it["id"] not in done]
    logger.info("%d items, %d already scored, %d to do", len(items), len(done), len(todo))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "a") as out, open(prompts_path, "a") as plog:
        for i, it in enumerate(todo, 1):
            prompt = build_prompt(rubric, it["question"], it["reply"])
            plog.write(json.dumps({"id": it["id"], "prompt": prompt}) + "\n")
            plog.flush()
            rec = judge_one(call, prompt, max_attempts)
            out.write(json.dumps({"id": it["id"], **rec, "backend": backend, "model": model}) + "\n")
            out.flush()
            logger.info("[%d/%d] %s -> %s", i, len(todo), it["id"], rec["score"])
    return out_path


# ------------------------------------------------------------------- backends

def openrouter_call(model):
    """Backend function prompt -> reply text for a free OpenRouter model (temperature 0)."""
    from openrouter import OpenRouterClient
    client = OpenRouterClient(model)
    return lambda prompt: client.chat([{"role": "user", "content": prompt}],
                                      temperature=0.0, max_tokens=2000)


# Structured outputs: the API only returns JSON matching this schema.
JUDGMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "enum": [0, 1, 2, 3]},
        "reason": {"type": "string"},
    },
    "required": ["score", "reason"],
    "additionalProperties": False,
}


def anthropic_params(model, prompt):
    """Message request parameters for one judge prompt, with JSON output enforced by a schema."""
    return {
        "model": model,
        # Haiku 5.5 thinks by default, and thinking counts toward max_tokens.
        "max_tokens": 4000,
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": JUDGMENT_SCHEMA}},
        "messages": [{"role": "user", "content": prompt}],
    }


def batch_result_text(result):
    """Reply text of one batch result; raises JudgeOutputError if the request did not finish normally."""
    r = result.result
    if r.type != "succeeded":
        detail = getattr(getattr(r, "error", None), "error", None) or getattr(r, "error", None)
        raise JudgeOutputError(f"batch request {r.type}: {detail}")
    msg = r.message
    if msg.stop_reason != "end_turn":
        raise JudgeOutputError(f"stop_reason {msg.stop_reason}")
    return next((b.text for b in msg.content if b.type == "text"), "")


def judge_batch(client, model, prompts, max_attempts=3, poll_seconds=15, sleep=time.sleep):
    """Judge {id: prompt} with Message Batches. Items that fail are resubmitted in a new batch.

    Returns {id: record} with the same fields as judge_one.
    """
    raws = {i: [] for i in prompts}
    records, pending = {}, list(prompts)
    for attempt in range(1, max_attempts + 1):
        if not pending:
            break
        batch = client.messages.batches.create(requests=[
            {"custom_id": i, "params": anthropic_params(model, prompts[i])} for i in pending])
        logger.info("batch %s submitted (%d requests, attempt %d/%d)", batch.id, len(pending), attempt, max_attempts)
        while batch.processing_status != "ended":
            sleep(poll_seconds)
            batch = client.messages.batches.retrieve(batch.id)
            c = batch.request_counts
            logger.info("batch %s: %s (processing %d, succeeded %d, errored %d)",
                        batch.id, batch.processing_status, c.processing, c.succeeded, c.errored)

        failed = []
        # Results come back in any order: key them by custom_id.
        for result in client.messages.batches.results(batch.id):
            i = result.custom_id
            try:
                raw = batch_result_text(result)
                raws[i].append(raw)
                records[i] = {**parse_judgment(raw), "raw": raw, "attempts": attempt, "error": None}
            except JudgeOutputError as e:
                if not raws[i] or raws[i][-1] != str(e):
                    raws[i].append(str(e))
                logger.warning("%s failed (attempt %d/%d): %s", i, attempt, max_attempts, e)
                failed.append(i)
        missing = set(pending) - set(records) - set(failed)
        pending = failed + sorted(missing)

    for i in pending:
        records[i] = {"score": None, "reason": None, "raw": raws[i], "attempts": max_attempts,
                      "error": f"no valid judgment after {max_attempts} attempts: {raws[i][-1] if raws[i] else 'no result'}"}
    return records


def run_batch(items, client, rubric, out_path, prompts_path, model, seed=0, max_attempts=3, **kw):
    """Batch counterpart of run(): same shuffling, resuming, prompt log and output rows."""
    items = list(items)
    random.Random(seed).shuffle(items)
    done = already_done(out_path)
    todo = [it for it in items if it["id"] not in done]
    logger.info("%d items, %d already scored, %d to do", len(items), len(done), len(todo))
    if not todo:
        return out_path

    prompts = {it["id"]: build_prompt(rubric, it["question"], it["reply"]) for it in todo}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(prompts_path, "a") as plog:
        for i, p in prompts.items():
            plog.write(json.dumps({"id": i, "prompt": p}) + "\n")

    records = judge_batch(client, model, prompts, max_attempts, **kw)
    with open(out_path, "a") as out:
        for i in prompts:  # shuffled order
            out.write(json.dumps({"id": i, **records[i], "backend": "anthropic", "model": model}) + "\n")
    return out_path


def inject_bad_outputs(call, n):
    """Debug wrapper: the first n calls return broken text, to exercise the retry path."""
    bad = ["I would give this a 2.", '{"score": 7, "reason": "x"}', "", '{"score": "two"}']
    state = {"left": n}

    def wrapped(prompt):
        """Return the next broken output while any are left, otherwise call the real backend."""
        if state["left"] > 0:
            state["left"] -= 1
            out = bad[(n - state["left"] - 1) % len(bad)]
            logger.info("injecting bad output: %r", out)
            return out
        return call(prompt)
    return wrapped


# ------------------------------------------------------------------------ CLI

def main(argv=None):
    """Command line: pick a backend, judge every input row, and print how many were left unscored."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--judge-backend", choices=["openrouter", "anthropic"])
    p.add_argument("--model", help="judge model id (OpenRouter: a ':free' model)")
    p.add_argument("--in", dest="inp", help="input JSONL with id, question, reply (e.g. a run's judge_in.jsonl)")
    p.add_argument("--out", help="output JSONL of scores")
    p.add_argument("--prompts-out", help="log of prompts exactly as sent (default: <out>.prompts.jsonl)")
    p.add_argument("--rubric", default=DEFAULT_RUBRIC)
    p.add_argument("--seed", type=int, default=0, help="shuffle seed")
    p.add_argument("--max-attempts", type=int, default=3)
    p.add_argument("--limit", type=int, help="judge only the first N items (after shuffling)")
    p.add_argument("--inject-bad", type=int, default=0, metavar="N",
                   help="debug: make the first N judge calls return broken output")
    p.add_argument("--list-free", action="store_true", help="list free OpenRouter models and exit")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    if args.list_free:
        from openrouter import list_free_models
        print("\n".join(list_free_models()))
        return 0
    if not args.judge_backend or not args.model or not args.inp or not args.out:
        p.error("--judge-backend, --model, --in and --out are required")

    out = Path(args.out)
    prompts_out = Path(args.prompts_out or out.with_suffix(".prompts.jsonl"))
    items = load_items(args.inp)
    if args.limit:
        rng_items = list(items)
        random.Random(args.seed).shuffle(rng_items)
        items = rng_items[:args.limit]

    if args.judge_backend == "anthropic":
        if args.inject_bad:
            p.error("--inject-bad works only with the openrouter backend")
        import anthropic
        run_batch(items, anthropic.Anthropic(), load_rubric(args.rubric), out, prompts_out,
                  args.model, args.seed, args.max_attempts)
    else:
        call = openrouter_call(args.model)
        if args.inject_bad:
            call = inject_bad_outputs(call, args.inject_bad)
        run(items, call, load_rubric(args.rubric), out, prompts_out,
            args.judge_backend, args.model, args.seed, args.max_attempts)

    rows = [json.loads(l) for l in open(out) if l.strip()]
    failed = [r["id"] for r in rows if r["score"] is None]
    print(f"wrote {out} ({len(rows)} rows, {len(failed)} unscored{': ' + ', '.join(failed) if failed else ''})")
    print(f"prompts as sent: {prompts_out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
