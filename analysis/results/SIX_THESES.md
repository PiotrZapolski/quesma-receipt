# Sześć tez: dane

Zbiór SWE-chat enhanced 2026-07-05, 9 770 sesji, 17,8 GB. Ledger: analysis/ledger. Zapytania: analysis/queries oraz ad hoc (zapisane wyniki w analysis/results/six/). Ceny: analysis/prices.csv. Tokeny z wyników narzędzi liczone jako znaki/4. Linie wygenerowane liczone jako znaki/40.

## 1. Linie w commicie kontra wygenerowany kod

Definicje: gen_lines_est = suma znaków w Write.content i Edit.new_string w sesji / 40. committed_lines = total_committed z atrybucji Entire. pct_survive_est = committed_lines / gen_lines_est. Tylko sesje z committed_lines > 0. W trybach human i collab committed_lines zawiera kod napisany przez człowieka, stąd wartości powyżej 100%.

| agent | mode | sessions | gen_lines_est | committed_lines | pct_survive_est | usd | usd_per_committed_line |
|---|---|---|---|---|---|---|---|
| claude_code | collab | 1 404 | 1 086 816 | 2 085 977 | 192 | 18 562 | 0.0089 |
| claude_code | human | 1 611 | 1 321 923 | 10 962 446 | 829 | 29 356 | 0.0027 |
| claude_code | vibe | 2 711 | 1 431 976 | 730 640 | 51 | 25 031 | 0.0343 |
| codex | collab | 112 | 174 824 | 281 775 | 161 | 2 677 | 0.0095 |
| codex | human | 108 | 208 229 | 653 242 | 314 | 2 784 | 0.0043 |
| codex | vibe | 379 | 567 394 | 97 763 | 17.2 | 7 481 | 0.0765 |
| opencode | collab | 46 | 52 651 | 83 524 | 159 | 131 | 0.0016 |
| opencode | human | 73 | 48 118 | 94 550 | 196 | 99 | 0.001 |
| opencode | vibe | 83 | 116 522 | 29 540 | 25.4 | 481 | 0.0163 |

Rozkład pct_survive_est per sesja, tryb vibe, sesje z co najmniej 400 wygenerowanymi znakami:

| bucket | sessions |
|---|---|
| 1. <10% | 994 |
| 2. 10-25% | 455 |
| 3. 25-50% | 575 |
| 4. 50-75% | 341 |
| 5. 75-100% | 209 |
| 6. >100% | 376 |

Z T01 (cały zbiór): USD na linię w commicie human 0,0029, collab 0,0066, vibe 0,0193; tokeny kontekstu na linię 3 830 / 8 754 / 26 099.

## 2. Nieprzeczytane odpowiedzi

Definicje: odpowiedź końcowa = ostatnie wywołanie z tekstem w turze przed następnym promptem człowieka (Codex: z korektą na wywołania stemplowane po następnym promptcie). read_time_s = (znaki/5)/250 słów na minutę. unread = czas do następnego promptu < 0,5 × read_time_s. Wykluczone przerwania.

| agent | final_replies | unread_replies | pct_replies_unread | final_text_tokens | unread_text_tokens | pct_text_tokens_unread | unread_usd | median_read_time_s | median_delta_s |
|---|---|---|---|---|---|---|---|---|---|
| claude_code | 55 223 | 6 543 | 11.85 | 13 793 522 | 2 786 147 | 20.2 | 68.43 | 29.57 | 98.46 |
| codex | 9 501 | 2 257 | 23.76 | 2 959 571 | 784 364 | 26.5 | 19.35 | 48.77 | 94.53 |
| opencode | 1 804 | 115 | 6.37 | 600 615 | 121 594 | 20.24 | 1 | 43.39 | 170 |

To samo według etykiety NASTĘPNEGO promptu człowieka (etykiety z klasyfikacji DeepSeek V4-Flash, 87 887 promptów):

| label | replies | unread | pct_unread | median_reply_chars | median_delta_s | unread_long_over_3000_chars |
|---|---|---|---|---|---|---|
| follow_up | 23 008 | 2 392 | 10.4 | 806 | 114 | 472 |
| approval | 10 599 | 1 911 | 18 | 976 | 73 | 385 |
| question | 10 521 | 865 | 8.2 | 813 | 123 | 139 |
| meta_other | 9 167 | 2 752 | 30 | 233 | 36 | 56 |
| failure_report | 5 755 | 293 | 5.1 | 520 | 154 | 13 |
| correction | 4 327 | 386 | 8.9 | 719 | 91 | 41 |
| new_task | 2 600 | 157 | 6 | 476 | 207 | 30 |
| interruption | 551 | 159 | 28.9 | 237 | 26 | 5 |

## 3. Ekonomia subagentów

Luka w danych: transkrypty subagentów nie są w zbiorze. Wywołań z flagą isSidechain: 300 z 933 529 (2,62 USD). Poniżej wyłącznie narzędzie Task widziane z sesji rodzica (Claude Code).

Sesje według liczby wywołań Task:

| task_calls_bucket | sessions | task_calls | result_Mchars |
|---|---|---|---|
| 1 | 1 128 | 1 128 | 7.8 |
| 2-3 | 1 024 | 2 544 | 17.5 |
| 4-10 | 980 | 5 654 | 34 |
| 11-30 | 355 | 5 811 | 24.8 |
| >30 | 55 | 2 696 | 7.1 |

Sesje Claude Code z Task i bez, per tryb (mediana kosztu sesji, USD na linię w commicie, odsetek sesji z commitem):

| mode | kind | sessions | median_usd | usd_per_committed_line | pct_with_commit |
|---|---|---|---|---|---|
| collab | bez Task | 772 | 1.59 | 0.003 | 99.4 |
| collab | z Task | 789 | 5.32 | 0.0142 | 99.6 |
| human | bez Task | 1 047 | 1.14 | 0.0011 | 81.9 |
| human | z Task | 1 135 | 6.72 | 0.0039 | 89.4 |
| vibe | bez Task | 1 719 | 1.45 | 0.0234 | 99.4 |
| vibe | z Task | 1 299 | 4.44 | 0.0347 | 99.5 |

Wyniki Task w kontekście rodzica: 17 833 wywołań w 3 542 sesjach, 91,3 mln znaków, mediana 3 136 znaków, czynsz kontekstu 1 898 USD (T04), koszt samych promptów Task 266 USD (T16).

## 4. Kompakcja

Definicje: granica = zdarzenie system/compact_boundary lub microcompact_boundary (Claude Code) albo compacted (Codex). Reread = Read ścieżki, która była czytana w tej sesji przed granicą, w 20 wywołaniach narzędzi po granicy. Rozmiar redukcji nie jest zapisany w ledgerze (tylko trigger = auto).

| agent | sessions | sessions_with_a_boundary | pct_sessions_compacted | median_boundaries_when_present | max_boundaries | usd_in_compacted_sessions |
|---|---|---|---|---|---|---|
| claude_code | 7 230 | 746 | 10.32 | 1 | 96 | 36 593 |
| codex | 1 167 | 302 | 25.88 | 2 | 103 | 16 718 |
| opencode | 783 | 0 | 0 |  |  |  |
| cursor | 86 | 0 | 0 |  |  |  |

| agent | event_kind | reads_in_next_20_tool_calls | reads_of_already_seen_paths | pct_rereads | reread_chars | reread_usd_one_pass | reread_usd_recached |
|---|---|---|---|---|---|---|---|
| claude_code | compact_boundary | 6 968 | 4 121 | 59.14 | 33 550 476 | 4.05 | 50.56 |
| claude_code | microcompact_boundary | 1 249 | 517 | 41.39 | 1 796 504 | 0.1577 | 1.97 |

Najczęściej czytane ponownie po kompakcji:

| file_path_80 | rereads_after_a_boundary | sessions | chars |
|---|---|---|---|
| cmd/entire/cli/strategy/manual_commit_hooks.go | 257 | 48 | 1 846 415 |
| src/rhea_bridge.py | 71 | 4 | 893 850 |
| scripts/rhea_query_persist.sh | 52 | 1 | 188 644 |
| static/index.html | 51 | 5 | 128 889 |
| cmd/entire/cli/strategy/manual_commit_condensation.go | 51 | 26 | 405 641 |
| cmd/entire/cli/checkpoint/temporary.go | 43 | 11 | 345 666 |
| cmd/entire/cli/hooks_claudecode_handlers.go | 42 | 21 | 864 872 |
| /Users/sa/rh.REDACTED.md | 41 | 2 | 32 669 |
| cmd/entire/cli/explain.go | 37 | 10 | 480 458 |
| src/clio_pipeline/pipeline/run_pipeline.py | 34 | 1 | 54 958 |
| src/trading/live_trading.py | 33 | 3 | 101 955 |
| cmd/entire/cli/lifecycle.go | 31 | 16 | 261 990 |

## 5. Czekanie na build w pętli

Definicje: polling = wywołanie Bash z `sleep N`, `gh run watch` lub `wait`. Burst = liczba pollingów w oknie 5 kolejnych wywołań narzędzi. usd = koszt wywołań API, które wydały polling (pełny kontekst).

| agent | bash_calls | polling_calls | pct_of_bash_calls | sessions | usd_of_the_calls_that_issued_them | ctx_tokens |
|---|---|---|---|---|---|---|
| claude_code | 291 956 | 7 041 | 2.41 | 961 | 1 082 | 1 705 656 825 |
| codex | 220 422 | 2 974 | 1.35 | 134 | 268 | 438 266 466 |
| opencode | 10 393 | 192 | 1.85 | 21 | 9.93 | 21 538 021 |
| cursor | 2 480 | 109 | 4.4 | 11 |  | 0 |

| burst | polling_calls | usd | ctx_tokens |
|---|---|---|---|
| isolated | 5 690 | 809 | 1 285 345 232 |
| 2 polls in 5 calls | 3 029 | 361 | 572 016 419 |
| 3 polls in 5 calls | 975 | 104 | 166 578 048 |
| 4+ polls in 5 calls | 622 | 84.89 | 141 521 613 |

Długość `sleep N` (tylko wywołania z liczbą sekund):

| sleep_bucket | calls | usd_context | hours_slept |
|---|---|---|---|
| 1. <10 s | 3 460 | 467 | 2.8 |
| 2. 10-29 s | 1 496 | 267 | 6.2 |
| 3. 30-59 s | 507 | 90 | 4.7 |
| 4. 60-299 s | 926 | 109 | 29.4 |
| 5. >=300 s | 589 | 105 | 202 |

Najczęstsze komendy: sleep 120 (326 wywołań, 27 sesji), sleep 180 (94, 13). Pełna lista: results/T09_polling__top_polling_commands.csv.

## 6. Gorące pliki edytowane równocześnie

Definicje: para nakładająca się = dwie sesje w tym samym repo, które edytowały (Write/Edit) ten sam plik, a ich okna [pierwsza edycja, ostatnia edycja] tego pliku nachodzą na siebie w czasie zegarowym. Luka w danych: równoczesność między subagentami w jednej sesji jest nieobserwowalna (patrz 3).

| overlapping_pairs | files_with_overlap | files_edited_total | sessions_involved |
|---|---|---|---|
| 2 908 | 1 591 | 32 127 | 914 |

| repo | file_path | overlapping_session_pairs |
|---|---|---|
| entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_condensation.go | 45 |
| entireio/cli-checkpoints | cmd/entire/cli/checkpoint/committed.go | 40 |
| entireio/cli-checkpoints | cmd/entire/cli/explain.go | 37 |
| E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_hooks.go | 34 |
| entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_hooks.go | 32 |
| entireio/cli-checkpoints | cmd/entire/cli/migrate.go | 22 |
| E2E-Solution/cli | cmd/entire/cli/lifecycle.go | 17 |
| entireio/cli-checkpoints | cmd/entire/cli/explain_test.go | 17 |
| entireio/cli-checkpoints | cmd/entire/cli/checkpoint/open.go | 17 |
| entireio/cli-checkpoints | cmd/entire/cli/resume.go | 17 |
| entireio/cli-checkpoints | cmd/entire/cli/settings/settings.go | 16 |
| entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_rewind.go | 15 |

Gorące pliki (edytowane w co najmniej 10 sesjach repo, T14): 518 plików, 20,6% ze 186 775 edycji; mediana udziału top 5% plików w edycjach repo 33,8%. Edycje z błędem w 3 kolejnych wywołaniach: gorące 6,8%, zimne 7,7%.

| repo | file_path_70 | agent | sessions | users | edits | pct_edits_followed_by_error | pct_edits_followed_by_short_correction |
|---|---|---|---|---|---|---|---|
| E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_hooks.go | claude_code | 120 | 8 | 745 | 9.13 | 50.87 |
| entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_condensation.go | codex | 100 | 9 | 341 | 4.99 | 80.35 |
| henryph24/neuralips26 | main.tex | claude_code | 91 | 1 | 2 012 | 3.38 | 74.75 |
| armelhbobdad/bmad-module-skill-forge | _bmad-output/implementation-artifacts/sprint-status.yaml | claude_code | 90 | 1 | 223 | 7.17 | 22.87 |
| entireio/cli-checkpoints | cmd/entire/cli/explain.go | codex | 86 | 13 | 480 | 6.88 | 67.5 |
| entireio/cli-checkpoints | cmd/entire/cli/checkpoint/committed.go | codex | 83 | 9 | 362 | 4.42 | 75.97 |
| entireio/cli-checkpoints | cmd/entire/cli/strategy/manual_commit_hooks.go | codex | 83 | 9 | 315 | 7.94 | 72.7 |
| FSM1/cipher-box | .planning/STATE.md | claude_code | 83 | 2 | 205 | 6.83 | 43.9 |
| E2E-Solution/cli | cmd/entire/cli/strategy/manual_commit_condensation.go | claude_code | 76 | 9 | 268 | 8.96 | 58.21 |
| cyyeh/duckdb-data-agent | backend/app/agent.py | claude_code | 66 | 1 | 259 | 6.18 | 70.66 |
| entireio/cli-checkpoints | cmd/entire/cli/migrate.go | codex | 63 | 6 | 483 | 1.24 | 72.67 |
| entireio/cli-checkpoints | cmd/entire/cli/settings/settings.go | codex | 62 | 9 | 165 | 2.42 | 67.27 |

Przyczyna edycji gorącego pliku według sędziego (DeepSeek V4-Pro, 200 przypadków, 40 plików po 5):

| cause | n | pct |
|---|---|---|
| architecture_hub | 110 | 55 |
| agent_regression | 56 | 28 |
| test_file | 18 | 9 |
| user_iteration | 14 | 7 |
| unclear | 1 | 0.5 |
| config_churn | 1 | 0.5 |

## Pliki źródłowe

results/six/*.csv (tabele powyżej), results/T01, T09, T11, T14, T16, T19 (*.csv), results/llm/prompt_labels.parquet, results/llm/judge_hot_file_cause.parquet, results/REPORT.md (wszystkie 24 tezy), results/FINDINGS.md (pełny raport).
