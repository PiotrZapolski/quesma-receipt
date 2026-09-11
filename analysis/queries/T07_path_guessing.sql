-- # T07 path guessing: the agent opens files that are not there
-- read/edit/write tool calls that came back with a "does not exist" style error.
-- Recovery cost = the USD of the next 3 calls after the failed tool call.

CREATE OR REPLACE TEMP TABLE t07 AS
SELECT tc.session_id, tc.agent, tc.seq, tc.tool_kind, tc.file_path, tc.error_head,
       s.session_model, s.mode, s.n_calls,
       p.calls_before, p.cum_cost_usd,
       coalesce(tc.is_error, false)
         AND regexp_matches(coalesce(tc.error_head, ''),
             '(does not exist|No such file|ENOENT|not found|File not found)') AS missing_path
FROM tool_calls tc
JOIN seq_pos p ON p.session_id = tc.session_id AND p.seq = tc.seq
JOIN sessions_x s ON s.session_id = tc.session_id
WHERE tc.tool_kind IN ('read', 'edit', 'write');

CREATE OR REPLACE TEMP TABLE t07r AS
SELECT t.*, coalesce(ci.cum_cost_usd, t.cum_cost_usd) - t.cum_cost_usd AS usd_next_3_calls
FROM t07 t
LEFT JOIN calls_idx ci
  ON ci.session_id = t.session_id AND ci.call_idx = least(t.calls_before + 3, t.n_calls);

-- @out by_agent
SELECT agent,
       count(*) AS file_tool_calls,
       count(*) FILTER (WHERE missing_path) AS missing_path_errors,
       100.0 * count(*) FILTER (WHERE missing_path) / count(*) AS pct_missing_path,
       count(DISTINCT session_id) FILTER (WHERE missing_path) AS sessions_affected,
       sum(usd_next_3_calls) FILTER (WHERE missing_path) AS usd_of_next_3_calls
FROM t07r
GROUP BY 1
ORDER BY missing_path_errors DESC;

-- @out by_model
SELECT session_model AS model,
       count(*) AS file_tool_calls,
       count(*) FILTER (WHERE missing_path) AS missing_path_errors,
       100.0 * count(*) FILTER (WHERE missing_path) / count(*) AS pct_missing_path,
       sum(usd_next_3_calls) FILTER (WHERE missing_path) AS usd_of_next_3_calls
FROM t07r
GROUP BY 1
HAVING count(*) >= 1000
ORDER BY pct_missing_path DESC;

-- @out by_tool_kind
SELECT agent, tool_kind,
       count(*) AS calls,
       count(*) FILTER (WHERE missing_path) AS missing_path_errors,
       100.0 * count(*) FILTER (WHERE missing_path) / count(*) AS pct_missing_path
FROM t07r
GROUP BY 1, 2
ORDER BY missing_path_errors DESC;

-- @out top_missing_paths
SELECT substr(file_path, 1, 80) AS file_path_80, count(*) AS errors,
       count(DISTINCT session_id) AS sessions
FROM t07r
WHERE missing_path AND file_path IS NOT NULL
GROUP BY 1
ORDER BY errors DESC
LIMIT 20;

-- @headline
SELECT count(*) FILTER (WHERE missing_path) AS missing_path_errors,
       100.0 * count(*) FILTER (WHERE missing_path) / count(*) AS pct_of_file_tool_calls,
       count(DISTINCT session_id) FILTER (WHERE missing_path) AS sessions_affected,
       sum(usd_next_3_calls) FILTER (WHERE missing_path) AS usd_of_the_next_3_calls_after_the_error,
       100.0 * sum(usd_next_3_calls) FILTER (WHERE missing_path)
             / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced) AS pct_of_total_usd
FROM t07r;
