-- # T04 context rent: every tool result is re-read by every later call
-- rent_tokens = result_chars/4 x number of non-sidechain calls that come after the
-- result in the same session. Priced at the session model's cache read price,
-- because that is what the prefix actually costs once it is cached.
-- CAVEAT: this assumes a result stays in context for the rest of the session. That
-- holds well for claude_code (rent = 51% of the cache read tokens actually billed)
-- but overshoots codex by ~10x, because codex compacts and its sessions reach 10k
-- calls. Read the codex number as an upper bound; the claude_code one as real.

CREATE OR REPLACE TEMP TABLE t04 AS
SELECT tc.session_id, tc.agent, tc.seq, tc.tool_kind, tc.tool_name,
       tc.command_head, tc.file_path, tc.result_chars,
       greatest(s.n_calls - p.calls_before, 0) AS later_calls,
       (tc.result_chars / 4.0) * greatest(s.n_calls - p.calls_before, 0) AS rent_tokens,
       (tc.result_chars / 4.0) * greatest(s.n_calls - p.calls_before, 0) * s.p_cache_read / 1e6 AS rent_usd
FROM tool_calls tc
JOIN seq_pos p ON p.session_id = tc.session_id AND p.seq = tc.seq
JOIN sessions_x s ON s.session_id = tc.session_id
WHERE coalesce(tc.result_chars, 0) > 0;

-- @out by_tool_kind
SELECT agent, tool_kind,
       count(*) AS tool_results,
       sum(result_chars) AS result_chars,
       avg(later_calls) AS avg_later_calls,
       sum(rent_tokens) AS rent_tokens,
       sum(rent_usd) AS rent_usd
FROM t04
GROUP BY 1, 2
ORDER BY rent_usd DESC NULLS LAST
LIMIT 40;

-- @out by_result_size_bucket
SELECT CASE WHEN result_chars < 1000 THEN '1. <1k'
            WHEN result_chars < 10000 THEN '2. 1-10k'
            WHEN result_chars < 50000 THEN '3. 10-50k'
            ELSE '4. >50k' END AS size_bucket,
       count(*) AS tool_results,
       100.0 * count(*) / sum(count(*)) OVER () AS pct_of_results,
       sum(result_chars) AS result_chars,
       100.0 * sum(result_chars) / sum(sum(result_chars)) OVER () AS pct_of_result_chars,
       avg(later_calls) AS avg_later_calls,
       sum(rent_tokens) AS rent_tokens,
       sum(rent_usd) AS rent_usd,
       100.0 * sum(rent_usd) / sum(sum(rent_usd)) OVER () AS pct_of_rent_usd
FROM t04
GROUP BY 1
ORDER BY 1;

-- @out rent_vs_actual_cache_read
SELECT t.agent,
       sum(t.rent_tokens) AS rent_tokens,
       c.cache_read_tokens,
       100.0 * sum(t.rent_tokens) / nullif(c.cache_read_tokens, 0) AS pct_of_cache_read_tokens,
       sum(t.rent_usd) AS rent_usd,
       c.cache_read_usd,
       100.0 * sum(t.rent_usd) / nullif(c.cache_read_usd, 0) AS pct_of_cache_read_usd
FROM t04 t
JOIN (SELECT agent, sum(coalesce(cache_read_tokens, 0)) AS cache_read_tokens,
             sum(coalesce(cache_read_usd, 0)) AS cache_read_usd
      FROM calls_priced GROUP BY 1) c USING (agent)
GROUP BY 1, c.cache_read_tokens, c.cache_read_usd
ORDER BY rent_usd DESC NULLS LAST;

-- @out top20_single_results_by_rent
SELECT session_id, seq, agent, tool_kind,
       coalesce(substr(command_head, 1, 70), substr(file_path, 1, 70)) AS what,
       result_chars, later_calls, rent_tokens, rent_usd
FROM t04
ORDER BY rent_usd DESC NULLS LAST
LIMIT 20;

-- @headline
SELECT 100.0 * (SELECT sum(rent_tokens) FROM t04 WHERE agent = 'claude_code')
             / (SELECT sum(coalesce(cache_read_tokens, 0)) FROM calls_priced WHERE agent = 'claude_code')
         AS pct_of_claude_code_cache_read_tokens_from_tool_results,
       sum(rent_usd) FILTER (WHERE agent = 'claude_code') AS rent_usd_claude_code,
       sum(rent_usd) AS rent_usd_all_agents_upper_bound,
       sum(rent_usd) FILTER (WHERE result_chars > 10000) AS rent_usd_from_results_over_10k_chars,
       100.0 * sum(rent_usd) FILTER (WHERE result_chars > 10000) / sum(rent_usd) AS pct_of_rent_from_results_over_10k,
       100.0 * count(*) FILTER (WHERE result_chars > 10000) / count(*) AS pct_of_results_over_10k_chars,
       sum(rent_tokens) AS rent_tokens_all_agents_upper_bound
FROM t04;
