-- # T15 harness vs model: who is cheaper per committed line
-- Only repos where at least two different agents were used, so the repo itself is
-- held roughly constant. Cursor is excluded: its transcripts carry no usage at all,
-- so every cursor session would look free.

CREATE OR REPLACE TEMP TABLE t15 AS
SELECT s.*,
       CASE WHEN s.session_model IS NULL THEN 'unknown'
            WHEN s.session_model LIKE '%opus%' THEN 'opus'
            WHEN s.session_model LIKE '%sonnet%' THEN 'sonnet'
            WHEN s.session_model LIKE '%haiku%' THEN 'haiku'
            WHEN s.session_model LIKE '%fable%' THEN 'fable'
            WHEN s.session_model LIKE 'gpt-5.5%' THEN 'gpt-5.5'
            WHEN s.session_model LIKE 'gpt-5.4%' THEN 'gpt-5.4'
            WHEN s.session_model LIKE 'gpt-5.3%' THEN 'gpt-5.3-codex'
            ELSE 'other' END AS model_family
FROM sessions_x s
WHERE s.n_calls > 0
  AND s.agent IS NOT NULL AND s.agent <> 'cursor'
  AND s.repo IN (SELECT repo FROM sessions_x WHERE n_calls > 0 AND agent IS NOT NULL
                 GROUP BY repo HAVING count(DISTINCT agent) >= 2);

-- @out by_agent_model_family
SELECT agent, model_family,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line,
       sum(ctx_tokens) / nullif(sum(committed_lines), 0) AS ctx_tokens_per_committed_line,
       sum(output_tokens) / nullif(sum(committed_lines), 0) AS output_tokens_per_committed_line
FROM t15
GROUP BY 1, 2
HAVING count(*) >= 10
ORDER BY usd DESC;

-- @out by_mode
SELECT mode, agent,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line
FROM t15
GROUP BY 1, 2
HAVING count(*) >= 10
ORDER BY mode, usd DESC;

-- @out by_repo_agent
SELECT repo, agent,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line
FROM t15
GROUP BY 1, 2
HAVING count(*) >= 10 AND sum(committed_lines) > 0
ORDER BY repo, usd DESC;

-- @headline
WITH a AS (
  SELECT agent, sum(session_cost_usd) AS usd, sum(committed_lines) AS lines_,
         sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS upl
  FROM t15 WHERE agent IS NOT NULL GROUP BY 1
)
SELECT (SELECT count(DISTINCT repo) FROM t15) AS repos_with_two_or_more_agents,
       (SELECT agent FROM a ORDER BY upl LIMIT 1) AS cheapest_agent_per_committed_line,
       (SELECT upl FROM a ORDER BY upl LIMIT 1) AS cheapest_usd_per_committed_line,
       (SELECT agent FROM a ORDER BY upl DESC LIMIT 1) AS dearest_agent_per_committed_line,
       (SELECT upl FROM a ORDER BY upl DESC LIMIT 1) AS dearest_usd_per_committed_line,
       (SELECT max(upl) / nullif(min(upl), 0) FROM a) AS ratio_dearest_to_cheapest;
