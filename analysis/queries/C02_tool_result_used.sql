-- # C02 case file: big tool results and whether anything used them
-- 300 highest-rent results + 300 random results over 5k chars.

SELECT setseed(0.43);

CREATE OR REPLACE TEMP TABLE c02_pool AS
SELECT tc.session_id, tc.agent, s.mode, s.repo, tc.seq, tc.tool_kind, tc.tool_name,
       substr(coalesce(tc.command_head, tc.file_path), 1, 200) AS what,
       tc.result_chars,
       greatest(s.n_calls - p.calls_before, 0) AS later_calls,
       (tc.result_chars / 4.0) * greatest(s.n_calls - p.calls_before, 0) AS rent_tokens,
       (tc.result_chars / 4.0) * greatest(s.n_calls - p.calls_before, 0) * s.p_cache_read / 1e6 AS rent_usd
FROM tool_calls tc
JOIN seq_pos p ON p.session_id = tc.session_id AND p.seq = tc.seq
JOIN sessions_x s ON s.session_id = tc.session_id
WHERE coalesce(tc.result_chars, 0) > 0;

-- @out tool_result_used
WITH top AS (
  SELECT *, 'top_by_rent' AS stratum_pick
  FROM c02_pool ORDER BY rent_usd DESC NULLS LAST LIMIT 300
), rnd AS (
  SELECT * FROM (
    SELECT p.*, 'random_over_5k' AS stratum_pick,
           row_number() OVER (PARTITION BY p.agent, p.tool_kind ORDER BY random()) AS rn
    FROM c02_pool p
    WHERE p.result_chars > 5000
      AND p.session_id || ':' || p.seq NOT IN (SELECT session_id || ':' || seq FROM top)
  ) WHERE rn <= 25 LIMIT 300
)
SELECT session_id, seq, 3 AS k_before, 12 AS k_after,
       agent, mode, repo, tool_kind, tool_name, what,
       result_chars, later_calls, rent_tokens, rent_usd,
       stratum_pick, agent || '|' || tool_kind AS stratum
FROM (SELECT * EXCLUDE (rn) FROM rnd UNION ALL SELECT * FROM top)
ORDER BY stratum_pick, rent_usd DESC;

-- @headline
SELECT count(*) AS pool_of_tool_results,
       count(*) FILTER (WHERE result_chars > 5000) AS results_over_5k_chars,
       sum(rent_usd) AS rent_usd_in_pool,
       median(result_chars) AS median_result_chars,
       count(DISTINCT session_id) AS sessions_in_pool
FROM c02_pool;
