-- # T20 self reread: reading back what the agent just wrote, and edit thrash
-- Reads of a path within 5 calls of a write or edit of the same path, and files
-- edited 3+ times inside a 10 call window.

CREATE OR REPLACE TEMP TABLE t20 AS
SELECT tc.session_id, tc.agent, tc.seq, tc.tool_kind, tc.file_path,
       coalesce(tc.result_chars, 0) AS result_chars,
       p.calls_before, s.p_cache_read, s.p_input,
       max(CASE WHEN tc.tool_kind IN ('write', 'edit') THEN p.calls_before END)
         OVER (PARTITION BY tc.session_id, tc.file_path ORDER BY tc.seq, tc.tool_use_id
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS last_mod_call_idx
FROM tool_calls tc
JOIN seq_pos p ON p.session_id = tc.session_id AND p.seq = tc.seq
JOIN sessions_x s ON s.session_id = tc.session_id
WHERE tc.file_path IS NOT NULL AND tc.tool_kind IN ('read', 'write', 'edit');

CREATE OR REPLACE TEMP TABLE t20_thrash AS
SELECT *, count(*) OVER (PARTITION BY session_id, file_path ORDER BY calls_before
                         RANGE BETWEEN 10 PRECEDING AND CURRENT ROW) AS edits_in_last_10_calls
FROM t20
WHERE tool_kind IN ('write', 'edit');

-- @out self_rereads
SELECT agent,
       count(*) AS reads,
       count(*) FILTER (WHERE calls_before - last_mod_call_idx BETWEEN 0 AND 5) AS reads_within_5_calls_of_a_write,
       100.0 * count(*) FILTER (WHERE calls_before - last_mod_call_idx BETWEEN 0 AND 5) / count(*) AS pct_of_reads,
       sum(result_chars) FILTER (WHERE calls_before - last_mod_call_idx BETWEEN 0 AND 5) AS reread_chars,
       sum(result_chars / 4.0 * p_input / 1e6) FILTER (WHERE calls_before - last_mod_call_idx BETWEEN 0 AND 5) AS usd_fresh_input_price
FROM t20
WHERE tool_kind = 'read'
GROUP BY 1
ORDER BY reread_chars DESC NULLS LAST;

-- @out edit_thrash
SELECT agent,
       count(*) AS edits,
       count(*) FILTER (WHERE edits_in_last_10_calls >= 3) AS edits_in_a_thrash_window,
       100.0 * count(*) FILTER (WHERE edits_in_last_10_calls >= 3) / count(*) AS pct_of_edits,
       count(DISTINCT CASE WHEN edits_in_last_10_calls >= 3 THEN session_id || '|' || file_path END) AS distinct_thrashed_files
FROM t20_thrash
GROUP BY 1
ORDER BY edits DESC;

-- @out top_thrashed_files
SELECT substr(file_path, 1, 80) AS file_path_80, any_value(agent) AS agent,
       count(*) AS edits_in_thrash_windows,
       count(DISTINCT session_id) AS sessions,
       max(edits_in_last_10_calls) AS worst_burst
FROM t20_thrash
WHERE edits_in_last_10_calls >= 3
GROUP BY 1
ORDER BY edits_in_thrash_windows DESC
LIMIT 20;

-- @headline
SELECT (SELECT count(*) FROM t20 WHERE tool_kind = 'read'
          AND calls_before - last_mod_call_idx BETWEEN 0 AND 5) AS reads_of_a_just_written_file,
       (SELECT 100.0 * count(*) FILTER (WHERE calls_before - last_mod_call_idx BETWEEN 0 AND 5) / count(*)
        FROM t20 WHERE tool_kind = 'read') AS pct_of_all_reads,
       (SELECT sum(result_chars) FROM t20 WHERE tool_kind = 'read'
          AND calls_before - last_mod_call_idx BETWEEN 0 AND 5) AS reread_chars,
       (SELECT sum(result_chars / 4.0 * p_input / 1e6) FROM t20 WHERE tool_kind = 'read'
          AND calls_before - last_mod_call_idx BETWEEN 0 AND 5) AS usd_at_fresh_input_price,
       (SELECT count(*) FROM t20_thrash WHERE edits_in_last_10_calls >= 3) AS edits_inside_a_thrash_window,
       (SELECT 100.0 * count(*) FILTER (WHERE edits_in_last_10_calls >= 3) / count(*) FROM t20_thrash) AS pct_of_edits_in_thrash;
