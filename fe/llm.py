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
}


def _load_key():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    env = os.environ.get("FE_ENV_FILE", os.path.join(ROOT, "..", "dragonclaw", ".env"))
    for line in open(env):
        if line.startswith("ANTHROPIC_API_KEY="):
            os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip('"')


class Budget(Exception):
    pass


class LLM:
    def __init__(self, max_usd=None):
        _load_key()
        self.client = anthropic.Anthropic(max_retries=6)
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
