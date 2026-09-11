/* data.js - ALL copy and ALL numbers for the page. One global, nothing runs.
   Every figure here is transcribed from SIX_THESES.md and FINDINGS.md.
   Display strings are preformatted pl-PL (space thousands, comma decimals);
   `value` fields are raw numbers so the count-ups can animate them.
   No em/en dashes anywhere. */

window.RECEIPT_DATA = {

  meta: {
    brand: 'Quesma',
    kicker: 'Sześć tez',
    dataset: 'SWE-chat enhanced',
    date: '2026-07-05',
    sessions: 9770,
    sizeGb: '17,8 GB',
    analysisDate: '11 września 2026'
  },

  /* ------------------------------------------------------------------ */
  /* HERO                                                                */
  /* ------------------------------------------------------------------ */

  hero: {
    stars: '* * * * RACHUNEK ZA TOKENY * * * *',
    title: 'Kartą czy <em>gotówką</em>?',
    lede: 'Wystawiamy wam rachunek za spalone tokeny. 9 770 sesji, 116 677 USD. Pozycja po pozycji.',
    lines: [
      { label: 'SESJI',          value: 9770,   decimals: 0, suffix: '' },
      { label: 'TRANSKRYPTÓW',   value: 17.8,   decimals: 1, suffix: ' GB' },
      { label: 'WYWOŁAŃ API',    value: 933529, decimals: 0, suffix: '' },
      { label: 'DO ZAPŁATY',     value: 116677, decimals: 0, suffix: ' USD', big: true }
    ],
    highlight: 'Odczyty cache to 64% rachunku. Nie prompt, nie output.',
    scene: 'sun',
    sceneLabel: 'POWIERZCHNIA'
  },

  /* ------------------------------------------------------------------ */
  /* SIX THESES                                                          */
  /* ------------------------------------------------------------------ */

  sections: [

    /* -------------------------------- 01 ---------------------------- */
    {
      id: 't1',
      number: '01',
      lineItem: 'LINIE W COMMICIE',
      usd: 32993,
      title: 'Płacicie za linie, które nie dożyły commita',
      lede: 'Zapłaciliście 32 993 USD za kod wygenerowany w trybie vibe. Do commita dotarła połowa u Claude Code, a u Codeksa jedna szósta. Reszta to znaki, które model napisał i skasował na waszą fakturę.',
      big: { value: 51, decimals: 0, suffix: '%', label: 'linii z trybu vibe przeżywa do commita (Claude Code)' },
      charts: [
        {
          type: 'bars',
          id: 't1a',
          title: 'PRZEŻYWALNOŚĆ LINII, AGENT x TRYB',
          unit: '%',
          note: 'Skala ucięta na 200%. Wartości powyżej 100% znaczą, że w commicie jest też kod człowieka.',
          max: 200,
          rows: [
            { label: 'claude_code', sub: 'human',  value: 829,  display: '829%',  tone: 'ink', note: 'człowiek dopisuje' },
            { label: 'claude_code', sub: 'collab', value: 192,  display: '192%',  tone: 'ink', note: 'człowiek dopisuje' },
            { label: 'claude_code', sub: 'vibe',   value: 51,   display: '51%',   tone: 'bad' },
            { label: 'codex',       sub: 'human',  value: 314,  display: '314%',  tone: 'ink', note: 'człowiek dopisuje' },
            { label: 'codex',       sub: 'collab', value: 161,  display: '161%',  tone: 'ink', note: 'człowiek dopisuje' },
            { label: 'codex',       sub: 'vibe',   value: 17.2, display: '17,2%', tone: 'bad' },
            { label: 'opencode',    sub: 'human',  value: 196,  display: '196%',  tone: 'ink', note: 'człowiek dopisuje' },
            { label: 'opencode',    sub: 'collab', value: 159,  display: '159%',  tone: 'ink', note: 'człowiek dopisuje' },
            { label: 'opencode',    sub: 'vibe',   value: 25.4, display: '25,4%', tone: 'bad' }
          ]
        },
        {
          type: 'histogram',
          id: 't1b',
          title: 'ROZKŁAD PRZEŻYWALNOŚCI, TRYB VIBE',
          note: 'Sesje z co najmniej 400 wygenerowanymi znakami. 994 sesje zostawiły w commicie mniej niż 10% tego, co model napisał.',
          bins: [
            { label: '<10%',    value: 994, display: '994', tone: 'bad' },
            { label: '10-25%',  value: 455, display: '455', tone: 'bad' },
            { label: '25-50%',  value: 575, display: '575', tone: 'ink' },
            { label: '50-75%',  value: 341, display: '341', tone: 'ink' },
            { label: '75-100%', value: 209, display: '209', tone: 'ink' },
            { label: '>100%',   value: 376, display: '376', tone: 'neutral' }
          ]
        }
      ],
      callouts: [
        'USD na linię w commicie: human 0,0029 · collab 0,0066 · vibe 0,0193',
        'Tokeny kontekstu na linię: 3 830 · 8 754 · 26 099'
      ],
      gap: null,
      footnote: 'Definicje: gen_lines_est = suma znaków w Write.content i Edit.new_string w sesji / 40. committed_lines = total_committed z atrybucji Entire. pct_survive_est = committed_lines / gen_lines_est. Tylko sesje z committed_lines > 0. W trybach human i collab committed_lines zawiera kod napisany przez człowieka, stąd wartości powyżej 100%.',
      scene: 'sharks',
      sceneLabel: 'WYGENEROWANE'
    },

    /* -------------------------------- 02 ---------------------------- */
    {
      id: 't2',
      number: '02',
      lineItem: 'NIEPRZECZYTANE',
      usd: 89,
      title: 'Płacicie za zdania, których nikt nie <em>czyta</em>',
      lede: 'Zapłaciliście około 89 USD za końcowe odpowiedzi, na które człowiek nie miał nawet czasu spojrzeć. Co piąty token, który model wypisał na koniec tury, poszedł w próżnię.',
      big: { value: 21, decimals: 0, suffix: '%', label: 'tokenów końcowych odpowiedzi trafia do nikogo' },
      charts: [
        {
          type: 'stackedBars',
          id: 't2a',
          title: 'ODPOWIEDZI KOŃCOWE: PRZECZYTANE I NIE',
          note: 'Kreskowany kawałek to odpowiedzi, na które człowiek poświęcił mniej niż połowę czasu potrzebnego na przeczytanie.',
          rows: [
            {
              label: 'claude_code',
              total: 55223,
              display: '11,85% nieprzeczytanych',
              parts: [
                { value: 48680, tone: 'ink', label: 'przeczytane 48 680' },
                { value: 6543,  tone: 'bad', label: 'nieprzeczytane 6 543' }
              ]
            },
            {
              label: 'codex',
              total: 9501,
              display: '23,76% nieprzeczytanych',
              parts: [
                { value: 7244, tone: 'ink', label: 'przeczytane 7 244' },
                { value: 2257, tone: 'bad', label: 'nieprzeczytane 2 257' }
              ]
            },
            {
              label: 'opencode',
              total: 1804,
              display: '6,37% nieprzeczytanych',
              parts: [
                { value: 1689, tone: 'ink', label: 'przeczytane 1 689' },
                { value: 115,  tone: 'bad', label: 'nieprzeczytane 115' }
              ]
            }
          ]
        },
        {
          type: 'bars',
          id: 't2b',
          title: 'ODSETEK NIEPRZECZYTANYCH WG NASTĘPNEGO PROMPTU',
          unit: '%',
          note: 'Etykiety z klasyfikacji DeepSeek V4-Flash, 87 887 promptów. Gdy człowiek zaraz potem tylko przerywa albo klika zgodę, odpowiedź przepada.',
          max: 30,
          rows: [
            { label: 'meta_other',     sub: '9 167 odpowiedzi',  value: 30,   display: '30%',   tone: 'bad' },
            { label: 'interruption',   sub: '551 odpowiedzi',    value: 28.9, display: '28,9%', tone: 'bad' },
            { label: 'approval',       sub: '10 599 odpowiedzi', value: 18,   display: '18%',   tone: 'bad' },
            { label: 'follow_up',      sub: '23 008 odpowiedzi', value: 10.4, display: '10,4%', tone: 'ink' },
            { label: 'correction',     sub: '4 327 odpowiedzi',  value: 8.9,  display: '8,9%',  tone: 'ink' },
            { label: 'question',       sub: '10 521 odpowiedzi', value: 8.2,  display: '8,2%',  tone: 'ink' },
            { label: 'new_task',       sub: '2 600 odpowiedzi',  value: 6,    display: '6%',    tone: 'ink' },
            { label: 'failure_report', sub: '5 755 odpowiedzi',  value: 5.1,  display: '5,1%',  tone: 'ink' }
          ]
        }
      ],
      callouts: [
        'Mediana czasu czytania 29,57 s · mediana czasu do następnego promptu 98,46 s (Claude Code)',
        'Nieprzeczytane tokeny tekstu: 2 786 147 · 784 364 · 121 594'
      ],
      gap: null,
      footnote: 'Definicje: odpowiedź końcowa = ostatnie wywołanie z tekstem w turze przed następnym promptem człowieka (Codex: z korektą na wywołania stemplowane po następnym promptcie). read_time_s = (znaki/5)/250 słów na minutę. Nieprzeczytana = czas do następnego promptu < 0,5 x read_time_s. Przerwania wykluczone.',
      scene: 'skulls',
      sceneLabel: 'NIEPRZECZYTANE'
    },

    /* -------------------------------- 03 ---------------------------- */
    {
      id: 't3',
      number: '03',
      lineItem: 'SUBAGENCI',
      usd: 2164,
      title: 'Subagent oddaje wynik, a wy płacicie czynsz',
      lede: 'Zapłaciliście 2 164 USD za to, że wyniki narzędzia Task siedzą w kontekście rodzica. 91,3 mln znaków wraca do sesji i jest opłacane przy każdym kolejnym wywołaniu. Sesja z subagentem kosztuje trzy razy więcej niż bez.',
      big: { value: 4.44, decimals: 2, suffix: ' USD', label: 'mediana sesji vibe z Taskiem, kontra 1,45 USD bez Taska' },
      charts: [
        {
          type: 'waffle',
          id: 't3a',
          title: 'SESJE WEDŁUG LICZBY WYWOŁAŃ TASK',
          note: '3 542 sesje Claude Code użyły narzędzia Task. 55 sesji wywołało je ponad 30 razy.',
          cellValue: 10,
          maxCells: 360,
          legend: '■ = 10 sesji',
          groups: [
            { label: '1 wywołanie',   value: 1128, tone: 'neutral' },
            { label: '2-3',           value: 1024, tone: 'ink' },
            { label: '4-10',          value: 980,  tone: 'focus' },
            { label: '11-30',         value: 355,  tone: 'warn' },
            { label: '>30',           value: 55,   tone: 'bad' }
          ]
        },
        {
          type: 'pairedBars',
          id: 't3b',
          title: 'MEDIANA KOSZTU SESJI: BEZ TASKA I Z TASKIEM',
          note: 'Claude Code, mediana USD na sesję. Odsetek sesji z commitem prawie się nie zmienia.',
          max: 7,
          pairs: [
            { label: 'collab', a: { label: 'bez Task', value: 1.59, display: '1,59 USD' }, b: { label: 'z Task', value: 5.32, display: '5,32 USD' } },
            { label: 'human',  a: { label: 'bez Task', value: 1.14, display: '1,14 USD' }, b: { label: 'z Task', value: 6.72, display: '6,72 USD' } },
            { label: 'vibe',   a: { label: 'bez Task', value: 1.45, display: '1,45 USD' }, b: { label: 'z Task', value: 4.44, display: '4,44 USD' } }
          ]
        }
      ],
      callouts: [
        'Wyniki Task w kontekście rodzica: 17 833 wywołania w 3 542 sesjach · 91,3 mln znaków · mediana 3 136 znaków',
        'Czynsz kontekstu 1 898 USD · koszt samych promptów Task 266 USD'
      ],
      gap: 'LUKA W DANYCH: transkrypty subagentów nie są w zbiorze',
      footnote: 'Luka w danych: transkrypty subagentów nie są w zbiorze. Wywołań z flagą isSidechain: 300 z 933 529 (2,62 USD). Powyżej wyłącznie narzędzie Task widziane z sesji rodzica (Claude Code).',
      scene: 'fish',
      sceneLabel: 'RODZIC'
    },

    /* -------------------------------- 04 ---------------------------- */
    {
      id: 't4',
      number: '04',
      lineItem: 'KOMPAKCJA',
      usd: 36593,
      title: 'Kompakcja zapomina, a potem czyta to samo jeszcze raz',
      lede: 'W sesjach Claude Code, które musiały się kompaktować, poszło 36 593 USD. Zaraz po granicy 59% Readów to pliki, które model już w tej sesji czytał. Same ponowne odczyty to 33,5 mln znaków i 50,56 USD, jeśli liczyć je po cenie recache.',
      big: { value: 59, decimals: 0, suffix: '%', label: 'Readów po kompakcji to pliki już czytane w tej samej sesji' },
      charts: [
        {
          type: 'bars',
          id: 't4a',
          title: 'ODSETEK SESJI Z KOMPAKCJĄ',
          unit: '%',
          note: 'OpenCode i Cursor nie zapisują granicy kompakcji, stąd zera.',
          max: 30,
          rows: [
            { label: 'codex',       sub: '302 z 1 167 sesji', value: 25.88, display: '25,88%', tone: 'bad' },
            { label: 'claude_code', sub: '746 z 7 230 sesji', value: 10.32, display: '10,32%', tone: 'ink' },
            { label: 'opencode',    sub: '0 z 783 sesji',     value: 0,     display: '0%',     tone: 'neutral' },
            { label: 'cursor',      sub: '0 z 86 sesji',      value: 0,     display: '0%',     tone: 'neutral' }
          ]
        },
        {
          type: 'bars',
          id: 't4b',
          title: 'ODSETEK PONOWNYCH ODCZYTÓW PO GRANICY',
          unit: '%',
          note: '20 pierwszych wywołań narzędzi po granicy, Claude Code. Razem 35,3 mln znaków wciągniętych drugi raz.',
          max: 100,
          rows: [
            { label: 'compact_boundary',      sub: '4 121 z 6 968 Readów', value: 59.14, display: '59,14%', tone: 'bad' },
            { label: 'microcompact_boundary', sub: '517 z 1 249 Readów',   value: 41.39, display: '41,39%', tone: 'ink' }
          ]
        },
        {
          type: 'table',
          id: 't4c',
          title: 'NAJCZĘŚCIEJ CZYTANE PONOWNIE PO KOMPAKCJI',
          note: 'Jeden plik odczytany ponownie 257 razy w 48 sesjach to 1,85 mln znaków.',
          columns: ['plik', 'ponowne odczyty', 'sesje'],
          mono: [0],
          rows: [
            ['strategy/manual_commit_hooks.go',       '257', '48'],
            ['src/rhea_bridge.py',                    '71',  '4'],
            ['scripts/rhea_query_persist.sh',         '52',  '1'],
            ['static/index.html',                     '51',  '5'],
            ['strategy/manual_commit_condensation.go','51',  '26'],
            ['checkpoint/temporary.go',               '43',  '11'],
            ['cli/hooks_claudecode_handlers.go',      '42',  '21'],
            ['sa/rh.REDACTED.md',                     '41',  '2']
          ]
        }
      ],
      callouts: [
        'Mediana granic w sesji z kompakcją: 1 (Claude Code), 2 (Codex) · maksimum 103',
        'Ponowne odczyty: 33 550 476 znaków · 4,05 USD jednym przebiegiem · 50,56 USD po recache'
      ],
      gap: 'LUKA W DANYCH: rozmiar redukcji kontekstu nie jest zapisany w ledgerze',
      footnote: 'Definicje: granica = zdarzenie system/compact_boundary lub microcompact_boundary (Claude Code) albo compacted (Codex). Reread = Read ścieżki, która była czytana w tej sesji przed granicą, w 20 wywołaniach narzędzi po granicy. Rozmiar redukcji nie jest zapisany w ledgerze (tylko trigger = auto).',
      scene: 'vortex',
      sceneLabel: 'KOMPAKCJA'
    },

    /* -------------------------------- 05 ---------------------------- */
    {
      id: 't5',
      number: '05',
      lineItem: 'SLEEP',
      usd: 1360,
      title: 'Agent śpi, kontekst tyka, wy <em>płacicie</em>',
      lede: 'Zapłaciliście około 1 360 USD za czekanie. Każde wywołanie Bash z komendą sleep niesie ze sobą pełny kontekst sesji, więc drzemka jest fakturowana po cenie odczytu cache. Razem 245 godzin przespanych przy buildzie.',
      big: { value: 202, decimals: 0, suffix: '', label: 'godzin przespanych w wywołaniach sleep 300 s i dłuższych' },
      charts: [
        {
          type: 'bars',
          id: 't5a',
          title: 'UDZIAŁ POLLINGU W WYWOŁANIACH BASH',
          unit: '%',
          note: 'Polling = Bash z sleep N, gh run watch albo wait.',
          max: 5,
          rows: [
            { label: 'cursor',      sub: '109 z 2 480',      value: 4.4,  display: '4,4%',  tone: 'bad' },
            { label: 'claude_code', sub: '7 041 z 291 956',  value: 2.41, display: '2,41%', tone: 'ink', note: '1 082 USD' },
            { label: 'opencode',    sub: '192 z 10 393',     value: 1.85, display: '1,85%', tone: 'ink' },
            { label: 'codex',       sub: '2 974 z 220 422',  value: 1.35, display: '1,35%', tone: 'ink', note: '268 USD' }
          ]
        },
        {
          type: 'histogram',
          id: 't5b',
          title: 'PRZESPANE GODZINY WEDŁUG DŁUGOŚCI SLEEP',
          note: '589 wywołań z sleep 300 s lub dłuższym odpowiada za 202 z 245 przespanych godzin.',
          bins: [
            { label: '<10 s',    value: 2.8,  display: '2,8 h',  tone: 'ink' },
            { label: '10-29 s',  value: 6.2,  display: '6,2 h',  tone: 'ink' },
            { label: '30-59 s',  value: 4.7,  display: '4,7 h',  tone: 'ink' },
            { label: '60-299 s', value: 29.4, display: '29,4 h', tone: 'warn' },
            { label: '>=300 s',  value: 202,  display: '202 h',  tone: 'bad' }
          ]
        },
        {
          type: 'bars',
          id: 't5c',
          title: 'POLLING POJEDYNCZY I SERIAMI',
          note: 'Burst = liczba pollingów w oknie 5 kolejnych wywołań narzędzi.',
          max: 5690,
          rows: [
            { label: 'pojedynczy',       sub: 'isolated',            value: 5690, display: '5 690', tone: 'ink',  note: '809 USD' },
            { label: '2 na 5 wywołań',   sub: '2 polls in 5 calls',  value: 3029, display: '3 029', tone: 'ink',  note: '361 USD' },
            { label: '3 na 5 wywołań',   sub: '3 polls in 5 calls',  value: 975,  display: '975',   tone: 'warn', note: '104 USD' },
            { label: '4 i więcej na 5',  sub: '4+ polls in 5 calls', value: 622,  display: '622',   tone: 'bad',  note: '84,89 USD' }
          ]
        }
      ],
      callouts: [
        'Najczęstsza komenda: sleep 120 · 326 wywołań · 27 sesji',
        'Kontekst przewieziony przez polling: 1 705 656 825 tokenów w Claude Code'
      ],
      gap: null,
      footnote: 'Definicje: polling = wywołanie Bash z sleep N, gh run watch lub wait. Burst = liczba pollingów w oknie 5 kolejnych wywołań narzędzi. usd = koszt wywołań API, które wydały polling (pełny kontekst). Godziny liczone tylko dla wywołań z podaną liczbą sekund.',
      scene: 'beach',
      sceneLabel: 'SLEEP'
    },

    /* -------------------------------- 06 ---------------------------- */
    {
      id: 't6',
      number: '06',
      lineItem: 'GORĄCE PLIKI',
      usd: 0,
      usdDisplay: '2 908 par',
      usdNote: 'bez wyceny',
      title: 'Dwie sesje, jeden plik, ta sama <em>minuta</em>',
      lede: 'Tej pozycji nie umiemy wycenić, ale trzeba ją pokazać. 2 908 par sesji edytowało ten sam plik w tym samym czasie zegarowym. 914 sesji, 1 591 plików, jeden wspólny plik architektury na środku.',
      big: { value: 2908, decimals: 0, suffix: '', label: 'par sesji edytujących ten sam plik w tym samym czasie' },
      charts: [
        {
          type: 'bars',
          id: 't6a',
          title: 'NAJGORĘTSZE PLIKI WEDŁUG PAR NAKŁADAJĄCYCH SIĘ',
          note: 'Dwa repozytoria mają ten sam plik hooks: nakładanie liczone osobno w każdym.',
          max: 45,
          rows: [
            { label: 'strategy/manual_commit_condensation.go', sub: 'entireio/cli-checkpoints', value: 45, display: '45', tone: 'bad' },
            { label: 'checkpoint/committed.go',                sub: 'entireio/cli-checkpoints', value: 40, display: '40', tone: 'bad' },
            { label: 'cli/explain.go',                         sub: 'entireio/cli-checkpoints', value: 37, display: '37', tone: 'bad' },
            { label: 'strategy/manual_commit_hooks.go',        sub: 'E2E-Solution/cli',         value: 34, display: '34', tone: 'ink' },
            { label: 'strategy/manual_commit_hooks.go',        sub: 'entireio/cli-checkpoints', value: 32, display: '32', tone: 'ink' },
            { label: 'cli/migrate.go',                         sub: 'entireio/cli-checkpoints', value: 22, display: '22', tone: 'ink' },
            { label: 'cli/lifecycle.go',                       sub: 'E2E-Solution/cli',         value: 17, display: '17', tone: 'ink' },
            { label: 'cli/explain_test.go',                    sub: 'entireio/cli-checkpoints', value: 17, display: '17', tone: 'ink' }
          ]
        },
        {
          type: 'waffle',
          id: 't6b',
          title: 'DLACZEGO PLIK JEST GORĄCY',
          note: 'Sędzia DeepSeek V4-Pro, 200 przypadków po 5 z 40 plików. Ponad połowa to jeden centralny plik, do którego wszyscy muszą dopisać.',
          cellValue: 1,
          maxCells: 100,
          legend: '■ = 1 przypadek na 100',
          groups: [
            { label: 'architecture_hub', value: 55, tone: 'bad' },
            { label: 'agent_regression', value: 28, tone: 'focus' },
            { label: 'test_file',        value: 9,  tone: 'ink' },
            { label: 'user_iteration',   value: 7,  tone: 'neutral' },
            { label: 'inne',             value: 1,  tone: 'warn' }
          ]
        }
      ],
      callouts: [
        'Gorące pliki (co najmniej 10 sesji w repo): 518 plików, 20,6% ze 186 775 edycji',
        'Mediana udziału top 5% plików w edycjach repo: 33,8% · błąd po edycji: gorące 6,8%, zimne 7,7%'
      ],
      gap: 'LUKA W DANYCH: równoczesność między subagentami w jednej sesji jest nieobserwowalna',
      footnote: 'Definicje: para nakładająca się = dwie sesje w tym samym repo, które edytowały (Write/Edit) ten sam plik, a ich okna [pierwsza edycja, ostatnia edycja] tego pliku nachodzą na siebie w czasie zegarowym. Luka w danych: równoczesność między subagentami w jednej sesji jest nieobserwowalna (patrz teza 03).',
      scene: 'surfers',
      sceneLabel: 'GORĄCY PLIK'
    }
  ],

  /* ------------------------------------------------------------------ */
  /* CLOSING                                                             */
  /* ------------------------------------------------------------------ */

  closing: {
    heading: 'RAZEM',
    lede: 'Dziesięć pozycji z pełnego raportu. Rachunek robi kontekst, nie output.',
    lines: [
      { label: 'Odczyty cache',            note: '64% kosztu',            value: 74600, decimals: 0, suffix: ' USD' },
      { label: 'Zapisy cache',             note: '22% kosztu',            value: 26000, decimals: 0, suffix: ' USD' },
      { label: 'Output',                   note: '9% kosztu',             value: 10734, decimals: 0, suffix: ' USD' },
      { label: 'Świeży input',             note: '5% kosztu',             value: 5367,  decimals: 0, suffix: ' USD' },
      { label: 'Przerwa na kawę',          note: 'pęknięcia cache',       value: 9223,  decimals: 0, suffix: ' USD' },
      { label: 'Wyniki narzędzi',          note: 'czynsz za kontekst',    value: 30746, decimals: 0, suffix: ' USD' },
      { label: 'Nigdy nieużyte wyniki',    note: '32% dużych wyników',    value: 10000, decimals: 0, suffix: ' USD' },
      { label: 'Pushback',                 note: '14% rachunku',          value: 16548, decimals: 0, suffix: ' USD' },
      { label: 'Prompt pisany przez harness', note: '377 mln znaków',     value: 75,    decimals: 0, suffix: '%' },
      { label: 'Godziny ludzkie',          note: '16 358 godzin po 60 USD', value: 8.6, decimals: 1, suffix: 'x tokenów' }
    ],
    total: { label: 'DO ZAPŁATY', value: 116677, decimals: 0, suffix: ' USD' },
    stamp: 'NIEZAPŁACONE',
    thanks: 'DZIĘKUJEMY ZA WSZYSTKIE DANE',
    sources: 'Źródła: results/six/*.csv, T01, T09, T11, T14, T16, T19. Zbiór SWE-chat enhanced 2026-07-05, analiza 11 września 2026.',
    scene: 'barcode',
    sceneLabel: 'KONIEC'
  }
};
