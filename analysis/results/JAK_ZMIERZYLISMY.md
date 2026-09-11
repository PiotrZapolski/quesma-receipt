# Jak dokładnie to zmierzyliśmy

Sześć tez, każda w tym samym układzie: co wzięliśmy z sesji, co z czym porównaliśmy, jak z tego wynika wniosek, jakie liczby to potwierdzają, gdzie jest słabe miejsce i co na to odpowiadamy. Wszystko liczone na całym zbiorze (9 770 sesji), nie na próbce, chyba że napisano inaczej.

## Wspólny fundament

**Surowiec.** Każda sesja to plik JSONL z pełnym zapisem: każda odpowiedź modelu z licznikami tokenów (input, odczyt cache, zapis cache, output), każde wywołanie narzędzia z argumentami, każdy wynik narzędzia, każdy prompt człowieka, wszystko z timestampami co do milisekundy. Do tego katalog metadanych z linkiem do commita: ile linii weszło do commita i jaki procent z nich napisał agent.

**Ledger.** Przepisaliśmy te pliki do pięciu płaskich tabel: jedno wywołanie API to jeden wiersz, jedno wywołanie narzędzia to jeden wiersz, jeden prompt to jeden wiersz. Sprawdziliśmy zgodność z metadanymi: suma tokenów wyjściowych zgadza się co do tokena w 7 241 z 7 242 sesji Claude Code, liczba wywołań narzędzi ma medianę odchylenia 0%.

**Tura.** Tura zaczyna się promptem człowieka (pomijamy wiadomości wstrzyknięte przez harness i te bez ani jednego znaku napisanego przez człowieka) i obejmuje wszystkie odpowiedzi modelu do następnego promptu. Wywołania subagentów (flaga sidechain) nie wchodzą do tury.

**Tryb kodowania.** Z atrybucji Entire, tak jak w paperze SWE-chat: vibe = agent napisał co najmniej 95% linii w commicie, human = co najwyżej 5%, collab = pomiędzy, unknown = brak atrybucji.

**Koszt.** Każde wywołanie wycenione po oficjalnym cenniku swojego modelu, osobno input, odczyt cache, zapis cache (5 min i 1 h), output. Tam, gdzie znamy tylko liczbę znaków (wyniki narzędzi), przyjmujemy 4 znaki na token. Tam, gdzie liczymy linie kodu z liczby znaków, przyjmujemy 40 znaków na linię.

**Korekta na Codex.** Codex zapisuje licznik tokenów ostatniego wywołania tury dopiero przy starcie następnego, więc jego timestamp jest późniejszy niż następny prompt człowieka (8 966 z 13 441 tur). Wszędzie, gdzie liczymy czas między odpowiedzią a promptem, używamy ostatniego wywołania Codexa, którego timestamp jest wcześniejszy niż następny prompt. Bez tej korekty Codex wychodził na 99% nieprzeczytanych odpowiedzi, co było artefaktem.

---

## Teza 1. Linie w commicie kontra wygenerowany kod

**Co wzięliśmy z sesji.**
Z każdego wywołania Write bierzemy długość zapisywanej treści, z każdego Edit długość nowego fragmentu. Sumujemy per sesja i dzielimy przez 40, żeby mieć szacunkową liczbę wygenerowanych linii. Z metadanych bierzemy liczbę linii, które weszły do commita powiązanego z tą sesją.

**Co porównaliśmy.**
Wygenerowane linie kontra linie w commicie, per sesja, zgrupowane po harnessie i trybie kodowania. Tylko sesje, w których commit ma co najmniej jedną linię (w pozostałych nie ma mianownika). Osobno histogram stosunku commit/wygenerowane per sesja dla trybu vibe, z odcięciem sesji poniżej 400 wygenerowanych znaków (10 linii), żeby jedna poprawka w README nie dawała 3 000% przeżywalności.

**Na jakiej podstawie wniosek.**
W trybie vibe człowiek nie pisze kodu, więc wszystko w commicie pochodzi od agenta. Stosunek commit/wygenerowane jest wtedy wprost odsetkiem kodu agenta, który przeżył. W trybach human i collab commit zawiera też kod człowieka, więc stosunek przekracza 100% i nie mierzy przeżywalności, tylko mówi, że agent pisze mniej niż wchodzi do repo.

**Liczby.**
Vibe: Claude Code 730 640 linii w commicie na 1 431 976 wygenerowanych, 51%. Codex 97 763 na 567 394, 17%. OpenCode 29 540 na 116 522, 25%. Rozkład per sesja w vibe: 994 z 2 950 sesji ma poniżej 10% przeżywalności, 376 powyżej 100%. Koszt na linię w commicie: vibe 0,019 USD, collab 0,0066, human 0,0029.

**Słabe miejsce i odpowiedź.**
"40 znaków na linię to strzał." Tak, ale ten sam współczynnik działa w liczniku i mianowniku porównań między harnessami, więc ranking jest odporny. Bezwzględne 51% ma niepewność rzędu kilku punktów. "Codex edytuje przez apply_patch, jak to liczycie?" Dla Codexa bierzemy długość całego tekstu patcha (24 440 edycji, średnio 1 850 znaków), a patch zawiera też linie kontekstu i usuwane, nie tylko dodane. Wygenerowane linie Codexa są więc zawyżone, a jego 17% przeżywalności to dolna granica; realna wartość jest wyższa, ale nadal poniżej Claude Code, bo nawet po odjęciu połowy patcha wychodzi około 35%. "Sesje powyżej 100% w vibe." To sesje, gdzie commit objął też kod spoza sesji (np. wcześniejsze sesje bez własnego checkpointu); to ograniczenie atrybucji Entire, nie naszego pomiaru, i dotyczy 13% sesji.

---

## Teza 2. Nieprzeczytane odpowiedzi

**Co wzięliśmy z sesji.**
Dla każdej tury: ostatnia odpowiedź modelu zawierająca tekst (nie wywołanie narzędzia), jej długość w znakach i jej timestamp. Timestamp następnego promptu człowieka. Flaga, czy następny prompt to przerwanie (te tury wykluczamy, bo tam człowiek nie miał nic czytać). Z klasyfikacji promptów (warstwa 2) etykieta następnego promptu.

**Co porównaliśmy.**
Czas potrzebny na przeczytanie odpowiedzi kontra czas, po jakim człowiek odpisał. Czas na przeczytanie liczymy z długości: 5 znaków na słowo, 250 słów na minutę (typowe tempo czytania po angielsku, dolna granica dla programisty czytającego znany kontekst). Odpowiedź uznajemy za nieprzeczytaną, jeśli człowiek odpisał w mniej niż połowie tego czasu. Połowa, nie całość, żeby margines był po stronie ostrożności: ktoś mógł przeczytać szybciej albo tylko przeskanować.

**Na jakiej podstawie wniosek.**
Jeśli odpowiedź ma 900 słów (3,6 minuty czytania), a człowiek odpisał po 40 sekundach, to fizycznie nie mógł jej przeczytać. Nie wnioskujemy o intencji, tylko o możliwości. Zestawienie z etykietą następnego promptu pokazuje, co człowiek robi zamiast czytać: jeśli odpowiada "ok, rób" (approval) w 73 sekundy na 976 znaków, to zatwierdza bez czytania.

**Liczby.**
66 528 odpowiedzi końcowych z pełnym pomiarem. Nieprzeczytanych: Claude Code 11,8% odpowiedzi i 20,2% tokenów tekstu, Codex 23,8% i 26,5%, OpenCode 6,4% i 20,2%. Mediana czasu potrzebnego na przeczytanie 33 s, mediana czasu do odpowiedzi 99 s. Według etykiety następnego promptu: approval 18,0% nieprzeczytanych (10 599 tur, mediana odpowiedzi 976 znaków, mediana 73 s), follow_up 10,4%, correction 8,9%, failure_report 5,1%, new_task 6,0%. 385 odpowiedzi dłuższych niż 3 000 znaków zostało zatwierdzonych w czasie krótszym niż połowa czasu czytania.

**Słabe miejsce i odpowiedź.**
"Człowiek mógł czytać odpowiedź w trakcie streamowania, zanim się skończyła." Częściowo tak, i dlatego próg to połowa czasu, a nie całość; streamowanie w Claude Code trwa sekundy, a mediana długości to 30 s czytania. "Człowiek czyta tylko ostatni akapit." To jest dokładnie teza: reszta tekstu jest wygenerowana na darmo. "Tempo 250 słów na minutę jest arbitralne." Przy 400 słowach na minutę odsetek spada mniej więcej o połowę, przy 150 rośnie; kierunek i ranking harnessów się nie zmieniają. Wrażliwość jest do policzenia jednym parametrem.

---

## Teza 3. Ekonomia subagentów

**Co wzięliśmy z sesji.**
Flaga isSidechain na wywołaniu API (Claude Code oznacza nią wywołania wykonane przez subagenta). Wywołania narzędzia Task (Claude Code), które uruchamia subagenta: ich liczba per sesja, długość zwróconego wyniku. Koszt sesji, liczba linii w commicie, tryb.

**Co porównaliśmy.**
Najpierw sprawdziliśmy, ile w ogóle jest wywołań z flagą sidechain: 300 na 933 529. To znaczy, że transkrypty subagentów nie są w zbiorze (Entire zapisuje tylko główną sesję). Zatem koszt subagentów jest niewidoczny i nie da się policzyć zwrotu z nich wprost. Zamiast tego porównaliśmy sesje Claude Code, w których pojawia się Task, z sesjami bez Task, w obrębie tego samego trybu kodowania: mediana kosztu sesji (widocznego, czyli rodzica), koszt na linię w commicie, odsetek sesji z commitem.

**Na jakiej podstawie wniosek.**
Nie twierdzimy, że subagenci się nie opłacają, bo nie widzimy ich kosztu. Twierdzimy dwie rzeczy, które widzimy: (a) sesje z subagentami są kilkakrotnie droższe już na poziomie samego rodzica i mają wyższy koszt na linię w commicie w każdym trybie, (b) wyniki subagentów wracają do kontekstu rodzica jako tekst (91 mln znaków, mediana 3 136 znaków na wynik) i płacą czynsz jak każdy inny wynik narzędzia. Prawdziwy koszt jest więc wyższy niż widoczny o całość pracy subagentów.

**Liczby.**
Task: 17 833 wywołania w 3 542 sesjach Claude Code (49% sesji). Rozkład: 1 128 sesji z jednym wywołaniem, 1 024 z 2 do 3, 980 z 4 do 10, 355 z 11 do 30, 55 z ponad 30. Mediana kosztu sesji z Task kontra bez: vibe 4,44 kontra 1,45 USD, collab 5,32 kontra 1,59, human 6,72 kontra 1,14. Koszt na linię: vibe 0,035 kontra 0,023, collab 0,014 kontra 0,003, human 0,0039 kontra 0,0011. Odsetek sesji z commitem: bez różnicy (99% w vibe i collab), w human 89% kontra 82%. Czynsz wyników Task w kontekście rodzica: 1 898 USD.

**Słabe miejsce i odpowiedź.**
"Sesje z Task są droższe, bo są po prostu większe, a nie przez subagentów." Prawda, i dlatego to jest korelacja, nie przyczynowość; porównanie w obrębie trybu to wszystko, co można zrobić bez transkryptów subagentów. Tezę o zwrocie z subagentów należy na tych danych zgłosić jako lukę: "zbiór nie widzi połowy kosztu, a Task jest w połowie sesji". To samo w sobie jest wynikiem.

---

## Teza 4. Kompakcja jako placebo

**Co wzięliśmy z sesji.**
Zdarzenia systemowe compact_boundary i microcompact_boundary (Claude Code) oraz compacted (Codex): ich pozycja w sesji. Każde wywołanie Read: ścieżka pliku, pozycja w sesji, długość wyniku.

**Co porównaliśmy.**
Dla każdej granicy kompakcji bierzemy 20 kolejnych wywołań narzędzi po niej i wśród nich Ready. Dla każdego Reada sprawdzamy, czy ta sama ścieżka była czytana w tej samej sesji przed granicą. Jeśli tak, to jest ponowne wciągnięcie tego, co kompakcja właśnie wyrzuciła.

**Na jakiej podstawie wniosek.**
Kompakcja ma oszczędzać kontekst. Jeśli po niej model natychmiast czyta te same pliki, to oszczędność jest pozorna: kontekst wraca, a do tego płacimy za odczyt i za ponowny zapis do cache. Okno 20 wywołań jest krótkie celowo: pokazuje, co model robi od razu po kompakcji, nie w dalekiej przyszłości sesji.

**Liczby.**
Claude Code: 1 334 pełne kompakcje w 720 sesjach (10% sesji), 338 mikrokompakcji w 45 sesjach, mediana 1 na sesję, maksimum 96. Codex: 1 235 w 302 sesjach (26%). Po pełnej kompakcji: 6 968 Readów w oknie, 4 121 to ponowne odczyty, 59%. Po mikrokompakcji 41%. Ponownie wciągnięte: 35 mln znaków. Rekord: manual_commit_hooks.go czytany po kompakcji 257 razy w 48 sesjach.

**Słabe miejsce i odpowiedź.**
"Model musi przeczytać plik ponownie, bo go nie ma w kontekście, to nie jest marnotrawstwo, tylko konieczność." Dokładnie o to chodzi: kompakcja wyrzuciła coś, co było potrzebne, i to jest miara jej jakości. 59% to odsetek, w jakim kompakcja usunęła rzeczy, których model potrzebował w ciągu następnych 20 kroków. "Ile kontekstu kompakcja faktycznie zwalnia." Tego ledger nie przechowuje (zdarzenie ma tylko trigger), więc "o połowę" z tezy nie jest zmierzone; mówimy tylko o tym, co wraca. Dla Codexa nie mamy ścieżek w zdarzeniu compacted, więc udział ponownych odczytów liczymy tylko dla Claude Code.

---

## Teza 5. Czekanie na build w pętli

**Co wzięliśmy z sesji.**
Każde wywołanie Bash: treść komendy (pierwsze 500 znaków), pozycja w sesji, koszt wywołania API, które ją wydało (z pełnym kontekstem). Z komendy wyciągamy regułą: `sleep N` na początku albo po separatorze, `gh run watch`, samotne `wait`. Dla sleep dodatkowo liczbę sekund.

**Co porównaliśmy.**
Liczbę wywołań pollingu do wszystkich wywołań Bash, per harness. Koszt wywołań API, które wydały polling. Czy polling występuje w seriach: liczymy, ile pollingów jest w oknie 5 kolejnych wywołań narzędzi; 2 i więcej to seria. Rozkład długości sleep i suma przespanego czasu.

**Na jakiej podstawie wniosek.**
Każde sprawdzenie statusu to pełne wywołanie API z całym kontekstem, więc pętla "sleep, sprawdź, sleep, sprawdź" mnoży koszt kontekstu przez liczbę iteracji, a informacji przynosi tyle, co jedno wywołanie po zakończeniu buildu. Serie (2 i więcej w 5 wywołaniach) to dowód, że to pętla, a nie jednorazowa pauza.

**Liczby.**
10 316 wywołań pollingu (2,0% Bashy) w 1 127 sesjach: Claude Code 7 041 (2,4%), Codex 2 974 (1,3%), OpenCode 192, Cursor 109. Koszt wywołań, które je wydały: 1 359 USD, w tym w seriach 4 626 wywołań za 550 USD. Rozkład sleep: 3 460 poniżej 10 s, 1 496 od 10 do 29 s, 507 od 30 do 59 s, 926 od 60 do 299 s, 589 od 300 s w górę. Suma przespanego czasu 245 godzin, z czego 202 godziny w sleepach od 5 minut. Najczęstsze komendy: sleep 120 (326 razy), sleep 180 (94).

**Słabe miejsce i odpowiedź.**
"Sleep 2 to nie polling, to czekanie na start serwera." Tak, dlatego pokazujemy rozkład długości i serie osobno; krótkie sleepy to 60% wywołań, ale tylko 3 godziny z 245. "Koszt 1 359 USD to koszt całych wywołań, nie samego pollingu." Tak, bo takie jest realne obciążenie: żeby wydać `sleep 30`, model musi dostać cały kontekst. Alternatywa (webhook albo blokujące czekanie po stronie harnessu) kosztuje zero wywołań.

---

## Teza 6. Gorące pliki edytowane równocześnie

**Co wzięliśmy z sesji.**
Każde wywołanie Write i Edit: repozytorium, ścieżka pliku znormalizowana do korzenia repo, timestamp, sesja, użytkownik (nazwa katalogu domowego, zahashowana). Dla każdej pary sesja i plik: czas pierwszej i ostatniej edycji tego pliku w tej sesji.

**Co porównaliśmy.**
Dwa pomiary. Pierwszy, gorące pliki: w każdym repo pliki edytowane w co najmniej 10 różnych sesjach; ich udział we wszystkich edycjach; w medianowym repo udział 5% najczęściej edytowanych plików. Drugi, równoczesność: pary sesji w tym samym repo, które edytowały ten sam plik i których okna edycji tego pliku nachodzą na siebie w czasie zegarowym. Do tego dwa proxy problemów po edycji: błąd narzędzia w 3 kolejnych wywołaniach oraz krótki (poniżej 200 znaków) prompt człowieka zaraz po edycji. I sędzia LLM na 200 losowych edycjach z 40 najgorętszych plików z pytaniem o przyczynę.

**Na jakiej podstawie wniosek.**
Równoczesność między subagentami w jednej sesji jest nieobserwowalna (patrz teza 3), więc mierzymy równoczesność między sesjami: dwie sesje edytujące ten sam plik w tym samym oknie czasu to ten sam mechanizm konfliktu, tylko na poziomie zespołu albo wielu terminali jednego użytkownika. Czy gorący plik to problem architektury, czy agent psuje: proxy z błędów mówią, że gorące i zimne pliki mają podobny odsetek błędów, więc sama "gorącość" nie jest błędogenna; sędzia rozstrzyga przyczynę na próbce.

**Liczby.**
518 gorących plików skupia 20,6% ze 186 775 edycji; w medianowym repo top 5% plików ma 33,8% edycji. Równoczesność: 2 908 par sesji, 1 591 plików (z 32 127 edytowanych), 914 sesji. Rekordy: manual_commit_condensation.go w entireio 45 nakładających się par, committed.go 40, explain.go 37 (13 różnych użytkowników). Błąd po edycji: gorące 6,8%, zimne 7,7%. Krótka korekta po edycji gorącego pliku: od 23% do 80% zależnie od pliku. Sędzia: 55% edycji gorących plików to hub architektoniczny, 28% regresja agenta, 9% plik testowy, 7% iteracja użytkownika.

**Słabe miejsce i odpowiedź.**
"Nakładające się sesje to może ten sam człowiek w dwóch terminalach." Może, i to też jest równoczesna edycja przez dwóch agentów; hash użytkownika pozwala to rozdzielić (explain.go: 13 użytkowników). "Sędzia to model, nie człowiek." Tak, 200 przypadków, przedziały ufności 95% podane w JUDGE_hot_file_cause.md; 28% regresji agenta ma przedział 22% do 35%. "Gorący plik to naturalne w każdym repo." Zgoda, i to jest 55% wyniku; teza broni się tym, że co czwarta edycja gorącego pliku to agent naprawiający własną zmianę.

---

## Jedno zdanie obrony na każdą tezę

1. Przeżywalność: w vibe wszystko w commicie jest od agenta, więc commit dzielony przez wygenerowane to wprost odsetek kodu, który przeżył; Claude Code 51%, Codex 17%.
2. Nieprzeczytane: nie wnioskujemy o intencji, tylko o fizycznej możliwości przeczytania w czasie, jaki minął; 21% tokenów końcowych odpowiedzi nie dało się przeczytać, a 18% zatwierdzeń padło za szybko.
3. Subagenci: zbiór nie widzi ich kosztu (300 wywołań sidechain na 933 tys.), a widoczna połowa jest 3 do 6 razy droższa; to luka w danych zgłoszona jako wynik.
4. Kompakcja: 59% Readów w 20 krokach po kompakcji to pliki, które kompakcja właśnie usunęła.
5. Polling: każde `sleep` to pełne wywołanie z całym kontekstem; 10 316 takich wywołań, 245 godzin spania, 1 359 USD.
6. Gorące pliki: 2 908 par sesji edytowało ten sam plik w tym samym czasie, a co czwarta edycja gorącego pliku to agent naprawiający własną regresję.
