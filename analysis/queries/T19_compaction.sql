-- # T19 compaction: what gets read again after the context is dropped
-- claude_code system/compact_boundary and microcompact_boundary events, plus the
-- codex `compacted` events for comparison. For each boundary, the reads in the
-- next 20 tool calls that touch a path already read before the boundary are
-- re-reads the compaction paid for.

CREATE OR REPLACE TEMP TABLE t19_b AS
SELECT e.session_id, e.agent, e.seq, e.subtype, e.value,
       p.tools_before, p.calls_before
FROM events e
JOIN seq_pos p ON p.session_id = e.session_id AND p.seq = e.seq
WHERE (e.event_type = 'system' AND e.subtype IN ('compact_boundary', 'microcompact_boundary'))
   OR e.event_type = 'compacted';

CREATE OR REPLACE TEMP TABLE t19_reads AS
SELECT tc.session_id, tc.seq, tc.file_path, coalesce(tc.result_chars, 0) AS result_chars,
       p.tools_before, s.p_cache_read, s.p_cache_write_5m,
       min(tc.seq) OVER (PARTITION BY tc.session_id, tc.file_path) AS first_read_seq
FROM tool_calls tc
JOIN seq_pos p ON p.session_id = tc.session_id AND p.seq = tc.seq
JOIN sessions_x s ON s.session_id = tc.session_id
WHERE tc.tool_kind = 'read' AND tc.file_path IS NOT NULL;
-- note: t19_reads also carries p_cache_write_5m through sessions_x

CREATE OR REPLACE TEMP TABLE t19 AS
SELECT b.session_id, b.agent, b.seq AS boundary_seq, b.subtype, b.value,
       r.seq AS read_seq, r.file_path, r.result_chars,
       r.first_read_seq < b.seq AS was_read_before_boundary,
       r.result_chars / 4.0 * r.p_cache_read / 1e6 AS reread_usd_one_pass,
       r.result_chars / 4.0 * coalesce(r.p_cache_write_5m, r.p_cache_read) / 1e6 AS reread_usd_recached
FROM t19_b b
JOIN t19_reads r
  ON r.session_id = b.session_id
 AND r.tools_before > b.tools_before
 AND r.tools_before <= b.tools_before + 20;

-- @out boundaries_by_subtype
SELECT agent, event_kind, count(*) AS boundaries, count(DISTINCT session_id) AS sessions
FROM (SELECT agent, session_id, coalesce(subtype, 'compacted') AS event_kind FROM t19_b)
GROUP BY 1, 2
ORDER BY boundaries DESC;

-- @out sessions_with_compaction
SELECT s.agent,
       count(*) AS sessions,
       count(*) FILTER (WHERE b.boundaries > 0) AS sessions_with_a_boundary,
       100.0 * count(*) FILTER (WHERE b.boundaries > 0) / count(*) AS pct_sessions_compacted,
       median(b.boundaries) FILTER (WHERE b.boundaries > 0) AS median_boundaries_when_present,
       max(b.boundaries) AS max_boundaries,
       sum(s.session_cost_usd) FILTER (WHERE b.boundaries > 0) AS usd_in_compacted_sessions
FROM sessions_x s
LEFT JOIN (SELECT session_id, count(*) AS boundaries FROM t19_b GROUP BY 1) b USING (session_id)
WHERE s.n_calls > 0
GROUP BY 1
ORDER BY sessions DESC;

-- @out rereads_after_boundary
SELECT agent, coalesce(subtype, 'compacted') AS event_kind,
       count(*) AS reads_in_next_20_tool_calls,
       count(*) FILTER (WHERE was_read_before_boundary) AS reads_of_already_seen_paths,
       100.0 * count(*) FILTER (WHERE was_read_before_boundary) / count(*) AS pct_rereads,
       sum(result_chars) FILTER (WHERE was_read_before_boundary) AS reread_chars,
       sum(reread_usd_one_pass) FILTER (WHERE was_read_before_boundary) AS reread_usd_one_pass,
       sum(reread_usd_recached) FILTER (WHERE was_read_before_boundary) AS reread_usd_recached
FROM t19
GROUP BY 1, 2
ORDER BY reads_in_next_20_tool_calls DESC;

-- @out top_reread_files
SELECT substr(file_path, 1, 80) AS file_path_80,
       count(*) AS rereads_after_a_boundary,
       count(DISTINCT session_id) AS sessions,
       sum(result_chars) AS chars
FROM t19
WHERE was_read_before_boundary
GROUP BY 1
ORDER BY rereads_after_a_boundary DESC
LIMIT 20;

-- @headline
SELECT (SELECT count(*) FROM t19_b) AS compaction_boundaries,
       (SELECT count(DISTINCT session_id) FROM t19_b) AS sessions_with_a_boundary,
       count(*) AS reads_in_the_20_tool_calls_after_a_boundary,
       100.0 * count(*) FILTER (WHERE was_read_before_boundary) / nullif(count(*), 0) AS pct_of_those_reads_already_seen,
       sum(result_chars) FILTER (WHERE was_read_before_boundary) AS reread_chars,
       sum(reread_usd_one_pass) FILTER (WHERE was_read_before_boundary) AS usd_of_the_rereads_first_pass_only,
       sum(reread_usd_recached) FILTER (WHERE was_read_before_boundary) AS usd_of_the_rereads_at_cache_write_price
FROM t19;
