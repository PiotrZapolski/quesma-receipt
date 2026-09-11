# Layers 2 and 3: the LLM passes

Two runnables plus the plumbing they share.

| file | what |
|---|---|
| `client.py` | provider abstraction, pricing, per-item cache, thread pool, dry-run reporting |
| `classify_prompts.py` | layer 2: classify every human prompt in the ledger |
| `judge.py` | layer 3: LLM judge over raw transcript slices for the layer 1 case files |

Everything reads `analysis/ledger/` (Parquet) and, for layer 3, the raw transcripts in
`data/transcripts/`. Nothing here writes outside `analysis/results/llm/`.

## Running

```bash
UV="uv run --with duckdb --with pyarrow --with orjson --with openai --with anthropic"

# layer 2, no API key needed, no network
$UV analysis/llm/classify_prompts.py --dry-run                 # all 87,887 prompts
$UV analysis/llm/classify_prompts.py --dry-run --limit 50 --print-sample 1

# layer 2, real
export DEEPSEEK_API_KEY=...
$UV analysis/llm/classify_prompts.py --provider deepseek --concurrency 16

# layer 3, no API key needed
$UV analysis/llm/judge.py --synthetic-cases 5 --dry-run --print-sample 1
$UV analysis/llm/judge.py --synthetic-cases 5 --dry-run --synth-agent opencode
$UV analysis/llm/judge.py --cases analysis/results/cases/C01_rewrite_necessary.csv --dry-run

# layer 3, real
export DEEPSEEK_API_KEY=...
$UV analysis/llm/judge.py --cases analysis/results/cases/C01_rewrite_necessary.csv
```

Python 3.9 syntax. No background processes, no servers, no other installs.
**Never run without `--dry-run` first**; the dry run prints the USD.

## Env vars

| var | used by |
|---|---|
| `DEEPSEEK_API_KEY` | `--provider deepseek` (default) |
| `ANTHROPIC_API_KEY` | `--provider anthropic` |

No key is read or needed in `--dry-run`; a dry run selects the items, assembles the
context, renders the full payloads and prices them, then exits. `--print-sample N`
prints N complete request payloads (system prompt, user prompt, tool schema, all
parameters) with the long strings shown verbatim instead of escaped, so a human can
read them before any money is spent. A real run needs nothing but the env var.

## Providers

| provider | package | base url | classify model | judge model | JSON mechanism |
|---|---|---|---|---|---|
| `deepseek` | `openai` | `https://api.deepseek.com` | `deepseek-v4-flash` | `deepseek-v4-pro` | `response_format={"type":"json_object"}`, schema pasted into the system prompt, `thinking` disabled |
| `anthropic` | `anthropic` | first party | `claude-haiku-4-5` | `claude-sonnet-5` | one tool, `strict: true`, `input_schema` with `additionalProperties: false`, `tool_choice: {"type":"auto"}` plus a system-prompt instruction to always call it |

The Anthropic path uses no assistant prefill and passes neither `thinking` nor
`budget_tokens`. `--model` overrides the model, `--provider` the provider.

### DeepSeek thinking mode

DeepSeek V4 **thinks by default**. The API takes `thinking: {"type": "enabled" |
"disabled"}` (default `enabled`, see api-docs.deepseek.com "Thinking Mode"), and with
the `openai` package that parameter has to travel inside `extra_body`. The chain of
thought comes back in `reasoning_content`, is billed, and counts against
`max_tokens`; when the budget runs out inside the reasoning, `content` comes back
**empty** and the JSON parse fails with `response was not valid JSON: ''`. That is
exactly what happened to `tool_result_used` cases at `--max-tokens 1000`.

Both layers ask for one small JSON object, so both send

```python
extra_body={"thinking": {"type": "disabled"}}
```

`--thinking` turns it back on for a run (and then wants a much larger
`--max-tokens`). Anthropic ignores the flag; nothing is sent on that path.

Empty content is now its own retryable failure (`client.EmptyResponseError`). The
runner logs `finish_reason`, whether `reasoning_content` was present and how long it
was, `max_tokens` and `completion_tokens`, then retries the request with thinking
forced off and the token budget doubled. `judge.py --max-tokens` defaults to **4000**
so a judgement of about 160 tokens has a wide margin.

Prices (USD per 1M tokens), in `client.PRICES`:

| model | input | output |
|---|---:|---:|
| deepseek-v4-flash | 0.14 | 0.28 |
| deepseek-v4-pro | 0.435 | 0.87 |
| claude-haiku-4-5 | 1.00 | 5.00 |
| claude-sonnet-5 | 2.00 | 10.00 |

Every estimate uses the flat rule **4 chars = 1 token**, applied to the serialized
request payload, so the tool schema and the JSON envelope are counted too. Real
billing comes back in `usage` and is what lands in the output tables.

## Cache and resume

```
analysis/results/llm/cache/<task>/<2-char shard>/<request id>.json
  tasks: classify_prompts, judge__rewrite_necessary, judge__tool_result_used,
         judge__hot_file_cause
  file:  {"id", "provider", "model", "usage", "result", "ts"}
```

The request id is `sha1("v1|" + the rendered user prompt)[:24]`, so the cache is
content addressed: change the prompt or the context and the id changes; rerun the same
work and every item is a free hit. A cached entry is only reused when its `model`
matches the run's model. `--no-cache` disables it.

Failures retry with exponential backoff and jitter (`--retries`, default 4) on rate
limits, timeouts, 5xx, malformed JSON, empty content and "answered without calling
the tool". A request that exhausts its retries is reported and skipped; the run
continues.

**Only a real answer is ever cached.** Every failure path raises before
`cache.put`, so a request that came back empty leaves no cache file and the next
run retries it instead of replaying the failure.

## Type coercion

A model can always answer with the wrong JSON type for a field, and pyarrow only
finds out when the table is built, at the very end of a run, after every call has
been paid for (`ArrowTypeError: Expected bytes, got a 'bool' object`). So every
value that reaches a table goes through `client.Coercer` first:

| declared type | rule |
|---|---|
| string | `str(x)` when not None, `True`/`False` become `"true"`/`"false"` |
| enum (`label`, `sentiment`, `fraction_of_result_needed`, `cause`) | must be one of the allowed values, else the fallback (`meta_other`, `neutral`, `none`, `unclear`), counted as invalid |
| `language` | lowercase two letter ISO 639-1 (`en-US` becomes `en`), else `"unknown"` |
| bool | true only for `True` itself or a string in `true`, `yes`, `1` |
| int | `int(x)` when it can be read as one, else `None` |

`coerced` counts values that had the wrong type or spelling but carried a usable
value, `invalid` counts values that had to be replaced by a fallback. Both are
logged per field at the end of the run and written into the summary markdown
(`PROMPT_LABELS.md`, `JUDGE_<case_type>.md`) with the first bad value seen.

## Layer 2: `classify_prompts.py`

**Items.** `user_turns` with `is_meta = false` and `human_chars > 0`. **87,887 items**
over 9,770 sessions (claude_code 67,737, codex 15,748, opencode 2,970, cursor 1,432).

**Context per item**, assembled in DuckDB in one pass:

- the previous assistant `text_head` (300 chars) from `calls`, via an ASOF join on
  `seq`;
- the last 5 `tool_calls.tool_name` values before the turn, via a window over the
  union of tool calls and turns;
- the prompt itself: `user_turns.text` with the harness tag blocks stripped (the same
  ~30 tag names `build_ledger.human_text` uses, but newlines kept), cut to 1500 chars.

**Batching.** 15 items per request (`--batch-size`), 5,860 requests for the full
population. The model returns `{"items": [ ... ]}` with one record per item; a JSON
object rather than a bare array because both providers want an object at the top
level.

**Per item the model returns**

| field | type |
|---|---|
| `label` | `new_task`, `follow_up`, `approval`, `correction`, `failure_report`, `interruption`, `question`, `meta_other` |
| `pushback` | bool: correction, failure report, or explicit dissatisfaction |
| `sentiment` | `neutral`, `frustrated`, `positive` |
| `language` | ISO 639-1 |
| `mentions_file` | bool |

**Output**

```
analysis/results/llm/prompt_labels.parquet
  session_id, agent, repo, seq, label, pushback, sentiment, language,
  mentions_file, model, cost_usd     (cost_usd = the batch cost split per item)
analysis/results/llm/PROMPT_LABELS.md
  label distribution by agent, pushback rate by agent, sentiment, top languages
```

**Measured dry run, full population** (`--dry-run`, no limit):

```
requests    5,860 batches of 15
est input   20,579,670 tokens
est output   3,632,680 tokens (620 per batch)
```

| provider / model | estimated cost |
|---|---:|
| deepseek-v4-flash (default) | **3.90 USD** |
| claude-haiku-4-5 | **38.74 USD** |
| deepseek-v4-pro | 12.11 USD |
| claude-sonnet-5 | 77.49 USD |

## Layer 3: `judge.py`

**Cases.** `--cases FILE` reads a layer 1 case CSV (`analysis/results/cases/*.csv`)
with columns `session_id, seq, k_before, k_after` plus optional `stratum`,
`population_n`, and any number of extra columns, which are passed to the model as
"known facts from the ledger". The case type comes from the file name
(`C01_rewrite_necessary.csv` -> `rewrite_necessary`) or from `--case-type`.

`--synthetic-cases N` skips the CSVs entirely and takes cases straight from the
ledger, so the slice extraction and rendering can be tested before layer 1 has run:
N random `tool_kind = 'write'` calls with `content_chars > 200` as `rewrite_necessary`
cases, and N random calls with `result_chars > 5000` as `tool_result_used` cases. The
sample is a seeded deterministic hash order (`--seed`). `--synth-agent claude_code |
codex | opencode | cursor` restricts it to one harness, which is how each format's
renderer gets exercised.

**Raw slice.** `seq` is the 0-based record index inside the transcript file: the line
index for claude_code, codex and cursor, the message index for opencode (whose file is
one JSON document; the loader handles all three opencode on-disk shapes). The file
path comes from `sessions.trajectory` (prefix with `--data-root`, default `.`); the
parser is chosen from `sessions.detected_format` and falls back to `sessions.agent`,
exactly as `build_ledger` does. Records `[seq - k_before, seq + k_after]` are read;
for opencode `k` is divided by 4 first, because one opencode record holds every part
of a whole step.

**Compaction**, uniform across the four formats:

| kept | dropped |
|---|---|
| user text, assistant text (cut to 3000 chars) | thinking / reasoning and their signatures |
| tool names and args (cut to 1500 chars) | attachments, file-history-snapshot, progress, step-start / step-finish, token_count, exec_command_* heartbeats |
| tool results, head 2000 chars + tail 500 chars, with the omitted count | codex's duplicate `response_item` echo of a user or agent message |
| `system` records, first 300 chars | everything else |

Rendered as `[seq] USER: / ASSISTANT: / TOOL_USE <name>: / TOOL_RESULT (ok|ERROR, N
chars): / SYSTEM <subtype>:`, with `<<< CASE FOCUS` on the focus record. The whole
slice is capped at `--max-transcript-chars` (default 60,000).

Per-format notes: cursor has no `tool_result` blocks in the format at all, so cursor
cases carry tool calls but never results (and `tool_result_used` produces zero cursor
cases, by construction). Codex `apply_patch` is a `custom_tool_call` whose input is the
raw patch text. OpenCode tool inputs are occasionally a JSON string rather than an
object and are parsed when they are.

**Rubrics** (one tool / one JSON object each)

| case type | fields | rate reported in the summary |
|---|---|---|
| `rewrite_necessary` | `was_full_rewrite_needed` (bool), `estimated_lines_actually_changed` (int), `reason` (<= 30 words) | unnecessary full rewrites (`was_full_rewrite_needed == false`) |
| `tool_result_used` | `was_result_referenced_later` (bool), `fraction_of_result_needed` (`none`, `small`, `most`, `all`), `reason` | results never referenced again |
| `hot_file_cause` | `cause` (`architecture_hub`, `agent_regression`, `user_iteration`, `config_churn`, `test_file`, `unclear`), `reason` | edits caused by agent regression |

**Output**

```
analysis/results/llm/judge_<case_type>.parquet
  session_id, seq, case_type, stratum, <rubric fields>, model, cost_usd
analysis/results/llm/JUDGE_<case_type>.md
  rate by stratum with a 95% Wilson interval, and the extrapolation to the
  population (stratum rate x the `population_n` column of the case CSV; `n/a`
  when the case file did not carry one)
```

**Measured dry runs** (`--synthetic-cases 5`, three seeds, 15 cases per case type;
`hot_file_cause` from a 4-row test CSV):

| case type | est input tokens per case | est output tokens per case |
|---|---:|---:|
| rewrite_necessary | 2,672 | 160 |
| tool_result_used | 3,336 | 160 |
| hot_file_cause | 2,400 | 160 |

At the case counts the layer 1 generators are specified for (C01 600, C02 600,
C03 200):

| case type | cases | deepseek-v4-pro | claude-sonnet-5 |
|---|---:|---:|---:|
| rewrite_necessary | 600 | 0.78 USD | 4.17 USD |
| tool_result_used | 600 | 0.95 USD | 4.96 USD |
| hot_file_cause | 200 | 0.24 USD | 1.28 USD |
| **all three** | 1,400 | **1.97 USD** | **10.41 USD** |

## CLI reference (both scripts)

```
--provider deepseek|anthropic   --model MODEL
--ledger DIR (analysis/ledger)  --results DIR (analysis/results)
--concurrency N (8)             --retries N (4)      --timeout S (120)
--limit N                       --dry-run            --print-sample N
--no-cache                      --seed N (20260705)
--thinking                      (deepseek only: leave thinking mode on)
```

`classify_prompts.py` adds `--batch-size` (15) and `--max-tokens` (2000).
`judge.py` adds `--cases FILE`, `--case-type`, `--synthetic-cases N`,
`--synth-agent`, `--data-root`, `--max-transcript-chars` (60000) and
`--max-tokens` (4000).
