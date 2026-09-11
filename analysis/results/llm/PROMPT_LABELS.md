# Layer 2: prompt classification

provider `deepseek`, model `deepseek-v4-flash`, 87887 labelled of 87887 selected, 0 failed, 3.64 USD


## Label distribution by agent

| label | claude_code | codex | cursor | opencode | total |
|---|---|---|---|---|---|
| new_task | 6541 | 1443 | 170 | 727 | 8881 |
| follow_up | 21047 | 4478 | 422 | 1062 | 27009 |
| approval | 8919 | 2238 | 124 | 329 | 11610 |
| correction | 4178 | 915 | 111 | 142 | 5346 |
| failure_report | 5836 | 838 | 79 | 301 | 7054 |
| interruption | 338 | 791 | 10 | 13 | 1152 |
| question | 9978 | 2202 | 276 | 316 | 12772 |
| meta_other | 10900 | 2843 | 240 | 80 | 14063 |

## Pushback rate by agent

| agent | prompts | pushback | rate |
|---|---:|---:|---:|
| claude_code | 67737 | 10494 | 15.5% |
| codex | 15748 | 1950 | 12.4% |
| cursor | 1432 | 213 | 14.9% |
| opencode | 2970 | 474 | 16.0% |

## Sentiment

| sentiment | prompts | share |
|---|---:|---:|
| neutral | 79803 | 90.8% |
| positive | 5798 | 6.6% |
| frustrated | 2286 | 2.6% |

## Top languages

| language | prompts | share |
|---|---:|---:|
| en | 82188 | 93.5% |
| ja | 2332 | 2.7% |
| zh | 1734 | 2.0% |
| ru | 533 | 0.6% |
| ko | 436 | 0.5% |
| fr | 387 | 0.4% |
| de | 198 | 0.2% |
| pt | 77 | 0.1% |
| unknown | 1 | 0.0% |
| pl | 1 | 0.0% |

mentions_file: 19683 of 87887 (22.4%)


## Coerced and invalid values

Values the model returned with the wrong type or outside the allowed set, repaired before the table was built.

| field | coerced | invalid | first bad value |
|---|---:|---:|---|
| language | 0 | 1 | `NoneType None` |
| sentiment | 0 | 3 | `bool False` |

