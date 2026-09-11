-- # T05 entry cost: what it costs to say hello
-- The first non-sidechain call of a session pays for the whole system prompt,
-- tool schemas, CLAUDE.md, skills and MCP listings. entry_tokens = input + cache_create.

CREATE OR REPLACE TEMP TABLE t05 AS
WITH f AS (
  SELECT *, row_number() OVER (PARTITION BY session_id ORDER BY seq) AS rn
  FROM calls_priced
  WHERE NOT is_sidechain AND is_priced
), e AS (
  SELECT session_id, agent, harness_version, month, model, provider,
         coalesce(input_tokens, 0) + coalesce(cache_create_tokens, 0) AS entry_tokens,
         CASE WHEN provider = 'anthropic'
              THEN (coalesce(input_tokens, 0) + coalesce(cache_create_tokens, 0)) * p_cache_write_5m / 1e6
              ELSE (coalesce(input_tokens, 0)) * p_input / 1e6 END AS entry_usd,
         coalesce(cost_usd, 0) AS first_call_usd,
         list_transform(string_split(regexp_replace(harness_version, '-.*$', ''), '.'),
                        x -> try_cast(x AS INTEGER)) AS vkey
  FROM f WHERE rn = 1
)
SELECT * FROM e;

-- @out claude_code_by_version
SELECT harness_version, vkey,
       count(*) AS sessions,
       median(entry_tokens) AS median_entry_tokens,
       quantile_cont(entry_tokens, 0.9) AS p90_entry_tokens,
       median(entry_usd) AS median_entry_usd,
       sum(entry_usd) AS total_entry_usd
FROM t05
WHERE agent = 'claude_code' AND harness_version IS NOT NULL
GROUP BY 1, 2
HAVING count(*) >= 50
ORDER BY vkey;

-- @out codex_by_version
SELECT harness_version, vkey,
       count(*) AS sessions,
       median(entry_tokens) AS median_entry_tokens,
       quantile_cont(entry_tokens, 0.9) AS p90_entry_tokens,
       median(entry_usd) AS median_entry_usd,
       sum(entry_usd) AS total_entry_usd
FROM t05
WHERE agent = 'codex' AND harness_version IS NOT NULL
GROUP BY 1, 2
HAVING count(*) >= 20
ORDER BY vkey;

-- @out by_agent_month
SELECT agent, month,
       count(*) AS sessions,
       median(entry_tokens) AS median_entry_tokens,
       quantile_cont(entry_tokens, 0.9) AS p90_entry_tokens,
       median(entry_usd) AS median_entry_usd,
       sum(entry_usd) AS total_entry_usd
FROM t05
WHERE month IS NOT NULL
GROUP BY 1, 2
ORDER BY agent, month;

-- @out totals_by_agent
SELECT agent,
       count(*) AS sessions,
       median(entry_tokens) AS median_entry_tokens,
       sum(entry_tokens) AS total_entry_tokens,
       sum(entry_usd) AS total_entry_usd,
       100.0 * sum(entry_usd) / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced) AS pct_of_total_usd
FROM t05
GROUP BY 1
ORDER BY total_entry_usd DESC;

-- @headline
WITH v AS (
  SELECT harness_version, vkey, count(*) AS sessions,
         median(entry_tokens) AS med_entry,
         median(entry_usd) AS med_usd
  FROM t05 WHERE agent = 'claude_code' AND harness_version IS NOT NULL
  GROUP BY 1, 2 HAVING count(*) >= 50
), r AS (
  SELECT *, row_number() OVER (ORDER BY vkey) AS rn_asc,
            row_number() OVER (ORDER BY vkey DESC) AS rn_desc
  FROM v
)
SELECT (SELECT harness_version FROM r WHERE rn_asc = 1) AS first_claude_code_version,
       (SELECT med_entry FROM r WHERE rn_asc = 1) AS median_entry_tokens_first_version,
       (SELECT harness_version FROM r WHERE rn_desc = 1) AS last_claude_code_version,
       (SELECT med_entry FROM r WHERE rn_desc = 1) AS median_entry_tokens_last_version,
       100.0 * ((SELECT med_entry FROM r WHERE rn_desc = 1) / (SELECT med_entry FROM r WHERE rn_asc = 1) - 1)
         AS pct_change_in_median_entry_tokens,
       (SELECT med_usd FROM r WHERE rn_desc = 1) AS median_entry_usd_last_version,
       (SELECT sum(entry_usd) FROM t05) AS total_entry_usd_all_sessions,
       100.0 * (SELECT sum(entry_usd) FROM t05) / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced)
         AS pct_of_total_usd;
