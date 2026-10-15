"""Logged, cached, cost-counted Claude client handed to candidate pipelines.

Candidates only get `LLM.ask(...)`; they never see file paths or labels.
Every response is cached on disk by a hash of (model, effort, system, prompt,
image bytes, sample index), so re-scoring a candidate costs nothing.
"""
import base64, hashlib, json, os, threading, time

import anthropic

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE = os.path.join(ROOT, "runs", "cache")

# $ per 1M tokens (input, output); cache reads billed at input rate here (upper bound)
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    # OpenAI GPT-6 generation (developers.openai.com/api/docs/pricing, checked 2026-10-16)
    "gpt-6-luna": (0.10, 0.50),
    "gpt-6.1-sol": (2.00, 10.00),
    "gpt-6-astra": (10.00, 50.00),
}
OPENAI_EFFORT = {"low": "low", "medium": "medium", "high": "high", "xhigh": "high", "max": "high"}


def _load_key():
    env = os.environ.get("FE_ENV_FILE", os.path.join(ROOT, "..", "dragonclaw", ".env"))
    for line in open(env):
        for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            if line.startswith(k + "=") and not os.environ.get(k):
                os.environ[k] = line.split("=", 1)[1].strip().strip('"')


class Budget(Exception):
    pass


class LLM:
    def __init__(self, max_usd=None):
        _load_key()
        self.client = anthropic.Anthropic(max_retries=6)
        self._oa = None
        self.lock = threading.Lock()
        self.usd = 0.0
        self.calls = 0
        self.cached = 0
        self.max_usd = max_usd
        os.makedirs(CACHE, exist_ok=True)

    def ask(self, prompt, image=None, model="claude-sonnet-5-5", effort="low",
            system=None, max_tokens=4000, sample=0):
        """Return the model's text answer. `image` is PNG bytes or None."""
        if model not in PRICES:
            raise ValueError(f"model not allowed: {model}")
        h = hashlib.sha256()
        for part in (model, effort, system or "", prompt, str(sample)):
            h.update(part.encode())
            h.update(b"\0")
        if image is not None:
            h.update(hashlib.sha256(image).digest())
        key = h.hexdigest()
        path = os.path.join(CACHE, key[:2], key + ".json")
        if os.path.exists(path):
            with self.lock:
                self.cached += 1
            return json.load(open(path))["text"]
        with self.lock:
            if self.max_usd is not None and self.usd >= self.max_usd:
                raise Budget(f"budget {self.max_usd} reached")
        if model.startswith("gpt-"):
            text, cost = self._ask_openai(model, prompt, image, effort, system, max_tokens)
            with self.lock:
                self.usd += cost
                self.calls += 1
            os.makedirs(os.path.dirname(path), exist_ok=True)
            json.dump({"text": text, "model": model, "cost": cost, "t": time.time()}, open(path, "w"))
            return text
        content = []
        if image is not None:
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                        "data": base64.standard_b64encode(image).decode()}})
        content.append({"type": "text", "text": prompt})
        kw = dict(model=model, max_tokens=max_tokens, output_config={"effort": effort},
                  messages=[{"role": "user", "content": content}])
        if system:
            kw["system"] = system
        resp = self.client.messages.create(**kw)
        if resp.stop_reason == "refusal":
            text = ""
        else:
            text = "".join(b.text for b in resp.content if b.type == "text")
        pin, pout = PRICES[model]
        u = resp.usage
        cost = ((u.input_tokens + (u.cache_read_input_tokens or 0) + (u.cache_creation_input_tokens or 0)) * pin
                + u.output_tokens * pout) / 1e6
        with self.lock:
            self.usd += cost
            self.calls += 1
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump({"text": text, "model": model, "usage": u.model_dump(), "cost": cost, "t": time.time()},
                  open(path, "w"))
        return text

    def _ask_openai(self, model, prompt, image, effort, system, max_tokens):
        if self._oa is None:
            import openai
            self._oa = openai.OpenAI(max_retries=6)
        content = [{"type": "text", "text": prompt}]
        if image is not None:
            content.insert(0, {"type": "image_url", "image_url": {
                "url": "data:image/png;base64," + base64.standard_b64encode(image).decode(), "detail": "high"}})
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": content}]
        r = self._oa.chat.completions.create(model=model, messages=msgs, reasoning_effort=OPENAI_EFFORT.get(effort, "medium"),
                                             max_completion_tokens=max(max_tokens, 16000))
        text = r.choices[0].message.content or ""
        u = r.usage
        pin, pout = PRICES[model]
        cost = (u.prompt_tokens * pin + u.completion_tokens * pout) / 1e6
        return text, cost
