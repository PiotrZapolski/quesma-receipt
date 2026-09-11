-- # T03 zero info: tool results the model has already seen verbatim
-- A repeat = a tool result whose sha1 already appeared earlier in the SAME session.
-- Direct USD is a lower bound: repeated chars / 4 tokens at the session input price.

CREATE OR REPLACE TEMP TABLE t03 AS
SELECT tc.session_id, tc.agent, tc.tool_kind, tc.tool_name, tc.seq,
       tc.command_head, tc.file_path, tc.result_chars,
       row_number() OVER (PARTITION BY tc.session_id, tc.result_hash ORDER BY tc.seq) AS occ,
       count(*) OVER (PARTITION BY tc.session_id, tc.result_hash) AS occ_total
FROM tool_calls tc
WHERE tc.result_hash IS NOT NULL AND coalesce(tc.result_chars, 0) > 0;

-- @out by_agent
SELECT agent,
       count(*) AS tool_results,
       count(*) FILTER (WHERE occ > 1) AS repeated_results,
       100.0 * count(*) FILTER (WHERE occ > 1) / count(*) AS pct_results_repeated,
       sum(result_chars) AS result_chars,
       sum(result_chars) FILTER (WHERE occ > 1) AS repeated_chars,
       100.0 * sum(result_chars) FILTER (WHERE occ > 1) / sum(result_chars) AS pct_chars_repeated
FROM t03
GROUP BY 1
ORDER BY result_chars DESC;

-- @out by_tool_kind
SELECT agent, tool_kind,
       count(*) AS tool_results,
       count(*) FILTER (WHERE occ > 1) AS repeated_results,
       100.0 * count(*) FILTER (WHERE occ > 1) / count(*) AS pct_results_repeated,
       sum(result_chars) FILTER (WHERE occ > 1) AS repeated_chars,
       100.0 * sum(result_chars) FILTER (WHERE occ > 1) / nullif(sum(result_chars), 0) AS pct_chars_repeated
FROM t03
GROUP BY 1, 2
HAVING count(*) >= 500
ORDER BY repeated_chars DESC;

-- @out usd_by_agent
SELECT t.agent,
       sum(t.result_chars) FILTER (WHERE t.occ > 1) AS repeated_chars,
       sum(t.result_chars / 4.0) FILTER (WHERE t.occ > 1) AS repeated_tokens,
       sum((t.result_chars / 4.0) * s.p_input / 1e6) FILTER (WHERE t.occ > 1) AS usd_lower_bound,
       sum((t.result_chars / 4.0) * s.p_cache_read / 1e6) FILTER (WHERE t.occ > 1) AS usd_if_cached_once
FROM t03 t JOIN sessions_x s USING (session_id)
GROUP BY 1
ORDER BY usd_lower_bound DESC NULLS LAST;

-- @out top_repeated_bash_commands
SELECT substr(command_head, 1, 90) AS command_head_90,
       count(*) FILTER (WHERE occ > 1) AS repeated_occurrences,
       count(DISTINCT session_id) AS sessions,
       sum(result_chars) FILTER (WHERE occ > 1) AS repeated_chars
FROM t03
WHERE tool_kind = 'bash' AND command_head IS NOT NULL
GROUP BY 1
HAVING count(*) FILTER (WHERE occ > 1) > 0
ORDER BY repeated_occurrences DESC
LIMIT 20;

-- @out top_repeated_files
SELECT substr(file_path, 1, 90) AS file_path_90, tool_kind,
       count(*) FILTER (WHERE occ > 1) AS repeated_occurrences,
       count(DISTINCT session_id) AS sessions,
       sum(result_chars) FILTER (WHERE occ > 1) AS repeated_chars
FROM t03
WHERE tool_kind = 'read' AND file_path IS NOT NULL
GROUP BY 1, 2
HAVING count(*) FILTER (WHERE occ > 1) > 0
ORDER BY repeated_chars DESC
LIMIT 20;

-- @out worst_offender_sessions
SELECT session_id, any_value(agent) AS agent,
       count(*) FILTER (WHERE occ > 1) AS repeated_results,
       sum(result_chars) FILTER (WHERE occ > 1) AS repeated_chars,
       max(occ_total) AS max_times_same_result
FROM t03
GROUP BY 1
ORDER BY repeated_chars DESC NULLS LAST
LIMIT 20;

-- @headline
SELECT 100.0 * sum(result_chars) FILTER (WHERE occ > 1) / sum(result_chars) AS pct_of_tool_result_chars_exact_repeats,
       count(*) FILTER (WHERE occ > 1) AS repeated_tool_results,
       100.0 * count(*) FILTER (WHERE occ > 1) / count(*) AS pct_of_tool_results_repeated,
       sum(result_chars) FILTER (WHERE occ > 1) AS repeated_chars,
       (SELECT sum((t.result_chars / 4.0) * s.p_input / 1e6)
        FROM t03 t JOIN sessions_x s USING (session_id) WHERE t.occ > 1) AS usd_lower_bound_fresh_input
FROM t03;
