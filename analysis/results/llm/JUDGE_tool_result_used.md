# Layer 3 judge: tool_result_used

provider `deepseek`, model `deepseek-v4-pro`, 600 cases judged, 0 failed, 1.02 USD


Rate reported: **results never referenced again** (`was_result_referenced_later` == False)


| stratum | cases | hits | rate | 95% Wilson | population | extrapolated |
|---|---:|---:|---:|---|---:|---:|
| claude_code|bash | 25 | 4 | 16.0% | 6.4% to 34.7% | n/a | n/a |
| claude_code|glob | 25 | 14 | 56.0% | 37.1% to 73.3% | n/a | n/a |
| claude_code|read | 26 | 7 | 26.9% | 13.7% to 46.1% | n/a | n/a |
| claude_code|web | 25 | 6 | 24.0% | 11.5% to 43.4% | n/a | n/a |
| claude_code|write | 25 | 6 | 24.0% | 11.5% to 43.4% | n/a | n/a |
| codex|bash | 295 | 97 | 32.9% | 27.8% to 38.4% | n/a | n/a |
| codex|mcp | 25 | 11 | 44.0% | 26.7% to 62.9% | n/a | n/a |
| codex|other | 27 | 11 | 40.7% | 24.5% to 59.3% | n/a | n/a |
| opencode|glob | 25 | 11 | 44.0% | 26.7% to 62.9% | n/a | n/a |
| opencode|other | 25 | 9 | 36.0% | 20.2% to 55.5% | n/a | n/a |
| opencode|read | 25 | 9 | 36.0% | 20.2% to 55.5% | n/a | n/a |
| opencode|task | 25 | 0 | 0.0% | 0.0% to 13.3% | n/a | n/a |
| opencode|web | 25 | 9 | 36.0% | 20.2% to 55.5% | n/a | n/a |
| opencode|write | 2 | 1 | 50.0% | 9.5% to 90.5% | n/a | n/a |
| **all** | 600 | 195 | 32.5% | 28.9% to 36.3% | n/a | n/a |

Extrapolation multiplies the stratum rate by the `population_n` column of the case CSV (the layer 1 count for that stratum). It is `n/a` when the case file did not carry one.

