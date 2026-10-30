#!/usr/bin/env python3
"""Project every assistant reply of finished conversations onto the Assistant Axis.

Model: Qwen3-32B-AWQ. Axis: the authors' released Assistant Axis, at the paper's layer for
Qwen 3 32B (32). Each reply's activations are averaged over its tokens, then projected.
Writes one row per (conversation, turn) to projections.jsonl next to the input.

With --probes, also projects each probe reply (from probes.jsonl): the probe's history is
the conversation up to its turn + the probe question, so its reply is projected in that
context. To avoid re-reading long histories, each conversation is run once with its KV
cache kept; each probe reuses the cached common prefix and only runs its own new tokens
(probes in order of decreasing prefix, cropping the cache back after each). Rows go to
probe_projections.jsonl. --verify-probes N recomputes N probes without the cache and logs
the difference.

Usage (after vLLM has exited, so the GPU is free):
    python experiment/project.py --repo /workspace/assistant-axis --run results/pilots/pilot2 [--probes]
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compat  # noqa: E402,F401  (must patch transformers before the model loads)
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from huggingface_hub import hf_hub_download  # noqa: E402

logger = logging.getLogger("project")

AWQ_MODEL = "Qwen/Qwen3-32B-AWQ"
CONFIG_MODEL = "Qwen/Qwen3-32B"  # the paper repo's layer config is keyed on the full-precision name
AXIS_REPO = "lu-christina/assistant-axis-vectors"
AXIS_FILE = "qwen-3-32b/assistant_axis.pt"
CHAT_KWARGS = {"enable_thinking": False}
EXTRA_FIELDS = ("family", "k", "sample")  # copied into each row when present


def capture(pm, layer):
    """Register a hook that stores the layer's output activations; returns (store, handle)."""
    store = {}

    def hook(module, inputs, output):
        """Forward hook: keep the layer's output activations (first batch item) on the CPU."""
        act = output[0] if isinstance(output, tuple) else output
        store["acts"] = act[0].float().cpu()

    return store, pm.get_layers()[layer].register_forward_hook(hook)


def turn_projections(pm, encoder, conversation, axis_vec, layer):
    """Projection of each assistant reply in one forward pass, without any KV cache.

    Runs the base model without the LM head, so long conversations do not also materialise
    full-vocab logits. Returns (projections, number of tokens). Used by --verify-probes.
    """
    ids, spans = encoder.build_turn_spans(conversation, **CHAT_KWARGS)
    store, handle = capture(pm, layer)
    try:
        with torch.inference_mode():
            pm.model.model(torch.tensor([ids], device=pm.model.device), use_cache=False)
    finally:
        handle.remove()
    acts = store["acts"]
    return [float(acts[s["start"]:s["end"]].mean(dim=0) @ axis_vec)
            for s in spans if s["role"] == "assistant"], len(ids)


def common_prefix(a, b):
    """Number of leading tokens two id lists share."""
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def conversation_with_probes(pm, encoder, messages, probes, axis_vec, layer):
    """Per-turn projections of the conversation, and the projection of each probe reply."""
    ids, spans = encoder.build_turn_spans(messages, **CHAT_KWARGS)
    store, handle = capture(pm, layer)
    try:
        with torch.inference_mode():
            out = pm.model.model(torch.tensor([ids], device=pm.model.device), use_cache=bool(probes))
            acts = store["acts"]
            turns = [float(acts[s["start"]:s["end"]].mean(dim=0) @ axis_vec)
                     for s in spans if s["role"] == "assistant"]
            cache = out.past_key_values if probes else None
            del out

            jobs = []
            for p in probes:
                hist = messages[:2 * p["turn"]] + [{"role": "user", "content": p["question"]},
                                                   {"role": "assistant", "content": p["reply"]}]
                p_ids, p_spans = encoder.build_turn_spans(hist, **CHAT_KWARGS)
                span = [s for s in p_spans if s["role"] == "assistant"][-1]
                keep = min(common_prefix(ids, p_ids), span["start"], len(ids))
                jobs.append((keep, p, p_ids, span))
            results = {}
            for keep, p, p_ids, span in sorted(jobs, key=lambda j: -j[0]):
                cache.crop(keep)
                pm.model.model(torch.tensor([p_ids[keep:]], device=pm.model.device),
                               past_key_values=cache, use_cache=True)
                a = store["acts"]
                results[p["id"]] = float(a[span["start"] - keep:span["end"] - keep].mean(dim=0) @ axis_vec)
                cache.crop(keep)
    finally:
        handle.remove()
    return turns, results, len(ids)


def main():
    """Load the axis and the model, then project every conversation (and optionally its probes) and write JSONL."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True, help="clone of safety-research/assistant-axis")
    parser.add_argument("--run", type=Path, required=True, help="dir with conversations.jsonl")
    parser.add_argument("--model", default=AWQ_MODEL)
    parser.add_argument("--probes", action="store_true", help="also project probe replies from probes.jsonl")
    parser.add_argument("--verify-probes", type=int, default=0, metavar="N",
                        help="recompute the first N probes without the cache and log the difference")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    sys.path.insert(0, str(args.repo))
    from assistant_axis import get_config, load_axis
    from assistant_axis.internals import ConversationEncoder, ProbingModel

    layer = get_config(CONFIG_MODEL)["target_layer"]
    axis = load_axis(hf_hub_download(repo_id=AXIS_REPO, filename=AXIS_FILE, repo_type="dataset"))
    axis_vec = F.normalize(axis[layer].float(), dim=0)
    pm = ProbingModel(args.model, dtype=torch.float16)
    encoder = ConversationEncoder(pm.tokenizer, CONFIG_MODEL)

    convs = [json.loads(line) for line in open(args.run / "conversations.jsonl")]
    probes_by_conv = defaultdict(list)
    if args.probes:
        for line in open(args.run / "probes.jsonl"):
            p = json.loads(line)
            probes_by_conv[p["conversation_id"]].append(p)
    verified = 0

    with open(args.run / "projections.jsonl", "w") as f, \
            open(args.run / "probe_projections.jsonl", "w") if args.probes else open("/dev/null", "w") as fp:
        for c in convs:
            probes = probes_by_conv.get(c["id"], [])
            projections, probe_vals, n_tokens = conversation_with_probes(
                pm, encoder, c["messages"], probes, axis_vec, layer)
            if len(projections) != len(c["turns"]):
                raise RuntimeError(f"{c['id']}: {len(projections)} projections for {len(c['turns'])} turns")
            extra = {k: c[k] for k in EXTRA_FIELDS if k in c}
            for t, p in zip(c["turns"], projections):
                f.write(json.dumps({
                    "conversation_id": c["id"], "stage": c["stage"], "seed": c["seed"],
                    "condition": c["condition"], **extra, "turn": t["turn"], "is_slot": t.get("is_slot"),
                    **({"is_block": t["is_block"], "rel": t["rel"]} if "rel" in t else {}),
                    "projection": p, "layer": layer,
                }) + "\n")
            for p in probes:
                fp.write(json.dumps({
                    "id": p["id"], "conversation_id": c["id"], "seed": c["seed"], "condition": c["condition"],
                    **extra, "point": p.get("point"), "turn": p["turn"], "rel": p.get("rel"),
                    "projection": probe_vals[p["id"]], "layer": layer,
                }) + "\n")
                if verified < args.verify_probes:
                    hist = c["messages"][:2 * p["turn"]] + [{"role": "user", "content": p["question"]},
                                                            {"role": "assistant", "content": p["reply"]}]
                    direct = turn_projections(pm, encoder, hist, axis_vec, layer)[0][-1]
                    logger.info("verify %s: cached %.3f, direct %.3f, diff %.3f",
                                p["id"], probe_vals[p["id"]], direct, probe_vals[p["id"]] - direct)
                    verified += 1
            probe_txt = " ".join("%.1f" % probe_vals[p["id"]] for p in probes)
            logger.info("%s: %d tokens, %s%s", c["id"], n_tokens, " ".join(f"{p:.1f}" for p in projections),
                        f" | probes {probe_txt}" if probes else "")
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
