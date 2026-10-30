"""Minimal OpenRouter chat client with rate-limit handling.

Used by the judge's free debug backend.
"""

import logging
import os
import time

import requests

API_URL = "https://openrouter.ai/api/v1"
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

logger = logging.getLogger(__name__)


class RateLimitExhausted(RuntimeError):
    """Raised when a request still fails after all rate-limit retries."""


def _retry_after(resp):
    """Seconds from a Retry-After header, or None."""
    value = resp.headers.get("Retry-After") if resp is not None else None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


class OpenRouterClient:
    """Chat client for OpenRouter that waits and retries on rate limits and transient errors."""
    def __init__(self, model, api_key=None, session=None, sleep=time.sleep,
                 max_retries=6, base_wait=2.0, max_wait=120.0, timeout=120):
        """Set the model, API key (default: $OPENROUTER_API_KEY) and retry/backoff settings."""
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")
        self.session = session or requests.Session()
        self.sleep = sleep
        self.max_retries = max_retries
        self.base_wait = base_wait
        self.max_wait = max_wait
        self.timeout = timeout

    def _wait(self, attempt, resp, why):
        """Sleep before a retry: the Retry-After header if given, else exponential backoff, capped at max_wait."""
        wait = _retry_after(resp)
        if wait is None:
            wait = self.base_wait * 2 ** attempt
        wait = min(wait, self.max_wait)
        logger.warning("%s; waiting %.1fs before retry %d/%d", why, wait, attempt + 1, self.max_retries)
        self.sleep(wait)

    def chat(self, messages, temperature=0.0, max_tokens=400):
        """Send one chat request and return the reply text ("" if the model sent nothing)."""
        payload = {"model": self.model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(self.max_retries + 1):
            last_try = attempt == self.max_retries
            try:
                resp = self.session.post(f"{API_URL}/chat/completions", json=payload,
                                         headers=headers, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as e:
                if last_try:
                    raise
                self._wait(attempt, None, f"network error ({e.__class__.__name__})")
                continue

            if resp.status_code in RETRYABLE_STATUS:
                if last_try:
                    break
                self._wait(attempt, resp, f"HTTP {resp.status_code}: {resp.text[:300]}")
                continue
            resp.raise_for_status()

            data = resp.json()
            # OpenRouter sometimes reports upstream errors (incl. rate limits) inside a 200 body.
            if "error" in data:
                code = data["error"].get("code")
                if code in RETRYABLE_STATUS and not last_try:
                    self._wait(attempt, resp, f"upstream error {code}: {data['error'].get('message')}")
                    continue
                raise RuntimeError(f"OpenRouter error: {data['error']}")

            return data["choices"][0]["message"].get("content") or ""

        raise RateLimitExhausted(f"gave up after {self.max_retries} retries")


def list_free_models(session=None):
    """IDs of OpenRouter models whose id ends in ':free'. Needs no API key."""
    resp = (session or requests).get(f"{API_URL}/models", timeout=30)
    resp.raise_for_status()
    return sorted(m["id"] for m in resp.json()["data"] if m["id"].endswith(":free"))
