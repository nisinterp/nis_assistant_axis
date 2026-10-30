"""Unit tests for the judge code: parsing, retries, rate limits, blinding, batches. No network needed.

Run from the project root:
    python -m unittest discover -s judge/tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import judge  # noqa: E402
from openrouter import OpenRouterClient, RateLimitExhausted  # noqa: E402

GOOD = '{"score": 1, "reason": "Mostly an assistant with some warmth."}'


class TestParser(unittest.TestCase):
    """parse_judgment accepts valid JSON and rejects every kind of broken output."""
    def test_valid(self):
        self.assertEqual(judge.parse_judgment(GOOD)["score"], 1)

    def test_code_fence(self):
        self.assertEqual(judge.parse_judgment("```json\n" + GOOD + "\n```")["score"], 1)

    def test_rejects_broken(self):
        for bad in ["I'd say 2", "", "   ", "2", '{"score": 5, "reason": "x"}',
                    '{"score": -1, "reason": "x"}', '{"score": "two", "reason": "x"}',
                    '{"score": 2.5, "reason": "x"}', '{"score": true, "reason": "x"}',
                    '{"score": 2}', '{"score": 2, "reason": ""}', '[2]', '{"score": 2, "reason": "x"'
                    ]:
            with self.subTest(bad=bad), self.assertRaises(judge.JudgeOutputError):
                judge.parse_judgment(bad)

    def test_number_in_reason_is_not_the_score(self):
        # The paper's regex parser would read "3" here.
        r = judge.parse_judgment('{"reason": "Uses 3 metaphors but stays an AI.", "score": 1}')
        self.assertEqual(r["score"], 1)


class TestRetry(unittest.TestCase):
    """judge_one retries bad outputs and gives up cleanly."""
    def fake(self, outputs):
        """Fake backend that returns `outputs` in order; also returns the list of prompts it received."""
        outputs = list(outputs)
        calls = []

        def call(prompt):
            """Record the prompt and return the next scripted output."""
            calls.append(prompt)
            return outputs.pop(0)
        return call, calls

    def test_bad_then_good(self):
        call, calls = self.fake(["not json", '{"score": 9, "reason": "x"}', GOOD])
        rec = judge.judge_one(call, "p", max_attempts=3)
        self.assertEqual((rec["score"], rec["attempts"], rec["error"]), (1, 3, None))
        self.assertEqual(len(calls), 3)

    def test_gives_up_without_crashing(self):
        call, _ = self.fake(["nope"] * 3)
        rec = judge.judge_one(call, "p", max_attempts=3)
        self.assertIsNone(rec["score"])
        self.assertIn("unparseable", rec["error"])
        self.assertEqual(rec["raw"], ["nope"] * 3)

    def test_inject_bad_wrapper(self):
        call = judge.inject_bad_outputs(lambda p: GOOD, 2)
        rec = judge.judge_one(call, "p", max_attempts=3)
        self.assertEqual((rec["score"], rec["attempts"]), (1, 3))


class FakeResp:
    """Minimal stand-in for a requests.Response."""
    def __init__(self, status, body=None, headers=None):
        """Store status code, JSON body and headers."""
        self.status_code, self._body, self.headers = status, body or {}, headers or {}
        self.text = json.dumps(self._body)

    def json(self):
        """Return the JSON body."""
        return self._body

    def raise_for_status(self):
        """Raise for 4xx/5xx status codes, like requests does."""
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    """Stand-in for requests.Session that returns scripted responses in order."""
    def __init__(self, responses):
        """Store the scripted responses."""
        self.responses, self.posts = list(responses), 0

    def post(self, *a, **kw):
        """Return the next scripted response."""
        self.posts += 1
        return self.responses.pop(0)


def ok(text):
    """HTTP 200 response whose reply text is `text`."""
    return FakeResp(200, {"choices": [{"message": {"content": text}}]})


class TestRateLimit(unittest.TestCase):
    """OpenRouterClient waits and retries on rate limits and stops after max_retries."""
    def client(self, responses, **kw):
        """Client wired to a fake session; recorded sleeps go to self.sleeps."""
        self.sleeps = []
        return OpenRouterClient("m:free", api_key="k", session=FakeSession(responses),
                                sleep=self.sleeps.append, **kw)

    def test_429_waits_and_retries(self):
        c = self.client([FakeResp(429), FakeResp(429, headers={"Retry-After": "7"}), ok(GOOD)])
        self.assertEqual(c.chat([]), GOOD)
        self.assertEqual(self.sleeps, [2.0, 7.0])  # backoff, then Retry-After

    def test_rate_limit_inside_200_body(self):
        c = self.client([FakeResp(200, {"error": {"code": 429, "message": "slow down"}}), ok(GOOD)])
        self.assertEqual(c.chat([]), GOOD)
        self.assertEqual(len(self.sleeps), 1)

    def test_gives_up_after_max_retries(self):
        c = self.client([FakeResp(429)] * 3, max_retries=2)
        with self.assertRaises(RateLimitExhausted):
            c.chat([])
        self.assertEqual(len(self.sleeps), 2)

    def test_non_retryable_error_raises(self):
        c = self.client([FakeResp(401)])
        with self.assertRaises(RuntimeError):
            c.chat([])
        self.assertEqual(self.sleeps, [])


class TestBlinding(unittest.TestCase):
    """Only question and reply reach the judge; shuffling is seeded."""
    def test_extra_fields_never_reach_the_judge(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            inp = d / "in.jsonl"
            inp.write_text(json.dumps({"id": "a1", "question": "How are you?", "reply": "I'm an AI.",
                                       "condition": "TRIGGER_EMOTIONAL", "turn": 17, "seed": "csv"}) + "\n")
            items = judge.load_items(inp)
            self.assertEqual(set(items[0]), {"id", "question", "reply"})

            sent = []
            judge.run(items, lambda p: sent.append(p) or GOOD, judge.load_rubric(),
                      d / "out.jsonl", d / "prompts.jsonl", "fake", "fake")
            logged = json.loads((d / "prompts.jsonl").read_text().splitlines()[0])["prompt"]
            self.assertEqual(logged, sent[0])
            for leak in ["TRIGGER_EMOTIONAL", "condition", "17", "csv", "a1"]:
                self.assertNotIn(leak, sent[0])

    def test_shuffle_is_seeded_and_changes_order(self):
        items = [{"id": str(i), "question": "q", "reply": "r"} for i in range(20)]
        with tempfile.TemporaryDirectory() as d:
            orders = []
            for run_no in range(2):
                seen = []
                out = Path(d) / f"o{run_no}.jsonl"
                judge.run(items, lambda p: GOOD, judge.load_rubric(), out, Path(d) / "p.jsonl",
                          "fake", "fake", seed=3)
                orders.append([json.loads(l)["id"] for l in out.read_text().splitlines()])
            self.assertEqual(orders[0], orders[1])
            self.assertNotEqual(orders[0], [str(i) for i in range(20)])


class TestRunOutput(unittest.TestCase):
    """run() writes one row per item and resumes only the unscored ones."""
    def test_writes_every_item_and_resumes(self):
        items = [{"id": f"r{i}", "question": "q", "reply": "r"} for i in range(4)]
        with tempfile.TemporaryDirectory() as d:
            out, plog = Path(d) / "out.jsonl", Path(d) / "p.jsonl"
            outputs = iter(["bad"] * 3 + [GOOD] * 3)  # first item fails all 3 attempts
            judge.run(items, lambda p: next(outputs), judge.load_rubric(), out, plog, "fake", "fake")
            rows = [json.loads(l) for l in out.read_text().splitlines()]
            self.assertEqual(len(rows), 4)
            self.assertEqual(sum(r["score"] is None for r in rows), 1)
            for r in rows:
                self.assertTrue({"id", "score", "reason", "raw", "attempts", "error", "backend", "model"} <= r.keys())

            # Resume: only the failed item is redone, and its stale row is replaced.
            calls = []
            judge.run(items, lambda p: calls.append(p) or GOOD, judge.load_rubric(), out, plog, "fake", "fake")
            rows = [json.loads(l) for l in out.read_text().splitlines()]
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(rows), 4)
            self.assertTrue(all(r["score"] is not None for r in rows))


class TestRubric(unittest.TestCase):
    """The rubric template is filled correctly."""
    def test_rubric_fills_and_keeps_json_braces(self):
        prompt = judge.build_prompt(judge.load_rubric(), "Q?", "A {weird} answer")
        self.assertIn("Q?", prompt)
        self.assertIn("A {weird} answer", prompt)
        self.assertIn('{"score": <integer 0-3>', prompt)
        self.assertNotIn("{question}", prompt)


# ------------------------------------------------------------ batch backend

from types import SimpleNamespace as NS  # noqa: E402


def ok_result(i, text, stop="end_turn"):
    """Fake successful batch result with a thinking block followed by `text`."""
    msg = NS(stop_reason=stop, content=[NS(type="thinking"), NS(type="text", text=text)])
    return NS(custom_id=i, result=NS(type="succeeded", message=msg))


class FakeBatches:
    """Each create() call returns the next scripted list of results."""
    def __init__(self, rounds):
        """Store the scripted result rounds, one per create() call."""
        self.rounds, self.created, self.retrieves = list(rounds), [], 0

    def create(self, requests):
        """Record the submitted requests and switch to the next scripted round."""
        self.created.append(requests)
        self.current = self.rounds.pop(0)
        return NS(id=f"b{len(self.created)}", processing_status="in_progress")

    def retrieve(self, batch_id):
        """Report the batch as finished."""
        self.retrieves += 1
        return NS(id=batch_id, processing_status="ended",
                  request_counts=NS(processing=0, succeeded=0, errored=0))

    def results(self, batch_id):
        """Return the current round's results in reverse order."""
        return list(reversed(self.current))  # any order


def fake_client(rounds):
    """Fake Anthropic client exposing messages.batches; returns (client, batches)."""
    b = FakeBatches(rounds)
    return NS(messages=NS(batches=b)), b


class TestBatch(unittest.TestCase):
    """Message Batch backend: request shape, resubmitting failures, giving up, writing rows."""
    def test_request_shape(self):
        params = judge.anthropic_params("claude-haiku-5-5", "PROMPT")
        self.assertEqual(params["messages"], [{"role": "user", "content": "PROMPT"}])
        self.assertEqual(params["output_config"]["format"]["schema"]["properties"]["score"]["enum"], [0, 1, 2, 3])
        self.assertNotIn("temperature", params)  # non-default sampling is rejected on Haiku 5.5

    def test_failures_are_resubmitted_alone(self):
        errored = NS(custom_id="b", result=NS(type="errored", error=NS(error=NS(type="overloaded_error"))))
        client, batches = fake_client([
            [ok_result("a", GOOD), errored, ok_result("c", "not json"), ok_result("d", GOOD, stop="max_tokens")],
            [ok_result("b", GOOD), ok_result("c", '{"score": 3, "reason": "Plays a spirit."}'),
             ok_result("d", GOOD)],
        ])
        recs = judge.judge_batch(client, "m", {i: "p" for i in "abcd"}, sleep=lambda s: None)
        self.assertEqual({i: r["score"] for i, r in recs.items()}, {"a": 1, "b": 1, "c": 3, "d": 1})
        self.assertEqual(sorted(r["custom_id"] for r in batches.created[1]), ["b", "c", "d"])
        self.assertEqual((recs["a"]["attempts"], recs["c"]["attempts"]), (1, 2))

    def test_gives_up_after_max_attempts(self):
        client, _ = fake_client([[ok_result("a", "nope")]] * 2)
        recs = judge.judge_batch(client, "m", {"a": "p"}, max_attempts=2, sleep=lambda s: None)
        self.assertIsNone(recs["a"]["score"])
        self.assertIn("no valid judgment", recs["a"]["error"])

    def test_run_batch_writes_rows(self):
        items = [{"id": f"r{i}", "question": "q", "reply": "r"} for i in range(3)]
        client, _ = fake_client([[ok_result(f"r{i}", GOOD) for i in range(3)]])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.jsonl"
            judge.run_batch(items, client, judge.load_rubric(), out, Path(d) / "p.jsonl", "m",
                            sleep=lambda s: None)
            rows = [json.loads(l) for l in out.read_text().splitlines()]
            self.assertEqual(sorted(r["id"] for r in rows), ["r0", "r1", "r2"])
            self.assertTrue(all(r["backend"] == "anthropic" and r["score"] == 1 for r in rows))


if __name__ == "__main__":
    unittest.main()
