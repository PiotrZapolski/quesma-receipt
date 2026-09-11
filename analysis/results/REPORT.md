# Layer 1 report

Generated 2026-09-11 20:47:24

- ledger: `/Users/zapol/Projects/swe-chat-enhanced-2026-07-05-full/analysis/ledger`
- prices: `/Users/zapol/Projects/swe-chat-enhanced-2026-07-05-full/analysis/prices.csv`
- setup: 6.3s, total runtime: 10.0s
- files run: 27, failed: 0

## T01 baseline: what the whole population costs  (`T01_baseline`)

**Headline**

- **total_usd**: 116676.7
- **usd_claude_code**: 96741.1
- **usd_codex**: 19048.4
- **usd_opencode**: 887.1856
- **pct_usd_cache_read**: 63.8482
- **pct_usd_cache_write**: 22.3326
- **pct_usd_output**: 9.2308
- **pct_usd_fresh_input**: 4.5884
- **pct_calls_unpriced**: 2.8985
- **usd_per_committed_line_all**: 0.0064

### by_agent  (4 rows)

| agent | sessions | calls | usd | pct_of_total_usd | input_tokens | cache_read_tokens | cache_write_tokens | output_tokens | ctx_tokens |
|---|---|---|---|---|---|---|---|---|---|
| claude_code | 7230 | 677725 | 96741.1 | 82.9138 | 119905333 | 123228962728 | 2697907771 | 351597181 | 126048591306 |
| codex | 1167 | 218945 | 19048.4 | 16.3258 | 29444027637 | 28165371264 | 0 | 73871238 | 29445241333 |
| opencode | 783 | 27949 | 887.1856 | 0.7604 | 237032931 | 2416143822 | 18555414 | 10336743 | 1149408071 |
| cursor | 86 | 8910 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0 | 0 |

### by_model  (56 rows)

| model | provider | calls | sessions | usd | input_usd | cache_read_usd | cache_write_usd | output_usd |
|---|---|---|---|---|---|---|---|---|
| claude-opus-4-6 | anthropic | 337485 | 4123 | 37313.6 | 21.8339 | 24373.8 | 10332.0 | 2586.0 |
| claude-opus-4-7 | anthropic | 149438 | 1290 | 29285.2 | 9.9834 | 19550.4 | 6988.4 | 2736.4 |
| claude-opus-4-8 | anthropic | 93434 | 647 | 21444.3 | 106.8731 | 12901.6 | 5789.2 | 2646.6 |
| gpt-5.5 | openai | 163983 | 599 | 15696.9 | 3507.1 | 10676.4 | 0.0000 | 1513.4 |
| claude-fable-5 | anthropic | 12166 | 88 | 4739.4 | 33.5299 | 2767.8 | 1440.1 | 498.0516 |
| gpt-5.4 | openai | 49726 | 575 | 3218.1 | 1344.1 | 1554.4 | 0.0000 | 319.5956 |
| claude-sonnet-4-6 | anthropic | 40435 | 657 | 1939.2 | 2.6784 | 987.9792 | 679.5739 | 268.9930 |
| claude-opus-4-5-20251101 | anthropic | 17950 | 208 | 1421.8 | 2.4642 | 848.8909 | 536.0674 | 34.4015 |
| gpt-5.3-codex | openai | 22146 | 565 | 774.9785 | 305.8650 | 354.1458 | 0.0000 | 114.9677 |
| claude-sonnet-4-5-20250929 | anthropic | 12962 | 132 | 582.3012 | 0.7332 | 343.8157 | 212.1664 | 25.5858 |
| claude-sonnet-5 | anthropic | 1761 | 7 | 144.7806 | 0.5758 | 94.7031 | 38.7299 | 10.7718 |
| claude-haiku-4-5-20251001 | anthropic | 2490 | 141 | 55.5637 | 0.0481 | 19.1380 | 34.4203 | 1.9572 |
| claude-sonnet-4.6 | anthropic | 629 | 24 | 21.5459 | 3.9828 | 7.4402 | 4.1021 | 6.0209 |
| gpt-5.4-mini | openai | 1000 | 50 | 13.0908 | 4.4617 | 5.6977 | 0.0000 | 2.9314 |
| anthropic/claude-opus-4.6 | anthropic | 94 | 5 | 6.9751 | 4.1909 | 2.1603 | 0.0000 | 0.6239 |
| claude-opus-4.6 | anthropic | 77 | 3 | 5.9209 | 3.0505 | 1.8225 | 0.0000 | 1.0479 |
| claude-haiku-4.5 | anthropic | 329 | 3 | 4.8482 | 0.0062 | 1.5661 | 2.2601 | 1.0158 |
| gpt-5.3-codex-spark | openai | 232 | 6 | 4.6785 | 1.2472 | 2.2032 | 0.0000 | 1.2281 |
| gpt-5.5-fast | openai | 110 | 3 | 3.0194 | 0.6151 | 1.9277 | 0.0000 | 0.4767 |
| claude-sonnet-4.5 | anthropic | 10 | 1 | 0.2675 | 0.1445 | 0.0674 | 0.0000 | 0.0556 |
| anthropic/claude-sonnet-4.6 | anthropic | 13 | 1 | 0.1861 | 0.1220 | 0.0394 | 0.0000 | 0.0246 |
| gemini-2.5-flash |  | 4 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| qwen3.6-plus |  | 1456 | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gpt-5-mini |  | 5 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gpt-5.1-codex-mini |  | 27 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| glm-5.2 |  | 37 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ling-2.6-flash-free |  | 7 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| big-pickle |  | 3525 | 42 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| glm-4.7 |  | 327 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gemini-3.1-pro |  | 1 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| glm-5.1 |  | 419 | 17 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| qwen3.5 |  | 6 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| benchmark-feedback |  | 24 | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| google/gemini-3.1-pro-preview |  | 305 | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gemini-3.1-pro-preview |  | 598 | 27 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| minimax-m2.5-free |  | 30 | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| z-ai/glm-5.1 |  | 26 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| mimo-v2.5-free |  | 1008 | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| nemotron-3-super-free |  | 217 | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gemini-3.1-pro-high |  | 40 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

_56 rows total, 40 shown._

### components_by_agent  (5 rows)

| agent | usd | input_usd | cache_read_usd | cache_write_usd | output_usd | pct_input | pct_cache_read | pct_cache_write | pct_output |
|---|---|---|---|---|---|---|---|---|---|
| ALL | 116676.7 | 5353.6 | 74496.0 | 26056.9 | 10770.2 | 4.5884 | 63.8482 | 22.3326 | 9.2308 |
| claude_code | 96741.1 | 178.7154 | 61755.7 | 26014.1 | 8792.6 | 0.1847 | 63.8360 | 26.8904 | 9.0888 |
| codex | 19048.4 | 4899.4 | 12295.4 | 0.0000 | 1853.7 | 25.7206 | 64.5480 | 0.0000 | 9.7313 |
| opencode | 887.1856 | 275.5126 | 444.9290 | 42.8600 | 123.8840 | 31.0547 | 50.1506 | 4.8310 | 13.9637 |
| cursor | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |  |  |  |

### usd_per_session  (4 rows)

| agent | sessions | mean_usd | p50_usd | p90_usd | p99_usd | max_usd |
|---|---|---|---|---|---|---|
| claude_code | 7230 | 13.3805 | 2.8447 | 27.1136 | 207.6799 | 1677.6 |
| codex | 1167 | 16.3226 | 2.2981 | 37.6021 | 197.3303 | 1069.8 |
| opencode | 783 | 1.1331 | 0.2384 | 0.8552 | 20.6308 | 182.0172 |
| cursor | 86 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### per_committed_line_by_mode  (4 rows)

| mode | sessions | usd | committed_lines | usd_per_committed_line | ctx_tokens_per_committed_line | output_tokens_per_committed_line |
|---|---|---|---|---|---|---|
| human | 2574 | 37041.1 | 12959502 | 0.0029 | 3830.1 | 9.6851 |
| vibe | 4072 | 34809.3 | 1799204 | 0.0193 | 26099.0 | 80.4847 |
| unknown | 602 | 23054.2 |  |  |  |  |
| collab | 2018 | 21772.1 | 3296891 | 0.0066 | 8753.7 | 26.2524 |

### per_committed_line_by_agent_mode  (16 rows)

| agent | mode | sessions | usd | committed_lines | usd_per_committed_line |
|---|---|---|---|---|---|
| claude_code | human | 2166 | 33452.0 | 11852981 | 0.0028 |
| claude_code | vibe | 2994 | 26409.7 | 865872 | 0.0305 |
| claude_code | collab | 1557 | 18771.6 | 2245224 | 0.0084 |
| claude_code | unknown | 513 | 18107.8 |  |  |
| codex | vibe | 608 | 7825.8 | 173763 | 0.0450 |
| codex | unknown | 74 | 4940.4 |  |  |
| codex | human | 257 | 3472.6 | 689539 | 0.0050 |
| codex | collab | 228 | 2809.7 | 554609 | 0.0051 |
| opencode | vibe | 438 | 573.7549 | 755976 | 7.590e-04 |
| opencode | collab | 210 | 190.8526 | 490224 | 3.893e-04 |
| opencode | human | 122 | 116.6109 | 168432 | 6.923e-04 |
| opencode | unknown | 13 | 5.9671 |  |  |
| cursor | human | 29 | 0.0000 | 248550 | 0.0000 |
| cursor | vibe | 32 | 0.0000 | 3593 | 0.0000 |
| cursor | unknown | 2 | 0.0000 |  |  |
| cursor | collab | 23 | 0.0000 | 6834 | 0.0000 |

### unpriced_share  (4 rows)

| agent | calls | unpriced_calls | pct_calls_unpriced | all_tokens | unpriced_tokens | pct_tokens_unpriced |
|---|---|---|---|---|---|---|
| claude_code | 677725 | 10282 | 1.5171 | 126400188487 | 360371929 | 0.2851 |
| codex | 218945 | 39 | 0.0178 | 29519112571 | 3036130 | 0.0103 |
| opencode | 27949 | 7827 | 28.0046 | 1159744814 | 623181623 | 53.7344 |
| cursor | 8910 | 8910 | 100.0000 | 0 | 0 |  |

### unpriced_models  (34 rows)

| model | calls | ctx_tokens | output_tokens |
|---|---|---|---|
|  | 13693 | 976402 | 3097 |
| big-pickle | 3525 | 258340154 | 1049896 |
| <synthetic> | 2269 | 0 | 0 |
| glm-5 | 1987 | 168103706 | 546417 |
| qwen3.6-plus | 1456 | 190330456 | 441487 |
| mimo-v2.5-free | 1008 | 87851739 | 316628 |
| gemini-3.1-pro-preview | 598 | 30999814 | 80053 |
| glm-5.1 | 419 | 25866293 | 127192 |
| exact-dodo | 355 | 81608617 | 162400 |
| glm-4.7 | 327 | 41114939 | 82546 |
| deepseek-v4-flash-free | 309 | 23672140 | 109336 |
| google/gemini-3.1-pro-preview | 305 | 11375153 | 23350 |
| nemotron-3-super-free | 217 | 6415405 | 37463 |
| stealth | 152 | 10069856 | 55695 |
| huge-cougar | 87 | 32604375 | 33069 |
| kimi-k2.5 | 58 | 3364207 | 40397 |
| gemini-3.1-pro-high | 40 | 1741107 | 3057 |
| glm-5.2 | 37 | 2279311 | 37637 |
| north-mini-code-free | 33 | 723320 | 4009 |
| minimax-m2.5-free | 30 | 573442 | 10518 |
| gemini-3.5-flash | 28 | 897658 | 3447 |
| gpt-5.1-codex-mini | 27 | 1995873 | 12754 |
| z-ai/glm-5.1 | 26 | 961616 | 9334 |
| benchmark-feedback | 24 | 0 | 0 |
| moonshotai/kimi-k2-instruct | 12 | 158056 | 1153 |
| moonshotai/kimi-k2.6-20260420 | 9 | 634226 | 1417 |
| ling-2.6-flash-free | 7 | 94694 | 377 |
| qwen3.5 | 6 | 311868 | 1383 |
| gpt-5-mini | 5 | 130052 | 6030 |
| gemini-2.5-flash | 4 | 83912 | 225 |
| gpt-5.2-codex | 2 | 62826 | 94 |
| gemini-3.1-pro | 1 | 0 | 0 |
| gpt-5.2 | 1 | 46045 | 1959 |
| gemini-3.1-flash | 1 | 0 | 0 |

_T01_baseline: 0.1s_

## T02 coffee break: the cache expires while the human is away  (`T02_coffee_break`)

**Headline**

- **usd_recached_after_gap_gt_5min**: 10195.2
- **pct_of_all_cache_write_usd**: 39.1265
- **pct_of_total_usd**: 8.7380
- **break_rate_pct_gap_lt_1min**: 0.5924
- **break_rate_pct_gap_gt_60min**: 83.6319
- **recached_tokens_after_gap_gt_5min**: 1071877903

### by_gap_bucket  (4 rows)

| gap_bucket | calls | pct_of_calls | breaks | break_rate_pct | recached_tokens | recached_tokens_on_breaks | cache_write_usd | cache_write_usd_on_breaks | median_gap_min |
|---|---|---|---|---|---|---|---|---|---|
| 1. <1 min | 582011 | 87.4550 | 3448 | 0.5924 | 1086734863 | 302857449 | 10632.4 | 2977.1 | 0.1296 |
| 2. 1-5 min | 59077 | 8.8771 | 1422 | 2.4070 | 382565768 | 207676629 | 3687.4 | 2007.1 | 1.8765 |
| 3. 5-60 min | 20781 | 3.1226 | 1612 | 7.7571 | 343417644 | 283959924 | 2951.2 | 2371.3 | 9.7460 |
| 4. >60 min | 3629 | 0.5453 | 3035 | 83.6319 | 728460259 | 691617987 | 7244.0 | 6852.5 | 206.9331 |

### break_rate_fine_grained  (7 rows)

| gap_bucket | calls | break_rate_pct | cache_write_usd |
|---|---|---|---|
| 1. <15 s | 444303 | 0.5215 | 6267.6 |
| 2. 15-60 s | 137708 | 0.8213 | 4364.7 |
| 3. 1-5 min | 59077 | 2.4070 | 3687.4 |
| 4. 5-20 min | 17013 | 7.2121 | 2166.2 |
| 5. 20-60 min | 3768 | 10.2176 | 784.9536 |
| 6. 1-5 h | 2102 | 84.4434 | 4013.9 |
| 7. >5 h | 1527 | 82.5147 | 3230.1 |

### ttl_era_by_month  (7 rows)

| month | calls | cache_write_5m_tokens | cache_write_1h_tokens | pct_tokens_1h | cache_write_usd | break_rate_pct |
|---|---|---|---|---|---|---|
| 2026-01-01 00:00:00 | 11540 | 42497376 | 3278996 | 7.1631 | 278.5191 | 2.9029 |
| 2026-02-01 00:00:00 | 115494 | 31097268 | 257257993 | 89.2156 | 2569.8 | 1.4841 |
| 2026-03-01 00:00:00 | 172815 | 35236013 | 487259544 | 93.2562 | 4849.1 | 1.3917 |
| 2026-04-01 00:00:00 | 150215 | 88208454 | 481229444 | 84.5096 | 5258.7 | 1.3214 |
| 2026-05-01 00:00:00 | 105420 | 4129969 | 465830520 | 99.1212 | 4615.1 | 1.2626 |
| 2026-06-01 00:00:00 | 95067 | 7995492 | 520791367 | 98.4880 | 5477.5 | 1.5032 |
| 2026-07-01 00:00:00 | 14947 | 21063946 | 93606074 | 81.6308 | 1466.1 | 2.1275 |

### gap_gt_5min_by_month  (7 rows)

| month | calls_after_gap_gt_5min | cache_write_usd_after_gap_gt_5min | pct_of_month_cache_write_usd |
|---|---|---|---|
| 2026-01-01 00:00:00 | 383 | 154.2402 | 55.3787 |
| 2026-02-01 00:00:00 | 3269 | 559.8291 | 21.7847 |
| 2026-03-01 00:00:00 | 6672 | 1864.3 | 38.4468 |
| 2026-04-01 00:00:00 | 5656 | 2534.5 | 48.1962 |
| 2026-05-01 00:00:00 | 3854 | 2154.8 | 46.6893 |
| 2026-06-01 00:00:00 | 3930 | 2290.3 | 41.8136 |
| 2026-07-01 00:00:00 | 646 | 637.1449 | 43.4570 |

_T02_coffee_break: 0.2s_

## T03 zero info: tool results the model has already seen verbatim  (`T03_zero_info`)

**Headline**

- **pct_of_tool_result_chars_exact_repeats**: 2.1411
- **repeated_tool_results**: 170474
- **pct_of_tool_results_repeated**: 16.0573
- **repeated_chars**: 59214228
- **usd_lower_bound_fresh_input**: 67.6401

### by_agent  (3 rows)

| agent | tool_results | repeated_results | pct_results_repeated | result_chars | repeated_chars | pct_chars_repeated |
|---|---|---|---|---|---|---|
| claude_code | 717259 | 143617 | 20.0230 | 1540646460 | 52402104 | 3.4013 |
| codex | 306600 | 20205 | 6.5900 | 1033640996 | 3014301 | 0.2916 |
| opencode | 37803 | 6652 | 17.5965 | 191342786 | 3797823 | 1.9848 |

### by_tool_kind  (25 rows)

| agent | tool_kind | tool_results | repeated_results | pct_results_repeated | repeated_chars | pct_chars_repeated |
|---|---|---|---|---|---|---|
| claude_code | read | 141736 | 4569 | 3.2236 | 29723990 | 3.8012 |
| claude_code | edit | 131514 | 89560 | 68.0992 | 13084760 | 59.7720 |
| claude_code | bash | 283632 | 22223 | 7.8352 | 4270099 | 1.4779 |
| claude_code | mcp | 12384 | 1670 | 13.4851 | 3090854 | 1.1082 |
| opencode | read | 15867 | 561 | 3.5356 | 2371990 | 1.7184 |
| codex | edit | 24569 | 14795 | 60.2182 | 2255599 | 48.7683 |
| claude_code | other | 55390 | 11899 | 21.4822 | 663984 | 4.7751 |
| claude_code | todo | 5330 | 3561 | 66.8105 | 606816 | 10.3864 |
| opencode | bash | 9521 | 1259 | 13.2234 | 529011 | 1.3872 |
| codex | bash | 267922 | 915 | 0.3415 | 327710 | 0.0327 |
| claude_code | write | 20910 | 2174 | 10.3969 | 303224 | 6.1481 |
| codex | mcp | 1194 | 252 | 21.1055 | 286033 | 2.4999 |
| claude_code | glob | 6888 | 1242 | 18.0314 | 261027 | 5.1103 |
| opencode | grep | 3270 | 307 | 9.3884 | 220878 | 2.8997 |
| claude_code | grep | 38784 | 6296 | 16.2335 | 201204 | 0.4868 |
| opencode | edit | 4195 | 3205 | 76.4005 | 183552 | 58.6916 |
| claude_code | task | 17622 | 274 | 1.5549 | 108895 | 0.1193 |
| claude_code | web | 3069 | 149 | 4.8550 | 87251 | 1.3232 |
| opencode | write | 1111 | 699 | 62.9163 | 82870 | 39.3667 |
| codex | other | 5662 | 413 | 7.2942 | 80940 | 0.6456 |
| codex | todo | 3939 | 3464 | 87.9411 | 41810 | 39.2372 |
| codex | task | 2234 | 335 | 14.9955 | 17510 | 0.9671 |
| opencode | glob | 2123 | 548 | 25.8125 | 13282 | 1.0186 |
| codex | write | 1080 | 31 | 2.8704 | 4699 | 2.4345 |
| opencode | todo | 838 | 4 | 0.4773 | 1845 | 0.2960 |

### usd_by_agent  (3 rows)

| agent | repeated_chars | repeated_tokens | usd_lower_bound | usd_if_cached_once |
|---|---|---|---|---|
| claude_code | 52402104 | 13100526.0 | 63.1484 | 6.3148 |
| codex | 3014301 | 753575.2 | 2.9668 | 0.2967 |
| opencode | 3797823 | 949455.8 | 1.5249 | 0.1525 |

### top_repeated_bash_commands  (20 rows)

| command_head_90 | repeated_occurrences | sessions | repeated_chars |
|---|---|---|---|
| scripts="/home/armel/Projects/OSS/bmad-module-skill-forge/.claude/skills/bmad-story-automa | 1023 | 4 | 201399 |
| git status | 166 | 2001 | 60773 |
| git status --short | 152 | 1526 | 33609 |
|  | 147 | 177 | 15435 |
| gcloud storage ls "gs://marin-us-central1/evaluation/harbor/open-thoughts__OpenThoughts-TB | 140 | 7 | 6999 |
| go build ./... 2>&1 \| head -10 | 126 | 38 | 3906 |
| pnpm --filter @dayhaysoos/nimbus-worker test | 101 | 109 | 93200 |
| go build ./... 2>&1 | 96 | 75 | 3048 |
| /usr/local/go/bin/go build -o safecast-new-map ./cmd/unified-server/ 2>&1 | 93 | 13 | 3543 |
| go build ./... 2>&1 \| head -20 | 87 | 57 | 2697 |
| git diff --stat | 87 | 1579 | 57230 |
| mise run lint 2>&1 | 85 | 302 | 5014 |
| uv run scripts/ray/cluster.py --cluster us-east5-a list-jobs 2>&1 \| grep -A8 "REDACTED" \|  | 75 | 1 | 1809 |
| bash -lc ". \"$HOME/.nvm/nvm.sh\" && nvm use >/dev/null && pnpm --filter @dayhaysoos/nimbu | 73 | 1 | 28857 |
| gcloud storage cat gs://marin-us-central1/evaluation/harbor/terminal-bench/nemotron-termin | 71 | 1 | 497 |
| mise run fmt 2>&1 | 59 | 185 | 1224 |
| go build ./... 2>&1 \| head -30 | 59 | 77 | 1912 |
| cargo +nightly-2025-11-30 fmt --all -- --check 2>&1 | 58 | 56 | 1885 |
| go build ./... | 55 | 87 | 1379 |
| mise run fmt | 54 | 200 | 1180 |

### top_repeated_files  (20 rows)

| file_path_90 | tool_kind | repeated_occurrences | sessions | repeated_chars |
|---|---|---|---|---|
| themes/portio/assets/images/writing/hypothesis.jpg | read | 1 | 1 | 645439 |
| public/images/writing/hypothesis_hu_a01b8ffa7e1d0e3f.jpg | read | 1 | 1 | 630963 |
| /Users/jeevanpillay/Desktop/Screenshot 2026-04-18 at 2.34.32 PM.png | read | 2 | 1 | 285060 |
| sample_apps/osvauld-demos/permit_template.json | read | 7 | 8 | 250664 |
| docs/plans/2026-02-06-session-phase-state-machine-v2.md | read | 6 | 5 | 229632 |
| cmd/entire/cli/hooks_claudecode_handlers.go | read | 7 | 78 | 225736 |
| slide-24-final.png | read | 1 | 1 | 196438 |
| data/joint/whitney_fine_2d_C2D2_pbf-exp-exp.png | read | 1 | 1 | 188942 |
| /tmp/paper_audit/fig6_hires.png | read | 1 | 1 | 188034 |
| MonoDreams.Examples/bin/Debug/net8.0/debug/screenshot_000002_gt6,00_20260217_211734_264.pn | read | 1 | 1 | 185574 |
| /tmp/skf-footer-dark-absolute-bottom.png | read | 1 | 1 | 185486 |
| /Users/jakobfaber/Developer/scratch/worktrees/faber2026-johndoeii/figures/sightline_dm_sca | read | 1 | 1 | 184246 |
| cmd/entire/cli/strategy/manual_commit_hooks.go | read | 19 | 309 | 183341 |
| /tmp/figreview/page28_top-28.png | read | 1 | 1 | 182470 |
| /tmp/lightfast-desktop8.png | read | 1 | 1 | 180882 |
| /tmp/lightfast-desktop6.png | read | 1 | 1 | 180866 |
| /tmp/paper_audit/fig1_hires.png | read | 1 | 1 | 174422 |
| /Users/ta93abe/Developer/github.com/ta93abe/slides/slide3-dark-retry.png | read | 1 | 1 | 172594 |
| /tmp/paper_audit/fig3_hires.png | read | 1 | 1 | 166718 |
| /tmp/paper_audit/fig_f2_hires.png | read | 1 | 1 | 165606 |

### worst_offender_sessions  (20 rows)

| session_id | agent | repeated_results | repeated_chars | max_times_same_result |
|---|---|---|---|---|
| 8fb9c608-e9d6-441a-a521-ca4f3b79a9b4 | claude_code | 183 | 1374354 | 21 |
| a819a36d-8818-470b-b2fb-eacc5a34369e | claude_code | 16 | 1261877 | 4 |
| 2cc7fe3e-bf24-49a2-96cb-3b9179db8782 | claude_code | 235 | 906919 | 53 |
| 8603fa2a-25c9-4c76-87d4-83228bd296a6 | claude_code | 1209 | 703882 | 85 |
| 8e345b8c-dd3b-4bb1-bd2d-ac84987ff616 | claude_code | 256 | 661411 | 198 |
| 83180c0d-bbe5-4c61-b9bc-5700e05669e4 | claude_code | 992 | 611877 | 51 |
| 93524006-88e3-4f85-9fa5-3161115f77ec | claude_code | 104 | 588985 | 51 |
| b0f301c7-a7ad-4dbf-baf9-ca56ddf7de06 | claude_code | 24 | 551362 | 6 |
| a1ac494b-68ad-46a3-a108-614ece008190 | claude_code | 44 | 526446 | 16 |
| 8d58fde0-5c32-463d-ac3c-f0c840c3d193 | claude_code | 202 | 513376 | 15 |
| 0959d8ff-f53e-4750-a836-35d84e1c98de | claude_code | 84 | 472835 | 18 |
| 39105afc-d9df-4d14-8e63-0823b58441a8 | claude_code | 107 | 460129 | 14 |
| 85501d26-d82a-431a-bb17-9ab3643262c2 | claude_code | 26 | 362734 | 20 |
| 2cae28a4-28e8-4bfa-9225-7682543f3664 | claude_code | 1683 | 361530 | 194 |
| ba40f717-f702-4a9e-9f76-b57a4768e4c0 | claude_code | 4 | 355239 | 2 |
| e5367972-885e-46b8-bcdf-22e3e6b87525 | claude_code | 97 | 349786 | 12 |
| 20430269-c3d6-46f0-a275-830e2c7009f4 | claude_code | 640 | 336838 | 80 |
| ses_178885d42ffe8daG4lOcU4Vm8r | opencode | 529 | 335352 | 194 |
| 1a289c77-a9da-491d-954a-2df7f0dd6a17-8eacff7bdb26 | claude_code | 192 | 323407 | 23 |
| 2def5933-7d7d-48c7-9c80-b3730c4d8579 | claude_code | 118 | 317686 | 31 |

_T03_zero_info: 0.3s_

## T04 context rent: every tool result is re-read by every later call  (`T04_context_rent`)

**Headline**

- **pct_of_claude_code_cache_read_tokens_from_tool_results**: 51.3159
- **rent_usd_claude_code**: 30745.5
- **rent_usd_all_agents_upper_bound**: 166972.8
- **rent_usd_from_results_over_10k_chars**: 102351.0
- **pct_of_rent_from_results_over_10k**: 61.2980
- **pct_of_results_over_10k_chars**: 5.3103
- **rent_tokens_all_agents_upper_bound**: 348111782159.8

### by_tool_kind  (28 rows)

| agent | tool_kind | tool_results | result_chars | avg_later_calls | rent_tokens | rent_usd |
|---|---|---|---|---|---|---|
| codex | bash | 267922 | 1002926521 | 916.3952 | 277965989917.8 | 133969.5 |
| claude_code | read | 141736 | 781965569 | 189.8497 | 32837503281.5 | 15712.0 |
| claude_code | bash | 283632 | 288922779 | 223.8043 | 14430924317.5 | 7175.3 |
| claude_code | mcp | 12384 | 278902245 | 191.2050 | 7706172753.8 | 3803.9 |
| claude_code | task | 17622 | 91255520 | 183.2815 | 3825771697.2 | 1897.9 |
| codex | other | 5662 | 12537263 | 1569.0 | 2103571814.8 | 1033.9 |
| claude_code | grep | 38784 | 41327933 | 180.0807 | 1713329248.0 | 829.8406 |
| claude_code | edit | 131514 | 21891125 | 208.1802 | 1224239079.0 | 596.4278 |
| codex | edit | 24569 | 4625135 | 1061.8 | 1169085430.0 | 551.2310 |
| claude_code | other | 55390 | 13905124 | 175.0840 | 570346514.8 | 277.6341 |
| opencode | read | 15867 | 138037134 | 86.6184 | 1774820457.5 | 257.9654 |
| claude_code | todo | 5330 | 5842403 | 287.6129 | 315039395.5 | 157.2576 |
| claude_code | web | 3069 | 6593847 | 188.7276 | 279999978.0 | 136.8666 |
| codex | mcp | 1194 | 11441883 | 133.4916 | 516649633.2 | 129.1616 |
| claude_code | write | 20910 | 4932020 | 209.9213 | 211903653.5 | 104.4728 |
| opencode | bash | 9521 | 38136090 | 138.7195 | 554025658.0 | 85.9614 |
| codex | task | 2234 | 1810622 | 286.4602 | 169142317.5 | 63.6567 |
| claude_code | glob | 6888 | 5107895 | 121.9161 | 120880291.0 | 53.9612 |
| opencode | grep | 3270 | 7617217 | 100.0817 | 242424005.2 | 45.5889 |
| opencode | web | 179 | 1850406 | 187.1844 | 89016050.8 | 27.8548 |
| codex | todo | 3939 | 106557 | 1877.6 | 43059622.2 | 21.4194 |
| opencode | other | 270 | 1876188 | 148.2593 | 52031006.2 | 13.1567 |
| codex | write | 1080 | 193015 | 648.9352 | 29646588.5 | 12.8097 |
| opencode | task | 429 | 1375294 | 199.2821 | 81936386.8 | 4.7837 |
| opencode | glob | 2123 | 1304001 | 69.6561 | 27517965.8 | 4.6087 |
| opencode | todo | 838 | 623208 | 176.0000 | 32439475.0 | 3.2601 |
| opencode | edit | 4195 | 312740 | 192.0327 | 13363062.8 | 2.0985 |
| opencode | write | 1111 | 210508 | 264.7426 | 10952558.0 | 0.3707 |

### by_result_size_bucket  (4 rows)

| size_bucket | tool_results | pct_of_results | result_chars | pct_of_result_chars | avg_later_calls | rent_tokens | rent_usd | pct_of_rent_usd |
|---|---|---|---|---|---|---|---|---|
| 1. <1k | 713109 | 67.1691 | 176163237 | 6.3697 | 394.4025 | 18323675672.2 | 8818.6 | 5.2815 |
| 2. 1-10k | 292165 | 27.5196 | 997124947 | 36.0542 | 435.2567 | 117896803654.8 | 55778.8 | 33.4059 |
| 3. 10-50k | 52756 | 4.9692 | 1080635650 | 39.0738 | 614.4962 | 194099016354.8 | 94430.5 | 56.5544 |
| 4. >50k | 3632 | 0.3421 | 511706408 | 18.5023 | 142.0746 | 17792286478.0 | 7944.8 | 4.7582 |

### rent_vs_actual_cache_read  (3 rows)

| agent | rent_tokens | cache_read_tokens | pct_of_cache_read_tokens | rent_usd | cache_read_usd | pct_of_cache_read_usd |
|---|---|---|---|---|---|---|
| codex | 281997145324.0 | 28165371264 | 1001.2 | 135781.6 | 12295.4 | 1104.3 |
| claude_code | 63236110209.8 | 123228962728 | 51.3159 | 30745.5 | 61755.7 | 49.7857 |
| opencode | 2878526626.0 | 2416143822 | 119.1372 | 445.6490 | 444.9290 | 100.1618 |

### top20_single_results_by_rent  (20 rows)

| session_id | seq | agent | tool_kind | what | result_chars | later_calls | rent_tokens | rent_usd |
|---|---|---|---|---|---|---|---|---|
| 019df9cd-55af-78a1-ba56-85910d0fd078-6778b9191d07 | 45 | codex | other |  | 180592 | 3914 | 176709272.0 | 88.3546 |
| 019df9cd-55af-78a1-ba56-85910d0fd078-f15a3e31c54b | 45 | codex | other |  | 180592 | 3760 | 169756480.0 | 84.8782 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 64 | codex | bash | rg -n "TODO\|Gap\|gap\|Open\|open\|block\|Block\|missing\|Missing\|Next\|next\|vi | 40156 | 10585 | 106262815.0 | 53.1314 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 188 | codex | bash | bun run format:write | 40156 | 10572 | 106132308.0 | 53.0662 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 724 | codex | bash | bun run format:write | 40156 | 10497 | 105379383.0 | 52.6897 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 931 | codex | bash | bun run format:write | 40156 | 10469 | 105098291.0 | 52.5491 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1095 | codex | bash | rg -n "translate\|right:\|left:\|width:\|min-width:\|100vw\|vw\|fixed" /tmp/e | 40153 | 10449 | 104889674.2 | 52.4448 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1134 | codex | bash | bun run format:write | 40156 | 10444 | 104847316.0 | 52.4237 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1269 | codex | bash | bun run format:write | 40156 | 10428 | 104686692.0 | 52.3433 |
| cc0f3de4-3b06-47d4-bc8e-3752f9786504 | 2945 | claude_code | read | /Users/arijit/Coding/Python/DataQ/live-login.png | 348894 | 1200 | 104668200.0 | 52.3341 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1415 | codex | bash | sed -n '620,1040p' STABILIZATION.md | 40153 | 10410 | 104498182.5 | 52.2491 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1413 | codex | bash | rg -n "TODO\|FIXME\|blocker\|remain\|remaining\|out of scope\|later\|manual\|B | 40152 | 10410 | 104495580.0 | 52.2478 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1504 | codex | bash | bun run format:write | 40156 | 10400 | 104405600.0 | 52.2028 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1555 | codex | bash | cat /Users/hedde/.codex/plugins/cache/openai-bundled/browser/26.601.21 | 40132 | 10394 | 104283002.0 | 52.1415 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1756 | codex | bash | rg "Organize this event\|Participants\|Event Details\|Description\|Registe | 40152 | 10367 | 104063946.0 | 52.0320 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 1789 | codex | bash | bun run format:write | 40156 | 10363 | 104034157.0 | 52.0171 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 2032 | codex | bash | sed -n '480,620p' STABILIZATION.md && sed -n '1880,2090p' STABILIZATIO | 40152 | 10329 | 103682502.0 | 51.8413 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 2042 | codex | bash | rg -n "finance\|receipt\|tax-rate\|viewport\|layout\|overflow\|direct-route\| | 40147 | 10328 | 103659554.0 | 51.8298 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 2121 | codex | bash | bun run format:write | 40156 | 10320 | 103602480.0 | 51.8012 |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 2160 | codex | bash | cat /Users/hedde/.codex/plugins/cache/openai-bundled/browser/26.601.21 | 40132 | 10316 | 103500428.0 | 51.7502 |

_T04_context_rent: 0.2s_

## T05 entry cost: what it costs to say hello  (`T05_entry_cost`)

**Headline**

- **first_claude_code_version**: 2.1.17
- **median_entry_tokens_first_version**: 26796.5
- **last_claude_code_version**: 2.1.195
- **median_entry_tokens_last_version**: 28689.0
- **pct_change_in_median_entry_tokens**: 7.0625
- **median_entry_usd_last_version**: 0.1799
- **total_entry_usd_all_sessions**: 1154.4
- **pct_of_total_usd**: 0.9894

### claude_code_by_version  (41 rows)

| harness_version | vkey | sessions | median_entry_tokens | p90_entry_tokens | median_entry_usd | total_entry_usd |
|---|---|---|---|---|---|---|
| 2.1.17 | [2, 1, 17] | 54 | 26796.5 | 28470.8 | 0.1006 | 6.2450 |
| 2.1.34 | [2, 1, 34] | 55 | 15094.0 | 33329.0 | 0.0943 | 5.9681 |
| 2.1.37 | [2, 1, 37] | 73 | 26945.0 | 44205.0 | 0.1681 | 12.2426 |
| 2.1.39 | [2, 1, 39] | 115 | 12798.0 | 34961.2 | 0.0770 | 11.5300 |
| 2.1.42 | [2, 1, 42] | 148 | 9716.0 | 27614.8 | 0.0579 | 11.6782 |
| 2.1.44 | [2, 1, 44] | 57 | 10564.0 | 23899.8 | 0.0553 | 3.8970 |
| 2.1.45 | [2, 1, 45] | 117 | 12441.0 | 30568.6 | 0.0537 | 8.2618 |
| 2.1.47 | [2, 1, 47] | 128 | 12835.5 | 25258.0 | 0.0735 | 10.8365 |
| 2.1.49 | [2, 1, 49] | 140 | 11414.0 | 34883.3 | 0.0679 | 12.1412 |
| 2.1.50 | [2, 1, 50] | 179 | 12504.0 | 28166.8 | 0.0617 | 14.7395 |
| 2.1.52 | [2, 1, 52] | 163 | 8927.0 | 21165.8 | 0.0508 | 12.0536 |
| 2.1.56 | [2, 1, 56] | 57 | 10205.0 | 28447.4 | 0.0638 | 4.7963 |
| 2.1.59 | [2, 1, 59] | 103 | 15591.0 | 35430.2 | 0.0802 | 9.7747 |
| 2.1.62 | [2, 1, 62] | 223 | 20908.0 | 41838.0 | 0.1275 | 28.5550 |
| 2.1.63 | [2, 1, 63] | 383 | 12323.0 | 40524.2 | 0.0728 | 42.3935 |
| 2.1.69 | [2, 1, 69] | 62 | 13457.5 | 24558.2 | 0.0829 | 5.4318 |
| 2.1.70 | [2, 1, 70] | 281 | 25728.0 | 32796.0 | 0.1598 | 41.9148 |
| 2.1.71 | [2, 1, 71] | 176 | 13188.5 | 29559.0 | 0.0806 | 16.2698 |
| 2.1.72 | [2, 1, 72] | 113 | 14507.0 | 27859.0 | 0.0818 | 10.4429 |
| 2.1.74 | [2, 1, 74] | 84 | 16757.5 | 29935.1 | 0.1044 | 9.1510 |
| 2.1.75 | [2, 1, 75] | 146 | 33817.5 | 40621.5 | 0.2110 | 29.2203 |
| 2.1.76 | [2, 1, 76] | 90 | 16840.5 | 30688.0 | 0.1043 | 10.4819 |
| 2.1.78 | [2, 1, 78] | 58 | 15388.5 | 40745.9 | 0.0952 | 7.1166 |
| 2.1.79 | [2, 1, 79] | 276 | 28109.0 | 41109.0 | 0.1707 | 42.3498 |
| 2.1.80 | [2, 1, 80] | 74 | 14586.0 | 44496.4 | 0.0851 | 9.0017 |
| 2.1.81 | [2, 1, 81] | 172 | 20492.0 | 38602.3 | 0.1281 | 25.2003 |
| 2.1.84 | [2, 1, 84] | 54 | 14259.0 | 37962.0 | 0.0891 | 6.9112 |
| 2.1.87 | [2, 1, 87] | 65 | 14519.0 | 31665.4 | 0.0839 | 6.7760 |
| 2.1.89 | [2, 1, 89] | 57 | 24085.0 | 36689.8 | 0.1230 | 7.3364 |
| 2.1.91 | [2, 1, 91] | 56 | 26364.5 | 42796.5 | 0.1605 | 8.9909 |
| 2.1.92 | [2, 1, 92] | 167 | 13118.0 | 31345.4 | 0.0791 | 16.6523 |
| 2.1.114 | [2, 1, 114] | 145 | 22077.0 | 45025.6 | 0.1322 | 23.1375 |
| 2.1.116 | [2, 1, 116] | 54 | 29637.5 | 58967.8 | 0.1770 | 10.6553 |
| 2.1.118 | [2, 1, 118] | 92 | 30384.0 | 50469.2 | 0.1899 | 18.4426 |
| 2.1.119 | [2, 1, 119] | 194 | 27977.5 | 49438.4 | 0.1749 | 35.6970 |
| 2.1.126 | [2, 1, 126] | 68 | 26863.5 | 63313.4 | 0.1623 | 13.4220 |
| 2.1.139 | [2, 1, 139] | 60 | 32747.5 | 53803.3 | 0.1964 | 11.2122 |
| 2.1.143 | [2, 1, 143] | 66 | 33668.0 | 61537.5 | 0.1928 | 12.8182 |
| 2.1.150 | [2, 1, 150] | 136 | 14678.5 | 45434.0 | 0.0914 | 19.6809 |
| 2.1.170 | [2, 1, 170] | 58 | 28557.5 | 52896.8 | 0.1957 | 17.1966 |

_41 rows total, 40 shown._

### codex_by_version  (19 rows)

| harness_version | vkey | sessions | median_entry_tokens | p90_entry_tokens | median_entry_usd | total_entry_usd |
|---|---|---|---|---|---|---|
| 0.118.0 | [0, 118, 0] | 170 | 18832.5 | 22342.4 | 0.0471 | 6.9314 |
| 0.120.0 | [0, 120, 0] | 39 | 19603.0 | 28042.6 | 0.0490 | 2.0057 |
| 0.122.0-alpha.12 | [0, 122, 0] | 31 | 51427.0 | 51618.0 | 0.1286 | 3.9812 |
| 0.122.0-alpha.1 | [0, 122, 0] | 27 | 22331.0 | 42704.4 | 0.0391 | 1.2558 |
| 0.122.0 | [0, 122, 0] | 52 | 20526.5 | 26047.8 | 0.0484 | 2.2822 |
| 0.124.0-alpha.1 | [0, 124, 0] | 21 | 54315.0 | 54439.0 | 0.1358 | 2.3951 |
| 0.125.0 | [0, 125, 0] | 62 | 23177.5 | 26000.8 | 0.1155 | 6.7902 |
| 0.128.0 | [0, 128, 0] | 20 | 25331.0 | 31371.0 | 0.1196 | 2.1387 |
| 0.129.0-alpha.2 | [0, 129, 0] | 38 | 34377.0 | 42649.1 | 0.1718 | 6.0639 |
| 0.130.0 | [0, 130, 0] | 36 | 24992.5 | 68302.5 | 0.1250 | 5.9373 |
| 0.133.0 | [0, 133, 0] | 75 | 26936.0 | 39187.6 | 0.1347 | 10.3110 |
| 0.139.0 | [0, 139, 0] | 29 | 7165.0 | 18849.4 | 0.0358 | 1.3999 |
| 0.140.0-alpha.19 | [0, 140, 0] | 26 | 18661.5 | 19336.5 | 0.0933 | 2.5134 |
| 0.140.0 | [0, 140, 0] | 20 | 23007.0 | 24666.3 | 0.1150 | 2.2962 |
| 0.140.0-alpha.2 | [0, 140, 0] | 24 | 17893.5 | 34430.5 | 0.0895 | 2.6789 |
| 0.141.0 | [0, 141, 0] | 30 | 17597.5 | 44677.0 | 0.0880 | 3.6489 |
| 0.142.0 | [0, 142, 0] | 27 | 39588.0 | 42110.2 | 0.1979 | 4.9436 |
| 0.142.5 | [0, 142, 5] | 35 | 22243.0 | 27207.2 | 0.1112 | 3.9215 |
| 1.0.0 | [1, 0, 0] | 42 | 44920.5 | 49377.1 | 0.1123 | 4.5357 |

### by_agent_month  (16 rows)

| agent | month | sessions | median_entry_tokens | p90_entry_tokens | median_entry_usd | total_entry_usd |
|---|---|---|---|---|---|---|
| claude_code | 2026-01-01 00:00:00 | 131 | 34854.0 | 43236.0 | 0.2170 | 24.1284 |
| claude_code | 2026-02-01 00:00:00 | 1658 | 12332.5 | 31777.1 | 0.0692 | 152.5285 |
| claude_code | 2026-03-01 00:00:00 | 2274 | 19622.0 | 38057.6 | 0.1139 | 293.9066 |
| claude_code | 2026-04-01 00:00:00 | 1430 | 23378.5 | 44463.2 | 0.1379 | 220.8093 |
| claude_code | 2026-05-01 00:00:00 | 851 | 30313.0 | 59848.0 | 0.1840 | 167.8879 |
| claude_code | 2026-06-01 00:00:00 | 685 | 26275.0 | 57630.2 | 0.1660 | 141.5162 |
| claude_code | 2026-07-01 00:00:00 | 80 | 33176.0 | 52410.5 | 0.2797 | 23.7247 |
| codex | 2026-03-01 00:00:00 | 4 | 20823.0 | 25257.6 | 0.0521 | 0.2159 |
| codex | 2026-04-01 00:00:00 | 629 | 22944.0 | 50454.2 | 0.0570 | 48.1301 |
| codex | 2026-05-01 00:00:00 | 249 | 30685.0 | 40075.0 | 0.1500 | 37.5330 |
| codex | 2026-06-01 00:00:00 | 244 | 22805.0 | 39993.0 | 0.1140 | 29.0828 |
| codex | 2026-07-01 00:00:00 | 39 | 21696.0 | 27204.4 | 0.1085 | 4.3375 |
| opencode | 2026-02-01 00:00:00 | 4 | 12989.0 | 17443.0 | 0.0473 | 0.2117 |
| opencode | 2026-03-01 00:00:00 | 567 | 7174.0 | 12736.2 | 0.0126 | 7.4944 |
| opencode | 2026-04-01 00:00:00 | 62 | 11605.5 | 22043.7 | 0.0294 | 2.2847 |
| opencode | 2026-05-01 00:00:00 | 28 | 4088.5 | 15030.7 | 0.0118 | 0.6512 |

### totals_by_agent  (3 rows)

| agent | sessions | median_entry_tokens | total_entry_tokens | total_entry_usd | pct_of_total_usd |
|---|---|---|---|---|---|
| claude_code | 7109 | 20472.0 | 168260247 | 1024.5 | 0.8781 |
| codex | 1165 | 24232.0 | 32576745 | 119.2993 | 0.1022 |
| opencode | 661 | 7174.0 | 4801489 | 10.6420 | 0.0091 |

_T05_entry_cost: 0.0s_

## T06 truncated: responses that hit the output cap  (`T06_truncated`)

**Headline**

- **truncated_calls**: 40
- **pct_of_all_calls_truncated**: 0.0043
- **sessions_affected**: 25
- **usd_paid_to_resume_after_truncation**: 2.6811
- **pct_of_total_usd**: 0.0023

### by_agent  (4 rows)

| agent | calls | truncated_calls | pct_calls_truncated | usd_of_continuation_input | continuation_ctx_tokens |
|---|---|---|---|---|---|
| claude_code | 677425 | 39 | 0.0058 | 2.3603 | 3745332 |
| opencode | 27949 | 1 | 0.0036 | 0.3208 | 85546 |
| cursor | 8910 | 0 | 0.0000 |  |  |
| codex | 218945 | 0 | 0.0000 |  |  |

### by_model  (4 rows)

| model | stop_reason | truncated_calls | sessions | avg_output_tokens | usd_of_continuation_input |
|---|---|---|---|---|---|
| claude-sonnet-4-6 | max_tokens | 22 | 13 | 9090.9 | 0.6331 |
| claude-opus-4-8 | max_tokens | 9 | 3 | 63999.9 | 1.4703 |
| claude-opus-4-6 | max_tokens | 8 | 8 | 14000.0 | 0.2569 |
| claude-sonnet-4.6 | length | 1 | 1 | 32000.0 | 0.3208 |

### stop_reason_distribution  (17 rows)

| agent | stop_reason | calls | pct_of_agent_calls |
|---|---|---|---|
| claude_code | tool_use | 495764 | 73.1836 |
| claude_code |  | 128736 | 19.0037 |
| claude_code | end_turn | 50615 | 7.4717 |
| claude_code | stop_sequence | 2269 | 0.3349 |
| claude_code | max_tokens | 39 | 0.0058 |
| claude_code | refusal | 2 | 2.952e-04 |
| codex | tool_use | 196382 | 89.6947 |
| codex | end_turn | 22563 | 10.3053 |
| cursor | tool_use | 6048 | 67.8788 |
| cursor | end_turn | 2862 | 32.1212 |
| opencode | tool-calls | 24962 | 89.3127 |
| opencode | stop | 2795 | 10.0004 |
| opencode |  | 178 | 0.6369 |
| opencode | unknown | 9 | 0.0322 |
| opencode | other | 2 | 0.0072 |
| opencode | error | 2 | 0.0072 |
| opencode | length | 1 | 0.0036 |

_T06_truncated: 0.1s_

## T07 path guessing: the agent opens files that are not there  (`T07_path_guessing`)

**Headline**

- **missing_path_errors**: 1989
- **pct_of_file_tool_calls**: 0.5703
- **sessions_affected**: 1209
- **usd_of_the_next_3_calls_after_the_error**: 643.8576
- **pct_of_total_usd**: 0.5518

### by_agent  (4 rows)

| agent | file_tool_calls | missing_path_errors | pct_missing_path | sessions_affected | usd_of_next_3_calls |
|---|---|---|---|---|---|
| claude_code | 298383 | 1844 | 0.6180 | 1132 | 635.8012 |
| opencode | 21173 | 145 | 0.6848 | 77 | 8.0565 |
| codex | 25649 | 0 | 0.0000 | 0 |  |
| cursor | 3563 | 0 | 0.0000 | 0 |  |

### by_model  (13 rows)

| model | file_tool_calls | missing_path_errors | pct_missing_path | usd_of_next_3_calls |
|---|---|---|---|---|
| glm-5 | 1049 | 34 | 3.2412 | 0.0000 |
| claude-sonnet-4-5-20250929 | 5635 | 94 | 1.6681 | 11.3386 |
| big-pickle | 3354 | 34 | 1.0137 | 0.0000 |
| claude-sonnet-4-6 | 18237 | 158 | 0.8664 | 15.6577 |
| claude-opus-4-5-20251101 | 8737 | 75 | 0.8584 | 13.6940 |
| claude-opus-4-6 | 154701 | 907 | 0.5863 | 222.3206 |
| claude-opus-4-8 | 39731 | 228 | 0.5739 | 172.8860 |
| gpt-5.4 | 8394 | 47 | 0.5599 | 3.1742 |
| claude-opus-4-7 | 61915 | 296 | 0.4781 | 185.9786 |
| claude-fable-5 | 4419 | 14 | 0.3168 | 11.6330 |
| gpt-5.3-codex | 12831 | 40 | 0.3117 | 3.7253 |
| gpt-5.5 | 18809 | 5 | 0.0266 | 0.8488 |
|  | 6034 | 0 | 0.0000 |  |

### by_tool_kind  (11 rows)

| agent | tool_kind | calls | missing_path_errors | pct_missing_path |
|---|---|---|---|---|
| claude_code | edit | 133185 | 1042 | 0.7824 |
| claude_code | read | 144080 | 802 | 0.5566 |
| opencode | read | 15867 | 140 | 0.8823 |
| opencode | edit | 4195 | 5 | 0.1192 |
| cursor | read | 1734 | 0 | 0.0000 |
| opencode | write | 1111 | 0 | 0.0000 |
| claude_code | write | 21118 | 0 | 0.0000 |
| codex | edit | 24569 | 0 | 0.0000 |
| codex | write | 1080 | 0 | 0.0000 |
| cursor | edit | 1313 | 0 | 0.0000 |
| cursor | write | 516 | 0 | 0.0000 |

### top_missing_paths  (20 rows)

| file_path_80 | errors | sessions |
|---|---|---|
| _bmad/bmb/workflows/module/steps-e/step-01-assess.md | 23 | 23 |
| frontend/src/components/RemediateTab.tsx | 17 | 8 |
| .golangci.yml | 14 | 14 |
| cmd/entire/cli/setup.go | 14 | 5 |
| cmd/entire/cli/strategy/manual_commit_hooks.go | 13 | 10 |
| main.tex | 12 | 7 |
| cmd/entire/cli/logging/logging.go | 8 | 8 |
| apps/wodsmith-start/src/routes/compete/organizer/$competitionId/events/$eventId/ | 8 | 3 |
| src/agent/index.ts | 8 | 3 |
| skills/ai-native-repo-bootstrap-workspace/iteration-2/eval-5-governance-heavy-do | 8 | 3 |
| Cee/Controllers/ImageViewController.swift | 7 | 1 |
| REDACTED.md | 7 | 6 |
| frontend/src/components/RemediationHistoryCard.tsx | 7 | 6 |
| src/pages/Code.tsx | 7 | 1 |
| Cee/Controllers/ImageWindowController.swift | 7 | 1 |
| cmd/entire/cli/agent/types/types.go | 7 | 6 |
| cmd/entire/cli/explain.go | 7 | 4 |
| REDACTED.output | 7 | 3 |
| cmd/entire/cli/validation/validators_test.go | 7 | 1 |
| crates/panopt/src/main.rs | 6 | 2 |

_T07_path_guessing: 0.2s_

## T08 ceremony: todo lists and task hand-offs  (`T08_ceremony`)

**Headline**

- **ceremony_tool_calls**: 31158
- **pct_of_all_tool_calls**: 2.8669
- **output_tokens_spent_on_ceremony**: 15774291.5
- **ceremony_usd**: 381.3802
- **pct_of_all_output_usd**: 3.5411

### by_agent  (4 rows)

| agent | tool_calls | ceremony_calls | pct_of_tool_calls | todo_tokens | task_tokens | ceremony_usd |
|---|---|---|---|---|---|---|
| claude_code | 731210 | 23293 | 3.1855 | 3834506.8 | 10601062.2 | 355.9561 |
| codex | 309060 | 6174 | 1.9977 | 447921.0 | 356112.5 | 20.0993 |
| opencode | 38690 | 1267 | 3.2747 | 129781.2 | 297955.0 | 5.3248 |
| cursor | 7864 | 424 | 5.3917 | 65548.5 | 41404.2 |  |

### sessions_with_vs_without  (8 rows)

| mode | kind | sessions | pct_sessions_with_commits | usd | committed_lines | usd_per_committed_line |
|---|---|---|---|---|---|---|
| collab | no todo/task | 1012 | 99.2095 | 3734.7 | 1787448 | 0.0021 |
| collab | uses todo/task | 959 | 99.6872 | 18030.1 | 1462930 | 0.0123 |
| human | no todo/task | 1155 | 77.7489 | 5125.7 | 4527734 | 0.0011 |
| human | uses todo/task | 1308 | 87.5382 | 31902.5 | 8194046 | 0.0039 |
| unknown | no todo/task | 198 | 0.0000 | 2384.4 |  |  |
| unknown | uses todo/task | 394 | 0.0000 | 20667.4 |  |  |
| vibe | no todo/task | 2381 | 99.2020 | 10263.3 | 1145607 | 0.0090 |
| vibe | uses todo/task | 1616 | 99.0718 | 24535.1 | 613800 | 0.0400 |

### by_agent_and_kind  (8 rows)

| agent | tool_kind | calls | tokens | usd | median_input_chars |
|---|---|---|---|---|---|
| claude_code | task | 17833 | 10601062.2 | 265.9264 | 1659.0 |
| claude_code | todo | 5460 | 3834506.8 | 90.0297 | 1007.5 |
| codex | todo | 3939 | 447921.0 | 11.3462 | 375.0000 |
| codex | task | 2235 | 356112.5 | 8.7531 | 110.0000 |
| opencode | task | 429 | 297955.0 | 4.1236 | 4903.0 |
| opencode | todo | 838 | 129781.2 | 1.2012 | 549.5000 |
| cursor | todo | 299 | 65548.5 |  | 283.0000 |
| cursor | task | 125 | 41404.2 |  | 1280.0 |

_T08_ceremony: 0.1s_

## T09 polling: sleep, wait, gh run watch  (`T09_polling`)

**Headline**

- **polling_bash_calls**: 10316
- **pct_of_all_bash_calls**: 1.9640
- **sessions_that_poll**: 1127
- **usd_of_calls_that_issued_a_poll**: 1359.1
- **polls_inside_a_burst**: 4626
- **usd_in_bursts**: 549.9164
- **pct_of_total_usd**: 1.1649

### by_agent  (4 rows)

| agent | bash_calls | polling_calls | pct_of_bash_calls | sessions | usd_of_the_calls_that_issued_them | ctx_tokens |
|---|---|---|---|---|---|---|
| claude_code | 291956 | 7041 | 2.4117 | 961 | 1081.5 | 1705656825 |
| codex | 220422 | 2974 | 1.3492 | 134 | 267.6909 | 438266466 |
| opencode | 10393 | 192 | 1.8474 | 21 | 9.9346 | 21538021 |
| cursor | 2480 | 109 | 4.3952 | 11 |  | 0 |

### polling_sequences  (4 rows)

| burst | polling_calls | usd | ctx_tokens |
|---|---|---|---|
| isolated | 5690 | 809.2240 | 1285345232 |
| 2 polls in 5 calls | 3029 | 361.4670 | 572016419 |
| 3 polls in 5 calls | 975 | 103.5597 | 166578048 |
| 4+ polls in 5 calls | 622 | 84.8897 | 141521613 |

### top_polling_commands  (20 rows)

| command_head_80 | polling_calls | sessions | usd |
|---|---|---|---|
| sleep 120 | 326 | 27 | 28.9138 |
| sleep 180 | 94 | 13 | 8.0477 |
| sleep 60 | 70 | 25 | 5.5475 |
| sleep 30 | 53 | 15 | 4.3815 |
| cd /Users/scottdensmore/Developer/scottdensmore/contactmanager for i in $(seq 1  | 47 | 1 | 11.7199 |
| sleep 120; gh api repos/fogodev/ars-ui/issues/679/reactions --paginate \| jq -r ' | 42 | 2 | 3.9148 |
| sleep 120 && echo poll | 36 | 3 | 2.9423 |
| sleep 120 printf 'reactions:\n' gh api repos/fogodev/ars-ui/issues/667/reactions | 32 | 1 | 2.5374 |
| sleep 300 | 31 | 11 | 2.9887 |
| sleep 120; echo '--- reactions ---'; gh api repos/fogodev/ars-ui/issues/694/reac | 30 | 2 | 2.3853 |
| sleep 180; gh pr view 679 --json mergeStateStatus,statusCheckRollup --jq '{merge | 30 | 2 | 3.3105 |
| sleep 240 | 26 | 11 | 2.4835 |
| sleep 90 | 26 | 13 | 1.9885 |
| sleep 900 && echo "=== $(date) ===" && uv run iris --config lib/iris/examples/ma | 25 | 2 | 5.7701 |
| sleep 120 && gh api repos/fogodev/ars-ui/issues/683/reactions --jq '.[] \| "\(.us | 23 | 1 | 1.8169 |
| sleep 180 && source ~/.bashrc && uv run iris --config lib/iris/examples/marin.ya | 22 | 7 | 1.9852 |
| sleep 45 | 21 | 12 | 1.8081 |
| sleep 3 | 21 | 15 | 1.1681 |
| sleep 120 && gh pr checks 727 --json name,state,bucket,link,startedAt,completedA | 20 | 1 | 2.4492 |
| until grep -qE "BUILD SUCCEEDED\|BUILD FAILED" /tmp/s6-ios.txt 2>/dev/null; do sl | 19 | 1 | 4.2031 |

_T09_polling: 0.2s_

## T10 rewrite vs edit: writing a whole file the model already has  (`T10_rewrite_vs_edit`)

**Headline**

- **usd_output_writes_to_files_already_in_context**: 186.5236
- **pct_of_all_output_usd**: 1.7319
- **writes_on_known_files**: 6282
- **pct_of_writes_on_known_files**: 26.5052
- **output_tokens_rewritten**: 8156467.0
- **usd_old_string_quotes_over_1500_chars**: 94.0694
- **median_json_overhead_ratio**: 0.0767

### writes_on_known_files  (4 rows)

| agent | writes | writes_on_known_files | pct_writes_on_known_files | output_tokens_on_known_files | usd_on_known_files | usd_all_writes |
|---|---|---|---|---|---|---|
| claude_code | 21025 | 5791 | 27.5434 | 7542823.5 | 180.3306 | 603.5731 |
| codex | 1080 | 112 | 10.3704 | 220761.2 | 4.6514 | 42.4028 |
| opencode | 1108 | 278 | 25.0903 | 318836.0 | 1.5416 | 8.6146 |
| cursor | 488 | 101 | 20.6967 | 74046.2 |  |  |

### rewrite_ratio_distribution  (5 rows)

| bucket | writes | content_tokens | usd | median_content_chars |
|---|---|---|---|---|
| 0. no earlier read | 1528 | 1919709.8 | 42.6038 | 2811.5 |
| 1. <25% of the file | 193 | 73321.2 | 1.6198 | 903.0000 |
| 2. 25-90% | 1941 | 2086243.5 | 47.4905 | 3028.0 |
| 3. ~same size (90-110%) | 774 | 1091058.5 | 25.3701 | 3975.0 |
| 4. bigger than what was read | 1846 | 2986134.0 | 69.4393 | 4351.5 |

### big_old_string_edits  (4 rows)

| agent | edits | edits_old_string_over_1500 | pct | old_string_chars | usd_old_string | usd_old_string_all_edits |
|---|---|---|---|---|---|---|
| claude_code | 132909 | 5784 | 4.3518 | 15494375 | 93.7293 | 320.8136 |
| opencode | 4189 | 118 | 2.8169 | 345705 | 0.3401 | 0.9803 |
| codex | 24569 | 0 | 0.0000 |  |  | 0.0000 |
| cursor | 1284 | 40 | 3.1153 | 110946 |  |  |

### json_overhead_for_writes  (4 rows)

| agent | writes | median_json_overhead_ratio | p90_json_overhead_ratio | extra_tokens_vs_bare_content |
|---|---|---|---|---|
| claude_code | 20469 | 0.0800 | 0.2621 | 2208328.8 |
| codex | 1076 | -0.0104 | -0.0027 | 0.0000 |
| opencode | 1063 | 0.0735 | 0.2643 | 73146.8 |
| cursor | 474 | 0.0958 | 0.2848 | 29719.2 |

### top_rewritten_files  (20 rows)

| file_path_80 | agent | writes_on_known_file | content_chars | usd |
|---|---|---|---|---|
| REDACTED.md | claude_code | 46 | 526643 | 3.0628 |
| README.md | claude_code | 73 | 370522 | 2.0392 |
| /Users/jk/Downloads/outbid-vs-harness-engineering.html | claude_code | 5 | 262100 | 1.6381 |
| src/droneBayView.js | claude_code | 4 | 223265 | 1.3954 |
| /home/hj/.claude/plans/hidden-noodling-bird.md | claude_code | 25 | 175840 | 1.0990 |
| docs/superpowers/plans/2026-04-20-entire-attach-picker.md | claude_code | 3 | 170618 | 1.0664 |
| /home/hj/.claude/plans/cuddly-fluttering-key.md | claude_code | 28 | 193579 | 0.7833 |
| static/index.html | claude_code | 3 | 110747 | 0.6922 |
| docs/superpowers/plans/2026-04-28-recap-perf-and-accuracy.md | claude_code | 2 | 105714 | 0.6607 |
| attribution-playground.html | claude_code | 3 | 104480 | 0.6530 |
| apps/wodsmith-start/src/routes/compete/organizer/$competitionId/athletes/-compon | claude_code | 8 | 90796 | 0.5675 |
| REDACTED.py | claude_code | 15 | 90264 | 0.5641 |
| src/islandView.js | claude_code | 4 | 87978 | 0.5499 |
| docs/superpowers/plans/2026-05-20-entire-review-redesign.md | claude_code | 1 | 85695 | 0.5356 |
| projects/frontend/src/pages/ops/ImportFlow.tsx | opencode | 4 | 142545 | 0.5345 |
| CLAUDE.md | claude_code | 22 | 96679 | 0.5130 |
| app/src/client/routes/tool-registry-page.test.tsx | claude_code | 4 | 74901 | 0.4681 |
| index.html | claude_code | 9 | 79174 | 0.4621 |
| /home/hj/.claude/plans/synthetic-weaving-toucan.md | claude_code | 21 | 99654 | 0.4491 |
| /Users/rodrigooliveira/.claude/plans/i-think-monodreams-is-velvet-hearth.md | claude_code | 6 | 71261 | 0.4454 |

_T10_rewrite_vs_edit: 0.2s_

## T11 unread output: final replies nobody had time to read  (`T11_unread_output`)

**Headline**

- **usd_final_text_that_could_not_be_read**: 88.7788
- **pct_of_all_output_usd**: 0.8243
- **pct_of_final_text_tokens_unread**: 21.2756
- **unread_replies**: 8915
- **final_replies_measured**: 66528
- **median_seconds_before_next_prompt**: 99.4225
- **median_seconds_needed_to_read**: 33.4560

### by_agent  (3 rows)

| agent | final_replies | unread_replies | pct_replies_unread | final_text_tokens | unread_text_tokens | pct_text_tokens_unread | unread_usd | median_read_time_s | median_delta_s |
|---|---|---|---|---|---|---|---|---|---|
| claude_code | 55223 | 6543 | 11.8483 | 13793522.2 | 2786147.0 | 20.1990 | 68.4263 | 29.5680 | 98.4600 |
| codex | 9501 | 2257 | 23.7554 | 2959570.8 | 784364.0 | 26.5026 | 19.3484 | 48.7680 | 94.5290 |
| opencode | 1804 | 115 | 6.3747 | 600615.2 | 121593.5 | 20.2448 | 1.0041 | 43.3920 | 170.2080 |

### delta_vs_read_time_distribution  (5 rows)

| bucket | final_replies | pct_of_replies | text_tokens | usd | median_text_chars |
|---|---|---|---|---|---|
| 1. <25% of read time | 4604 | 6.9204 | 1861497.2 | 44.1336 | 1071.0 |
| 2. 25-50% | 4311 | 6.4800 | 1830607.2 | 44.6452 | 1266.0 |
| 3. 50-100% | 7535 | 11.3261 | 2827220.8 | 67.5813 | 1161.0 |
| 4. 1-5x | 22508 | 33.8324 | 6418166.2 | 152.9936 | 868.0000 |
| 5. >5x (took their time) | 27570 | 41.4412 | 4416216.8 | 104.6309 | 319.0000 |

### by_reply_length  (4 rows)

| length_bucket | final_replies | pct_unread | text_tokens | unread_usd |
|---|---|---|---|---|
| 1. <500 chars | 27324 | 7.9783 | 1393877.0 | 3.2900 |
| 2. 0.5-2k | 30327 | 15.0196 | 8348808.8 | 33.2438 |
| 3. 2-6k | 8181 | 22.5400 | 6133602.0 | 34.7599 |
| 4. >6k chars | 696 | 48.2759 | 1477420.5 | 17.4851 |

### longest_unread_replies  (20 rows)

| session_id | turn_idx | agent | n_text_chars | read_time_s | delta_s | text_usd |
|---|---|---|---|---|---|---|
| ses_10a768004ffeHAmBUOMS9czhcG | 5 | opencode | 34952 | 1677.7 | 293.7180 |  |
| e5a3e2c6-422a-4a20-9af8-61afddb2b6c5 | 1 | claude_code | 31832 | 1527.9 | 181.0220 | 0.1989 |
| e5a3e2c6-422a-4a20-9af8-61afddb2b6c5 | 2 | claude_code | 28635 | 1374.5 | 95.1830 | 0.1790 |
| 019e56aa-18c9-7122-9658-3077c7106725 | 2 | codex | 22221 | 1066.6 | 13.7130 | 0.1667 |
| c58456d9-709a-4a41-b50b-241f0e065cee | 8 | claude_code | 18802 | 902.4960 | 125.8530 | 0.1175 |
| 2e3df92b-358b-4e2f-83f5-8b62591ddca5 | 1 | claude_code | 18618 | 893.6640 | 344.2340 | 0.1164 |
| 261e433d-477e-4516-9fbf-2eba6dd912ac | 2 | claude_code | 18537 | 889.7760 | 108.2450 | 0.1159 |
| 0929f616-70fa-4c45-a0f9-02d932d95aa3 | 7 | claude_code | 18070 | 867.3600 | 128.3990 | 0.0678 |
| bb028fb8-27a3-4fc5-8c43-5208f3e988ba | 7 | claude_code | 17707 | 849.9360 | 301.1610 | 0.1107 |
| 0020a454-e7a8-43c9-ba7a-4e85bfa59f81 | 3 | claude_code | 17209 | 826.0320 | 128.0930 | 0.1076 |
| 2e3df92b-358b-4e2f-83f5-8b62591ddca5 | 7 | claude_code | 16716 | 802.3680 | 219.3740 | 0.1045 |
| 5ed9f5ff-3132-461d-ab9d-82ad2068a401 | 1 | claude_code | 16666 | 799.9680 | 42.0660 | 0.1042 |
| 27c10fbd-3055-4d96-8e88-8a95ee2d9e1e | 3 | claude_code | 16398 | 787.1040 | 232.6010 | 0.1025 |
| f91cf4d2-1b71-4a98-a77f-464647caccb6 | 22 | claude_code | 16374 | 785.9520 | 170.7650 | 0.1023 |
| b14a73cd-50c9-47ac-abfd-c13933046912 | 12 | claude_code | 15880 | 762.2400 | 27.4820 | 0.0993 |
| 019e6252-572e-7c62-a9ae-4b7341b06e3b | 2 | codex | 15733 | 755.1840 | 92.5240 | 0.1180 |
| 0929f616-70fa-4c45-a0f9-02d932d95aa3 | 5 | claude_code | 14985 | 719.2800 | 142.4530 | 0.0562 |
| aaa2322e-c03b-46fe-b73b-07239acb0f17 | 1 | claude_code | 14483 | 695.1840 | 284.0250 | 0.0905 |
| 3cc5038a-01e9-49c6-896a-7f708bcf00d4 | 1 | claude_code | 14483 | 695.1840 | 284.0250 | 0.1810 |
| 019e57fe-8571-7122-a65d-3a151cb21cc1 | 2 | codex | 14116 | 677.5680 | 7.1440 | 0.1059 |

### ordering_diagnostic  (3 rows)

| agent | turns_with_a_next_prompt | turns_dropped_no_call_before_next_prompt | turns_where_last_call_ts_was_after_next_prompt | median_raw_delta_s | median_adjusted_delta_s |
|---|---|---|---|---|---|
| claude_code | 57362 | 19 | 59 | 95.9885 | 96.2050 |
| codex | 13441 | 2684 | 12352 | -4.6050 | 74.2590 |
| opencode | 2178 | 7 | 17 | 123.8835 | 126.1960 |

_T11_unread_output: 0.1s_

## T12 human wait: the token bill is not the expensive part  (`T12_human_wait`)

**Headline**

- **total_agent_working_hours**: 16358.0
- **total_token_usd_in_those_turns**: 113944.9
- **human_usd_at_60_per_hour_if_watching**: 981481.0
- **ratio_human_wait_cost_to_token_cost**: 8.6136
- **total_human_typing_and_thinking_hours**: 3336.5
- **median_agent_seconds_per_turn**: 69.6925
- **usd_of_tokens_per_agent_hour**: 6.9657

### by_agent  (3 rows)

| agent | turns | agent_hours | median_agent_time_s | p90_agent_time_s | human_wait_hours | median_human_time_s | usd | usd_per_agent_hour |
|---|---|---|---|---|---|---|---|---|
| claude_code | 63245 | 14676.9 | 68.8450 | 685.7284 | 2767.7 | 84.8640 | 94333.5 | 6.4274 |
| codex | 11767 | 1461.2 | 81.5860 | 565.7700 | 431.9904 | 64.9280 | 18724.2 | 12.8140 |
| opencode | 2952 | 219.9368 | 51.8880 | 366.2024 | 136.7853 | 110.0785 | 887.1856 | 4.0338 |

### by_mode  (4 rows)

| mode | turns | agent_hours | human_wait_hours | token_usd | human_usd_if_watching_at_60ph | ratio_wait_cost_to_token_cost | median_agent_time_s |
|---|---|---|---|---|---|---|---|
| vibe | 25856 | 4527.4 | 1067.4 | 33771.1 | 271644.7 | 8.0437 | 66.7475 |
| human | 24835 | 4493.4 | 1105.1 | 36283.1 | 269605.4 | 7.4306 | 67.3280 |
| unknown | 11520 | 3794.4 | 500.1521 | 22703.8 | 227666.3 | 10.0277 | 80.5420 |
| collab | 15753 | 3542.7 | 663.8365 | 21186.9 | 212564.6 | 10.0328 | 71.5220 |

### per_session  (3 rows)

| agent | sessions | median_agent_hours_per_session | p90_agent_hours_per_session | median_human_hours_per_session | agent_hours | usd |
|---|---|---|---|---|---|---|
| claude_code | 6959 | 0.2135 | 2.4712 | 0.1869 | 14676.9 | 94333.5 |
| codex | 1133 | 0.1313 | 2.5183 | 0.2785 | 1461.2 | 18724.2 |
| opencode | 783 | 0.0231 | 0.1956 | 0.2425 | 219.9368 | 887.1856 |

### agent_time_buckets  (5 rows)

| bucket | turns | pct_of_turns | agent_hours | usd |
|---|---|---|---|---|
| 1. <30 s | 23902 | 30.6577 | 92.5192 | 5395.6 |
| 2. 0.5-2 min | 24377 | 31.2670 | 436.0116 | 16161.4 |
| 3. 2-10 min | 21204 | 27.1972 | 1602.8 | 39947.8 |
| 4. 10-30 min | 5776 | 7.4085 | 1576.1 | 27650.0 |
| 5. >30 min | 2705 | 3.4696 | 12650.6 | 24790.2 |

_T12_human_wait: 0.1s_

## T13 abandoned: sessions that produced no committed line  (`T13_abandoned`)

**Headline**

- **abandoned_sessions**: 1088
- **pct_of_sessions_abandoned**: 11.7419
- **usd_abandoned**: 28626.3
- **pct_of_total_usd_abandoned**: 24.5348
- **usd_zero_committed_lines**: 5572.1
- **usd_no_attribution**: 23054.2
- **median_usd_of_an_abandoned_session**: 4.0369

### by_agent  (12 rows)

| agent | outcome | sessions | pct_of_agent_sessions | usd | pct_of_agent_usd | median_session_usd | median_calls |
|---|---|---|---|---|---|---|---|
| claude_code | committed | 6384 | 88.2988 | 73912.7 | 76.4026 | 2.6995 | 41.0000 |
| claude_code | no attribution | 513 | 7.0954 | 18107.8 | 18.7178 | 9.2850 | 94.0000 |
| claude_code | zero committed lines | 333 | 4.6058 | 4720.6 | 4.8796 | 2.2798 | 35.0000 |
| codex | committed | 969 | 83.0334 | 13268.6 | 69.6572 | 2.1127 | 40.0000 |
| codex | no attribution | 74 | 6.3410 | 4940.4 | 25.9362 | 14.2521 | 183.0000 |
| codex | zero committed lines | 124 | 10.6255 | 839.3928 | 4.4066 | 1.5815 | 30.5000 |
| cursor | committed | 81 | 94.1860 | 0.0000 |  | 0.0000 | 24.0000 |
| cursor | no attribution | 2 | 2.3256 | 0.0000 |  | 0.0000 | 13.5000 |
| cursor | zero committed lines | 3 | 3.4884 | 0.0000 |  | 0.0000 | 329.0000 |
| opencode | committed | 744 | 95.0192 | 869.0808 | 97.9593 | 0.2445 | 12.0000 |
| opencode | no attribution | 13 | 1.6603 | 5.9671 | 0.6726 | 0.0000 | 10.0000 |
| opencode | zero committed lines | 26 | 3.3206 | 12.1376 | 1.3681 | 0.0000 | 14.5000 |

### by_mode  (7 rows)

| mode | outcome | sessions | usd | pct_of_all_usd | median_human_turns | median_tool_calls |
|---|---|---|---|---|---|---|
| vibe | committed | 4038 | 33894.3 | 29.0497 | 3.0000 | 39.0000 |
| human | committed | 2134 | 32467.7 | 27.8271 | 4.0000 | 54.0000 |
| unknown | no attribution | 602 | 23054.2 | 19.7591 | 9.0000 | 109.0000 |
| collab | committed | 2006 | 21688.4 | 18.5885 | 3.0000 | 45.0000 |
| human | zero committed lines | 440 | 4573.4 | 3.9198 | 3.0000 | 43.0000 |
| vibe | zero committed lines | 34 | 914.9996 | 0.7842 | 5.0000 | 55.5000 |
| collab | zero committed lines | 12 | 83.6970 | 0.0717 | 3.0000 | 28.5000 |

### size_of_abandoned_sessions  (4 rows)

| usd_bucket | abandoned_sessions | usd | median_calls | median_human_turns |
|---|---|---|---|---|
| 1. <0.1 USD | 56 | 0.2997 | 12.0000 | 1.0000 |
| 2. 0.1-1 USD | 229 | 113.4993 | 8.0000 | 2.0000 |
| 3. 1-10 USD | 410 | 1596.8 | 45.5000 | 4.5000 |
| 4. >10 USD | 393 | 26915.8 | 232.0000 | 19.0000 |

### where_do_they_die  (3 rows)

| outcome | sessions | median_position_of_last_prompt | usd_weighted_median_position | usd |
|---|---|---|---|---|
| committed | 7731 | 0.7857 | 0.9736 | 87513.1 |
| no attribution | 563 | 0.9000 | 0.9783 | 23009.0 |
| zero committed lines | 425 | 0.8077 | 0.9804 | 5514.6 |

### most_expensive_abandoned  (20 rows)

| session_id | agent | repo | mode | session_cost_usd | n_calls | n_human_turns | n_tool_calls | outcome |
|---|---|---|---|---|---|---|---|---|
| 2cae28a4-28e8-4bfa-9225-7682543f3664 | claude_code | scottdensmore/MovieSwiftUI | unknown | 1677.6 | 5929 | 342 | 6000 | no attribution |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | codex | evorto-app/app | unknown | 1069.8 | 10592 | 318 | 17033 | no attribution |
| 3f097ff1-5bb6-4622-8cfe-35782dd270ba | claude_code | pcastelo/lock_code_manager | unknown | 988.7759 | 3466 | 450 | 3237 | no attribution |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-ba3d321274cb | codex | evorto-app/app | unknown | 832.6147 | 8223 | 260 | 13181 | no attribution |
| 6629a885-3d0f-45f3-b34c-af9881428368 | claude_code | pcastelo/lock_code_manager | unknown | 700.9331 | 2527 | 266 | 2657 | no attribution |
| f007f8e0-8e15-49f8-9b78-ca4730e9a56f | claude_code | raman325/lock_code_manager | unknown | 676.3657 | 2037 | 133 | 1985 | no attribution |
| cc0f3de4-3b06-47d4-bc8e-3752f9786504 | claude_code | TheurgicDuke771/DataQ | human | 513.8596 | 1826 | 86 | 1786 | zero committed lines |
| a654b6ca-4957-4d7c-8c99-62db313ff0a0 | claude_code | entireio/cli-checkpoints | human | 402.6406 | 1165 | 190 | 1128 | zero committed lines |
| 0bc8148b-2e5a-476e-be1e-cf08b88d6fd8 | claude_code | marin-community/marin | human | 380.7603 | 926 | 167 | 844 | zero committed lines |
| 019df9cd-55af-78a1-ba56-85910d0fd078-6778b9191d07 | codex | entireio/cli-checkpoints | unknown | 374.2183 | 3918 | 184 | 2822 | no attribution |
| 86f7230f-16a2-4201-9dae-105c1789c2c6 | claude_code | scottdensmore/Cakebrew | unknown | 320.9354 | 1043 | 89 | 1020 | no attribution |
| 064836b9-90e4-42d5-aabc-ed5fde831a57 | claude_code | FSM1/cipher-box | unknown | 295.5619 | 673 | 76 | 678 | no attribution |
| 737704b2-0d90-4bb4-bf1c-59b70e20a2e6 | claude_code | fogodev/ars-ui | unknown | 285.4763 | 838 | 14 | 839 | no attribution |
| b1ed7d58-eb6b-498c-931f-1f6f207e13c3 | claude_code | entireio/cli-checkpoints | unknown | 278.8613 | 964 | 40 | 927 | no attribution |
| 9a29d9ba-5e22-4e92-a5d0-017356e28328 | claude_code | entireio/cli-checkpoints | vibe | 277.9281 | 1019 | 72 | 953 | zero committed lines |
| 8619ea54-7ffc-44fb-96ff-4c199b70945e | claude_code | scottdensmore/antigravity-brain-visualizer | unknown | 277.8192 | 689 | 40 | 678 | no attribution |
| 11232391-c5e3-4f6c-9dfc-75ed12f9e103 | claude_code | fogodev/ars-ui | vibe | 267.1650 | 714 | 11 | 705 | zero committed lines |
| 3af9f603-f1ee-4a00-b691-0e66b3030165 | claude_code | jakobtfaber/dsa110-FLITS | unknown | 254.9663 | 1249 | 113 | 1164 | no attribution |
| 019e92f8-84a9-7fc0-bf0e-061072d47c47 | codex | fogodev/ars-ui | unknown | 250.5494 | 1959 | 114 | 3092 | no attribution |
| 019ed138-54c9-72c2-a294-7cd525eddd48 | codex | fogodev/ars-ui | unknown | 249.5899 | 2121 | 107 | 3507 | no attribution |

_T13_abandoned: 0.0s_

## T14 hot files: the files every session has to touch  (`T14_hot_files`)

**Headline**

- **hot_files**: 518
- **pct_of_edits_on_hot_files**: 20.5584
- **median_repo_share_of_edits_in_top_5pct_of_files**: 33.7824
- **pct_hot_file_edits_followed_by_error**: 6.8050
- **pct_cold_file_edits_followed_by_error**: 7.6636
- **edits_total**: 186775

### top30_hot_files  (30 rows)

| repo | file_path_70 | agent | sessions | users | edits | pct_edits_followed_by_error | pct_edits_followed_by_short_correction |
|---|---|---|---|---|---|---|---|
| E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_hooks.go | claude_code | 120 | 8 | 745 | 9.1275 | 50.8725 |
| entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_condensation.go | codex | 100 | 9 | 341 | 4.9853 | 80.3519 |
| henryph24/neuralips26 | main.tex | claude_code | 91 | 1 | 2012 | 3.3797 | 74.7515 |
| armelhbobdad/bmad-module-skill-forge | _bmad-output/implementation-artifacts/sprint-status.yaml | claude_code | 90 | 1 | 223 | 7.1749 | 22.8700 |
| entireio/cli-checkpoints | cmd/entire/cli/explain.go | codex | 86 | 13 | 480 | 6.8750 | 67.5000 |
| entireio/cli-checkpoints | cmd/entire/cli/checkpoint/committed.go | codex | 83 | 9 | 362 | 4.4199 | 75.9669 |
| entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_hooks.go | codex | 83 | 9 | 315 | 7.9365 | 72.6984 |
| FSM1/cipher-box | .planning/STATE.md | claude_code | 83 | 2 | 205 | 6.8293 | 43.9024 |
| E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_condensation.go | claude_code | 76 | 9 | 268 | 8.9552 | 58.2090 |
| cyyeh/duckdb-data-agent | backend/app/agent.py | claude_code | 66 | 1 | 259 | 6.1776 | 70.6564 |
| entireio/cli-checkpoints | cmd/entire/cli/migrate.go | codex | 63 | 6 | 483 | 1.2422 | 72.6708 |
| entireio/cli-checkpoints | cmd/entire/cli/settings/settings.go | codex | 62 | 9 | 165 | 2.4242 | 67.2727 |
| entireio/cli-checkpoints | cmd/entire/cli/strategy/push_common.go | codex | 61 | 7 | 202 | 1.9802 | 59.9010 |
| FSM1/cipher-box | .planning/ROADMAP.md | claude_code | 60 | 2 | 210 | 13.8095 | 50.4762 |
| entireio/cli-checkpoints | cmd/entire/cli/attach.go | codex | 59 | 8 | 209 | 5.2632 | 75.1196 |
| E2E-Solution/cli | cmd/entire/cli/setup.go | claude_code | 52 | 9 | 359 | 14.4847 | 54.5961 |
| cyyeh/duckdb-data-agent | README.md | claude_code | 52 | 1 | 166 | 4.2169 | 78.9157 |
| marcus-sa/brain | schema/surreal-schema.surql | claude_code | 52 | 1 | 152 | 11.8421 | 60.5263 |
| entireio/cli-checkpoints | CLAUDE.md | codex | 52 | 9 | 91 | 7.6923 | 57.1429 |
| E2E-Solution/cli | cmd/entire/cli/strategy/common.go | claude_code | 51 | 10 | 178 | 12.3596 | 59.5506 |
| entireio/cli-checkpoints | cmd/entire/cli/strategy/common.go | codex | 50 | 9 | 139 | 5.7554 | 66.1871 |
| entireio/cli-checkpoints | cmd/entire/cli/resume.go | claude_code | 49 | 7 | 268 | 2.9851 | 77.9851 |
| entireio/cli-checkpoints | cmd/entire/cli/migrate_test.go | codex | 49 | 5 | 193 | 2.5907 | 73.5751 |
| armelhbobdad/bmad-module-skill-forge | package.json | claude_code | 49 | 1 | 102 | 11.7647 | 49.0196 |
| E2E-Solution/cli | cmd/entire/cli/hooks_claudecode_handlers.go | claude_code | 48 | 7 | 237 | 10.9705 | 55.2743 |
| entireio/cli-checkpoints | cmd/entire/cli/explain_test.go | codex | 47 | 8 | 240 | 2.0833 | 75.4167 |
| E2E-Solution/cli | cmd/entire/cli/strategy/auto_commit.go | claude_code | 47 | 10 | 126 | 7.9365 | 50.0000 |
| E2E-Solution/cli | cmd/entire/cli/lifecycle.go | claude_code | 46 | 8 | 184 | 5.9783 | 74.4565 |
| entireio/cli-checkpoints | cmd/entire/cli/checkpoint/v2_committed.go | codex | 46 | 6 | 168 | 8.3333 | 78.5714 |
| armelhbobdad/bmad-module-skill-forge | README.md | claude_code | 46 | 1 | 104 | 13.4615 | 83.6538 |

### concentration_by_repo  (30 rows)

| repo | files | edits | pct_of_edits_in_top_5pct_of_files | pct_of_edits_in_top_20pct_of_files |
|---|---|---|---|---|
| entireio/cli-checkpoints | 2648 | 29389 | 45.0475 | 77.0560 |
| E2E-Solution/cli | 835 | 12369 | 43.7869 | 76.6836 |
| fogodev/ars-ui | 776 | 8707 | 38.5322 | 74.2391 |
| FSM1/cipher-box | 1559 | 6898 | 43.4329 | 70.2522 |
| marcus-sa/brain | 1212 | 6704 | 40.9606 | 69.8986 |
| armelhbobdad/bmad-module-skill-forge | 861 | 6309 | 32.9371 | 62.5773 |
| TheurgicDuke771/DataQ | 892 | 5478 | 43.3552 | 71.4677 |
| evorto-app/app | 290 | 4280 | 68.9953 | 85.6542 |
| dayhaysoos/nimbus | 362 | 3359 | 40.7562 | 75.9155 |
| lightfastai/lightfast | 894 | 3335 | 34.4828 | 65.6072 |
| henryph24/neuralips26 | 271 | 3013 | 82.0777 | 92.4328 |
| moltis-org/moltis | 518 | 2628 | 37.3668 | 67.9604 |
| entireio/git-sync | 176 | 2625 | 46.0952 | 75.7714 |
| ainaive/agentcenter-nuxt | 469 | 2175 | 39.8161 | 67.5402 |
| pcastelo/lock_code_manager | 165 | 2119 | 42.8976 | 76.9231 |
| raman325/lock_code_manager | 227 | 1995 | 35.4887 | 69.1228 |
| cyyeh/duckdb-data-agent | 307 | 1981 | 50.9339 | 78.1928 |
| jakobtfaber/dsa110-FLITS | 527 | 1739 | 33.5825 | 67.6251 |
| blackgirlbytes/planetfall-seed-signalkit | 103 | 1726 | 73.2908 | 90.4403 |
| roo-oliv/monodreams | 349 | 1605 | 45.3583 | 75.2648 |
| InTheCloudDan/family-schedule-agent-conversations | 396 | 1591 | 28.1584 | 58.0767 |
| fortuna/moltis | 254 | 1556 | 41.5810 | 73.3933 |
| BIDEquity/outbid-dirigent | 334 | 1530 | 44.1176 | 76.5359 |
| HMAKT99/cli | 209 | 1489 | 43.4520 | 69.9127 |
| TheUHO/AI-voyager | 270 | 1487 | 41.7619 | 76.5299 |
| scottdensmore/MovieSwiftUI | 294 | 1406 | 45.0925 | 69.9858 |
| marin-community/marin | 199 | 1285 | 40.3891 | 71.9844 |
| heath0xFF/fornax | 137 | 1275 | 47.6078 | 79.1373 |
| enactive/panopt | 84 | 1218 | 45.5665 | 80.4598 |
| Coderx85/wave | 338 | 1198 | 29.0484 | 59.7663 |

### hot_vs_cold  (2 rows)

| heat | files | edits | pct_of_all_edits | avg_pct_edits_followed_by_error | avg_pct_edits_followed_by_short_correction | median_edits_per_file |
|---|---|---|---|---|---|---|
| cold (<10 sessions) | 32096 | 148377 | 79.4416 | 9.2237 | 61.9840 | 2.0000 |
| hot (>=10 sessions) | 518 | 38398 | 20.5584 | 7.6348 | 64.5026 | 47.0000 |

### hot_vs_cold_weighted  (2 rows)

| heat | edits | pct_edits_followed_by_error | pct_edits_followed_by_short_correction |
|---|---|---|---|
| cold (<10 sessions) | 148377 | 7.6636 | 61.2905 |
| hot (>=10 sessions) | 38398 | 6.8050 | 64.9565 |

### edits_by_agent  (4 rows)

| agent | edits | pct_edits_followed_by_error | pct_edits_followed_by_short_correction |
|---|---|---|---|
| claude_code | 154027 | 8.9841 | 62.6332 |
| codex | 25649 | 0.0000 | 57.5500 |
| opencode | 5299 | 2.7552 | 67.6731 |
| cursor | 1800 | 0.0000 | 59.1111 |

_T14_hot_files: 0.3s_

## T15 harness vs model: who is cheaper per committed line  (`T15_harness_vs_model`)

**Headline**

- **repos_with_two_or_more_agents**: 47
- **cheapest_agent_per_committed_line**: opencode
- **cheapest_usd_per_committed_line**: 4.973e-04
- **dearest_agent_per_committed_line**: claude_code
- **dearest_usd_per_committed_line**: 0.0390
- **ratio_dearest_to_cheapest**: 78.4748

### by_agent_model_family  (13 rows)

| agent | model_family | sessions | usd | committed_lines | usd_per_committed_line | ctx_tokens_per_committed_line | output_tokens_per_committed_line |
|---|---|---|---|---|---|---|---|
| claude_code | opus | 1199 | 29173.6 | 630484 | 0.0463 | 61380.6 | 172.3564 |
| codex | gpt-5.5 | 490 | 11493.5 | 116703 | 0.0985 | 137514.1 | 332.5749 |
| codex | gpt-5.4 | 525 | 3038.3 | 316719 | 0.0096 | 20180.5 | 63.0434 |
| claude_code | fable | 38 | 1557.0 | 4233 | 0.3678 | 215798.3 | 820.7012 |
| opencode | gpt-5.3-codex | 499 | 491.2247 | 1069432 | 4.593e-04 | 151.1936 | 5.0335 |
| claude_code | sonnet | 78 | 387.2657 | 29182 | 0.0133 | 24534.3 | 139.7805 |
| codex | gpt-5.3-codex | 40 | 261.2312 | 444704 | 5.874e-04 | 1862.0 | 6.2183 |
| opencode | gpt-5.4 | 57 | 66.6639 | 185527 | 3.593e-04 | 82.6971 | 4.2427 |
| opencode | sonnet | 16 | 17.6679 | 8424 | 0.0021 | 2472.7 | 41.9785 |
| opencode | opus | 10 | 14.9760 | 2090 | 0.0072 | 5348.2 | 37.1670 |
| claude_code | haiku | 18 | 6.1774 | 35125 | 1.759e-04 | 248.1382 | 1.8737 |
| opencode | other | 15 | 0.0000 | 1970 | 0.0000 | 103152.9 | 240.2284 |
| claude_code | unknown | 35 | 0.0000 | 98525 | 0.0000 | 0.0000 | 0.0000 |

### by_mode  (11 rows)

| mode | agent | sessions | usd | committed_lines | usd_per_committed_line |
|---|---|---|---|---|---|
| collab | claude_code | 218 | 5207.3 | 142313 | 0.0366 |
| collab | codex | 203 | 1923.3 | 529876 | 0.0036 |
| collab | opencode | 156 | 152.0423 | 438823 | 3.465e-04 |
| human | claude_code | 347 | 9197.2 | 532882 | 0.0173 |
| human | codex | 233 | 2895.6 | 199477 | 0.0145 |
| human | opencode | 61 | 106.8868 | 88699 | 0.0012 |
| unknown | claude_code | 170 | 6417.7 |  |  |
| unknown | codex | 66 | 2631.3 |  |  |
| vibe | claude_code | 633 | 10301.9 | 122354 | 0.0842 |
| vibe | codex | 555 | 7342.8 | 148836 | 0.0493 |
| vibe | opencode | 378 | 365.8343 | 739953 | 4.944e-04 |

### by_repo_agent  (37 rows)

| repo | agent | sessions | usd | committed_lines | usd_per_committed_line |
|---|---|---|---|---|---|
| AI-Stats/AI-Stats | codex | 25 | 230.7304 | 434824 | 5.306e-04 |
| EntityProcess/agentv | codex | 25 | 589.9084 | 1464 | 0.4029 |
| HMAKT99/cli | claude_code | 120 | 601.5388 | 41427 | 0.0145 |
| JustinBeaudry/kb | claude_code | 26 | 163.9534 | 50905 | 0.0032 |
| SnowingFox/skills | claude_code | 10 | 154.2716 | 444 | 0.3475 |
| basher83/domain-chassis | claude_code | 17 | 15.1557 | 8281 | 0.0018 |
| blackgirlbytes/planetfall-seed-signalkit | codex | 45 | 420.4292 | 4897 | 0.0859 |
| blackgirlbytes/planetfall-seed-signalkit | claude_code | 20 | 366.5595 | 7041 | 0.0521 |
| cmgramse/skill-development | claude_code | 11 | 490.9453 | 4851 | 0.1012 |
| computermode/test-repo | claude_code | 28 | 6.8676 | 156 | 0.0440 |
| dayhaysoos/nimbus | codex | 68 | 568.3794 | 111988 | 0.0051 |
| dayhaysoos/nimbus | opencode | 491 | 470.8853 | 1132498 | 4.158e-04 |
| desplega-ai/agent-swarm | claude_code | 36 | 394.7156 | 56323 | 0.0070 |
| entireio/cli-checkpoints | claude_code | 771 | 18835.5 | 265020 | 0.0711 |
| entireio/cli-checkpoints | codex | 439 | 6583.3 | 143748 | 0.0458 |
| entireio/cli-checkpoints | opencode | 26 | 99.5835 | 3423 | 0.0291 |
| entireio/external-agents | claude_code | 43 | 229.5837 | 27966 | 0.0082 |
| entireio/git-sync | claude_code | 45 | 1429.2 | 4270 | 0.3347 |
| entireio/git-sync | codex | 52 | 359.6207 | 4811 | 0.0747 |
| fogodev/ars-ui | claude_code | 28 | 4480.8 | 78957 | 0.0568 |
| fogodev/ars-ui | codex | 58 | 4251.8 | 43412 | 0.0979 |
| galactica-labs/project-atlas | opencode | 16 | 21.7003 | 67930 | 3.195e-04 |
| geroitscompiling/hackathon_Buena | claude_code | 25 | 0.0000 | 1277 | 0.0000 |
| heath0xFF/fornax | claude_code | 14 | 554.1204 | 3653 | 0.1517 |
| heath0xFF/fornax | opencode | 10 | 7.1612 | 2331 | 0.0031 |
| jakobtfaber/dsa110-FLITS | claude_code | 27 | 1506.2 | 111480 | 0.0135 |
| jakobtfaber/dsa110-FLITS | codex | 22 | 46.1325 | 5068 | 0.0091 |
| lgulliver/derrick | claude_code | 16 | 157.3431 | 20449 | 0.0077 |
| liatrio-labs/ai-prompts | opencode | 30 | 11.8068 | 52531 | 2.248e-04 |
| m0nhawk/incomplete.fun | claude_code | 10 | 11.6244 | 623 | 0.0187 |
| prayashm/agent-lab | claude_code | 11 | 253.5207 | 1335 | 0.1899 |
| savekirk/session-bridge | codex | 18 | 53.8365 | 31349 | 0.0017 |
| ta93abe/me | claude_code | 11 | 91.6751 | 14522 | 0.0063 |
| zchee/agent | codex | 14 | 13.0216 | 55776 | 2.335e-04 |
| zchee/spanner-manager | codex | 142 | 323.0319 | 18365 | 0.0176 |
| zchee/zmux | codex | 86 | 780.2537 | 12143 | 0.0643 |
| zchee/zmux | claude_code | 12 | 202.1363 | 8107 | 0.0249 |

_T15_harness_vs_model: 0.0s_

## T16 subagents: what the sidechains cost (claude_code only)  (`T16_subagents`)

**Headline**

- **sidechain_calls**: 300
- **sidechain_usd**: 2.6247
- **pct_of_claude_code_usd**: 0.0027
- **task_tool_calls**: 20622
- **task_result_chars**: 94441436
- **sessions_using_task**: 3741

### sidechain_share  (4 rows)

| agent | calls | sidechain_calls | pct_calls_sidechain | usd | sidechain_usd | pct_usd_sidechain |
|---|---|---|---|---|---|---|
| claude_code | 677725 | 300 | 0.0443 | 96741.1 | 2.6247 | 0.0027 |
| codex | 218945 | 0 | 0.0000 | 19048.4 |  |  |
| opencode | 27949 | 0 | 0.0000 | 887.1856 |  |  |
| cursor | 8910 | 0 | 0.0000 | 0.0000 |  |  |

### sessions_with_vs_without  (11 rows)

| kind | mode | sessions | usd | pct_sessions_with_commits | committed_lines | usd_per_committed_line | median_session_usd |
|---|---|---|---|---|---|---|---|
| has sidechain calls | human | 2 | 70.0078 | 0.0000 | 0 |  | 35.0039 |
| has sidechain calls | unknown | 1 | 16.3210 | 0.0000 |  |  | 16.3210 |
| has sidechain calls | vibe | 2 | 16.3003 | 100.0000 | 1774 | 0.0092 | 8.1501 |
| no subagents | vibe | 1695 | 8436.5 | 99.3510 | 348337 | 0.0242 | 1.4519 |
| no subagents | human | 1031 | 4737.5 | 81.8623 | 4475237 | 0.0011 | 1.1376 |
| no subagents | collab | 768 | 3483.4 | 99.3490 | 1167242 | 0.0030 | 1.5919 |
| no subagents | unknown | 194 | 2228.5 | 0.0000 |  |  | 2.5803 |
| uses the task tool | human | 1133 | 28644.5 | 89.5852 | 7377744 | 0.0039 | 6.6915 |
| uses the task tool | vibe | 1297 | 17956.9 | 99.4603 | 515761 | 0.0348 | 4.4425 |
| uses the task tool | unknown | 318 | 15863.0 | 0.0000 |  |  | 19.0633 |
| uses the task tool | collab | 789 | 15288.2 | 99.6198 | 1077982 | 0.0142 | 5.3196 |

### task_tool_usage  (4 rows)

| agent | task_calls | sessions | result_chars | median_result_chars | usd_of_the_task_prompts |
|---|---|---|---|---|---|
| claude_code | 17833 | 3542 | 91255520 | 3136.5 | 265.9264 |
| codex | 2235 | 125 | 1810622 | 76.0000 | 8.7531 |
| opencode | 429 | 56 | 1375294 | 1241.0 | 4.1236 |
| cursor | 125 | 18 | 0 |  |  |

_T16_subagents: 0.0s_

## T17 bypass: permission mode and what it buys (claude_code)  (`T17_bypass`)

**Headline**

- **sessions_on_bypass**: 719
- **usd_on_bypass**: 12987.3
- **usd_per_committed_line_bypass**: 0.0243
- **usd_per_committed_line_default**: 0.0476
- **tool_error_rate_pct_bypass**: 3.0391
- **tool_error_rate_pct_default**: 3.2301

### by_permission_mode  (7 rows)

| permission_mode | sessions | usd | committed_lines | usd_per_committed_line | tool_error_rate_pct | tool_calls_per_committed_line | pct_sessions_with_commits | median_session_usd |
|---|---|---|---|---|---|---|---|---|
| no permission-mode events | 5330 | 54038.9 | 13534963 | 0.0040 | 4.0561 | 0.0362 | 90.1126 | 2.4535 |
| bypassPermissions | 719 | 12987.3 | 533617 | 0.0243 | 3.0391 | 0.1511 | 89.7079 | 3.4574 |
| acceptEdits | 360 | 12955.5 | 351892 | 0.0368 | 2.5631 | 0.1914 | 81.1111 | 13.4499 |
| auto | 356 | 9315.6 | 372923 | 0.0250 | 2.5939 | 0.1381 | 83.1461 | 8.9467 |
| default | 437 | 7147.4 | 150170 | 0.0476 | 3.2301 | 0.2626 | 73.6842 | 2.2539 |
| plan | 27 | 295.3327 | 20393 | 0.0145 | 3.6064 | 0.1101 | 92.5926 | 3.3184 |
| dontAsk | 1 | 1.0314 | 119 | 0.0087 | 13.6364 | 0.1849 | 100.0000 | 1.0314 |

### by_permission_mode_and_mode  (20 rows)

| permission_mode | mode | sessions | usd | usd_per_committed_line | tool_error_rate_pct |
|---|---|---|---|---|---|
| acceptEdits | vibe | 158 | 4864.5 | 0.2278 | 2.5299 |
| acceptEdits | human | 99 | 4262.8 | 0.0135 | 2.6344 |
| acceptEdits | unknown | 48 | 1963.9 |  | 2.2414 |
| acceptEdits | collab | 55 | 1864.3 | 0.1173 | 2.8272 |
| auto | vibe | 172 | 3181.5 | 0.0761 | 2.3670 |
| auto | human | 93 | 2843.9 | 0.0108 | 2.6233 |
| auto | unknown | 37 | 1838.9 |  | 2.8817 |
| auto | collab | 54 | 1451.3 | 0.0215 | 2.7529 |
| bypassPermissions | unknown | 58 | 3756.0 |  | 2.8789 |
| bypassPermissions | human | 158 | 3632.6 | 0.0160 | 3.5024 |
| bypassPermissions | collab | 237 | 2938.4 | 0.0136 | 3.3443 |
| bypassPermissions | vibe | 266 | 2660.3 | 0.0294 | 2.4467 |
| default | human | 113 | 3030.7 | 0.0499 | 3.5219 |
| default | collab | 85 | 1513.3 | 0.0252 | 3.4352 |
| default | unknown | 56 | 1441.0 |  | 3.2253 |
| default | vibe | 183 | 1162.4 | 0.0396 | 2.6563 |
| no permission-mode events | human | 1699 | 19525.8 | 0.0018 | 4.4064 |
| no permission-mode events | vibe | 2202 | 14448.6 | 0.0213 | 3.4776 |
| no permission-mode events | collab | 1117 | 10969.4 | 0.0058 | 4.1570 |
| no permission-mode events | unknown | 312 | 9095.0 |  | 4.3100 |

_T17_bypass: 0.0s_

## T18 impatience: interrupts, queued commands and sunk tokens  (`T18_impatience`)

**Headline**

- **interrupts**: 4260
- **sessions_with_at_least_one_interrupt**: 1948
- **usd_sunk_before_interrupts**: 5259.3
- **pct_of_total_usd**: 4.5076
- **usd_per_committed_line_interrupted_sessions**: 0.0083
- **usd_per_committed_line_calm_sessions**: 0.0051
- **queue_operation_events**: 254171

### interrupts_by_agent  (1 rows)

| agent | interrupts | sessions_with_interrupts | sunk_usd | median_sunk_usd | median_sunk_calls | pct_of_total_usd |
|---|---|---|---|---|---|---|
| claude_code | 4260 | 1948 | 5259.3 | 0.4284 | 4.0000 | 4.5076 |

### queue_operations  (1 rows)

| agent | sessions_with_queue_events | queue_events | median_queue_events_per_session |
|---|---|---|---|
| claude_code | 3924 | 254171 | 180606.0 |

### sessions_with_vs_without_interrupts  (8 rows)

| kind | mode | sessions | usd | committed_lines | usd_per_committed_line | median_calls | pct_sessions_with_commits |
|---|---|---|---|---|---|---|---|
| interrupted | human | 714 | 19650.0 | 5660467 | 0.0035 | 98.0000 | 89.3557 |
| interrupted | collab | 479 | 12022.4 | 627228 | 0.0192 | 85.0000 | 100.0000 |
| interrupted | unknown | 200 | 11227.3 |  |  | 198.0000 | 0.0000 |
| interrupted | vibe | 551 | 10163.3 | 133387 | 0.0762 | 80.0000 | 99.4555 |
| never interrupted | vibe | 2443 | 16246.4 | 732485 | 0.0222 | 31.0000 | 99.3860 |
| never interrupted | human | 1452 | 13801.9 | 6192514 | 0.0022 | 30.0000 | 84.0909 |
| never interrupted | unknown | 313 | 6880.5 |  |  | 58.0000 | 0.0000 |
| never interrupted | collab | 1078 | 6749.2 | 1617996 | 0.0042 | 32.0000 | 99.2579 |

_T18_impatience: 0.1s_

## T19 compaction: what gets read again after the context is dropped  (`T19_compaction`)

**Headline**

- **compaction_boundaries**: 2907
- **sessions_with_a_boundary**: 1048
- **reads_in_the_20_tool_calls_after_a_boundary**: 8217
- **pct_of_those_reads_already_seen**: 56.4440
- **reread_chars**: 35346980
- **usd_of_the_rereads_first_pass_only**: 4.2027
- **usd_of_the_rereads_at_cache_write_price**: 52.5342

### boundaries_by_subtype  (3 rows)

| agent | event_kind | boundaries | sessions |
|---|---|---|---|
| claude_code | compact_boundary | 1334 | 720 |
| codex | compacted | 1235 | 302 |
| claude_code | microcompact_boundary | 338 | 45 |

### sessions_with_compaction  (4 rows)

| agent | sessions | sessions_with_a_boundary | pct_sessions_compacted | median_boundaries_when_present | max_boundaries | usd_in_compacted_sessions |
|---|---|---|---|---|---|---|
| claude_code | 7230 | 746 | 10.3181 | 1.0000 | 96 | 36593.4 |
| codex | 1167 | 302 | 25.8783 | 2.0000 | 103 | 16718.2 |
| opencode | 783 | 0 | 0.0000 |  |  |  |
| cursor | 86 | 0 | 0.0000 |  |  |  |

### rereads_after_boundary  (2 rows)

| agent | event_kind | reads_in_next_20_tool_calls | reads_of_already_seen_paths | pct_rereads | reread_chars | reread_usd_one_pass | reread_usd_recached |
|---|---|---|---|---|---|---|---|
| claude_code | compact_boundary | 6968 | 4121 | 59.1418 | 33550476 | 4.0451 | 50.5632 |
| claude_code | microcompact_boundary | 1249 | 517 | 41.3931 | 1796504 | 0.1577 | 1.9709 |

### top_reread_files  (20 rows)

| file_path_80 | rereads_after_a_boundary | sessions | chars |
|---|---|---|---|
| cmd/entire/cli/strategy/manual_commit_hooks.go | 257 | 48 | 1846415 |
| src/rhea_bridge.py | 71 | 4 | 893850 |
| scripts/rhea_query_persist.sh | 52 | 1 | 188644 |
| static/index.html | 51 | 5 | 128889 |
| cmd/entire/cli/strategy/manual_commit_condensation.go | 51 | 26 | 405641 |
| cmd/entire/cli/checkpoint/temporary.go | 43 | 11 | 345666 |
| cmd/entire/cli/hooks_claudecode_handlers.go | 42 | 21 | 864872 |
| /Users/sa/rh.REDACTED.md | 41 | 2 | 32669 |
| cmd/entire/cli/explain.go | 37 | 10 | 480458 |
| src/clio_pipeline/pipeline/run_pipeline.py | 34 | 1 | 54958 |
| src/trading/live_trading.py | 33 | 3 | 101955 |
| cmd/entire/cli/lifecycle.go | 31 | 16 | 261990 |
| cmd/entire/cli/setup.go | 30 | 9 | 360466 |
| client/src/App.tsx | 29 | 4 | 49996 |
| docs/plans/2026-02-06-session-phase-state-machine-v2.md | 29 | 4 | 337395 |
| cmd/entire/cli/resume.go | 26 | 8 | 140268 |
| /Users/sa/rh.1/ops/rhea_firebase.py | 26 | 1 | 37648 |
| cmd/unified-server/public_html/map.html | 26 | 5 | 63540 |
| src/components/UserChat.vue | 23 | 1 | 110781 |
| scribe/src/sync/apply.rs | 23 | 6 | 238109 |

_T19_compaction: 0.1s_

## T20 self reread: reading back what the agent just wrote, and edit thrash  (`T20_self_reread`)

**Headline**

- **reads_of_a_just_written_file**: 23104
- **pct_of_all_reads**: 14.3024
- **reread_chars**: 48831788
- **usd_at_fresh_input_price**: 55.9774
- **edits_inside_a_thrash_window**: 53297
- **pct_of_edits_in_thrash**: 28.5354

### self_rereads  (3 rows)

| agent | reads | reads_within_5_calls_of_a_write | pct_of_reads | reread_chars | usd_fresh_input_price |
|---|---|---|---|---|---|
| claude_code | 143978 | 22334 | 15.5121 | 45897929 | 54.8185 |
| opencode | 15865 | 667 | 4.2042 | 2933859 | 1.1590 |
| cursor | 1696 | 103 | 6.0731 | 0 |  |

### edit_thrash  (4 rows)

| agent | edits | edits_in_a_thrash_window | pct_of_edits | distinct_thrashed_files |
|---|---|---|---|---|
| claude_code | 154027 | 48070 | 31.2088 | 11330 |
| codex | 25649 | 3740 | 14.5815 | 862 |
| opencode | 5299 | 1020 | 19.2489 | 275 |
| cursor | 1800 | 467 | 25.9444 | 113 |

### top_thrashed_files  (20 rows)

| file_path_80 | agent | edits_in_thrash_windows | sessions | worst_burst |
|---|---|---|---|---|
| main.tex | claude_code | 1416 | 74 | 78 |
| static/index.html | claude_code | 437 | 8 | 10 |
| README.md | claude_code | 435 | 128 | 15 |
| cmd/entire/cli/strategy/manual_commit_hooks.go | claude_code | 416 | 94 | 10 |
| docs/progress.md | claude_code | 385 | 27 | 27 |
| src/droneBayView.js | codex | 352 | 13 | 16 |
| cmd/entire/cli/setup.go | claude_code | 328 | 59 | 14 |
| cmd/entire/cli/explain.go | claude_code | 327 | 48 | 10 |
| src/server.zig | claude_code | 272 | 19 | 11 |
| helpers/testing/stabilization-source.spec.ts | codex | 247 | 2 | 6 |
| CLAUDE.md | claude_code | 220 | 66 | 12 |
| cmd/entire/cli/migrate.go | codex | 213 | 34 | 11 |
| src/app.rs | claude_code | 182 | 10 | 13 |
| REDACTED.md | claude_code | 179 | 23 | 15 |
| cmd/entire/cli/trail_cmd.go | claude_code | 175 | 21 | 11 |
| crates/ars-components/src/selection/combobox/mod.rs | codex | 172 | 2 | 10 |
| cmd/entire/cli/checkpoint/committed.go | claude_code | 167 | 37 | 9 |
| cmd/entire/cli/search_tui.go | codex | 164 | 14 | 10 |
| cmd/entire/cli/resume.go | claude_code | 159 | 29 | 10 |
| src/islandView.js | codex | 159 | 12 | 12 |

_T20_self_reread: 0.3s_

## T21 fast mode: does speed=fast change anything (claude_code)  (`T21_fast_mode`)

**Headline**

- **fast_calls**: 4376
- **pct_of_claude_code_calls**: 0.6457
- **fast_usd**: 648.0807
- **pct_of_claude_code_usd**: 0.6699
- **sessions_using_fast**: 42
- **pct_of_calls_without_a_speed_field**: 17.7575

### speed_share  (3 rows)

| speed | calls | pct_of_calls | sessions | usd | pct_of_usd | output_tokens |
|---|---|---|---|---|---|---|
| standard | 553002 | 81.5968 | 6404 | 87855.9 | 90.8155 | 342094262 |
| not recorded | 120347 | 17.7575 | 4222 | 8237.1 | 8.5146 | 6190260 |
| fast | 4376 | 0.6457 | 42 | 648.0807 | 0.6699 | 3312659 |

### fast_sessions_vs_standard  (2 rows)

| kind | sessions | median_agent_time_s_per_turn | usd | usd_per_committed_line |
|---|---|---|---|---|
| never fast | 6921 | 99.1130 | 94441.1 | 0.0064 |
| uses fast | 38 | 143.0765 | 1729.7 | 0.0585 |

### fast_by_month  (7 rows)

| month | fast_calls | calls | pct_fast | fast_usd |
|---|---|---|---|---|
| 2026-01-01 00:00:00 | 0 | 11671 | 0.0000 |  |
| 2026-02-01 00:00:00 | 0 | 117168 | 0.0000 |  |
| 2026-03-01 00:00:00 | 0 | 175098 | 0.0000 |  |
| 2026-04-01 00:00:00 | 1518 | 151956 | 0.9990 | 238.8847 |
| 2026-05-01 00:00:00 | 132 | 106288 | 0.1242 | 10.3199 |
| 2026-06-01 00:00:00 | 2726 | 95753 | 2.8469 | 398.8761 |
| 2026-07-01 00:00:00 | 0 | 15027 | 0.0000 |  |

_T21_fast_mode: 0.0s_

## T22 model switch: the same person, the same repo, a different model  (`T22_model_switch`)

**Headline**

- **user_repo_pairs_that_switched_models**: 93
- **models_involved**: 23
- **sessions**: 6419
- **usd**: 77343.1
- **usd_per_committed_line_overall**: 0.0100
- **median_dearest_to_cheapest_ratio_within_a_pair**: 8.4724

### pairs  (248 rows)

| user_hash | repo | session_model | sessions | usd | committed_lines | usd_per_committed_line | ctx_tokens_per_committed_line |
|---|---|---|---|---|---|---|---|
| 0161eecd96 | ashtom/react-split-flap-display | gpt-5.5 | 3 | 120.8654 | 119 | 1.0157 | 1489220.0 |
| 0161eecd96 | ashtom/react-split-flap-display | claude-opus-4-8 | 4 | 86.5601 | 297 | 0.2914 | 309238.6 |
| 0161eecd96 | entireio/cli-checkpoints | claude-opus-4-7 | 4 | 185.9545 | 213 | 0.8730 | 1226611.6 |
| 0161eecd96 | entireio/cli-checkpoints | gpt-5.4 | 10 | 17.2217 | 1868 | 0.0092 | 24235.3 |
| 0267d3edb4 | vancityAyush/sshx | gpt-5.4 | 4 | 8.2677 | 0 |  |  |
| 0267d3edb4 | vancityAyush/sshx | claude-sonnet-4-6 | 4 | 8.0137 | 951 | 0.0084 | 14976.8 |
| 02a76a9b19 | m0nhawk/incomplete.fun | gpt-5.5 | 9 | 14.1205 | 4555 | 0.0031 | 3115.6 |
| 02a76a9b19 | m0nhawk/incomplete.fun | claude-sonnet-4-6 | 10 | 11.6244 | 623 | 0.0187 | 26844.9 |
| 04788c4f52 | parthjeet/taskflow | claude-opus-4-6 | 10 | 50.8874 | 152044 | 3.347e-04 | 424.6209 |
| 04788c4f52 | parthjeet/taskflow | claude-sonnet-4-6 | 22 | 30.7031 | 38244 | 8.028e-04 | 1083.7 |
| 051a9911de | BIDEquity/outbid-dirigent | claude-opus-4-7 | 24 | 673.6661 | 47989 | 0.0140 | 16047.0 |
| 051a9911de | BIDEquity/outbid-dirigent | claude-opus-4-6 | 15 | 350.4340 | 19629 | 0.0179 | 21592.3 |
| 051a9911de | BIDEquity/outbid-dirigent | claude-opus-4-8 | 7 | 78.5537 | 35196 | 0.0022 | 1316.5 |
| 051a9911de | BIDEquity/outbid-dirigent | claude-sonnet-4-6 | 8 | 20.2717 | 2860 | 0.0071 | 11408.8 |
| 051a9911de | BIDEquity/outbid-dirigent | claude-haiku-4-5-20251001 | 4 | 1.7601 | 357 | 0.0049 | 28050.1 |
| 0938f59cc7 | 135yshr/documents | claude-opus-4-6 | 51 | 269.3525 | 53512 | 0.0050 | 6228.5 |
| 0938f59cc7 | 135yshr/documents | claude-opus-4-7 | 4 | 47.2340 | 67 | 0.7050 | 1082126.5 |
| 0938f59cc7 | 135yshr/documents | claude-sonnet-4-6 | 10 | 19.7383 | 157 | 0.1257 | 193821.0 |
| 0b30293d06 | baotoq/micro-commerce | claude-opus-4-6 | 19 | 43.3525 | 28889 | 0.0015 | 1446.7 |
| 0b30293d06 | baotoq/micro-commerce | claude-sonnet-4-6 | 10 | 13.5226 | 6765 | 0.0020 | 3793.6 |
| 0ea4a0db01 | entireio/cli-checkpoints | claude-opus-4-7 | 19 | 188.8129 | 1105 | 0.1709 | 196289.8 |
| 0ea4a0db01 | entireio/cli-checkpoints | claude-opus-4-6 | 28 | 162.4005 | 5045 | 0.0322 | 44435.3 |
| 0ea4a0db01 | entireio/cli-checkpoints | gpt-5.5 | 15 | 119.1597 | 22502 | 0.0053 | 7451.5 |
| 0ea4a0db01 | entireio/cli-checkpoints | gpt-5.4 | 17 | 59.1992 | 2173 | 0.0272 | 59828.4 |
| 0ea4a0db01 | entireio/cli-checkpoints | claude-opus-4-8 | 4 | 35.0528 | 38 | 0.9224 | 862478.2 |
| 106bf3191c | galactica-labs/project-atlas | claude-sonnet-4-6 | 8 | 21.1444 | 4926 | 0.0043 | 8412.5 |
| 106bf3191c | galactica-labs/project-atlas | claude-sonnet-4.6 | 11 | 11.2422 | 6598 | 0.0017 | 1951.6 |
| 1237ff3ed0 | pc035860/agent-tail | claude-opus-4-7 | 7 | 517.9517 | 922 | 0.5618 | 761265.7 |
| 1237ff3ed0 | pc035860/agent-tail | claude-opus-4-6 | 13 | 153.5708 | 4723 | 0.0325 | 50234.3 |
| 1237ff3ed0 | pc035860/cee | claude-opus-4-6 | 18 | 95.1887 | 1364 | 0.0698 | 78267.6 |
| 1237ff3ed0 | pc035860/cee | claude-sonnet-4-6 | 13 | 28.2040 | 601 | 0.0469 | 70964.0 |
| 1237ff3ed0 | pc035860/cee | glm-5 | 4 | 0.0000 | 287 | 0.0000 | 223296.2 |
| 171ca65f38 | dayhaysoos/nimbus | gpt-5.4 | 78 | 586.2250 | 173271 | 0.0034 | 7619.0 |
| 171ca65f38 | dayhaysoos/nimbus | gpt-5.3-codex | 481 | 453.0396 | 1071215 | 4.229e-04 | 208.5532 |
| 18ed86d074 | blackgirlbytes/planetfall-seed-signalkit | gpt-5.5 | 45 | 420.4292 | 4897 | 0.0859 | 94070.6 |
| 18ed86d074 | blackgirlbytes/planetfall-seed-signalkit | claude-opus-4-8 | 11 | 222.3882 | 5808 | 0.0383 | 42768.5 |
| 18ed86d074 | blackgirlbytes/planetfall-seed-signalkit | claude-fable-5 | 5 | 143.2699 | 944 | 0.1518 | 77911.0 |
| 18ed86d074 | blackgirlbytes/planetfall-seed-signalkit | claude-sonnet-4-6 | 4 | 0.9014 | 289 | 0.0031 | 3256.3 |
| 1a4c5ee96d | petercr/ccw | claude-sonnet-4-6 | 7 | 12.0484 | 666 | 0.0181 | 23514.6 |
| 1a4c5ee96d | petercr/ccw | claude-opus-4-6 | 3 | 9.1900 | 140 | 0.0656 | 83805.6 |

_248 rows total, 40 shown._

### model_totals_within_switchers  (23 rows)

| session_model | user_repo_cells | sessions | usd | committed_lines | usd_per_committed_line | output_tokens_per_committed_line |
|---|---|---|---|---|---|---|
| claude-opus-4-7 | 39 | 1042 | 22032.9 | 721005 | 0.0306 | 114.7089 |
| claude-opus-4-8 | 35 | 521 | 18168.8 | 480266 | 0.0378 | 180.1854 |
| claude-opus-4-6 | 58 | 2469 | 16951.9 | 3495519 | 0.0048 | 15.9595 |
| gpt-5.5 | 15 | 430 | 10501.6 | 111890 | 0.0939 | 312.5802 |
| claude-fable-5 | 10 | 59 | 3518.9 | 24819 | 0.1418 | 293.2113 |
| gpt-5.4 | 17 | 485 | 2956.5 | 300601 | 0.0098 | 62.0604 |
| claude-opus-4-5-20251101 | 6 | 174 | 1335.9 | 389831 | 0.0034 | 2.8246 |
| claude-sonnet-4-6 | 37 | 415 | 955.4388 | 740866 | 0.0013 | 11.2272 |
| gpt-5.3-codex | 4 | 527 | 547.6270 | 1095554 | 4.999e-04 | 5.2593 |
| claude-sonnet-4-5-20250929 | 6 | 81 | 312.2147 | 297504 | 0.0010 | 2.4062 |
| claude-haiku-4-5-20251001 | 6 | 52 | 27.3752 | 47719 | 5.737e-04 | 3.5112 |
| claude-sonnet-4.6 | 1 | 11 | 11.2422 | 6598 | 0.0017 | 36.3888 |
| gpt-5.4-mini | 3 | 41 | 10.0026 | 6258 | 0.0016 | 87.3790 |
| anthropic/claude-opus-4.6 | 1 | 5 | 6.9751 | 1291 | 0.0054 | 19.3315 |
| claude-haiku-4.5 | 1 | 3 | 4.8482 | 922 | 0.0053 | 220.4469 |
| gpt-5.3-codex-spark | 1 | 4 | 0.9265 | 263 | 0.0035 | 51.0076 |
| glm-5 | 2 | 18 | 0.0000 | 10988 | 0.0000 | 22.5483 |
| glm-5.1 | 1 | 4 | 0.0000 | 1893 | 0.0000 | 28.3782 |
| gemini-3.1-pro-preview | 1 | 25 | 0.0000 | 2856 | 0.0000 | 28.0298 |
| google/gemini-3.1-pro-preview | 1 | 4 | 0.0000 | 1039 | 0.0000 | 22.4735 |
| mimo-v2.5-free | 1 | 9 | 0.0000 | 12519 | 0.0000 | 21.5236 |
| nemotron-3-super-free | 1 | 4 | 0.0000 | 1996 | 0.0000 | 5.9464 |
| big-pickle | 1 | 36 | 0.0000 | 15890 | 0.0000 | 66.0527 |

### within_pair_comparison  (30 rows)

| user_hash | repo | cheapest_model | cheapest_usd_per_line | dearest_model | dearest_usd_per_line | ratio |
|---|---|---|---|---|---|---|
| 61d088a119 | entireio/cli-checkpoints | gpt-5.4-mini | 0.0016 | gpt-5.5 | 0.5885 | 373.8646 |
| e444727853 | JustinBeaudry/kb | claude-haiku-4-5-20251001 | 4.167e-05 | claude-opus-4-7 | 0.0088 | 210.5647 |
| 0ea4a0db01 | entireio/cli-checkpoints | gpt-5.5 | 0.0053 | claude-opus-4-8 | 0.9224 | 174.1933 |
| dddf0ac818 | SnowingFox/skills | gpt-5.4 | 0.0084 | claude-opus-4-6 | 1.4289 | 169.9337 |
| ffad3509ca | E2E-Solution/cli | claude-opus-4-6 | 0.0068 | claude-opus-4-5-20251101 | 1.1172 | 163.5318 |
| 0938f59cc7 | 135yshr/documents | claude-opus-4-6 | 0.0050 | claude-opus-4-7 | 0.7050 | 140.0587 |
| 760061f6bf | Safecast/safecast-new-map | claude-sonnet-4-5-20250929 | 2.682e-04 | claude-opus-4-6 | 0.0285 | 106.4299 |
| 0161eecd96 | entireio/cli-checkpoints | gpt-5.4 | 0.0092 | claude-opus-4-7 | 0.8730 | 94.6951 |
| b2e68a9749 | entireio/git-sync | claude-opus-4-7 | 0.0015 | claude-opus-4-8 | 0.1311 | 85.3599 |
| bea79cf809 | itsmaleen/dispatch | claude-opus-4-5-20251101 | 2.242e-04 | claude-sonnet-4-5-20250929 | 0.0187 | 83.5962 |
| fd678cccd6 | entireio/cli-checkpoints | claude-opus-4-6 | 0.0023 | claude-opus-4-7 | 0.1832 | 79.0251 |
| 3a47328bc0 | zchee/zmux | gpt-5.4-mini | 8.771e-04 | gpt-5.4 | 0.0691 | 78.8053 |
| 758e971770 | YESS-lab/s26_3_31_class_and_guide | claude-sonnet-4-5-20250929 | 5.526e-04 | claude-opus-4-6 | 0.0389 | 70.3502 |
| 926e27eecd | pskoett/pskoett-ai-skills | claude-opus-4-7 | 0.0028 | claude-opus-4-6 | 0.1511 | 53.5837 |
| 8a0594d4b8 | adrientaudiere/MiscMetabar | claude-sonnet-4-6 | 3.018e-04 | claude-opus-4-8 | 0.0153 | 50.6085 |
| 18ed86d074 | blackgirlbytes/planetfall-seed-signalkit | claude-sonnet-4-6 | 0.0031 | claude-fable-5 | 0.1518 | 48.6608 |
| e5afd70a0a | wodsmith/thewodapp | claude-opus-4-7 | 0.0022 | claude-fable-5 | 0.1003 | 46.2148 |
| 8d7b914e55 | ta93abe/me | claude-opus-4-6 | 0.0059 | claude-opus-4-8 | 0.2009 | 34.2299 |
| 5a4134dfc3 | 1natsu-vacation/agent-skills | claude-opus-4-6 | 0.0261 | claude-opus-4-8 | 0.7965 | 30.4722 |
| 6c63212ab4 | entireio/cli-checkpoints | claude-opus-4-8 | 0.0653 | claude-fable-5 | 1.9379 | 29.6906 |
| 51dc30ddc4 | entireio/cli-checkpoints | gpt-5.4 | 0.0219 | gpt-5.5 | 0.6210 | 28.4071 |
| cc0b9cb559 | InTheCloudDan/family-schedule-agent-conversations | claude-opus-4-7 | 0.0045 | claude-fable-5 | 0.1258 | 27.9594 |
| e6ac3dbbab | entireio/git-sync | gpt-5.5 | 0.0365 | claude-opus-4-7 | 0.9271 | 25.4203 |
| c60a241074 | s4lly/splitzy | claude-sonnet-4-6 | 0.0166 | claude-opus-4-8 | 0.3536 | 21.3431 |
| 26b3d0d892 | armelhbobdad/bmad-module-skill-forge | claude-opus-4-6 | 0.0085 | claude-opus-4-8 | 0.1694 | 19.8648 |
| 39a01e366f | entireio/cli-checkpoints | claude-opus-4-6 | 0.0403 | claude-opus-4-7 | 0.7680 | 19.0723 |
| e6ac3dbbab | entireio/cli-checkpoints | claude-opus-4-6 | 0.0286 | claude-fable-5 | 0.5450 | 19.0380 |
| fd678cccd6 | computermode/test-repo | claude-opus-4-6 | 0.0244 | claude-opus-4-8 | 0.4608 | 18.8464 |
| ddbb20c557 | basher83/domain-chassis | claude-haiku-4-5-20251001 | 1.577e-04 | claude-opus-4-6 | 0.0029 | 18.4802 |
| 9ea3e7bea0 | entireio/cli-checkpoints | claude-opus-4-8 | 0.0173 | claude-opus-4-7 | 0.3092 | 17.9156 |

_T22_model_switch: 0.0s_

## T23 local hour: night coding (codex only, it is the only harness with a timezone)  (`T23_local_hour`)

**Headline**

- **codex_sessions_with_a_timezone**: 1167
- **pct_of_sessions_started_at_night**: 11.9109
- **pct_of_codex_usd_spent_at_night**: 10.1960
- **abandonment_rate_pct_night**: 23.0216
- **abandonment_rate_pct_day**: 17.4136
- **usd_per_committed_line_night**: 0.0493
- **usd_per_committed_line_day**: 0.0117
- **median_session_usd_night**: 2.2668

### sessions_per_local_hour  (24 rows)

| local_hour | sessions | usd | tool_error_rate_pct | abandonment_rate_pct | usd_per_committed_line |
|---|---|---|---|---|---|
| 0 | 31 | 585.2850 | 0.0000 | 22.5806 | 0.0666 |
| 1 | 41 | 299.8633 | 0.0000 | 14.6341 | 0.0142 |
| 2 | 23 | 571.8709 | 0.0000 | 26.0870 | 0.1171 |
| 3 | 9 | 99.4123 | 0.0000 | 66.6667 | 0.2291 |
| 4 | 15 | 295.6045 | 0.0000 | 33.3333 | 0.2680 |
| 5 | 20 | 90.1469 | 0.0000 | 10.0000 | 0.0289 |
| 6 | 11 | 62.7355 | 0.0000 | 18.1818 | 0.0333 |
| 7 | 18 | 129.9774 | 0.0000 | 11.1111 | 0.0296 |
| 8 | 39 | 842.9091 | 0.0000 | 12.8205 | 0.0403 |
| 9 | 55 | 3204.8 | 0.0000 | 18.1818 | 0.0800 |
| 10 | 79 | 1100.3 | 0.0000 | 16.4557 | 0.0282 |
| 11 | 87 | 970.1497 | 0.0000 | 17.2414 | 0.0413 |
| 12 | 50 | 659.7084 | 0.0000 | 18.0000 | 0.0194 |
| 13 | 111 | 2152.8 | 0.0000 | 24.3243 | 0.0041 |
| 14 | 88 | 1620.7 | 0.0000 | 14.7727 | 0.0315 |
| 15 | 83 | 1484.7 | 0.0000 | 12.0482 | 0.0203 |
| 16 | 84 | 1492.6 | 0.0000 | 17.8571 | 0.0808 |
| 17 | 76 | 506.8317 | 0.0000 | 19.7368 | 0.0013 |
| 18 | 53 | 857.7616 | 0.0000 | 18.8679 | 0.0253 |
| 19 | 42 | 61.4249 | 0.0000 | 4.7619 | 0.0011 |
| 20 | 35 | 274.2169 | 0.0000 | 8.5714 | 0.0133 |
| 21 | 28 | 390.9810 | 0.0000 | 21.4286 | 0.0262 |
| 22 | 49 | 996.5861 | 0.0000 | 10.2041 | 0.0493 |
| 23 | 40 | 297.1427 | 0.0000 | 10.0000 | 0.0135 |

### by_hour_bucket  (3 rows)

| hour_bucket | sessions | pct_of_sessions | usd | tool_error_rate_pct | abandonment_rate_pct | usd_per_committed_line | median_session_usd |
|---|---|---|---|---|---|---|---|
| 1. night 0-6 | 139 | 11.9109 | 1942.2 | 0.0000 | 23.0216 | 0.0493 | 2.2668 |
| 2. day 6-18 | 781 | 66.9237 | 14228.1 | 0.0000 | 17.4136 | 0.0117 | 2.5599 |
| 3. evening 18-24 | 247 | 21.1654 | 2878.1 | 0.0000 | 12.1457 | 0.0173 | 1.5547 |

### by_timezone  (22 rows)

| timezone | offset_min | sessions | usd | pct_started_at_night |
|---|---|---|---|---|
| America/Los_Angeles | -420 | 261 | 4152.7 | 0.7663 |
| Asia/Tokyo | 540 | 248 | 1138.4 | 25.0000 |
| Europe/Berlin | 120 | 221 | 5470.8 | 9.9548 |
| America/New_York | -240 | 181 | 2766.2 | 12.7072 |
| America/Sao_Paulo | -180 | 58 | 4251.8 | 20.6897 |
| Etc/UTC | 0 | 33 | 185.2197 | 12.1212 |
| Europe/London | 60 | 29 | 276.8277 | 0.0000 |
| Europe/Paris | 120 | 29 | 176.2764 | 0.0000 |
| Europe/Madrid | 120 | 20 | 149.2096 | 0.0000 |
| Europe/Athens | 180 | 18 | 131.1177 | 0.0000 |
| Africa/Nairobi | 180 | 18 | 53.8365 | 33.3333 |
| Asia/Kolkata | 330 | 16 | 71.1502 | 50.0000 |
| America/Chicago | -300 | 12 | 17.0399 | 0.0000 |
| Europe/Stockholm | 120 | 5 | 12.9006 | 0.0000 |
| America/Toronto | -240 | 3 | 7.9547 | 0.0000 |
| Europe/Brussels | 120 | 3 | 5.9436 | 0.0000 |
| Australia/Melbourne | 600 | 3 | 61.5285 | 0.0000 |
| Asia/Shanghai | 480 | 2 | 77.4748 | 0.0000 |
| Europe/Amsterdam | 120 | 2 | 31.9380 | 0.0000 |
| Asia/Karachi | 300 | 2 | 7.6696 | 0.0000 |
| Europe/Rome | 120 | 2 | 1.7873 | 0.0000 |
| America/Denver | -360 | 1 | 0.6881 | 0.0000 |

_T23_local_hour: 0.0s_

## T24 harness whisper: how much of the prompt side the harness writes itself  (`T24_harness_whisper`)

**Headline**

- **harness_attachment_chars**: 376770182
- **human_typed_chars**: 126243011
- **pct_of_prompt_side_written_by_the_harness**: 74.9026
- **harness_attachment_tokens**: 94192545.5
- **all_event_payload_chars**: 5281426819
- **attachment_events**: 235503

### injected_by_subtype  (30 rows)

| agent | event_type | subtype | events | payload_chars | payload_tokens | median_payload_chars |
|---|---|---|---|---|---|---|
| claude_code | progress | progress | 1359488 | 2958147779 | 739536944.8 | 665.0000 |
| claude_code | user_image | user_image | 2027 | 633510771 | 158377692.8 | 203035.0 |
| codex | event_msg | exec_command_end | 65269 | 252308000 | 63077000.0 | 2299.0 |
| codex | compacted | compacted | 1235 | 221784334 | 55446083.5 | 69553.0 |
| codex | turn_context | workspace-write | 8841 | 161987788 | 40496947.0 | 8636.0 |
| claude_code | file-history-snapshot | file-history-snapshot | 105433 | 159913216 | 39978304.0 | 779.0000 |
| claude_code | attachment | hook_success | 119287 | 155553096 | 38888274.0 | 311.0000 |
| claude_code | queue-operation | queue-operation | 122136 | 119357930 | 29839482.5 | 572.0000 |
| codex | event_msg | patch_apply_end | 23578 | 57052190 | 14263047.5 | 1323.0 |
| codex | event_msg | mcp_tool_call_end | 5533 | 56160350 | 14040087.5 | 911.0000 |
| codex | session_meta | openai | 2616 | 54644427 | 13661106.8 | 21335.0 |
| codex | turn_context | danger-full-access | 4105 | 46596590 | 11649147.5 | 1562.0 |
| claude_code | attachment | skill_listing | 3086 | 44787071 | 11196767.8 | 10906.0 |
| codex | response_item | message:developer | 2282 | 39055732 | 9763933.0 | 10894.0 |
| codex | event_msg | agent_message | 114591 | 33590316 | 8397579.0 | 191.0000 |
| codex | event_msg | thread_goal_updated | 35750 | 30323140 | 7580785.0 | 852.0000 |
| claude_code | attachment | deferred_tools_delta | 4200 | 26906083 | 6726520.8 | 3762.0 |
| claude_code | attachment | edited_text_file | 4578 | 24170802 | 6042700.5 | 6779.5 |
| claude_code | attachment | async_hook_response | 23714 | 21919943 | 5479985.8 | 366.0000 |
| claude_code | attachment | task_reminder | 32132 | 18728445 | 4682111.2 | 51.0000 |
| claude_code | attachment | file | 1785 | 15877741 | 3969435.2 | 6032.0 |
| claude_code | attachment | queued_command | 4297 | 14984713 | 3746178.2 | 453.0000 |
| codex | event_msg | task_complete | 10550 | 14863037 | 3715759.2 | 1215.0 |
| claude_code | attachment | diagnostics | 6205 | 11936240 | 2984060.0 | 1571.0 |
| claude_code | attachment | hook_additional_context | 6936 | 10030254 | 2507563.5 | 442.0000 |
| claude_code | system | local_command | 3980 | 9965918 | 2491479.5 | 130.0000 |
| claude_code | attachment | agent_listing_delta | 751 | 8191192 | 2047798.0 | 7726.0 |
| claude_code | last-prompt | last-prompt | 78910 | 7480050 | 1870012.5 | 77.0000 |
| claude_code | attachment | mcp_instructions_delta | 2389 | 6637601 | 1659400.2 | 2192.0 |
| claude_code | pr-link | pr-link | 28992 | 6370057 | 1592514.2 | 220.0000 |

### injected_vs_human_by_agent  (4 rows)

| agent | injected_chars | attachment_chars | human_chars | pct_injected_of_prompt_side | pct_attachments_of_prompt_side |
|---|---|---|---|---|---|
| claude_code | 4283189782 | 376770182 | 69592473 | 98.4012 | 84.4090 |
| codex | 992233306 |  | 48931372 | 95.3003 |  |
| opencode | 5996978 |  | 7084458 | 45.8434 |  |
| cursor | 6753 |  | 634708 | 1.0528 |  |

### by_version_claude_code  (43 rows)

| harness_version | vkey | sessions | attachment_chars_per_session | human_chars_per_session | pct_injected |
|---|---|---|---|---|---|
| 2.1.17 | [2, 1, 17] | 54 |  | 15236.6 |  |
| 2.1.34 | [2, 1, 34] | 56 |  | 7121.5 |  |
| 2.1.37 | [2, 1, 37] | 74 |  | 11774.7 |  |
| 2.1.39 | [2, 1, 39] | 112 |  | 14211.6 |  |
| 2.1.42 | [2, 1, 42] | 149 |  | 16028.6 |  |
| 2.1.44 | [2, 1, 44] | 57 |  | 11313.9 |  |
| 2.1.45 | [2, 1, 45] | 117 |  | 8059.7 |  |
| 2.1.47 | [2, 1, 47] | 125 |  | 5352.6 |  |
| 2.1.49 | [2, 1, 49] | 140 |  | 5193.1 |  |
| 2.1.50 | [2, 1, 50] | 181 |  | 12453.8 |  |
| 2.1.52 | [2, 1, 52] | 162 |  | 5816.9 |  |
| 2.1.56 | [2, 1, 56] | 58 |  | 11512.9 |  |
| 2.1.59 | [2, 1, 59] | 114 |  | 12246.2 |  |
| 2.1.62 | [2, 1, 62] | 224 |  | 5250.5 |  |
| 2.1.63 | [2, 1, 63] | 387 |  | 6483.2 |  |
| 2.1.69 | [2, 1, 69] | 63 |  | 8863.5 |  |
| 2.1.70 | [2, 1, 70] | 277 |  | 5851.4 |  |
| 2.1.71 | [2, 1, 71] | 184 |  | 6150.4 |  |
| 2.1.72 | [2, 1, 72] | 113 |  | 7922.9 |  |
| 2.1.74 | [2, 1, 74] | 84 |  | 7848.7 |  |
| 2.1.75 | [2, 1, 75] | 145 |  | 4706.0 |  |
| 2.1.76 | [2, 1, 76] | 93 |  | 11275.1 |  |
| 2.1.78 | [2, 1, 78] | 58 |  | 14394.3 |  |
| 2.1.79 | [2, 1, 79] | 273 |  | 17695.9 |  |
| 2.1.80 | [2, 1, 80] | 75 |  | 9736.3 |  |
| 2.1.81 | [2, 1, 81] | 174 | 3.2356 | 13097.3 | 0.0247 |
| 2.1.84 | [2, 1, 84] | 55 |  | 6307.5 |  |
| 2.1.87 | [2, 1, 87] | 65 | 809.6923 | 10581.4 | 7.1081 |
| 2.1.89 | [2, 1, 89] | 57 | 25.7895 | 6589.1 | 0.3899 |
| 2.1.91 | [2, 1, 91] | 57 | 11941.9 | 5950.8 | 66.7416 |
| 2.1.92 | [2, 1, 92] | 169 | 11221.9 | 6313.8 | 63.9945 |
| 2.1.112 | [2, 1, 112] | 53 | 277724.1 | 4472.8 | 98.4150 |
| 2.1.114 | [2, 1, 114] | 143 | 80398.3 | 3254.8 | 96.1091 |
| 2.1.116 | [2, 1, 116] | 57 | 157913.4 | 5334.4 | 96.7323 |
| 2.1.118 | [2, 1, 118] | 92 | 43146.3 | 3007.0 | 93.4848 |
| 2.1.119 | [2, 1, 119] | 195 | 106575.8 | 6609.9 | 94.1601 |
| 2.1.126 | [2, 1, 126] | 66 | 87926.6 | 5667.9 | 93.9442 |
| 2.1.128 | [2, 1, 128] | 51 | 390899.8 | 2078.4 | 99.4711 |
| 2.1.139 | [2, 1, 139] | 59 | 55525.8 | 5887.5 | 90.4132 |
| 2.1.143 | [2, 1, 143] | 67 | 209779.6 | 5813.3 | 97.3036 |

_43 rows total, 40 shown._

### per_session_distribution  (4 rows)

| agent | sessions | median_attachment_chars_per_session | p90_attachment_chars_per_session | max_attachment_chars |
|---|---|---|---|---|
| claude_code | 7204 | 46529.0 | 248493.2 | 13718630 |
| codex | 1240 |  |  |  |
| opencode | 233 |  |  |  |
| cursor | 19 |  |  |  |

_T24_harness_whisper: 0.2s_

## C01 case file: Write calls on files that were already in context  (`C01_rewrite_necessary`)

**Headline**

- **pool_of_writes_on_known_files**: 6282
- **content_chars_in_pool**: 32625868
- **output_usd_in_pool**: 186.5236
- **median_content_chars**: 3341.5
- **sessions_in_pool**: 1906

### rewrite_necessary  (600 rows)

| session_id | seq | k_before | k_after | agent | mode | repo | file_path | content_chars | input_chars | max_earlier_read_chars | rewrite_ratio | output_usd_estimate | stratum_pick | stratum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2cae28a4-28e8-4bfa-9225-7682543f3664 | 19422 | 10 | 5 | claude_code | unknown | scottdensmore/MovieSwiftUI | MovieSwift/Packages/Backend/Tests/BackendTests/APIServiceTests.swift | 15988 | 16716 | 5831 | 2.7419 | 0.0999 | random | claude_code\|unknown |
| 492f3e72-6fd6-4a75-95a5-abf3069e973d | 1047 | 10 | 5 | claude_code | vibe | Bio1988/moltisown | crates/web/ui/e2e/specs/sandboxes.spec.js | 15647 | 17790 | 21313 | 0.7342 | 0.0978 | random | claude_code\|vibe |
| 9b854080-5799-41cb-91c1-a3714b4bb75f | 285 | 10 | 5 | claude_code | human | E2E-Solution/cli | docs/architecture/hunk-level-carry-forward.md | 14738 | 16003 | 9877 | 1.4922 | 0.0921 | random | claude_code\|human |
| f5bbbbab-b049-423c-b432-d5c155a5b347 | 192 | 10 | 5 | claude_code | unknown | frank-fs/frank | kitty-specs/001-semantic-resources-phase1/spec.md | 14549 | 14869 | 126 | 115.4683 | 0.0909 | random | claude_code\|unknown |
| 97b27f7f-6011-4ba8-a387-df80a0d0f427 | 1436 | 10 | 5 | claude_code | human | marcus-sa/brain | docs/feature/intent-gated-mcp/deliver/roadmap.json | 14096 | 14934 | 3826 | 3.6843 | 0.0881 | random | claude_code\|human |
| 6ba200ff-f026-498c-b12d-b94ef255458f-0bf88dbfc3e5 | 1008 | 10 | 5 | cursor | human | Toubat/arche | /Users/toubatbrian/.cursor/projects/Users-toubatbrian-Documents-GitHub-arche/canvases/waiterqueue-explainer.canvas.tsx | 12814 | 13516 |  |  |  | random | cursor\|human |
| eb35d8bf-ebc6-4c6c-8eb9-acfcee60f19c | 1057 | 10 | 5 | claude_code | human | fortuna/moltis | website/scripts/build-changelog.mjs | 12783 | 13706 | 11050 | 1.1568 | 0.0799 | random | claude_code\|human |
| f5bbbbab-b049-423c-b432-d5c155a5b347 | 5335 | 10 | 5 | claude_code | unknown | frank-fs/frank | specs/002-phase1-fixes/spec.md | 12201 | 12482 | 4772 | 2.5568 | 0.0763 | random | claude_code\|unknown |
| d6c99475-e176-4546-b57b-ce910f802481 | 364 | 10 | 5 | claude_code | vibe | entireio/cli-checkpoints | cmd/entire/cli/settings/load_v2.go | 12022 | 12919 | 14123 | 0.8512 | 0.0751 | random | claude_code\|vibe |
| 019d4f1d-0e1e-7561-95a4-03df99f243b3 | 204 | 10 | 5 | codex | collab | entireio/cli-checkpoints | docs/plans/2026-04-02-summary-browser.md | 11899 | 11899 |  |  | 0.0446 | random | codex\|collab |
| 019d4f2c-d686-7be2-be93-3f7617272bb4 | 171 | 10 | 5 | codex | unknown | entireio/cli-checkpoints | docs/plans/2026-04-02-summary-browser.md | 11899 | 11899 |  |  | 0.0446 | random | codex\|unknown |
| 019d4f2b-21be-7bd1-88d1-db1efb76146d | 171 | 10 | 5 | codex | human | entireio/cli-checkpoints | docs/plans/2026-04-02-summary-browser.md | 11899 | 11899 |  |  | 0.0446 | random | codex\|human |
| 019d80d3-9312-7982-ad8d-ddf3028c020e | 848 | 10 | 5 | codex | unknown | Soph/go-git | plumbing/compat/mapping_file.go | 11671 | 11671 |  |  | 0.0438 | random | codex\|unknown |
| 019e6db7-a97a-7852-954d-feff812dcef2 | 104 | 10 | 5 | codex | collab | socratesomiliadis/syntheci-shipping | apps/web/src/app/page.tsx | 11654 | 11654 |  |  | 0.0874 | random | codex\|collab |
| ses_25ba963bdffeUnzAsqx26HNZ5d | 432 | 10 | 5 | opencode | vibe | ishaan812/reflex.md | electron/src/main/github.ts | 11437 | 12124 |  |  | 0.0715 | random | opencode\|vibe |
| 108d2ff0-c3d9-45f9-b93e-639ac9ce9321 | 256 | 10 | 5 | claude_code | vibe | Bio1988/moltisown | crates/gateway/src/update_check.rs | 11145 | 11760 | 8469 | 1.3160 | 0.0697 | random | claude_code\|vibe |
| 450f5da9-bcce-4e2e-b30f-9804b07113f0 | 265 | 10 | 5 | claude_code | vibe | E2E-Solution/cli | cmd/entire/cli/trail/store.go | 11074 | 12055 |  |  | 0.0692 | random | claude_code\|vibe |
| d305a67d-f315-4d5b-9481-8b86594e1c44 | 613 | 10 | 5 | cursor | collab | SnowingFox/ai-skills | /Users/bytedance/dev/ai-skills/apps/web/src/app/(registry)/about/page.tsx | 10602 | 11091 |  |  |  | random | cursor\|collab |
| ses_190c8ffbfffei1KPJTro7tb7bH | 25 | 10 | 5 | opencode | vibe | galactica-labs/project-atlas | README.md | 10558 | 12039 | 5707 | 1.8500 |  | random | opencode\|vibe |
| ac4fa545-da7b-4519-8f8e-bc90a7b4bdb4 | 38 | 10 | 5 | claude_code | vibe | 135yshr/documents | articles/b32070e6b12a01.md | 10096 | 19570 | 152 | 66.4211 | 0.0631 | random | claude_code\|vibe |
| f02270cc-e9ef-4ef2-8c3e-9a8bc08845d4 | 590 | 10 | 5 | claude_code | vibe | armelhbobdad/bmad-module-skill-forge | tools/cli/lib/ui.js | 10086 | 10564 | 11664 | 0.8647 | 0.0630 | random | claude_code\|vibe |
| 595d8da7-a1d5-4135-ae05-921e4b62e171 | 193 | 10 | 5 | claude_code | unknown | entireio/cli-checkpoints | /private/tmp/claude-501/-Users-soph-Work-entire-devenv-cli-experiments-2/595d8da7-a1d5-4135-ae05-921e4b62e171/scratchpad/phase2-plan.md | 9940 | 10337 |  |  | 0.0621 | random | claude_code\|unknown |
| c5c0dfc4-ae6f-47f1-86e4-0bc92fde69e0 | 132 | 10 | 5 | claude_code | vibe | theexperiencecompany/gaia | /Users/dhruvmaradiya/.claude/plans/system-instruction-you-are-working-tender-petal.md | 9537 | 9867 |  |  | 0.0596 | random | claude_code\|vibe |
| 6aca4eae-0220-426b-887e-785973f04557 | 300 | 10 | 5 | claude_code | human | cyyeh/duckdb-web | src/App.tsx | 9217 | 9625 | 10982 | 0.8393 | 0.0576 | random | claude_code\|human |
| 94eea312-8dde-4715-b21b-5bcb2caefea5 | 330 | 10 | 5 | claude_code | unknown | jolehuit/reonic-hackathon | src/lib/sizing.ts | 9195 | 9563 | 1443 | 6.3721 | 0.0575 | random | claude_code\|unknown |
| 019dc501-80a1-74a3-8366-beca50119213 | 30 | 10 | 5 | codex | human | geroitscompiling/hackathon_Buena | IMPLEMENTATION_PLAN.md | 9110 | 9110 |  |  | 0.0342 | random | codex\|human |
| ses_178885d42ffe8daG4lOcU4Vm8r | 857 | 10 | 5 | opencode | vibe | Coderx85/wave | src/pages/HomePage.tsx | 9076 | 9582 | 11229 | 0.8083 |  | random | opencode\|vibe |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 2106 | 10 | 5 | codex | unknown | evorto-app/app | tests/specs/finance/finance-viewports.spec.ts | 9038 | 9038 |  |  | 0.0678 | random | codex\|unknown |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-ba3d321274cb | 2106 | 10 | 5 | codex | unknown | evorto-app/app | tests/specs/finance/finance-viewports.spec.ts | 9038 | 9038 |  |  | 0.0678 | random | codex\|unknown |
| 7b980acc-3f13-489f-90d4-b499be91ffd4-67a4a0d01ffc | 194 | 10 | 5 | claude_code | unknown | prayashm/agent-lab | backend/app/channels/telegram_poller.py | 8917 | 9500 | 7491 | 1.1904 | 0.0557 | random | claude_code\|unknown |
| 0696ef34-7ff1-4c1e-9103-ffbca94f3ebd | 57 | 10 | 5 | claude_code | vibe | ClusterCockpit/cc-backend | pkg/metricstore/archive.go | 8882 | 10119 | 11171 | 0.7951 | 0.0555 | random | claude_code\|vibe |
| ses_178885d42ffe8daG4lOcU4Vm8r | 811 | 10 | 5 | opencode | vibe | Coderx85/wave | src/components/NotificationPage.tsx | 8868 | 9388 | 10229 | 0.8669 |  | random | opencode\|vibe |
| d305a67d-f315-4d5b-9481-8b86594e1c44 | 151 | 10 | 5 | cursor | collab | SnowingFox/ai-skills | /Users/bytedance/.cursor/plans/sync_skills_to_db_13574b3f.plan.md | 8835 | 11494 |  |  |  | random | cursor\|collab |
| f6fd2061-fed0-47f5-808a-fa7c3192f219 | 619 | 10 | 5 | claude_code | unknown | entireio/cli-checkpoints | cmd/entire/cli/versioncheck/autoupdate_test.go | 8708 | 9571 | 10784 | 0.8075 | 0.0544 | random | claude_code\|unknown |
| 4b1935f2-997b-4117-aaed-e129ed1ceae6 | 1008 | 10 | 5 | claude_code | human | enismustafaj/baulog | README.md | 8501 | 9187 | 12872 | 0.6604 | 0.0319 | random | claude_code\|human |
| ses_178885d42ffe8daG4lOcU4Vm8r | 583 | 10 | 5 | opencode | vibe | Coderx85/wave | src/pages/AccountPage.tsx | 8492 | 8977 | 93 | 91.3118 |  | random | opencode\|vibe |
| 4b7bf3d3-0d31-4237-918f-b56804225f2c | 1014 | 10 | 5 | claude_code | unknown | entireio/cli-checkpoints | cmd/entire/cli/agent/cursor/chatexport.go | 8462 | 9249 | 5194 | 1.6292 | 0.0529 | random | claude_code\|unknown |
| 75b95053-adb5-472f-bafd-ee45562b45c4 | 263 | 10 | 5 | claude_code | human | marcus-sa/brain | app/src/client/routes/settings-page.test.tsx | 8274 | 8750 | 8875 | 0.9323 | 0.0517 | random | claude_code\|human |
| 311dfedb-2d03-4718-894a-3dc5abdee770 | 731 | 10 | 5 | claude_code | vibe | codyborders/pup-mcp | src/pup_mcp/tools/slos.py | 8181 | 8683 | 2985 | 2.7407 | 0.0511 | random | claude_code\|vibe |
| 763e0b75-dd74-49da-9e0a-a07f8e0b46a0-e2ec057c4768 | 227 | 10 | 5 | cursor | collab | jakobtfaber/dsa110-FLITS | /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/dsa110-FLITS/scripts/query_machine_inventory.py | 8093 | 8682 |  |  |  | random | cursor\|collab |

_600 rows total, 40 shown._

_C01_rewrite_necessary: 0.1s_

## C02 case file: big tool results and whether anything used them  (`C02_tool_result_used`)

**Headline**

- **pool_of_tool_results**: 1061662
- **results_over_5k_chars**: 120383
- **rent_usd_in_pool**: 166972.8
- **median_result_chars**: 311.0000
- **sessions_in_pool**: 8943

### tool_result_used  (600 rows)

| session_id | seq | k_before | k_after | agent | mode | repo | tool_kind | tool_name | what | result_chars | later_calls | rent_tokens | rent_usd | stratum_pick | stratum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-ba3d321274cb | 12073 | 3 | 12 | codex | unknown | evorto-app/app | other | js |  | 15431 | 6766 | 26101536.5 | 13.0508 | random_over_5k | codex\|other |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-e096ea147a34 | 65179 | 3 | 12 | codex | unknown | evorto-app/app | other | js |  | 10753 | 2546 | 6844284.5 | 3.4221 | random_over_5k | codex\|other |
| 469e58d2-a1b1-4eb8-b65f-b02fefb8bb77 | 3090 | 3 | 12 | claude_code | collab | roo-oliv/monodreams | read | Read | /tmp/settings_4x.png | 49630 | 530 | 6575975.0 | 3.2880 | random_over_5k | claude_code\|read |
| ses_1fe66c14effeU5Zvqjz7WOGWaF | 102 | 3 | 12 | opencode | vibe | entireio/cli-checkpoints | web | webfetch |  | 51385 | 363 | 4663188.8 | 2.3316 | random_over_5k | opencode\|web |
| 6629a885-3d0f-45f3-b34c-af9881428368 | 85 | 3 | 12 | claude_code | unknown | pcastelo/lock_code_manager | web | WebSearch | home assistant ha-dialog primaryAction secondaryAction slot deprecated 2025 2026 | 7234 | 2501 | 4523058.5 | 2.2615 | random_over_5k | claude_code\|web |
| 019e5deb-595e-7542-9c0d-69e8b7d894d5 | 209 | 3 | 12 | codex | unknown | edhor1608/qwer-q | other | _fetch |  | 10603 | 1542 | 4087456.5 | 2.0437 | random_over_5k | codex\|other |
| 019d64c5-2795-7463-8fff-73c754b04b4c | 58 | 3 | 12 | codex | vibe | zchee/zmux | mcp | mcp__filesystem__read_multiple_files |  | 113159 | 245 | 6930988.8 | 1.7327 | random_over_5k | codex\|mcp |
| 019e5d87-db21-77f1-988f-4eeb0f07811c-92e842573ead | 4892 | 3 | 12 | codex | vibe | fogodev/ars-ui | other | _list_pull_request_review_threads |  | 34054 | 405 | 3447967.5 | 1.7240 | random_over_5k | codex\|other |
| ses_1fe66c14effeU5Zvqjz7WOGWaF | 101 | 3 | 12 | opencode | vibe | entireio/cli-checkpoints | web | webfetch |  | 37006 | 364 | 3367546.0 | 1.6838 | random_over_5k | opencode\|web |
| 019e5d83-477f-7ea1-9c87-e37f379078af | 3135 | 3 | 12 | codex | collab | fogodev/ars-ui | other | _fetch_pr_comments |  | 47761 | 275 | 3283568.8 | 1.6418 | random_over_5k | codex\|other |
| ses_1fe66c14effeU5Zvqjz7WOGWaF | 102 | 3 | 12 | opencode | vibe | entireio/cli-checkpoints | web | webfetch |  | 35010 | 363 | 3177157.5 | 1.5886 | random_over_5k | opencode\|web |
| 019d724a-df1e-7e20-b01c-6caf0bb02e7a | 66 | 3 | 12 | codex | vibe | dayhaysoos/nimbus | mcp | mcp__codex_apps__github_fetch |  | 37220 | 605 | 5629525.0 | 1.4074 | random_over_5k | codex\|mcp |
| 019ec66b-5210-7711-a71e-86632c398f1f | 103 | 3 | 12 | codex | collab | blackgirlbytes/planetfall-seed-signalkit | other | js |  | 31457 | 348 | 2736759.0 | 1.3684 | random_over_5k | codex\|other |
| 019d64c5-2795-7463-8fff-73c754b04b4c | 547 | 3 | 12 | codex | vibe | zchee/zmux | mcp | mcp__filesystem__read_multiple_files |  | 111745 | 189 | 5279951.2 | 1.3200 | random_over_5k | codex\|mcp |
| cbaf4029-7236-4b9d-9634-7a812f837cc8 | 61 | 3 | 12 | claude_code | vibe | 1natsu-vacation/agent-skills | web | WebFetch |  | 32978 | 311 | 2564039.5 | 1.2820 | random_over_5k | claude_code\|web |
| 019ed2e2-c0ba-7551-9a3b-dcad81973311 | 324 | 3 | 12 | codex | unknown | blackgirlbytes/planetfall-seed-signalkit | other | js |  | 31457 | 305 | 2398596.2 | 1.1993 | random_over_5k | codex\|other |
| fb93c4d8-9548-4a4c-97e6-364245c50453 | 85 | 3 | 12 | claude_code | human | entireio/cli-checkpoints | bash | Bash | gh api repos/openai/privacy-filter/readme --jq '.content' 2>&1 \| base64 -d 2>/dev/null \| head -200 | 12609 | 760 | 2395710.0 | 1.1979 | random_over_5k | claude_code\|bash |
| 28dd7259-aded-4f4a-90cb-540849b25278 | 223 | 3 | 12 | claude_code | human | armelhbobdad/bmad-module-skill-forge | web | WebFetch |  | 41402 | 202 | 2090801.0 | 1.0454 | random_over_5k | claude_code\|web |
| 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9 | 2771 | 3 | 12 | claude_code | unknown | serg-alexv/rhea-project | glob | Glob |  | 5360 | 1439 | 1928260.0 | 0.9641 | random_over_5k | claude_code\|glob |
| 019d724a-df1e-7e20-b01c-6caf0bb02e7a | 35 | 3 | 12 | codex | vibe | dayhaysoos/nimbus | mcp | mcp__codex_apps__github_fetch |  | 25089 | 607 | 3807255.8 | 0.9518 | random_over_5k | codex\|mcp |
| 019e8c4a-fce8-7c63-a3e9-08fd96884c12-ba3d321274cb | 58368 | 3 | 12 | codex | unknown | evorto-app/app | other | js |  | 6518 | 1024 | 1668608.0 | 0.8343 | random_over_5k | codex\|other |
| 019d633b-5b67-7971-a43c-1a2d068388d1 | 81 | 3 | 12 | codex | vibe | zchee/zmux | mcp | mcp__filesystem__read_multiple_files |  | 286440 | 46 | 3294060.0 | 0.8235 | random_over_5k | codex\|mcp |
| a33e4939-e8b1-4b81-aaa1-168fd7fc382f | 2834 | 3 | 12 | claude_code | human | TheurgicDuke771/DataQ | bash | Bash | gh pr diff 544 | 7404 | 361 | 668211.0 | 0.6682 | random_over_5k | claude_code\|bash |
| 019ed688-f0d8-7531-a5f3-ca1cf17f7c75 | 259 | 3 | 12 | codex | human | blackgirlbytes/planetfall-seed-signalkit | other | js |  | 31457 | 165 | 1297601.2 | 0.6488 | random_over_5k | codex\|other |
| 019d783b-5901-7592-b09d-ce70710faeaa | 522 | 3 | 12 | codex | human | entireio/cli-checkpoints | mcp | mcp__codex_apps__github_fetch_pr |  | 90549 | 114 | 2580646.5 | 0.6452 | random_over_5k | codex\|mcp |
| ses_25ba963bdffeUnzAsqx26HNZ5d | 13 | 3 | 12 | opencode | vibe | ishaan812/reflex.md | web | webfetch |  | 8180 | 598 | 1222910.0 | 0.6115 | random_over_5k | opencode\|web |
| ses_32543468affeyW1YI2BEqJxTCu | 10 | 3 | 12 | opencode | vibe | dayhaysoos/nimbus | web | webfetch |  | 32759 | 412 | 3374177.0 | 0.5905 | random_over_5k | opencode\|web |
| 019d724a-df1e-7e20-b01c-6caf0bb02e7a | 24 | 3 | 12 | codex | vibe | dayhaysoos/nimbus | mcp | mcp__codex_apps__github_fetch |  | 14245 | 608 | 2165240.0 | 0.5413 | random_over_5k | codex\|mcp |
| ses_1fe66c14effeU5Zvqjz7WOGWaF | 110 | 3 | 12 | opencode | vibe | entireio/cli-checkpoints | other | skill |  | 11992 | 359 | 1076282.0 | 0.5381 | random_over_5k | opencode\|other |
| 8f1ee6f8-197f-4dea-9f83-0f2fe088e5b9 | 346 | 3 | 12 | claude_code | human | tpmjs/tpmjs | write | Write | apps/web/src/components/ExecutorConfigPanel.tsx | 13418 | 313 | 1049958.5 | 0.5250 | random_over_5k | claude_code\|write |
| 2b3ebe95-a039-46be-9a43-347debb84793 | 42 | 3 | 12 | claude_code | human | ta93abe/data-engineering-with-cloudflare | glob | Glob |  | 17692 | 234 | 1034982.0 | 0.5175 | random_over_5k | claude_code\|glob |
| 1a289c77-a9da-491d-954a-2df7f0dd6a17-8eacff7bdb26 | 2713 | 3 | 12 | claude_code | human | E2E-Solution/cli | bash | Bash | gh api repos/entireio/cli/pulls/172/comments/2777185969/replies \   -f body="This state is intentionally representative. In production, the sequence is:  1. ... | 9730 | 419 | 1019217.5 | 0.5096 | random_over_5k | claude_code\|bash |
| 019d62f5-3225-7142-9e75-ecc3dc600da0 | 272 | 3 | 12 | codex | vibe | zchee/zmux | mcp | mcp__filesystem__read_text_file | src/server.zig | 47378 | 163 | 1930653.5 | 0.4827 | random_over_5k | codex\|mcp |
| a33e4939-e8b1-4b81-aaa1-168fd7fc382f | 3162 | 3 | 12 | claude_code | human | TheurgicDuke771/DataQ | web | WebFetch |  | 5832 | 298 | 434484.0 | 0.4345 | random_over_5k | claude_code\|web |
| e2df973f-328f-4c61-abb6-d89bdee9eaeb | 231 | 3 | 12 | claude_code | collab | anchoo2kewl/SprintSpark | write | Write | internal/email/brevo.go | 8221 | 414 | 850873.5 | 0.4254 | random_over_5k | claude_code\|write |
| 3171104e-0184-4cbd-8c06-875d006a34d2 | 169 | 3 | 12 | claude_code | collab | BIDEquity/outbid-dirigent | web | WebFetch |  | 27779 | 200 | 1388950.0 | 0.4167 | random_over_5k | claude_code\|web |
| 753f66c3-a063-4f29-bce3-ef80ab8825e7 | 496 | 3 | 12 | claude_code | vibe | moltis-org/moltis | read | Read | crates/chat/src/run_with_tools.rs | 6858 | 486 | 833247.0 | 0.4166 | random_over_5k | claude_code\|read |
| dfbb4922-3529-4eab-a5dc-3c8d30b7c660-b5ba7e15aa75 | 1147 | 3 | 12 | claude_code | vibe | E2E-Solution/cli | read | Read | cmd/entire/cli/state.go | 7368 | 451 | 830742.0 | 0.4154 | random_over_5k | claude_code\|read |
| 0c275b1b-9732-433e-9e70-9b7bfdb578a3-507640c3f1e3 | 313 | 3 | 12 | claude_code | human | E2E-Solution/cli | write | Write | docs/plans/2026-02-06-session-phase-review-notes.md | 12409 | 255 | 791073.8 | 0.3955 | random_over_5k | claude_code\|write |
| ses_1fe66c14effeU5Zvqjz7WOGWaF | 5 | 3 | 12 | opencode | vibe | entireio/cli-checkpoints | glob | glob | . | 6958 | 448 | 779296.0 | 0.3896 | random_over_5k | opencode\|glob |

_600 rows total, 40 shown._

_C02_tool_result_used: 0.5s_

## C03 case file: why the hot files are hot  (`C03_hot_file_cause`)

**Headline**

- **hot_files_selected**: 40
- **sessions_covered**: 2340
- **edits_covered**: 10557
- **max_sessions_on_one_file**: 120
- **min_sessions_on_one_file**: 39

### hot_file_cause  (200 rows)

| session_id | seq | k_before | k_after | agent | mode | repo | file_path | tool_kind | file_sessions | file_edits | file_users | stratum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8dab6c26-fc6b-4cc5-8263-6150b598af24-2b7c4f3db4f1 | 216 | 10 | 10 | claude_code | human | E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 120 | 745 | 8 | E2E-Solution/cli\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| 533ff7a3-d390-41ff-b9e8-1b09fb4c2fe2 | 253 | 10 | 10 | claude_code | human | E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 120 | 745 | 8 | E2E-Solution/cli\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| 258a514e-cd22-4513-94b6-49095182e3fa | 387 | 10 | 10 | claude_code | collab | E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 120 | 745 | 8 | E2E-Solution/cli\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| 2026-01-23-6113e919-67d3-417b-b525-c63700228d19-aef9110ba66b | 1030 | 10 | 10 | claude_code | vibe | E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 120 | 745 | 8 | E2E-Solution/cli\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| 2026-01-23-6113e919-67d3-417b-b525-c63700228d19-aef9110ba66b | 1196 | 10 | 10 | claude_code | vibe | E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 120 | 745 | 8 | E2E-Solution/cli\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| bab0cafd-1ba3-4eaf-96b9-4332fe2a340c | 405 | 10 | 10 | claude_code | unknown | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_condensation.go | edit | 100 | 341 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_condensation.go |
| 019e50e7-072d-7611-98fd-7655d10291bd-09466b2a0b60 | 1556 | 10 | 10 | codex | human | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_condensation.go | edit | 100 | 341 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_condensation.go |
| 345ffa6b-bd28-4afc-953f-78cb65a1c2eb-e0a9524df63b | 2024 | 10 | 10 | claude_code | collab | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_condensation.go | edit | 100 | 341 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_condensation.go |
| 6852b33a-0d22-4364-aa6c-8de706ecc215 | 5303 | 10 | 10 | claude_code | human | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_condensation.go | edit | 100 | 341 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_condensation.go |
| 6852b33a-0d22-4364-aa6c-8de706ecc215 | 5310 | 10 | 10 | claude_code | human | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_condensation.go | edit | 100 | 341 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_condensation.go |
| 95560bd3-b4b3-442f-b3c5-3fc1f0cf95b5 | 61 | 10 | 10 | claude_code | collab | henryph24/neuralips26 | main.tex | edit | 91 | 2012 | 1 | henryph24/neuralips26\|main.tex |
| 5bf92790-b3d7-4f91-a7dc-956d671eea4a | 66 | 10 | 10 | claude_code | vibe | henryph24/neuralips26 | main.tex | edit | 91 | 2012 | 1 | henryph24/neuralips26\|main.tex |
| 80438afe-d56f-4d55-a039-052cf1cf500e | 150 | 10 | 10 | claude_code | vibe | henryph24/neuralips26 | main.tex | edit | 91 | 2012 | 1 | henryph24/neuralips26\|main.tex |
| dd693f48-c8c7-464a-9721-c339ef9012ee | 282 | 10 | 10 | claude_code | human | henryph24/neuralips26 | main.tex | edit | 91 | 2012 | 1 | henryph24/neuralips26\|main.tex |
| 73a5c0b0-23f7-4be3-8d21-7cf844164879 | 641 | 10 | 10 | claude_code | collab | henryph24/neuralips26 | main.tex | edit | 91 | 2012 | 1 | henryph24/neuralips26\|main.tex |
| 88ba40a9-e971-4b1b-9655-6cb39f079449 | 107 | 10 | 10 | claude_code | vibe | armelhbobdad/bmad-module-skill-forge | _bmad-output/implementation-artifacts/sprint-status.yaml | edit | 90 | 223 | 1 | armelhbobdad/bmad-module-skill-forge\|_bmad-output/implementation-artifacts/sprint-status.yaml |
| 3df7fb16-7317-40c7-aa75-7437c5604deb | 138 | 10 | 10 | claude_code | vibe | armelhbobdad/bmad-module-skill-forge | _bmad-output/implementation-artifacts/sprint-status.yaml | edit | 90 | 223 | 1 | armelhbobdad/bmad-module-skill-forge\|_bmad-output/implementation-artifacts/sprint-status.yaml |
| d20660fa-e4ff-4bfe-b49c-6a854b6fe00a | 152 | 10 | 10 | claude_code | collab | armelhbobdad/bmad-module-skill-forge | _bmad-output/implementation-artifacts/sprint-status.yaml | edit | 90 | 223 | 1 | armelhbobdad/bmad-module-skill-forge\|_bmad-output/implementation-artifacts/sprint-status.yaml |
| d87fcc85-d674-427b-9e68-702c7a232c35 | 163 | 10 | 10 | claude_code | human | armelhbobdad/bmad-module-skill-forge | _bmad-output/implementation-artifacts/sprint-status.yaml | edit | 90 | 223 | 1 | armelhbobdad/bmad-module-skill-forge\|_bmad-output/implementation-artifacts/sprint-status.yaml |
| 88c1e838-029f-4dc5-8053-27325ab66306 | 612 | 10 | 10 | claude_code | vibe | armelhbobdad/bmad-module-skill-forge | _bmad-output/implementation-artifacts/sprint-status.yaml | edit | 90 | 223 | 1 | armelhbobdad/bmad-module-skill-forge\|_bmad-output/implementation-artifacts/sprint-status.yaml |
| 551922be-297f-446a-aca0-ae85589deaff | 185 | 10 | 10 | claude_code | vibe | entireio/cli-checkpoints | cmd/entire/cli/explain.go | edit | 86 | 480 | 13 | entireio/cli-checkpoints\|cmd/entire/cli/explain.go |
| 27aa2f53-5c52-4fcc-bde3-4e4ef3b0d8bf | 188 | 10 | 10 | claude_code | human | entireio/cli-checkpoints | cmd/entire/cli/explain.go | edit | 86 | 480 | 13 | entireio/cli-checkpoints\|cmd/entire/cli/explain.go |
| 019dd911-f1c3-7443-b650-b4df245ee53e | 330 | 10 | 10 | codex | vibe | entireio/cli-checkpoints | cmd/entire/cli/explain.go | edit | 86 | 480 | 13 | entireio/cli-checkpoints\|cmd/entire/cli/explain.go |
| 27aa2f53-5c52-4fcc-bde3-4e4ef3b0d8bf | 667 | 10 | 10 | claude_code | human | entireio/cli-checkpoints | cmd/entire/cli/explain.go | edit | 86 | 480 | 13 | entireio/cli-checkpoints\|cmd/entire/cli/explain.go |
| e6137d90-dc46-43a5-8d29-5e5e5cbe2b32 | 1583 | 10 | 10 | claude_code | vibe | entireio/cli-checkpoints | cmd/entire/cli/explain.go | edit | 86 | 480 | 13 | entireio/cli-checkpoints\|cmd/entire/cli/explain.go |
| 609f7cee-c4c5-4016-8d1a-95ec65b0f2dd | 18 | 10 | 10 | claude_code | unknown | FSM1/cipher-box | .planning/STATE.md | edit | 83 | 205 | 2 | FSM1/cipher-box\|.planning/STATE.md |
| 9e367a0f-780f-408b-8cb7-2c378e3aadfb | 71 | 10 | 10 | claude_code | human | FSM1/cipher-box | .planning/STATE.md | edit | 83 | 205 | 2 | FSM1/cipher-box\|.planning/STATE.md |
| 9e367a0f-780f-408b-8cb7-2c378e3aadfb | 106 | 10 | 10 | claude_code | human | FSM1/cipher-box | .planning/STATE.md | edit | 83 | 205 | 2 | FSM1/cipher-box\|.planning/STATE.md |
| ff87d486-a76c-43ec-b42e-ed864560c25c | 1002 | 10 | 10 | claude_code | human | FSM1/cipher-box | .planning/STATE.md | edit | 83 | 205 | 2 | FSM1/cipher-box\|.planning/STATE.md |
| ca83442d-e993-4fad-8db8-b0bd2dad4a99 | 3520 | 10 | 10 | claude_code | unknown | FSM1/cipher-box | .planning/STATE.md | edit | 83 | 205 | 2 | FSM1/cipher-box\|.planning/STATE.md |
| 9a29d9ba-5e22-4e92-a5d0-017356e28328 | 455 | 10 | 10 | claude_code | vibe | entireio/cli-checkpoints | cmd/entire/cli/checkpoint/committed.go | edit | 83 | 362 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/checkpoint/committed.go |
| cde6bd89-1d46-477f-b499-bb2e6b8d2a2e | 713 | 10 | 10 | claude_code | human | entireio/cli-checkpoints | cmd/entire/cli/checkpoint/committed.go | edit | 83 | 362 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/checkpoint/committed.go |
| 1290facc-cb4c-4da7-aafd-22f5b86fedc1 | 768 | 10 | 10 | claude_code | vibe | entireio/cli-checkpoints | cmd/entire/cli/checkpoint/committed.go | edit | 83 | 362 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/checkpoint/committed.go |
| 5a330055-ac9f-417e-a008-c293510737fe | 1134 | 10 | 10 | claude_code | human | entireio/cli-checkpoints | cmd/entire/cli/checkpoint/committed.go | edit | 83 | 362 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/checkpoint/committed.go |
| 019dd0f5-bf9d-7521-a357-f745b5c66cf7-ba6027fbb4e2 | 3478 | 10 | 10 | codex | vibe | entireio/cli-checkpoints | cmd/entire/cli/checkpoint/committed.go | edit | 83 | 362 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/checkpoint/committed.go |
| d7eb2c7b-65ce-4dbe-b20a-285326019897 | 135 | 10 | 10 | claude_code | vibe | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 83 | 315 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| 41550a00-f693-4559-8e46-61593a0788ad | 203 | 10 | 10 | claude_code | human | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 83 | 315 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| 0798c36e-9fc3-43f4-a878-d7b5a53c7a76 | 620 | 10 | 10 | claude_code | unknown | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 83 | 315 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| 53820994-09c3-4a2b-8aff-8ebfda43134b | 710 | 10 | 10 | claude_code | unknown | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 83 | 315 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_hooks.go |
| b1ed7d58-eb6b-498c-931f-1f6f207e13c3 | 1725 | 10 | 10 | claude_code | unknown | entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_hooks.go | edit | 83 | 315 | 9 | entireio/cli-checkpoints\|cmd/entire/cli/strategy/manual_commit_hooks.go |

_200 rows total, 40 shown._

_C03_hot_file_cause: 0.1s_

