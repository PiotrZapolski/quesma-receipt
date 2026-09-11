-- # T16 subagents: what the sidechains cost (claude_code only)
-- Note: only 300 calls in the whole ledger are flagged is_sidechain, so the Task
-- tool traffic is mostly recorded as ordinary calls. Treat this as a floor.

-- @out sidechain_share
SELECT agent,
       count(*) AS calls,
       count(*) FILTER (WHERE is_sidechain) AS sidechain_calls,
       100.0 * count(*) FILTER (WHERE is_sidechain) / count(*) AS pct_calls_sidechain,
       sum(coalesce(cost_usd, 0)) AS usd,
       sum(coalesce(cost_usd, 0)) FILTER (WHERE is_sidechain) AS sidechain_usd,
       100.0 * sum(coalesce(cost_usd, 0)) FILTER (WHERE is_sidechain)
             / nullif(sum(coalesce(cost_usd, 0)), 0) AS pct_usd_sidechain
FROM calls_priced
GROUP BY 1
ORDER BY usd DESC;

-- @out sessions_with_vs_without
WITH s AS (
  SELECT x.*, CASE WHEN x.n_sidechain_calls > 0 THEN 'has sidechain calls'
                   WHEN t.task_calls > 0 THEN 'uses the task tool'
                   ELSE 'no subagents' END AS kind
  FROM sessions_x x
  LEFT JOIN (SELECT session_id, count(*) AS task_calls FROM tool_calls
             WHERE tool_kind = 'task' GROUP BY 1) t USING (session_id)
  WHERE x.agent = 'claude_code' AND x.n_calls > 0
)
SELECT kind, mode,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       100.0 * count(*) FILTER (WHERE committed_lines > 0) / count(*) AS pct_sessions_with_commits,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line,
       median(session_cost_usd) AS median_session_usd
FROM s
GROUP BY 1, 2
ORDER BY kind, usd DESC;

-- @out task_tool_usage
SELECT s.agent,
       count(*) AS task_calls,
       count(DISTINCT tc.session_id) AS sessions,
       sum(coalesce(tc.result_chars, 0)) AS result_chars,
       median(tc.result_chars) AS median_result_chars,
       sum(coalesce(tc.input_chars, 0) / 4.0 * s.p_output / 1e6) AS usd_of_the_task_prompts
FROM tool_calls tc JOIN sessions_x s USING (session_id)
WHERE tc.tool_kind = 'task'
GROUP BY 1
ORDER BY task_calls DESC;

-- @headline
SELECT (SELECT count(*) FROM calls_priced WHERE is_sidechain) AS sidechain_calls,
       (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced WHERE is_sidechain) AS sidechain_usd,
       (SELECT 100.0 * sum(coalesce(cost_usd, 0)) FILTER (WHERE is_sidechain)
               / sum(coalesce(cost_usd, 0)) FROM calls_priced WHERE agent = 'claude_code') AS pct_of_claude_code_usd,
       (SELECT count(*) FROM tool_calls WHERE tool_kind = 'task') AS task_tool_calls,
       (SELECT sum(coalesce(result_chars, 0)) FROM tool_calls WHERE tool_kind = 'task') AS task_result_chars,
       (SELECT count(DISTINCT session_id) FROM tool_calls WHERE tool_kind = 'task') AS sessions_using_task;
