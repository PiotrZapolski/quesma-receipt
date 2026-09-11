#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_ledger - flatten SWE-chat agent transcripts into flat Parquet tables.

Run with:
    uv run --with duckdb --with orjson --with pyarrow analysis/build_ledger.py \
        --sessions analysis/sample_sessions.txt --out analysis/ledger_sample --workers 2

Extraction only. Nothing is analysed here.
Python 3.9 compatible.
"""

from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import multiprocessing as mp
import os
import re
import sys
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta

import orjson
import pyarrow as pa
import pyarrow.parquet as pq

# --------------------------------------------------------------------------
# paths / constants
# --------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_JSON = os.path.join(ROOT, "metadata", "sessions.json")

AGENTS = ("claude_code", "codex", "opencode", "cursor")

FLUSH_ROWS = 50000
TEXT_HEAD = 300
CMD_HEAD = 500
ERR_HEAD = 200

# --------------------------------------------------------------------------
# agent normalization
# --------------------------------------------------------------------------

_AGENT_MAP = {
    "claude code": "claude_code",
    "claude-code": "claude_code",
    "claude_code": "claude_code",
    "codex": "codex",
    "codex cli": "codex",
    "opencode": "opencode",
    "cursor": "cursor",
}


def normalize_agent(raw):
    if not raw:
        return None
    return _AGENT_MAP.get(str(raw).strip().lower())


# --------------------------------------------------------------------------
# schemas
# --------------------------------------------------------------------------

_S = pa.string()
_I64 = pa.int64()
_I32 = pa.int32()
_B = pa.bool_()
_TS = pa.timestamp("ms")

CALLS_SCHEMA = pa.schema(
    [
        ("session_id", _S), ("agent", _S), ("repo", _S), ("seq", _I32),
        ("ts", _TS), ("msg_id", _S), ("request_id", _S), ("parent_id", _S),
        ("is_sidechain", _B), ("model", _S), ("harness_version", _S),
        ("stop_reason", _S), ("speed", _S), ("service_tier", _S),
        ("input_tokens", _I64), ("cache_read_tokens", _I64),
        ("cache_create_tokens", _I64), ("cache_create_5m", _I64),
        ("cache_create_1h", _I64), ("output_tokens", _I64),
        ("reasoning_tokens", _I64), ("context_window", _I64),
        ("n_text_chars", _I64), ("n_thinking_chars", _I64),
        ("n_thinking_blocks", _I32), ("n_tool_uses", _I32),
        ("text_head", _S), ("cwd", _S), ("git_branch", _S), ("timezone", _S),
    ]
)

TOOLS_SCHEMA = pa.schema(
    [
        ("session_id", _S), ("agent", _S), ("repo", _S), ("seq", _I32),
        ("msg_id", _S), ("ts", _TS), ("tool_use_id", _S), ("tool_name", _S),
        ("tool_kind", _S), ("file_path_raw", _S), ("file_path", _S),
        ("patched_files", _S), ("command_head", _S), ("input_chars", _I64),
        ("old_string_chars", _I64), ("new_string_chars", _I64),
        ("content_chars", _I64), ("read_offset", _I64), ("read_limit", _I64),
        ("result_chars", _I64), ("result_hash", _S), ("is_error", _B),
        ("error_head", _S), ("result_ts", _TS), ("result_latency_ms", _I64),
        ("is_interrupted", _B),
    ]
)

TURNS_SCHEMA = pa.schema(
    [
        ("session_id", _S), ("agent", _S), ("repo", _S), ("seq", _I32),
        ("ts", _TS), ("prompt_id", _S), ("text", _S), ("chars", _I64),
        ("human_chars", _I64), ("is_meta", _B), ("is_interrupt", _B),
        ("is_slash_command", _B), ("has_system_reminder", _B),
    ]
)

EVENTS_SCHEMA = pa.schema(
    [
        ("session_id", _S), ("agent", _S), ("repo", _S), ("seq", _I32),
        ("ts", _TS), ("event_type", _S), ("subtype", _S), ("value", _S),
        ("payload_chars", _I64),
    ]
)

SCHEMAS = {
    "calls": CALLS_SCHEMA,
    "tool_calls": TOOLS_SCHEMA,
    "user_turns": TURNS_SCHEMA,
    "events": EVENTS_SCHEMA,
}
TABLES = ("calls", "tool_calls", "user_turns", "events")

_DEFAULTS = {}
for _t, _sch in SCHEMAS.items():
    _DEFAULTS[_t] = dict((n, None) for n in _sch.names)


def new_row(table, session_id, agent, repo, seq):
    r = dict(_DEFAULTS[table])
    r["session_id"] = session_id
    r["agent"] = agent
    r["repo"] = repo
    r["seq"] = seq
    return r


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------


def parse_iso(value):
    """Parse '2026-04-24T21:13:53.677Z' style stamps without strptime cost."""
    if not value or not isinstance(value, str) or len(value) < 19:
        return None
    try:
        y = int(value[0:4]); mo = int(value[5:7]); d = int(value[8:10])
        h = int(value[11:13]); mi = int(value[14:16]); s = int(value[17:19])
        us = 0
        if len(value) > 20 and value[19] == ".":
            frac = ""
            i = 20
            while i < len(value) and value[i].isdigit():
                frac += value[i]
                i += 1
            frac = (frac + "000000")[:6]
            us = int(frac)
        return datetime(y, mo, d, h, mi, s, us)
    except Exception:
        return None


_EPOCH = datetime(1970, 1, 1)


def parse_epoch_ms(value):
    if value is None:
        return None
    try:
        v = float(value)
    except Exception:
        return None
    if v <= 0:
        return None
    if v > 1e12:            # milliseconds
        v = v / 1000.0
    return _EPOCH + timedelta(seconds=v)


def as_int(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except Exception:
        return None


def imax(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return a if a > b else b


def head(text, n):
    if text is None:
        return None
    if len(text) > n:
        return text[:n]
    return text


def sha1(text):
    if text is None:
        return None
    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()


def jdump(obj):
    if obj is None:
        return None
    try:
        return orjson.dumps(obj).decode("utf-8")
    except Exception:
        return str(obj)


def payload_len(obj):
    if obj is None:
        return 0
    if isinstance(obj, str):
        return len(obj)
    try:
        return len(orjson.dumps(obj))
    except Exception:
        return len(str(obj))


# --------------------------------------------------------------------------
# harness-tag stripping (human_chars)
# --------------------------------------------------------------------------

_HARNESS_TAGS = (
    "system-reminder|command-name|command-message|command-args|"
    "local-command-stdout|local-command-stderr|local-command-out|"
    "manually_attached_skills|attached_files|attached_selection|code_selection|"
    "git_diff_from_branch_to_main|git_diff|environment_details|environment_context|"
    "user_instructions|ide_selection|ide_opened_file|timestamp|user_rules|open_files|"
    "linter_errors|current_file|recently_viewed_files|cursor_rules|additional_data|"
    "custom_instructions|project_layout|attachments|selected_code|snippet|"
    "tool_output|function_results|task_reminder"
)

_RE_PAIRED = re.compile(r"<(" + _HARNESS_TAGS + r")(\s[^>]*)?>.*?</\1>", re.S)
_RE_BARE = re.compile(r"</?(" + _HARNESS_TAGS + r")(\s[^>]*)?/?>", re.S)
_RE_INTERRUPT = re.compile(r"\[Request interrupted by[^\]]*\]")
_RE_USER_QUERY = re.compile(r"<user_query>(.*?)</user_query>", re.S)
_RE_WS = re.compile(r"\s+")


def human_text(text):
    """Text with harness injections removed. Cursor wraps the real prompt in
    <user_query>; when present that block alone is the human part."""
    if not text:
        return ""
    hits = _RE_USER_QUERY.findall(text)
    if hits:
        return "\n".join(h.strip() for h in hits).strip()
    out = _RE_PAIRED.sub(" ", text)
    out = _RE_BARE.sub(" ", out)
    out = _RE_INTERRUPT.sub(" ", out)
    return _RE_WS.sub(" ", out).strip()


# --------------------------------------------------------------------------
# tool kind normalization
# --------------------------------------------------------------------------

_KIND = {
    "read": "read", "view": "read", "read_file": "read", "readfile": "read",
    "file_read": "read", "notebookread": "read", "readlints": "read",
    "readmanyfiles": "read", "read_many_files": "read", "already_read_file": "read",
    "edit": "edit", "multiedit": "edit", "notebookedit": "edit",
    "str_replace": "edit", "strreplace": "edit", "str_replace_editor": "edit",
    "apply_patch": "edit", "applypatch": "edit", "patch": "edit",
    "edit_file": "edit", "update_file": "edit", "editfile": "edit",
    "write": "write", "write_file": "write", "writefile": "write",
    "create": "write", "create_file": "write", "file_write": "write",
    "delete": "write", "remove": "write", "move": "write", "rename": "write",
    "bash": "bash", "shell": "bash", "shell_command": "bash",
    "exec_command": "bash", "exec": "bash", "run_command": "bash",
    "terminal": "bash", "runterminalcmd": "bash", "awaitshell": "bash",
    "write_stdin": "bash", "send_input": "bash", "kill_shell": "bash",
    "killshell": "bash", "bashoutput": "bash", "runcommand": "bash",
    "glob": "glob", "ls": "glob", "list": "glob", "listdir": "glob",
    "list_dir": "glob", "find": "glob", "findfiles": "glob",
    "grep": "grep", "search": "grep", "rg": "grep", "ripgrep": "grep",
    "codesearch": "grep", "searchtext": "grep", "grep_search": "grep",
    "webfetch": "web", "web_fetch": "web", "fetch": "web",
    "websearch": "web", "web_search": "web", "web_search_call": "web",
    "browser": "web", "open_url": "web",
    "task": "task", "agent": "task", "spawn_agent": "task",
    "wait_agent": "task", "close_agent": "task", "dispatch_agent": "task",
    "subagent": "task", "collab": "task",
    "todowrite": "todo", "todoread": "todo", "todo": "todo",
    "update_plan": "todo", "createplan": "todo", "exitplanmode": "todo",
    "updatetodos": "todo", "update_goal": "todo", "create_goal": "todo",
    "get_goal": "todo",
}


def tool_kind(name):
    if not name:
        return "other"
    low = name.strip().lower()
    if low.startswith("mcp__") or low.startswith("mcp_"):
        return "mcp"
    if low in ("callmcptool", "call_mcp_tool", "read_mcp_resource",
               "list_mcp_resources", "use_mcp_tool"):
        return "mcp"
    return _KIND.get(low, "other")


# --------------------------------------------------------------------------
# file path helpers
# --------------------------------------------------------------------------

_PATH_KEYS = ("filePath", "file_path", "path", "target_file", "notebook_path",
              "filename", "file", "absolute_path", "target_directory")


def pick_path(inp):
    if not isinstance(inp, dict):
        return None
    for k in _PATH_KEYS:
        v = inp.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def rel_path(raw, bases):
    if not raw:
        return raw
    for b in bases:
        if b and raw.startswith(b):
            rest = raw[len(b):]
            if rest.startswith("/"):
                return rest[1:] or "."
            if rest == "":
                return "."
    return raw


_RE_PATCH_FILE = re.compile(
    r"^\*\*\*\s+(Update|Add|Delete)\s+File:\s*(.+?)\s*$", re.M)


def patch_files(text):
    """Return (ops, paths) for an apply_patch style payload."""
    if not text or "*** " not in text:
        return ([], [])
    ops = []
    paths = []
    for m in _RE_PATCH_FILE.finditer(text):
        ops.append(m.group(1))
        paths.append(m.group(2))
    return (ops, paths)


def apply_patch_info(row, text, bases):
    ops, paths = patch_files(text)
    if not paths:
        return False
    row["patched_files"] = jdump(paths)
    row["file_path_raw"] = paths[0]
    row["file_path"] = rel_path(paths[0], bases)
    if ops and all(o == "Add" for o in ops):
        row["tool_kind"] = "write"
    else:
        row["tool_kind"] = "edit"
    return True


# --------------------------------------------------------------------------
# parquet part writer (one per worker process)
# --------------------------------------------------------------------------


class PartWriter(object):
    def __init__(self, out_dir, worker_id, flush_rows=FLUSH_ROWS):
        self.out_dir = out_dir
        self.worker_id = worker_id
        self.flush_rows = flush_rows
        self.buf = dict((t, []) for t in TABLES)
        self.part_no = dict((t, 0) for t in TABLES)
        self.total = dict((t, 0) for t in TABLES)
        for t in TABLES:
            d = os.path.join(out_dir, t)
            if not os.path.isdir(d):
                try:
                    os.makedirs(d)
                except OSError:
                    pass
        d = os.path.join(out_dir, "errors")
        if not os.path.isdir(d):
            try:
                os.makedirs(d)
            except OSError:
                pass
        self.err_path = os.path.join(d, "part-%s.jsonl" % worker_id)
        self.err_fh = None
        self.n_errors = 0

    def add(self, table, row):
        b = self.buf[table]
        b.append(row)
        self.total[table] += 1
        if len(b) >= self.flush_rows:
            self.flush(table)

    def extend(self, table, rows):
        for r in rows:
            self.add(table, r)

    def flush(self, table):
        rows = self.buf[table]
        if not rows:
            return
        tbl = pa.Table.from_pylist(rows, schema=SCHEMAS[table])
        name = "part-%s-%d.parquet" % (self.worker_id, self.part_no[table])
        pq.write_table(tbl, os.path.join(self.out_dir, table, name),
                       compression="zstd")
        self.part_no[table] += 1
        self.buf[table] = []

    def error(self, session_id, line_no, exc):
        self.n_errors += 1
        if self.err_fh is None:
            self.err_fh = open(self.err_path, "a")
        self.err_fh.write(json.dumps({
            "session_id": session_id,
            "line_no": line_no,
            "exception": "%s: %s" % (type(exc).__name__, exc),
        }) + "\n")

    def close(self):
        for t in TABLES:
            self.flush(t)
        if self.err_fh is not None:
            self.err_fh.close()
            self.err_fh = None


# --------------------------------------------------------------------------
# per-session parse context
# --------------------------------------------------------------------------


class Ctx(object):
    """Accumulates the rows of one session, then hands them to the writer."""

    __slots__ = ("sid", "agent", "repo", "calls", "tools", "turns", "events",
                 "tool_by_id", "n_lines", "n_bad")

    def __init__(self, sid, agent, repo):
        self.sid = sid
        self.agent = agent
        self.repo = repo
        self.calls = OrderedDict()
        self.tools = []
        self.turns = []
        self.events = []
        self.tool_by_id = {}
        self.n_lines = 0
        self.n_bad = 0

    def row(self, table, seq):
        return new_row(table, self.sid, self.agent, self.repo, seq)

    def add_tool(self, row):
        self.tools.append(row)
        tid = row.get("tool_use_id")
        if tid:
            self.tool_by_id[tid] = row
        return row

    def event(self, seq, ts, etype, subtype=None, value=None, payload=0):
        r = self.row("events", seq)
        r["ts"] = ts
        r["event_type"] = etype
        r["subtype"] = None if subtype is None else str(subtype)
        r["value"] = None if value is None else head(str(value), 300)
        r["payload_chars"] = payload
        self.events.append(r)
        return r

    def add_turn(self, seq, ts, prompt_id, text, is_meta=None):
        if text is None:
            text = ""
        r = self.row("user_turns", seq)
        r["ts"] = ts
        r["prompt_id"] = prompt_id
        r["text"] = text
        r["chars"] = len(text)
        hum = human_text(text)
        r["human_chars"] = len(hum)
        r["has_system_reminder"] = "<system-reminder>" in text
        r["is_interrupt"] = bool(_RE_INTERRUPT.search(text))
        stripped = text.lstrip()
        r["is_slash_command"] = bool(
            stripped.startswith("/") and not stripped.startswith("//")
        ) or ("<command-name>" in text)
        if is_meta is None:
            r["is_meta"] = bool(len(text) > 0 and len(hum) == 0)
        else:
            r["is_meta"] = bool(is_meta) or bool(len(text) > 0 and len(hum) == 0)
        self.turns.append(r)
        return r

    def emit(self, writer):
        writer.extend("calls", list(self.calls.values()))
        writer.extend("tool_calls", self.tools)
        writer.extend("user_turns", self.turns)
        writer.extend("events", self.events)


def fill_result(ctx, tool_use_id, result_text, is_error, result_ts):
    row = ctx.tool_by_id.get(tool_use_id)
    if row is None:
        return None
    if result_text is None:
        result_text = ""
    row["result_chars"] = len(result_text)
    row["result_hash"] = sha1(result_text)
    if is_error is not None:
        row["is_error"] = bool(is_error)
    elif row["is_error"] is None:
        row["is_error"] = False
    if row["is_error"]:
        row["error_head"] = head(result_text, ERR_HEAD)
    row["is_interrupted"] = bool(_RE_INTERRUPT.search(result_text))
    if result_ts is not None:
        row["result_ts"] = result_ts
        if row["ts"] is not None:
            delta = (result_ts - row["ts"])
            row["result_latency_ms"] = int(delta.total_seconds() * 1000)
    return row


# --------------------------------------------------------------------------
# claude_code
# --------------------------------------------------------------------------

_CC_TEXTY = ("last-prompt", "progress", "ai-title", "agent-name",
             "custom-title", "pr-link")


def _cc_result_text(content):
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
                    parts.append(jdump(b) or "")
            elif isinstance(b, str):
                parts.append(b)
        return "".join(parts)
    return jdump(content) or ""


def parse_claude_code(path, ctx, writer):
    with open(path, "rb") as fh:
        for seq, raw in enumerate(fh):
            if not raw.strip():
                continue
            ctx.n_lines += 1
            try:
                rec = orjson.loads(raw)
            except Exception as exc:
                ctx.n_bad += 1
                writer.error(ctx.sid, seq, exc)
                continue
            try:
                _cc_line(ctx, rec, seq)
            except Exception as exc:
                ctx.n_bad += 1
                writer.error(ctx.sid, seq, exc)


def _cc_line(ctx, rec, seq):
    if not isinstance(rec, dict):
        return
    typ = rec.get("type")
    ts = parse_iso(rec.get("timestamp"))
    cwd = rec.get("cwd")
    bases = (cwd,) if cwd else ()

    if typ == "assistant":
        msg = rec.get("message") or {}
        mid = msg.get("id")
        key = mid if mid else ("__noid__", seq)
        row = ctx.calls.get(key)
        if row is None:
            row = ctx.row("calls", seq)
            row["ts"] = ts
            row["msg_id"] = mid
            row["request_id"] = rec.get("requestId")
            row["parent_id"] = rec.get("parentUuid")
            row["is_sidechain"] = bool(rec.get("isSidechain"))
            row["cwd"] = cwd
            row["git_branch"] = rec.get("gitBranch")
            row["harness_version"] = rec.get("version")
            row["n_text_chars"] = 0
            row["n_thinking_chars"] = 0
            row["n_thinking_blocks"] = 0
            row["n_tool_uses"] = 0
            ctx.calls[key] = row
        if row["request_id"] is None:
            row["request_id"] = rec.get("requestId")
        row["model"] = msg.get("model") or row["model"]
        if msg.get("stop_reason"):
            row["stop_reason"] = msg.get("stop_reason")
        usage = msg.get("usage") or {}
        if usage:
            row["service_tier"] = usage.get("service_tier") or row["service_tier"]
            row["input_tokens"] = imax(row["input_tokens"],
                                       as_int(usage.get("input_tokens")))
            row["output_tokens"] = imax(row["output_tokens"],
                                        as_int(usage.get("output_tokens")))
            row["cache_read_tokens"] = imax(
                row["cache_read_tokens"], as_int(usage.get("cache_read_input_tokens")))
            row["cache_create_tokens"] = imax(
                row["cache_create_tokens"],
                as_int(usage.get("cache_creation_input_tokens")))
            cc = usage.get("cache_creation") or {}
            if isinstance(cc, dict):
                row["cache_create_5m"] = imax(
                    row["cache_create_5m"],
                    as_int(cc.get("ephemeral_5m_input_tokens")))
                row["cache_create_1h"] = imax(
                    row["cache_create_1h"],
                    as_int(cc.get("ephemeral_1h_input_tokens")))
        sp = msg.get("speed")
        if sp is None:
            sp = usage.get("speed") if isinstance(usage, dict) else None
        if sp is not None:
            row["speed"] = str(sp)

        for blk in (msg.get("content") or []):
            if not isinstance(blk, dict):
                continue
            bt = blk.get("type")
            if bt == "text":
                txt = blk.get("text") or ""
                row["n_text_chars"] += len(txt)
                if not row["text_head"] and txt:
                    row["text_head"] = head(txt, TEXT_HEAD)
            elif bt == "thinking":
                row["n_thinking_chars"] += len(blk.get("thinking") or "")
                row["n_thinking_blocks"] += 1
            elif bt in ("tool_use", "server_tool_use"):
                row["n_tool_uses"] += 1
                _cc_tool_use(ctx, blk, seq, mid, ts, bases)
            elif bt == "redacted_thinking":
                row["n_thinking_blocks"] += 1
        return

    if typ == "user":
        msg = rec.get("message") or {}
        content = msg.get("content")
        texts = []
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                bt = blk.get("type")
                if bt == "text":
                    texts.append(blk.get("text") or "")
                elif bt == "tool_result":
                    rtext = _cc_result_text(blk.get("content"))
                    fill_result(ctx, blk.get("tool_use_id"), rtext,
                                blk.get("is_error"), ts)
                elif bt == "image":
                    ctx.event(seq, ts, "user_image", None, None,
                              payload_len(blk))
        if texts:
            joined = "\n".join(texts)
            ctx.add_turn(seq, ts, rec.get("uuid"), joined,
                         is_meta=bool(rec.get("isMeta")))
        return

    if typ == "system":
        meta = rec.get("compactMetadata") or {}
        value = meta.get("trigger") if meta else rec.get("level")
        ctx.event(seq, ts, "system", rec.get("subtype"), value,
                  payload_len(rec.get("content")))
        return

    if typ == "attachment":
        att = rec.get("attachment") or {}
        ctx.event(seq, ts, "attachment", att.get("type"), None,
                  payload_len(att))
        return

    if typ == "file-history-snapshot":
        snap = rec.get("snapshot") or {}
        backups = snap.get("trackedFileBackups") or {}
        try:
            n = len(backups)
        except Exception:
            n = 0
        ctx.event(seq, ts, "file-history-snapshot", None, str(n),
                  payload_len(snap))
        return

    if typ == "permission-mode":
        ctx.event(seq, ts, "permission-mode", None, rec.get("permissionMode"), 0)
        return

    if typ == "mode":
        ctx.event(seq, ts, "mode", None, rec.get("mode"), 0)
        return

    if typ == "queue-operation":
        ctx.event(seq, ts, "queue-operation", None, rec.get("operation"),
                  payload_len(rec.get("content")))
        return

    if typ in _CC_TEXTY:
        payload = 0
        for k in ("lastPrompt", "content", "title", "message", "name", "url"):
            if rec.get(k) is not None:
                payload = payload_len(rec.get(k))
                break
        if payload == 0:
            payload = payload_len(rec) - 0
        ctx.event(seq, ts, typ, None, None, payload)
        return

    ctx.event(seq, ts, typ or "unknown", None, None, payload_len(rec))


def _cc_tool_use(ctx, blk, seq, mid, ts, bases):
    inp = blk.get("input")
    if not isinstance(inp, dict):
        inp = {}
    name = blk.get("name")
    row = ctx.row("tool_calls", seq)
    row["msg_id"] = mid
    row["ts"] = ts
    row["tool_use_id"] = blk.get("id")
    row["tool_name"] = name
    row["tool_kind"] = tool_kind(name)
    row["input_chars"] = payload_len(inp)
    _fill_tool_input(row, inp, bases)
    ctx.add_tool(row)


_CMD_KEYS = ("command", "cmd", "script", "shell_command", "query",
             "search_term", "chars", "stdin")
_OLD_KEYS = ("old_string", "oldString", "old_str")
_NEW_KEYS = ("new_string", "newString", "new_str")
_CONTENT_KEYS = ("content", "contents", "file_text", "new_content", "text")
_PATCH_KEYS = ("patchText", "patch", "input", "diff")


def _first(inp, keys):
    for k in keys:
        v = inp.get(k)
        if v is not None:
            return v
    return None


def _fill_tool_input(row, inp, bases):
    """Common handling of a tool-call input dict."""
    raw = pick_path(inp)
    if raw:
        row["file_path_raw"] = raw
        row["file_path"] = rel_path(raw, bases)

    cmd = _first(inp, _CMD_KEYS)
    if isinstance(cmd, list):
        cmd = " ".join(str(c) for c in cmd)
    if isinstance(cmd, str) and cmd:
        row["command_head"] = head(cmd, CMD_HEAD)
        if "apply_patch" in cmd:
            apply_patch_info(row, cmd, bases)

    old = _first(inp, _OLD_KEYS)
    if isinstance(old, str):
        row["old_string_chars"] = len(old)
    new = _first(inp, _NEW_KEYS)
    if isinstance(new, str):
        row["new_string_chars"] = len(new)
    cont = _first(inp, _CONTENT_KEYS)
    if isinstance(cont, str):
        row["content_chars"] = len(cont)

    row["read_offset"] = as_int(inp.get("offset"))
    row["read_limit"] = as_int(inp.get("limit"))

    patch = _first(inp, _PATCH_KEYS)
    if isinstance(patch, str) and "*** " in patch:
        apply_patch_info(row, patch, bases)
        if row["content_chars"] is None:
            row["content_chars"] = len(patch)


# --------------------------------------------------------------------------
# codex
# --------------------------------------------------------------------------


def _cx_text(blocks):
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


def _cx_output_text(out):
    if out is None:
        return ""
    if isinstance(out, str):
        return out
    if isinstance(out, list):
        return _cx_text(out)
    if isinstance(out, dict):
        for k in ("output", "text", "content"):
            v = out.get(k)
            if isinstance(v, str):
                return v
            if isinstance(v, list):
                return _cx_text(v)
        return jdump(out) or ""
    return str(out)


class _CxState(object):
    __slots__ = ("model", "timezone", "cwd", "version", "seq0",
                 "n_text", "n_reason", "n_tools", "text_head", "has_tool",
                 "last_ts", "echo_pool", "echo_rows")

    def __init__(self):
        self.model = None
        self.timezone = None
        self.cwd = None
        self.version = None
        self.reset(0)
        self.echo_pool = {}
        self.echo_rows = []

    def reset(self, seq):
        self.seq0 = seq
        self.n_text = 0
        self.n_reason = 0
        self.n_tools = 0
        self.text_head = None
        self.has_tool = False
        self.last_ts = None


def parse_codex(path, ctx, writer):
    st = _CxState()
    with open(path, "rb") as fh:
        for seq, raw in enumerate(fh):
            if not raw.strip():
                continue
            ctx.n_lines += 1
            try:
                rec = orjson.loads(raw)
            except Exception as exc:
                ctx.n_bad += 1
                writer.error(ctx.sid, seq, exc)
                continue
            try:
                _cx_line(ctx, rec, seq, st)
            except Exception as exc:
                ctx.n_bad += 1
                writer.error(ctx.sid, seq, exc)

    # fallback: sessions from older codex builds carry no token_count events
    if not ctx.calls:
        _cx_fallback_calls(ctx, st)

    # drop response_item user echoes that duplicate an event_msg user_message
    keep = []
    for row in ctx.turns:
        if row.get("prompt_id") == "__echo__":
            txt = row["text"]
            n = st.echo_pool.get(txt, 0)
            if n > 0:
                st.echo_pool[txt] = n - 1
                continue
            row["prompt_id"] = None
        keep.append(row)
    ctx.turns = keep


def _cx_fallback_calls(ctx, st):
    """No token_count events: one call row per assistant message item."""
    for seq, ts, nchars, thead in st.echo_rows:
        row = ctx.row("calls", seq)
        row["ts"] = ts
        row["model"] = st.model
        row["timezone"] = st.timezone
        row["cwd"] = st.cwd
        row["harness_version"] = st.version
        row["n_text_chars"] = nchars
        row["n_thinking_chars"] = 0
        row["n_thinking_blocks"] = 0
        row["n_tool_uses"] = 0
        row["text_head"] = thead
        ctx.calls[("fallback", seq)] = row


def _cx_line(ctx, rec, seq, st):
    if not isinstance(rec, dict):
        return
    typ = rec.get("type")
    ts = parse_iso(rec.get("timestamp"))
    payload = rec.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    bases = (st.cwd,) if st.cwd else ()

    if typ == "session_meta":
        st.cwd = payload.get("cwd") or st.cwd
        st.version = payload.get("cli_version") or st.version
        bi = payload.get("base_instructions") or {}
        chars = payload_len(bi.get("text") if isinstance(bi, dict) else bi)
        ctx.event(seq, ts or parse_iso(payload.get("timestamp")),
                  "session_meta", payload.get("model_provider"),
                  payload.get("cli_version"), chars)
        return

    if typ == "turn_context":
        st.model = payload.get("model") or st.model
        st.timezone = payload.get("timezone") or st.timezone
        st.cwd = payload.get("cwd") or st.cwd
        sp = payload.get("sandbox_policy") or {}
        cm = payload.get("collaboration_mode") or {}
        settings = cm.get("settings") if isinstance(cm, dict) else None
        effort = None
        if isinstance(settings, dict):
            effort = settings.get("reasoning_effort")
        if effort is None:
            effort = payload.get("effort")
        ctx.event(seq, ts, "turn_context",
                  sp.get("type") if isinstance(sp, dict) else None,
                  "model=%s;approval=%s;effort=%s" % (
                      st.model, payload.get("approval_policy"), effort),
                  payload_len(payload))
        return

    if typ == "compacted":
        ctx.event(seq, ts, "compacted", None, None, payload_len(rec))
        return

    if typ == "response_item":
        _cx_response_item(ctx, payload, seq, ts, st, bases)
        return

    if typ == "event_msg":
        _cx_event_msg(ctx, payload, seq, ts, st)
        return

    ctx.event(seq, ts, typ or "unknown", None, None, payload_len(rec))


def _cx_response_item(ctx, payload, seq, ts, st, bases):
    ptype = payload.get("type")

    if ptype == "message":
        role = payload.get("role")
        text = _cx_text(payload.get("content"))
        if role == "assistant":
            st.n_text += len(text)
            if st.text_head is None and text:
                st.text_head = head(text, TEXT_HEAD)
            st.echo_rows.append((seq, ts, len(text), head(text, TEXT_HEAD)))
        elif role == "user":
            row = ctx.add_turn(seq, ts, "__echo__", text)
            row["prompt_id"] = "__echo__"
        else:
            ctx.event(seq, ts, "response_item", "message:%s" % role, None,
                      len(text))
        return

    if ptype == "reasoning":
        n = 0
        for key in ("summary", "content"):
            n += len(_cx_text(payload.get(key)))
        st.n_reason += n
        return

    if ptype in ("function_call", "custom_tool_call", "local_shell_call",
                 "tool_search_call", "web_search_call"):
        st.n_tools += 1
        st.has_tool = True
        name = payload.get("name")
        if ptype == "web_search_call":
            name = name or "web_search"
        elif ptype == "tool_search_call":
            name = name or "tool_search"
        elif ptype == "local_shell_call":
            name = name or "local_shell"
        row = ctx.row("tool_calls", seq)
        row["ts"] = ts
        row["tool_use_id"] = payload.get("call_id") or payload.get("id")
        row["tool_name"] = name
        row["tool_kind"] = tool_kind(name)
        args = payload.get("arguments")
        if args is None:
            args = payload.get("input")
        if args is None:
            args = payload.get("action") or payload.get("query")
        row["input_chars"] = payload_len(args)
        inp = None
        if isinstance(args, str):
            s = args.lstrip()
            if s.startswith("{"):
                try:
                    inp = orjson.loads(args)
                except Exception:
                    inp = None
            if inp is None:
                # raw text payload (apply_patch, exec script, search query)
                if "*** " in args:
                    apply_patch_info(row, args, bases)
                    row["content_chars"] = len(args)
                else:
                    row["command_head"] = head(args, CMD_HEAD)
        elif isinstance(args, dict):
            inp = args
        if isinstance(inp, dict):
            _fill_tool_input(row, inp, bases)
        ctx.add_tool(row)
        return

    if ptype in ("function_call_output", "custom_tool_call_output",
                 "local_shell_call_output", "tool_search_call_output"):
        text = _cx_output_text(payload.get("output"))
        is_err = None
        out = payload.get("output")
        if isinstance(out, dict) and out.get("success") is not None:
            is_err = not bool(out.get("success"))
        fill_result(ctx, payload.get("call_id"), text, is_err, ts)
        return

    ctx.event(seq, ts, "response_item", ptype, None, payload_len(payload))


def _cx_event_msg(ctx, payload, seq, ts, st):
    ptype = payload.get("type")

    if ptype == "token_count":
        info = payload.get("info")
        if not isinstance(info, dict):
            # rate-limit-only heartbeat, not an API response
            ctx.event(seq, ts, "event_msg", "token_count_norate", None, 0)
            return
        last = info.get("last_token_usage") or {}
        row = ctx.row("calls", st.seq0)
        row["ts"] = ts
        row["model"] = st.model
        row["timezone"] = st.timezone
        row["cwd"] = st.cwd
        row["harness_version"] = st.version
        row["input_tokens"] = as_int(last.get("input_tokens"))
        row["cache_read_tokens"] = as_int(last.get("cached_input_tokens"))
        row["output_tokens"] = as_int(last.get("output_tokens"))
        row["reasoning_tokens"] = as_int(last.get("reasoning_output_tokens"))
        row["context_window"] = as_int(info.get("model_context_window"))
        row["n_text_chars"] = st.n_text
        row["n_thinking_chars"] = st.n_reason
        row["n_thinking_blocks"] = 1 if st.n_reason else 0
        row["n_tool_uses"] = st.n_tools
        row["text_head"] = st.text_head
        row["stop_reason"] = "tool_use" if st.has_tool else "end_turn"
        ctx.calls[("tc", seq)] = row
        st.reset(seq + 1)
        return

    if ptype == "user_message":
        msg = payload.get("message")
        if not isinstance(msg, str):
            msg = jdump(msg) or ""
        ctx.add_turn(seq, ts, None, msg)
        st.echo_pool[msg] = st.echo_pool.get(msg, 0) + 1
        return

    if ptype == "agent_message":
        msg = payload.get("message")
        ctx.event(seq, ts, "event_msg", "agent_message", None, payload_len(msg))
        return

    value = None
    for k in ("reason", "status", "call_id", "command", "name"):
        v = payload.get(k)
        if isinstance(v, (str, int, float)):
            value = v
            break
    ctx.event(seq, ts, "event_msg", ptype, value, payload_len(payload))


# --------------------------------------------------------------------------
# opencode
# --------------------------------------------------------------------------


def parse_opencode(path, ctx, writer):
    with open(path, "rb") as fh:
        blob = fh.read()
    ctx.n_lines += 1
    doc = None
    try:
        doc = orjson.loads(blob)
    except Exception:
        doc = None

    info = {}
    messages = None
    if isinstance(doc, dict):
        if isinstance(doc.get("messages"), list):
            info = doc.get("info") or {}
            if not isinstance(info, dict):
                info = {}
            messages = doc["messages"]
        elif "info" in doc and "parts" in doc:
            messages = [doc]
    if messages is None:
        # JSONL variant: one {info, parts} object per line
        messages = []
        for lineno, raw in enumerate(blob.splitlines()):
            if not raw.strip():
                continue
            try:
                obj = orjson.loads(raw)
            except Exception as exc:
                ctx.n_bad += 1
                writer.error(ctx.sid, lineno, exc)
                continue
            if isinstance(obj, dict):
                messages.append(obj)

    version = info.get("version")
    root = None
    directory = info.get("directory")

    for seq, msg in enumerate(messages):
        try:
            if not isinstance(msg, dict) or "info" not in msg:
                ctx.event(seq, None, "unparsed_message", None, None,
                          payload_len(msg))
                continue
            root = _oc_message(ctx, msg, seq, version, directory, root)
        except Exception as exc:
            ctx.n_bad += 1
            writer.error(ctx.sid, seq, exc)


def _oc_tokens(tok):
    if not isinstance(tok, dict):
        return (None, None, None, None, None)
    cache = tok.get("cache") or {}
    if not isinstance(cache, dict):
        cache = {}
    return (as_int(tok.get("input")), as_int(tok.get("output")),
            as_int(tok.get("reasoning")), as_int(cache.get("read")),
            as_int(cache.get("write")))


def _oc_message(ctx, msg, seq, version, directory, root):
    info = msg.get("info") or {}
    if not isinstance(info, dict):
        info = {}
    parts = msg.get("parts")
    if not isinstance(parts, list):
        parts = []
    role = info.get("role")
    tinfo = info.get("time") or {}
    ts = parse_epoch_ms(tinfo.get("created") if isinstance(tinfo, dict) else None)
    path_info = info.get("path") or {}
    cwd = path_info.get("cwd") if isinstance(path_info, dict) else None
    proot = path_info.get("root") if isinstance(path_info, dict) else None
    if proot:
        root = proot
    bases = tuple(b for b in (cwd, root, directory) if b)

    model = info.get("modelID")
    if model is None:
        m = info.get("model")
        if isinstance(m, dict):
            model = m.get("modelID")
    mid = info.get("id")

    if role == "user":
        texts = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            pt = part.get("type")
            if pt == "text":
                texts.append(part.get("text") or "")
            elif pt in ("file", "patch", "agent", "snapshot"):
                ctx.event(seq, ts, "part", pt, None, payload_len(part))
        if texts:
            ctx.add_turn(seq, ts, mid, "\n".join(texts))
        return root

    # assistant (or anything else carrying parts)
    acc = {"text": 0, "reason": 0, "tools": 0, "head": None}
    steps = 0

    def mkcall(tok, reason, cts):
        i, o, r, cr, cw = _oc_tokens(tok)
        row = ctx.row("calls", seq)
        row["ts"] = cts or ts
        row["msg_id"] = mid
        row["parent_id"] = info.get("parentID")
        row["model"] = model
        row["harness_version"] = version
        row["stop_reason"] = reason
        row["input_tokens"] = i
        row["output_tokens"] = o
        row["reasoning_tokens"] = r
        row["cache_read_tokens"] = cr
        row["cache_create_tokens"] = cw
        row["n_text_chars"] = acc["text"]
        row["n_thinking_chars"] = acc["reason"]
        row["n_thinking_blocks"] = 1 if acc["reason"] else 0
        row["n_tool_uses"] = acc["tools"]
        row["text_head"] = acc["head"]
        row["cwd"] = cwd
        return row

    for pi, part in enumerate(parts):
        if not isinstance(part, dict):
            continue
        pt = part.get("type")
        if pt == "text":
            txt = part.get("text") or ""
            acc["text"] += len(txt)
            if acc["head"] is None and txt:
                acc["head"] = head(txt, TEXT_HEAD)
        elif pt == "reasoning":
            acc["reason"] += len(part.get("text") or "")
        elif pt == "tool":
            acc["tools"] += 1
            _oc_tool(ctx, part, seq, mid, bases)
        elif pt == "step-finish":
            pts = None
            tm = part.get("time")
            if isinstance(tm, dict):
                pts = parse_epoch_ms(tm.get("end") or tm.get("start"))
            row = mkcall(part.get("tokens"), part.get("reason"), pts)
            ctx.calls[("step", seq, pi)] = row
            steps += 1
            acc = {"text": 0, "reason": 0, "tools": 0, "head": None}
        elif pt == "step-start":
            continue
        else:
            ctx.event(seq, ts, "part", pt, None, payload_len(part))

    if steps == 0 and role == "assistant":
        completed = None
        if isinstance(tinfo, dict):
            completed = parse_epoch_ms(tinfo.get("completed"))
        row = mkcall(info.get("tokens"), info.get("finish"), completed or ts)
        ctx.calls[("msg", seq)] = row
    elif acc["tools"] or acc["text"] or acc["reason"]:
        # trailing parts after the last step-finish
        row = mkcall(None, info.get("finish"), ts)
        ctx.calls[("tail", seq)] = row
    return root


def _oc_tool(ctx, part, seq, mid, bases):
    state = part.get("state")
    if not isinstance(state, dict):
        state = {}
    inp = state.get("input")
    if isinstance(inp, str):
        try:
            inp = orjson.loads(inp)
        except Exception:
            inp = {"command": inp}
    if not isinstance(inp, dict):
        inp = {}

    name = part.get("tool")
    row = ctx.row("tool_calls", seq)
    row["msg_id"] = mid
    row["tool_use_id"] = part.get("callID") or part.get("id")
    row["tool_name"] = name
    row["tool_kind"] = tool_kind(name)
    row["input_chars"] = payload_len(inp)
    if part.get("filePath") and not inp.get("filePath"):
        inp = dict(inp)
        inp["filePath"] = part.get("filePath")
    _fill_tool_input(row, inp, bases)

    tm = state.get("time")
    start = end = None
    if isinstance(tm, dict):
        start = parse_epoch_ms(tm.get("start"))
        end = parse_epoch_ms(tm.get("end"))
    row["ts"] = start
    status = state.get("status")
    err = state.get("error")
    is_err = (status == "error") or bool(err)
    out = state.get("output")
    if not isinstance(out, str):
        out = jdump(out) if out is not None else ""
    if is_err and isinstance(err, str) and err:
        out = err
    row["result_chars"] = len(out)
    row["result_hash"] = sha1(out)
    row["is_error"] = bool(is_err)
    if is_err:
        row["error_head"] = head(out, ERR_HEAD)
    row["is_interrupted"] = bool(_RE_INTERRUPT.search(out)) or (
        isinstance(err, str) and "abort" in err.lower())
    row["result_ts"] = end
    if start is not None and end is not None:
        row["result_latency_ms"] = int((end - start).total_seconds() * 1000)
    ctx.add_tool(row)


# --------------------------------------------------------------------------
# cursor
# --------------------------------------------------------------------------


def parse_cursor(path, ctx, writer):
    with open(path, "rb") as fh:
        for seq, raw in enumerate(fh):
            if not raw.strip():
                continue
            ctx.n_lines += 1
            try:
                rec = orjson.loads(raw)
            except Exception as exc:
                ctx.n_bad += 1
                writer.error(ctx.sid, seq, exc)
                continue
            try:
                _cu_line(ctx, rec, seq)
            except Exception as exc:
                ctx.n_bad += 1
                writer.error(ctx.sid, seq, exc)


def _cu_blocks(msg):
    if not isinstance(msg, dict):
        return []
    content = msg.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def _cu_line(ctx, rec, seq):
    if not isinstance(rec, dict):
        return
    role = rec.get("role")
    if role is None:
        value = rec.get("status")
        ctx.event(seq, None, rec.get("type") or "unknown", None,
                  rec.get("error") or value, payload_len(rec))
        return

    blocks = _cu_blocks(rec.get("message"))

    if role == "assistant":
        row = ctx.row("calls", seq)
        row["n_text_chars"] = 0
        row["n_thinking_chars"] = 0
        row["n_thinking_blocks"] = 0
        row["n_tool_uses"] = 0
        for blk in blocks:
            bt = blk.get("type")
            if bt == "text":
                txt = blk.get("text") or ""
                row["n_text_chars"] += len(txt)
                if not row["text_head"] and txt:
                    row["text_head"] = head(txt, TEXT_HEAD)
            elif bt == "thinking":
                row["n_thinking_chars"] += len(
                    blk.get("thinking") or blk.get("text") or "")
                row["n_thinking_blocks"] += 1
            elif bt == "tool_use":
                row["n_tool_uses"] += 1
                _cu_tool(ctx, blk, seq)
            elif bt == "tool_result":
                fill_result(ctx, blk.get("tool_use_id") or blk.get("id"),
                            _cc_result_text(blk.get("content")),
                            blk.get("is_error"), None)
        row["stop_reason"] = "tool_use" if row["n_tool_uses"] else "end_turn"
        ctx.calls[("a", seq)] = row
        return

    if role == "user":
        texts = []
        for blk in blocks:
            bt = blk.get("type")
            if bt == "text":
                texts.append(blk.get("text") or "")
            elif bt == "tool_result":
                fill_result(ctx, blk.get("tool_use_id") or blk.get("id"),
                            _cc_result_text(blk.get("content")),
                            blk.get("is_error"), None)
            else:
                ctx.event(seq, None, "user_block", bt, None, payload_len(blk))
        if texts:
            ctx.add_turn(seq, None, None, "\n".join(texts))
        return

    ctx.event(seq, None, "role:%s" % role, None, None, payload_len(rec))


def _cu_tool(ctx, blk, seq):
    inp = blk.get("input")
    if not isinstance(inp, dict):
        inp = {}
    name = blk.get("name")
    row = ctx.row("tool_calls", seq)
    row["tool_use_id"] = blk.get("id")
    row["tool_name"] = name
    row["tool_kind"] = tool_kind(name)
    row["input_chars"] = payload_len(inp)
    _fill_tool_input(row, inp, ())
    if row["command_head"] is None:
        wd = inp.get("working_directory")
        if isinstance(wd, str) and row["file_path_raw"]:
            row["file_path"] = rel_path(row["file_path_raw"], (wd,))
    else:
        wd = inp.get("working_directory")
        if isinstance(wd, str) and row["file_path_raw"]:
            row["file_path"] = rel_path(row["file_path_raw"], (wd,))
    ctx.add_tool(row)


# --------------------------------------------------------------------------
# worker plumbing
# --------------------------------------------------------------------------

PARSERS = {
    "claude_code": parse_claude_code,
    "codex": parse_codex,
    "opencode": parse_opencode,
    "cursor": parse_cursor,
}

_W = {}


def _init_worker(out_dir, flush_rows):
    _W["writer"] = PartWriter(out_dir, str(os.getpid()), flush_rows)
    # pool workers exit normally on pool.close()/join(), so atexit is the
    # reliable place to flush the tail of each worker's buffers
    atexit.register(_close_worker, None)


def _run_session(task):
    """task = (session_id, agent, repo, rel_path, parse_format)"""
    sid, agent, repo, relpath, fmt = task
    writer = _W["writer"]
    ctx = Ctx(sid, agent, repo)
    path = os.path.join(ROOT, relpath)
    try:
        parser = PARSERS.get(fmt)
        if parser is None:
            writer.error(sid, -1, ValueError("no parser for %r" % fmt))
        else:
            parser(path, ctx, writer)
        ctx.emit(writer)
    except Exception as exc:
        writer.error(sid, -1, exc)
        sys.stderr.write("session %s failed: %s\n%s\n"
                         % (sid, exc, traceback.format_exc()))
    return (sid, agent, len(ctx.calls), len(ctx.tools), len(ctx.turns),
            len(ctx.events), ctx.n_bad)


def _close_worker(_ignored=None):
    w = _W.pop("writer", None)
    if w is not None:
        w.close()
        return w.n_errors
    return 0


# --------------------------------------------------------------------------
# sessions table (DuckDB read_json in the main process)
# --------------------------------------------------------------------------

_SQL_AGENT = """CASE lower(trim(s.agent))
    WHEN 'claude code' THEN 'claude_code'
    WHEN 'claude-code' THEN 'claude_code'
    WHEN 'claude_code' THEN 'claude_code'
    WHEN 'codex' THEN 'codex'
    WHEN 'codex cli' THEN 'codex'
    WHEN 'opencode' THEN 'opencode'
    WHEN 'cursor' THEN 'cursor'
    ELSE NULL END"""

_SQL_SID = ("regexp_replace(regexp_replace(s.trajectory, '^.*/', ''), "
            "'\\.jsonl$', '')")


def write_sessions_table(out_dir):
    import duckdb

    con = duckdb.connect()
    con.execute("""
        CREATE TABLE raw AS
        SELECT unnest(sessions) AS s
        FROM read_json(?, maximum_object_size=200000000, sample_size=-1)
    """, [SESSIONS_JSON])

    def struct_fields(expr):
        try:
            rows = con.execute(
                "DESCRIBE SELECT unnest(%s) FROM raw LIMIT 0" % expr).fetchall()
        except Exception:
            return []
        return [r[0] for r in rows]

    cols = [
        "%s AS session_id" % _SQL_SID,
        "s.session_id AS session_id_meta",
        "%s AS agent" % _SQL_AGENT,
        "s.agent AS agent_raw",
        "s.detected_format AS detected_format",
        "s.source.repository AS repo",
        "s.created_at AS created_at",
        "s.branch AS branch",
        "s.strategy AS strategy",
        "s.bytes AS bytes",
        "s.trajectory AS trajectory",
        "to_json(s.models) AS models",
        "to_json(s.agent_versions) AS agent_versions",
        "to_json(s.files_touched) AS files_touched",
        "coalesce(len(s.files_touched), 0) AS n_files_touched",
    ]
    for prefix, expr in (("stat", "s.statistics"),
                         ("ckpt", "s.checkpoint_token_usage"),
                         ("attr", "s.initial_attribution")):
        for f in struct_fields(expr):
            cols.append('%s."%s" AS %s_%s' % (expr, f, prefix, f))

    d = os.path.join(out_dir, "sessions")
    if not os.path.isdir(d):
        os.makedirs(d)
    target = os.path.join(d, "part-main-0.parquet").replace("'", "''")
    con.execute("COPY (SELECT %s FROM raw) TO '%s' (FORMAT PARQUET)"
                % (", ".join(cols), target))
    n = con.execute("SELECT count(*) FROM raw").fetchone()[0]
    con.close()
    return n


# --------------------------------------------------------------------------
# catalog
# --------------------------------------------------------------------------


def load_catalog():
    with open(SESSIONS_JSON, "rb") as fh:
        doc = orjson.loads(fh.read())
    out = []
    skipped = {}
    for s in doc.get("sessions") or []:
        traj = s.get("trajectory") or ""
        base = os.path.basename(traj)
        if base.endswith(".jsonl"):
            base = base[:-6]
        agent = normalize_agent(s.get("agent"))
        if agent is None:
            key = str(s.get("agent"))
            skipped[key] = skipped.get(key, 0) + 1
            continue
        fmt = normalize_agent(s.get("detected_format")) or agent
        src = s.get("source") or {}
        out.append({
            "sid": base,
            "agent": agent,
            "fmt": fmt,
            "repo": src.get("repository"),
            "path": traj,
            "bytes": s.get("bytes") or 0,
        })
    return out, skipped


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(ROOT, "analysis", "ledger"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sessions", default=None,
                    help="file with one session_id (transcript basename) per line")
    ap.add_argument("--agents", default=",".join(AGENTS))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--flush-rows", type=int, default=FLUSH_ROWS)
    ap.add_argument("--no-sessions-table", action="store_true")
    args = ap.parse_args(argv)

    out_dir = args.out
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(ROOT, out_dir)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    wanted_agents = set(a.strip() for a in args.agents.split(",") if a.strip())
    catalog, skipped = load_catalog()

    wanted_ids = None
    if args.sessions:
        wanted_ids = set()
        with open(args.sessions) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    wanted_ids.add(line)

    tasks = []
    for row in catalog:
        if row["agent"] not in wanted_agents:
            continue
        if wanted_ids is not None and row["sid"] not in wanted_ids:
            continue
        full = os.path.join(ROOT, row["path"])
        if not os.path.exists(full):
            continue
        tasks.append(row)

    tasks.sort(key=lambda r: r["bytes"], reverse=True)
    if args.limit:
        tasks = tasks[:args.limit]

    if wanted_ids is not None:
        missing = wanted_ids - set(t["sid"] for t in tasks)
        if missing:
            sys.stderr.write("warning: %d requested sessions not found: %s\n"
                             % (len(missing), sorted(missing)[:5]))

    total_bytes = sum(t["bytes"] for t in tasks)
    sys.stderr.write("sessions=%d bytes=%.1f MB workers=%d out=%s\n"
                     % (len(tasks), total_bytes / 1e6, args.workers, out_dir))
    sys.stderr.write("skipped agents (not one of the four): %s\n"
                     % json.dumps(skipped, sort_keys=True))

    payload = [(t["sid"], t["agent"], t["repo"], t["path"], t["fmt"])
               for t in tasks]

    totals = {"calls": 0, "tool_calls": 0, "user_turns": 0, "events": 0,
              "bad_lines": 0}
    per_agent = {}

    if not payload:
        sys.stderr.write("nothing to do\n")
    elif args.workers <= 1:
        _init_worker(out_dir, args.flush_rows)
        for task in payload:
            res = _accumulate(_run_session(task), totals, per_agent)
        _close_worker(None)
    else:
        ctx_mp = mp.get_context("spawn")
        pool = ctx_mp.Pool(args.workers, initializer=_init_worker,
                           initargs=(out_dir, args.flush_rows))
        try:
            for res in pool.imap_unordered(_run_session, payload, chunksize=1):
                _accumulate(res, totals, per_agent)
        finally:
            pool.close()
            pool.join()

    # merge worker error files into <out>/errors.jsonl
    err_dir = os.path.join(out_dir, "errors")
    err_out = os.path.join(out_dir, "errors.jsonl")
    n_err = 0
    if os.path.isdir(err_dir):
        with open(err_out, "w") as dst:
            for name in sorted(os.listdir(err_dir)):
                with open(os.path.join(err_dir, name)) as src:
                    for line in src:
                        dst.write(line)
                        n_err += 1
                os.remove(os.path.join(err_dir, name))
        try:
            os.rmdir(err_dir)
        except OSError:
            pass
    else:
        open(err_out, "w").close()

    if not args.no_sessions_table:
        n_sessions = write_sessions_table(out_dir)
        sys.stderr.write("sessions table rows: %d\n" % n_sessions)

    sys.stderr.write("rows: %s\n" % json.dumps(totals, sort_keys=True))
    sys.stderr.write("per agent: %s\n" % json.dumps(per_agent, sort_keys=True))
    sys.stderr.write("errors logged: %d (%s)\n" % (n_err, err_out))
    return 0


def _accumulate(res, totals, per_agent):
    sid, agent, ncalls, ntools, nturns, nevents, nbad = res
    totals["calls"] += ncalls
    totals["tool_calls"] += ntools
    totals["user_turns"] += nturns
    totals["events"] += nevents
    totals["bad_lines"] += nbad
    a = per_agent.setdefault(agent, {"sessions": 0, "calls": 0,
                                     "tool_calls": 0, "user_turns": 0,
                                     "events": 0})
    a["sessions"] += 1
    a["calls"] += ncalls
    a["tool_calls"] += ntools
    a["user_turns"] += nturns
    a["events"] += nevents
    return res


if __name__ == "__main__":
    sys.exit(main())
