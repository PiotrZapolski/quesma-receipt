-- # T10 rewrite vs edit: writing a whole file the model already has
-- A Write on a file_path that was read or edited earlier in the same session means
-- the content is emitted a second time, at output price. Same for Edit calls that
-- quote a huge old_string.

CREATE OR REPLACE TEMP TABLE t10 AS
SELECT tc.session_id, tc.agent, tc.seq, tc.tool_kind, tc.file_path,
       tc.input_chars, tc.content_chars, tc.old_string_chars, tc.new_string_chars,
       s.p_output, s.mode,
       count(*) FILTER (WHERE tc.tool_kind IN ('read', 'edit', 'write'))
         OVER (PARTITION BY tc.session_id, tc.file_path ORDER BY tc.seq, tc.tool_use_id
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS earlier_touches,
       max(CASE WHEN tc.tool_kind = 'read' THEN tc.result_chars END)
         OVER (PARTITION BY tc.session_id, tc.file_path ORDER BY tc.seq, tc.tool_use_id
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS max_earlier_read_chars
FROM tool_calls tc
JOIN sessions_x s USING (session_id)
WHERE tc.file_path IS NOT NULL AND tc.tool_kind IN ('read', 'edit', 'write');

CREATE OR REPLACE TEMP TABLE t10w AS
SELECT *, coalesce(content_chars, 0) / 4.0 AS content_tokens,
          coalesce(content_chars, 0) / 4.0 * p_output / 1e6 AS content_usd,
          CASE WHEN max_earlier_read_chars > 0
               THEN coalesce(content_chars, 0) * 1.0 / max_earlier_read_chars END AS rewrite_ratio
FROM t10
WHERE tool_kind = 'write' AND coalesce(content_chars, 0) > 0;

-- @out writes_on_known_files
SELECT agent,
       count(*) AS writes,
       count(*) FILTER (WHERE earlier_touches > 0) AS writes_on_known_files,
       100.0 * count(*) FILTER (WHERE earlier_touches > 0) / count(*) AS pct_writes_on_known_files,
       sum(content_tokens) FILTER (WHERE earlier_touches > 0) AS output_tokens_on_known_files,
       sum(content_usd) FILTER (WHERE earlier_touches > 0) AS usd_on_known_files,
       sum(content_usd) AS usd_all_writes
FROM t10w
GROUP BY 1
ORDER BY usd_on_known_files DESC NULLS LAST;

-- @out rewrite_ratio_distribution
SELECT CASE WHEN rewrite_ratio IS NULL THEN '0. no earlier read'
            WHEN rewrite_ratio < 0.25 THEN '1. <25% of the file'
            WHEN rewrite_ratio < 0.9 THEN '2. 25-90%'
            WHEN rewrite_ratio <= 1.1 THEN '3. ~same size (90-110%)'
            ELSE '4. bigger than what was read' END AS bucket,
       count(*) AS writes,
       sum(content_tokens) AS content_tokens,
       sum(content_usd) AS usd,
       median(coalesce(content_chars, 0)) AS median_content_chars
FROM t10w
WHERE earlier_touches > 0
GROUP BY 1
ORDER BY 1;

-- @out big_old_string_edits
SELECT agent,
       count(*) AS edits,
       count(*) FILTER (WHERE old_string_chars > 1500) AS edits_old_string_over_1500,
       100.0 * count(*) FILTER (WHERE old_string_chars > 1500) / count(*) AS pct,
       sum(old_string_chars) FILTER (WHERE old_string_chars > 1500) AS old_string_chars,
       sum(coalesce(old_string_chars, 0) / 4.0 * p_output / 1e6) FILTER (WHERE old_string_chars > 1500) AS usd_old_string,
       sum(coalesce(old_string_chars, 0) / 4.0 * p_output / 1e6) AS usd_old_string_all_edits
FROM t10
WHERE tool_kind = 'edit'
GROUP BY 1
ORDER BY usd_old_string DESC NULLS LAST;

-- @out json_overhead_for_writes
SELECT agent,
       count(*) AS writes,
       median((input_chars - content_chars - 40) * 1.0 / nullif(content_chars, 0)) AS median_json_overhead_ratio,
       quantile_cont((input_chars - content_chars - 40) * 1.0 / nullif(content_chars, 0), 0.9) AS p90_json_overhead_ratio,
       sum(input_chars - content_chars) / 4.0 AS extra_tokens_vs_bare_content
FROM t10w
WHERE input_chars IS NOT NULL AND content_chars > 100
GROUP BY 1
ORDER BY writes DESC;

-- @out top_rewritten_files
SELECT substr(file_path, 1, 80) AS file_path_80, any_value(agent) AS agent,
       count(*) AS writes_on_known_file,
       sum(content_chars) AS content_chars,
       sum(content_usd) AS usd
FROM t10w
WHERE earlier_touches > 0
GROUP BY 1
ORDER BY usd DESC
LIMIT 20;

-- @headline
SELECT sum(content_usd) FILTER (WHERE earlier_touches > 0) AS usd_output_writes_to_files_already_in_context,
       100.0 * sum(content_usd) FILTER (WHERE earlier_touches > 0)
             / (SELECT sum(coalesce(output_usd, 0)) FROM calls_priced) AS pct_of_all_output_usd,
       count(*) FILTER (WHERE earlier_touches > 0) AS writes_on_known_files,
       100.0 * count(*) FILTER (WHERE earlier_touches > 0) / count(*) AS pct_of_writes_on_known_files,
       sum(content_tokens) FILTER (WHERE earlier_touches > 0) AS output_tokens_rewritten,
       (SELECT sum(coalesce(old_string_chars, 0) / 4.0 * p_output / 1e6)
        FROM t10 WHERE tool_kind = 'edit' AND old_string_chars > 1500) AS usd_old_string_quotes_over_1500_chars,
       (SELECT median((input_chars - content_chars - 40) * 1.0 / nullif(content_chars, 0))
        FROM t10w WHERE input_chars IS NOT NULL AND content_chars > 100) AS median_json_overhead_ratio
FROM t10w;
