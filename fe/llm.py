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
# Google Gemini (ai.google.dev/gemini-api/docs/pricing): rows are added by fe.llm `gemini-models` after models.list on run day
# (addendum J); thinking tokens are billed as output.
GEMINI_PRICES_FILE = os.path.join(ROOT, "runs", "gemini_prices.json")
if os.path.exists(GEMINI_PRICES_FILE):
    PRICES.update({k: tuple(v) for k, v in json.load(open(GEMINI_PRICES_FILE)).items()})
GEMINI_LEVEL = {"low": "low", "medium": "medium", "high": "high", "xhigh": "high", "max": "high"}
OPENAI_EFFORT = {"low": "low", "medium": "medium", "high": "high", "xhigh": "high", "max": "high"}


def _load_key():
    """API keys come from ANTHROPIC_API_KEY / OPENAI_API_KEY, or from a .env file (FE_ENV_FILE, default ./.env)."""
    env = os.environ.get("FE_ENV_FILE", os.path.join(ROOT, ".env"))
    if not os.path.exists(env):
        return
    for line in open(env):
        for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
            if line.startswith(k + "=") and not os.environ.get(k):
                os.environ[k] = line.split("=", 1)[1].strip().strip('"')


class Budget(Exception):
    pass


class LLM:
    def __init__(self, max_usd=None):
        _load_key()
        self.client = anthropic.Anthropic(max_retries=6)
        self._oa = None
        self._gg = None
        self.lock = threading.Lock()
        self.usd = 0.0
        self.calls = 0
        self.cached = 0
        self.max_usd = max_usd
        os.makedirs(CACHE, exist_ok=True)

    def ask(self, prompt, image=None, model="claude-sonnet-5-5", effort="low",
            system=None, max_tokens=4000, sample=0, images=None):
        """Return the model's text answer. `image` is PNG bytes or None; `images` is a list of PNG bytes (in order)."""
        if model not in PRICES:
            raise ValueError(f"model not allowed: {model}")
        h = hashlib.sha256()
        for part in (model, effort, system or "", prompt, str(sample)):
            h.update(part.encode())
            h.update(b"\0")
        if image is not None:
            h.update(hashlib.sha256(image).digest())
        for im in images or ():
            h.update(b"\1")
            h.update(hashlib.sha256(im).digest())
        key = h.hexdigest()
        path = os.path.join(CACHE, key[:2], key + ".json")
        if os.path.exists(path):
            with self.lock:
                self.cached += 1
            return json.load(open(path))["text"]
        with self.lock:
            if self.max_usd is not None and self.usd >= self.max_usd:
                raise Budget(f"budget {self.max_usd} reached")
        if model.startswith(("gpt-", "gemini-")):
            imgs = ([image] if image is not None else []) + list(images or ())
            if model.startswith("gpt-"):
                text, cost = self._ask_openai(model, prompt, imgs, effort, system, max_tokens)
            else:
                text, cost = self._ask_gemini(model, prompt, imgs, effort, system, max_tokens)
            with self.lock:
                self.usd += cost
                self.calls += 1
            os.makedirs(os.path.dirname(path), exist_ok=True)
            json.dump({"text": text, "model": model, "cost": cost, "t": time.time()}, open(path, "w"))
            return text
        content = []
        for im in ([image] if image is not None else []) + list(images or ()):
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                        "data": base64.standard_b64encode(im).decode()}})
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

    def _ask_openai(self, model, prompt, imgs, effort, system, max_tokens):
        if self._oa is None:
            import openai
            self._oa = openai.OpenAI(max_retries=6)
        content = [{"type": "image_url", "image_url": {
            "url": "data:image/png;base64," + base64.standard_b64encode(im).decode(), "detail": "high"}} for im in imgs]
        content.append({"type": "text", "text": prompt})
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": content}]
        r = self._oa.chat.completions.create(model=model, messages=msgs, reasoning_effort=OPENAI_EFFORT.get(effort, "medium"),
                                             max_completion_tokens=max(max_tokens, 16000))
        text = r.choices[0].message.content or ""
        u = r.usage
        pin, pout = PRICES[model]
        cost = (u.prompt_tokens * pin + u.completion_tokens * pout) / 1e6
        return text, cost

    def _ask_gemini(self, model, prompt, imgs, effort, system, max_tokens):
        """Gemini via google-genai. Reasoning effort maps to thinking_level (Gemini 3.x); older models fall back to thinking_budget."""
        from google import genai
        from google.genai import types
        if self._gg is None:
            self._gg = genai.Client(http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=6)))
        parts = [types.Part.from_bytes(data=im, mime_type="image/png") for im in imgs] + [types.Part.from_text(text=prompt)]
        level = GEMINI_LEVEL.get(effort, "medium")
        base = dict(system_instruction=system, max_output_tokens=max(max_tokens, 16000), temperature=1.0)
        try:
            cfg = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level=level), **base)
            r = self._gg.models.generate_content(model=model, contents=parts, config=cfg)
        except Exception as e:  # models without thinking_level (2.5 generation)
            if "thinking_level" not in str(e) and "INVALID_ARGUMENT" not in str(e):
                raise
            budget = {"low": 1024, "medium": 4096, "high": 16384}[level]
            cfg = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=budget), **base)
            r = self._gg.models.generate_content(model=model, contents=parts, config=cfg)
        text = r.text or ""
        u = r.usage_metadata
        pin, pout = PRICES[model]
        cost = ((u.prompt_token_count or 0) * pin + ((u.candidates_token_count or 0) + (u.thoughts_token_count or 0)) * pout) / 1e6
        return text, cost


def gemini_models():
    """List Gemini models visible to the key (addendum J selection step). Prints name, display name and version."""
    _load_key()
    from google import genai
    c = genai.Client()
    for m in c.models.list():
        if "gemini" in m.name and "generateContent" in (m.supported_actions or []):
            print(m.name, "|", m.display_name, "|", getattr(m, "version", ""))


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["gemini-models"]:
        gemini_models()
