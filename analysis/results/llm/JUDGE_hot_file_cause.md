# Layer 3 judge: hot_file_cause

provider `deepseek`, model `deepseek-v4-pro`, 200 cases judged, 0 failed, 0.22 USD


Rate reported: **edits caused by agent regression** (`cause` == 'agent_regression')


| stratum | cases | hits | rate | 95% Wilson | population | extrapolated |
|---|---:|---:|---:|---|---:|---:|
| E2E-Solution/cli|cmd/entire/cli/checkpoint/committed.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/explain.go | 5 | 3 | 60.0% | 23.1% to 88.2% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/hooks_claudecode_handlers.go | 5 | 2 | 40.0% | 11.8% to 76.9% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/lifecycle.go | 5 | 3 | 60.0% | 23.1% to 88.2% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/session/state.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/setup.go | 5 | 2 | 40.0% | 11.8% to 76.9% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/strategy/auto_commit.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/strategy/common.go | 5 | 2 | 40.0% | 11.8% to 76.9% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/strategy/manual_commit_condensation.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| E2E-Solution/cli|cmd/entire/cli/strategy/manual_commit_hooks.go | 5 | 3 | 60.0% | 23.1% to 88.2% | n/a | n/a |
| FSM1/cipher-box|.planning/ROADMAP.md | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| FSM1/cipher-box|.planning/STATE.md | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| FSM1/cipher-box|/Users/myankelev/.claude/projects/-Users-myankelev-Code-random-cipher-box/memory/MEMORY.md | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| armelhbobdad/bmad-module-skill-forge|README.md | 5 | 0 | 0.0% | 0.0% to 43.4% | n/a | n/a |
| armelhbobdad/bmad-module-skill-forge|_bmad-output/implementation-artifacts/sprint-status.yaml | 5 | 0 | 0.0% | 0.0% to 43.4% | n/a | n/a |
| armelhbobdad/bmad-module-skill-forge|docs/workflows.md | 5 | 0 | 0.0% | 0.0% to 43.4% | n/a | n/a |
| armelhbobdad/bmad-module-skill-forge|package.json | 5 | 0 | 0.0% | 0.0% to 43.4% | n/a | n/a |
| cyyeh/duckdb-data-agent|README.md | 5 | 0 | 0.0% | 0.0% to 43.4% | n/a | n/a |
| cyyeh/duckdb-data-agent|backend/app/agent.py | 5 | 3 | 60.0% | 23.1% to 88.2% | n/a | n/a |
| entireio/cli-checkpoints|CLAUDE.md | 5 | 0 | 0.0% | 0.0% to 43.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/attach.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/checkpoint/checkpoint.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/checkpoint/committed.go | 5 | 3 | 60.0% | 23.1% to 88.2% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/checkpoint/v2_committed.go | 5 | 2 | 40.0% | 11.8% to 76.9% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/explain.go | 5 | 3 | 60.0% | 23.1% to 88.2% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/explain_test.go | 5 | 0 | 0.0% | 0.0% to 43.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/git_operations.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/migrate.go | 5 | 2 | 40.0% | 11.8% to 76.9% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/migrate_test.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/resume.go | 5 | 3 | 60.0% | 23.1% to 88.2% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/root.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/settings/settings.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/settings/settings_test.go | 5 | 0 | 0.0% | 0.0% to 43.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/setup.go | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/strategy/common.go | 5 | 2 | 40.0% | 11.8% to 76.9% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/strategy/manual_commit_condensation.go | 5 | 2 | 40.0% | 11.8% to 76.9% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/strategy/manual_commit_hooks.go | 5 | 3 | 60.0% | 23.1% to 88.2% | n/a | n/a |
| entireio/cli-checkpoints|cmd/entire/cli/strategy/push_common.go | 5 | 2 | 40.0% | 11.8% to 76.9% | n/a | n/a |
| henryph24/neuralips26|main.tex | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| marcus-sa/brain|schema/surreal-schema.surql | 5 | 1 | 20.0% | 3.6% to 62.4% | n/a | n/a |
| **all** | 200 | 56 | 28.0% | 22.2% to 34.6% | n/a | n/a |

Extrapolation multiplies the stratum rate by the `population_n` column of the case CSV (the layer 1 count for that stratum). It is `n/a` when the case file did not carry one.

