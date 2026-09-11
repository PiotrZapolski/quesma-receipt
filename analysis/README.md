# build_ledger - flat Parquet ledger of 9770 agent transcripts

Extraction layer only. Nothing is analysed here: the scripts turn
`data/transcripts/*.jsonl` (17.8 GB, 4 harness formats) into flat Parquet tables
that DuckDB can query directly.

## Running

```bash
# full run (done by the user, not during development)
uv run --with duckdb --with orjson --with pyarrow analysis/build_ledger.py \
    --out analysis/ledger --workers 6

# the sample used for the validation table below
uv run --with duckdb --with orjson --with pyarrow analysis/build_ledger.py \
    --sessions analysis/sample_sessions.txt --out analysis/ledger_sample --workers 2

uv run --with duckdb analysis/validate.py --ledger analysis/ledger_sample
```

CLI: `--out DIR`, `--limit N`, `--sessions FILE` (one session id per line, `#`
comments allowed), `--agents claude_code,codex,opencode,cursor`, `--workers N`
(default 6), `--flush-rows N` (default 50000), `--no-sessions-table`.

Note on `--limit N`: sessions are sorted largest-file-first (so the 133 MB files
start while workers are free), which means `--limit N` keeps the **N biggest**
files. For a cheap smoke test use `--sessions` with an explicit id list instead.

Query it:

```sql
SELECT * FROM read_parquet('analysis/ledger/calls/*.parquet');
SELECT * FROM read_parquet('analysis/ledger/tool_calls/*.parquet');
SELECT * FROM read_parquet('analysis/ledger/user_turns/*.parquet');
SELECT * FROM read_parquet('analysis/ledger/events/*.parquet');
SELECT * FROM read_parquet('analysis/ledger/sessions/*.parquet');
```

Layout: `<out>/<table>/part-<pid>-<n>.parquet` (zstd). Each worker writes its own
part files, flushing every 50k rows per table; there is no shared state. Sessions
are processed largest-file-first over a `multiprocessing.Pool` (spawn). Bad lines
and failed sessions never abort the run - they are counted and appended to
`<out>/errors.jsonl` as `{session_id, line_no, exception}`.

## Tables

### `calls` - one row per model API response

`session_id, agent, repo, seq, ts, msg_id, request_id, parent_id, is_sidechain,
model, harness_version, stop_reason, speed, service_tier, input_tokens,
cache_read_tokens, cache_create_tokens, cache_create_5m, cache_create_1h,
output_tokens, reasoning_tokens, context_window, n_text_chars, n_thinking_chars,
n_thinking_blocks, n_tool_uses, text_head (300 chars), cwd, git_branch, timezone`

### `tool_calls` - one row per tool invocation

`session_id, agent, repo, seq, msg_id, ts, tool_use_id, tool_name (raw),
tool_kind (read|edit|write|bash|glob|grep|web|task|todo|mcp|other),
file_path_raw, file_path (relative to cwd/root when it is under it),
patched_files (JSON array string), command_head (500 chars), input_chars,
old_string_chars, new_string_chars, content_chars, read_offset, read_limit,
result_chars, result_hash (sha1 of result text), is_error, error_head (200
chars), result_ts, result_latency_ms, is_interrupted`

### `user_turns` - human-authored prompts

`session_id, agent, repo, seq, ts, prompt_id, text (full), chars, human_chars,
is_meta, is_interrupt, is_slash_command, has_system_reminder`

### `events` - everything else

`session_id, agent, repo, seq, ts, event_type, subtype, value, payload_chars`

### `sessions` - flattened `metadata/sessions.json`

Written once by the main process with DuckDB `read_json(..., sample_size=-1)`.
42 columns: `session_id, session_id_meta, agent, agent_raw, detected_format,
repo, created_at, branch, strategy, bytes, trajectory, models (JSON),
agent_versions (JSON), files_touched (JSON), n_files_touched` plus every scalar
under `statistics.*` / `checkpoint_token_usage.*` / `initial_attribution.*`
prefixed `stat_` / `ckpt_` / `attr_`. All 9770 catalog rows are written,
including harnesses we skip, so joins never lose a session.

`seq` is the 0-based index of the source record inside the file (line index for
the three JSONL formats, message index for OpenCode), so rows can be re-ordered
and joined back to the raw line.

## Per-harness mapping of counts

| | claude_code | codex | opencode | cursor |
|---|---|---|---|---|
| **one `calls` row =** | one `.message.id` (lines with the same id merged) | one `event_msg/token_count` with non-null `info` | one `step-finish` part (fallback: one assistant message) | one `role=assistant` line |
| **tokens** | `message.usage`, max per field across the lines of that id | `info.last_token_usage` | `step-finish.tokens` (or `info.tokens`) | none (all NULL) |
| **reasoning tokens** | none (thinking is inside `output_tokens`) | `reasoning_output_tokens` | `tokens.reasoning` | none |
| **cache 5m/1h split** | `usage.cache_creation.ephemeral_*` | not present | not present | not present |
| **`tool_calls` row =** | `tool_use` / `server_tool_use` content block | `function_call`, `custom_tool_call`, `web_search_call`, `tool_search_call`, `local_shell_call` | `parts[].type == "tool"` | `tool_use` content block |
| **tool result** | `tool_result` block on the next `user` line, matched by `tool_use_id` | `*_call_output`, matched by `call_id` | `state.output` / `state.error` inline | **not present in the format** |
| **`user_turns` row =** | `type=user` line with text blocks (or a string content) | `event_msg/user_message` (plus non-duplicate `response_item` `role=user`) | `role=user` message text parts | `role=user` line |
| **`events`** | system, attachment, file-history-snapshot, permission-mode, mode, queue-operation, last-prompt, progress, ai-title, agent-name, custom-title, pr-link | session_meta, turn_context, compacted, non-call event_msg, non-call response_item | `patch` / `file` / unknown parts | `turn_ended` and other role-less lines |
| **compaction marker** | `events` where `event_type='system'` and `subtype IN ('compact_boundary','microcompact_boundary')`; `value` = `compactMetadata.trigger` | `events` `event_type='compacted'` and `event_msg/context_compacted` | none seen | none |

## What the formats actually look like (differences from the spec)

Verified with `jq` over 20-40 real sessions per harness before writing each
parser. Everything below deviates from, or adds to, `SPEC.md`.

**Dataset / catalog**

- `session_id` is **not unique**: 180 values are shared by 2-32 transcript files
  (32 files have no `session_id` at all and are named `unidentified-*.jsonl`).
  The transcript basename **is** unique (9770/9770). The ledger therefore uses
  the basename as `session_id`; the catalog value is kept as `session_id_meta`.
- `agent` and `detected_format` disagree for 151 sessions. The big groups:
  65 labelled `agent: "Claude Code"` are byte-for-byte Cursor transcripts,
  30 labelled `"Agent"` are Claude Code, 26 `"Claude Code"` are `unknown`,
  7 `"Claude Code"` are Copilot CLI. The spec only says how to normalize
  `agent`, so the `agent` column still comes from the `agent` field, but the
  **parser** is chosen from `detected_format` when that normalizes to one of the
  four (otherwise from `agent`). Both columns are in the `sessions` table, so a
  stricter filter is available. The ~9 sessions whose `detected_format` is a
  harness we do not parse (Copilot CLI, Pi, Gemini CLI) still get their `agent`
  parser and will mostly land in `errors.jsonl` or produce near-empty output.
- Files are read from the catalog's `trajectory` path, not from
  `data/transcripts/<session_id>.jsonl`, because of the two points above.

**claude_code**

- Lines that share `.message.id` do **not** repeat the same usage: `output_tokens`
  grows across the lines of one response (e.g. 4 -> 318 -> 318). Merging takes the
  **max** of each usage field, not the first. With that rule, `sum(output_tokens)`
  matches `stat_output_tokens` exactly on 5/5 sample sessions.
- `stop_reason` is null on the early lines of a response; the last non-null wins.
- Compaction markers exist and the spec did not name them:
  `system/compact_boundary` (with `compactMetadata.trigger` = `auto`/`manual` and
  `preTokens`) and `system/microcompact_boundary`. Other subtypes seen:
  `stop_hook_summary`, `turn_duration`, `away_summary`, `local_command`,
  `api_error`, `bridge_status`.
- Line types beyond the spec list: `mode`, `agent-name`, `custom-title`,
  `pr-link`. Content block types beyond the spec list: `server_tool_use` and
  `advisor_tool_result` (both rare); `redacted_thinking` is handled defensively.
- `usage` has no `speed`/`service_tier`/`iterations` in older CLI versions
  (`speed` present on ~88% of sample rows, `service_tier` ~100%).
- `<system-reminder>` is now mostly delivered as `attachment` records
  (`attachment.type = task_reminder`, `hook_success`, ...), not inline in user
  text, which is why `has_system_reminder` is near zero on modern sessions.
- `tool_result.content` is a string ~93% of the time and a block array ~7%.

**codex**

- `apply_patch` is **not** inside `shell_command` in any version present in this
  dataset. It is a `custom_tool_call` whose `input` is the raw
  `*** Begin Patch / *** Update File: X` text. The same `*** ... File:` parsing is
  still applied to shell commands that mention `apply_patch`, but it never fired
  in the sample.
- The shell tool is `exec_command` with argument key **`cmd`** (not `command`);
  `shell_command` / `shell` use `command`. Both are handled.
- There is also a `custom_tool_call` named `exec` whose `input` is a JavaScript
  program calling `tools.shell_command(...)`, and `tool_search_call` items.
- `event_msg/token_count` is emitted with **`info: null`** as a rate-limit
  heartbeat. Those are not API responses; only events with
  `info.last_token_usage` become `calls` rows (the rest go to `events` as
  `token_count_norate`). Without this filter the call count is inflated.
- Some (older, short) sessions contain **no** `token_count` events at all. For
  those only, the ledger falls back to one `calls` row per assistant
  `response_item` message, with all token columns NULL.
- `function_call_output.output` is a string ~99% of the time;
  `custom_tool_call_output.output` is usually a `[{type,text}]` array.
- `reasoning` items carry text in `summary[].text` (`summary_text`) and
  sometimes `content[]`; about 70% of them are empty (encrypted-only).
- Top-level type `compacted` and `event_msg/context_compacted` exist.
- User-prompt dedupe: `response_item` `role=user` echoes the `event_msg`
  `user_message`. The spec says "dedupe by text within the same second"; the echo
  can be several seconds away, so the ledger dedupes by **exact text with a
  multiset count** over the whole session instead (an echo is dropped only if an
  `event_msg` with identical text is still unmatched). Result: `user_turns`
  matches `stat_user_messages` exactly on 5/5 codex sessions.

**opencode**

- Two on-disk shapes. 782/784 files are the pretty-printed whole-file
  `{info, messages}` object the spec describes. One file is JSONL with one
  `{info, parts}` message per line, and one file (`a324af07-...`) is a completely
  different `{sessionId, projectHash, messages:[{id, type, content}]}` schema. The
  parser tries the whole-file form, falls back to per-line messages, and records
  anything else as an `unparsed_message` event rather than failing.
- `message.info.model` is sometimes a nested `{providerID, modelID}` object and
  sometimes the flat `modelID`/`providerID` pair; both are read.
- `step-finish.tokens` are **per step**, and `info.tokens` equals the tokens of
  the last step (not the sum), so using step-finish rows is required. Confirmed:
  `count(calls)` equals `ckpt_api_call_count` exactly on 5/5 sample sessions.
- `apply_patch` is a tool whose input key is `patchText`, with the same
  `*** Add/Update/Delete File:` grammar as codex.
- Errors live in `state.error` (a string) as well as `state.status == "error"`;
  `state.output` can be absent on an error.
- `state.input` is occasionally a JSON **string** rather than an object.

**cursor**

- Lines are `{role, message:{content:[...]}}` plus bare
  `{type:"turn_ended", status, error?}` records (no `role`) which go to `events`.
- Only two content block types exist: `text` and `tool_use`. There are **no**
  `tool_result` blocks, no `id` on `tool_use`, no timestamps and no usage. So for
  cursor: `calls.ts`, all token columns, `tool_calls.tool_use_id`, `ts`,
  `result_*`, `is_error` and `is_interrupted` are all NULL by construction.
- Tool names are PascalCase and cursor-specific: `Shell`, `StrReplace`, `Read`,
  `Write`, `Delete`, `Glob`, `Grep`, `TodoWrite`, `CreatePlan`, `AskQuestion`,
  `CallMcpTool`, `WebFetch`, `WebSearch`, `Task`, `AwaitShell`, `ReadLints`,
  `SetActiveBranch`. Input keys: `path`, `command`+`working_directory`,
  `old_string`/`new_string`, `contents`, `glob_pattern`, `pattern`,
  `offset`/`limit`.
- The first user text is wrapped in harness tags (`<timestamp>`,
  `<attached_files>`, `<code_selection>`, `<git_diff_from_branch_to_main>`) with
  the real prompt inside `<user_query>`. `human_chars` therefore uses the
  `<user_query>` contents when that tag is present, and otherwise strips the
  known harness blocks. In the sample that halves the character count
  (287642 raw -> 146176 human).

## Validation

`validate.py` compares, per session present in the ledger, the ledger counts
against `metadata/sessions.json`. Table A is the comparison the spec asks for.
Table B uses the metadata fields that actually describe the same thing - the
spec's choices are systematically off for reasons explained under "known gaps".

Output of
`uv run --with duckdb analysis/validate.py --ledger analysis/ledger_sample`
on the 20-session sample (5 per harness, mixed sizes, 13.0 MB, 0 errors,
1450 calls / 1797 tool_calls / 157 user_turns / 1239 events):

### A. spec comparison (ledger vs `metadata.statistics`)

| metric | agent | sessions | ledger total | metadata total | median rel delta | exact | meta=0 |
|---|---|---:|---:|---:|---:|---:|---:|
| tool_calls | claude_code | 5 | 495 | 481 | +0.0% | 3 | 0 |
| tool_calls | codex | 5 | 429 | 426 | +0.0% | 4 | 1 |
| tool_calls | cursor | 5 | 675 | 675 | +0.0% | 5 | 3 |
| tool_calls | opencode | 5 | 198 | 170 | +18.2% | 1 | 0 |
| calls | claude_code | 5 | 459 | 193 | +360.0% | 0 | 0 |
| calls | codex | 5 | 295 | 126 | +282.0% | 1 | 1 |
| calls | cursor | 5 | 573 | 573 | +0.0% | 5 | 0 |
| calls | opencode | 5 | 123 | 31 | +800.0% | 0 | 0 |
| output_tokens | claude_code | 5 | 244087 | 244087 | +0.0% | 5 | 0 |
| output_tokens | codex | 5 | 105830 | 52833 | +93.6% | 1 | 1 |
| output_tokens | cursor | 5 | 0 | 0 | n/a | 5 | 5 |
| output_tokens | opencode | 5 | 59663 | 56389 | +0.0% | 3 | 0 |
| user_turns(!meta) | claude_code | 5 | 24 | 65 | -40.0% | 0 | 0 |
| user_turns(!meta) | codex | 5 | 16 | 17 | +0.0% | 4 | 0 |
| user_turns(!meta) | cursor | 5 | 67 | 68 | +0.0% | 4 | 0 |
| user_turns(!meta) | opencode | 5 | 7 | 7 | +0.0% | 5 | 0 |

### B. closer baselines

| metric | agent | sessions | ledger total | metadata total | median rel delta | exact | meta=0 |
|---|---|---:|---:|---:|---:|---:|---:|
| calls vs ckpt_api_call_count | claude_code | 5 | 459 | 426 | +1.7% | 1 | 1 |
| calls vs ckpt_api_call_count | codex | 5 | 295 | 274 | +0.0% | 4 | 1 |
| calls vs ckpt_api_call_count | cursor | 5 | 573 | 0 | n/a | 0 | 5 |
| calls vs ckpt_api_call_count | opencode | 5 | 123 | 123 | +0.0% | 5 | 0 |
| output_tokens vs ckpt_output_tokens | claude_code | 5 | 244087 | 230907 | +1.1% | 1 | 1 |
| output_tokens vs ckpt_output_tokens | codex | 5 | 105830 | 107396 | -5.1% | 1 | 1 |
| output_tokens vs ckpt_output_tokens | cursor | 5 | 0 | 0 | n/a | 5 | 5 |
| output_tokens vs ckpt_output_tokens | opencode | 5 | 59663 | 59663 | +0.0% | 5 | 0 |
| output-reasoning vs stat_output_tokens | claude_code | 5 | 244087 | 244087 | +0.0% | 5 | 0 |
| output-reasoning vs stat_output_tokens | codex | 5 | 53776 | 52833 | +0.3% | 3 | 1 |
| output-reasoning vs stat_output_tokens | cursor | 5 | 0 | 0 | n/a | 5 | 5 |
| output-reasoning vs stat_output_tokens | opencode | 5 | 43683 | 56389 | -76.3% | 0 | 0 |
| user_turns(all) vs stat_user_messages | claude_code | 5 | 65 | 65 | +0.0% | 5 | 0 |
| user_turns(all) vs stat_user_messages | codex | 5 | 17 | 17 | +0.0% | 5 | 0 |
| user_turns(all) vs stat_user_messages | cursor | 5 | 68 | 68 | +0.0% | 5 | 0 |
| user_turns(all) vs stat_user_messages | opencode | 5 | 7 | 7 | +0.0% | 5 | 0 |

`exact` = sessions where the two numbers are identical. `meta=0` = sessions where
the metadata field is 0 (excluded from the median).

## Known gaps

1. **`stat_assistant_messages` is not the API-call count.** It counts *visible
   assistant replies* (turns that ended with text), not API responses. One CC
   session in the sample has 64 distinct `message.id` values and
   `stat_assistant_messages = 1`. The right metadata field is
   `checkpoint_token_usage.api_call_count`, against which the ledger is exact on
   opencode (5/5) and codex (median 0.0%) and +1.7% median on claude_code.
   Residual claude_code overcount: assistant records with a non-`msg_` UUID id
   (locally synthesized messages, `output_tokens = 0`) and API responses the
   checkpointer did not see. `ckpt_api_call_count` is 0 for some sessions, so it
   is not a universal baseline either - hence both tables.

2. **`stat_output_tokens` excludes reasoning tokens for codex.** For codex,
   `sum(output_tokens) - sum(reasoning_tokens)` matches `stat_output_tokens`
   (median +0.3%), while `ckpt_output_tokens` matches `sum(output_tokens)`. For
   claude_code, `stat_output_tokens` matches `sum(output_tokens)` exactly (5/5)
   because thinking tokens are already inside `output_tokens` there. For
   opencode, reasoning is counted on top, so the "output-reasoning" row is
   expected to be far off and should be ignored for that harness.

3. **`stat_user_messages` counts every user record, harness-injected ones
   included.** `count(user_turns)` matches it exactly on 20/20 sample sessions,
   while `count(*) WHERE NOT is_meta` is ~40% lower for claude_code. Use
   `is_meta` to get the human-authored subset; do not expect it to reproduce the
   metadata number. `is_meta` is set from the harness flag (`isMeta` on CC) and,
   for every harness, additionally when the text is entirely harness tags
   (`human_chars = 0`) - slash-command echoes, `<local-command-stdout>`, skill
   expansions, `<environment_context>` blocks.

4. **`stat_tool_calls` undercounts opencode (+18% median) and some CC sessions.**
   The ledger count equals the number of tool records actually present in the
   file (verified by hand with `jq` on the worst offenders: 12 vs 9, 31 vs 18).
   The metadata figure appears to dedupe or to count only part of the tree. The
   ledger number is the one backed by the raw data. `stat_tool_calls` is 0 for
   3/5 cursor sessions, which is why cursor shows 5 exact but 3 `meta=0`.

5. **Cursor has no usage or timing data at all.** All token columns, `calls.ts`,
   and all `tool_calls` result/latency columns are NULL for cursor. Any
   token-based analysis must exclude it.

6. **Tool results are not linked for cursor** (the format has no `tool_result`
   block), so `result_chars`, `result_hash`, `is_error`, `is_interrupted`,
   `result_ts` and `result_latency_ms` are NULL for all 675 cursor tool calls.

7. **`n_thinking_blocks` for codex/opencode is 0 or 1**, not a true block count:
   those formats emit reasoning as a per-response blob, so the column is set to 1
   whenever `n_thinking_chars > 0`.

8. **`repo` comes from the catalog, not from the transcript**, so it is NULL for
   sessions the catalog has no `source.repository` for.

9. **Non-target harnesses are skipped, not parsed**: 383 sessions across
   `Copilot CLI` (110), `null` (79), `Gemini CLI` (77), `Pi` (72), `Agent` (31),
   `Kiro` (5), `Roger Roger Agent` (4), `Factory AI Droid` (3), `Baulog` (1),
   `Vogon Agent` (1). They are still present in the `sessions` table with
   `agent IS NULL`. Note that 30 of the `Agent` ones are Claude Code transcripts
   by `detected_format`; widening the `agent` normalization would pick them up.

10. **`speed` is stored as a string.** Claude Code writes it as a token, and
    other harnesses do not write it at all.

## Resolved spec ambiguities

| ambiguity | resolution |
|---|---|
| `session_id` used as the file key | transcript basename (unique) is `session_id`; catalog value kept as `session_id_meta` |
| which parser to run when `agent` and `detected_format` disagree | parser from `detected_format` when known, `agent` column still from `agent` per spec |
| "one API response split across assistant lines ... same usage repeated" | usage is **not** repeated; merge takes the max per field, last non-null `stop_reason` |
| codex "one calls row per token_count" | only `token_count` events with non-null `info.last_token_usage`; rate-limit heartbeats become events; sessions with no `token_count` at all fall back to one row per assistant message |
| codex apply_patch "inside shell_command" | it is a `custom_tool_call`; both paths implemented |
| codex user-turn dedupe "by text within the same second" | exact-text multiset dedupe across the whole session (echo latency exceeds one second) |
| opencode "whole-file JSON object" | three shapes exist; whole-file, JSONL-per-message, and one foreign schema which is logged as an event |
| `human_chars` "harness tags stripped" | a fixed list of ~30 harness tag names is stripped; when `<user_query>` is present (cursor) only its contents count |
| `errors.jsonl` with multiprocessing | each worker appends to `<out>/errors/part-<pid>.jsonl`; the main process concatenates into `<out>/errors.jsonl` and removes the directory |
| `is_meta` for harnesses without an `isMeta` field | derived: `human_chars == 0 and chars > 0` |

## Files

- `analysis/build_ledger.py` - the extractor
- `analysis/validate.py` - the metadata comparison
- `analysis/sample_sessions.txt` - the 20 session ids used above
- `analysis/ledger_sample/` - the sample output (3.2 MB)
