"""Shared LLM plumbing for analysis layers 2 (classification) and 3 (judge).

Two providers behind one interface:

  deepseek   OpenAI-compatible, base_url https://api.deepseek.com, `openai` package,
             key env DEEPSEEK_API_KEY, JSON via response_format={"type":"json_object"},
             thinking mode disabled by default (see below).
  anthropic  `anthropic` package, key env ANTHROPIC_API_KEY, JSON via a single
             tool with strict:true and an input_schema with additionalProperties:false,
             tool_choice {"type":"auto"} plus an instruction to always call the tool.

DeepSeek V4 runs in thinking mode by default (api-docs.deepseek.com, "Thinking
Mode": the request takes `thinking: {"type": "enabled" | "disabled"}`, default
`enabled`, passed through `extra_body` when the openai package is used). The chain
of thought is billed and counted against `max_tokens`, so a short JSON task with a
small budget can come back with an empty `content` and the whole budget spent in
`reasoning_content`. Both layers here ask for one small JSON object, so this module
sends `thinking: {"type": "disabled"}` unless `--thinking` is passed, and an empty
content is treated as a retryable failure that retries with thinking off and twice
the token budget.

Nothing here makes a network call unless `call()` is reached, so every caller can be
driven end to end with --dry-run without an API key.

Run with:
  uv run --with duckdb --with pyarrow --with orjson --with openai --with anthropic \
      analysis/llm/<script>.py ...

Python 3.9 syntax. No em or en dashes anywhere.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------------------------
# pricing and models
# ---------------------------------------------------------------------------

CHARS_PER_TOKEN = 4.0

# USD per 1M tokens: (input, output)
PRICES = {
    "deepseek-v4-flash": (0.14, 0.28),
    "deepseek-v4-pro": (0.435, 0.87),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5": (2.0, 10.0),
}

# (provider, task) -> default model
DEFAULT_MODELS = {
    ("deepseek", "classify"): "deepseek-v4-flash",
    ("deepseek", "judge"): "deepseek-v4-pro",
    ("anthropic", "classify"): "claude-haiku-4-5",
    ("anthropic", "judge"): "claude-sonnet-5",
}

PROVIDERS = ("deepseek", "anthropic")

ENV_KEYS = {
    "deepseek": "DEEPSEEK_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def est_tokens(text):
    """Token estimate at the fixed 4 chars per token rule used by every dry run."""
    if not text:
        return 0
    return int(math.ceil(len(text) / CHARS_PER_TOKEN))


def cost_usd(model, in_tokens, out_tokens):
    price = PRICES.get(model)
    if price is None:
        return None
    return (in_tokens / 1e6) * price[0] + (out_tokens / 1e6) * price[1]


def fmt_usd(x):
    if x is None:
        return "n/a"
    if x < 0.01:
        return "%.4f USD" % x
    return "%.2f USD" % x


# ---------------------------------------------------------------------------
# request objects
# ---------------------------------------------------------------------------


class ToolSpec(object):
    """The single JSON-returning tool. `schema` must set additionalProperties:false."""

    __slots__ = ("name", "description", "schema")

    def __init__(self, name, description, schema):
        self.name = name
        self.description = description
        self.schema = schema


class Request(object):
    """One unit of work: a stable id, a system prompt, a user prompt, a tool spec."""

    __slots__ = ("rid", "system", "user", "tool", "meta", "est_out_tokens")

    def __init__(self, rid, system, user, tool, meta=None, est_out_tokens=256):
        self.rid = rid
        self.system = system
        self.user = user
        self.tool = tool
        self.meta = meta or {}
        self.est_out_tokens = est_out_tokens


class Result(object):
    __slots__ = ("rid", "data", "usage", "model", "provider", "cached", "error")

    def __init__(self, rid, data=None, usage=None, model=None, provider=None,
                 cached=False, error=None):
        self.rid = rid
        self.data = data
        self.usage = usage or {}
        self.model = model
        self.provider = provider
        self.cached = cached
        self.error = error

    @property
    def cost(self):
        """What this result cost to produce, cache hit or not."""
        if not self.usage:
            return 0.0
        c = cost_usd(self.model, self.usage.get("input_tokens", 0),
                     self.usage.get("output_tokens", 0))
        return c or 0.0

    @property
    def new_cost(self):
        """What this result cost in THIS run (0 when it came from the cache)."""
        return 0.0 if self.cached else self.cost


class TransientError(Exception):
    """Retryable: rate limit, timeout, 5xx, malformed JSON, missing tool call."""


class EmptyResponseError(TransientError):
    """The model returned no visible content at all.

    On DeepSeek this is the thinking-mode failure: the reasoning consumed the
    whole `max_tokens` budget and `content` came back empty. The runner retries
    it with thinking disabled and double the budget, and never caches it.
    """


# ---------------------------------------------------------------------------
# clients
# ---------------------------------------------------------------------------

ALWAYS_CALL_TMPL = (
    "You must answer by calling the `%s` tool exactly once, with all required "
    "fields filled in. Never answer with prose outside the tool call, and never "
    "call the tool more than once."
)

JSON_ONLY_TMPL = (
    "Answer with a single JSON object and nothing else: no prose, no markdown "
    "fences. The object must match this JSON schema exactly (no extra keys):\n%s"
)


class BaseClient(object):
    provider = "base"

    def __init__(self, model, max_tokens=2048, api_key=None, timeout=120.0,
                 temperature=None, thinking=False):
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.temperature = temperature
        # thinking mode: off by default, these are short JSON tasks. Only the
        # deepseek payload carries it; the anthropic path passes nothing.
        self.thinking = bool(thinking)
        self._api_key = api_key or os.environ.get(ENV_KEYS[self.provider])
        self._sdk = None
        self._lock = threading.Lock()

    # -- to be implemented -------------------------------------------------

    def build_payload(self, req, retry_boost=False):
        raise NotImplementedError

    def _send(self, payload):
        raise NotImplementedError

    # -- shared ------------------------------------------------------------

    def has_key(self):
        return bool(self._api_key)

    def estimate(self, req):
        """(input_tokens, output_tokens) for one request, 4 chars per token.

        The input side counts the serialized payload, so the tool schema and the
        JSON envelope are included, exactly like the real prompt would be.
        """
        payload = self.build_payload(req)
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return est_tokens(blob), req.est_out_tokens

    def render(self, req):
        """The exact wire payload as JSON."""
        return json.dumps(self.build_payload(req), ensure_ascii=False, indent=2)

    def render_human(self, req):
        """The same payload, with the long strings printed verbatim so a human
        can read the prompt instead of a wall of backslash-n."""
        payload = self.build_payload(req)
        bar = "-" * 74
        out = []
        for key in ("model", "max_tokens", "temperature", "tool_choice",
                    "response_format", "extra_body"):
            if key in payload:
                out.append("%s: %s" % (key, json.dumps(payload[key],
                                                       ensure_ascii=False)))
        if "tools" in payload:
            out.append("tools:")
            out.append(json.dumps(payload["tools"], ensure_ascii=False, indent=2))
        if "system" in payload:
            out.append("system:")
            out.append(bar)
            out.append(payload["system"])
            out.append(bar)
        for i, m in enumerate(payload.get("messages", [])):
            out.append("messages[%d] role=%s:" % (i, m.get("role")))
            out.append(bar)
            out.append(m.get("content") if isinstance(m.get("content"), str)
                       else json.dumps(m.get("content"), ensure_ascii=False,
                                       indent=2))
            out.append(bar)
        return "\n".join(out)

    def call(self, req, retry_boost=False):
        """One real request. `retry_boost` is the after-an-empty-response retry:
        thinking forced off and the token budget doubled."""
        if not self._api_key:
            raise RuntimeError(
                "no API key: set %s (or pass --api-key-env). Use --dry-run to "
                "estimate without calling." % ENV_KEYS[self.provider])
        data, usage = self._send(self.build_payload(req, retry_boost=retry_boost))
        if not data:
            # nothing usable came back; retryable, and never written to the cache
            raise EmptyResponseError("model returned an empty JSON object")
        return Result(req.rid, data=data, usage=usage, model=self.model,
                      provider=self.provider)


class AnthropicClient(BaseClient):
    provider = "anthropic"

    def build_payload(self, req, retry_boost=False):
        system = req.system.rstrip() + "\n\n" + (ALWAYS_CALL_TMPL % req.tool.name)
        return {
            "model": self.model,
            "max_tokens": self.max_tokens * 2 if retry_boost else self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": req.user}],
            "tools": [{
                "name": req.tool.name,
                "description": req.tool.description,
                "strict": True,
                "input_schema": req.tool.schema,
            }],
            "tool_choice": {"type": "auto"},
        }

    def _client(self):
        with self._lock:
            if self._sdk is None:
                import anthropic
                self._sdk = anthropic.Anthropic(
                    api_key=self._api_key, timeout=self.timeout, max_retries=0)
            return self._sdk

    def _send(self, payload):
        import anthropic
        try:
            msg = self._client().messages.create(**payload)
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, (anthropic.RateLimitError,
                                anthropic.APITimeoutError,
                                anthropic.APIConnectionError)):
                raise TransientError(str(exc))
            status = getattr(exc, "status_code", None)
            if status is not None and int(status) >= 500:
                raise TransientError(str(exc))
            raise
        data = None
        for blk in msg.content:
            if getattr(blk, "type", None) == "tool_use":
                data = blk.input
                break
        if data is None:
            raise TransientError("model answered without calling the tool")
        usage = {
            "input_tokens": int(getattr(msg.usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(msg.usage, "output_tokens", 0) or 0),
        }
        return data, usage


class DeepSeekClient(BaseClient):
    provider = "deepseek"

    def build_payload(self, req, retry_boost=False):
        schema_text = json.dumps(req.tool.schema, ensure_ascii=False, indent=2)
        system = (req.system.rstrip() + "\n\n" + (JSON_ONLY_TMPL % schema_text))
        # DeepSeek V4 thinks by default and the chain of thought is charged to
        # max_tokens, which leaves `content` empty on a tight budget. Disabled
        # unless --thinking, and always disabled on the after-empty retry. The
        # openai package wants non-OpenAI parameters inside extra_body.
        thinking_on = self.thinking and not retry_boost
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens * 2 if retry_boost else self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": req.user},
            ],
            "response_format": {"type": "json_object"},
            "extra_body": {
                "thinking": {"type": "enabled" if thinking_on else "disabled"},
            },
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        return payload

    def _client(self):
        with self._lock:
            if self._sdk is None:
                from openai import OpenAI
                self._sdk = OpenAI(api_key=self._api_key,
                                   base_url=DEEPSEEK_BASE_URL,
                                   timeout=self.timeout, max_retries=0)
            return self._sdk

    def _send(self, payload):
        try:
            resp = self._client().chat.completions.create(**payload)
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status_code", None)
            name = type(exc).__name__
            if name in ("RateLimitError", "APITimeoutError", "APIConnectionError",
                        "InternalServerError"):
                raise TransientError(str(exc))
            if status is not None and int(status) >= 500:
                raise TransientError(str(exc))
            raise
        choice = resp.choices[0]
        message = getattr(choice, "message", None)
        text = (getattr(message, "content", None) or "") if message else ""
        usage = {
            "input_tokens": int(getattr(resp.usage, "prompt_tokens", 0) or 0),
            "output_tokens": int(getattr(resp.usage, "completion_tokens", 0) or 0),
        }
        finish = getattr(choice, "finish_reason", None)
        if not text.strip():
            reasoning = (getattr(message, "reasoning_content", None) or "") \
                if message else ""
            raise EmptyResponseError(
                "empty content from %s: finish_reason=%s, reasoning_content=%s "
                "(%d chars), max_tokens=%s, completion_tokens=%d"
                % (self.model, finish,
                   "present" if reasoning else "absent", len(reasoning),
                   payload.get("max_tokens"), usage["output_tokens"]))
        try:
            data = parse_json_object(text)
        except TransientError as exc:
            raise TransientError("%s (finish_reason=%s, max_tokens=%s)"
                                 % (exc, finish, payload.get("max_tokens")))
        return data, usage


def parse_json_object(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.endswith("```"):
            t = t[:-3]
        t = t.strip()
        if t.startswith("json"):
            t = t[4:].strip()
    try:
        return json.loads(t)
    except Exception:
        start = t.find("{")
        end = t.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(t[start:end + 1])
            except Exception:
                pass
        raise TransientError("response was not valid JSON: %r" % t[:200])


# ---------------------------------------------------------------------------
# defensive coercion of model output
#
# A model can always answer with the wrong JSON type for a field: a bool where a
# string belongs, a string where a bool belongs, a value outside the declared
# enum, a field dropped so the next one shifts into its place. pyarrow only
# finds out when the table is built, at the very end of a run, and dies with
# "Expected bytes, got a 'bool' object" after every API call has been paid for.
# So every value that reaches a table goes through a Coercer first, and every
# repair is counted and reported.
# ---------------------------------------------------------------------------

TRUE_STRINGS = ("true", "yes", "1")


class Coercer(object):
    """Coerce model output to its declared type, counting every repair.

    `coerced` counts values that had the wrong type or spelling but carried a
    usable value; `invalid` counts values that had to be replaced by a fallback.
    """

    def __init__(self):
        self.coerced = {}
        self.invalid = {}
        self.examples = {}

    # -- counting ---------------------------------------------------------

    def _note(self, table, field, value):
        table[field] = table.get(field, 0) + 1
        if field not in self.examples:
            shown = repr(value)
            if len(shown) > 60:
                shown = shown[:57] + "..."
            shown = shown.replace("|", "/").replace("`", "'")
            self.examples[field] = "%s %s" % (type(value).__name__, shown)

    def _coerced(self, field, value):
        self._note(self.coerced, field, value)

    def _invalid(self, field, value):
        self._note(self.invalid, field, value)

    # -- per type ---------------------------------------------------------

    def text(self, field, value, default=None):
        """Any scalar to a string. None stays None unless a default is given."""
        if isinstance(value, str):
            return value
        if value is None:
            if default is None:
                return None
            self._invalid(field, value)
            return default
        self._coerced(field, value)
        if value is True:
            return "true"
        if value is False:
            return "false"
        return str(value)

    def enum(self, field, value, allowed, fallback):
        """One of `allowed`, else `fallback`, counted as invalid."""
        if isinstance(value, str):
            if value in allowed:
                return value
            s = value.strip().lower()
            if s in allowed:
                self._coerced(field, value)
                return s
        self._invalid(field, value)
        return fallback

    def language(self, field, value):
        """A lowercase ISO 639-1 code, else "unknown"."""
        if isinstance(value, str):
            s = value.strip().lower()
            if len(s) > 2 and s[2] in "-_":
                s = s[:2]
            if len(s) == 2 and s.isalpha():
                if s != value:
                    self._coerced(field, value)
                return s
        self._invalid(field, value)
        return "unknown"

    def flag(self, field, value):
        """True only for True itself or a string in TRUE_STRINGS."""
        if isinstance(value, bool):
            return value
        if value is None:
            self._invalid(field, value)
            return False
        self._coerced(field, value)
        if isinstance(value, str):
            return value.strip().lower() in TRUE_STRINGS
        return False

    def integer(self, field, value):
        """An int, or None when the value cannot be read as one."""
        if isinstance(value, bool):
            self._coerced(field, value)
            return 1 if value else 0
        if isinstance(value, int):
            return value
        if value is None:
            self._invalid(field, value)
            return None
        try:
            out = int(float(str(value).strip()))
        except (TypeError, ValueError):
            self._invalid(field, value)
            return None
        self._coerced(field, value)
        return out

    # -- reporting --------------------------------------------------------

    def fields(self):
        names = set(self.coerced)
        names.update(self.invalid)
        return sorted(names)

    def total(self):
        return sum(self.coerced.values()) + sum(self.invalid.values())

    def log(self, out=None, label="coercion"):
        out = out or sys.stderr
        names = self.fields()
        if not names:
            out.write("%s: nothing coerced, nothing invalid\n" % label)
            return
        out.write("%s: %d values repaired over %d fields\n"
                  % (label, self.total(), len(names)))
        for f in names:
            out.write("  %-34s coerced %d, invalid %d, first bad value: %s\n"
                      % (f, self.coerced.get(f, 0), self.invalid.get(f, 0),
                         self.examples.get(f, "")))

    def markdown(self, title="Coercions"):
        """The same counts as markdown lines, for a summary file."""
        L = ["\n## %s\n" % title]
        names = self.fields()
        if not names:
            L.append("Every field came back with its declared type and an "
                     "allowed value. Nothing was coerced, nothing was invalid.\n")
            return L
        L.append("Values the model returned with the wrong type or outside the "
                 "allowed set, repaired before the table was built.\n")
        L.append("| field | coerced | invalid | first bad value |")
        L.append("|---|---:|---:|---|")
        for f in names:
            L.append("| %s | %d | %d | `%s` |"
                     % (f, self.coerced.get(f, 0), self.invalid.get(f, 0),
                        self.examples.get(f, "")))
        L.append("")
        return L


def make_client(provider, task, model=None, max_tokens=2048, timeout=120.0,
                temperature=None, api_key=None, thinking=False):
    if provider not in PROVIDERS:
        raise SystemExit("unknown provider %r, expected one of %s"
                         % (provider, ", ".join(PROVIDERS)))
    model = model or DEFAULT_MODELS[(provider, task)]
    cls = AnthropicClient if provider == "anthropic" else DeepSeekClient
    return cls(model, max_tokens=max_tokens, timeout=timeout,
               temperature=temperature, api_key=api_key, thinking=thinking)


# ---------------------------------------------------------------------------
# per-item cache
# ---------------------------------------------------------------------------


class Cache(object):
    """results/llm/cache/<task>/<id[:2]>/<id>.json, one file per request.

    Sharded on the first two characters so a 6k-file task does not make one
    directory with 6000 entries. A rerun with the same items is free.
    """

    def __init__(self, root, task, enabled=True):
        self.root = os.path.join(root, task)
        self.task = task
        self.enabled = enabled
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()

    def path(self, rid):
        return os.path.join(self.root, rid[:2], rid + ".json")

    def get(self, rid):
        if not self.enabled:
            return None
        p = self.path(rid)
        if not os.path.exists(p):
            with self._lock:
                self.misses += 1
            return None
        try:
            with open(p, "r") as fh:
                obj = json.load(fh)
        except Exception:
            return None
        with self._lock:
            self.hits += 1
        return obj

    def put(self, rid, obj):
        if not self.enabled:
            return
        p = self.path(rid)
        d = os.path.dirname(p)
        if not os.path.isdir(d):
            try:
                os.makedirs(d)
            except OSError:
                pass
        tmp = p + ".tmp%d" % os.getpid()
        with open(tmp, "w") as fh:
            json.dump(obj, fh, ensure_ascii=False)
        os.replace(tmp, p)

    def describe(self):
        return ("cache dir      %s/<2-char shard>/<request id>.json"
                % self.root)


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------


def run_requests(client, cache, requests, concurrency=8, retries=4,
                 backoff=2.0, progress_every=25, out=None):
    """Execute requests through the thread pool, resuming from the cache.

    Yields Result objects in completion order. A request that fails every retry
    yields a Result with .error set; the run continues.
    """
    out = out or sys.stderr
    total = len(requests)
    state = {"done": 0, "cost": 0.0}
    lock = threading.Lock()

    def one(req):
        cached = cache.get(req.rid)
        if cached is not None and cached.get("model") == client.model:
            return Result(req.rid, data=cached.get("result"),
                          usage=cached.get("usage"), model=cached.get("model"),
                          provider=cached.get("provider"), cached=True)
        last = None
        boost = False  # set after an empty response: thinking off, double budget
        for attempt in range(retries + 1):
            try:
                res = client.call(req, retry_boost=boost)
                # only a real answer is ever written here: every failure path
                # raises before this line, so a failed item is not cached and a
                # rerun retries it instead of replaying the failure.
                cache.put(req.rid, {
                    "id": req.rid,
                    "provider": res.provider,
                    "model": res.model,
                    "usage": res.usage,
                    "result": res.data,
                    "ts": time.time(),
                })
                return res
            except EmptyResponseError as exc:
                last = exc
                boost = True
                out.write("  empty response, retrying with thinking disabled "
                          "and double max_tokens: %s\n" % exc)
                out.flush()
            except TransientError as exc:
                last = exc
            except Exception as exc:  # noqa: BLE001
                last = exc
                break
            time.sleep(min(60.0, backoff * (2 ** attempt)) *
                       (0.5 + random.random()))
        return Result(req.rid, error=str(last), model=client.model,
                      provider=client.provider)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for res in pool.map(one, requests):
            with lock:
                state["done"] += 1
                state["cost"] += res.new_cost
                n = state["done"]
            if progress_every and (n % progress_every == 0 or n == total):
                out.write("  %d/%d done, %s spent, %d from cache\n"
                          % (n, total, fmt_usd(state["cost"]), cache.hits))
                out.flush()
            yield res


# ---------------------------------------------------------------------------
# dry-run reporting
# ---------------------------------------------------------------------------


def dry_run_report(client, cache, requests, label, out=None, per_provider=True):
    """Print item counts, token and USD estimates for every provider option."""
    out = out or sys.stdout
    n = len(requests)
    in_tok = 0
    out_tok = 0
    for req in requests:
        i, o = client.estimate(req)
        in_tok += i
        out_tok += o
    out.write("\n== dry run: %s ==\n" % label)
    out.write("requests       %d\n" % n)
    out.write("provider       %s\n" % client.provider)
    out.write("model          %s\n" % client.model)
    out.write("est input      %s tokens (4 chars per token, whole payload)\n"
              % _th(in_tok))
    out.write("est output     %s tokens (%d per request)\n"
              % (_th(out_tok), requests[0].est_out_tokens if n else 0))
    out.write("est cost       %s\n" % fmt_usd(cost_usd(client.model, in_tok, out_tok)))
    out.write("%s\n" % cache.describe())
    out.write("cache hits     %d already on disk\n" % _count_cached(cache, requests))
    if per_provider:
        out.write("\nsame workload on every provider/model option:\n")
        for prov in PROVIDERS:
            for task in ("classify", "judge"):
                m = DEFAULT_MODELS[(prov, task)]
                out.write("  %-9s %-18s %-6s %s\n"
                          % (prov, m, task, fmt_usd(cost_usd(m, in_tok, out_tok))))
    out.write("\nno API key needed for the numbers above; a real run wants %s set.\n"
              % ENV_KEYS[client.provider])
    return {"requests": n, "input_tokens": in_tok, "output_tokens": out_tok,
            "cost_usd": cost_usd(client.model, in_tok, out_tok)}


def _count_cached(cache, requests):
    if not cache.enabled:
        return 0
    n = 0
    for req in requests:
        if os.path.exists(cache.path(req.rid)):
            n += 1
    return n


def _th(n):
    return "{:,}".format(int(n))


def print_samples(client, requests, n, out=None):
    out = out or sys.stdout
    for req in requests[:n]:
        out.write("\n" + "=" * 78 + "\n")
        out.write("REQUEST id=%s  meta=%s\n"
                  % (req.rid, json.dumps(req.meta, ensure_ascii=False)))
        i, o = client.estimate(req)
        out.write("est %d input tokens, %d output tokens, %s\n"
                  % (i, o, fmt_usd(cost_usd(client.model, i, o))))
        out.write("=" * 78 + "\n")
        out.write(client.render_human(req))
        out.write("\n")


# ---------------------------------------------------------------------------
# argparse helpers
# ---------------------------------------------------------------------------


def add_common_args(parser, task):
    parser.add_argument("--provider", default="deepseek", choices=list(PROVIDERS))
    parser.add_argument("--model", default=None,
                        help="override the default model for the provider "
                             "(defaults: %s)"
                             % ", ".join("%s=%s" % (p, DEFAULT_MODELS[(p, task)])
                                         for p in PROVIDERS))
    parser.add_argument("--ledger", default="analysis/ledger")
    parser.add_argument("--results", default="analysis/results")
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--limit", type=int, default=0,
                        help="only take the first N items (0 = all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="select items, render prompts, print token and USD "
                             "estimates, then exit without calling anything")
    parser.add_argument("--print-sample", type=int, default=0, metavar="N",
                        help="print N fully rendered request payloads")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--thinking", action="store_true",
                        help="deepseek only: leave thinking mode on. Off by "
                             "default because both tasks want one short JSON "
                             "object and the chain of thought is charged to "
                             "max_tokens, which can empty the visible content")
    parser.add_argument("--seed", type=int, default=20260705)
    return parser
