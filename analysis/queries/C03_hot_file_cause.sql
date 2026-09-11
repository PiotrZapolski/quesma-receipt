-- # C03 case file: why the hot files are hot
-- The 40 hottest files (most distinct sessions), 5 random edit events each.

SELECT setseed(0.44);

CREATE OR REPLACE TEMP TABLE c03_edits AS
SELECT tc.session_id, tc.agent, s.mode, s.repo, s.user_hash, tc.seq, tc.tool_kind, tc.file_path
FROM tool_calls tc
JOIN sessions_x s ON s.session_id = tc.session_id
WHERE tc.tool_kind IN ('edit', 'write') AND tc.file_path IS NOT NULL;

CREATE OR REPLACE TEMP TABLE c03_hot AS
SELECT repo, file_path,
       count(*) AS edits,
       count(DISTINCT session_id) AS sessions,
       count(DISTINCT user_hash) AS users
FROM c03_edits
GROUP BY 1, 2
ORDER BY sessions DESC, edits DESC
LIMIT 40;

-- @out hot_file_cause
WITH picked AS (
  SELECT e.*, h.sessions AS file_sessions, h.edits AS file_edits, h.users AS file_users,
         row_number() OVER (PARTITION BY e.repo, e.file_path ORDER BY random()) AS rn
  FROM c03_edits e
  JOIN c03_hot h ON h.repo IS NOT DISTINCT FROM e.repo AND h.file_path = e.file_path
)
SELECT session_id, seq, 10 AS k_before, 10 AS k_after,
       agent, mode, repo, file_path, tool_kind,
       file_sessions, file_edits, file_users,
       repo || '|' || file_path AS stratum
FROM picked
WHERE rn <= 5
ORDER BY file_sessions DESC, file_path, seq;

-- @headline
SELECT count(*) AS hot_files_selected,
       sum(sessions) AS sessions_covered,
       sum(edits) AS edits_covered,
       max(sessions) AS max_sessions_on_one_file,
       min(sessions) AS min_sessions_on_one_file
FROM c03_hot;
