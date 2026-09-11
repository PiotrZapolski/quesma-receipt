-- # T23 local hour: night coding (codex only, it is the only harness with a timezone)
-- DuckDB's ICU extension is not available offline, so the UTC offsets below are
-- fixed values valid for the data window (2026-03-26 to 2026-07-05, northern
-- summer time). Worst case a session lands one hour off.
-- CAVEAT: the codex parser never sets is_error (0 of 309060 codex tool calls), so
-- the tool error rate columns are structurally zero here. Abandonment and USD per
-- committed line are the usable signals.

CREATE OR REPLACE TEMP TABLE t23 AS
WITH f AS (
  SELECT session_id, agent, timezone, ts,
         row_number() OVER (PARTITION BY session_id ORDER BY seq) AS rn
  FROM calls_priced
  WHERE agent = 'codex' AND ts IS NOT NULL AND timezone IS NOT NULL
), o AS (
  SELECT f.session_id, f.timezone, f.ts,
         CASE f.timezone
           WHEN 'Europe/Berlin' THEN 120 WHEN 'Europe/Paris' THEN 120
           WHEN 'Europe/Madrid' THEN 120 WHEN 'Europe/Stockholm' THEN 120
           WHEN 'Europe/Amsterdam' THEN 120 WHEN 'Europe/Brussels' THEN 120
           WHEN 'Europe/Rome' THEN 120 WHEN 'Europe/Athens' THEN 180
           WHEN 'Europe/London' THEN 60 WHEN 'Etc/UTC' THEN 0
           WHEN 'America/Los_Angeles' THEN -420 WHEN 'America/Denver' THEN -360
           WHEN 'America/Chicago' THEN -300 WHEN 'America/New_York' THEN -240
           WHEN 'America/Toronto' THEN -240 WHEN 'America/Sao_Paulo' THEN -180
           WHEN 'Asia/Tokyo' THEN 540 WHEN 'Asia/Shanghai' THEN 480
           WHEN 'Asia/Kolkata' THEN 330 WHEN 'Asia/Karachi' THEN 300
           WHEN 'Africa/Nairobi' THEN 180 WHEN 'Australia/Melbourne' THEN 600
         END AS offset_min
  FROM f WHERE f.rn = 1
)
SELECT o.session_id, o.timezone, o.offset_min,
       extract('hour' FROM o.ts + (o.offset_min * INTERVAL 1 MINUTE)) AS local_hour,
       CASE WHEN extract('hour' FROM o.ts + (o.offset_min * INTERVAL 1 MINUTE)) < 6 THEN '1. night 0-6'
            WHEN extract('hour' FROM o.ts + (o.offset_min * INTERVAL 1 MINUTE)) < 18 THEN '2. day 6-18'
            ELSE '3. evening 18-24' END AS hour_bucket,
       s.session_cost_usd, s.committed_lines, s.n_tool_calls, s.n_tool_errors, s.mode, s.n_calls
FROM o JOIN sessions_x s ON s.session_id = o.session_id
WHERE o.offset_min IS NOT NULL;

-- @out sessions_per_local_hour
SELECT local_hour,
       count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       100.0 * sum(n_tool_errors) / nullif(sum(n_tool_calls), 0) AS tool_error_rate_pct,
       100.0 * count(*) FILTER (WHERE coalesce(committed_lines, 0) = 0) / count(*) AS abandonment_rate_pct,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line
FROM t23
GROUP BY 1
ORDER BY 1;

-- @out by_hour_bucket
SELECT hour_bucket,
       count(*) AS sessions,
       100.0 * count(*) / sum(count(*)) OVER () AS pct_of_sessions,
       sum(session_cost_usd) AS usd,
       100.0 * sum(n_tool_errors) / nullif(sum(n_tool_calls), 0) AS tool_error_rate_pct,
       100.0 * count(*) FILTER (WHERE coalesce(committed_lines, 0) = 0) / count(*) AS abandonment_rate_pct,
       sum(session_cost_usd) / nullif(sum(committed_lines), 0) AS usd_per_committed_line,
       median(session_cost_usd) AS median_session_usd
FROM t23
GROUP BY 1
ORDER BY 1;

-- @out by_timezone
SELECT timezone, offset_min, count(*) AS sessions,
       sum(session_cost_usd) AS usd,
       100.0 * count(*) FILTER (WHERE local_hour < 6) / count(*) AS pct_started_at_night
FROM t23
GROUP BY 1, 2
ORDER BY sessions DESC;

-- @headline
SELECT count(*) AS codex_sessions_with_a_timezone,
       100.0 * count(*) FILTER (WHERE hour_bucket = '1. night 0-6') / count(*) AS pct_of_sessions_started_at_night,
       100.0 * sum(session_cost_usd) FILTER (WHERE hour_bucket = '1. night 0-6') / sum(session_cost_usd) AS pct_of_codex_usd_spent_at_night,
       (SELECT 100.0 * count(*) FILTER (WHERE coalesce(committed_lines, 0) = 0) / count(*) FROM t23 WHERE hour_bucket = '1. night 0-6') AS abandonment_rate_pct_night,
       (SELECT 100.0 * count(*) FILTER (WHERE coalesce(committed_lines, 0) = 0) / count(*) FROM t23 WHERE hour_bucket = '2. day 6-18') AS abandonment_rate_pct_day,
       (SELECT sum(session_cost_usd) / nullif(sum(committed_lines), 0) FROM t23 WHERE hour_bucket = '1. night 0-6') AS usd_per_committed_line_night,
       (SELECT sum(session_cost_usd) / nullif(sum(committed_lines), 0) FROM t23 WHERE hour_bucket = '2. day 6-18') AS usd_per_committed_line_day,
       (SELECT median(session_cost_usd) FROM t23 WHERE hour_bucket = '1. night 0-6') AS median_session_usd_night
FROM t23;
