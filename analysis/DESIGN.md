# Token-waste analysis on the SWE-chat ledger: architecture

Input: `analysis/ledger/` (Parquet: calls, tool_calls, user_turns, events, sessions; see
`analysis/README.md` for columns). Raw transcripts stay in `data/transcripts/` and are opened only
by layer 1b (raw probes) and layer 3 (judge), by line index (`seq` = 0-based record index in the file;
for OpenCode `seq` is the message/part index, see README).

Three layers, each a separate runnable, each writing under `analysis/results/`:

| Layer | What | Cost | Runner |
|---|---|---|---|
| 1 | SQL on the full population, one file per thesis | 0 USD, seconds | `analysis/run_queries.py` |
| 1b | Raw-file probes on a random sample of tool calls (things the ledger does not store) | 0 USD, ~1 min | `analysis/raw_probes.py` |
| 2 | LLM classification of all 121k human prompts | ~4 USD DeepSeek Flash | `analysis/llm/classify_prompts.py` |
| 3 | LLM judge on stratified samples of anomalies found by layer 1 | ~1-20 USD | `analysis/llm/judge.py` |

Everything runs with `uv run --with duckdb --with pyarrow --with orjson [--with openai --with anthropic] <script>`.
Python 3.9 syntax. No other installs, no background processes, no servers. No em or en dashes anywhere.

## Layer 1: pricing and theses (SQL)

### Runner contract (`run_queries.py`)
- Opens (creates) `analysis/ledger.duckdb`. First run executes `queries/00_setup.sql` which creates
  views over the Parquet folders and the table `prices`, plus the materialised table `calls_priced`.
- Then executes every `queries/T*.sql` in name order. Inside a file, statements are separated by
  marker lines `-- @out <result_name>`; the statement following a marker is executed and its result
  written to `results/<file_stem>__<result_name>.csv` and rendered as a markdown table (max 40 rows)
  in `results/REPORT.md` under the heading from the first line comment `-- # <title>`. A statement
  without a marker is executed for side effects only (temp tables). A marker `-- @headline` marks
  a one-row result whose columns are rendered as the thesis summary line.
- CLI: `--only T02,T04`, `--ledger DIR`, `--results DIR`, `--rebuild` (drop calls_priced).
- Failures in one file are reported and do not stop the others.

### Prices (`analysis/prices.csv`, USD per 1M tokens)
Columns: model_pattern (SQL LIKE), provider, p_input, p_cache_read, p_cache_write_5m, p_cache_write_1h, p_output.
Anthropic rule: cache read = 0.1 x input, 5m write = 1.25 x input, 1h write = 2 x input.

| pattern | provider | input | cache read | 5m write | 1h write | output |
|---|---|---|---|---|---|---|
| claude-opus-4-% (4-5, 4-6, 4-7, 4-8) | anthropic | 5 | 0.5 | 6.25 | 10 | 25 |
| claude-sonnet-4-% (4-5, 4-6) | anthropic | 3 | 0.3 | 3.75 | 6 | 15 |
| claude-sonnet-5% | anthropic | 2 | 0.2 | 2.5 | 4 | 10 |
| claude-fable-5% | anthropic | 10 | 1 | 12.5 | 20 | 50 |
| claude-opus-5% | anthropic | 5 | 0.5 | 6.25 | 10 | 25 |
| claude-haiku-4-5% | anthropic | 1 | 0.1 | 1.25 | 2 | 5 |
| gpt-5.5% | openai | 5 | 0.5 | - | - | 30 |
| gpt-5.4-mini% | openai | 0.75 | 0.075 | - | - | 4.5 |
| gpt-5.4% | openai | 2.5 | 0.25 | - | - | 15 |
| gpt-5.3-codex% | openai | 1.75 | 0.175 | - | - | 14 |

Anything else (glm, qwen, mimo, gemini, `<synthetic>`, NULL): unpriced, cost NULL. Report the share
of calls and tokens that are unpriced per agent.

Cost per call (`calls_priced.cost_usd`, plus the four components as separate columns):
- anthropic: input*p_input + cache_read*p_cache_read + c5m*p_5m + c1h*p_1h + output*p_output.
  If cache_create_tokens is set but the 5m/1h split is NULL, treat all of it as 5m.
- openai (codex, opencode with gpt models): OpenAI `input_tokens` INCLUDES cached tokens, so
  (input - cache_read)*p_input + cache_read*p_cache_read + output*p_output. Output includes reasoning.
- `ctx_tokens` = input + cache_read + cache_create (anthropic) or input (openai) = context size of that call.
- `session_cost_usd`, `mode` (vibe if attr_agent_percentage >= 95, human if <= 5, collab otherwise,
  unknown if NULL), `committed_lines` (attr_total_committed) joined from sessions into a view `sessions_x`.

### Theses, one SQL file each. P0 first.

T01 baseline (P0): total USD by agent and model; component shares (input / cache read / cache write /
output); USD per session p50 p90 p99; USD and tokens per committed line by mode; unpriced share.
This is the denominator for every other thesis: express each waste in USD and as % of T01 total.

T02 coffee_break (P0, claude_code only): calls ordered by ts within session, non-sidechain. gap_min =
minutes since previous call. cache_break = cache_create_tokens >= 0.5 * prev.ctx_tokens (the whole
prefix was rewritten). Buckets: <1, 1-5, 5-60, >60 min. Per bucket: calls, break rate, re-cached
tokens, USD of cache writes. Headline: USD spent on cache re-writes in calls that follow a gap > 5 min,
and its % of total cache-write USD. Also split by TTL era: month of ts, share of 1h vs 5m writes.

T03 zero_info (P0): tool_calls where the same result_hash already occurred earlier in the same session
(result_chars > 0). Count, share of tool calls, share of result chars, by agent and tool_kind. Top 20
command_head values (bash) by repeated occurrences. Direct USD = repeated result_chars/4 * p_input
(lower bound). Headline: % of all tool-result characters that are exact repeats.

T04 context_rent (P0): for each tool call: later_calls = number of calls in the session with seq >
this seq (non-sidechain). rent_tokens = result_chars/4 * later_calls. Sum by tool_kind and by result
size bucket (<1k, 1-10k, 10-50k, >50k chars). USD at the session model's cache-read price. Top 20
single tool results by rent (session, seq, tool, command_head, chars, later_calls). Headline: share
of all cache-read tokens attributable to tool results (sum rent / sum cache_read), and USD of rent
generated by results > 10k chars.

T05 entry_cost (P0): first call per session (min seq, non-sidechain): cache_create + input =
entry_tokens. Median and p90 by harness_version (claude_code) and by month; same for codex by
harness_version. USD = entry_tokens * cache write price. Headline: entry cost trend first vs last
version with >= 50 sessions.

T06 truncated: stop_reason = 'max_tokens': count, share of calls, by model; USD of the next call's
input side (the continuation re-pays the context).

T07 path_guessing: tool_kind in (read, edit, write) AND is_error AND error_head ~ 'does not exist|
No such file|ENOENT|not found|File not found'. Rate per agent and model. Recovery: USD of the next
3 calls after such an error.

T08 ceremony: tool_kind in (todo, task): share of tool calls; output-side tokens = input_chars/4;
USD. Sessions with vs without such calls: completion rate (committed_lines > 0), USD per committed
line, by mode.

T09 polling: bash command_head ~ '(^|[;&| ])sleep [0-9]+' or 'gh run watch' or 'wait'. Count,
sequences (>= 2 in 5 consecutive calls), USD of those calls incl. context.

T10 rewrite_vs_edit (P0): Write on a file_path that appeared earlier in the session (read or edit):
content_chars vs the largest earlier read result_chars of that path (rewrite_ratio). Count Writes on
known files, tokens (content_chars/4), USD at output price. Edit with old_string_chars > 1500:
count, chars, USD. JSON overhead estimate: (input_chars - content_chars - 40) / content_chars for
Write; report median. Headline: USD of output tokens spent on Writes to files already in context.

T11 unread_output (P0): the last call of a turn = a non-sidechain call whose next event in the session
is a non-meta user_turn (by seq). words = n_text_chars/5; read_time_s = words/250*60; delta_s =
user_turn.ts - call.ts. unread if delta_s < 0.5*read_time_s. Share of final-text tokens (n_text_chars/4)
flagged unread, by agent; distribution of delta vs read_time. Exclude interrupt turns. Headline: USD
of output tokens in final replies that could not have been read.

T12 human_wait (P0): per turn: agent_time = last call ts of turn - user_turn ts; human_time =
user_turn ts - previous turn's last call ts (cap 30 min, else treat as break). Sum per session.
Headline: total agent-working hours vs total USD; at 60 USD/h, ratio of human wait cost to token cost,
by mode. Also median agent_time per turn by agent.

T13 abandoned (P0): sessions with committed_lines = 0 or NULL attribution: count, USD, share of
total USD, by agent and mode. Where in the session do they die: USD-weighted median position of last
user_turn.

T14 hot_files (P0): per repo, file_path with tool_kind in (edit, write): distinct sessions, distinct
users (cwd home dir hash), total edits. Top 30 files across repos with >= 20 sessions. Concentration:
share of edits in top 5% of files per repo. Proxy for "agent breaks it": share of edits to a file
followed within 3 calls by is_error, and share followed by a non-meta user_turn with human_chars <
200 (short correction). Compare hot (>= 10 sessions) vs cold files.

T15 harness_vs_model: repos with >= 2 agents: USD and tokens per committed line by agent x model
family (opus, sonnet, gpt-5.5, gpt-5.4, other), by mode.

T16 subagents (claude_code): share of USD in is_sidechain calls; sessions with vs without
sidechains: USD per committed line, completion rate, by mode.

T17 bypass (claude_code): permission-mode events: dominant mode per session (value with most
events). USD per committed line, tool error rate, tool calls per committed line, by mode.

T18 impatience: queue-operation events per session; user_turns is_interrupt; USD of calls between
the last user_turn and the interrupt (sunk). Sessions with >= 1 interrupt vs none: USD per committed line.

T19 compaction (claude_code): system subtype 'compact_boundary' and 'microcompact_boundary' events
(value carries trigger/preTokens if the ledger stored it). Count per session; share of sessions;
after each boundary: within next 20 tool calls, share of read file_paths that were read before the
boundary in the same session; USD of those re-reads.

T20 self_reread: Read of file_path within 5 calls after Write or Edit of the same path; edit thrash:
same file_path edited >= 3 times within 10 calls. Counts, USD.

T21 fast_mode (claude_code): speed = 'fast' share of calls and USD; sessions using fast: median
agent_time per turn vs standard (join T12).

T22 model_switch: user = regexp_extract(cwd, '^/(Users|home)/([^/]+)', 2) hashed; user x repo with
>= 2 distinct models and >= 3 sessions each: USD and tokens per committed line per model.

T23 local_hour (codex only): timezone column: local hour of the first call; sessions per local hour;
tool error rate, abandonment rate, USD per committed line by hour bucket (night 0-6, day 6-18, evening).

T24 harness_whisper: events attachment payload_chars by subtype and by harness_version, per session,
vs user_turns human_chars. Share of injected chars in (attachments + human prompts). Trend by version.

Each file ends with a `-- @headline` statement returning one row with the numbers that would go on
a slide (name the columns in plain words).

## Layer 1b: raw probes (`raw_probes.py`)
The ledger stores lengths and hashes, not content. Sample from tool_calls (seeded RNG, default N=3000
per probe, claude_code + codex + opencode), open the raw file, take the record at `seq`, measure:
- READ results: share of characters that are `cat -n` line-number prefixes (regex `^\s*\d+\t` per line),
  and lines count. Output: median and mean share; extrapolate to all Read result chars in the ledger.
- WRITE/EDIT inputs: JSON serialisation overhead = len(json.dumps(input)) - len(raw content strings);
  and separately the count of `\n` and `"` and leading-whitespace chars in content (indentation share).
  Group by file extension (py, ts, tsx, js, go, rs, md, json, yaml, other).
- BASH results: gzip ratio of the result text (bytes / gzipped bytes); bucket by ratio; share of result
  chars in results with ratio > 10 (logs, listings).
- FINAL TEXT: the assistant text of last-call-of-turn rows: count of markdown headers, bullet lines,
  code fences, and the share of chars in "summary" sections (lines after a header matching
  summary|recap|next steps|what I did), to size "chatty finishes".
Write `results/probes/<probe>.csv` and `results/probes/PROBES.md` with the extrapolated totals in tokens
and USD (use prices.csv and the same cost rules as layer 1).

## Layer 2: prompt classification (`llm/classify_prompts.py`)
- Provider abstraction in `llm/client.py`: `deepseek` (OpenAI-compatible, base_url
  https://api.deepseek.com, model deepseek-v4-flash, key env DEEPSEEK_API_KEY, uses the `openai`
  package) and `anthropic` (model claude-haiku-4-5 by default, `anthropic` package, key
  ANTHROPIC_API_KEY, JSON via a single tool with strict schema). Thread pool with `--concurrency`,
  retries with backoff, per-item cache in `results/llm/cache/<task>/<id>.json` so reruns resume.
  `--dry-run` prints item count, estimated tokens and USD and exits. `--limit N` for tests.
- Items: user_turns with is_meta = false and human_chars > 0. Context per item: the previous
  assistant text_head (300 chars) and previous tool names (up to 5) from calls/tool_calls in the same
  session by seq, plus the prompt (human text, first 1500 chars).
- Batch 15 items per request; the model returns a JSON array with, per id: label in
  {new_task, follow_up, approval, correction, failure_report, interruption, question, meta_other},
  pushback (bool: correction or failure_report or explicit dissatisfaction), sentiment
  {neutral, frustrated, positive}, language (ISO 639-1), mentions_file (bool).
- Output: `results/llm/prompt_labels.parquet` (session_id, seq, label, pushback, sentiment, language,
  mentions_file, model, cost_usd) and a summary markdown with label distribution by agent.

## Layer 3: judge (`llm/judge.py`)
- Case files are CSV produced by layer 1 queries (`results/cases/<case_type>.csv`) with columns
  session_id, seq, k_before, k_after, plus any context columns. Case generators live in
  `queries/C*.sql` (run by run_queries.py, written to results/cases/): C01 rewrite_necessary (top 300
  Writes by content_chars on known files + 300 random such Writes, stratified by agent x mode),
  C02 tool_result_used (top 300 tool results by rent + 300 random with result_chars > 5k),
  C03 hot_file_cause (for each of the top 40 hot files: 5 random edit events with 10 calls of context).
- For each case: open the raw transcript, take records [seq - k_before, seq + k_after], compact
  them (drop signatures, progress, attachments, file-history-snapshot; tool results truncated to
  2000 chars head + 500 tail; thinking dropped; keep text, tool names and args truncated to 1500 chars),
  render as a readable transcript with `[seq]` markers, and ask the judge with the rubric for that
  case type. Rubrics (JSON answers):
  - rewrite_necessary: was_full_rewrite_needed (bool), estimated_lines_actually_changed (int),
    reason (<= 30 words).
  - tool_result_used: was_result_referenced_later (bool), fraction_of_result_needed
    {none, small, most, all}, reason.
  - hot_file_cause: cause in {architecture_hub, agent_regression, user_iteration, config_churn,
    test_file, unclear}, reason.
- Output `results/llm/judge_<case_type>.parquet` and a markdown summary with rates by stratum and
  a 95% Wilson interval; extrapolation to the population uses the layer 1 counts for that stratum.
- Default judge: deepseek-v4-pro or claude-sonnet-5 (`--provider`, `--model`). Never run without
  `--dry-run` first; the dry run prints USD.

## Results layout
```
analysis/results/REPORT.md              layer 1 headlines and tables
analysis/results/T*__*.csv              layer 1 result sets
analysis/results/cases/*.csv            layer 3 inputs
analysis/results/probes/                layer 1b
analysis/results/llm/                   layers 2 and 3
```
