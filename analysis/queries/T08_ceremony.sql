-- # T08 ceremony: todo lists and task hand-offs
-- tool_kind todo (TodoWrite and friends) and task (sub agent dispatch). The tool
-- input is generated text, so its cost is output tokens: input_chars/4.

CREATE OR REPLACE TEMP TABLE t08 AS
SELECT tc.session_id, tc.agent, tc.seq, tc.tool_kind, tc.input_chars, tc.result_chars,
       s.mode, s.committed_lines, s.p_output,
       coalesce(tc.input_chars, 0) / 4.0 AS ceremony_tokens,
       coalesce(tc.input_chars, 0) / 4.0 * s.p_output / 1e6 AS ceremony_usd
FROM tool_calls tc
JOIN sessions_x s USING (session_id);

-- @out by_agent
SELECT agent,
       count(*) AS tool_calls,
       count(*) FILTER (WHERE tool_kind IN ('todo', 'task')) AS ceremony_calls,
       100.0 * count(*) FILTER (WHERE tool_kind IN ('todo', 'task')) / count(*) AS pct_of_tool_calls,
       sum(ceremony_tokens) FILTER (WHERE tool_kind = 'todo') AS todo_tokens,
       sum(ceremony_tokens) FILTER (WHERE tool_kind = 'task') AS task_tokens,
       sum(ceremony_usd) FILTER (WHERE tool_kind IN ('todo', 'task')) AS ceremony_usd
FROM t08
GROUP BY 1
ORDER BY ceremony_usd DESC NULLS LAST;

-- @out sessions_with_vs_without
WITH s AS (
  SELECT session_id, any_value(agent) AS agent, any_value(mode) AS mode,
         any_value(committed_lines) AS committed_lines,
         count(*) FILTER (WHERE tool_kind IN ('todo', 'task')) AS ceremony_calls
  FROM t08 GROUP BY 1
), j AS (
  SELECT s.*, x.session_cost_usd FROM s JOIN sessions_x x USING (session_id)
)
SELECT mode,
       CASE WHEN ceremony_calls > 0 THEN 'uses todo/task' ELSE 'no todo/task' END AS kind,
       count(*) AS sessions,
       100.0 * count(*) FILTER (WHERE committed_lines > 0) / count(*) AS pct_sessions_with_commits,
       sum(session_cost_usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line
FROM j
GROUP BY 1, 2
ORDER BY mode, kind;

-- @out by_agent_and_kind
SELECT agent, tool_kind,
       count(*) AS calls,
       sum(ceremony_tokens) AS tokens,
       sum(ceremony_usd) AS usd,
       median(input_chars) AS median_input_chars
FROM t08
WHERE tool_kind IN ('todo', 'task')
GROUP BY 1, 2
ORDER BY usd DESC NULLS LAST;

-- @headline
SELECT count(*) FILTER (WHERE tool_kind IN ('todo', 'task')) AS ceremony_tool_calls,
       100.0 * count(*) FILTER (WHERE tool_kind IN ('todo', 'task')) / count(*) AS pct_of_all_tool_calls,
       sum(ceremony_tokens) FILTER (WHERE tool_kind IN ('todo', 'task')) AS output_tokens_spent_on_ceremony,
       sum(ceremony_usd) FILTER (WHERE tool_kind IN ('todo', 'task')) AS ceremony_usd,
       100.0 * sum(ceremony_usd) FILTER (WHERE tool_kind IN ('todo', 'task'))
             / (SELECT sum(coalesce(output_usd, 0)) FROM calls_priced) AS pct_of_all_output_usd
FROM t08;
