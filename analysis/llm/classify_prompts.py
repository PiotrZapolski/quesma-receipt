"""Layer 2: LLM classification of every human prompt in the ledger.

Items are `user_turns` with is_meta = false and human_chars > 0. Each item carries a
little context (the previous assistant text_head, the previous tool names) and the
human part of the prompt truncated to 1500 chars. Items go out 15 to a request; the
model answers with one JSON record per item.

Run (dry, no key needed):
  uv run --with duckdb --with pyarrow --with orjson --with openai --with anthropic \
      analysis/llm/classify_prompts.py --dry-run --limit 50 --print-sample 1

Real run (needs DEEPSEEK_API_KEY or ANTHROPIC_API_KEY):
  uv run --with duckdb --with pyarrow --with orjson --with openai --with anthropic \
      analysis/llm/classify_prompts.py --provider deepseek --concurrency 16

Python 3.9 syntax. No em or en dashes anywhere.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import client as llm  # noqa: E402

TASK = "classify_prompts"

LABELS = ["new_task", "follow_up", "approval", "correction", "failure_report",
          "interruption", "question", "meta_other"]
SENTIMENTS = ["neutral", "frustrated", "positive"]

PROMPT_CHARS = 1500
TEXT_HEAD_CHARS = 300
MAX_PREV_TOOLS = 5
DEFAULT_BATCH = 15
EST_OUT_PER_ITEM = 40

# ---------------------------------------------------------------------------
# harness-tag stripping (same tag list as build_ledger.human_text, but newlines
# are kept so the model sees the prompt's real shape)
# ---------------------------------------------------------------------------

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
_RE_BLANK = re.compile(r"\n{3,}")
_RE_SPACES = re.compile(r"[ \t]{2,}")


def human_text(text):
    if not text:
        return ""
    hits = _RE_USER_QUERY.findall(text)
    if hits:
        out = "\n".join(h.strip() for h in hits)
    else:
        out = _RE_PAIRED.sub(" ", text)
        out = _RE_BARE.sub(" ", out)
        out = _RE_INTERRUPT.sub(" ", out)
    out = _RE_SPACES.sub(" ", out)
    return _RE_BLANK.sub("\n\n", out).strip()


# ---------------------------------------------------------------------------
# prompt
# ---------------------------------------------------------------------------

SYSTEM = """You label messages that humans typed to a coding agent (Claude Code,
Codex, OpenCode, Cursor) during real software engineering sessions. You see each
message with a little context: the tail of what the agent said just before, and the
tools the agent had just run.

For every item return exactly one record with these fields.

label, one of:
  new_task        starts a new piece of work, unrelated to what just happened
  follow_up       extends or refines the task in progress, no complaint implied
  approval        agrees, confirms, or tells the agent to go ahead ("yes", "lgtm", "continue")
  correction      tells the agent it did something wrong and what to do instead
  failure_report  reports that something is broken or still failing, without
                  necessarily saying what to do
  interruption    stops or redirects the agent mid-work ("stop", "wait", "no, not that")
  question        asks the agent something and expects an answer, not an edit
  meta_other      about the session or the tooling itself, or none of the above

pushback: true when the message is a correction, a failure_report, or otherwise
  expresses dissatisfaction with the agent's work. false otherwise.

sentiment: neutral, frustrated, or positive. Use frustrated only for visible
  irritation (swearing, "again?", "I already told you", all caps complaints), not for
  a plain bug report.

language: the ISO 639-1 code of the language the human wrote in ("en", "pl", "zh",
  "es", ...). Use "en" when a message is only code or a path.

mentions_file: true when the message names a file, path, directory, module, or
  function by name.

Judge only what the human wrote. Context is there to disambiguate short messages
such as "yes", "no", "still broken". Answer for every item, in the same order, using
the item ids given."""

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "the item id as given"},
        "label": {"type": "string", "enum": LABELS},
        "pushback": {"type": "boolean"},
        "sentiment": {"type": "string", "enum": SENTIMENTS},
        "language": {"type": "string", "description": "ISO 639-1 code"},
        "mentions_file": {"type": "boolean"},
    },
    "required": ["id", "label", "pushback", "sentiment", "language",
                 "mentions_file"],
    "additionalProperties": False,
}

TOOL = llm.ToolSpec(
    "record_prompt_labels",
    "Record one label record for every item in the batch, in the order given.",
    {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": ITEM_SCHEMA},
        },
        "required": ["items"],
        "additionalProperties": False,
    },
)


def render_item(n, row):
    parts = ["--- ITEM %d ---" % n]
    if row.get("agent"):
        parts.append("harness: %s" % row["agent"])
    prev = (row.get("prev_text") or "").strip()
    if prev:
        parts.append("agent said just before (tail): %s" % _oneline(prev))
    tools = row.get("prev_tools") or []
    if tools:
        parts.append("agent tools just before: %s" % ", ".join(tools))
    parts.append("human message:")
    parts.append(row["prompt"])
    return "\n".join(parts)


def _oneline(s):
    return _RE_BLANK.sub(" ", s.replace("\n", " ")).strip()


def build_request(batch, model_hint):
    body = "\n\n".join(render_item(i + 1, row) for i, row in enumerate(batch))
    user = ("Classify the %d human messages below.\n\n%s\n\n"
            "Return one record per item, ids 1 to %d."
            % (len(batch), body, len(batch)))
    rid = hashlib.sha1(("v1|" + user).encode("utf-8", "replace")).hexdigest()[:24]
    return llm.Request(
        rid, SYSTEM, user, TOOL,
        meta={"n_items": len(batch),
              "first": "%s#%d" % (batch[0]["session_id"], batch[0]["seq"])},
        est_out_tokens=EST_OUT_PER_ITEM * len(batch) + 20,
    )


# ---------------------------------------------------------------------------
# item selection
# ---------------------------------------------------------------------------

SQL_ITEMS = """
create or replace temp view ut as
select session_id, agent, repo, seq, ts, human_chars,
       substr(text, 1, 20000) as text
from read_parquet('{ledger}/user_turns/*.parquet')
where is_meta = false and human_chars > 0;

create or replace temp table items as
select * from ut order by session_id, seq {limit};

create or replace temp view ca as
select session_id, seq, text_head
from read_parquet('{ledger}/calls/*.parquet')
where text_head is not null and length(text_head) > 0
  and session_id in (select session_id from items);

create or replace temp view tc as
select session_id, seq, tool_name
from read_parquet('{ledger}/tool_calls/*.parquet')
where session_id in (select session_id from items);

create or replace temp table ctx_text as
select i.session_id, i.seq, c.text_head as prev_text
from items i asof left join ca c
  on i.session_id = c.session_id and i.seq > c.seq;

create or replace temp table ctx_tools as
select session_id, seq, prev_tools from (
  select session_id, seq, pri,
         list_slice(
           list_filter(
             array_agg(tool_name) over (
               partition by session_id order by seq, pri
               rows between 40 preceding and 1 preceding),
             x -> x is not null),
           -{ntools}, -1) as prev_tools
  from (
    select session_id, seq, 1 as pri, tool_name from tc
    union all
    select session_id, seq, 0 as pri, cast(null as varchar) from items
  )
) where pri = 0;
"""

SQL_FETCH = """
select i.session_id, i.agent, i.repo, i.seq, i.text,
       t.prev_text, g.prev_tools
from items i
left join ctx_text t using (session_id, seq)
left join ctx_tools g using (session_id, seq)
order by i.session_id, i.seq
"""


def load_items(con, ledger, limit):
    lim = "limit %d" % limit if limit else ""
    con.execute(SQL_ITEMS.format(ledger=ledger, limit=lim,
                                 ntools=MAX_PREV_TOOLS))
    rows = con.execute(SQL_FETCH).fetchall()
    out = []
    for sid, agent, repo, seq, text, prev_text, prev_tools in rows:
        prompt = human_text(text)
        if not prompt:
            continue
        if len(prompt) > PROMPT_CHARS:
            prompt = prompt[:PROMPT_CHARS] + " [...truncated]"
        head = (prev_text or "")[:TEXT_HEAD_CHARS]
        tools = [t for t in (prev_tools or []) if t][-MAX_PREV_TOOLS:]
        out.append({"session_id": sid, "agent": agent, "repo": repo,
                    "seq": int(seq), "prompt": prompt, "prev_text": head,
                    "prev_tools": tools})
    return out


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------


def write_parquet(path, rows):
    import pyarrow as pa
    import pyarrow.parquet as pq
    cols = ["session_id", "agent", "repo", "seq", "label", "pushback",
            "sentiment", "language", "mentions_file", "model", "cost_usd"]
    table = pa.table({c: [r.get(c) for r in rows] for c in cols})
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    pq.write_table(table, path, compression="zstd")


def coerce_row(co, item, rec, model, per_item):
    """Every model-supplied value forced to its declared type before it can
    reach pyarrow. `co` counts the repairs."""
    return {
        "session_id": co.text("session_id", item.get("session_id"), default=""),
        "agent": co.text("agent", item.get("agent"), default="unknown"),
        "repo": co.text("repo", item.get("repo")),
        "seq": co.integer("seq", item.get("seq")),
        "label": co.enum("label", rec.get("label"), LABELS, "meta_other"),
        "pushback": co.flag("pushback", rec.get("pushback")),
        "sentiment": co.enum("sentiment", rec.get("sentiment"), SENTIMENTS,
                             "neutral"),
        "language": co.language("language", rec.get("language")),
        "mentions_file": co.flag("mentions_file", rec.get("mentions_file")),
        "model": co.text("model", model, default="unknown"),
        "cost_usd": float(per_item),
    }


def write_summary(path, rows, model, provider, total_cost, n_items, n_failed,
                  co=None):
    from collections import Counter, defaultdict
    by_agent = defaultdict(Counter)
    push = defaultdict(lambda: [0, 0])
    sent = Counter()
    lang = Counter()
    mentions = [0, 0]
    for r in rows:
        by_agent[r["agent"]][r["label"]] += 1
        push[r["agent"]][0] += 1 if r["pushback"] else 0
        push[r["agent"]][1] += 1
        sent[r["sentiment"]] += 1
        lang[r["language"]] += 1
        mentions[0] += 1 if r["mentions_file"] else 0
        mentions[1] += 1
    L = []
    L.append("# Layer 2: prompt classification\n")
    L.append("provider `%s`, model `%s`, %d labelled of %d selected, %d failed, %s\n"
             % (provider, model, len(rows), n_items, n_failed,
                llm.fmt_usd(total_cost)))
    L.append("\n## Label distribution by agent\n")
    agents = sorted(by_agent)
    L.append("| label | " + " | ".join(agents) + " | total |")
    L.append("|---|" + "---|" * (len(agents) + 1))
    for lab in LABELS:
        tot = sum(by_agent[a][lab] for a in agents)
        L.append("| %s | %s | %d |" % (
            lab, " | ".join(str(by_agent[a][lab]) for a in agents), tot))
    L.append("\n## Pushback rate by agent\n")
    L.append("| agent | prompts | pushback | rate |")
    L.append("|---|---:|---:|---:|")
    for a in agents:
        p, n = push[a]
        L.append("| %s | %d | %d | %.1f%% |" % (a, n, p, 100.0 * p / n if n else 0))
    L.append("\n## Sentiment\n")
    L.append("| sentiment | prompts | share |")
    L.append("|---|---:|---:|")
    n = max(1, len(rows))
    for s, c in sent.most_common():
        L.append("| %s | %d | %.1f%% |" % (s, c, 100.0 * c / n))
    L.append("\n## Top languages\n")
    L.append("| language | prompts | share |")
    L.append("|---|---:|---:|")
    for s, c in lang.most_common(12):
        L.append("| %s | %d | %.1f%% |" % (s, c, 100.0 * c / n))
    L.append("\nmentions_file: %d of %d (%.1f%%)\n"
             % (mentions[0], mentions[1],
                100.0 * mentions[0] / max(1, mentions[1])))
    if co is not None:
        L.extend(co.markdown("Coerced and invalid values"))
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    llm.add_common_args(ap, "classify")
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    ap.add_argument("--max-tokens", type=int, default=2000)
    args = ap.parse_args(argv)

    import duckdb

    con = duckdb.connect()
    sys.stderr.write("selecting items from %s ...\n" % args.ledger)
    items = load_items(con, args.ledger, args.limit)
    sys.stderr.write("%d items\n" % len(items))
    if not items:
        raise SystemExit("no items selected")

    cl = llm.make_client(args.provider, "classify", model=args.model,
                         max_tokens=args.max_tokens, timeout=args.timeout,
                         temperature=0.0 if args.provider == "deepseek" else None,
                         thinking=args.thinking)
    batches = list(chunk(items, args.batch_size))
    requests = [build_request(b, cl.model) for b in batches]

    cache_root = os.path.join(args.results, "llm", "cache")
    cache = llm.Cache(cache_root, TASK, enabled=not args.no_cache)

    if args.print_sample:
        llm.print_samples(cl, requests, args.print_sample)

    if args.dry_run:
        info = llm.dry_run_report(cl, cache, requests,
                                  "layer 2, %d prompts in %d batches of %d"
                                  % (len(items), len(requests), args.batch_size))
        sys.stdout.write("items         %d\n" % len(items))
        sys.stdout.write("output parquet %s\n"
                         % os.path.join(args.results, "llm",
                                        "prompt_labels.parquet"))
        return 0

    if not cl.has_key():
        raise SystemExit("set %s, or pass --dry-run"
                         % llm.ENV_KEYS[cl.provider])

    by_rid = {}
    for req, b in zip(requests, batches):
        by_rid[req.rid] = b

    out_rows = []
    co = llm.Coercer()
    total_cost = 0.0
    new_cost = 0.0
    n_failed = 0
    for res in llm.run_requests(cl, cache, requests,
                                concurrency=args.concurrency,
                                retries=args.retries):
        batch = by_rid[res.rid]
        if res.error:
            n_failed += len(batch)
            sys.stderr.write("FAILED %s: %s\n" % (res.rid, res.error))
            continue
        total_cost += res.cost
        new_cost += res.new_cost
        per_item = res.cost / max(1, len(batch))
        got = (res.data or {}).get("items") or []
        by_id = {}
        for rec in got:
            if not isinstance(rec, dict):
                continue
            try:
                by_id[int(rec.get("id"))] = rec
            except (TypeError, ValueError):
                continue
        for i, item in enumerate(batch):
            rec = by_id.get(i + 1)
            if rec is None:
                n_failed += 1
                continue
            out_rows.append(coerce_row(co, item, rec, res.model, per_item))

    out_dir = os.path.join(args.results, "llm")
    pq_path = os.path.join(out_dir, "prompt_labels.parquet")
    write_parquet(pq_path, out_rows)
    write_summary(os.path.join(out_dir, "PROMPT_LABELS.md"), out_rows, cl.model,
                  cl.provider, total_cost, len(items), n_failed, co=co)
    co.log(label="coercion (layer 2)")
    sys.stderr.write("wrote %s (%d rows), %s of labels (%s new this run, "
                     "%d cache hits), %d failed\n"
                     % (pq_path, len(out_rows), llm.fmt_usd(total_cost),
                        llm.fmt_usd(new_cost), cache.hits, n_failed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
