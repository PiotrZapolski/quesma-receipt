-- # T24 harness whisper: how much of the prompt side the harness writes itself
-- attachment events (system reminders, hook output, diagnostics, skill listings)
-- carry payload_chars. Compared against what the human actually typed.

CREATE OR REPLACE TEMP TABLE t24 AS
SELECT e.session_id, s.agent, s.harness_version, s.mode,
       e.event_type, coalesce(e.subtype, e.event_type) AS subtype,
       coalesce(e.payload_chars, 0) AS payload_chars
FROM events e
JOIN sessions_x s ON s.session_id = e.session_id
WHERE e.payload_chars IS NOT NULL AND e.payload_chars > 0;

-- @out injected_by_subtype
SELECT agent, event_type, subtype,
       count(*) AS events,
       sum(payload_chars) AS payload_chars,
       sum(payload_chars) / 4.0 AS payload_tokens,
       median(payload_chars) AS median_payload_chars
FROM t24
GROUP BY 1, 2, 3
ORDER BY payload_chars DESC
LIMIT 30;

-- @out injected_vs_human_by_agent
WITH inj AS (
  SELECT agent, sum(payload_chars) AS injected_chars,
         sum(payload_chars) FILTER (WHERE event_type = 'attachment') AS attachment_chars
  FROM t24 GROUP BY 1
), hum AS (
  SELECT agent, sum(human_chars) AS human_chars
  FROM user_turns WHERE NOT coalesce(is_meta, false) GROUP BY 1
)
SELECT i.agent, i.injected_chars, i.attachment_chars, h.human_chars,
       100.0 * i.injected_chars / nullif(i.injected_chars + h.human_chars, 0) AS pct_injected_of_prompt_side,
       100.0 * i.attachment_chars / nullif(i.attachment_chars + h.human_chars, 0) AS pct_attachments_of_prompt_side
FROM inj i LEFT JOIN hum h USING (agent)
ORDER BY injected_chars DESC;

-- @out by_version_claude_code
WITH inj AS (
  SELECT harness_version, count(DISTINCT session_id) AS sessions,
         sum(payload_chars) FILTER (WHERE event_type = 'attachment') AS attachment_chars
  FROM t24 WHERE agent = 'claude_code' AND harness_version IS NOT NULL
  GROUP BY 1
), hum AS (
  SELECT s.harness_version, sum(u.human_chars) AS human_chars
  FROM user_turns u JOIN sessions_x s USING (session_id)
  WHERE s.agent = 'claude_code' AND NOT coalesce(u.is_meta, false)
  GROUP BY 1
)
SELECT i.harness_version,
       list_transform(string_split(regexp_replace(i.harness_version, '-.*$', ''), '.'),
                      x -> try_cast(x AS INTEGER)) AS vkey,
       i.sessions,
       i.attachment_chars / i.sessions AS attachment_chars_per_session,
       h.human_chars / i.sessions AS human_chars_per_session,
       100.0 * i.attachment_chars / nullif(i.attachment_chars + h.human_chars, 0) AS pct_injected
FROM inj i LEFT JOIN hum h USING (harness_version)
WHERE i.sessions >= 50
ORDER BY vkey;

-- @out per_session_distribution
WITH p AS (
  SELECT session_id, any_value(agent) AS agent,
         sum(payload_chars) FILTER (WHERE event_type = 'attachment') AS attachment_chars
  FROM t24 GROUP BY 1
)
SELECT agent, count(*) AS sessions,
       median(attachment_chars) AS median_attachment_chars_per_session,
       quantile_cont(attachment_chars, 0.9) AS p90_attachment_chars_per_session,
       max(attachment_chars) AS max_attachment_chars
FROM p
GROUP BY 1
ORDER BY sessions DESC;

-- @headline
WITH inj AS (SELECT sum(payload_chars) FILTER (WHERE event_type = 'attachment') AS attachment_chars,
                    sum(payload_chars) AS all_event_chars FROM t24),
     hum AS (SELECT sum(human_chars) AS human_chars FROM user_turns WHERE NOT coalesce(is_meta, false))
SELECT inj.attachment_chars AS harness_attachment_chars,
       hum.human_chars AS human_typed_chars,
       100.0 * inj.attachment_chars / nullif(inj.attachment_chars + hum.human_chars, 0) AS pct_of_prompt_side_written_by_the_harness,
       inj.attachment_chars / 4.0 AS harness_attachment_tokens,
       inj.all_event_chars AS all_event_payload_chars,
       (SELECT count(*) FROM t24 WHERE event_type = 'attachment') AS attachment_events
FROM inj, hum;
