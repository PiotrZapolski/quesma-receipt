-- # T01 baseline: what the whole population costs
-- Denominator for every other thesis. Cursor has no usage data at all, so it is
-- priced at 0 and shows up only in the unpriced table.

-- @out by_agent
SELECT agent,
       count(DISTINCT session_id) AS sessions,
       count(*) AS calls,
       sum(coalesce(cost_usd, 0)) AS usd,
       100.0 * sum(coalesce(cost_usd, 0))
             / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced) AS pct_of_total_usd,
       sum(coalesce(input_tokens, 0)) AS input_tokens,
       sum(coalesce(cache_read_tokens, 0)) AS cache_read_tokens,
       sum(c5m_tokens + c1h_tokens) AS cache_write_tokens,
       sum(coalesce(output_tokens, 0)) AS output_tokens,
       sum(coalesce(ctx_tokens, 0)) AS ctx_tokens
FROM calls_priced
GROUP BY 1
ORDER BY usd DESC;

-- @out by_model
SELECT model, any_value(provider) AS provider,
       count(*) AS calls,
       count(DISTINCT session_id) AS sessions,
       sum(coalesce(cost_usd, 0)) AS usd,
       sum(coalesce(input_usd, 0)) AS input_usd,
       sum(coalesce(cache_read_usd, 0)) AS cache_read_usd,
       sum(coalesce(cache_write_usd, 0)) AS cache_write_usd,
       sum(coalesce(output_usd, 0)) AS output_usd
FROM calls_priced
GROUP BY 1
ORDER BY usd DESC;

-- @out components_by_agent
WITH a AS (
  SELECT agent,
         sum(coalesce(input_usd, 0)) AS input_usd,
         sum(coalesce(cache_read_usd, 0)) AS cache_read_usd,
         sum(coalesce(cache_write_usd, 0)) AS cache_write_usd,
         sum(coalesce(output_usd, 0)) AS output_usd,
         sum(coalesce(cost_usd, 0)) AS usd
  FROM calls_priced GROUP BY 1
)
SELECT agent, usd, input_usd, cache_read_usd, cache_write_usd, output_usd,
       100.0 * input_usd / nullif(usd, 0) AS pct_input,
       100.0 * cache_read_usd / nullif(usd, 0) AS pct_cache_read,
       100.0 * cache_write_usd / nullif(usd, 0) AS pct_cache_write,
       100.0 * output_usd / nullif(usd, 0) AS pct_output
FROM a
UNION ALL
SELECT 'ALL', sum(usd), sum(input_usd), sum(cache_read_usd), sum(cache_write_usd), sum(output_usd),
       100.0 * sum(input_usd) / nullif(sum(usd), 0),
       100.0 * sum(cache_read_usd) / nullif(sum(usd), 0),
       100.0 * sum(cache_write_usd) / nullif(sum(usd), 0),
       100.0 * sum(output_usd) / nullif(sum(usd), 0)
FROM a
ORDER BY usd DESC;

-- @out usd_per_session
SELECT agent,
       count(*) AS sessions,
       avg(session_cost_usd) AS mean_usd,
       quantile_cont(session_cost_usd, 0.5) AS p50_usd,
       quantile_cont(session_cost_usd, 0.9) AS p90_usd,
       quantile_cont(session_cost_usd, 0.99) AS p99_usd,
       max(session_cost_usd) AS max_usd
FROM sessions_x
WHERE session_cost_usd IS NOT NULL AND n_calls > 0
GROUP BY 1
ORDER BY sessions DESC;

-- @out per_committed_line_by_mode
SELECT mode,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line,
       sum(ctx_tokens) / nullif(sum(committed_lines), 0) AS ctx_tokens_per_committed_line,
       sum(output_tokens) / nullif(sum(committed_lines), 0) AS output_tokens_per_committed_line
FROM sessions_x
WHERE n_calls > 0
GROUP BY 1
ORDER BY usd DESC;

-- @out per_committed_line_by_agent_mode
SELECT agent, mode,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line
FROM sessions_x
WHERE n_calls > 0
GROUP BY 1, 2
ORDER BY usd DESC;

-- @out unpriced_share
SELECT agent,
       count(*) AS calls,
       count(*) FILTER (WHERE NOT is_priced) AS unpriced_calls,
       100.0 * count(*) FILTER (WHERE NOT is_priced) / count(*) AS pct_calls_unpriced,
       sum(coalesce(ctx_tokens, 0) + coalesce(output_tokens, 0)) AS all_tokens,
       sum(CASE WHEN NOT is_priced THEN coalesce(ctx_tokens, 0) + coalesce(output_tokens, 0) ELSE 0 END) AS unpriced_tokens,
       100.0 * sum(CASE WHEN NOT is_priced THEN coalesce(ctx_tokens, 0) + coalesce(output_tokens, 0) ELSE 0 END)
             / nullif(sum(coalesce(ctx_tokens, 0) + coalesce(output_tokens, 0)), 0) AS pct_tokens_unpriced
FROM calls_priced
GROUP BY 1
ORDER BY calls DESC;

-- @out unpriced_models
SELECT model, count(*) AS calls,
       sum(coalesce(ctx_tokens, 0)) AS ctx_tokens,
       sum(coalesce(output_tokens, 0)) AS output_tokens
FROM calls_priced
WHERE NOT is_priced
GROUP BY 1
ORDER BY calls DESC;

-- @headline
SELECT sum(coalesce(cost_usd, 0)) AS total_usd,
       sum(coalesce(cost_usd, 0)) FILTER (WHERE agent = 'claude_code') AS usd_claude_code,
       sum(coalesce(cost_usd, 0)) FILTER (WHERE agent = 'codex') AS usd_codex,
       sum(coalesce(cost_usd, 0)) FILTER (WHERE agent = 'opencode') AS usd_opencode,
       100.0 * sum(coalesce(cache_read_usd, 0)) / sum(coalesce(cost_usd, 0)) AS pct_usd_cache_read,
       100.0 * sum(coalesce(cache_write_usd, 0)) / sum(coalesce(cost_usd, 0)) AS pct_usd_cache_write,
       100.0 * sum(coalesce(output_usd, 0)) / sum(coalesce(cost_usd, 0)) AS pct_usd_output,
       100.0 * sum(coalesce(input_usd, 0)) / sum(coalesce(cost_usd, 0)) AS pct_usd_fresh_input,
       100.0 * count(*) FILTER (WHERE NOT is_priced) / count(*) AS pct_calls_unpriced,
       (SELECT sum(coalesce(cost_usd, 0)) / nullif(sum(committed_lines), 0) FROM sessions_x) AS usd_per_committed_line_all
FROM calls_priced;
