# Rachunek za tokeny: co naprawdę kosztuje w sesjach agentów kodujących

Analiza zbioru SWE-chat enhanced 2026-07-05 (9 770 sesji, 17,8 GB surowych transkryptów, 344 repozytoria, harnessy Claude Code, Codex, OpenCode, Cursor). Data analizy: 11 września 2026. Wszystkie kwoty w USD po oficjalnych cennikach Anthropic i OpenAI z dnia analizy, przeliczone wywołanie po wywołaniu.

Punkt odniesienia: paper SWE-chat (Stanford, arXiv 2604.20779) i strona swe-chat.com operują na poziomie sesji i commitu: tryby kodowania, 44% przeżywalności kodu, tokeny na linię w commicie, 44% tur z pushbackiem, Semgrep. My schodzimy do poziomu pojedynczego wywołania API i pojedynczego wyniku narzędzia. Wszystkie liczby poniżej są liczone na całej populacji, chyba że napisano "próbka".

---

## 1. Streszczenie w dziesięciu punktach

| # | Znalezisko | Liczba | Skąd |
|---|---|---|---|
| 1 | Rachunek to cache, nie prompt. Odczyty cache to 64% kosztu, zapisy cache 22%, output 9%, świeży input 5% | 116 677 USD łącznie | T01 |
| 2 | Przerwa na kawę kosztuje. Po przerwie użytkownika dłuższej niż 5 minut harness zapisuje cache od nowa; po przerwie ponad godzinę pęka w 84% przypadków | 9 223 USD na samych pęknięciach, 8% rachunku | T02 |
| 3 | Wyniki narzędzi to połowa czynszu za kontekst w Claude Code. 5% największych wyników (ponad 10 tys. znaków) generuje 61% tego czynszu | 30 746 USD | T04 |
| 4 | Sędzia LLM: 32% dużych wyników narzędzi nigdy nie zostało użytych, 97% było potrzebne co najwyżej w małym fragmencie | 600 przypadków | Warstwa 3 |
| 5 | 80% pełnych przepisań plików, które model miał już w kontekście, było niepotrzebne. Codex 30 do 53%, bo apply_patch wymusza diff | 636 przypadków | Warstwa 3 |
| 6 | Trzy czwarte strony promptu pisze harness, nie człowiek | 377 mln znaków kontra 126 mln | T24 |
| 7 | Pushback kosztuje 14% rachunku: tury po korekcie albo zgłoszeniu błędu | około 16 000 USD | Warstwa 2 + ledger |
| 8 | 1,4% wywołań Read to obrazki w base64, ale to 33% wszystkich znaków wciągniętych przez Read | około 65 mln tokenów | Sondy |
| 9 | Bash jest głównym śmietnikiem: 1,33 mld znaków wyników, gzip ściska je średnio 3,6 razy | około 70% redundancji | Sondy |
| 10 | Godziny ludzkie przebijają tokeny. 16 358 godzin pracy agenta, przy 60 USD/h to 8,6 razy koszt tokenów, jeśli człowiek patrzy | górna granica | T12 |

Wniosek nadrzędny: optymalizowanie liczby tokenów wyjściowych jest złym celem. Pieniądze siedzą w tym, co siedzi w kontekście i jest opłacane przy każdym kolejnym wywołaniu, a decyduje o tym harness (narzędzia, formatowanie, cache), nie model.

---

## 2. Dane i metoda

### 2.1 Zbiór

| | |
|---|---|
| Transkrypty | 9 770 plików JSONL, 17,8 GB |
| Harnessy | Claude Code 7 285 (14,2 GB), Codex 1 240 (2,7 GB), OpenCode 783 (0,7 GB), Cursor 152, inne 383 pominięte |
| Wywołań API | 933 529 (po scaleniu linii tej samej odpowiedzi) |
| Wywołań narzędzi | 1 086 824 |
| Promptów ludzkich | 121 235 zapisanych, 87 887 po odsianiu wstrzykniętych przez harness |
| Zdarzeń meta | 2 637 254 |
| Okres | marzec do lipiec 2026 |

### 2.2 Ledger

Surowe pliki zostały jednorazowo przepisane do pięciu płaskich tabel Parquet (`analysis/ledger/`, 248 MB, 24 sekundy na 6 rdzeniach): `calls` (jeden wiersz na odpowiedź modelu z pełnym rozbiciem usage), `tool_calls` (nazwa, ścieżka, długości argumentów, rozmiar i hash wyniku, błąd), `user_turns` (pełny tekst promptu plus liczba znaków napisanych przez człowieka), `events` (kompakcje, tryby uprawnień, załączniki, kolejka), `sessions` (metadane z katalogu). Walidacja z metadanymi: tokeny wyjściowe Claude Code zgodne co do tokena w 7 241 z 7 242 sesji, liczba wywołań narzędzi z medianą odchylenia 0% we wszystkich czterech harnessach.

Pułapki w danych, które trzeba znać:

- `files_touched` w metadanych to pliki w commicie, łącznie z edycjami człowieka, nie pliki edytowane przez agenta. Do "co edytował agent" służą wyłącznie wywołania narzędzi.
- Atrybucja (ile linii agenta przetrwało) jest per sesja, nie per plik, i brakuje jej w 731 sesjach.
- `session_id` nie jest unikalne (180 duplikatów). Kluczem jest nazwa pliku.
- 65 sesji oznaczonych jako Claude Code to fizycznie logi Cursora. Parser wybiera format po treści.
- Claude Code dzieli jedną odpowiedź na kilka linii z tym samym `message.id`, a `output_tokens` rośnie między nimi. Trzeba brać maksimum, nie pierwszą wartość.
- Codex stempluje ostatnie wywołanie tury już po następnym promptcie użytkownika (w 8 966 z 13 441 tur). Bez korekty każda analiza czasu reakcji człowieka na Codexie jest fałszywa.
- Codex nigdy nie ustawia flagi błędu narzędzia (0 z 309 060), więc jego wskaźnik błędów to strukturalne zero.
- Cursor nie loguje ani tokenów, ani timestampów, ani wyników narzędzi.
- Thinking w Claude Code jest pusty: zostają tylko zaszyfrowane sygnatury (255 KB sygnatur na 9 KB tekstu w próbce).
- OpenCode zapisuje sesję jako jeden ładnie sformatowany JSON, nie JSONL.

### 2.3 Cztery warstwy

| Warstwa | Co | Koszt | Czas |
|---|---|---|---|
| 1 | 24 tezy jako SQL w DuckDB na całej populacji | 0 | 10 s |
| 1b | Sondy na surowych plikach, 3 000 losowych próbek na sondę, dla rzeczy, których ledger nie przechowuje | 0 | 11 s |
| 2 | Klasyfikacja wszystkich 87 887 promptów ludzkich przez DeepSeek V4-Flash | 3,64 USD | 3 min |
| 3 | Sędzia DeepSeek V4-Pro na 1 400 przypadkach wybranych przez warstwę 1 | 1,96 USD | 2 min |

Zasada: model czyta tylko to, co wymaga osądu. Wszystko, co da się policzyć deterministycznie, jest policzone na całości i za darmo.

### 2.4 Cennik (USD za milion tokenów)

| Model | input | odczyt cache | zapis cache 5 min | zapis cache 1 h | output |
|---|---|---|---|---|---|
| claude-opus-4-5 do 4-8 | 5 | 0,5 | 6,25 | 10 | 25 |
| claude-sonnet-4-5, 4-6 | 3 | 0,3 | 3,75 | 6 | 15 |
| claude-sonnet-5 | 2 | 0,2 | 2,5 | 4 | 10 |
| claude-fable-5 | 10 | 1 | 12,5 | 20 | 50 |
| claude-haiku-4-5 | 1 | 0,1 | 1,25 | 2 | 5 |
| gpt-5.5 | 5 | 0,5 | | | 30 |
| gpt-5.4 | 2,5 | 0,25 | | | 15 |
| gpt-5.4-mini | 0,75 | 0,075 | | | 4,5 |
| gpt-5.3-codex | 1,75 | 0,175 | | | 14 |

OpenAI raportuje `input_tokens` łącznie z cache, więc koszt to (input minus cache) razy cena plus cache razy cena cache. Modele spoza tabeli (glm, qwen, mimo, gemini, darmowe endpointy OpenCode) są niewycenione: 2,9% wywołań.

---

## 3. Warstwa 1: dwadzieścia cztery tezy na całej populacji

### T01. Rachunek to cache

| Składnik | Udział w koszcie |
|---|---|
| Odczyty cache | 63,9% |
| Zapisy cache | 22,3% |
| Output | 9,2% |
| Świeży input | 4,6% |

Łącznie 116 677 USD: Claude Code 96 741 (83%), Codex 19 048 (16%), OpenCode 887, Cursor niewyceniony. Mediana sesji około 2,5 USD, ale rozkład ma bardzo długi ogon (najdroższa sesja 1 678 USD).

Per model: claude-opus-4-6 37 314 USD, z czego 24 374 to odczyty cache i 10 332 zapisy; opus-4-7 29 285; opus-4-8 21 444; gpt-5.5 15 697; fable-5 4 739 w zaledwie 88 sesjach.

Koszt na linię w commicie według trybu (tryby jak w paperze: vibe to atrybucja agenta co najmniej 95%, human co najwyżej 5%):

| Tryb | Sesje | USD | Linie w commicie | USD na linię | Tokeny kontekstu na linię |
|---|---|---|---|---|---|
| human | 2 574 | 37 041 | 12 959 502 | 0,0029 | 3 830 |
| collab | 2 018 | 21 772 | 3 296 891 | 0,0066 | 8 754 |
| vibe | 4 072 | 34 809 | 1 799 204 | 0,0193 | 26 099 |

Vibe coding kosztuje na linię 6,7 razy więcej niż tryb human i 2,9 razy więcej niż collab. Paper podaje "około 3 razy" względem collab, więc zgodność. Zastrzeżenie: w trybie human linie w commicie pisze człowiek, więc ten mianownik mierzy co innego.

### T02. Cena kawy

Cache prompt w Claude Code żyje 5 minut (starsze wersje) albo godzinę (nowsze, w zbiorze dominują zapisy 1h: 1 006 mln tokenów na opus-4-6 kontra 44 mln zapisów 5m). Jeśli człowiek nie odpowie przed wygaśnięciem, cały kontekst jest zapisywany od nowa po cenie 1,25 do 2 razy wyższej niż zwykły input.

| Przerwa przed wywołaniem | Wywołań | Odsetek pęknięć cache | USD zapisów cache na pęknięciach |
|---|---|---|---|
| poniżej 1 min | 582 011 | 0,6% | 2 977 |
| 1 do 5 min | 59 077 | 2,4% | 2 007 |
| 5 do 60 min | 20 781 | 7,8% | 2 371 |
| ponad 60 min | 3 629 | 83,6% | 6 852 |

Pęknięcie definiujemy jako zapis cache co najmniej połowy rozmiaru poprzedniego kontekstu. Wywołania po przerwie ponad 5 minut to 3,7% wszystkich, a odpowiadają za 39% kosztu zapisów cache i 8% całego rachunku (9 223 USD liczone tylko na pęknięciach; 10 195 USD licząc wszystkie zapisy po takich przerwach). To koszt czysto harnessowy: po godzinnej przerwie najtańszą decyzją byłoby dopisanie krótkiego "ping" przed końcem TTL albo świadome zaczęcie nowej sesji.

### T03. Zero bitów informacji

16% wyników narzędzi to dokładne powtórki wcześniejszego wyniku w tej samej sesji (identyczny hash), ale tylko 2,1% znaków, bo większość powtórek to krótkie potwierdzenia edycji ("The file has been updated successfully") i identyczne `git status`. Bezpośredni koszt jest mały (68 USD po cenie świeżego inputu), ale każde powtórzenie zostaje w kontekście i płaci czynsz z T04.

### T04. Czynsz za kontekst

Token wrzucony do kontekstu w n-tym wywołaniu jest opłacany ponownie w każdym kolejnym. Czynsz wyniku narzędzia = jego tokeny razy liczba późniejszych wywołań w sesji, wyceniony po cenie odczytu cache.

W Claude Code wyniki narzędzi odpowiadają za 51% wszystkich tokenów odczytu cache: 30 746 USD. Rozkład:

| Harness | Narzędzie | Wyników | Znaków | Śr. późniejszych wywołań | Czynsz USD |
|---|---|---|---|---|---|
| Claude Code | Read | 141 736 | 782 mln | 190 | 15 712 |
| Claude Code | Bash | 283 632 | 289 mln | 224 | 7 175 |
| Claude Code | MCP | 12 384 | 279 mln | 191 | 3 804 |
| Claude Code | Task (subagenci) | 17 622 | 91 mln | 183 | 1 898 |
| Claude Code | Grep | 38 784 | 41 mln | 180 | 830 |

Wyniki powyżej 10 tys. znaków to 5,3% wszystkich, a generują 61% czynszu. Dla Codexa model "wynik siedzi w kontekście do końca sesji" załamuje się przez kompakcję i sesje po 10 tys. wywołań: nominalny czynsz Basha w Codexie (134 tys. USD) jest 10 razy wyższy niż realny wolumen odczytów cache, więc podajemy go jako górną granicę, a nagłówek opiera się na Claude Code.

### T05. Ile kosztuje pusty prompt

Pierwsze wywołanie w sesji zapisuje do cache prompt systemowy plus definicje narzędzi. Mediana w Claude Code: 26 796 tokenów w wersji 2.1.17, 28 689 w 2.1.195 (plus 7%), z wyraźnym dołkiem około 9 do 13 tys. w wersjach 2.1.39 do 2.1.56. Codex: mediana 19 do 27 tys., wersje alpha 51 do 54 tys. Łącznie koszt wejścia do sesji to 1 154 USD, 1% rachunku. Wniosek: sam prompt systemowy nie jest problemem, problem zaczyna się w trakcie sesji.

### T06. Ucięte odpowiedzi

40 wywołań ze `stop_reason = max_tokens` w 25 sesjach, 2,68 USD dokończeń. Pomijalne.

### T07. Zgadywanie ścieżek

1 989 wywołań Read, Edit lub Write na nieistniejący plik (0,57% wywołań plikowych) w 1 209 sesjach. Trzy kolejne wywołania po takim błędzie kosztują 644 USD (0,55%). Codex ma tu strukturalne zero, bo nie flaguje błędów.

### T08. Ceremonia

TaskCreate, TaskUpdate, TodoWrite, update_plan: 31 158 wywołań, 2,9% wszystkich, 15,8 mln tokenów wyjściowych, 381 USD, 3,5% kosztu outputu. Niewielki koszt, ale zerowa zawartość kodu.

### T09. Czekanie na build w pętli

10 316 wywołań Bash z `sleep` albo `gh run watch` (2% Bashy) w 1 127 sesjach, 1 359 USD kontekstu na tych wywołaniach; 4 626 z nich to serie co najmniej dwóch pod rząd. Każde sprawdzenie statusu płaci cały kontekst.

### T10. Przepisywanie zamiast edycji

26,5% wywołań Write dotyczy plików, które model miał już w kontekście (czytał je albo edytował wcześniej): 6 282 przepisania, 8,2 mln tokenów wyjściowych, 187 USD. Edycje z `old_string` powyżej 1 500 znaków (model kopiuje pół pliku, żeby zmienić linijkę): 94 USD. Mediana narzutu serializacji JSON na treść w Write: 8%. Sędzia z warstwy 3 ocenia, że 80% takich przepisań było zbędne.

### T11. Nieprzeczytane odpowiedzi

Bierzemy ostatnią odpowiedź tekstową przed następnym promptem człowieka, liczymy czas potrzebny na przeczytanie przy 250 słowach na minutę i porównujemy z czasem, po jakim człowiek odpisał. Jeśli odpisał w mniej niż połowie tego czasu, nie mógł przeczytać.

| Harness | Odpowiedzi końcowych | Nieprzeczytanych | Udział tokenów nieprzeczytanych | Mediana czasu na przeczytanie | Mediana czasu do odpowiedzi |
|---|---|---|---|---|---|
| Claude Code | 55 223 | 11,8% | 20,2% | 30 s | 99 s |
| Codex | 9 501 | 23,8% | 26,5% | 49 s | 95 s |
| OpenCode | 1 804 | 6,4% | 20,2% | 43 s | 170 s |

21% tokenów końcowych odpowiedzi trafia do nikogo. W dolarach to tylko 89 USD, bo output końcowy jest tani; koszt prawdziwy to czynsz tych akapitów w kolejnych wywołaniach i uwaga człowieka.

### T12. Godziny ludzkie kontra tokeny

Suma czasu od promptu człowieka do ostatniego wywołania agenta w turze: 16 358 godzin pracy agenta; człowiek na pisanie i myślenie wydał 3 337 godzin. Tokeny w tych turach: 113 945 USD, czyli 7 USD za godzinę pracy agenta. Gdyby człowiek patrzył na spinner za 60 USD/h, jego czas kosztowałby 981 tys. USD, 8,6 razy więcej niż tokeny. Mediana tury agenta 70 s, 90. percentyl 686 s w Claude Code. To jest górna granica (założenie, że człowiek czeka), ale nawet jeśli patrzy w jednej czwartej przypadków, czas ludzki nadal przebija rachunek za API.

Per tryb: vibe 8,0 razy, human 7,4, collab 10,0. Wniosek dla producentów harnessów: opłaca się płacić więcej za tokeny, jeśli skraca to czas tury.

### T13. Porzucone sesje

1 088 sesji (11,7%) bez ani jednej linii w commicie: 28 626 USD, 24,5% rachunku. Ale 23 054 USD z tego to sesje bez atrybucji w ogóle (602 sesje, mediana 9 promptów i 109 wywołań narzędzi, czyli długie, poważne sesje, których job atrybucji nie objął), a tylko 5 572 USD to prawdziwe "zero linii". Sześć najdroższych "porzuconych" sesji (od 676 do 1 678 USD) to wszystkie sesje bez atrybucji. Ta teza wymaga uzupełnienia danych, nie interpretacji.

### T14. Gorące pliki

518 plików edytowanych w co najmniej 10 sesjach tego samego repo skupia 20,6% wszystkich 186 775 edycji. W medianowym repo 5% plików bierze 33,8% edycji. Rekordziści: `manual_commit_hooks.go` w E2E-Solution/cli (120 sesji, 8 użytkowników, 745 edycji), `main.tex` w henryph24/neuralips26 (91 sesji, 1 użytkownik, 2 012 edycji), `explain.go` w entireio/cli-checkpoints (86 sesji, 13 użytkowników).

Edycje gorących plików nie są bardziej błędogenne niż zimnych (6,8% kontra 7,7% edycji z błędem w następnych 3 wywołaniach), ale 51 do 80% edycji gorących plików jest natychmiast korygowanych krótkim promptem człowieka. Przyczyny rozstrzyga sędzia w warstwie 3.

### T15. Harness kontra model

47 repozytoriów ma sesje z co najmniej dwóch harnessów. Rozpiętość kosztu na linię w commicie między najtańszym a najdroższym: 78 razy, ale ta liczba jest zdominowana przez OpenCode na darmowych modelach i dużych commitach. Uczciwsze zestawienie w obrębie trybu:

| Tryb | Claude Code | Codex | OpenCode |
|---|---|---|---|
| collab | 0,037 | 0,0036 | 0,0003 |
| human | 0,017 | 0,015 | 0,0012 |
| vibe | 0,084 | 0,049 | 0,0005 |

W tym samym repo (blackgirlbytes/planetfall-seed-signalk) Codex 0,086 USD na linię kontra Claude Code 0,052. Wniosek: porównanie harnessów bez kontroli modelu i trybu jest bezwartościowe, a z kontrolą różnice są rzędu 1,5 do 2 razy, nie 78.

### T16. Subagenci

Wywołań z flagą sidechain jest tylko 300 (2,62 USD), bo transkrypty subagentów w Claude Code nie są w zbiorze. Za to narzędzie Task uruchomiono 20 622 razy w 3 741 sesjach, a jego wyniki (94 mln znaków) płacą 1 898 USD czynszu. Koszt samych subagentów jest niewidoczny w danych.

### T17. Tryby uprawnień

| Tryb | Sesje | USD na linię | Błędy narzędzi | Sesje z commitem | Mediana USD sesji |
|---|---|---|---|---|---|
| bez zdarzeń (starsze wersje) | 5 330 | 0,004 | 4,1% | 90,1% | 2,45 |
| bypassPermissions | 719 | 0,024 | 3,0% | 89,7% | 3,46 |
| acceptEdits | 360 | 0,037 | 2,6% | 81,1% | 13,4 |
| auto | 356 | 0,025 | 2,6% | 83,1% | 8,95 |
| default | 437 | 0,048 | 3,2% | 73,7% | 2,25 |
| plan | 27 | 0,015 | 3,6% | 92,6% | 3,32 |

Hipoteza "bypass = więcej śmieci" się nie potwierdza: bypass jest tańszy na linię niż default i ma mniej błędów. Sesje w acceptEdits są za to 4 razy droższe (mediana 13,4 USD): to tryb długich, ciężkich sesji.

### T18. Niecierpliwość

4 260 przerwań w 1 948 sesjach, 5 259 USD utopione w przerwanych turach (4,5% rachunku). 254 171 operacji na kolejce (użytkownik dopisuje, gdy agent pracuje). Koszt na linię w sesjach z przerwaniami i bez jest taki sam, więc przerwania nie są oznaką rozrzutnych sesji, tylko normalnym sterowaniem.

### T19. Kompakcja jako placebo

2 907 granic kompakcji w 1 048 sesjach Claude Code. W 20 wywołaniach narzędzi po kompakcji 56% Readów dotyczy plików, które model już czytał przed kompakcją: 35 mln znaków ponownie wciągniętych. Kompakcja oszczędza kontekst, ale model natychmiast odbudowuje część z niego, płacąc za odczyt i za ponowny zapis do cache (53 USD po cenie zapisu).

### T20. Model czyta to, co sam napisał

23 104 Ready pliku, który model zapisał albo edytował w poprzednich 5 wywołaniach (14,3% wszystkich Readów, 49 mln znaków). 28,5% edycji leży w oknie "ten sam plik edytowany co najmniej 3 razy w 10 wywołaniach", czyli model kłóci się z samym sobą.

### T21. Tryb fast

0,65% wywołań Claude Code, 648 USD, 42 sesje. Za mało, żeby zmierzyć wpływ na czas.

### T22. Naturalny eksperyment ze zmianą modelu

93 pary użytkownik i repozytorium, w których ta sama osoba używała co najmniej dwóch modeli w co najmniej 3 sesjach każdy (23 modele, 6 419 sesji, 77 343 USD). Mediana stosunku kosztu na linię między najdroższym a najtańszym modelem w obrębie pary: 8,5 razy. To jest test, którego żadne laboratorium nie zrobi, bo wymaga prawdziwego użytkownika na prawdziwym repo; szczegóły per para w `T22_model_switch__*.csv`.

### T23. Noc (tylko Codex, który loguje strefę czasową)

1 167 sesji Codexa ze strefą. 11,9% startuje w nocy (0 do 6 lokalnie), porzucenie nocne 23,0% kontra 17,4% w dzień, koszt na linię w nocy 0,049 USD kontra 0,012 w dzień. Ostrożnie: mała próba, ale kierunek jest wyraźny.

### T24. Harness pisze prompt

Znaki po stronie promptu, których człowiek nie napisał (system-reminders, wyniki hooków, przypomnienia o zadaniach, diagnostyka): 376,8 mln, kontra 126,2 mln napisanych przez ludzi. 74,9% strony promptu to szept harnessu, w 235 503 zdarzeniach załączników. Największe źródła: linie `progress` w Claude Code (2,96 mld znaków, ale to zapis lokalny, nie kontekst), obrazy użytkownika (634 mln znaków w 2 027 zdarzeniach, mediana 203 tys. znaków na obraz), wyniki `exec_command_end` w Codexie (252 mln), zdarzenia kompakcji w Codexie (222 mln), `hook_success` w Claude Code (156 mln w 119 287 zdarzeniach).

---

## 4. Warstwa 1b: sondy na surowych plikach

Ledger przechowuje długości i hashe, nie treść. Cztery sondy po 3 000 losowych próbek (ziarno stałe, 100% trafień w surowe rekordy):

### Numery linii w Read

Claude Code zmienił format: starsze wersje zwracają `cat -n` (numer i tabulator), nowsze `N→`, OpenCode `N: `. Udział samych prefiksów w znakach wyniku: 8,3% dla tabulatora, 16,0% dla strzałki, 12,4% dla dwukropka; średnia ważona 9,3% wszystkich 920 mln znaków z Read, czyli 21 mln tokenów, 89 USD po cenie inputu (bez czynszu).

### Obrazki

1,4% wywołań Read zwraca obraz w base64 (zrzuty ekranu, PNG, `/tmp/page_25-25.png`), ale to 33% wszystkich znaków z Read: 260 mln znaków, około 65 mln tokenów, 311 USD po cenie inputu i wielokrotnie więcej w czynszu. Wyłącznie Claude Code. Tego nie było w żadnej hipotezie.

### Narzut serializacji w Write i Edit

| Harness i narzędzie | Mediana narzutu JSON | Ważony znakami |
|---|---|---|
| Claude Code Edit (old_string i new_string) | 13,0% | 10,2% |
| Claude Code Write | 5,8% | 7,3% |
| OpenCode edit | 7,0% | 5,8% |
| Codex apply_patch | 4,0% | 4,8% |

Wcięcia i nowe linie w treści: rs 16%, tsx 19%, py 14%, go 3%, md 2%. Narzut JSON na wszystkie 337 mln bajtów argumentów: 6,9 mln tokenów, 167 USD po cenie outputu; wcięcia 140 USD. Codex z apply_patch jest strukturalnie o połowę tańszy w serializacji niż Edit Claude Code, bo patch to jeden surowy string.

### Wyniki Bash

1,33 mld znaków wyników Bash w zbiorze (Codex sam 1,0 mld, 3,5 razy więcej niż Claude Code).

| Stopień kompresji gzip | Udział wyników | Udział znaków |
|---|---|---|
| poniżej 2 | 58,2% | 7,0% |
| 2 do 3 | 22,4% | 24,1% |
| 3 do 5 | 14,3% | 35,4% |
| 5 do 10 | 4,5% | 25,8% |
| 10 do 20 | 0,5% | 6,2% |
| 20 i więcej | 0,1% | 1,4% |

93% znaków z Bash siedzi w wynikach, które gzip ściska co najmniej dwukrotnie. Czysta redundancja (znaki razy 1 minus 1/stopień): 953 mln znaków, 238 mln tokenów, około 1 050 USD po cenie inputu, z czego około 800 USD w Codexie. To największa pojedyncza liczba w sondach i największa dźwignia dla harnessów: streszczanie albo obcinanie logów przed wrzuceniem do kontekstu.

### Końcowe odpowiedzi

65 229 odpowiedzi końcowych, 63,4 mln znaków. Claude Code: mediana 603 znaki, 1,1 nagłówka i 3,3 punktora na odpowiedź, 34,6% znaków w liniach punktowanych, sekcje "podsumowanie" tylko 1,8%. Codex: mediana 226 znaków, 0,17 nagłówka. Cursor: mediana 1 535 znaków. OpenCode: 72% znaków w punktorach. "Gadatliwe zakończenia" to listy, nie akapity podsumowań.

---

## 5. Warstwa 2: co ludzie piszą do agentów

87 887 promptów napisanych przez ludzi (po odsianiu 33 348 wiadomości wstrzykniętych przez harness), sklasyfikowanych przez DeepSeek V4-Flash z kontekstem poprzedniej odpowiedzi agenta i ostatnich narzędzi. 0 błędów, 3,64 USD.

| Etykieta | Claude Code | Codex | Cursor | OpenCode | Razem | Udział |
|---|---|---|---|---|---|---|
| follow_up (kolejny krok) | 21 047 | 4 478 | 422 | 1 062 | 27 009 | 30,7% |
| meta_other | 10 900 | 2 843 | 240 | 80 | 14 063 | 16,0% |
| question | 9 978 | 2 202 | 276 | 316 | 12 772 | 14,5% |
| approval ("ok, dawaj") | 8 919 | 2 238 | 124 | 329 | 11 610 | 13,2% |
| new_task | 6 541 | 1 443 | 170 | 727 | 8 881 | 10,1% |
| failure_report (nie działa) | 5 836 | 838 | 79 | 301 | 7 054 | 8,0% |
| correction (źle, miało być inaczej) | 4 178 | 915 | 111 | 142 | 5 346 | 6,1% |
| interruption | 338 | 791 | 10 | 13 | 1 152 | 1,3% |

Pushback (korekta, zgłoszenie błędu albo jawne niezadowolenie): Claude Code 15,5%, Codex 12,4%, Cursor 14,9%, OpenCode 16,0%. Paper podaje 44% tur z pushbackiem, ale liczy szerzej (włącznie z przerwaniami i doprecyzowaniami) i na innej definicji tury; nasza definicja jest węższa i bardziej konserwatywna.

Sentyment: 90,8% neutralny, 6,6% pozytywny, 2,6% sfrustrowany. Języki: 93,5% angielski, 2,7% japoński, 2,0% chiński. 22,4% promptów wymienia konkretny plik.

### Koszt tego, co człowiek powiedział

Łączymy etykietę promptu z kosztem wszystkich wywołań agenta aż do następnego promptu:

| Etykieta promptu | Tur | USD tur po nim | Udział w rachunku | Mediana USD tury | Mediana wywołań |
|---|---|---|---|---|---|
| follow_up | 25 980 | 38 898 | 34,1% | 0,49 | 5 |
| approval | 11 287 | 20 801 | 18,2% | 0,56 | 6 |
| meta_other | 10 557 | 15 320 | 13,4% | 0,38 | 3 |
| new_task | 8 195 | 13 815 | 12,1% | 0,76 | 10 |
| failure_report | 6 715 | 9 245 | 8,1% | 0,60 | 6 |
| question | 12 442 | 9 104 | 8,0% | 0,25 | 2 |
| correction | 5 193 | 6 505 | 5,7% | 0,43 | 5 |
| interruption | 448 | 414 | 0,4% | 0,26 | 2 |

Tury po korekcie i zgłoszeniu błędu to 13,8% rachunku (15 750 USD); po wszystkich promptach oznaczonych jako pushback 14,5% (16 548 USD). To jest cena mówienia agentowi, że zrobił to źle. Tury po sfrustrowanym promptcie nie są droższe od neutralnych (mediana 0,53 kontra 0,51 USD), więc frustracja nie eskaluje kosztu, tylko oznacza, że koszt już poszedł.

Najdroższą kategorią jest "approval": 18% rachunku uruchamia dwuliterowe "ok". To tury, w których agent dostaje wolną rękę po zaprezentowaniu planu.

---

## 6. Warstwa 3: sędzia na przypadkach wybranych przez SQL

DeepSeek V4-Pro czyta wycinek surowego transkryptu wokół wskazanego wywołania (skompaktowany, bez sygnatur i załączników, wyniki narzędzi obcięte do 2 500 znaków) i odpowiada w ustalonym JSON. Próbki są stratyfikowane po harnessie i trybie, a każda ma warstwę "top" (najdroższe przypadki według warstwy 1) i "losową". Przedziały ufności Wilsona 95%.

### 6.1 Czy pełne przepisanie pliku było potrzebne (636 przypadków, 0,72 USD)

Pytanie: model zapisuje Write na plik, który miał już w kontekście. Czy pełne przepisanie było potrzebne, czy wystarczyła edycja?

| Warstwa próby | Harness i tryb | Przypadków | Niepotrzebne przepisania |
|---|---|---|---|
| losowa | Claude Code vibe | 40 | 92,5% |
| losowa | Claude Code human | 40 | 87,5% |
| losowa | Cursor | 43 | 95,3% |
| losowa | OpenCode | 112 | 87,5% |
| losowa | Codex | 61 | 44,3% |
| top według rozmiaru | Claude Code | 269 | 66,2% |
| top według rozmiaru | Codex | 17 | 23,5% |
| razem losowa | | 336 | 79,8% |
| razem top | | 300 | 63,3% |

Przy dużych plikach odsetek spada, bo tam częściej faktycznie trzeba przebudować całość. Codex wypada radykalnie lepiej we wszystkich warstwach, bo jego narzędzie edycji (apply_patch) nie ma trybu "zapisz cały plik" jako domyślnego. To argument, że o marnotrawstwie decyduje projekt narzędzia, nie inteligencja modelu. Typowe uzasadnienie sędziego: "agent właśnie przeczytał plan, chciał zmienić dwie linie w sekcji todo i zapisał cały plik od nowa".

Pole "ile linii naprawdę się zmieniło" wyszło zerowe, bo sędzia nie widzi pełnej treści po kompaktowaniu wycinka. Nie używamy go.

### 6.2 Czy duży wynik narzędzia został użyty (612 przypadków, 1,02 USD)

Pytanie: wynik narzędzia powyżej 5 tys. znaków wpadł do kontekstu. Czy model odwołał się do niego później i jaka część była potrzebna?

| Potrzebna część wyniku | Udział |
|---|---|
| żadna | 32,5% |
| mały fragment | 64,2% |
| większość | 3,2% |
| całość | 0,2% |

Odsetek nigdy nieużytych wyników per narzędzie: Claude Code Glob 56%, Read 27 do 30%, Bash 16%, WebFetch 24%; Codex Bash 33%, MCP 44%; OpenCode Glob 45%, Read 36%. Warstwa "top według czynszu" i "losowa" dają identyczny wynik (32,3% kontra 32,4%), więc to jest własność populacji, nie ogona. W połączeniu z T04: co najmniej jedna trzecia z 30 746 USD czynszu w Claude Code to czynsz za dane, których model nigdy nie tknął, a 97% to czynsz za dane, z których potrzebował ułamka.

### 6.3 Dlaczego plik jest gorący (200 przypadków, 40 plików, 0,22 USD)

| Przyczyna | Udział |
|---|---|
| hub architektoniczny (każda zmiana przez niego przechodzi) | 55,0% |
| regresja agenta (naprawia to, co sam zepsuł) | 28,0% |
| plik testowy | 9,0% |
| iteracja użytkownika (świadome dopracowywanie) | 7,0% |
| churn konfiguracji, niejasne | 1,0% |

Pliki z najwyższym odsetkiem regresji agenta (60% w 5 przypadkach): `explain.go`, `lifecycle.go`, `manual_commit_hooks.go`, `resume.go`, `committed.go` w repozytoriach entireio i E2E-Solution oraz `backend/app/agent.py` w duckdb-data-agent. Pliki dokumentacyjne i konfiguracyjne (README, sprint-status.yaml, CLAUDE.md, package.json): 0% regresji. Wniosek: co czwarta edycja gorącego pliku to agent sprzątający po sobie, ale ponad połowa to po prostu architektura repozytorium.

---

## 7. Syntezy krzyżowe

### Gdzie naprawdę siedzą pieniądze

Składając T01, T02, T04, sondy i sędziego w jeden obraz dla Claude Code (83% rachunku):

| Mechanizm | Kwota | Kto o tym decyduje |
|---|---|---|
| Odczyty cache łącznie | około 61 800 USD | harness (co trzyma w kontekście) |
| w tym czynsz za wyniki narzędzi | 30 746 USD | harness (obcinanie, streszczanie) |
| w tym za wyniki nigdy nieużyte (32,5% z sędziego) | około 10 000 USD | model (co czyta) i harness (ile zwraca) |
| Zapisy cache po przerwach ponad 5 min | 9 223 USD | harness (TTL, ping, resume) |
| Tury po pushbacku | 16 548 USD (cały zbiór) | model (jakość) |
| Output końcowych odpowiedzi, których nikt nie czyta | 89 USD plus czynsz | model (długość) |
| Ceremonia, polling, zgadywanie ścieżek, ucięcia | około 2 400 USD | model |

Trzy pierwsze pozycje to ponad 60% rachunku i wszystkie są w rękach twórców harnessu, nie modelu.

### Narzędzie edycji jest ważniejsze od modelu

Ten sam sędzia, ta sama rubryka: Codex 44% zbędnych przepisań, reszta 87 do 95%. Ten sam pomiar serializacji: apply_patch 4,8% narzutu, Edit 10,2%. Ten sam pomiar Basha: Codex 3,5 razy więcej znaków wyników niż Claude Code. Każdy harness marnuje inaczej i zależy to od projektu narzędzi, a nie od tego, który model pod spodem.

### Człowiek jest droższy niż API

T12 (8,6 razy) i T11 (21% tekstu do nikogo) razem mówią, że metryką do optymalizacji jest czas tury i długość tego, co człowiek musi przeczytać, a nie liczba tokenów. Harness, który skróci turę o 20% płacąc 20% więcej tokenów, jest netto tańszy.

---

## 8. Zastrzeżenia

1. **Cursor** nie ma tokenów, timestampów ani wyników narzędzi. Występuje tylko w liczeniu wywołań i u sędziego.
2. **Codex nie flaguje błędów narzędzi**, więc każda metryka "błąd narzędzia" dla Codexa to zero z definicji, nie z jakości.
3. **731 sesji bez atrybucji**, w tym najdroższe w zbiorze. "Porzucone" (T13) jest w większości luką w danych.
4. **Czynsz dla Codexa** to górna granica: model "wynik zostaje do końca sesji" nie uwzględnia kompakcji.
5. **Sędzia to DeepSeek V4-Pro**, nie człowiek. Rubryki są wąskie i binarne, przedziały ufności podane. Tryb thinking DeepSeeka trzeba było wyłączyć, bo zjadał limit tokenów i zwracał puste odpowiedzi.
6. **Klasyfikacja promptów**: w 3 z 88 tys. odpowiedzi model zwrócił zły typ pola; skorygowane deterministycznie.
7. **Stosunek czasu ludzkiego do tokenów** zakłada, że człowiek czeka. To górna granica; dolna to około 3 337 godzin samego pisania i myślenia.
8. **Ceny** są z dnia analizy. DeepSeek zapowiada cennik dzienny/nocny, Anthropic i OpenAI mają wyższe stawki dla długiego kontekstu (ponad 272 tys. tokenów u OpenAI), których nie uwzględniliśmy; realne koszty Codexa są więc zaniżone.
9. **Populacja** to użytkownicy, którzy zainstalowali Entire.io na publicznych repozytoriach; jest tu nadreprezentacja hackathonów i repozytoriów samego Entire (entireio/cli-checkpoints 1 305 sesji, E2E-Solution/cli 832).
10. **Tokeny liczone jako znaki przez 4** wszędzie tam, gdzie surowe usage nie rozbija wyniku narzędzia.

---

## 9. Rekomendacje, które wynikają wprost z liczb

Dla twórców harnessów:

- Obcinać i streszczać wyniki Bash przed wrzuceniem do kontekstu; 93% ich znaków to powtarzalny szum, a 32% dużych wyników nigdy nie jest użytych.
- Nie zwracać obrazów jako base64 w Read domyślnie; 1,4% wywołań robi 33% znaków.
- Usuwać z kontekstu wyniki narzędzi starsze niż N wywołań (context editing), zamiast czekać na kompakcję, po której model i tak czyta te same pliki ponownie (56%).
- Pilnować TTL cache: ping przed wygaśnięciem albo jawne "zacznij nową sesję" po przerwie ponad godzinę; 8% rachunku.
- Preferować narzędzie edycji typu patch nad "zapisz cały plik"; różnica między 44% a 90% zbędnych przepisań.
- Zredukować wstrzykiwane przypomnienia; harness pisze 75% promptu.

Dla użytkowników:

- Krótkie przerwy albo nowa sesja po dłuższej; nie zostawiać sesji na godzinę i wracać.
- Prosić o krótkie odpowiedzi końcowe; 21% i tak nie jest czytane.
- Tryb bypass nie jest droższy ani bardziej błędogenny; ostrożność kosztuje czas, nie oszczędza tokenów.

Dla badaczy:

- Atrybucja per plik i transkrypty subagentów zamknęłyby dwie największe dziury w danych.
- Flaga błędu w Codexie i timestampy w Cursorze.

---

## 10. Gdzie co leży

| Plik | Zawartość |
|---|---|
| `analysis/DESIGN.md` | architektura czterech warstw i definicje wszystkich tez |
| `analysis/README.md`, `analysis/SPEC.md` | schemat ledgera i mapowanie per harness |
| `analysis/ledger/` | pięć tabel Parquet, 248 MB |
| `analysis/ledger.duckdb` | baza z wycenionymi wywołaniami i widokami pomocniczymi |
| `analysis/queries/T01..T24.sql, C01..C03.sql` | tezy i generatory przypadków |
| `analysis/results/REPORT.md` | pełny automatyczny raport warstwy 1, 121 tabel CSV obok |
| `analysis/results/probes/PROBES.md` | sondy |
| `analysis/results/llm/PROMPT_LABELS.md`, `prompt_labels.parquet` | klasyfikacja promptów |
| `analysis/results/llm/JUDGE_*.md`, `judge_*.parquet` | werdykty sędziego |
| `analysis/results/findings.html` | wizualizacja |

Odtworzenie całości od zera: `build_ledger.py` (24 s), `run_queries.py --rebuild` (10 s), `raw_probes.py` (11 s), `llm/classify_prompts.py` i `llm/judge.py` (5 min, około 6 USD, wznawialne z cache).
