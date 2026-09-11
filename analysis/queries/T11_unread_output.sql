-- # T11 unread output: final replies nobody had time to read
-- The last call of a turn is the one that ends with assistant text and is followed
-- by the next human prompt. words = n_text_chars/5, reading speed 250 wpm, so
-- read_time_s = n_text_chars * 0.048. A reply is "unread" when the human answered
-- in less than half that time. Interrupt turns are excluded.
-- Uses last_call_seq_adj (see 00_setup): codex stamps the last token_count record
-- of a turn after the next prompt, so the raw last call ts is unusable there.

CREATE OR REPLACE TEMP TABLE t11 AS
SELECT t.session_id, t.agent, t.turn_idx, t.last_call_seq, t.last_call_ts, t.next_user_ts,
       t.last_call_ts_adj, c.n_text_chars, c.model, c.output_tokens, c.output_usd,
       c.n_text_chars / 5.0 AS words,
       c.n_text_chars / 5.0 / 250.0 * 60.0 AS read_time_s,
       date_diff('millisecond', t.last_call_ts_adj, t.next_user_ts) / 1000.0 AS delta_s,
       c.n_text_chars / 4.0 AS text_tokens,
       c.n_text_chars / 4.0 * s.p_output / 1e6 AS text_usd
FROM turns t
JOIN calls_priced c
  ON c.session_id = t.session_id AND c.seq = t.last_call_seq_adj AND NOT c.is_sidechain
JOIN sessions_x s ON s.session_id = t.session_id
WHERE t.last_call_seq_adj IS NOT NULL
  AND t.next_user_ts IS NOT NULL
  AND t.last_call_ts_adj IS NOT NULL
  AND NOT coalesce(t.next_is_interrupt, false)
  AND coalesce(c.n_text_chars, 0) > 0;

-- @out by_agent
SELECT agent,
       count(*) AS final_replies,
       count(*) FILTER (WHERE delta_s < 0.5 * read_time_s) AS unread_replies,
       100.0 * count(*) FILTER (WHERE delta_s < 0.5 * read_time_s) / count(*) AS pct_replies_unread,
       sum(text_tokens) AS final_text_tokens,
       sum(text_tokens) FILTER (WHERE delta_s < 0.5 * read_time_s) AS unread_text_tokens,
       100.0 * sum(text_tokens) FILTER (WHERE delta_s < 0.5 * read_time_s) / sum(text_tokens) AS pct_text_tokens_unread,
       sum(text_usd) FILTER (WHERE delta_s < 0.5 * read_time_s) AS unread_usd,
       median(read_time_s) AS median_read_time_s,
       median(delta_s) AS median_delta_s
FROM t11
GROUP BY 1
ORDER BY final_replies DESC;

-- @out delta_vs_read_time_distribution
SELECT CASE WHEN delta_s < 0.25 * read_time_s THEN '1. <25% of read time'
            WHEN delta_s < 0.5 * read_time_s THEN '2. 25-50%'
            WHEN delta_s < 1 * read_time_s THEN '3. 50-100%'
            WHEN delta_s < 5 * read_time_s THEN '4. 1-5x'
            ELSE '5. >5x (took their time)' END AS bucket,
       count(*) AS final_replies,
       100.0 * count(*) / sum(count(*)) OVER () AS pct_of_replies,
       sum(text_tokens) AS text_tokens,
       sum(text_usd) AS usd,
       median(n_text_chars) AS median_text_chars
FROM t11
GROUP BY 1
ORDER BY 1;

-- @out by_reply_length
SELECT CASE WHEN n_text_chars < 500 THEN '1. <500 chars'
            WHEN n_text_chars < 2000 THEN '2. 0.5-2k'
            WHEN n_text_chars < 6000 THEN '3. 2-6k'
            ELSE '4. >6k chars' END AS length_bucket,
       count(*) AS final_replies,
       100.0 * count(*) FILTER (WHERE delta_s < 0.5 * read_time_s) / count(*) AS pct_unread,
       sum(text_tokens) AS text_tokens,
       sum(text_usd) FILTER (WHERE delta_s < 0.5 * read_time_s) AS unread_usd
FROM t11
GROUP BY 1
ORDER BY 1;

-- @out longest_unread_replies
SELECT session_id, turn_idx, agent, n_text_chars, read_time_s, delta_s, text_usd
FROM t11
WHERE delta_s < 0.5 * read_time_s
ORDER BY n_text_chars DESC
LIMIT 20;

-- @out ordering_diagnostic
SELECT agent,
       count(*) AS turns_with_a_next_prompt,
       count(*) FILTER (WHERE last_call_seq_adj IS NULL) AS turns_dropped_no_call_before_next_prompt,
       count(*) FILTER (WHERE last_call_seq IS DISTINCT FROM last_call_seq_adj) AS turns_where_last_call_ts_was_after_next_prompt,
       median(date_diff('millisecond', last_call_ts, next_user_ts) / 1000.0) AS median_raw_delta_s,
       median(date_diff('millisecond', last_call_ts_adj, next_user_ts) / 1000.0) AS median_adjusted_delta_s
FROM turns
WHERE next_user_ts IS NOT NULL AND last_call_ts IS NOT NULL
GROUP BY 1
ORDER BY turns_with_a_next_prompt DESC;

-- @headline
SELECT sum(text_usd) FILTER (WHERE delta_s < 0.5 * read_time_s) AS usd_final_text_that_could_not_be_read,
       100.0 * sum(text_usd) FILTER (WHERE delta_s < 0.5 * read_time_s)
             / (SELECT sum(coalesce(output_usd, 0)) FROM calls_priced) AS pct_of_all_output_usd,
       100.0 * sum(text_tokens) FILTER (WHERE delta_s < 0.5 * read_time_s) / sum(text_tokens) AS pct_of_final_text_tokens_unread,
       count(*) FILTER (WHERE delta_s < 0.5 * read_time_s) AS unread_replies,
       count(*) AS final_replies_measured,
       median(delta_s) AS median_seconds_before_next_prompt,
       median(read_time_s) AS median_seconds_needed_to_read
FROM t11;
