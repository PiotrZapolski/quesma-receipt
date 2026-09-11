-- # T09 polling: sleep, wait, gh run watch
-- Bash commands whose only job is to wait. Each one still pays for the whole
-- context of the call that issued it.

CREATE OR REPLACE TEMP TABLE t09 AS
SELECT tc.session_id, tc.agent, tc.seq, tc.command_head, tc.result_chars,
       p.calls_before,
       regexp_matches(coalesce(tc.command_head, ''),
         '(^|[;&| ])sleep [0-9]+|gh run watch|(^|[;&| ])wait($|[;&| ])') AS is_poll
FROM tool_calls tc
JOIN seq_pos p ON p.session_id = tc.session_id AND p.seq = tc.seq
WHERE tc.tool_kind = 'bash' AND tc.command_head IS NOT NULL;

CREATE OR REPLACE TEMP TABLE t09p AS
SELECT t.*, ci.cost_usd AS call_usd, ci.ctx_tokens,
       count(*) OVER (PARTITION BY t.session_id ORDER BY t.calls_before
                      RANGE BETWEEN CURRENT ROW AND 4 FOLLOWING) AS polls_in_next_5_calls
FROM t09 t
LEFT JOIN calls_idx ci ON ci.session_id = t.session_id AND ci.call_idx = t.calls_before
WHERE t.is_poll;

-- @out by_agent
SELECT t.agent,
       (SELECT count(*) FROM t09 x WHERE x.agent = t.agent) AS bash_calls,
       count(*) AS polling_calls,
       100.0 * count(*) / (SELECT count(*) FROM t09 x WHERE x.agent = t.agent) AS pct_of_bash_calls,
       count(DISTINCT t.session_id) AS sessions,
       sum(t.call_usd) AS usd_of_the_calls_that_issued_them,
       sum(t.ctx_tokens) AS ctx_tokens
FROM t09p t
GROUP BY 1
ORDER BY polling_calls DESC;

-- @out polling_sequences
SELECT CASE WHEN polls_in_next_5_calls >= 4 THEN '4+ polls in 5 calls'
            WHEN polls_in_next_5_calls = 3 THEN '3 polls in 5 calls'
            WHEN polls_in_next_5_calls = 2 THEN '2 polls in 5 calls'
            ELSE 'isolated' END AS burst,
       count(*) AS polling_calls,
       sum(call_usd) AS usd,
       sum(ctx_tokens) AS ctx_tokens
FROM t09p
GROUP BY 1
ORDER BY polling_calls DESC;

-- @out top_polling_commands
SELECT substr(command_head, 1, 80) AS command_head_80,
       count(*) AS polling_calls,
       count(DISTINCT session_id) AS sessions,
       sum(call_usd) AS usd
FROM t09p
GROUP BY 1
ORDER BY polling_calls DESC
LIMIT 20;

-- @headline
SELECT count(*) AS polling_bash_calls,
       100.0 * count(*) / (SELECT count(*) FROM t09) AS pct_of_all_bash_calls,
       count(DISTINCT session_id) AS sessions_that_poll,
       sum(call_usd) AS usd_of_calls_that_issued_a_poll,
       count(*) FILTER (WHERE polls_in_next_5_calls >= 2) AS polls_inside_a_burst,
       sum(call_usd) FILTER (WHERE polls_in_next_5_calls >= 2) AS usd_in_bursts,
       100.0 * sum(call_usd) / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced) AS pct_of_total_usd
FROM t09p;
