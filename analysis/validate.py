#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate - compare the extracted ledger against metadata/sessions.json stats.

    uv run --with duckdb analysis/validate.py --ledger analysis/ledger_sample

Exact agreement is not expected: the dataset metadata counted things with a
different definition. The point is to see whether we are in the right ballpark
and to name the systematic gaps.

Python 3.9 compatible.
"""

from __future__ import annotations

import argparse
import os
import sys

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the four comparisons the spec asks for
METRICS = [
    ("tool_calls", "n_tool_calls", "stat_tool_calls"),
    ("calls", "n_calls", "stat_assistant_messages"),
    ("output_tokens", "sum_output_tokens", "stat_output_tokens"),
    ("user_turns(!meta)", "n_user_turns", "stat_user_messages"),
]

# the baselines that actually line up with what we extract (see README)
METRICS2 = [
    ("calls", "n_calls", "ckpt_api_call_count"),
    ("output_tokens", "sum_output_tokens", "ckpt_output_tokens"),
    ("output-reasoning", "sum_output_net", "stat_output_tokens"),
    ("user_turns(all)", "n_user_turns_all", "stat_user_messages"),
]


def g(path):
    return os.path.join(path, "*.parquet").replace("'", "''")


def build(con, ledger):
    con.execute("""
        CREATE VIEW s AS SELECT * FROM read_parquet('%s');
        """ % g(os.path.join(ledger, "sessions")))
    con.execute("""
        CREATE TABLE agg AS
        WITH c AS (
            SELECT session_id, count(*) AS n_calls,
                   sum(coalesce(output_tokens, 0)) AS sum_output_tokens,
                   sum(coalesce(output_tokens, 0))
                       - sum(coalesce(reasoning_tokens, 0)) AS sum_output_net
            FROM read_parquet('%s') GROUP BY 1
        ), t AS (
            SELECT session_id, count(*) AS n_tool_calls
            FROM read_parquet('%s') GROUP BY 1
        ), u AS (
            SELECT session_id,
                   count(*) FILTER (WHERE NOT coalesce(is_meta, false))
                       AS n_user_turns,
                   count(*) AS n_user_turns_all
            FROM read_parquet('%s') GROUP BY 1
        ), ids AS (
            SELECT session_id FROM c
            UNION SELECT session_id FROM t
            UNION SELECT session_id FROM u
        )
        SELECT ids.session_id,
               s.agent,
               coalesce(c.n_calls, 0) AS n_calls,
               coalesce(c.sum_output_tokens, 0) AS sum_output_tokens,
               coalesce(c.sum_output_net, 0) AS sum_output_net,
               coalesce(t.n_tool_calls, 0) AS n_tool_calls,
               coalesce(u.n_user_turns, 0) AS n_user_turns,
               coalesce(u.n_user_turns_all, 0) AS n_user_turns_all,
               coalesce(s.stat_assistant_messages, 0) AS stat_assistant_messages,
               coalesce(s.stat_output_tokens, 0) AS stat_output_tokens,
               coalesce(s.stat_tool_calls, 0) AS stat_tool_calls,
               coalesce(s.stat_user_messages, 0) AS stat_user_messages,
               coalesce(s.ckpt_api_call_count, 0) AS ckpt_api_call_count,
               coalesce(s.ckpt_output_tokens, 0) AS ckpt_output_tokens
        FROM ids
        LEFT JOIN c USING (session_id)
        LEFT JOIN t USING (session_id)
        LEFT JOIN u USING (session_id)
        LEFT JOIN s USING (session_id)
    """ % (g(os.path.join(ledger, "calls")),
           g(os.path.join(ledger, "tool_calls")),
           g(os.path.join(ledger, "user_turns"))))


def fmt_pct(v):
    if v is None:
        return "n/a"
    return "%+.1f%%" % (100.0 * v)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", default=os.path.join(ROOT, "analysis", "ledger"))
    ap.add_argument("--worst", type=int, default=5)
    args = ap.parse_args(argv)

    ledger = args.ledger
    if not os.path.isabs(ledger):
        ledger = os.path.join(ROOT, ledger)

    con = duckdb.connect()
    build(con, ledger)

    n = con.execute("SELECT count(*) FROM agg").fetchone()[0]
    print("ledger: %s" % ledger)
    print("sessions in ledger: %d" % n)
    print("")

    for title, metrics in (("A. spec comparison (ledger vs metadata.statistics)",
                            METRICS),
                           ("B. closer baselines (see README, 'known gaps')",
                            METRICS2)):
        print(title)
        print("")
        _table(con, metrics)
        print("")

    for label, ours, theirs in METRICS + METRICS2:
        q = """
            SELECT session_id, coalesce(agent,'(unknown)'), {ours}, {theirs},
                   CASE WHEN {theirs} > 0
                        THEN ({ours} - {theirs}) / {theirs}::DOUBLE END AS rel
            FROM agg
            WHERE {theirs} > 0
            ORDER BY abs(rel) DESC NULLS LAST
            LIMIT {k}
        """.format(ours=ours, theirs=theirs, k=args.worst)
        print("worst %d sessions for %s vs %s:" % (args.worst, ours, theirs))
        for sid, agent, a, b, rel in con.execute(q).fetchall():
            print("    %-55s %-12s %10s vs %10s  %s"
                  % (sid, agent, a, b, fmt_pct(rel)))
        print("")

    con.close()
    return 0


def _table(con, metrics):
    rows = []
    for label, ours, theirs in metrics:
        q = """
            SELECT coalesce(agent, '(unknown)') AS agent,
                   count(*) AS n,
                   sum({ours}) AS ours,
                   sum({theirs}) AS meta,
                   median(CASE WHEN {theirs} > 0
                          THEN ({ours} - {theirs}) / {theirs}::DOUBLE END)
                       AS med_rel,
                   count(*) FILTER (WHERE {ours} = {theirs}) AS n_exact,
                   count(*) FILTER (WHERE {theirs} = 0) AS n_meta_zero
            FROM agg GROUP BY 1 ORDER BY 1
        """.format(ours=ours, theirs=theirs)
        for r in con.execute(q).fetchall():
            rows.append((label, r[0], r[1], r[2], r[3], r[4], r[5], r[6]))

    hdr = ("| metric | agent | sessions | ledger total | metadata total | "
           "median rel delta | exact | meta=0 |")
    print(hdr)
    print("|---|---|---:|---:|---:|---:|---:|---:|")
    for label, agent, n_s, ours, meta, med, n_exact, n_zero in rows:
        print("| %s | %s | %d | %d | %d | %s | %d | %d |"
              % (label, agent, n_s, ours or 0, meta or 0, fmt_pct(med),
                 n_exact, n_zero))


if __name__ == "__main__":
    sys.exit(main())
