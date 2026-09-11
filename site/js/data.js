/* data.js - ALL copy and ALL numbers for the page. One global, nothing runs.
   Pitch cut: one line item, one headline, one number, one small chart per
   slide. No footnotes, no callouts, no method sentences, no amounts under
   1 000 USD. Display strings are preformatted pl-PL (space thousands, comma
   decimals); `value` fields are raw numbers so the count-ups can animate them.
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
    invoice: 'RACHUNEK',
    meta: [
      { k: 'NR',      v: '0001/2026-07-05' },
      { k: 'DATA',    v: '11.09.2026' },
      { k: 'KASA',    v: 'SWE-chat enhanced' },
      { k: 'KASJER',  v: 'Quesma' },
      { k: 'POZYCJI', v: '6' }
    ],
    stars: '* * * * RACHUNEK ZA TOKENY * * * *',
    title: 'Kartą czy <em>gotówką</em>?',
    lede: 'Wystawiamy wam rachunek za spalone tokeny. 9 770 sesji, pozycja po pozycji.',
    lines: [
      { label: 'SESJI',       value: 9770,   decimals: 0, suffix: '' },
      { label: 'WYWOŁAŃ API', value: 933529, decimals: 0, suffix: '' },
      { label: 'DO ZAPŁATY',  value: 116677, decimals: 0, suffix: ' USD', big: true }
    ],
    highlight: null,
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
      title: 'Połowa wygenerowanego kodu nie <em>dożywa</em> commita.',
      lede: '',
      big: {
        value: 51,
        decimals: 0,
        suffix: '%',
        label: 'linii z trybu vibe trafia do commita'
      },
      charts: [
        {
          type: 'bars',
          id: 't1a',
          title: 'PRZEŻYWALNOŚĆ LINII, TRYB VIBE',
          unit: '%',
          max: 60,
          rows: [
            { label: 'claude_code', value: 51,   display: '51%',   tone: 'bad' },
            { label: 'opencode',    value: 25.4, display: '25,4%', tone: 'bad' },
            { label: 'codex',       value: 17.2, display: '17,2%', tone: 'bad' }
          ]
        }
      ],
      callouts: [],
      gap: null,
      footnote: null,
      scene: 'sharks',
      sceneLabel: 'WYGENEROWANE'
    },

    /* -------------------------------- 02 ---------------------------- */
    {
      id: 't2',
      number: '02',
      lineItem: 'NIEPRZECZYTANE',
      usd: 0,
      usdDisplay: 'CZYNSZ ZA KONTEKST',
      title: 'Płacicie za odpowiedzi, których nikt nie <em>czyta</em>.',
      lede: '',
      big: {
        value: 21,
        decimals: 0,
        suffix: '%',
        label: 'każdy nieprzeczytany akapit zostaje w kontekście i jest opłacany przy każdym kolejnym wywołaniu'
      },
      charts: [
        {
          type: 'stackedBars',
          id: 't2a',
          title: 'ODPOWIEDZI KOŃCOWE, WSZYSTKIE AGENTY',
          rows: [
            {
              label: '66 528 odpowiedzi',
              total: 66528,
              display: '8 915 nieprzeczytanych',
              parts: [
                { value: 57613, tone: 'ink', label: 'przeczytane 57 613' },
                { value: 8915,  tone: 'bad', label: 'nieprzeczytane 8 915' }
              ]
            }
          ]
        }
      ],
      callouts: [],
      gap: null,
      footnote: null,
      scene: 'skulls',
      sceneLabel: 'NIEPRZECZYTANE'
    },

    /* -------------------------------- 03 ---------------------------- */
    {
      id: 't3',
      number: '03',
      lineItem: 'SUBAGENCI',
      usd: 2164,
      title: 'Sesja z subagentami kosztuje <em>trzy razy</em> więcej.',
      lede: '',
      big: {
        value: 3,
        decimals: 0,
        suffix: 'x',
        label: 'mediana kosztu sesji vibe: 4,44 USD z Taskiem, 1,45 USD bez'
      },
      charts: [
        {
          type: 'bars',
          id: 't3a',
          title: 'MEDIANA KOSZTU SESJI VIBE',
          unit: 'USD',
          max: 5,
          rows: [
            { label: 'bez Task', value: 1.45, display: '1,45 USD', tone: 'ink' },
            { label: 'z Task',   value: 4.44, display: '4,44 USD', tone: 'bad' }
          ]
        }
      ],
      callouts: [],
      gap: null,
      footnote: null,
      scene: 'fish',
      sceneLabel: 'RODZIC'
    },

    /* -------------------------------- 04 ---------------------------- */
    {
      id: 't4',
      number: '04',
      lineItem: 'KOMPAKCJA',
      usd: 36593,
      title: 'Po kompakcji model czyta te same pliki <em>od nowa</em>.',
      lede: '',
      big: {
        value: 59,
        decimals: 0,
        suffix: '%',
        label: 'odczytów po kompakcji to pliki już czytane w tej sesji'
      },
      charts: [
        {
          type: 'bars',
          id: 't4a',
          title: 'ODSETEK SESJI Z KOMPAKCJĄ',
          unit: '%',
          max: 30,
          rows: [
            { label: 'codex',       value: 25.9, display: '25,9%', tone: 'bad' },
            { label: 'claude_code', value: 10.3, display: '10,3%', tone: 'ink' }
          ]
        }
      ],
      callouts: [],
      gap: null,
      footnote: null,
      scene: 'vortex',
      sceneLabel: 'KOMPAKCJA'
    },

    /* -------------------------------- 05 ---------------------------- */
    {
      id: 't5',
      number: '05',
      lineItem: 'POLLING',
      usd: 1360,
      title: 'Agent pyta w kółko, czy proces <em>już</em> się skończył.',
      lede: 'Każde sprawdzenie statusu płaci pełny kontekst. Gdyby proces sam zgłaszał koniec, żadne z nich nie byłoby potrzebne.',
      big: {
        value: 10316,
        decimals: 0,
        suffix: '',
        label: 'wywołań sprawdzających status w 1 127 sesjach'
      },
      charts: [
        {
          type: 'bars',
          id: 't5a',
          title: 'SERIE POLLINGU W OKNIE 5 WYWOŁAŃ',
          max: 6000,
          rows: [
            { label: 'pojedyncze',         value: 5690, display: '5 690', tone: 'ink' },
            { label: '2 z rzędu',          value: 3029, display: '3 029', tone: 'ink' },
            { label: '3 z rzędu',          value: 975,  display: '975',   tone: 'warn' },
            { label: '4 i więcej z rzędu', value: 622,  display: '622',   tone: 'bad' }
          ]
        }
      ],
      callouts: [],
      gap: null,
      footnote: null,
      scene: 'beach',
      sceneLabel: 'CZEKANIE'
    },

    /* -------------------------------- 06 ---------------------------- */
    {
      id: 't6',
      number: '06',
      lineItem: 'GORĄCE PLIKI',
      usd: 0,
      usdDisplay: 'PODWÓJNA ROBOTA',
      title: 'Jeden plik, 120 sesji, edycje <em>nakładają</em> się w czasie.',
      lede: 'Sesje agentów edytują ten sam plik równolegle, a potem agent poprawia to, co sam popsuł.',
      big: {
        value: 2908,
        decimals: 0,
        suffix: '',
        label: 'par sesji, które edytowały ten sam plik w tym samym czasie'
      },
      charts: [
        {
          type: 'bars',
          id: 't6a',
          title: 'DLACZEGO PLIK JEST GORĄCY',
          unit: '%',
          max: 60,
          rows: [
            {
              label: 'hub architektury',
              value: 55,
              display: '55%',
              tone: 'ink',
              sub: 'każda zmiana przez niego przechodzi'
            },
            {
              label: 'regresja agenta',
              value: 28,
              display: '28%',
              tone: 'bad',
              sub: 'naprawia to, co sam zepsuł'
            },
            { label: 'plik testowy', value: 9, display: '9%', tone: 'neutral' }
          ]
        }
      ],
      callouts: [],
      gap: null,
      footnote: null,
      scene: 'surfers',
      sceneLabel: 'GORĄCY PLIK'
    }
  ],

  /* ------------------------------------------------------------------ */
  /* CLOSING                                                             */
  /* ------------------------------------------------------------------ */

  closing: {
    heading: 'RAZEM',
    lede: 'Rachunek robi kontekst, nie output.',
    lines: [
      { label: 'Odczyty cache',                value: 74600, decimals: 0, suffix: ' USD' },
      { label: 'Wyniki narzędzi w kontekście', value: 30746, decimals: 0, suffix: ' USD' },
      { label: 'Zapisy cache',                 value: 26000, decimals: 0, suffix: ' USD' },
      { label: 'Pushback',                     value: 16548, decimals: 0, suffix: ' USD' },
      { label: 'Przerwa na kawę',              value: 9223,  decimals: 0, suffix: ' USD' }
    ],
    total: { label: 'DO ZAPŁATY', value: 116677, decimals: 0, suffix: ' USD' },
    stamp: 'NIEZAPŁACONE',
    thanks: 'DZIĘKUJEMY ZA WSZYSTKIE DANE',
    sources: 'SWE-chat enhanced 2026-07-05 · analiza Quesma',
    fiscal: 'NIP 0000000000 · KASA 01 · W 2026.07.05',
    scene: 'barcode',
    sceneLabel: 'KONIEC'
  }
};
