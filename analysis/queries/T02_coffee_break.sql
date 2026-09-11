-- # T02 coffee break: the cache expires while the human is away
-- claude_code only (the only harness that reports cache_creation), non-sidechain
-- calls ordered by ts inside the session. A "cache break" is a call that had to
-- re-write at least half of the previous context as fresh cache.

CREATE OR REPLACE TEMP TABLE t02 AS
WITH c AS (
  SELECT session_id, seq, ts, month, ctx_tokens, cache_create_tokens,
         c5m_tokens, c1h_tokens, cache_write_usd, cost_usd, model,
         lag(ctx_tokens) OVER w AS prev_ctx,
         lag(ts) OVER w AS prev_ts
  FROM calls_priced
  WHERE agent = 'claude_code' AND NOT is_sidechain AND ts IS NOT NULL
  WINDOW w AS (PARTITION BY session_id ORDER BY ts, seq)
)
SELECT *,
       date_diff('millisecond', prev_ts, ts) / 60000.0 AS gap_min,
       CASE WHEN prev_ctx > 0 AND coalesce(cache_create_tokens, 0) >= 0.5 * prev_ctx
            THEN true ELSE false END AS cache_break,
       CASE WHEN date_diff('millisecond', prev_ts, ts) / 60000.0 < 1 THEN '1. <1 min'
            WHEN date_diff('millisecond', prev_ts, ts) / 60000.0 < 5 THEN '2. 1-5 min'
            WHEN date_diff('millisecond', prev_ts, ts) / 60000.0 < 60 THEN '3. 5-60 min'
            ELSE '4. >60 min' END AS gap_bucket
FROM c
WHERE prev_ts IS NOT NULL;

-- @out by_gap_bucket
SELECT gap_bucket,
       count(*) AS calls,
       100.0 * count(*) / sum(count(*)) OVER () AS pct_of_calls,
       count(*) FILTER (WHERE cache_break) AS breaks,
       100.0 * count(*) FILTER (WHERE cache_break) / count(*) AS break_rate_pct,
       sum(coalesce(cache_create_tokens, 0)) AS recached_tokens,
       sum(coalesce(cache_create_tokens, 0)) FILTER (WHERE cache_break) AS recached_tokens_on_breaks,
       sum(coalesce(cache_write_usd, 0)) AS cache_write_usd,
       sum(coalesce(cache_write_usd, 0)) FILTER (WHERE cache_break) AS cache_write_usd_on_breaks,
       median(gap_min) AS median_gap_min
FROM t02
GROUP BY 1
ORDER BY 1;

-- @out break_rate_fine_grained
SELECT CASE WHEN gap_min < 0.25 THEN '1. <15 s'
            WHEN gap_min < 1 THEN '2. 15-60 s'
            WHEN gap_min < 5 THEN '3. 1-5 min'
            WHEN gap_min < 20 THEN '4. 5-20 min'
            WHEN gap_min < 60 THEN '5. 20-60 min'
            WHEN gap_min < 300 THEN '6. 1-5 h'
            ELSE '7. >5 h' END AS gap_bucket,
       count(*) AS calls,
       100.0 * count(*) FILTER (WHERE cache_break) / count(*) AS break_rate_pct,
       sum(coalesce(cache_write_usd, 0)) AS cache_write_usd
FROM t02
GROUP BY 1
ORDER BY 1;

-- @out ttl_era_by_month
SELECT month,
       count(*) AS calls,
       sum(c5m_tokens) AS cache_write_5m_tokens,
       sum(c1h_tokens) AS cache_write_1h_tokens,
       100.0 * sum(c1h_tokens) / nullif(sum(c5m_tokens + c1h_tokens), 0) AS pct_tokens_1h,
       sum(coalesce(cache_write_usd, 0)) AS cache_write_usd,
       100.0 * count(*) FILTER (WHERE cache_break) / count(*) AS break_rate_pct
FROM t02
WHERE month IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- @out gap_gt_5min_by_month
SELECT month,
       count(*) FILTER (WHERE gap_min > 5) AS calls_after_gap_gt_5min,
       sum(coalesce(cache_write_usd, 0)) FILTER (WHERE gap_min > 5) AS cache_write_usd_after_gap_gt_5min,
       100.0 * sum(coalesce(cache_write_usd, 0)) FILTER (WHERE gap_min > 5)
             / nullif(sum(coalesce(cache_write_usd, 0)), 0) AS pct_of_month_cache_write_usd
FROM t02
WHERE month IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- @headline
SELECT sum(coalesce(cache_write_usd, 0)) FILTER (WHERE gap_min > 5) AS usd_recached_after_gap_gt_5min,
       100.0 * sum(coalesce(cache_write_usd, 0)) FILTER (WHERE gap_min > 5)
             / (SELECT sum(coalesce(cache_write_usd, 0)) FROM calls_priced) AS pct_of_all_cache_write_usd,
       100.0 * sum(coalesce(cache_write_usd, 0)) FILTER (WHERE gap_min > 5)
             / (SELECT sum(coalesce(cost_usd, 0)) FROM calls_priced) AS pct_of_total_usd,
       100.0 * count(*) FILTER (WHERE cache_break AND gap_min < 1) / nullif(count(*) FILTER (WHERE gap_min < 1), 0) AS break_rate_pct_gap_lt_1min,
       100.0 * count(*) FILTER (WHERE cache_break AND gap_min > 60) / nullif(count(*) FILTER (WHERE gap_min > 60), 0) AS break_rate_pct_gap_gt_60min,
       sum(coalesce(cache_create_tokens, 0)) FILTER (WHERE gap_min > 5) AS recached_tokens_after_gap_gt_5min
FROM t02;
