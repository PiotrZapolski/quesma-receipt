-- # T13 abandoned: sessions that produced no committed line
-- committed_lines = attr_total_committed from the catalog. 0 means the work never
-- reached a commit; NULL means the attribution job never ran for that session.

CREATE OR REPLACE TEMP TABLE t13 AS
SELECT s.*,
       CASE WHEN s.committed_lines IS NULL THEN 'no attribution'
            WHEN s.committed_lines = 0 THEN 'zero committed lines'
            ELSE 'committed' END AS outcome
FROM sessions_x s
WHERE s.n_calls > 0;

-- @out by_agent
SELECT agent, outcome,
       count(*) AS sessions,
       100.0 * count(*) / sum(count(*)) OVER (PARTITION BY agent) AS pct_of_agent_sessions,
       sum(session_cost_usd) AS usd,
       100.0 * sum(session_cost_usd) / nullif(sum(sum(session_cost_usd)) OVER (PARTITION BY agent), 0) AS pct_of_agent_usd,
       median(session_cost_usd) AS median_session_usd,
       median(n_calls) AS median_calls
FROM t13
GROUP BY 1, 2
ORDER BY agent, outcome;

-- @out by_mode
SELECT mode, outcome,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       100.0 * sum(session_cost_usd) / (SELECT sum(session_cost_usd) FROM t13) AS pct_of_all_usd,
       median(n_human_turns) AS median_human_turns,
       median(n_tool_calls) AS median_tool_calls
FROM t13
GROUP BY 1, 2
ORDER BY usd DESC;

-- @out size_of_abandoned_sessions
SELECT CASE WHEN session_cost_usd < 0.1 THEN '1. <0.1 USD'
            WHEN session_cost_usd < 1 THEN '2. 0.1-1 USD'
            WHEN session_cost_usd < 10 THEN '3. 1-10 USD'
            ELSE '4. >10 USD' END AS usd_bucket,
       count(*) AS abandoned_sessions,
       sum(session_cost_usd) AS usd,
       median(n_calls) AS median_calls,
       median(n_human_turns) AS median_human_turns
FROM t13
WHERE outcome <> 'committed'
GROUP BY 1
ORDER BY 1;

-- @out where_do_they_die
-- relative position of the last human prompt inside the session, 0 = start, 1 = end
WITH lastq AS (
  SELECT u.session_id, max(u.seq) AS last_user_seq
  FROM user_turns u
  WHERE NOT coalesce(u.is_meta, false) AND u.human_chars > 0
  GROUP BY 1
), pos AS (
  SELECT t.session_id, t.agent, t.outcome, t.session_cost_usd,
         p.calls_before * 1.0 / nullif(t.n_calls, 0) AS rel_position
  FROM t13 t JOIN lastq l USING (session_id)
  JOIN seq_pos p ON p.session_id = t.session_id AND p.seq = l.last_user_seq
  WHERE t.n_calls > 3
), o AS (
  SELECT outcome, rel_position, session_cost_usd,
         sum(session_cost_usd) OVER (PARTITION BY outcome ORDER BY rel_position) AS cum_usd,
         sum(session_cost_usd) OVER (PARTITION BY outcome) AS tot_usd
  FROM pos
)
SELECT outcome,
       count(*) AS sessions,
       median(rel_position) AS median_position_of_last_prompt,
       min(rel_position) FILTER (WHERE cum_usd >= 0.5 * tot_usd) AS usd_weighted_median_position,
       sum(session_cost_usd) AS usd
FROM o
GROUP BY 1
ORDER BY usd DESC;

-- @out most_expensive_abandoned
SELECT session_id, agent, repo, mode, session_cost_usd, n_calls, n_human_turns, n_tool_calls, outcome
FROM t13
WHERE outcome <> 'committed'
ORDER BY session_cost_usd DESC
LIMIT 20;

-- @headline
SELECT count(*) FILTER (WHERE outcome <> 'committed') AS abandoned_sessions,
       100.0 * count(*) FILTER (WHERE outcome <> 'committed') / count(*) AS pct_of_sessions_abandoned,
       sum(session_cost_usd) FILTER (WHERE outcome <> 'committed') AS usd_abandoned,
       100.0 * sum(session_cost_usd) FILTER (WHERE outcome <> 'committed')
             / sum(session_cost_usd) AS pct_of_total_usd_abandoned,
       sum(session_cost_usd) FILTER (WHERE outcome = 'zero committed lines') AS usd_zero_committed_lines,
       sum(session_cost_usd) FILTER (WHERE outcome = 'no attribution') AS usd_no_attribution,
       median(session_cost_usd) FILTER (WHERE outcome <> 'committed') AS median_usd_of_an_abandoned_session
FROM t13;
