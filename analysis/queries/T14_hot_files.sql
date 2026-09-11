-- # T14 hot files: the files every session has to touch
-- Per repo, files that get edited or written. "Hot" = touched in >= 10 distinct
-- sessions. Two proxies for trouble: an error within the next 3 tool calls, and a
-- short human correction (< 200 chars) as the next prompt after the edit.

CREATE OR REPLACE TEMP TABLE t14_tc AS
SELECT tc.session_id, tc.seq, tc.tool_kind, tc.file_path,
       coalesce(tc.is_error, false) AS is_error,
       p.tools_before, p.calls_before
FROM tool_calls tc
JOIN seq_pos p ON p.session_id = tc.session_id AND p.seq = tc.seq;

-- is there an errored tool call within the next 3 tool calls of the session?
CREATE OR REPLACE TEMP TABLE t14_tc2 AS
SELECT *, coalesce(bool_or(is_error) OVER (PARTITION BY session_id ORDER BY tools_before
                                           RANGE BETWEEN 1 FOLLOWING AND 3 FOLLOWING), false)
            AS error_within_3_tool_calls
FROM t14_tc;

CREATE OR REPLACE TEMP TABLE t14_edits AS
WITH e AS (
  SELECT t.session_id, s.agent, s.repo, s.user_hash, t.seq, t.tool_kind, t.file_path,
         t.tools_before, t.calls_before, t.error_within_3_tool_calls, -t.seq AS nseq
  FROM t14_tc2 t
  JOIN sessions_x s ON s.session_id = t.session_id
  WHERE t.tool_kind IN ('edit', 'write') AND t.file_path IS NOT NULL
), nu AS (
  SELECT session_id, seq, -seq AS nseq, human_chars
  FROM user_turns
  WHERE NOT coalesce(is_meta, false) AND human_chars > 0
)
SELECT e.*, u.human_chars AS next_human_chars,
       coalesce(u.human_chars < 200, false) AS short_correction_next
FROM e ASOF LEFT JOIN nu u
  ON e.session_id = u.session_id AND e.nseq >= u.nseq;

CREATE OR REPLACE TEMP TABLE t14_files AS
SELECT repo, file_path,
       any_value(agent) AS agent,
       count(*) AS edits,
       count(DISTINCT session_id) AS sessions,
       count(DISTINCT user_hash) AS users,
       100.0 * count(*) FILTER (WHERE error_within_3_tool_calls) / count(*) AS pct_edits_followed_by_error,
       100.0 * count(*) FILTER (WHERE short_correction_next) / count(*) AS pct_edits_followed_by_short_correction
FROM t14_edits
GROUP BY 1, 2;

-- @out top30_hot_files
SELECT repo, substr(file_path, 1, 70) AS file_path_70, agent, sessions, users, edits,
       pct_edits_followed_by_error, pct_edits_followed_by_short_correction
FROM t14_files
WHERE repo IN (SELECT repo FROM t14_files GROUP BY 1 HAVING sum(sessions) >= 20)
ORDER BY sessions DESC, edits DESC
LIMIT 30;

-- @out concentration_by_repo
WITH r AS (
  SELECT repo, file_path, edits,
         percent_rank() OVER (PARTITION BY repo ORDER BY edits DESC) AS pr
  FROM t14_files
)
SELECT repo,
       count(*) AS files,
       sum(edits) AS edits,
       100.0 * sum(edits) FILTER (WHERE pr < 0.05) / sum(edits) AS pct_of_edits_in_top_5pct_of_files,
       100.0 * sum(edits) FILTER (WHERE pr < 0.20) / sum(edits) AS pct_of_edits_in_top_20pct_of_files
FROM r
GROUP BY 1
HAVING count(*) >= 50
ORDER BY edits DESC
LIMIT 30;

-- @out hot_vs_cold
SELECT CASE WHEN sessions >= 10 THEN 'hot (>=10 sessions)' ELSE 'cold (<10 sessions)' END AS heat,
       count(*) AS files,
       sum(edits) AS edits,
       100.0 * sum(edits) / sum(sum(edits)) OVER () AS pct_of_all_edits,
       avg(pct_edits_followed_by_error) AS avg_pct_edits_followed_by_error,
       avg(pct_edits_followed_by_short_correction) AS avg_pct_edits_followed_by_short_correction,
       median(edits) AS median_edits_per_file
FROM t14_files
GROUP BY 1
ORDER BY heat;

-- @out hot_vs_cold_weighted
SELECT CASE WHEN f.sessions >= 10 THEN 'hot (>=10 sessions)' ELSE 'cold (<10 sessions)' END AS heat,
       count(*) AS edits,
       100.0 * count(*) FILTER (WHERE e.error_within_3_tool_calls) / count(*) AS pct_edits_followed_by_error,
       100.0 * count(*) FILTER (WHERE e.short_correction_next) / count(*) AS pct_edits_followed_by_short_correction
FROM t14_edits e
JOIN t14_files f ON f.repo IS NOT DISTINCT FROM e.repo AND f.file_path = e.file_path
GROUP BY 1
ORDER BY heat;

-- @out edits_by_agent
SELECT agent,
       count(*) AS edits,
       100.0 * count(*) FILTER (WHERE error_within_3_tool_calls) / count(*) AS pct_edits_followed_by_error,
       100.0 * count(*) FILTER (WHERE short_correction_next) / count(*) AS pct_edits_followed_by_short_correction
FROM t14_edits
GROUP BY 1
ORDER BY edits DESC;

-- @headline
SELECT (SELECT count(*) FROM t14_files WHERE sessions >= 10) AS hot_files,
       (SELECT 100.0 * sum(edits) FILTER (WHERE sessions >= 10) / sum(edits) FROM t14_files) AS pct_of_edits_on_hot_files,
       (SELECT median(pct_of_edits_in_top_5pct) FROM (
          SELECT repo, 100.0 * sum(edits) FILTER (WHERE pr < 0.05) / sum(edits) AS pct_of_edits_in_top_5pct
          FROM (SELECT repo, edits, percent_rank() OVER (PARTITION BY repo ORDER BY edits DESC) AS pr
                FROM t14_files) GROUP BY 1 HAVING sum(edits) >= 100
        )) AS median_repo_share_of_edits_in_top_5pct_of_files,
       (SELECT 100.0 * count(*) FILTER (WHERE e.error_within_3_tool_calls) / count(*)
        FROM t14_edits e JOIN t14_files f ON f.repo IS NOT DISTINCT FROM e.repo AND f.file_path = e.file_path
        WHERE f.sessions >= 10) AS pct_hot_file_edits_followed_by_error,
       (SELECT 100.0 * count(*) FILTER (WHERE e.error_within_3_tool_calls) / count(*)
        FROM t14_edits e JOIN t14_files f ON f.repo IS NOT DISTINCT FROM e.repo AND f.file_path = e.file_path
        WHERE f.sessions < 10) AS pct_cold_file_edits_followed_by_error,
       (SELECT count(*) FROM t14_edits) AS edits_total;
