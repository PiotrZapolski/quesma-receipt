#!/usr/bin/env python3
"""Layer 1 runner: executes analysis/queries/*.sql against the Parquet ledger.

Usage:
    uv run --with duckdb --with pyarrow analysis/run_queries.py [--only T02,T04]

Contract (see analysis/DESIGN.md):
  * 00_setup.sql builds the views, the prices table and the materialised helper
    tables (calls_priced, sessions_x, calls_idx, seq_pos, turns, session_price).
  * every T*.sql then C*.sql file is executed in name order.
  * inside a file, a line `-- @out <name>` marks the statement that follows: its
    result is written to results/<stem>__<name>.csv (results/cases/<name>.csv for
    C files) and rendered into results/REPORT.md.
  * `-- @headline` marks the one row summary of the thesis.
  * statements without a marker are executed for side effects only.
  * a failing file is reported and does not stop the others.

Python 3.9, no dependencies beyond duckdb (pyarrow is pulled in for parquet).
"""

import argparse
import csv
import datetime
import os
import re
import sys
import time
import traceback

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEDGER = os.path.join(HERE, "ledger")
DEFAULT_RESULTS = os.path.join(HERE, "results")
DEFAULT_QUERIES = os.path.join(HERE, "queries")
DEFAULT_PRICES = os.path.join(HERE, "prices.csv")
DEFAULT_DB = os.path.join(HERE, "ledger.duckdb")

OUT_RE = re.compile(r"^\s*--\s*@out\s+([A-Za-z0-9_]+)\s*$")
HEADLINE_RE = re.compile(r"^\s*--\s*@headline\s*([A-Za-z0-9_]*)\s*$")
TITLE_RE = re.compile(r"^\s*--\s*#\s*(.+?)\s*$")


# --------------------------------------------------------------------------- SQL parsing

def split_statements(text):
    """Split a SQL blob on top level semicolons (quote and comment aware)."""
    out = []
    buf = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if ch == "-" and nxt == "-":
            j = text.find("\n", i)
            j = n if j < 0 else j + 1
            buf.append(text[i:j])
            i = j
            continue
        if ch == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            buf.append(text[i:j])
            i = j
            continue
        if ch in ("'", '"'):
            j = i + 1
            while j < n:
                if text[j] == ch:
                    if j + 1 < n and text[j + 1] == ch:
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            buf.append(text[i:j])
            i = j
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                out.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    stmt = "".join(buf).strip()
    if stmt:
        out.append(stmt)
    return [s for s in out if strip_comments(s)]


def strip_comments(stmt):
    body = re.sub(r"--[^\n]*", "", stmt)
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    return body.strip()


# --------------------------------------------------------------------------- rendering

def fmt_cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return str(v)
        av = abs(v)
        if av != 0 and av < 0.001:
            return "%.3e" % v
        if av >= 1000:
            return "%.1f" % v
        return "%.4f" % round(v, 4)
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat(sep=" ")
    s = str(v)
    if len(s) > 160:
        s = s[:157] + "..."
    return s.replace("|", "\\|").replace("\n", " ")


def md_table(cols, rows, max_rows=40):
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows[:max_rows]:
        lines.append("| " + " | ".join(fmt_cell(v) for v in r) + " |")
    if len(rows) > max_rows:
        lines.append("")
        lines.append("_%d rows total, %d shown._" % (len(rows), max_rows))
    return "\n".join(lines)


def csv_cell(v):
    if v is None:
        return ""
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat(sep=" ")
    return v


def write_csv(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([csv_cell(v) for v in r])


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Layer 1 SQL runner")
    ap.add_argument("--only", default=None,
                    help="comma separated file prefixes, e.g. T02,T04,C01")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--results", default=DEFAULT_RESULTS)
    ap.add_argument("--queries", default=DEFAULT_QUERIES)
    ap.add_argument("--prices", default=DEFAULT_PRICES)
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--rebuild", action="store_true",
                    help="delete the duckdb file before running (full rebuild)")
    ap.add_argument("--skip-setup", action="store_true",
                    help="do not re-run 00_setup.sql (reuse the existing tables)")
    args = ap.parse_args()

    if args.rebuild and os.path.exists(args.db):
        os.remove(args.db)
    os.makedirs(args.results, exist_ok=True)
    os.makedirs(os.path.join(args.results, "cases"), exist_ok=True)

    only = None
    if args.only:
        only = set(p.strip() for p in args.only.split(",") if p.strip())

    files = sorted(f for f in os.listdir(args.queries) if f.endswith(".sql"))
    setup = [f for f in files if f.startswith("00_")]
    theses = [f for f in files if f.startswith("T")]
    cases = [f for f in files if f.startswith("C")]

    def selected(f):
        if only is None:
            return True
        stem = os.path.splitext(f)[0]
        return any(stem.startswith(p) for p in only)

    con = duckdb.connect(args.db)
    con.execute("PRAGMA threads=6")
    report = []
    t_start = time.time()
    failures = []

    subs = {"{LEDGER}": os.path.abspath(args.ledger),
            "{PRICES}": os.path.abspath(args.prices)}

    def load(path):
        with open(path) as fh:
            text = fh.read()
        for k, v in subs.items():
            text = text.replace(k, v)
        return text

    # setup ------------------------------------------------------------------
    setup_secs = 0.0
    if not args.skip_setup:
        for f in setup:
            path = os.path.join(args.queries, f)
            t0 = time.time()
            try:
                for s in split_statements(load(path)):
                    con.execute(s)
                setup_secs = time.time() - t0
                sys.stderr.write("setup %s ok (%.1fs)\n" % (f, setup_secs))
            except Exception:
                sys.stderr.write("setup %s FAILED\n%s\n" % (f, traceback.format_exc()))
                failures.append((f, traceback.format_exc(limit=3)))
                return 1

    # theses and cases -------------------------------------------------------
    done = []
    for f in theses + cases:
        if not selected(f):
            continue
        path = os.path.join(args.queries, f)
        is_case = f.startswith("C")
        # re-substitute inside the file body by writing a temp parse: parse_file
        # reads from disk, so substitute by writing the text through a shim.
        try:
            text = load(path)
            tmp_parse = _ParsedFile(path, text)
            dt, n_outs, has_head = run_file_text(con, tmp_parse, args.results, report, is_case)
            done.append((f, dt, n_outs, has_head))
            sys.stderr.write("%-34s ok  %5.1fs  %d results%s\n"
                             % (f, dt, n_outs, "" if has_head else "  [NO HEADLINE ROW]"))
        except Exception:
            tb = traceback.format_exc()
            sys.stderr.write("%-34s FAILED\n%s\n" % (f, tb))
            failures.append((f, tb))
            report.append("## %s\n\n**FAILED**\n\n```\n%s\n```\n" % (f, tb[-2000:]))

    total = time.time() - t_start

    head = ["# Layer 1 report",
            "",
            "Generated %s" % datetime.datetime.now().replace(microsecond=0).isoformat(sep=" "),
            "",
            "- ledger: `%s`" % os.path.abspath(args.ledger),
            "- prices: `%s`" % os.path.abspath(args.prices),
            "- setup: %.1fs, total runtime: %.1fs" % (setup_secs, total),
            "- files run: %d, failed: %d" % (len(done), len(failures)),
            ""]
    if failures:
        head.append("**Failures:** " + ", ".join(f for f, _ in failures))
        head.append("")
    empty = [f for f, _, _, h in done if not h]
    if empty:
        head.append("**Files without a non-empty headline row:** " + ", ".join(empty))
        head.append("")

    with open(os.path.join(args.results, "REPORT.md"), "w") as fh:
        fh.write("\n".join(head) + "\n" + "\n".join(report) + "\n")

    sys.stderr.write("\ntotal %.1fs, report at %s\n"
                     % (total, os.path.join(args.results, "REPORT.md")))
    return 1 if failures else 0


class _ParsedFile(object):
    """Holds the substituted text so parse_file does not have to re-read disk."""

    def __init__(self, path, text):
        self.path = path
        self.text = text


def run_file_text(con, pf, results_dir, report, is_case):
    stem = os.path.splitext(os.path.basename(pf.path))[0]
    lines = pf.text.split("\n")
    title = None
    for line in lines[:3]:
        m = TITLE_RE.match(line)
        if m:
            title = m.group(1)
            break
    blocks = []
    cur = [None, None, []]
    for line in lines:
        m_out = OUT_RE.match(line)
        m_head = HEADLINE_RE.match(line)
        if m_out or m_head:
            text = "\n".join(cur[2]).strip()
            if text:
                blocks.append((cur[0], cur[1], text))
            if m_out:
                cur = ["out", m_out.group(1), []]
            else:
                cur = ["headline", (m_head.group(1) or "headline"), []]
            continue
        cur[2].append(line)
    text = "\n".join(cur[2]).strip()
    if text:
        blocks.append((cur[0], cur[1], text))

    t0 = time.time()
    outs = []
    headline = None
    for kind, name, text in blocks:
        stmts = split_statements(text)
        if not stmts:
            continue
        if kind is None:
            for s in stmts:
                con.execute(s)
            continue
        for s in stmts[:-1]:
            con.execute(s)
        c = con.execute(stmts[-1])
        cols = [d[0] for d in c.description]
        rows = c.fetchall()
        if is_case and kind == "out":
            out_path = os.path.join(results_dir, "cases", "%s.csv" % name)
        else:
            out_path = os.path.join(results_dir, "%s__%s.csv" % (stem, name))
        write_csv(out_path, cols, rows)
        if kind == "headline":
            headline = (cols, rows)
        else:
            outs.append((name, cols, rows, out_path))
    dt = time.time() - t0

    report.append("## %s  (`%s`)\n" % (title or stem, stem))
    if headline is not None:
        cols, rows = headline
        if rows:
            report.append("**Headline**\n")
            for c_, v in zip(cols, rows[0]):
                report.append("- **%s**: %s" % (c_, fmt_cell(v)))
            report.append("")
        else:
            report.append("**Headline: EMPTY RESULT (check the query)**\n")
    for name, cols, rows, out_path in outs:
        report.append("### %s  (%d rows)\n" % (name, len(rows)))
        report.append(md_table(cols, rows) if rows else "_empty_")
        report.append("")
    report.append("_%s: %.1fs_\n" % (stem, dt))
    return dt, len(outs), (headline is not None and bool(headline[1]))


if __name__ == "__main__":
    sys.exit(main())
