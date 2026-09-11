-- # T21 fast mode: does speed=fast change anything (claude_code)
-- speed is only written by recent Claude Code versions, so "no speed field" is the
-- majority bucket and is reported separately rather than merged into standard.

-- @out speed_share
SELECT coalesce(speed, 'not recorded') AS speed,
       count(*) AS calls,
       100.0 * count(*) / sum(count(*)) OVER () AS pct_of_calls,
       count(DISTINCT session_id) AS sessions,
       sum(coalesce(cost_usd, 0)) AS usd,
       100.0 * sum(coalesce(cost_usd, 0)) / sum(sum(coalesce(cost_usd, 0))) OVER () AS pct_of_usd,
       sum(coalesce(output_tokens, 0)) AS output_tokens
FROM calls_priced
WHERE agent = 'claude_code'
GROUP BY 1
ORDER BY calls DESC;

-- @out fast_sessions_vs_standard
WITH s AS (
  SELECT x.session_id, x.mode, x.session_cost_usd, x.committed_lines, x.n_calls,
         CASE WHEN x.n_fast_calls > 0 THEN 'uses fast' ELSE 'never fast' END AS kind
  FROM sessions_x x WHERE x.agent = 'claude_code' AND x.n_calls > 0
), t AS (
  SELECT s.kind, s.mode, s.session_id, s.session_cost_usd, s.committed_lines,
         median(date_diff('millisecond', tu.user_ts, tu.last_call_ts_adj) / 1000.0) AS median_agent_time_s
  FROM s LEFT JOIN turns tu USING (session_id)
  WHERE tu.user_ts IS NOT NULL AND tu.last_call_ts_adj IS NOT NULL
  GROUP BY 1, 2, 3, 4, 5
)
SELECT kind,
       count(*) AS sessions,
       median(median_agent_time_s) AS median_agent_time_s_per_turn,
       sum(session_cost_usd) AS usd,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line
FROM t
GROUP BY 1
ORDER BY sessions DESC;

-- @out fast_by_month
SELECT month,
       count(*) FILTER (WHERE speed = 'fast') AS fast_calls,
       count(*) AS calls,
       100.0 * count(*) FILTER (WHERE speed = 'fast') / count(*) AS pct_fast,
       sum(coalesce(cost_usd, 0)) FILTER (WHERE speed = 'fast') AS fast_usd
FROM calls_priced
WHERE agent = 'claude_code' AND month IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- @headline
SELECT count(*) FILTER (WHERE speed = 'fast') AS fast_calls,
       100.0 * count(*) FILTER (WHERE speed = 'fast') / count(*) AS pct_of_claude_code_calls,
       sum(coalesce(cost_usd, 0)) FILTER (WHERE speed = 'fast') AS fast_usd,
       100.0 * sum(coalesce(cost_usd, 0)) FILTER (WHERE speed = 'fast')
             / sum(coalesce(cost_usd, 0)) AS pct_of_claude_code_usd,
       count(DISTINCT session_id) FILTER (WHERE speed = 'fast') AS sessions_using_fast,
       100.0 * count(*) FILTER (WHERE speed IS NULL) / count(*) AS pct_of_calls_without_a_speed_field
FROM calls_priced
WHERE agent = 'claude_code';
