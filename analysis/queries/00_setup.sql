-- # setup: views, prices, calls_priced and the shared helper tables
-- Everything here is rebuilt on every run (a few seconds on the 248 MB ledger),
-- so a change in prices.csv always propagates.
--
-- Helper tables created here and used by the T/C files:
--   calls_priced  one row per API response, with the four USD components
--   session_price the modal model of a session and its prices
--   sessions_x    sessions + cost, mode, committed_lines, user hash, counters
--   calls_idx     non-sidechain calls with a dense per-session index and cum cost
--   seq_pos       for every (session_id, seq) in the ledger: how many calls and
--                 tool calls precede it, and the cumulative USD up to it
--   turns         one row per human turn (user prompt + the calls that answered it)

CREATE OR REPLACE VIEW calls      AS SELECT * FROM read_parquet('{LEDGER}/calls/*.parquet');
CREATE OR REPLACE VIEW tool_calls AS SELECT * FROM read_parquet('{LEDGER}/tool_calls/*.parquet');
CREATE OR REPLACE VIEW user_turns AS SELECT * FROM read_parquet('{LEDGER}/user_turns/*.parquet');
CREATE OR REPLACE VIEW events     AS SELECT * FROM read_parquet('{LEDGER}/events/*.parquet');
CREATE OR REPLACE VIEW sessions   AS SELECT * FROM read_parquet('{LEDGER}/sessions/*.parquet');

CREATE OR REPLACE TABLE prices AS
SELECT * FROM read_csv('{PRICES}', header = true, auto_detect = true);

-- model string normalisation: drop an "openrouter style" provider prefix and,
-- for anthropic model names only, turn "claude-opus-4.6" into "claude-opus-4-6".
CREATE OR REPLACE MACRO norm_model(m) AS
  CASE
    WHEN m IS NULL THEN NULL
    WHEN lower(regexp_replace(m, '^.*/', '')) LIKE 'claude%'
      THEN replace(lower(regexp_replace(m, '^.*/', '')), '.', '-')
    ELSE lower(regexp_replace(m, '^.*/', ''))
  END;

-- one price row per distinct raw model string; the longest matching LIKE pattern
-- wins (so gpt-5.4-mini% beats gpt-5.4%).
CREATE OR REPLACE TABLE model_prices AS
WITH m AS (
  SELECT DISTINCT model, norm_model(model) AS model_norm
  FROM calls WHERE model IS NOT NULL
), j AS (
  SELECT m.model, m.model_norm, p.provider, p.p_input, p.p_cache_read,
         p.p_cache_write_5m, p.p_cache_write_1h, p.p_output,
         row_number() OVER (PARTITION BY m.model
                            ORDER BY length(p.model_pattern) DESC, p.model_pattern) AS rn
  FROM m JOIN prices p ON m.model_norm LIKE p.model_pattern
)
SELECT model, model_norm, provider, p_input, p_cache_read,
       p_cache_write_5m, p_cache_write_1h, p_output
FROM j WHERE rn = 1;

-- ---------------------------------------------------------------- calls_priced
CREATE OR REPLACE TABLE calls_priced AS
WITH c AS (
  SELECT c.*, mp.provider, mp.p_input, mp.p_cache_read, mp.p_cache_write_5m,
         mp.p_cache_write_1h, mp.p_output, mp.model_norm
  FROM calls c LEFT JOIN model_prices mp ON c.model = mp.model
), t AS (
  SELECT c.*,
    coalesce(c.is_sidechain, false) AS sidechain,
    CASE WHEN c.cache_create_5m IS NULL AND c.cache_create_1h IS NULL
         THEN coalesce(c.cache_create_tokens, 0)
         ELSE coalesce(c.cache_create_5m, 0) END AS c5m_tokens,
    coalesce(c.cache_create_1h, 0) AS c1h_tokens
  FROM c
)
SELECT
  session_id, agent, repo, seq, ts, msg_id, request_id, parent_id,
  sidechain AS is_sidechain,
  model, model_norm, harness_version, stop_reason, speed, service_tier,
  input_tokens, cache_read_tokens, cache_create_tokens, cache_create_5m, cache_create_1h,
  output_tokens, reasoning_tokens, context_window,
  n_text_chars, n_thinking_chars, n_thinking_blocks, n_tool_uses, text_head,
  cwd, git_branch, timezone,
  provider,
  provider IS NOT NULL AS is_priced,
  date_trunc('month', ts) AS month,
  c5m_tokens, c1h_tokens,
  CASE WHEN provider = 'openai' THEN coalesce(input_tokens, 0)
       ELSE coalesce(input_tokens, 0) + coalesce(cache_read_tokens, 0)
            + coalesce(cache_create_tokens, 0) END AS ctx_tokens,
  -- OpenAI input_tokens INCLUDES the cached prefix, anthropic input_tokens does not
  CASE WHEN provider = 'openai'
         THEN greatest(coalesce(input_tokens, 0) - coalesce(cache_read_tokens, 0), 0) * p_input / 1e6
       WHEN provider IS NOT NULL
         THEN coalesce(input_tokens, 0) * p_input / 1e6 END AS input_usd,
  coalesce(cache_read_tokens, 0) * p_cache_read / 1e6 AS cache_read_usd,
  CASE WHEN provider = 'anthropic'
         THEN c5m_tokens * p_cache_write_5m / 1e6 + c1h_tokens * p_cache_write_1h / 1e6
       WHEN provider IS NOT NULL THEN 0.0 END AS cache_write_usd,
  coalesce(output_tokens, 0) * p_output / 1e6 AS output_usd,
  CASE WHEN provider IS NULL THEN NULL ELSE
    (CASE WHEN provider = 'openai'
            THEN greatest(coalesce(input_tokens, 0) - coalesce(cache_read_tokens, 0), 0) * p_input / 1e6
          ELSE coalesce(input_tokens, 0) * p_input / 1e6 END)
    + coalesce(cache_read_tokens, 0) * p_cache_read / 1e6
    + (CASE WHEN provider = 'anthropic'
              THEN c5m_tokens * p_cache_write_5m / 1e6 + c1h_tokens * p_cache_write_1h / 1e6
            ELSE 0.0 END)
    + coalesce(output_tokens, 0) * p_output / 1e6 END AS cost_usd,
  p_input, p_cache_read, p_cache_write_5m, p_cache_write_1h, p_output
FROM t;

-- ---------------------------------------------------------------- session_price
CREATE OR REPLACE TABLE session_price AS
WITH m AS (
  SELECT session_id, model, count(*) AS n FROM calls_priced
  WHERE model IS NOT NULL GROUP BY 1, 2
), r AS (
  SELECT *, row_number() OVER (PARTITION BY session_id ORDER BY n DESC, model) AS rn FROM m
)
SELECT r.session_id, r.model AS session_model, mp.provider AS session_provider,
       mp.p_input, mp.p_cache_read, mp.p_cache_write_5m, mp.p_output
FROM r LEFT JOIN model_prices mp ON r.model = mp.model
WHERE r.rn = 1;

-- ---------------------------------------------------------------- calls_idx
CREATE OR REPLACE TABLE calls_idx AS
SELECT session_id, seq, ts, agent, model, cost_usd, ctx_tokens, output_tokens,
       cache_read_tokens, output_usd,
       row_number() OVER (PARTITION BY session_id ORDER BY seq) AS call_idx,
       sum(coalesce(cost_usd, 0)) OVER (PARTITION BY session_id ORDER BY seq
                                        ROWS UNBOUNDED PRECEDING) AS cum_cost_usd
FROM calls_priced
WHERE NOT is_sidechain;

-- ---------------------------------------------------------------- seq_pos
CREATE OR REPLACE TABLE seq_pos AS
WITH pts AS (
  SELECT DISTINCT session_id, seq FROM (
    SELECT session_id, seq FROM tool_calls
    UNION ALL SELECT session_id, seq FROM user_turns
    UNION ALL SELECT session_id, seq FROM events
    UNION ALL SELECT session_id, seq FROM calls
  )
), cagg AS (
  SELECT session_id, seq, max(call_idx) AS call_idx, max(cum_cost_usd) AS cum_cost_usd
  FROM calls_idx GROUP BY 1, 2
), tnum AS (
  SELECT session_id, seq,
         row_number() OVER (PARTITION BY session_id ORDER BY seq) AS tool_idx
  FROM tool_calls
), tagg AS (
  SELECT session_id, seq, max(tool_idx) AS tool_idx FROM tnum GROUP BY 1, 2
), a AS (
  SELECT p.session_id, p.seq,
         coalesce(c.call_idx, 0) AS calls_before,
         coalesce(c.cum_cost_usd, 0.0) AS cum_cost_usd
  FROM pts p ASOF LEFT JOIN cagg c
    ON p.session_id = c.session_id AND p.seq >= c.seq
)
SELECT a.session_id, a.seq, a.calls_before, a.cum_cost_usd,
       coalesce(t.tool_idx, 0) AS tools_before
FROM a ASOF LEFT JOIN tagg t
  ON a.session_id = t.session_id AND a.seq >= t.seq;

-- ---------------------------------------------------------------- sessions_x
CREATE OR REPLACE TABLE sessions_x AS
WITH agg AS (
  SELECT session_id, any_value(agent) AS calls_agent,
         count(*) AS n_calls,
         count(*) FILTER (WHERE is_sidechain) AS n_sidechain_calls,
         count(*) FILTER (WHERE NOT is_priced) AS n_unpriced_calls,
         sum(coalesce(cost_usd, 0)) AS session_cost_usd,
         sum(coalesce(output_usd, 0)) AS session_output_usd,
         sum(coalesce(input_tokens, 0)) AS input_tokens,
         sum(coalesce(cache_read_tokens, 0)) AS cache_read_tokens,
         sum(c5m_tokens + c1h_tokens) AS cache_write_tokens,
         sum(coalesce(output_tokens, 0)) AS output_tokens,
         sum(ctx_tokens) AS ctx_tokens,
         min(ts) AS first_ts, max(ts) AS last_ts,
         count(*) FILTER (WHERE speed = 'fast') AS n_fast_calls
  FROM calls_priced GROUP BY 1
), hv AS (
  SELECT session_id, harness_version FROM (
    SELECT session_id, harness_version, count(*) AS n,
           row_number() OVER (PARTITION BY session_id ORDER BY count(*) DESC, harness_version) AS rn
    FROM calls_priced WHERE harness_version IS NOT NULL GROUP BY 1, 2
  ) WHERE rn = 1
), cw AS (
  SELECT session_id, cwd FROM (
    SELECT session_id, cwd, count(*) AS n,
           row_number() OVER (PARTITION BY session_id ORDER BY count(*) DESC, cwd) AS rn
    FROM calls_priced WHERE cwd IS NOT NULL GROUP BY 1, 2
  ) WHERE rn = 1
), tc AS (
  SELECT session_id, count(*) AS n_tool_calls,
         count(*) FILTER (WHERE is_error) AS n_tool_errors,
         sum(coalesce(result_chars, 0)) AS tool_result_chars
  FROM tool_calls GROUP BY 1
), ut AS (
  SELECT session_id,
         count(*) FILTER (WHERE NOT coalesce(is_meta, false) AND human_chars > 0) AS n_human_turns,
         sum(coalesce(human_chars, 0)) AS human_chars,
         count(*) FILTER (WHERE is_interrupt) AS n_interrupts
  FROM user_turns GROUP BY 1
)
SELECT s.session_id, coalesce(s.agent, agg.calls_agent) AS agent, s.repo, s.created_at,
       s.bytes, s.models, s.detected_format,
       s.attr_agent_percentage,
       s.attr_total_committed AS committed_lines,
       CASE WHEN s.attr_agent_percentage IS NULL THEN 'unknown'
            WHEN s.attr_agent_percentage >= 95 THEN 'vibe'
            WHEN s.attr_agent_percentage <= 5 THEN 'human'
            ELSE 'collab' END AS mode,
       hv.harness_version,
       cw.cwd,
       md5(coalesce(regexp_extract(cw.cwd, '^/(Users|home)/([^/]+)', 2), 'unknown'))[1:10] AS user_hash,
       sp.session_model, sp.session_provider, sp.p_input, sp.p_cache_read, sp.p_cache_write_5m, sp.p_output,
       coalesce(agg.n_calls, 0) AS n_calls,
       coalesce(agg.n_sidechain_calls, 0) AS n_sidechain_calls,
       coalesce(agg.n_unpriced_calls, 0) AS n_unpriced_calls,
       coalesce(agg.n_fast_calls, 0) AS n_fast_calls,
       agg.session_cost_usd, agg.session_output_usd,
       agg.input_tokens, agg.cache_read_tokens, agg.cache_write_tokens,
       agg.output_tokens, agg.ctx_tokens,
       agg.first_ts, agg.last_ts,
       coalesce(tc.n_tool_calls, 0) AS n_tool_calls,
       coalesce(tc.n_tool_errors, 0) AS n_tool_errors,
       coalesce(tc.tool_result_chars, 0) AS tool_result_chars,
       coalesce(ut.n_human_turns, 0) AS n_human_turns,
       coalesce(ut.human_chars, 0) AS human_chars,
       coalesce(ut.n_interrupts, 0) AS n_interrupts
FROM sessions s
LEFT JOIN agg USING (session_id)
LEFT JOIN hv USING (session_id)
LEFT JOIN cw USING (session_id)
LEFT JOIN tc USING (session_id)
LEFT JOIN ut USING (session_id)
LEFT JOIN session_price sp USING (session_id);

-- ---------------------------------------------------------------- turns
-- A turn = one non-meta human prompt plus every non-sidechain call that follows
-- it before the next human prompt. turn_idx 0 holds calls before the first prompt.
--
-- last_call_ts_adj / last_call_seq_adj: codex flushes the token_count record of a
-- finished response at the moment the NEXT request starts, so the last call of a
-- codex turn carries a ts a few hundred ms AFTER the next human prompt (8966 of
-- 13441 codex turns). The adjusted columns ignore calls stamped after the next
-- prompt, which makes agent_time and reply timing comparable across harnesses.
CREATE OR REPLACE TABLE turns AS
WITH ev AS (
  SELECT session_id, agent, seq, ts, 1 AS is_user,
         human_chars, coalesce(is_interrupt, false) AS is_interrupt,
         0.0 AS cost_usd, 0.0 AS output_usd
  FROM user_turns
  WHERE NOT coalesce(is_meta, false) AND human_chars > 0
  UNION ALL
  SELECT session_id, agent, seq, ts, 0 AS is_user,
         NULL AS human_chars, false AS is_interrupt,
         coalesce(cost_usd, 0) AS cost_usd, coalesce(output_usd, 0) AS output_usd
  FROM calls_priced WHERE NOT is_sidechain
), idx AS (
  SELECT *, sum(is_user) OVER (PARTITION BY session_id ORDER BY seq, is_user DESC
                               ROWS UNBOUNDED PRECEDING) AS turn_idx
  FROM ev
), agg AS (
  SELECT session_id, turn_idx, any_value(agent) AS agent,
         max(seq) FILTER (WHERE is_user = 1) AS user_seq,
         max(ts) FILTER (WHERE is_user = 1) AS user_ts,
         max(human_chars) FILTER (WHERE is_user = 1) AS human_chars,
         bool_or(is_interrupt) FILTER (WHERE is_user = 1) AS is_interrupt,
         count(*) FILTER (WHERE is_user = 0) AS n_calls,
         min(ts) FILTER (WHERE is_user = 0) AS first_call_ts,
         max(ts) FILTER (WHERE is_user = 0) AS last_call_ts,
         max(seq) FILTER (WHERE is_user = 0) AS last_call_seq,
         sum(cost_usd) AS turn_cost_usd,
         sum(output_usd) AS turn_output_usd
  FROM idx GROUP BY session_id, turn_idx
), agg2 AS (
  SELECT *,
         lead(user_ts) OVER w AS next_user_ts,
         lead(user_seq) OVER w AS next_user_seq,
         lead(is_interrupt) OVER w AS next_is_interrupt,
         lead(human_chars) OVER w AS next_human_chars
  FROM agg
  WINDOW w AS (PARTITION BY session_id ORDER BY turn_idx)
), adj AS (
  SELECT i.session_id, i.turn_idx,
         max(i.seq) FILTER (WHERE i.is_user = 0
              AND (a.next_user_ts IS NULL OR i.ts <= a.next_user_ts)) AS last_call_seq_adj,
         arg_max(i.ts, i.seq) FILTER (WHERE i.is_user = 0
              AND (a.next_user_ts IS NULL OR i.ts <= a.next_user_ts)) AS last_call_ts_adj,
         count(*) FILTER (WHERE i.is_user = 0
              AND (a.next_user_ts IS NULL OR i.ts <= a.next_user_ts)) AS n_calls_adj
  FROM idx i JOIN agg2 a USING (session_id, turn_idx)
  GROUP BY 1, 2
)
SELECT a.*, d.last_call_seq_adj, d.last_call_ts_adj, d.n_calls_adj,
       lag(d.last_call_ts_adj) OVER w AS prev_last_call_ts_adj,
       lag(a.last_call_ts) OVER w AS prev_last_call_ts
FROM agg2 a JOIN adj d USING (session_id, turn_idx)
WINDOW w AS (PARTITION BY a.session_id ORDER BY a.turn_idx);
