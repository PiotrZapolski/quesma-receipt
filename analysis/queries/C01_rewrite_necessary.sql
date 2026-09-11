-- # C01 case file: Write calls on files that were already in context
-- Layer 3 asks the judge whether the full rewrite was necessary.
-- 300 largest + 300 random, stratified by agent x mode. k_before/k_after are the
-- number of raw records to pull around `seq` when rendering the transcript.

SELECT setseed(0.42);

CREATE OR REPLACE TEMP TABLE c01_pool AS
WITH w AS (
  SELECT tc.session_id, tc.agent, tc.seq, tc.file_path, tc.content_chars, tc.input_chars,
         count(*) FILTER (WHERE tc.tool_kind IN ('read', 'edit', 'write'))
           OVER (PARTITION BY tc.session_id, tc.file_path ORDER BY tc.seq, tc.tool_use_id
                 ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS earlier_touches,
         max(CASE WHEN tc.tool_kind = 'read' THEN tc.result_chars END)
           OVER (PARTITION BY tc.session_id, tc.file_path ORDER BY tc.seq, tc.tool_use_id
                 ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS max_earlier_read_chars,
         tc.tool_kind
  FROM tool_calls tc
  WHERE tc.file_path IS NOT NULL AND tc.tool_kind IN ('read', 'edit', 'write')
)
SELECT w.session_id, w.agent, s.mode, s.repo, w.seq, w.file_path,
       w.content_chars, w.input_chars, w.max_earlier_read_chars,
       w.content_chars * 1.0 / nullif(w.max_earlier_read_chars, 0) AS rewrite_ratio,
       w.content_chars / 4.0 * s.p_output / 1e6 AS output_usd_estimate
FROM w JOIN sessions_x s USING (session_id)
WHERE w.tool_kind = 'write' AND w.earlier_touches > 0 AND coalesce(w.content_chars, 0) > 0;

-- @out rewrite_necessary
WITH top AS (
  SELECT *, 'top_by_size' AS stratum_pick
  FROM c01_pool ORDER BY content_chars DESC LIMIT 300
), rnd AS (
  SELECT * FROM (
    SELECT p.*, 'random' AS stratum_pick,
           row_number() OVER (PARTITION BY p.agent, p.mode ORDER BY random()) AS rn
    FROM c01_pool p
    WHERE p.session_id || ':' || p.seq NOT IN (SELECT session_id || ':' || seq FROM top)
  ) WHERE rn <= 40 LIMIT 300
)
SELECT session_id, seq, 10 AS k_before, 5 AS k_after,
       agent, mode, repo, file_path, content_chars, input_chars,
       max_earlier_read_chars, rewrite_ratio, output_usd_estimate,
       stratum_pick, agent || '|' || mode AS stratum
FROM (SELECT * EXCLUDE (rn) FROM rnd UNION ALL SELECT * FROM top)
ORDER BY stratum_pick, content_chars DESC;

-- @headline
SELECT count(*) AS pool_of_writes_on_known_files,
       sum(content_chars) AS content_chars_in_pool,
       sum(output_usd_estimate) AS output_usd_in_pool,
       median(content_chars) AS median_content_chars,
       count(DISTINCT session_id) AS sessions_in_pool
FROM c01_pool;
