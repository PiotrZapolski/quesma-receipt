-- # T06 truncated: responses that hit the output cap
-- stop_reason max_tokens (anthropic) or length (openai). The continuation re-pays
-- the whole context, so the next call's input side is the direct waste.

CREATE OR REPLACE TEMP TABLE t06 AS
SELECT session_id, agent, seq, model, stop_reason, output_tokens, ctx_tokens,
       coalesce(cost_usd, 0) AS cost_usd,
       lead(coalesce(input_usd, 0) + coalesce(cache_read_usd, 0) + coalesce(cache_write_usd, 0))
         OVER w AS next_call_input_usd,
       lead(ctx_tokens) OVER w AS next_call_ctx_tokens,
       stop_reason IN ('max_tokens', 'length') AS truncated
FROM calls_priced
WHERE NOT is_sidechain
WINDOW w AS (PARTITION BY session_id ORDER BY seq);

-- @out by_agent
SELECT agent,
       count(*) AS calls,
       count(*) FILTER (WHERE truncated) AS truncated_calls,
       100.0 * count(*) FILTER (WHERE truncated) / count(*) AS pct_calls_truncated,
       sum(next_call_input_usd) FILTER (WHERE truncated) AS usd_of_continuation_input,
       sum(next_call_ctx_tokens) FILTER (WHERE truncated) AS continuation_ctx_tokens
FROM t06
GROUP BY 1
ORDER BY truncated_calls DESC;

-- @out by_model
SELECT model, stop_reason,
       count(*) AS truncated_calls,
       count(DISTINCT session_id) AS sessions,
       avg(output_tokens) AS avg_output_tokens,
       sum(next_call_input_usd) AS usd_of_continuation_input
FROM t06
WHERE truncated
GROUP BY 1, 2
ORDER BY truncated_calls DESC;

-- @out stop_reason_distribution
SELECT agent, stop_reason, count(*) AS calls,
       100.0 * count(*) / sum(count(*)) OVER (PARTITION BY agent) AS pct_of_agent_calls
FROM t06
GROUP BY 1, 2
ORDER BY agent, calls DESC;

-- @headline
SELECT count(*) FILTER (WHERE truncated) AS truncated_calls,
       100.0 * count(*) FILTER (WHERE truncated) / count(*) AS pct_of_all_calls_truncated,
       count(DISTINCT session_id) FILTER (WHERE truncated) AS sessions_affected,
       sum(next_call_input_usd) FILTER (WHERE truncated) AS usd_paid_to_resume_after_truncation,
       100.0 * coalesce(sum(next_call_input_usd) FILTER (WHERE truncated), 0)
             / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced) AS pct_of_total_usd
FROM t06;
