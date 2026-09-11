#!/usr/bin/env python3
"""Layer 1b of the token-waste analysis: raw-transcript probes.

The ledger stores lengths and hashes, not content. This script samples tool
calls (and last-call-of-turn assistant texts) from the Parquet ledger with a
fixed seed, opens the raw transcripts, measures four things the ledger cannot
answer, and extrapolates the measured shares to the ledger totals.

Probes
  read   share of Read result characters that are `cat -n` line-number prefixes
  write  JSON serialisation overhead of Write/Edit inputs, plus newline, quote
         and indentation shares of the written content, by file extension
  bash   gzip (deflate) compression ratio of Bash results, bucketed
  final  markdown structure of last-call-of-turn assistant texts

Run:
  uv run --with duckdb --with pyarrow --with orjson analysis/raw_probes.py
  uv run --with duckdb --with pyarrow --with orjson analysis/raw_probes.py \
      --n 100 --probe read,bash

Python 3.9 syntax. One pass over each transcript file, streaming line by line.
"""

from __future__ import print_function

import argparse
import csv
import os
import re
import sys
import time
import zlib
from collections import defaultdict

import duckdb
import orjson

# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------

PROBES = ("read", "write", "bash", "final")

# how far forward we scan for a tool result / the rest of an assistant message
RESULT_LOOKAHEAD = 4000
TEXT_LOOKAHEAD = 400
CODEX_SEGMENT_MAX = 4000

# harnesses whose tool results are recoverable from the raw file
RESULT_AGENTS = ("claude_code", "codex", "opencode")
READ_AGENTS = ("claude_code", "opencode")          # codex has no Read tool
TEXT_AGENTS = ("claude_code", "codex", "opencode", "cursor")

# built-in price table, USD per 1M tokens, used when prices.csv is absent.
# (pattern, p_input, p_output); patterns are fnmatch-style, first match wins,
# model ids are lowercased and '.' is normalised to '-' before matching.
BUILTIN_PRICES = (
    ("claude-opus-4-*", 5.0, 25.0),
    ("claude-opus-5*", 5.0, 25.0),
    ("claude-sonnet-4-*", 3.0, 15.0),
    ("claude-sonnet-5*", 2.0, 10.0),
    ("claude-fable-5*", 10.0, 50.0),
    ("claude-haiku-4-5*", 1.0, 5.0),
    ("gpt-5-5*", 5.0, 30.0),
    ("gpt-5-4-mini*", 0.75, 4.5),
    ("gpt-5-4*", 2.5, 15.0),
    ("gpt-5-3-codex*", 1.75, 14.0),
)

EXT_MAP = {
    "py": "py", "ts": "ts", "tsx": "tsx", "js": "js", "jsx": "js",
    "mjs": "js", "cjs": "js", "go": "go", "rs": "rs", "md": "md",
    "markdown": "md", "json": "json", "jsonl": "json",
    "yaml": "yaml", "yml": "yaml",
}

# Line-number prefix styles seen in the corpus. DESIGN.md names only the
# `cat -n` tab style; claude_code >= late 2025 uses an arrow, opencode uses
# "N: " and some builds use "N| ". The probe tries all of them per result and
# keeps the one that matches the most lines.
RE_LINENOS = (
    ("tab", re.compile(r"^[ \t]*\d+\t")),
    ("arrow", re.compile(u"^[ \t]*\\d+→")),
    ("colon", re.compile(r"^[ \t]*\d+: ")),
    ("pipe", re.compile(r"^[ \t]*\d+ ?\| ?")),
)
RE_HEADER = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
RE_BOLD_HEADER = re.compile(r"^ {0,3}\*\*([^*]{1,80})\*\*:?[ \t]*$")
RE_BULLET = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+\S")
RE_FENCE = re.compile(r"^[ \t]*(?:```|~~~)")
RE_SUMMARY = re.compile(r"summary|recap|next steps?|what i did", re.I)

CONTENT_KEYS = ("new_string", "newString", "new_str",
                "content", "contents", "file_text", "new_content", "text",
                "patchText", "patch", "diff")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def fnmatch_like(name, pattern):
    """Minimal fnmatch: '*' only (our patterns never use '?' or classes)."""
    parts = pattern.split("*")
    if len(parts) == 1:
        return name == pattern
    if not name.startswith(parts[0]):
        return False
    pos = len(parts[0])
    for part in parts[1:-1]:
        if not part:
            continue
        idx = name.find(part, pos)
        if idx < 0:
            return False
        pos = idx + len(part)
    tail = parts[-1]
    if tail:
        return name.endswith(tail) and len(name) - len(tail) >= pos
    return True


def norm_model(model):
    if not model:
        return ""
    m = model.lower().replace(".", "-")
    if "/" in m:                      # openrouter style "vendor/model"
        m = m.split("/", 1)[1]
    return m


def load_prices(path):
    """(source, list of (pattern, p_input, p_output))."""
    if path and os.path.exists(path):
        rows = []
        with open(path, "r") as fh:
            for rec in csv.DictReader(fh):
                pat = (rec.get("model_pattern") or "").strip().lower()
                if not pat:
                    continue
                pat = pat.replace(".", "-").replace("%", "*").replace("_", "?")
                try:
                    pin = float(rec.get("p_input") or 0)
                    pout = float(rec.get("p_output") or 0)
                except ValueError:
                    continue
                rows.append((pat, pin, pout))
        if rows:
            return (path, rows)
    return ("built-in table (prices.csv absent)", list(BUILTIN_PRICES))


def price_for(model, table):
    m = norm_model(model)
    if not m:
        return (None, None)
    for pat, pin, pout in table:
        if fnmatch_like(m, pat):
            return (pin, pout)
    return (None, None)


def ext_of(path):
    if not path:
        return "none"
    base = os.path.basename(path)
    if "." not in base:
        return "other"
    ext = base.rsplit(".", 1)[1].lower()
    return EXT_MAP.get(ext, "other")


def median(values):
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def mean(values):
    if not values:
        return None
    return sum(values) / float(len(values))


def fmt(value, digits=3):
    if value is None:
        return "-"
    if isinstance(value, float):
        if value != value:
            return "-"
        return ("%." + str(digits) + "f") % value
    return str(value)


def fmt_int(value):
    if value is None:
        return "-"
    return "{:,}".format(int(round(value)))


def fmt_usd(value):
    if value is None:
        return "-"
    return "{:,.2f}".format(value)


# --------------------------------------------------------------------------
# metric computation per probe
# --------------------------------------------------------------------------

def measure_read(text):
    """Line-number prefix share of a Read result."""
    total = len(text)
    lines = text.split("\n")
    n_nonempty = sum(1 for ln in lines if ln.strip())
    best = ("none", 0, 0)
    for style, rx in RE_LINENOS:
        chars = 0
        hit = 0
        for line in lines:
            m = rx.match(line)
            if m:
                hit += 1
                chars += m.end()
        if hit > best[1]:
            best = (style, hit, chars)
    style, prefixed, prefix_chars = best
    # a numbered listing prefixes essentially every line; below that the
    # matches are content that happens to start with a number
    if n_nonempty and prefixed < 0.5 * n_nonempty:
        style, prefixed, prefix_chars = ("none", 0, 0)
    if style == "none" and total > 2000 and len(lines) <= 3:
        head = text[:600]
        if '"type":"image"' in head or '"base64"' in head \
                or '"media_type"' in head:
            style = "image_base64"
    return {
        "result_chars": total,
        "n_lines": len(lines),
        "style": style,
        "n_prefixed_lines": prefixed,
        "prefix_chars": prefix_chars,
        "prefix_share": (prefix_chars / float(total)) if total else 0.0,
        "prefixed_line_share": (prefixed / float(len(lines))) if lines else 0.0,
    }


def _string_leaves(obj, acc):
    if isinstance(obj, str):
        acc[0] += len(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _string_leaves(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _string_leaves(v, acc)


def pick_content(inp):
    if isinstance(inp, str):
        return inp
    if not isinstance(inp, dict):
        return ""
    best = ""
    for key in CONTENT_KEYS:
        v = inp.get(key)
        if isinstance(v, str) and len(v) > len(best):
            best = v
    return best


def measure_write(inp, file_path):
    """JSON serialisation overhead and content composition of a Write/Edit."""
    try:
        json_bytes = len(orjson.dumps(inp))
    except Exception:
        json_bytes = len(str(inp))
    acc = [0]
    _string_leaves(inp, acc)
    leaf_chars = acc[0]
    overhead = json_bytes - leaf_chars

    content = pick_content(inp)
    clen = len(content)
    n_newlines = content.count("\n")
    n_quotes = content.count('"')
    indent = 0
    if clen:
        for line in content.split("\n"):
            stripped = line.lstrip(" \t")
            indent += len(line) - len(stripped)
    return {
        "ext": ext_of(file_path),
        "json_bytes": json_bytes,
        "string_leaf_chars": leaf_chars,
        "json_overhead_bytes": overhead,
        "json_overhead_share": (overhead / float(json_bytes)) if json_bytes else 0.0,
        "content_chars": clen,
        "n_newlines": n_newlines,
        "n_quotes": n_quotes,
        "indent_chars": indent,
        "newline_share": (n_newlines / float(clen)) if clen else 0.0,
        "quote_share": (n_quotes / float(clen)) if clen else 0.0,
        "indent_share": (indent / float(clen)) if clen else 0.0,
    }


BASH_BUCKETS = ((2.0, "<2"), (3.0, "2-3"), (5.0, "3-5"),
                (10.0, "5-10"), (20.0, "10-20"))


def bash_bucket(ratio):
    for edge, label in BASH_BUCKETS:
        if ratio < edge:
            return label
    return ">=20"


def measure_bash(text):
    raw = text.encode("utf-8", "replace")
    nbytes = len(raw)
    if nbytes == 0:
        return None
    comp = len(zlib.compress(raw, 6))
    ratio = nbytes / float(comp)
    return {
        "result_chars": len(text),
        "result_bytes": nbytes,
        "gzip_bytes": comp,
        "gzip_ratio": ratio,
        "bucket": bash_bucket(ratio),
    }


def measure_final(text):
    """Markdown structure of a final assistant reply."""
    total = len(text)
    lines = text.split("\n")
    n_headers = 0
    n_bullets = 0
    n_fence_lines = 0
    summary_chars = 0
    header_chars = 0
    bullet_chars = 0
    in_fence = False
    in_summary = False
    for line in lines:
        if RE_FENCE.match(line):
            n_fence_lines += 1
            in_fence = not in_fence
            if in_summary:
                summary_chars += len(line) + 1
            continue
        if in_fence:
            if in_summary:
                summary_chars += len(line) + 1
            continue
        mh = RE_HEADER.match(line)
        title = None
        if mh:
            title = mh.group(2)
        else:
            mb = RE_BOLD_HEADER.match(line)
            if mb:
                title = mb.group(1)
        if title is not None:
            n_headers += 1
            header_chars += len(line) + 1
            in_summary = bool(RE_SUMMARY.search(title))
            continue
        if RE_BULLET.match(line):
            n_bullets += 1
            bullet_chars += len(line) + 1
        if in_summary:
            summary_chars += len(line) + 1
    return {
        "text_chars": total,
        "n_lines": len(lines),
        "n_headers": n_headers,
        "n_bullets": n_bullets,
        "n_fences": n_fence_lines // 2,
        "header_chars": header_chars,
        "bullet_chars": bullet_chars,
        "summary_chars": min(summary_chars, total),
        "summary_share": (min(summary_chars, total) / float(total)) if total else 0.0,
        "bullet_share": (bullet_chars / float(total)) if total else 0.0,
    }


# --------------------------------------------------------------------------
# raw text extraction helpers (mirror build_ledger.py)
# --------------------------------------------------------------------------

def cc_result_text(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    parts.append(b.get("text") or "")
                else:
                    try:
                        parts.append(orjson.dumps(b).decode("utf-8"))
                    except Exception:
                        parts.append(str(b))
            elif isinstance(b, str):
                parts.append(b)
        return "".join(parts)
    try:
        return orjson.dumps(content).decode("utf-8")
    except Exception:
        return str(content)


def cx_blocks_text(blocks):
    out = []
    if isinstance(blocks, list):
        for b in blocks:
            if isinstance(b, dict):
                t = b.get("text")
                if isinstance(t, str):
                    out.append(t)
            elif isinstance(b, str):
                out.append(b)
    elif isinstance(blocks, str):
        out.append(blocks)
    return "".join(out)


def cx_output_text(out):
    if out is None:
        return ""
    if isinstance(out, str):
        return out
    if isinstance(out, list):
        return cx_blocks_text(out)
    if isinstance(out, dict):
        for k in ("output", "text", "content"):
            v = out.get(k)
            if isinstance(v, str):
                return v
            if isinstance(v, list):
                return cx_blocks_text(v)
        try:
            return orjson.dumps(out).decode("utf-8")
        except Exception:
            return str(out)
    return str(out)


# --------------------------------------------------------------------------
# item container
# --------------------------------------------------------------------------

class Item(object):
    __slots__ = ("probe", "session_id", "agent", "model", "seq",
                 "tool_use_id", "msg_id", "tool_kind", "file_path",
                 "ledger_chars")

    def __init__(self, probe, row):
        self.probe = probe
        self.session_id = row.get("session_id")
        self.agent = row.get("agent")
        self.model = row.get("model")
        self.seq = int(row.get("seq") or 0)
        self.tool_use_id = row.get("tool_use_id")
        self.msg_id = row.get("msg_id")
        self.tool_kind = row.get("tool_kind")
        self.file_path = row.get("file_path_raw") or row.get("file_path")
        self.ledger_chars = row.get("ledger_chars")

    def base_row(self):
        return {
            "probe": self.probe,
            "session_id": self.session_id,
            "agent": self.agent,
            "model": self.model or "",
            "seq": self.seq,
            "tool_use_id": self.tool_use_id or "",
            "tool_kind": self.tool_kind or "",
            "file_path": self.file_path or "",
        }


# --------------------------------------------------------------------------
# per-harness file readers
# --------------------------------------------------------------------------

def emit(out, item, metrics):
    row = item.base_row()
    row.update(metrics)
    out[item.probe].append(row)


def read_claude_code(path, items, out, stats):
    by_seq = defaultdict(list)
    for it in items:
        by_seq[it.seq].append(it)
    max_seq = max(by_seq)
    pending_res = {}     # tool_use_id -> (item, start_seq, id_bytes)
    pending_txt = {}     # key -> (item, start_seq, id_bytes, [texts])

    def flush_txt(key):
        it, _s, _b, texts = pending_txt.pop(key)
        emit(out, it, measure_final("".join(texts)))

    with open(path, "rb") as fh:
        for seq, raw in enumerate(fh):
            if seq > max_seq + RESULT_LOOKAHEAD and not pending_res \
                    and not pending_txt:
                break
            hits = by_seq.get(seq)
            rec = None
            if hits:
                try:
                    rec = orjson.loads(raw)
                except Exception:
                    rec = None
                if isinstance(rec, dict):
                    msg = rec.get("message") or {}
                    blocks = msg.get("content")
                    if not isinstance(blocks, list):
                        blocks = []
                    byid = {}
                    for blk in blocks:
                        if isinstance(blk, dict) and blk.get("id"):
                            byid[blk.get("id")] = blk
                    for it in hits:
                        if it.probe == "final":
                            texts = [b.get("text") or "" for b in blocks
                                     if isinstance(b, dict)
                                     and b.get("type") == "text"]
                            if not it.msg_id:
                                emit(out, it, measure_final("".join(texts)))
                                continue
                            key = (it.seq, it.probe)
                            pending_txt[key] = (
                                it, seq, it.msg_id.encode("utf-8"), texts)
                            continue
                        blk = byid.get(it.tool_use_id)
                        if blk is None:
                            stats["missing_input"] += 1
                            continue
                        inp = blk.get("input")
                        if it.probe == "write":
                            emit(out, it, measure_write(
                                inp if inp is not None else {}, it.file_path))
                        else:
                            pending_res[it.tool_use_id] = (
                                it, seq, (it.tool_use_id or "").encode("utf-8"))
                continue

            if pending_res:
                for tid in list(pending_res):
                    it, start, idb = pending_res[tid]
                    if seq - start > RESULT_LOOKAHEAD:
                        del pending_res[tid]
                        stats["missing_result"] += 1
                        continue
                    if idb and idb in raw:
                        if rec is None:
                            try:
                                rec = orjson.loads(raw)
                            except Exception:
                                rec = {}
                        msg = rec.get("message") if isinstance(rec, dict) else None
                        blocks = (msg or {}).get("content")
                        if not isinstance(blocks, list):
                            continue
                        for blk in blocks:
                            if not isinstance(blk, dict):
                                continue
                            if blk.get("type") != "tool_result":
                                continue
                            if blk.get("tool_use_id") != tid:
                                continue
                            text = cc_result_text(blk.get("content"))
                            if it.probe == "read":
                                emit(out, it, measure_read(text))
                            else:
                                m = measure_bash(text)
                                if m:
                                    emit(out, it, m)
                            del pending_res[tid]
                            break

            if pending_txt:
                for key in list(pending_txt):
                    it, start, idb, texts = pending_txt[key]
                    if seq - start > TEXT_LOOKAHEAD:
                        flush_txt(key)
                        continue
                    if idb and idb in raw:
                        if rec is None:
                            try:
                                rec = orjson.loads(raw)
                            except Exception:
                                rec = {}
                        if not isinstance(rec, dict) or rec.get("type") != "assistant":
                            continue
                        msg = rec.get("message") or {}
                        if msg.get("id") != it.msg_id:
                            continue
                        for blk in (msg.get("content") or []):
                            if isinstance(blk, dict) and blk.get("type") == "text":
                                texts.append(blk.get("text") or "")

    for tid in list(pending_res):
        stats["missing_result"] += 1
    for key in list(pending_txt):
        flush_txt(key)


def read_codex(path, items, out, stats):
    by_seq = defaultdict(list)
    for it in items:
        by_seq[it.seq].append(it)
    max_seq = max(by_seq)
    pending_res = {}      # call_id -> (item, start_seq, id_bytes)
    pending_txt = {}      # seq -> (item, start_seq, [texts])

    def flush_txt(key):
        it, _s, texts = pending_txt.pop(key)
        emit(out, it, measure_final("\n".join(t for t in texts if t)))

    with open(path, "rb") as fh:
        for seq, raw in enumerate(fh):
            if seq > max_seq + RESULT_LOOKAHEAD and not pending_res \
                    and not pending_txt:
                break
            rec = None
            hits = by_seq.get(seq)
            if hits:
                try:
                    rec = orjson.loads(raw)
                except Exception:
                    rec = None
                payload = (rec or {}).get("payload")
                if not isinstance(payload, dict):
                    payload = {}
                for it in hits:
                    if it.probe == "final":
                        pending_txt[it.seq] = (it, seq, [])
                        continue
                    args = payload.get("arguments")
                    if args is None:
                        args = payload.get("input")
                    if args is None:
                        args = payload.get("action") or payload.get("query")
                    if it.probe == "write":
                        inp = args
                        if isinstance(args, str):
                            s = args.lstrip()
                            if s.startswith("{"):
                                try:
                                    inp = orjson.loads(args)
                                except Exception:
                                    inp = args
                        if inp is None:
                            stats["missing_input"] += 1
                            continue
                        emit(out, it, measure_write(inp, it.file_path))
                    else:
                        cid = payload.get("call_id") or payload.get("id") \
                            or it.tool_use_id
                        pending_res[cid] = (
                            it, seq, (cid or "").encode("utf-8"))

            if pending_txt:
                if rec is None:
                    try:
                        rec = orjson.loads(raw)
                    except Exception:
                        rec = {}
                if isinstance(rec, dict):
                    typ = rec.get("type")
                    payload = rec.get("payload")
                    if not isinstance(payload, dict):
                        payload = {}
                    closed = False
                    if typ == "event_msg" and payload.get("type") == "token_count" \
                            and isinstance(payload.get("info"), dict):
                        closed = True
                    text = None
                    if typ == "response_item" and payload.get("type") == "message" \
                            and payload.get("role") == "assistant":
                        text = cx_blocks_text(payload.get("content"))
                    for key in list(pending_txt):
                        it, start, texts = pending_txt[key]
                        if seq < start:
                            continue
                        if text:
                            texts.append(text)
                        if closed or seq - start > CODEX_SEGMENT_MAX:
                            flush_txt(key)

            if pending_res:
                for cid in list(pending_res):
                    it, start, idb = pending_res[cid]
                    if seq - start > RESULT_LOOKAHEAD:
                        del pending_res[cid]
                        stats["missing_result"] += 1
                        continue
                    if not idb or idb not in raw:
                        continue
                    if rec is None:
                        try:
                            rec = orjson.loads(raw)
                        except Exception:
                            rec = {}
                    payload = (rec or {}).get("payload")
                    if not isinstance(payload, dict):
                        continue
                    ptype = payload.get("type") or ""
                    if not ptype.endswith("_call_output"):
                        continue
                    if payload.get("call_id") != cid:
                        continue
                    text = cx_output_text(payload.get("output"))
                    if it.probe == "read":
                        emit(out, it, measure_read(text))
                    else:
                        m = measure_bash(text)
                        if m:
                            emit(out, it, m)
                    del pending_res[cid]

    for cid in list(pending_res):
        stats["missing_result"] += 1
    for key in list(pending_txt):
        flush_txt(key)


def _oc_messages(blob):
    doc = None
    try:
        doc = orjson.loads(blob)
    except Exception:
        doc = None
    if isinstance(doc, dict):
        if isinstance(doc.get("messages"), list):
            return doc["messages"]
        if "info" in doc and "parts" in doc:
            return [doc]
    messages = []
    for raw in blob.splitlines():
        if not raw.strip():
            continue
        try:
            obj = orjson.loads(raw)
        except Exception:
            continue
        if isinstance(obj, dict):
            messages.append(obj)
    return messages


def read_opencode(path, items, out, stats):
    with open(path, "rb") as fh:
        blob = fh.read()
    messages = _oc_messages(blob)
    del blob
    for it in items:
        if it.seq >= len(messages):
            stats["missing_input"] += 1
            continue
        msg = messages[it.seq]
        if not isinstance(msg, dict):
            stats["missing_input"] += 1
            continue
        parts = msg.get("parts")
        if not isinstance(parts, list):
            parts = []
        if it.probe == "final":
            texts = [p.get("text") or "" for p in parts
                     if isinstance(p, dict) and p.get("type") == "text"]
            emit(out, it, measure_final("".join(texts)))
            continue
        part = None
        for p in parts:
            if not isinstance(p, dict) or p.get("type") != "tool":
                continue
            if (p.get("callID") or p.get("id")) == it.tool_use_id:
                part = p
                break
        if part is None:
            stats["missing_input"] += 1
            continue
        state = part.get("state")
        if not isinstance(state, dict):
            state = {}
        if it.probe == "write":
            inp = state.get("input")
            if isinstance(inp, str):
                try:
                    inp = orjson.loads(inp)
                except Exception:
                    inp = {"command": inp}
            if not isinstance(inp, dict):
                inp = {}
            if part.get("filePath") and not inp.get("filePath"):
                inp = dict(inp)
                inp["filePath"] = part.get("filePath")
            emit(out, it, measure_write(inp, it.file_path))
            continue
        text = state.get("output")
        if not isinstance(text, str):
            err = state.get("error")
            text = err if isinstance(err, str) else ""
        if it.probe == "read":
            emit(out, it, measure_read(text))
        else:
            m = measure_bash(text)
            if m:
                emit(out, it, m)
    del messages


def read_cursor(path, items, out, stats):
    by_seq = defaultdict(list)
    for it in items:
        by_seq[it.seq].append(it)
    max_seq = max(by_seq)
    with open(path, "rb") as fh:
        for seq, raw in enumerate(fh):
            if seq > max_seq:
                break
            hits = by_seq.get(seq)
            if not hits:
                continue
            try:
                rec = orjson.loads(raw)
            except Exception:
                continue
            msg = (rec or {}).get("message") or {}
            blocks = msg.get("content")
            if isinstance(blocks, str):
                blocks = [{"type": "text", "text": blocks}]
            if not isinstance(blocks, list):
                blocks = []
            texts = [b.get("text") or "" for b in blocks
                     if isinstance(b, dict) and b.get("type") == "text"]
            for it in hits:
                if it.probe == "final":
                    emit(out, it, measure_final("".join(texts)))
                else:
                    stats["missing_input"] += 1


READERS = {
    "claude_code": read_claude_code,
    "codex": read_codex,
    "opencode": read_opencode,
    "cursor": read_cursor,
}


# --------------------------------------------------------------------------
# ledger access
# --------------------------------------------------------------------------

def open_ledger(con, ledger):
    def view(name):
        pat = os.path.join(ledger, name, "*.parquet").replace("'", "''")
        con.execute(
            "create or replace view %s as select * from read_parquet('%s')"
            % (name, pat))
    for name in ("calls", "tool_calls", "user_turns", "sessions"):
        view(name)
    con.execute("""
        create or replace table sess_model as
        select session_id, arg_max(model, n) as model
        from (select session_id, model, count(*) as n
              from calls where model is not null group by 1, 2)
        group by 1
    """)
    con.execute("""
        create or replace table traj as
        select session_id, any_value(trajectory) as trajectory
        from sessions where trajectory is not null group by 1
    """)


FILTERS = {
    "read": ("tool_calls t",
             "t.tool_kind = 'read' and t.result_chars > 0 "
             "and t.tool_use_id is not null and t.agent in %s"
             % (str(READ_AGENTS),),
             "t.result_chars"),
    "bash": ("tool_calls t",
             "t.tool_kind = 'bash' and t.result_chars > 0 "
             "and t.tool_use_id is not null and t.agent in %s"
             % (str(RESULT_AGENTS),),
             "t.result_chars"),
    "write": ("tool_calls t",
              "t.tool_kind in ('write', 'edit') and t.input_chars > 0 "
              "and t.tool_use_id is not null and t.agent in %s"
              % (str(RESULT_AGENTS),),
              "t.input_chars"),
}

FINAL_BASE = """
    with u as (
        select session_id, agent, seq, msg_id, n_text_chars, 1 as is_call
        from calls
        where coalesce(is_sidechain, false) = false
        union all
        select session_id, agent, seq, null, 0, 0
        from user_turns
        where is_meta = false and human_chars > 0
    ), w as (
        select *, lead(is_call) over (
            partition by session_id order by seq, is_call desc) as nxt
        from u
    ), t as (
        select session_id, agent, seq, any_value(msg_id) as msg_id,
               max(n_text_chars) as n_text_chars
        from w
        where is_call = 1 and nxt = 0 and n_text_chars > 0 and agent in %s
        group by session_id, agent, seq
    )
""" % (str(TEXT_AGENTS),)


def sample_probe(con, probe, n, seed):
    """Reservoir sample of the probe population.

    DuckDB applies `USING SAMPLE` before the WHERE clause, so the filtered
    population is materialised in a subquery and the sample taken outside it.
    """
    if probe == "final":
        inner = FINAL_BASE + """
            select t.session_id, t.agent, t.seq, t.msg_id,
                   cast(null as varchar) as tool_use_id,
                   cast(null as varchar) as tool_kind,
                   cast(null as varchar) as file_path_raw,
                   t.n_text_chars as ledger_chars,
                   tr.trajectory, sm.model
            from t
            join traj tr on tr.session_id = t.session_id
            left join sess_model sm on sm.session_id = t.session_id
        """
    else:
        _tbl, where, chars = FILTERS[probe]
        inner = """
            select t.session_id, t.agent, t.seq, t.msg_id, t.tool_use_id,
                   t.tool_kind, t.file_path_raw, %s as ledger_chars,
                   tr.trajectory, sm.model
            from tool_calls t
            join traj tr on tr.session_id = t.session_id
            left join sess_model sm on sm.session_id = t.session_id
            where %s
        """ % (chars, where)
    sql = ("select * from (%s) as pop using sample reservoir(%d rows) "
           "repeatable (%d)" % (inner, n, seed))
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def population(con, probe):
    """(agent, model) -> (n_items, total_chars) over the whole ledger."""
    if probe == "final":
        sql = FINAL_BASE + """
            select t.agent, coalesce(sm.model, '') as model,
                   count(*) as n, sum(t.n_text_chars) as chars
            from t left join sess_model sm on sm.session_id = t.session_id
            group by 1, 2
        """
    else:
        _tbl, where, chars = FILTERS[probe]
        sql = """
            select t.agent, coalesce(sm.model, '') as model,
                   count(*) as n, sum(%s) as chars
            from tool_calls t
            left join sess_model sm on sm.session_id = t.session_id
            where %s
            group by 1, 2
        """ % (chars, where)
    out = {}
    for agent, model, n, chars in con.execute(sql).fetchall():
        out[(agent, model)] = (int(n or 0), int(chars or 0))
    return out


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

# probe -> list of (name, numerator function, denominator column, price side,
#                   label)
EXTRAPOLATE = {
    "read": [
        ("lineno_prefixes", lambda r: r["prefix_chars"], "result_chars",
         "input", "Read result chars that are line-number prefixes"),
        ("image_base64",
         lambda r: r["result_chars"] if r["style"] == "image_base64" else 0,
         "result_chars", "input",
         "Read result chars that are base64 image payloads, not text"),
    ],
    "write": [
        ("json_overhead", lambda r: r["json_overhead_bytes"], "json_bytes",
         "output",
         "Write/Edit input bytes that are JSON syntax, not file content"),
        ("newlines_and_indent",
         lambda r: r["n_newlines"] + r["indent_chars"], "json_bytes", "output",
         "Write/Edit content chars that are newlines or leading whitespace"),
    ],
    "bash": [
        ("high_ratio_results",
         lambda r: r["result_chars"] if r["gzip_ratio"] > 10 else 0,
         "result_chars", "input",
         "Bash result chars in highly compressible results (gzip ratio > 10)"),
        ("compressible_redundancy",
         lambda r: r["result_chars"] * (1.0 - 1.0 / r["gzip_ratio"]),
         "result_chars", "input",
         "Bash result chars that are pure redundancy "
         "(chars * (1 - 1/gzip ratio))"),
    ],
    "final": [
        ("summary_sections", lambda r: r["summary_chars"], "text_chars",
         "output", "Final-reply chars inside summary/recap sections"),
        ("bullets", lambda r: r["bullet_chars"], "text_chars", "output",
         "Final-reply chars on bullet lines"),
    ],
}


def extrapolate(spec, rows, pop, price_table):
    """Apply the sample's char-weighted share per agent to the ledger totals."""
    name, num_fn, den_col, side, _label = spec
    num = defaultdict(float)
    den = defaultdict(float)
    for r in rows:
        agent = r["agent"]
        num[agent] += num_fn(r)
        den[agent] += r[den_col]

    out = []
    for (agent, model), (n_items, chars) in sorted(pop.items()):
        d = den.get(agent, 0.0)
        share = (num.get(agent, 0.0) / d) if d else None
        pin, pout = price_for(model, price_table)
        price = pin if side == "input" else pout
        wasted = (chars * share) if share is not None else None
        tokens = (wasted / 4.0) if wasted is not None else None
        usd = (tokens / 1e6 * price) if (tokens is not None and price) else None
        out.append({
            "measure": name, "agent": agent, "model": model or "(unknown)",
            "n_items": n_items, "population_chars": chars,
            "sample_share": share, "wasted_chars": wasted,
            "wasted_tokens": tokens, "price_usd_per_mtok": price,
            "usd": usd, "priced": price is not None,
        })
    return out


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(lines)


def write_csv(path, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def summarize_read(rows):
    shares = [r["prefix_share"] for r in rows]
    total = sum(r["result_chars"] for r in rows)
    pref = sum(r["prefix_chars"] for r in rows)
    body = []
    by_agent = defaultdict(list)
    for r in rows:
        by_agent[r["agent"]].append(r)
    table = []
    for agent in sorted(by_agent):
        rs = by_agent[agent]
        t = sum(x["result_chars"] for x in rs)
        p = sum(x["prefix_chars"] for x in rs)
        table.append([agent, len(rs),
                      fmt(median([x["prefix_share"] for x in rs]), 4),
                      fmt(mean([x["prefix_share"] for x in rs]), 4),
                      fmt((p / float(t)) if t else 0, 4),
                      fmt_int(median([x["n_lines"] for x in rs])),
                      fmt(mean([x["prefixed_line_share"] for x in rs]), 3)])
    body.append(md_table(
        ["agent", "sampled", "median share", "mean share",
         "char-weighted share", "median lines", "mean prefixed-line share"],
        table))
    body.append("")
    body.append("Pooled: %s sampled results, %s result chars, %s prefix chars, "
                "char-weighted prefix share %s."
                % (fmt_int(len(rows)), fmt_int(total), fmt_int(pref),
                   fmt((pref / float(total)) if total else 0, 4)))
    body.append("")
    by_style = defaultdict(list)
    for r in rows:
        by_style[r["style"]].append(r)
    stbl = []
    for style in sorted(by_style, key=lambda s: -len(by_style[s])):
        rs = by_style[style]
        t = sum(x["result_chars"] for x in rs)
        p = sum(x["prefix_chars"] for x in rs)
        stbl.append([style, len(rs), fmt(len(rs) / float(len(rows)), 3),
                     fmt_int(t), fmt((p / float(t)) if t else 0, 4)])
    body.append(md_table(
        ["numbering style", "sampled", "share of results", "result chars",
         "char-weighted prefix share"], stbl))
    _ = shares
    return "\n".join(body)


def summarize_write(rows):
    body = []
    by_ext = defaultdict(list)
    for r in rows:
        by_ext[r["ext"]].append(r)
    table = []
    for ext in sorted(by_ext, key=lambda e: -len(by_ext[e])):
        rs = by_ext[ext]
        jb = sum(x["json_bytes"] for x in rs)
        ov = sum(x["json_overhead_bytes"] for x in rs)
        cc = sum(x["content_chars"] for x in rs)
        table.append([
            ext, len(rs),
            fmt(median([x["json_overhead_share"] for x in rs]), 4),
            fmt((ov / float(jb)) if jb else 0, 4),
            fmt((sum(x["n_newlines"] for x in rs) / float(cc)) if cc else 0, 4),
            fmt((sum(x["n_quotes"] for x in rs) / float(cc)) if cc else 0, 4),
            fmt((sum(x["indent_chars"] for x in rs) / float(cc)) if cc else 0, 4),
            fmt_int(median([x["content_chars"] for x in rs]))])
    body.append(md_table(
        ["ext", "sampled", "median JSON overhead share",
         "char-weighted JSON overhead share", "newline share", "quote share",
         "indent share", "median content chars"], table))

    table2 = []
    by_kind = defaultdict(list)
    for r in rows:
        by_kind[(r["agent"], r["tool_kind"])].append(r)
    for key in sorted(by_kind):
        rs = by_kind[key]
        jb = sum(x["json_bytes"] for x in rs)
        ov = sum(x["json_overhead_bytes"] for x in rs)
        table2.append([key[0], key[1], len(rs),
                       fmt(median([x["json_overhead_share"] for x in rs]), 4),
                       fmt((ov / float(jb)) if jb else 0, 4),
                       fmt_int(median([x["json_bytes"] for x in rs]))])
    body.append("")
    body.append(md_table(
        ["agent", "tool", "sampled", "median JSON overhead share",
         "char-weighted overhead share", "median input bytes"], table2))
    return "\n".join(body)


def summarize_bash(rows):
    body = []
    order = ["<2", "2-3", "3-5", "5-10", "10-20", ">=20"]
    by_b = defaultdict(list)
    for r in rows:
        by_b[r["bucket"]].append(r)
    total_chars = sum(r["result_chars"] for r in rows)
    table = []
    for b in order:
        rs = by_b.get(b, [])
        if not rs:
            continue
        c = sum(x["result_chars"] for x in rs)
        table.append([b, len(rs), fmt(len(rs) / float(len(rows)), 3),
                      fmt_int(c), fmt(c / float(total_chars), 3),
                      fmt(median([x["gzip_ratio"] for x in rs]), 2),
                      fmt_int(median([x["result_chars"] for x in rs]))])
    body.append(md_table(
        ["gzip ratio bucket", "sampled", "share of results", "result chars",
         "share of result chars", "median ratio", "median chars"], table))

    table2 = []
    by_agent = defaultdict(list)
    for r in rows:
        by_agent[r["agent"]].append(r)
    for agent in sorted(by_agent):
        rs = by_agent[agent]
        c = sum(x["result_chars"] for x in rs)
        big = sum(x["result_chars"] for x in rs if x["gzip_ratio"] > 10)
        table2.append([agent, len(rs),
                       fmt(median([x["gzip_ratio"] for x in rs]), 2),
                       fmt(mean([x["gzip_ratio"] for x in rs]), 2),
                       fmt((big / float(c)) if c else 0, 4)])
    body.append("")
    body.append(md_table(
        ["agent", "sampled", "median ratio", "mean ratio",
         "share of chars with ratio > 10"], table2))
    return "\n".join(body)


def summarize_final(rows):
    body = []
    by_agent = defaultdict(list)
    for r in rows:
        by_agent[r["agent"]].append(r)
    table = []
    for agent in sorted(by_agent):
        rs = by_agent[agent]
        tc = sum(x["text_chars"] for x in rs)
        sc = sum(x["summary_chars"] for x in rs)
        bc = sum(x["bullet_chars"] for x in rs)
        table.append([agent, len(rs),
                      fmt_int(median([x["text_chars"] for x in rs])),
                      fmt(median([x["n_headers"] for x in rs]), 1),
                      fmt(mean([x["n_headers"] for x in rs]), 2),
                      fmt(median([x["n_bullets"] for x in rs]), 1),
                      fmt(mean([x["n_bullets"] for x in rs]), 2),
                      fmt(mean([x["n_fences"] for x in rs]), 2),
                      fmt((bc / float(tc)) if tc else 0, 3),
                      fmt((sc / float(tc)) if tc else 0, 4)])
    body.append(md_table(
        ["agent", "sampled", "median chars", "median headers", "mean headers",
         "median bullets", "mean bullets", "mean fences", "bullet char share",
         "summary char share"], table))
    n_struct = sum(1 for r in rows
                   if r["n_headers"] > 0 or r["n_bullets"] >= 3)
    body.append("")
    body.append("Structured replies (>= 1 header or >= 3 bullets): %s of %s "
                "(%s)." % (fmt_int(n_struct), fmt_int(len(rows)),
                           fmt(n_struct / float(len(rows)), 3) if rows else "-"))
    return "\n".join(body)


SUMMARIZERS = {
    "read": summarize_read,
    "write": summarize_write,
    "bash": summarize_bash,
    "final": summarize_final,
}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    ap = argparse.ArgumentParser(description="Layer 1b raw-transcript probes")
    ap.add_argument("--ledger", default=os.path.join(here, "ledger"))
    ap.add_argument("--results", default=os.path.join(here, "results", "probes"))
    ap.add_argument("--root", default=root,
                    help="base directory the trajectory paths are relative to")
    ap.add_argument("--prices", default=os.path.join(here, "prices.csv"))
    ap.add_argument("--n", type=int, default=3000, help="sample size per probe")
    ap.add_argument("--probe", default=",".join(PROBES))
    ap.add_argument("--seed", type=int, default=20260705)
    args = ap.parse_args(argv)

    probes = [p.strip() for p in args.probe.split(",") if p.strip()]
    for p in probes:
        if p not in PROBES:
            ap.error("unknown probe: %s (known: %s)" % (p, ", ".join(PROBES)))

    t0 = time.time()
    price_src, price_table = load_prices(args.prices)
    print("prices: %s" % price_src)

    con = duckdb.connect()
    open_ledger(con, args.ledger)

    items_by_path = defaultdict(list)
    sampled = {}
    pops = {}
    for probe in probes:
        rows = sample_probe(con, probe, args.n, args.seed)
        sampled[probe] = len(rows)
        pops[probe] = population(con, probe)
        for r in rows:
            path = r.get("trajectory")
            if not path:
                continue
            if not os.path.isabs(path):
                path = os.path.join(args.root, path)
            items_by_path[path].append(Item(probe, r))
        print("probe %-6s sampled %d items" % (probe, len(rows)))
    con.close()

    paths = sorted(items_by_path)
    print("reading %d transcript files" % len(paths))

    out = dict((p, []) for p in probes)
    stats = defaultdict(int)
    t_read = time.time()
    for i, path in enumerate(paths):
        items = items_by_path[path]
        agent = items[0].agent
        reader = READERS.get(agent)
        if reader is None or not os.path.exists(path):
            stats["missing_file"] += len(items)
            continue
        try:
            reader(path, items, out, stats)
        except Exception as exc:
            stats["read_error"] += len(items)
            print("  ! %s: %s" % (os.path.basename(path), exc))
        if (i + 1) % 250 == 0:
            print("  %d/%d files, %.1fs" % (i + 1, len(paths),
                                            time.time() - t_read))

    if not os.path.isdir(args.results):
        os.makedirs(args.results)

    extras = {}
    for probe in probes:
        rows = out[probe]
        write_csv(os.path.join(args.results, probe + ".csv"), rows)
        extras[probe] = []
        flat = []
        for spec in EXTRAPOLATE[probe]:
            ex = extrapolate(spec, rows, pops[probe], price_table) if rows \
                else []
            extras[probe].append((spec, ex))
            flat.extend(ex)
        write_csv(os.path.join(args.results, probe + "_extrapolation.csv"),
                  flat)
        print("probe %-6s measured %d items" % (probe, len(rows)))

    runtime = time.time() - t0
    write_report(args, probes, out, extras, price_src, stats, runtime, sampled)
    print("done in %.1fs" % runtime)
    return 0


ASSUMPTIONS = """\
1. **Sampling.** Each probe draws a reservoir sample of `N` rows from the
   ledger with DuckDB `USING SAMPLE reservoir(N ROWS) REPEATABLE (seed)`, so a
   rerun with the same `--n` and `--seed` selects the same rows. The sample is
   uniform over *tool calls* (not over characters).
2. **Extrapolation.** For each probe the sample's **character-weighted** share
   is computed per agent and multiplied by that agent's exact ledger total
   (Read result chars, Write/Edit input bytes, Bash result chars, final-reply
   text chars). This uses the exact population total and only estimates the
   share, which is more stable than scaling a per-call mean by the row count.
   No confidence intervals are computed. Result sizes are heavy-tailed, so a
   character-weighted share can be dominated by a handful of sampled items:
   each extrapolation states how many sampled items contribute to it, and the
   ones resting on tens of items (base64 image reads, bash results with a gzip
   ratio above 10) should be read as an order of magnitude, not a figure.
3. **Tokens.** `tokens = chars / 4`. No tokeniser is run.
4. **Model attribution.** The ledger has no model on `tool_calls`, so every row
   of a session is attributed to that session's **dominant model** (the model
   of the most `calls` rows in the session). Sessions whose model is missing or
   not in the price table are reported as unpriced.
5. **Prices.** Input-side populations (Read results, Bash results) are priced
   at the **input** rate, output-side populations (Write/Edit inputs, final
   replies) at the **output** rate. This is a **lower bound** for the input
   side: a tool result that stays in context is re-paid on every later call as
   a cache read (that is thesis T04, not this layer). Cache writes and cache
   reads are ignored here.
6. **Harness coverage.** Cursor transcripts carry no `tool_result` blocks and
   no `tool_use` ids, so cursor is excluded from the read, write and bash
   probes; it is included in the final-text probe (which needs only the
   assistant text of a line). Codex has no Read tool at all (it reads files
   with shell commands), so the read probe covers claude_code and opencode.
7. **Last call of a turn** is approximated from the ledger: every non-sidechain
   `calls` row and every non-meta `user_turns` row of a session are merged and
   ordered by `seq` (a call sorts before a user turn at the same `seq`);
   `tool_calls` rows are not in that order, so "the next non-tool record". A
   call whose successor in that order is a user turn, and which has
   `n_text_chars > 0`, is the final reply of the turn. Approximations: a turn
   whose last call emitted no text contributes nothing (the text that the human
   answered may sit one call earlier); the last turn of every session is never
   counted, because no human prompt follows it; sidechain (subagent) replies are
   excluded entirely; for opencode a message can hold several `calls` rows
   (one per `step-finish`) and the probe reads the text parts of the whole
   message, so its final text can be slightly over-counted.
8. **Raw-record location.** `seq` is the 0-based record index in the transcript
   (line index for claude_code, codex and cursor, message index for opencode).
   For claude_code the tool result is found by scanning forward from the tool
   call for a `user` record carrying a `tool_result` with the same
   `tool_use_id` (max %d records); for codex by scanning forward for a
   `*_call_output` with the same `call_id`; for opencode the result is inline in
   the same part (`state.output`). For claude_code the final reply is the
   concatenation of the text blocks of every assistant record sharing the
   call's `message.id` (max %d records ahead); for codex it is every assistant
   `response_item` message from the call's first record until the closing
   `token_count` event.
9. **Line-number prefixes.** DESIGN.md names the `cat -n` style `^\\s*\\d+\\t`.
   The corpus actually uses four styles: a tab (older claude_code), a
   rightwards arrow `N->` (current claude_code), `N: ` (opencode) and `N| `.
   Each result is matched against all four and the style with the most matching
   lines wins; if fewer than half the non-empty lines match, the result counts
   as not numbered (so prose that happens to start with a number is not
   mistaken for a listing). An unnumbered result longer than 2000 chars that
   fits on at most 3 lines and whose head contains `"type":"image"`,
   `"media_type"` or `"base64"` is classified `image_base64`: the Read returned
   a picture, so those characters are a base64 blob rather than file text.
10. **gzip ratio** is `len(utf-8 bytes) / len(zlib.compress(bytes, 6))`, i.e.
   the raw deflate stream without the ~18 byte gzip header and footer.
11. **JSON overhead** is `len(orjson.dumps(tool_input)) - sum(len(s))` over all
   string leaves of the input, i.e. braces, keys, commas and the `\\n`, `\\"`
   and `\\uXXXX` escape expansion. `orjson.dumps` is the same serialiser the
   ledger used for `input_chars`, so the two are directly comparable.
   Indentation share counts leading spaces and tabs per line of the written
   content; newline and quote shares count `\\n` and `"` in that content. The
   newline-and-indent extrapolation counts one byte per newline although JSON
   serialises it as two (`\\n`), so it is a lower bound.
12. **Summary sections** are the lines after a markdown header (`#`..`######`)
   or a bold-only line whose title matches `summary|recap|next steps|what I
   did`, up to the next header. Fenced code blocks are not treated as headers
   but their content counts toward a summary section it sits in.
""" % (RESULT_LOOKAHEAD, TEXT_LOOKAHEAD)


def write_report(args, probes, out, extras, price_src, stats, runtime,
                 sampled):
    lines = []
    lines.append("# Layer 1b: raw-transcript probes")
    lines.append("")
    lines.append("Generated by `analysis/raw_probes.py` "
                 "(N = %d per probe, seed %d, runtime %.1fs)."
                 % (args.n, args.seed, runtime))
    lines.append("")
    lines.append("Prices: %s." % price_src)
    lines.append("")

    tbl = []
    for probe in probes:
        rows = out[probe]
        tbl.append([probe, fmt_int(sampled.get(probe, 0)), fmt_int(len(rows)),
                    fmt((len(rows) / float(sampled[probe]))
                        if sampled.get(probe) else 0, 3)])
    lines.append("## Coverage")
    lines.append("")
    lines.append(md_table(["probe", "sampled", "measured", "hit rate"], tbl))
    if stats:
        lines.append("")
        lines.append("Drops: " + ", ".join(
            "%s=%d" % (k, v) for k, v in sorted(stats.items())))
    lines.append("")

    titles = {
        "read": "Probe READ: line-number prefixes in Read results",
        "write": "Probe WRITE/EDIT: JSON overhead and content composition",
        "bash": "Probe BASH: gzip compressibility of shell output",
        "final": "Probe FINAL TEXT: structure of last-call-of-turn replies",
    }
    for probe in probes:
        rows = out[probe]
        lines.append("## " + titles[probe])
        lines.append("")
        if not rows:
            lines.append("No rows measured.")
            lines.append("")
            continue
        lines.append(SUMMARIZERS[probe](rows))
        lines.append("")
        for spec, ex in extras[probe]:
            lines.append("### Extrapolation: %s" % spec[4])
            lines.append("")
            nz = sum(1 for r in rows if spec[1](r) > 0)
            lines.append("Priced on the **%s** side. %s of %s sampled items "
                         "contribute (%s); an estimate resting on few items is "
                         "noisy."
                         % (spec[3], fmt_int(nz), fmt_int(len(rows)),
                            fmt(nz / float(len(rows)), 3) if rows else "-"))
            lines.append("")
            by_agent = defaultdict(lambda: [0, 0, 0.0, 0.0, 0.0, 0.0])
            for r in ex:
                a = by_agent[r["agent"]]
                a[0] += r["n_items"]
                a[1] += r["population_chars"]
                a[2] += r["wasted_chars"] or 0.0
                a[3] += r["wasted_tokens"] or 0.0
                a[4] += r["usd"] or 0.0
                if r["usd"] is None:
                    a[5] += r["wasted_tokens"] or 0.0
            tbl = []
            tot = [0, 0, 0.0, 0.0, 0.0, 0.0]
            for agent in sorted(by_agent):
                a = by_agent[agent]
                for i in range(6):
                    tot[i] += a[i]
                tbl.append([agent, fmt_int(a[0]), fmt_int(a[1]),
                            fmt_int(a[2]), fmt_int(a[3]), fmt_usd(a[4]),
                            fmt((a[5] / a[3]) if a[3] else 0, 3)])
            tbl.append(["**all**", fmt_int(tot[0]), fmt_int(tot[1]),
                        fmt_int(tot[2]), fmt_int(tot[3]), fmt_usd(tot[4]),
                        fmt((tot[5] / tot[3]) if tot[3] else 0, 3)])
            lines.append(md_table(
                ["agent", "population items", "population chars",
                 "extrapolated chars", "extrapolated tokens", "USD",
                 "unpriced token share"], tbl))

            top = sorted([r for r in ex if r["usd"]],
                         key=lambda r: -r["usd"])[:10]
            if top:
                lines.append("")
                lines.append("Top models by extrapolated USD:")
                lines.append("")
                lines.append(md_table(
                    ["agent", "model", "population chars", "share",
                     "extrapolated tokens", "USD/1M", "USD"],
                    [[r["agent"], r["model"], fmt_int(r["population_chars"]),
                      fmt(r["sample_share"], 4), fmt_int(r["wasted_tokens"]),
                      fmt(r["price_usd_per_mtok"], 2), fmt_usd(r["usd"])]
                     for r in top]))
            lines.append("")

    lines.append("## Assumptions")
    lines.append("")
    lines.append(ASSUMPTIONS)
    lines.append("")

    path = os.path.join(args.results, "PROBES.md")
    with open(path, "w") as fh:
        fh.write("\n".join(lines))
    print("wrote %s" % path)


if __name__ == "__main__":
    sys.exit(main())
