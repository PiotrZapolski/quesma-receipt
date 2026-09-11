-- # T22 model switch: the same person, the same repo, a different model
-- user = the home directory name in cwd, hashed. Only user x repo pairs with at
-- least two models and at least 3 sessions on each model.

CREATE OR REPLACE TEMP TABLE t22 AS
WITH s AS (
  SELECT user_hash, repo, session_id, session_model, agent, mode,
         session_cost_usd, committed_lines, ctx_tokens, output_tokens, n_calls
  FROM sessions_x
  WHERE n_calls > 0 AND session_model IS NOT NULL AND user_hash <> md5('unknown')[1:10]
), g AS (
  SELECT user_hash, repo, session_model, count(*) AS sessions,
         sum(session_cost_usd) AS usd, sum(committed_lines) AS committed_lines,
         sum(ctx_tokens) AS ctx_tokens, sum(output_tokens) AS output_tokens
  FROM s GROUP BY 1, 2, 3
), q AS (
  SELECT * FROM g WHERE sessions >= 3
)
SELECT * FROM q
WHERE (user_hash, repo) IN (SELECT user_hash, repo FROM q GROUP BY 1, 2 HAVING count(*) >= 2);

-- @out pairs
SELECT user_hash, repo, session_model, sessions, usd, committed_lines,
       usd / nullif(committed_lines, 0) AS usd_per_committed_line,
       ctx_tokens / nullif(committed_lines, 0) AS ctx_tokens_per_committed_line
FROM t22
ORDER BY user_hash, repo, usd DESC;

-- @out model_totals_within_switchers
SELECT session_model,
       count(*) AS user_repo_cells,
       sum(sessions) AS sessions,
       sum(usd) AS usd,
       sum(committed_lines) AS committed_lines,
       sum(usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line,
       sum(output_tokens) / nullif(sum(committed_lines), 0) AS output_tokens_per_committed_line
FROM t22
GROUP BY 1
ORDER BY usd DESC;

-- @out within_pair_comparison
WITH r AS (
  SELECT *, usd / nullif(committed_lines, 0) AS upl,
         row_number() OVER (PARTITION BY user_hash, repo ORDER BY usd / nullif(committed_lines, 0)) AS rn_cheap,
         count(*) OVER (PARTITION BY user_hash, repo) AS n_models
  FROM t22 WHERE committed_lines > 0
)
SELECT user_hash, repo,
       max(CASE WHEN rn_cheap = 1 THEN session_model END) AS cheapest_model,
       max(CASE WHEN rn_cheap = 1 THEN upl END) AS cheapest_usd_per_line,
       max(CASE WHEN rn_cheap = n_models THEN session_model END) AS dearest_model,
       max(CASE WHEN rn_cheap = n_models THEN upl END) AS dearest_usd_per_line,
       max(CASE WHEN rn_cheap = n_models THEN upl END)
         / nullif(max(CASE WHEN rn_cheap = 1 THEN upl END), 0) AS ratio
FROM r
GROUP BY 1, 2
HAVING count(*) >= 2
ORDER BY ratio DESC NULLS LAST
LIMIT 30;

-- @headline
SELECT count(DISTINCT user_hash || '|' || repo) AS user_repo_pairs_that_switched_models,
       count(DISTINCT session_model) AS models_involved,
       sum(sessions) AS sessions,
       sum(usd) AS usd,
       sum(usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line_overall,
       (SELECT median(ratio) FROM (
          SELECT max(upl) / nullif(min(upl), 0) AS ratio FROM (
            SELECT user_hash, repo, session_model, usd / nullif(committed_lines, 0) AS upl
            FROM t22 WHERE committed_lines > 0)
          GROUP BY user_hash, repo HAVING count(*) >= 2)) AS median_dearest_to_cheapest_ratio_within_a_pair
FROM t22;
