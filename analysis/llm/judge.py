"""Layer 3: LLM judge over raw transcript slices.

A case is a (session_id, seq) pointer into a raw transcript plus how many records of
context to take on each side. For each case the script opens the raw file, takes
records [seq - k_before, seq + k_after], compacts them (thinking dropped, signatures
and progress and attachments dropped, tool results cut to 2000 chars head plus 500
tail, tool args cut to 1500 chars), renders a readable transcript with `[seq]`
markers, and asks the judge the rubric for that case type.

All four harness formats are handled. `seq` is the 0-based record index inside the
file: the line index for claude_code / codex / cursor, the message index for
opencode (whose file is one JSON document).

Cases come from `results/cases/<case_type>.csv` (produced by the layer 1 C*.sql
generators) with columns session_id, seq, k_before, k_after plus any extra context
columns. Until those exist, `--synthetic-cases N` picks cases straight from the
ledger so the slice extraction and rendering can be tested end to end.

Run (dry, no key needed):
  uv run --with duckdb --with pyarrow --with orjson --with openai --with anthropic \
      analysis/llm/judge.py --synthetic-cases 5 --dry-run --print-sample 1

  uv run --with duckdb --with pyarrow --with orjson --with openai --with anthropic \
      analysis/llm/judge.py --cases analysis/results/cases/C01_rewrite_necessary.csv \
      --dry-run

Python 3.9 syntax. No em or en dashes anywhere.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import client as llm  # noqa: E402

try:
    import orjson

    def _loads(b):
        return orjson.loads(b)
except ImportError:  # pragma: no cover
    def _loads(b):
        if isinstance(b, bytes):
            b = b.decode("utf-8", "replace")
        return json.loads(b)


TASK = "judge"

TOOL_RESULT_HEAD = 2000
TOOL_RESULT_TAIL = 500
TOOL_ARGS_CHARS = 1500
TEXT_CHARS = 3000
SYSTEM_CHARS = 300

DEFAULT_K = {
    "rewrite_necessary": (12, 6),
    "tool_result_used": (2, 14),
    "hot_file_cause": (10, 10),
}

# One opencode record is a whole message with every part of a step inside it, so
# k records there is worth several times k lines of a JSONL harness. Scale down
# so an opencode slice is not ten times the size of a claude_code one.
OPENCODE_K_DIVISOR = 4

# ---------------------------------------------------------------------------
# sessions index
# ---------------------------------------------------------------------------

_FORMATS = {
    "claudecode": "claude_code", "claude_code": "claude_code",
    "codex": "codex",
    "opencode": "opencode",
    "cursor": "cursor",
}


def norm_format(detected, agent):
    for v in (detected, agent):
        if not v:
            continue
        k = str(v).strip().lower().replace(" ", "").replace("-", "")
        if k in _FORMATS:
            return _FORMATS[k]
    return None


def load_sessions(con, ledger):
    rows = con.execute(
        "select session_id, agent, detected_format, trajectory, repo "
        "from read_parquet('%s/sessions/*.parquet')" % ledger).fetchall()
    idx = {}
    for sid, agent, det, traj, repo in rows:
        idx[sid] = {"agent": agent, "format": norm_format(det, agent),
                    "trajectory": traj, "repo": repo}
    return idx


# ---------------------------------------------------------------------------
# raw record access
# ---------------------------------------------------------------------------


def _jsonl_slice(path, lo, hi):
    """seq -> record for the 0-based line indices in [lo, hi]."""
    out = {}
    with open(path, "rb") as fh:
        for i, raw in enumerate(fh):
            if i < lo:
                continue
            if i > hi:
                break
            raw = raw.strip()
            if not raw:
                continue
            try:
                out[i] = _loads(raw)
            except Exception:
                continue
    return out


def _opencode_messages(path):
    """The three on-disk shapes build_ledger handles, in the same order."""
    with open(path, "rb") as fh:
        blob = fh.read()
    doc = None
    try:
        doc = _loads(blob)
    except Exception:
        doc = None
    if isinstance(doc, dict):
        if isinstance(doc.get("messages"), list):
            return doc["messages"]
        if "info" in doc and "parts" in doc:
            return [doc]
    msgs = []
    for raw in blob.splitlines():
        if not raw.strip():
            continue
        try:
            obj = _loads(raw)
        except Exception:
            continue
        if isinstance(obj, dict):
            msgs.append(obj)
    return msgs


def read_slice(path, fmt, lo, hi):
    lo = max(0, lo)
    if fmt == "opencode":
        msgs = _opencode_messages(path)
        return dict((i, msgs[i]) for i in range(lo, min(len(msgs), hi + 1)))
    return _jsonl_slice(path, lo, hi)


# ---------------------------------------------------------------------------
# record -> blocks
# ---------------------------------------------------------------------------
# A block is (seq, kind, name, text). kind is one of:
#   user, assistant, tool_use, tool_result, tool_error, system


def _txt(x):
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        parts = []
        for b in x:
            if isinstance(b, dict):
                parts.append(b.get("text") or b.get("content") or "")
            elif isinstance(b, str):
                parts.append(b)
        return "\n".join(p for p in parts if isinstance(p, str))
    if isinstance(x, dict):
        return x.get("text") or json.dumps(x, ensure_ascii=False)
    return str(x)


def _result_text(x):
    """Tool-result text, with a marker when the result is non-text content
    (an image read, a document block) so the judge does not see an empty slot."""
    t = _txt(x)
    if t.strip():
        return t
    kinds = []
    if isinstance(x, list):
        for b in x:
            if isinstance(b, dict) and b.get("type"):
                kinds.append(b["type"])
    elif isinstance(x, dict) and x.get("type"):
        kinds.append(x["type"])
    if kinds:
        return "[non-text tool result: %s]" % ", ".join(sorted(set(kinds)))
    return t


def _dumps(x):
    if isinstance(x, str):
        return x
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return str(x)


def blocks_claude_code(seq, rec):
    typ = rec.get("type")
    if typ == "assistant":
        msg = rec.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            yield (seq, "assistant", None, content)
            return
        for blk in content or []:
            if not isinstance(blk, dict):
                continue
            bt = blk.get("type")
            if bt == "text":
                yield (seq, "assistant", None, blk.get("text") or "")
            elif bt in ("tool_use", "server_tool_use"):
                yield (seq, "tool_use", blk.get("name"), _dumps(blk.get("input")))
            # thinking / redacted_thinking / signatures: dropped
    elif typ == "user":
        msg = rec.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            yield (seq, "user", None, content)
            return
        for blk in content or []:
            if not isinstance(blk, dict):
                continue
            bt = blk.get("type")
            if bt == "text":
                yield (seq, "user", None, blk.get("text") or "")
            elif bt in ("tool_result", "advisor_tool_result"):
                kind = "tool_error" if blk.get("is_error") else "tool_result"
                yield (seq, kind, None, _result_text(blk.get("content")))
    elif typ == "system":
        sub = rec.get("subtype") or "system"
        yield (seq, "system", sub, _txt(rec.get("content"))[:SYSTEM_CHARS])
    # attachment, file-history-snapshot, progress, mode, ai-title, ...: dropped


_CX_CALLS = ("function_call", "custom_tool_call", "local_shell_call",
             "web_search_call", "tool_search_call")
_CX_OUTPUTS = ("function_call_output", "custom_tool_call_output",
               "local_shell_call_output", "web_search_call_output")


def blocks_codex(seq, rec):
    typ = rec.get("type")
    payload = rec.get("payload") or {}
    if not isinstance(payload, dict):
        return
    pt = payload.get("type")
    if typ == "response_item":
        if pt == "message":
            role = payload.get("role")
            text = _txt(payload.get("content"))
            if role == "user":
                yield (seq, "user", None, text)
            elif role == "assistant":
                yield (seq, "assistant", None, text)
            else:
                yield (seq, "system", role, text[:SYSTEM_CHARS])
        elif pt in _CX_CALLS:
            args = payload.get("arguments")
            if args is None:
                args = payload.get("input")
            if args is None:
                args = payload.get("action") or payload.get("query")
            yield (seq, "tool_use", payload.get("name") or pt, _dumps(args))
        elif pt in _CX_OUTPUTS:
            yield (seq, "tool_result", None,
                   _result_text(payload.get("output")))
        # reasoning: dropped
    elif typ == "event_msg":
        if pt == "user_message":
            yield (seq, "user", None, _txt(payload.get("message")))
        elif pt == "agent_message":
            yield (seq, "assistant", None, _txt(payload.get("message")))
        # token_count, exec_command_*, task_started, ...: dropped
    elif typ == "compacted":
        yield (seq, "system", "compacted", "[context compacted here]")


def blocks_opencode(seq, msg):
    info = msg.get("info") or {}
    if not isinstance(info, dict):
        info = {}
    role = info.get("role")
    parts = msg.get("parts")
    if not isinstance(parts, list):
        parts = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        pt = part.get("type")
        if pt == "text":
            yield (seq, "user" if role == "user" else "assistant", None,
                   part.get("text") or "")
        elif pt == "tool":
            state = part.get("state") or {}
            if not isinstance(state, dict):
                state = {}
            inp = state.get("input")
            if isinstance(inp, str):
                try:
                    inp = json.loads(inp)
                except Exception:
                    pass
            yield (seq, "tool_use", part.get("tool"), _dumps(inp))
            err = state.get("error")
            if err:
                yield (seq, "tool_error", None, _txt(err))
            elif state.get("output") is not None:
                yield (seq, "tool_result", None, _result_text(state.get("output")))
        # reasoning, step-start, step-finish, patch, file, snapshot: dropped


def blocks_cursor(seq, rec):
    role = rec.get("role")
    if role is None:
        return  # turn_ended and friends
    msg = rec.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        yield (seq, "user" if role == "user" else "assistant", None, content)
        return
    for blk in content or []:
        if not isinstance(blk, dict):
            continue
        bt = blk.get("type")
        if bt == "text":
            yield (seq, "user" if role == "user" else "assistant", None,
                   blk.get("text") or "")
        elif bt == "tool_use":
            yield (seq, "tool_use", blk.get("name"), _dumps(blk.get("input")))
        # cursor has no tool_result blocks at all


BLOCKERS = {
    "claude_code": blocks_claude_code,
    "codex": blocks_codex,
    "opencode": blocks_opencode,
    "cursor": blocks_cursor,
}


# ---------------------------------------------------------------------------
# compaction and rendering
# ---------------------------------------------------------------------------


def _clip(text, head, tail=0):
    n = len(text)
    if n <= head + tail:
        return text
    if tail:
        return ("%s\n... %d chars omitted ...\n%s"
                % (text[:head], n - head - tail, text[-tail:]))
    return "%s\n... %d chars omitted ..." % (text[:head], n - head)


def render_slice(fmt, records, focus_seq, max_chars=None):
    fn = BLOCKERS[fmt]
    lines = []
    seen = set()
    # codex writes the same user prompt twice (event_msg/user_message plus the
    # response_item echo) and the same for agent messages; nothing else does.
    dedupe = fmt == "codex"
    for seq in sorted(records):
        for blk in fn(seq, records[seq]):
            s, kind, name, text = blk
            text = (text or "").strip()
            if not text:
                continue
            if dedupe:
                key = (kind, name, text[:400])
                if key in seen:
                    continue
                seen.add(key)
            mark = "  <<< CASE FOCUS" if s == focus_seq else ""
            if kind == "user":
                lines.append("[%d] USER:%s\n%s" % (s, mark, _clip(text, TEXT_CHARS)))
            elif kind == "assistant":
                lines.append("[%d] ASSISTANT:%s\n%s"
                             % (s, mark, _clip(text, TEXT_CHARS)))
            elif kind == "tool_use":
                lines.append("[%d] TOOL_USE %s:%s\n%s"
                             % (s, name or "?", mark,
                                _clip(text, TOOL_ARGS_CHARS)))
            elif kind in ("tool_result", "tool_error"):
                tag = "ERROR" if kind == "tool_error" else "ok"
                lines.append("[%d] TOOL_RESULT (%s, %d chars):%s\n%s"
                             % (s, tag, len(text), mark,
                                _clip(text, TOOL_RESULT_HEAD, TOOL_RESULT_TAIL)))
            elif kind == "system":
                lines.append("[%d] SYSTEM %s: %s"
                             % (s, name or "", _clip(text, SYSTEM_CHARS)))
    body = "\n\n".join(lines)
    if max_chars and len(body) > max_chars:
        body = body[:max_chars] + "\n\n[... transcript truncated ...]"
    return body


# ---------------------------------------------------------------------------
# rubrics
# ---------------------------------------------------------------------------

REASON = {"type": "string",
          "description": "at most 30 words, concrete, cite the evidence"}

RUBRICS = {
    "rewrite_necessary": {
        "tool": llm.ToolSpec(
            "record_rewrite_judgement",
            "Record whether the flagged Write needed to rewrite the whole file.",
            {
                "type": "object",
                "properties": {
                    "was_full_rewrite_needed": {"type": "boolean"},
                    "estimated_lines_actually_changed": {"type": "integer"},
                    "reason": REASON,
                },
                "required": ["was_full_rewrite_needed",
                             "estimated_lines_actually_changed", "reason"],
                "additionalProperties": False,
            }),
        "system": """You review a slice of a coding agent session. The marked
CASE FOCUS record is a Write tool call: the agent wrote a whole file, replacing
whatever was there before, instead of making a targeted edit.

Decide whether writing the whole file was actually necessary.

was_full_rewrite_needed: true only when most of the file genuinely changed, or the
  file is brand new, or the change is a restructure that a few edits could not
  express. false when the surrounding transcript shows the agent had the old
  content and only a small part of it differs.

estimated_lines_actually_changed: your best integer estimate of how many lines
  actually differ from what was there before the Write. Use 0 when you cannot tell
  that anything changed, and the full line count when the file is new.

reason: at most 30 words. Point at what in the transcript decided it.""",
        "fields": ["was_full_rewrite_needed", "estimated_lines_actually_changed",
                   "reason"],
        "coerce": {"was_full_rewrite_needed": ("bool",),
                   "estimated_lines_actually_changed": ("int",),
                   "reason": ("text",)},
        "rate_field": "was_full_rewrite_needed",
        "rate_positive": False,
        "rate_label": "unnecessary full rewrites",
    },
    "tool_result_used": {
        "tool": llm.ToolSpec(
            "record_result_usage",
            "Record whether the flagged large tool result was actually used.",
            {
                "type": "object",
                "properties": {
                    "was_result_referenced_later": {"type": "boolean"},
                    "fraction_of_result_needed": {
                        "type": "string",
                        "enum": ["none", "small", "most", "all"]},
                    "reason": REASON,
                },
                "required": ["was_result_referenced_later",
                             "fraction_of_result_needed", "reason"],
                "additionalProperties": False,
            }),
        "system": """You review a slice of a coding agent session. The marked
CASE FOCUS record is a tool call whose result was large, and it then sat in the
model's context for the rest of the session, re-read on every later call.

Decide whether that result earned its place.

was_result_referenced_later: true when anything after it (agent text, a later tool
  call, an edit) clearly uses information that could only have come from that result.

fraction_of_result_needed: how much of the result the later work actually needed.
  none  nothing from it was used
  small a few lines, a path, a number, one function
  most  a large part of it
  all   effectively the whole thing

reason: at most 30 words. Name the later record that used it, or say nothing did.""",
        "fields": ["was_result_referenced_later", "fraction_of_result_needed",
                   "reason"],
        "coerce": {"was_result_referenced_later": ("bool",),
                   "fraction_of_result_needed":
                       ("enum", ["none", "small", "most", "all"], "none"),
                   "reason": ("text",)},
        "rate_field": "was_result_referenced_later",
        "rate_positive": False,
        "rate_label": "results never referenced again",
    },
    "hot_file_cause": {
        "tool": llm.ToolSpec(
            "record_hot_file_cause",
            "Record why this file is edited over and over across sessions.",
            {
                "type": "object",
                "properties": {
                    "cause": {
                        "type": "string",
                        "enum": ["architecture_hub", "agent_regression",
                                 "user_iteration", "config_churn", "test_file",
                                 "unclear"]},
                    "reason": REASON,
                },
                "required": ["cause", "reason"],
                "additionalProperties": False,
            }),
        "system": """You review a slice of a coding agent session around an edit to
a file that gets edited in an unusually large number of sessions. Decide why.

cause, one of:
  architecture_hub   a central file (router, schema, index, types, main config of
                     the app) that any feature has to touch
  agent_regression   the agent broke this file and is editing it again to fix its
                     own damage
  user_iteration     the human keeps changing their mind about what this file
                     should contain
  config_churn       settings, env, lockfile, build config churn
  test_file          a test file that changes with every feature
  unclear            the slice does not say

reason: at most 30 words, pointing at the evidence in the slice.""",
        "fields": ["cause", "reason"],
        "coerce": {"cause": ("enum", ["architecture_hub", "agent_regression",
                                      "user_iteration", "config_churn",
                                      "test_file", "unclear"], "unclear"),
                   "reason": ("text",)},
        "rate_field": "cause",
        "rate_positive": "agent_regression",
        "rate_label": "edits caused by agent regression",
    },
}


def build_request(case, transcript, case_type):
    r = RUBRICS[case_type]
    facts = []
    for k in sorted(case.get("facts") or {}):
        v = case["facts"][k]
        if v not in (None, ""):
            facts.append("  %s: %s" % (k, v))
    user = ["CASE"]
    user.append("  harness: %s" % case["format"])
    user.append("  session: %s" % case["session_id"])
    user.append("  focus record seq: %d" % case["seq"])
    if case.get("repo"):
        user.append("  repo: %s" % case["repo"])
    if facts:
        user.append("  known facts from the ledger:")
        user.extend(facts)
    user.append("")
    user.append("TRANSCRIPT SLICE (records [%d .. %d], compacted; the focus record "
                "is marked)" % (case["lo"], case["hi"]))
    user.append("")
    user.append(transcript)
    text = "\n".join(user)
    rid = hashlib.sha1(("v1|%s|%s" % (case_type, text))
                       .encode("utf-8", "replace")).hexdigest()[:24]
    return llm.Request(
        rid, r["system"], text, r["tool"],
        meta={"case_type": case_type, "session_id": case["session_id"],
              "seq": case["seq"], "stratum": case.get("stratum")},
        est_out_tokens=160,
    )


# ---------------------------------------------------------------------------
# case sources
# ---------------------------------------------------------------------------

_CORE = ("session_id", "seq", "k_before", "k_after", "stratum", "population_n")


def cases_from_csv(path, case_type):
    out = []
    kb, ka = DEFAULT_K.get(case_type, (10, 10))
    with open(path, "r", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                seq = int(float(row["seq"]))
            except (KeyError, TypeError, ValueError):
                continue
            facts = dict((k, v) for k, v in row.items()
                         if k not in _CORE and v not in (None, ""))
            out.append({
                "session_id": row["session_id"],
                "seq": seq,
                "k_before": _int(row.get("k_before"), kb),
                "k_after": _int(row.get("k_after"), ka),
                "stratum": row.get("stratum") or None,
                "population_n": _int(row.get("population_n"), 0),
                "facts": facts,
            })
    return out


def _int(v, default):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


SYNTH_SQL = {
    "rewrite_necessary": """
select session_id, agent, seq, tool_name, file_path, content_chars, input_chars
from read_parquet('{ledger}/tool_calls/*.parquet')
where tool_kind = 'write' and content_chars > 200 {agent}
order by hash(session_id || '#' || cast(seq as varchar) || '#{seed}')
limit {n}
""",
    "tool_result_used": """
select session_id, agent, seq, tool_name, tool_kind, file_path, command_head,
       result_chars
from read_parquet('{ledger}/tool_calls/*.parquet')
where result_chars > 5000 {agent}
order by hash(session_id || '#' || cast(seq as varchar) || '#{seed}')
limit {n}
""",
}


def cases_synthetic(con, ledger, case_type, n, seed, agent=None):
    clause = ("and agent = '%s'" % agent.replace("'", "")) if agent else ""
    sql = SYNTH_SQL[case_type].format(ledger=ledger, n=n, seed=seed, agent=clause)
    cur = con.execute(sql)
    names = [d[0] for d in cur.description]
    kb, ka = DEFAULT_K[case_type]
    out = []
    for row in cur.fetchall():
        d = dict(zip(names, row))
        out.append({
            "session_id": d["session_id"],
            "seq": int(d["seq"]),
            "k_before": kb,
            "k_after": ka,
            "stratum": d.get("agent"),
            "population_n": 0,
            "facts": dict((k, v) for k, v in d.items()
                          if k not in ("session_id", "seq") and v not in (None, "")),
        })
    return out


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------


def prepare(cases, sessions, data_root, case_type, max_chars, skipped):
    ready = []
    for c in cases:
        info = sessions.get(c["session_id"])
        if info is None:
            skipped.append((c["session_id"], c["seq"], "session not in ledger"))
            continue
        fmt = info["format"]
        if fmt is None:
            skipped.append((c["session_id"], c["seq"], "unknown harness format"))
            continue
        path = info["trajectory"]
        if path and not os.path.isabs(path):
            path = os.path.join(data_root, path)
        if not path or not os.path.exists(path):
            skipped.append((c["session_id"], c["seq"], "transcript not found"))
            continue
        kb, ka = c["k_before"], c["k_after"]
        if fmt == "opencode":
            kb = max(2, kb // OPENCODE_K_DIVISOR)
            ka = max(1, ka // OPENCODE_K_DIVISOR)
        lo = max(0, c["seq"] - kb)
        hi = c["seq"] + ka
        try:
            recs = read_slice(path, fmt, lo, hi)
        except Exception as exc:  # noqa: BLE001
            skipped.append((c["session_id"], c["seq"], "read failed: %s" % exc))
            continue
        if not recs:
            skipped.append((c["session_id"], c["seq"], "no records in range"))
            continue
        text = render_slice(fmt, recs, c["seq"], max_chars=max_chars)
        if not text.strip():
            skipped.append((c["session_id"], c["seq"], "slice compacted to nothing"))
            continue
        c = dict(c)
        c["format"] = fmt
        c["repo"] = info.get("repo")
        c["lo"] = min(recs)
        c["hi"] = max(recs)
        c["stratum"] = c.get("stratum") or fmt
        ready.append((c, build_request(c, text, case_type)))
    return ready


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = float(k) / n
    d = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4.0 * n * n))) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def coerce_row(co, case, case_type, data, model, cost):
    """Every model-supplied value forced to its declared type before it can
    reach pyarrow. `co` counts the repairs."""
    row = {"session_id": co.text("session_id", case.get("session_id"),
                                 default=""),
           "seq": co.integer("seq", case.get("seq")),
           "case_type": case_type,
           "stratum": co.text("stratum", case.get("stratum"),
                              default="unknown"),
           "model": co.text("model", model, default="unknown"),
           "cost_usd": float(cost)}
    spec = RUBRICS[case_type].get("coerce") or {}
    for f in RUBRICS[case_type]["fields"]:
        rule = spec.get(f, ("text",))
        v = data.get(f)
        if rule[0] == "bool":
            row[f] = co.flag(f, v)
        elif rule[0] == "int":
            row[f] = co.integer(f, v)
        elif rule[0] == "enum":
            row[f] = co.enum(f, v, rule[1], rule[2])
        else:
            row[f] = co.text(f, v, default="")
    return row


def write_outputs(results_dir, case_type, rows, strata_pop, model, provider,
                  cost, n_failed, co=None):
    import pyarrow as pa
    import pyarrow.parquet as pq

    out_dir = os.path.join(results_dir, "llm")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    r = RUBRICS[case_type]
    cols = (["session_id", "seq", "case_type", "stratum"] + r["fields"] +
            ["model", "cost_usd"])
    table = pa.table(dict((c, [row.get(c) for row in rows]) for c in cols))
    pq_path = os.path.join(out_dir, "judge_%s.parquet" % case_type)
    pq.write_table(table, pq_path, compression="zstd")

    field = r["rate_field"]
    positive = r["rate_positive"]
    by = {}
    for row in rows:
        s = row.get("stratum") or "all"
        hit, tot = by.get(s, (0, 0))
        v = row.get(field)
        ok = (v == positive) if not isinstance(positive, bool) else (bool(v) is positive)
        by[s] = (hit + (1 if ok else 0), tot + 1)

    L = ["# Layer 3 judge: %s\n" % case_type]
    L.append("provider `%s`, model `%s`, %d cases judged, %d failed, %s\n"
             % (provider, model, len(rows), n_failed, llm.fmt_usd(cost)))
    L.append("\nRate reported: **%s** (`%s` == %r)\n"
             % (r["rate_label"], field, positive))
    L.append("\n| stratum | cases | hits | rate | 95% Wilson | population | extrapolated |")
    L.append("|---|---:|---:|---:|---|---:|---:|")
    th = tt = 0
    for s in sorted(by):
        hit, tot = by[s]
        th += hit
        tt += tot
        lo, hi = wilson(hit, tot)
        pop = strata_pop.get(s, 0)
        extra = "%.0f" % (pop * hit / float(tot)) if pop and tot else "n/a"
        L.append("| %s | %d | %d | %.1f%% | %.1f%% to %.1f%% | %s | %s |"
                 % (s, tot, hit, 100.0 * hit / tot, 100.0 * lo, 100.0 * hi,
                    pop or "n/a", extra))
    if tt:
        lo, hi = wilson(th, tt)
        pop = sum(strata_pop.values())
        extra = "%.0f" % (pop * th / float(tt)) if pop else "n/a"
        L.append("| **all** | %d | %d | %.1f%% | %.1f%% to %.1f%% | %s | %s |"
                 % (tt, th, 100.0 * th / tt, 100.0 * lo, 100.0 * hi,
                    pop or "n/a", extra))
    if co is not None:
        L.extend(co.markdown("Coerced and invalid values"))
    L.append("\nExtrapolation multiplies the stratum rate by the `population_n` "
             "column of the case CSV (the layer 1 count for that stratum). It is "
             "`n/a` when the case file did not carry one.\n")
    md_path = os.path.join(out_dir, "JUDGE_%s.md" % case_type)
    with open(md_path, "w") as fh:
        fh.write("\n".join(L) + "\n")
    return pq_path, md_path


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    llm.add_common_args(ap, "judge")
    ap.add_argument("--cases", default=None, metavar="FILE",
                    help="results/cases/<case_type>.csv from the layer 1 "
                         "C*.sql generators")
    ap.add_argument("--case-type", default=None, choices=sorted(RUBRICS),
                    help="defaults to the case type named in the CSV file name")
    ap.add_argument("--synthetic-cases", type=int, default=0, metavar="N",
                    help="skip the CSVs: take N random Write tool calls "
                         "(rewrite_necessary) and N random large tool results "
                         "(tool_result_used) straight from the ledger")
    ap.add_argument("--synth-agent", default=None,
                    choices=["claude_code", "codex", "opencode", "cursor"],
                    help="restrict --synthetic-cases to one harness, to exercise "
                         "that format's renderer")
    ap.add_argument("--data-root", default=".",
                    help="prefix for the sessions table `trajectory` paths")
    ap.add_argument("--max-transcript-chars", type=int, default=60000)
    # 4000, not 1000: a judgement is ~160 tokens, but a tight budget leaves no
    # margin, and on deepseek the thinking-mode chain of thought is charged to
    # max_tokens as well (thinking is off here unless --thinking is passed).
    ap.add_argument("--max-tokens", type=int, default=4000)
    args = ap.parse_args(argv)

    if not args.cases and not args.synthetic_cases:
        raise SystemExit("pass --cases FILE or --synthetic-cases N")

    import duckdb

    con = duckdb.connect()
    sys.stderr.write("indexing sessions ...\n")
    sessions = load_sessions(con, args.ledger)

    jobs = []  # (case_type, cases)
    if args.cases:
        ct = args.case_type or infer_case_type(args.cases)
        if ct not in RUBRICS:
            raise SystemExit("cannot tell the case type from %r, pass --case-type"
                             % args.cases)
        cases = cases_from_csv(args.cases, ct)
        if args.limit:
            cases = cases[:args.limit]
        jobs.append((ct, cases))
    else:
        for ct in ("rewrite_necessary", "tool_result_used"):
            jobs.append((ct, cases_synthetic(con, args.ledger, ct,
                                             args.synthetic_cases, args.seed,
                                             args.synth_agent)))

    cl = llm.make_client(args.provider, "judge", model=args.model,
                         max_tokens=args.max_tokens, timeout=args.timeout,
                         temperature=0.0 if args.provider == "deepseek" else None,
                         thinking=args.thinking)
    cache_root = os.path.join(args.results, "llm", "cache")

    grand = {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    for case_type, cases in jobs:
        skipped = []
        ready = prepare(cases, sessions, args.data_root, case_type,
                        args.max_transcript_chars, skipped)
        sys.stderr.write("%s: %d cases, %d usable, %d skipped\n"
                         % (case_type, len(cases), len(ready), len(skipped)))
        for s in skipped[:10]:
            sys.stderr.write("  skip %s#%s: %s\n" % s)
        if not ready:
            continue
        requests = [r for _, r in ready]
        cache = llm.Cache(cache_root, "%s__%s" % (TASK, case_type),
                          enabled=not args.no_cache)

        if args.print_sample:
            llm.print_samples(cl, requests, args.print_sample)

        if args.dry_run:
            info = llm.dry_run_report(
                cl, cache, requests,
                "layer 3 %s, %d cases" % (case_type, len(requests)))
            _fmt_counts(ready)
            grand["requests"] += info["requests"]
            grand["input_tokens"] += info["input_tokens"]
            grand["output_tokens"] += info["output_tokens"]
            grand["cost_usd"] += info["cost_usd"] or 0.0
            continue

        if not cl.has_key():
            raise SystemExit("set %s, or pass --dry-run" % llm.ENV_KEYS[cl.provider])

        by_rid = dict((r.rid, c) for c, r in ready)
        rows = []
        co = llm.Coercer()
        cost = 0.0
        new_cost = 0.0
        n_failed = 0
        strata_pop = {}
        for c, _ in ready:
            if c.get("population_n"):
                strata_pop[c["stratum"]] = c["population_n"]
        for res in llm.run_requests(cl, cache, requests,
                                    concurrency=args.concurrency,
                                    retries=args.retries):
            case = by_rid[res.rid]
            if res.error:
                n_failed += 1
                sys.stderr.write("FAILED %s#%s: %s\n"
                                 % (case["session_id"], case["seq"], res.error))
                continue
            cost += res.cost
            new_cost += res.new_cost
            data = res.data if isinstance(res.data, dict) else {}
            rows.append(coerce_row(co, case, case_type, data, res.model,
                                   res.cost))
        pq_path, md_path = write_outputs(args.results, case_type, rows,
                                         strata_pop, cl.model, cl.provider,
                                         cost, n_failed, co=co)
        co.log(label="coercion (layer 3, %s)" % case_type)
        sys.stderr.write("wrote %s and %s (%d rows, %s of judgements, %s new "
                         "this run, %d cache hits)\n"
                         % (pq_path, md_path, len(rows), llm.fmt_usd(cost),
                            llm.fmt_usd(new_cost), cache.hits))

    if args.dry_run and len(jobs) > 1:
        sys.stdout.write("\n== dry run total over %d case types ==\n" % len(jobs))
        sys.stdout.write("requests       %d\n" % grand["requests"])
        sys.stdout.write("est input      %s tokens\n"
                         % "{:,}".format(grand["input_tokens"]))
        sys.stdout.write("est output     %s tokens\n"
                         % "{:,}".format(grand["output_tokens"]))
        sys.stdout.write("est cost       %s\n" % llm.fmt_usd(grand["cost_usd"]))
    return 0


def _fmt_counts(ready):
    from collections import Counter
    c = Counter(case["format"] for case, _ in ready)
    sys.stdout.write("harness mix    %s\n"
                     % ", ".join("%s=%d" % kv for kv in sorted(c.items())))


def infer_case_type(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    for ct in RUBRICS:
        if stem.endswith(ct) or ct in stem:
            return ct
    return stem


if __name__ == "__main__":
    raise SystemExit(main())
