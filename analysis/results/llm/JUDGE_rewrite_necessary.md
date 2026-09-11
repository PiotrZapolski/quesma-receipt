# Layer 3 judge: rewrite_necessary

provider `deepseek`, model `deepseek-v4-pro`, 600 cases judged, 0 failed, 0.72 USD


Rate reported: **unnecessary full rewrites** (`was_full_rewrite_needed` == False)


| stratum | cases | hits | rate | 95% Wilson | population | extrapolated |
|---|---:|---:|---:|---|---:|---:|
| claude_code|collab | 88 | 60 | 68.2% | 57.9% to 77.0% | n/a | n/a |
| claude_code|human | 118 | 82 | 69.5% | 60.7% to 77.1% | n/a | n/a |
| claude_code|unknown | 62 | 45 | 72.6% | 60.4% to 82.1% | n/a | n/a |
| claude_code|vibe | 121 | 94 | 77.7% | 69.5% to 84.2% | n/a | n/a |
| codex|collab | 14 | 3 | 21.4% | 7.6% to 47.6% | n/a | n/a |
| codex|human | 35 | 17 | 48.6% | 33.0% to 64.4% | n/a | n/a |
| codex|unknown | 22 | 8 | 36.4% | 19.7% to 57.0% | n/a | n/a |
| codex|vibe | 7 | 3 | 42.9% | 15.8% to 75.0% | n/a | n/a |
| cursor|collab | 16 | 15 | 93.8% | 71.7% to 98.9% | n/a | n/a |
| cursor|human | 27 | 26 | 96.3% | 81.7% to 99.3% | n/a | n/a |
| opencode|collab | 1 | 0 | 0.0% | 0.0% to 79.3% | n/a | n/a |
| opencode|human | 9 | 4 | 44.4% | 18.9% to 73.3% | n/a | n/a |
| opencode|unknown | 36 | 32 | 88.9% | 74.7% to 95.6% | n/a | n/a |
| opencode|vibe | 44 | 39 | 88.6% | 76.0% to 95.0% | n/a | n/a |
| **all** | 600 | 428 | 71.3% | 67.6% to 74.8% | n/a | n/a |

Extrapolation multiplies the stratum rate by the `population_n` column of the case CSV (the layer 1 count for that stratum). It is `n/a` when the case file did not carry one.

