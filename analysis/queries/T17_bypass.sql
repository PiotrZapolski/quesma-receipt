-- # T17 bypass: permission mode and what it buys (claude_code)
-- The dominant permission-mode event of a session decides its bucket.

CREATE OR REPLACE TEMP TABLE t17 AS
WITH m AS (
  SELECT session_id, value AS permission_mode, count(*) AS n,
         row_number() OVER (PARTITION BY session_id ORDER BY count(*) DESC, value) AS rn
  FROM events
  WHERE event_type = 'permission-mode' AND value IS NOT NULL
  GROUP BY 1, 2
)
SELECT s.*, coalesce(m.permission_mode, 'no permission-mode events') AS permission_mode
FROM sessions_x s
LEFT JOIN (SELECT session_id, permission_mode FROM m WHERE rn = 1) m USING (session_id)
WHERE s.agent = 'claude_code' AND s.n_calls > 0;

-- @out by_permission_mode
SELECT permission_mode,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line,
       100.0 * sum(n_tool_errors) / nullif(sum(n_tool_calls), 0) AS tool_error_rate_pct,
       sum(n_tool_calls) * 1.0 / nullif(sum(committed_lines), 0) AS tool_calls_per_committed_line,
       100.0 * count(*) FILTER (WHERE committed_lines > 0) / count(*) AS pct_sessions_with_commits,
       median(session_cost_usd) AS median_session_usd
FROM t17
GROUP BY 1
ORDER BY usd DESC;

-- @out by_permission_mode_and_mode
SELECT permission_mode, mode,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line,
       100.0 * sum(n_tool_errors) / nullif(sum(n_tool_calls), 0) AS tool_error_rate_pct
FROM t17
GROUP BY 1, 2
HAVING count(*) >= 20
ORDER BY permission_mode, usd DESC;

-- @headline
WITH a AS (
  SELECT permission_mode,
         sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS upl,
         100.0 * sum(n_tool_errors) / nullif(sum(n_tool_calls), 0) AS err,
         count(*) AS sessions, sum(session_cost_usd) AS usd
  FROM t17 GROUP BY 1 HAVING count(*) >= 50
)
SELECT (SELECT sessions FROM a WHERE permission_mode = 'bypassPermissions') AS sessions_on_bypass,
       (SELECT usd FROM a WHERE permission_mode = 'bypassPermissions') AS usd_on_bypass,
       (SELECT upl FROM a WHERE permission_mode = 'bypassPermissions') AS usd_per_committed_line_bypass,
       (SELECT upl FROM a WHERE permission_mode = 'default') AS usd_per_committed_line_default,
       (SELECT err FROM a WHERE permission_mode = 'bypassPermissions') AS tool_error_rate_pct_bypass,
       (SELECT err FROM a WHERE permission_mode = 'default') AS tool_error_rate_pct_default;
