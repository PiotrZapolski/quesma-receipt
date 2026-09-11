# build_ledger: flatten SWE-chat transcripts into a per-API-call ledger (Parquet)

## Goal
Turn 9770 raw agent transcripts (17.8 GB JSONL, 4 harness formats) into flat Parquet tables
queryable with DuckDB. One row per API call, one row per tool call, one row per human prompt,
one row per meta event. Nothing is analysed here; this is the extraction layer only.

## Hard constraints
- Python 3.9 (system). Run via `uv run --with duckdb --with orjson --with pyarrow analysis/build_ledger.py ...`.
  No other installs. No venv creation. No background processes.
- NEVER run on the full dataset during development. Use `--limit` / `--sessions` with at most
  ~20 sessions total for testing. The full run is done by the user separately.
- Stream JSONL line by line (files go up to 133 MB). OpenCode files are ONE pretty-printed JSON
  object spread over many lines (keys: info, messages) - load those whole.
- Never crash the whole run on a bad line/session: count the error, log to `errors.jsonl`
  (session_id, line_no, exception), continue.
- Paths: dataset root = `/Users/zapol/Projects/swe-chat-enhanced-2026-07-05-full`.
  Transcripts: `data/transcripts/<session_id>.jsonl`. Catalog: `metadata/sessions.json`
  (`.sessions[]` has session_id, agent, source.repository, bytes, statistics, checkpoint_token_usage,
  initial_attribution, files_touched, created_at, models, agent_versions, detected_format).
- Output layout: `<out>/<table>/part-<worker>-<n>.parquet` so DuckDB reads `<out>/<table>/*.parquet`.
  Default out: `analysis/ledger`. Tests must write to `analysis/ledger_sample`.
- CLI: `--out DIR`, `--limit N`, `--sessions FILE` (one session_id per line), `--agents a,b`
  (default all four), `--workers N` (default 6, multiprocessing over sessions, largest files first).
- Every table carries: session_id, agent (normalized), repo, seq (0-based order of the source
  record within the file, so rows can be re-ordered and joined back to the raw line).

## Agent normalization (from metadata `agent` field)
"Claude Code","claude-code" -> claude_code | "Codex","Codex CLI" -> codex |
"OpenCode","Opencode","opencode" -> opencode | "Cursor" -> cursor | anything else -> skip (count it).

## Formats (verified by inspection; re-verify on 2-3 sessions each with jq before coding)

### claude_code (one JSON per line)
Line `type` values seen: assistant, user, attachment, file-history-snapshot, last-prompt,
permission-mode, queue-operation, system, progress, ai-title. Common fields: uuid, parentUuid,
timestamp (ISO ms), sessionId, isSidechain, cwd, gitBranch, version, requestId, isMeta.
- assistant: `.message` = {id, model, role, content[], stop_reason, usage{input_tokens,
  cache_creation_input_tokens, cache_read_input_tokens, output_tokens, cache_creation{
  ephemeral_5m_input_tokens, ephemeral_1h_input_tokens}, service_tier, speed, iterations[]}}.
  content block types: text{text}, thinking{thinking, signature}, tool_use{id, name, input}.
  IMPORTANT: one API response is often split across several consecutive assistant lines that
  share the same `.message.id` (one content block per line, same usage repeated). Merge them
  into ONE `calls` row; count usage once.
- user: `.message.content` is either a string (human prompt) or an array. Array may contain
  tool_result{tool_use_id, content (string or [{type:text,text}]), is_error} and/or text blocks.
  `toolUseResult` duplicates the tool result at top level (ignore it, use message content).
  Human prompts: content string or text blocks with no tool_result. Text may contain harness
  injections: `<system-reminder>...</system-reminder>`, `<command-name>`, `<local-command-stdout>`,
  `[Request interrupted by user...]`. Keep full text; also compute the human-only char count
  with those tags stripped. `isMeta: true` lines are harness-generated - flag them.
- system: has `.subtype` (record it; look for compaction markers), `.content`, `.level`.
- permission-mode: record the mode value. queue-operation: record `.operation`.
- attachment: record `.attachment.type` and char size. file-history-snapshot: record count of
  `.snapshot.trackedFileBackups` keys. progress / last-prompt / ai-title: type + char size only.

### codex (one JSON per line; `type` in session_meta, turn_context, response_item, event_msg)
- session_meta.payload: id, timestamp, cwd, originator, cli_version, model_provider,
  base_instructions.text (record char count only).
- turn_context.payload: turn_id, cwd, current_date, timezone, approval_policy, sandbox_policy.type,
  model, collaboration_mode.settings.reasoning_effort. -> events rows, and model/timezone carried
  to subsequent calls rows until next turn_context.
- response_item.payload.type: message{role: user|assistant|developer, content[{type:
  input_text|output_text, text}]}, reasoning{summary[], ...}, function_call{name, arguments (JSON
  string), call_id}, function_call_output{call_id, output}, possibly custom_tool_call /
  local_shell_call / web_search_call - inspect and handle generically (name + args + output).
- event_msg.payload.type: token_count{info{last_token_usage{input_tokens, cached_input_tokens,
  output_tokens, reasoning_output_tokens, total_tokens}, total_token_usage, model_context_window}},
  user_message{message}, agent_message{message}, agent_reasoning, task_started, exec_command_end,
  mcp_tool_call_end, ghost_snapshot, etc.
- calls row: one per token_count event (that is one API response). Attach the response_items
  seen since the previous token_count: n_text_chars (assistant message text), n_reasoning,
  n_tool_uses. cached_input_tokens -> cache_read_tokens; reasoning_output_tokens ->
  reasoning_tokens. stop_reason: "tool_use" if any function_call in that span else "end_turn".
- tool_calls: function_call + matching function_call_output by call_id. For name ==
  "shell_command"/"shell"/"exec_command": args.command (string or list) -> command_head. Detect
  `apply_patch` in the command: extract file paths from lines `*** Update File: X`,
  `*** Add File: X`, `*** Delete File: X` -> file_path = first, patched_files = JSON list,
  tool_kind = edit (or write for Add File only). `update_plan` -> tool_kind todo. `mcp__*` -> mcp.
- user_turns: event_msg user_message (human). Also response_item message role=user is the same
  prompt echoed - dedupe by text within the same second; prefer the event_msg.

### opencode (whole-file JSON: {info:{id, directory, version, title, model{id, providerID},
  tokens, cost, summary}, messages:[{info, parts[]}]})
- message.info: id, role (user|assistant), parentID, agent, mode, modelID, providerID, cost,
  tokens{input, output, reasoning, cache{read, write}}, time{created, completed} (epoch ms),
  finish, path{cwd, root}.
- parts[].type: text{text}, reasoning{text}, tool{tool, callID, state{status, input, output,
  time{start,end}, title, error?}}, step-start{snapshot}, step-finish{tokens, cost, reason, snapshot},
  file, patch, etc. Note: an assistant message may span multiple step-start/step-finish pairs -
  each step-finish with tokens is one API call. If step-finish rows exist use them as `calls`
  (tokens from the step), else fall back to one row per assistant message (info.tokens).
- tool_calls: parts type tool. tool names lowercase: read, edit, write, bash, glob, grep, list,
  webfetch, task, todowrite, etc. Input keys: filePath, command, pattern, content, oldString,
  newString. status "error" -> is_error.
- user_turns: role user messages, text parts.

### cursor (one JSON per line: {role, message:{content:[...]}} ONLY; no timestamps, no usage)
- Inspect 3 sessions to learn the content block types (text, tool_use/tool_result variants).
- calls: one row per assistant line, tokens NULL, ts NULL. tool_calls as far as blocks allow.
- user_turns: role user. The first user text often starts with harness-injected
  `<manually_attached_skills>` or similar tags - keep, and strip for human char count.

## Tables (Parquet). NULL where a harness has no such field.

### calls  (one row per model API response)
session_id, agent, repo, seq, ts TIMESTAMP, msg_id, request_id, parent_id, is_sidechain BOOL,
model, harness_version, stop_reason, speed, service_tier,
input_tokens, cache_read_tokens, cache_create_tokens, cache_create_5m, cache_create_1h,
output_tokens, reasoning_tokens, context_window,
n_text_chars, n_thinking_chars, n_thinking_blocks, n_tool_uses, text_head (first 300 chars),
cwd, git_branch, timezone (codex only)

### tool_calls  (one row per tool invocation)
session_id, agent, repo, seq, msg_id, ts, tool_use_id, tool_name (raw), tool_kind (normalized:
read|edit|write|bash|glob|grep|web|task|todo|mcp|other), file_path_raw, file_path (made relative
to cwd/root when it is under it, else unchanged), patched_files (JSON string or NULL),
command_head (first 500 chars), input_chars, old_string_chars, new_string_chars, content_chars,
read_offset, read_limit, result_chars, result_hash (sha1 hex of result text), is_error BOOL,
error_head (first 200 chars when is_error), result_ts, result_latency_ms, is_interrupted BOOL

### user_turns  (human-authored prompts)
session_id, agent, repo, seq, ts, prompt_id, text (full), chars, human_chars (harness tags
stripped), is_meta BOOL, is_interrupt BOOL, is_slash_command BOOL, has_system_reminder BOOL

### events  (everything that is not a model call, tool call, or human prompt)
session_id, agent, repo, seq, ts, event_type, subtype, value (short string), payload_chars

### sessions  (flattened metadata/sessions.json, written once by the main process via DuckDB
read_json). Keep: session_id, agent (normalized), agent_raw, repo, created_at, branch, strategy,
bytes, models (JSON), agent_versions (JSON), files_touched (JSON), n_files_touched, and every
scalar under statistics.*, checkpoint_token_usage.*, initial_attribution.* prefixed
stat_/ckpt_/attr_.

## validate.py
`uv run --with duckdb analysis/validate.py --ledger DIR` : for every session present in the ledger,
compare against metadata: count(tool_calls) vs stat_tool_calls, count(calls) vs
stat_assistant_messages, sum(output_tokens) vs stat_output_tokens, count(user_turns where not
is_meta) vs stat_user_messages. Print a per-agent table with median relative delta and the worst
5 sessions per metric. Exact match is not expected (metadata counted differently); the goal is
to see that we are in the right ballpark and to explain systematic gaps in README.md.

## Deliverables
analysis/build_ledger.py, analysis/validate.py, analysis/README.md (schema, how counts map per
harness, known gaps). Run the sample (5 sessions per harness, `--out analysis/ledger_sample`)
and validate.py; paste the validation table into README.md.
