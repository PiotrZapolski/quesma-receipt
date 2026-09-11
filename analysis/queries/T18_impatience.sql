-- # T18 impatience: interrupts, queued commands and sunk tokens
-- The sunk cost of an interrupt = the USD of the calls between the previous human
-- prompt and the interrupt itself.

CREATE OR REPLACE TEMP TABLE t18 AS
WITH u AS (
  -- interrupt records are written by the harness (is_meta, human_chars = 0), so the
  -- anchor is the last real human prompt before them.
  SELECT session_id, agent, seq, ts, coalesce(is_interrupt, false) AS is_interrupt,
         max(CASE WHEN NOT coalesce(is_meta, false) AND human_chars > 0 THEN seq END)
           OVER (PARTITION BY session_id ORDER BY seq
                 ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_user_seq
  FROM user_turns
)
SELECT u.session_id, u.agent, u.seq, u.prev_user_seq,
       p.cum_cost_usd AS cum_usd_at_interrupt,
       pp.cum_cost_usd AS cum_usd_at_prev_prompt,
       greatest(coalesce(p.cum_cost_usd, 0) - coalesce(pp.cum_cost_usd, 0), 0) AS sunk_usd,
       p.calls_before - coalesce(pp.calls_before, 0) AS sunk_calls
FROM u
JOIN seq_pos p ON p.session_id = u.session_id AND p.seq = u.seq
LEFT JOIN seq_pos pp ON pp.session_id = u.session_id AND pp.seq = u.prev_user_seq
WHERE u.is_interrupt;

-- @out interrupts_by_agent
SELECT agent,
       count(*) AS interrupts,
       count(DISTINCT session_id) AS sessions_with_interrupts,
       sum(sunk_usd) AS sunk_usd,
       median(sunk_usd) AS median_sunk_usd,
       median(sunk_calls) AS median_sunk_calls,
       100.0 * sum(sunk_usd) / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced) AS pct_of_total_usd
FROM t18
GROUP BY 1
ORDER BY interrupts DESC;

-- @out queue_operations
SELECT s.agent,
       count(DISTINCT e.session_id) AS sessions_with_queue_events,
       count(*) AS queue_events,
       median(q.n) AS median_queue_events_per_session
FROM events e
JOIN sessions_x s ON s.session_id = e.session_id
JOIN (SELECT session_id, count(*) AS n FROM events WHERE event_type = 'queue-operation' GROUP BY 1) q
  ON q.session_id = e.session_id
WHERE e.event_type = 'queue-operation'
GROUP BY 1
ORDER BY queue_events DESC;

-- @out sessions_with_vs_without_interrupts
SELECT CASE WHEN n_interrupts > 0 THEN 'interrupted' ELSE 'never interrupted' END AS kind,
       mode,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line,
       median(n_calls) AS median_calls,
       100.0 * count(*) FILTER (WHERE committed_lines > 0) / count(*) AS pct_sessions_with_commits
FROM sessions_x
WHERE n_calls > 0 AND agent = 'claude_code'
GROUP BY 1, 2
ORDER BY kind, usd DESC;

-- @headline
SELECT (SELECT count(*) FROM t18) AS interrupts,
       (SELECT count(DISTINCT session_id) FROM t18) AS sessions_with_at_least_one_interrupt,
       (SELECT sum(sunk_usd) FROM t18) AS usd_sunk_before_interrupts,
       (SELECT 100.0 * sum(sunk_usd) / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced) FROM t18) AS pct_of_total_usd,
       (SELECT sum(session_cost_usd) / nullif(sum(committed_lines), 0) FROM sessions_x
        WHERE agent = 'claude_code' AND n_interrupts > 0) AS usd_per_committed_line_interrupted_sessions,
       (SELECT sum(session_cost_usd) / nullif(sum(committed_lines), 0) FROM sessions_x
        WHERE agent = 'claude_code' AND n_interrupts = 0 AND n_calls > 0) AS usd_per_committed_line_calm_sessions,
       (SELECT count(*) FROM events WHERE event_type = 'queue-operation') AS queue_operation_events;
