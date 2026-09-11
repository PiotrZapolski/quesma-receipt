-- # T12 human wait: the token bill is not the expensive part
-- Per turn: agent_time = last call ts - prompt ts, human_time = prompt ts - the
-- previous turn's last call ts (capped at 30 min, anything longer is a break and
-- is not counted as waiting). Human time is valued at 60 USD/h.
-- Uses the adjusted last-call timestamps (see 00_setup) so codex is comparable.

CREATE OR REPLACE TEMP TABLE t12 AS
SELECT t.session_id, t.agent, t.turn_idx, t.n_calls, t.turn_cost_usd,
       date_diff('millisecond', t.user_ts, t.last_call_ts_adj) / 1000.0 AS agent_time_s,
       CASE WHEN date_diff('millisecond', t.prev_last_call_ts_adj, t.user_ts) / 1000.0 BETWEEN 0 AND 1800
            THEN date_diff('millisecond', t.prev_last_call_ts_adj, t.user_ts) / 1000.0 END AS human_time_s,
       s.mode, s.committed_lines
FROM turns t
JOIN sessions_x s USING (session_id)
WHERE t.user_ts IS NOT NULL AND t.last_call_ts_adj IS NOT NULL
  AND date_diff('millisecond', t.user_ts, t.last_call_ts_adj) >= 0;

-- @out by_agent
SELECT agent,
       count(*) AS turns,
       sum(agent_time_s) / 3600.0 AS agent_hours,
       median(agent_time_s) AS median_agent_time_s,
       quantile_cont(agent_time_s, 0.9) AS p90_agent_time_s,
       sum(human_time_s) / 3600.0 AS human_wait_hours,
       median(human_time_s) AS median_human_time_s,
       sum(turn_cost_usd) AS usd,
       sum(turn_cost_usd) / nullif(sum(agent_time_s) / 3600.0, 0) AS usd_per_agent_hour
FROM t12
GROUP BY 1
ORDER BY turns DESC;

-- @out by_mode
SELECT mode,
       count(*) AS turns,
       sum(agent_time_s) / 3600.0 AS agent_hours,
       sum(human_time_s) / 3600.0 AS human_wait_hours,
       sum(turn_cost_usd) AS token_usd,
       60.0 * sum(agent_time_s) / 3600.0 AS human_usd_if_watching_at_60ph,
       60.0 * sum(agent_time_s) / 3600.0 / nullif(sum(turn_cost_usd), 0) AS ratio_wait_cost_to_token_cost,
       median(agent_time_s) AS median_agent_time_s
FROM t12
GROUP BY 1
ORDER BY agent_hours DESC;

-- @out per_session
WITH s AS (
  SELECT session_id, any_value(agent) AS agent, any_value(mode) AS mode,
         count(*) AS turns,
         sum(agent_time_s) / 3600.0 AS agent_hours,
         sum(human_time_s) / 3600.0 AS human_hours,
         sum(turn_cost_usd) AS usd
  FROM t12 GROUP BY 1
)
SELECT agent,
       count(*) AS sessions,
       median(agent_hours) AS median_agent_hours_per_session,
       quantile_cont(agent_hours, 0.9) AS p90_agent_hours_per_session,
       median(human_hours) AS median_human_hours_per_session,
       sum(agent_hours) AS agent_hours,
       sum(usd) AS usd
FROM s
GROUP BY 1
ORDER BY agent_hours DESC;

-- @out agent_time_buckets
SELECT CASE WHEN agent_time_s < 30 THEN '1. <30 s'
            WHEN agent_time_s < 120 THEN '2. 0.5-2 min'
            WHEN agent_time_s < 600 THEN '3. 2-10 min'
            WHEN agent_time_s < 1800 THEN '4. 10-30 min'
            ELSE '5. >30 min' END AS bucket,
       count(*) AS turns,
       100.0 * count(*) / sum(count(*)) OVER () AS pct_of_turns,
       sum(agent_time_s) / 3600.0 AS agent_hours,
       sum(turn_cost_usd) AS usd
FROM t12
GROUP BY 1
ORDER BY 1;

-- @headline
SELECT sum(agent_time_s) / 3600.0 AS total_agent_working_hours,
       sum(turn_cost_usd) AS total_token_usd_in_those_turns,
       60.0 * sum(agent_time_s) / 3600.0 AS human_usd_at_60_per_hour_if_watching,
       60.0 * sum(agent_time_s) / 3600.0 / nullif(sum(turn_cost_usd), 0) AS ratio_human_wait_cost_to_token_cost,
       sum(human_time_s) / 3600.0 AS total_human_typing_and_thinking_hours,
       median(agent_time_s) AS median_agent_seconds_per_turn,
       sum(turn_cost_usd) / nullif(sum(agent_time_s) / 3600.0, 0) AS usd_of_tokens_per_agent_hour
FROM t12;
