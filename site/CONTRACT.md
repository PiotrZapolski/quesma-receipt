# CONTRACT: "Rachunek za tokeny" receipt page (shared by all implementers)

Static site, no build, no ES modules. Scripts are plain `<script defer src=...>` tags loaded in this order:
gsap.min.js (cdnjs 3.12.5), ScrollTrigger.min.js (cdnjs 3.12.5), js/data.js, js/charts.js, js/halftone/engine.js, js/halftone/scenes.js, js/render.js, js/motion.js, js/main.js.
Each file exposes exactly one global (below). Nothing runs at load time except main.js.

Rules for every file: Polish copy, `pl-PL` number formatting (space thousands, comma decimals), NO em-dash or en-dash characters anywhere (use "-"), light theme only, Quesma tokens from css/tokens.css only (never hardcode colors outside tokens.css and the halftone engine, which uses `--ink` RGB 23,20,17).

## Globals

- `window.RECEIPT_DATA` (data.js): all copy and numbers. Shape below.
- `window.Charts = { render(el, spec) }` (charts.js): renders one chart spec into `el` (empty div). Must produce the class names listed under "Chart DOM" so motion.js can animate them.
- `window.Halftone = { init(), register(canvas, sceneName, opts), setProgress(canvas, p), start(), stop(), refresh() }` (engine.js). `init()` finds every `canvas[data-scene]`, registers it with `window.Scenes[name]`, sets up ResizeObserver + IntersectionObserver and the shared rAF loop. `setProgress(canvas, p)` stores scroll progress 0..1 for the print wipe. Honors `matchMedia('(prefers-reduced-motion: reduce)')` by drawing one static frame with p = 1.
- `window.Scenes = { sun, sharks, skulls, fish, vortex, beach, surfers, barcode }` (scenes.js): each is `function(ctx, t, p, w, h)` that paints GRAYSCALE only (black = ink, white = paper, grays become halftone) into the low-res buffer context. No colors.
- `window.Render = { build(data) }` (render.js): builds the whole DOM inside `<main id="strip">` from RECEIPT_DATA using the DOM contract below, then calls `Charts.render` for each chart container. Returns nothing.
- `window.Motion = { init() }` (motion.js): wires all GSAP / ScrollTrigger effects using the class names below. Uses `gsap.matchMedia()` for reduced-motion and `(max-width: 600px)` branches.
- main.js: `DOMContentLoaded` -> `document.fonts.ready` -> `Render.build(RECEIPT_DATA)` -> `Halftone.init()` -> `Motion.init()` -> `ScrollTrigger.refresh()`. Also re-refreshes on `resize` (debounced 200 ms).

## RECEIPT_DATA shape (data.js)

```js
window.RECEIPT_DATA = {
  meta: { brand: 'Quesma', kicker: 'Sześć tez', dataset: 'SWE-chat enhanced', date: '2026-07-05', sessions: 9770, sizeGb: '17,8 GB', analysisDate: '11 września 2026' },
  hero: {
    stars: '* * * * RACHUNEK ZA TOKENY * * * *',
    title: 'Co <em>naprawdę</em> kosztuje w sesjach agentów kodujących',   // em = vermilion
    lede: '...one or two sentences...',
    lines: [ { label: 'SESJI', value: 9770, decimals: 0, suffix: '' }, { label: 'TRANSKRYPTÓW', value: 17.8, decimals: 1, suffix: ' GB' }, { label: 'WYWOŁAŃ API', value: 933529 }, { label: 'RACHUNEK ŁĄCZNIE', value: 116677, suffix: ' USD', big: true } ],
    highlight: 'Odczyty cache to 64% rachunku',   // gets the sulphur highlighter
    scene: 'sun', sceneLabel: 'POWIERZCHNIA'       // boxed pixel caption drawn as HTML over the canvas
  },
  sections: [
    {
      id: 't1', number: '01', lineItem: 'LINIE W COMMICIE', usd: 25031,     // usd is added to the sticky ticker when the section enters
      title: 'Linie w commicie kontra wygenerowany kod',
      lede: '...',
      big: { value: 51, decimals: 0, suffix: '%', label: 'linii z trybu vibe przeżywa do commita' },
      charts: [ /* chart specs, see below; 1 to 3 per section */ ],
      callouts: [ 'USD na linię: human 0,0029 · collab 0,0066 · vibe 0,0193' ],
      gap: null | 'LUKA W DANYCH: transkrypty subagentów nie są w zbiorze',   // red rotated stamp when present
      footnote: 'Definicje: ...',      // the definition sentence from SIX_THESES.md, mono, small
      scene: 'sharks', sceneLabel: 'WYGENEROWANE'
    },
    // t2 skulls, t3 fish, t4 vortex, t5 beach, t6 surfers
  ],
  closing: {
    heading: 'RAZEM',
    lines: [ { label: 'Odczyty cache', note: '64% kosztu', value: 74600, suffix: ' USD' }, ... ten lines from FINDINGS section 1 ... ],
    total: { label: 'RACHUNEK ŁĄCZNIE', value: 116677, suffix: ' USD' },
    thanks: 'DZIĘKUJEMY ZA WSZYSTKIE DANE',
    sources: 'Źródła: results/six/*.csv, T01, T09, T11, T14, T16, T19',
    scene: 'barcode'
  }
};
```

## Chart spec shapes (data.js produces, charts.js consumes)

Common fields: `type`, `id` (unique, e.g. 't1a'), `title` (short, mono uppercase), `note` (optional small text under the chart), `unit` (optional, e.g. '%').
Tones: `'ink' | 'bad' | 'good' | 'neutral' | 'warn' | 'focus'` mapped to tokens ink / vermilion / saving / sage / sulphur / oxblood.

- `bars`: `{ rows: [ { label, sub, value, display, tone, note } ], max }` horizontal bars, `display` is the preformatted string shown at the end of the bar (e.g. '829%'), `sub` optional second mono line under the label, `note` optional tiny annotation right of the value. Bars longer than `max` are clamped visually and get a small "▸" overflow mark.
- `stackedBars`: `{ rows: [ { label, total, display, parts: [ { value, tone, label } ] } ] }` each row one full-width bar split proportionally; parts with tone `'bad'` get a diagonal hatch.
- `waffle`: `{ cellValue, groups: [ { label, value, tone } ], legend: '■ = 10 sesji', maxCells: 100 }` cells drawn as small squares, grouped colors, group labels below.
- `histogram`: `{ bins: [ { label, value, display, tone } ] }` vertical bars, equal width, value labels on top, x labels below.
- `pairedBars`: `{ pairs: [ { label, a: { label, value, display }, b: { label, value, display } } ], max }` two horizontal bars per group (a = ink, b = vermilion).
- `table`: `{ columns: [ 'plik', 'ponowne odczyty', 'sesje' ], rows: [ [ 'cmd/...', '257', '48' ], ... ], mono: [0] }` indexes in `mono` render in Fragment Mono; numeric columns right-aligned.

## DOM contract (render.js produces, css and motion.js consume)

```
body.rx-page
  header.rx-header
    .rx-header__brand  (img/svg Q mark + span.rx-header__kicker "Sześć tez" + span.rx-cursor)
    .rx-header__meta   (mono: dataset · date · sessions)
    .rx-ticker         (mono, "SUMA DOTĄD" + span.rx-ticker__value data-total="0")
  main#strip.rx-strip
    section.rx-section.rx-section--hero#s-hero[data-section=hero]
      .rx-print                     (clip-path wrapper animated by motion.js)
        .rx-stars                   (mono)
        h1.rx-title                 (Schibsted, em inside = vermilion)
        p.rx-lede
        ul.rx-lines > li.rx-line   (mono label ... dotted leader ... span.rx-num[data-count][data-decimals][data-suffix])
        p.rx-highlight > span.rx-hl (sulphur highlighter behind the text)
        figure.rx-stamp[data-scene=sun] > canvas[data-scene=sun][aria-label] + figcaption.rx-stamp__label (boxed pixel caption)
    section.rx-section#s-t1[data-section=t1][data-usd=25031]
      .rx-print
        .rx-lineitem                (mono: span.rx-lineitem__no "01" · span.rx-lineitem__name · leader · span.rx-lineitem__usd)
        h2.rx-title
        p.rx-lede
        .rx-big > span.rx-num[data-count] + span.rx-big__label
        .rx-charts > .chart[data-chart=<type>][data-chart-id=<id>]   (one per spec; Charts.render fills it)
        .rx-callouts > p.rx-callout
        .rx-gap (only if gap)       (red rotated stamp text)
        figure.rx-stamp[data-scene=sharks] > canvas[data-scene=sharks] + figcaption.rx-stamp__label
        p.rx-footnote               (mono small)
    ... t2..t6 same ...
    section.rx-section.rx-section--closing#s-closing
      .rx-print
        .rx-lineitem "RAZEM"
        ul.rx-lines (ten lines, each with span.rx-num)
        .rx-total (mono big, span.rx-num)
        p.rx-thanks
        figure.rx-stamp[data-scene=barcode] > canvas[data-scene=barcode]
        p.rx-sources
  .rx-printhead (fixed, thin ink line with sulphur glow; motion.js moves it)
```

Canvas sizing: `.rx-stamp canvas { width: 100%; aspect-ratio: 16 / 6; display: block; image-rendering: pixelated; }` and 16 / 5 below 600px. Engine sets the backing store size from the CSS box.

## Chart DOM (charts.js produces, charts.css and motion.js consume)

- bars: `.chart-bars > .chart-bars__row > (.chart-bars__label, .chart-bars__track > .chart-bars__fill[data-tone], .chart-bars__value)`. Motion animates `.chart-bars__fill` scaleX from 0 (transform-origin left), stagger 0.05.
- stackedBars: `.chart-stacked > .chart-stacked__row > (.chart-stacked__label, .chart-stacked__track > .chart-stacked__part[data-tone] ..., .chart-stacked__value)`. Motion animates `.chart-stacked__part` scaleX.
- waffle: `.chart-waffle > .chart-waffle__grid > .chart-waffle__cell[data-tone]` + `.chart-waffle__legend`. Motion animates `.chart-waffle__cell` opacity/scale with grid stagger.
- histogram: `.chart-hist > .chart-hist__bin > (.chart-hist__value, .chart-hist__bar[data-tone], .chart-hist__label)`. Motion animates `.chart-hist__bar` scaleY (origin bottom).
- pairedBars: `.chart-paired > .chart-paired__group > (.chart-paired__label, .chart-paired__row x2 > .chart-paired__track > .chart-paired__fill[data-tone])`. Motion animates `.chart-paired__fill` scaleX.
- table: `.chart-table-wrap (overflow-x auto) > table.chart-table > thead + tbody > tr`. Motion animates `tbody tr` opacity + y.
- Every chart root gets `.chart__title` (mono uppercase) above and optional `.chart__note` below.

Widths of fills are set inline by charts.js as `style="--w: 62%"` and CSS uses `width: var(--w)`; motion only touches transform/opacity.

## Storytelling direction (from the client, binding)

The page is a BILL we hand to the audience for the tokens they burned. Tone: dry, confident, a little cheeky, never corporate.

- Hero headline (ice-breaker, huge Schibsted): `Kartą czy gotówką?` Lede: `Wystawiamy wam rachunek za spalone tokeny. 9 770 sesji, 116 677 USD. Pozycja po pozycji.` The stars line above reads `* * * * RACHUNEK ZA TOKENY * * * *`. Hero receipt lines: SESJI, TRANSKRYPTÓW, WYWOŁAŃ API, then `DO ZAPŁATY 116 677 USD` (big, count-up).
- Every thesis section is a line item on the bill: `01  LINIE W COMMICIE ............ 25 031 USD`. The `usd` is what that item cost (from SIX_THESES / FINDINGS: t1 vibe usd 25 031 + 7 481 + 481 = 32 993 for vibe generated code; t2 unread usd 68,43 + 19,35 + 1 = about 89 USD plus context rent, use 89; t3 subagents Task context rent 1 898 + 266 = 2 164; t4 compaction reread 50,56 recached + 36 593 usd in compacted sessions (use 36 593 as "usd w sesjach z kompakcją" and show the reread 50,56 separately in the lede); t5 polling 1 082 + 268 + 9,93 = about 1 360; t6 hot files: no direct USD, show `2 908 par` instead of USD in the line item and add 0 to the ticker but keep a mono note `bez wyceny`). The section lede must say plainly what the audience paid for and why ("Zapłaciliście X za Y").
- The sticky ticker `SUMA DOTĄD` accumulates these amounts as the audience scrolls, so the bill grows under their nose.
- Closing = the finale, the biggest moment on the page ("rozpierdol"): the ten summary lines print fast one after another (rapid stagger, dot-matrix ticking), then `DO ZAPŁATY 116 677 USD` slams in at full width with a 1-frame screen shake, a red rotated `NIEZAPŁACONE` stamp thuds onto it, the paper visibly jolts (translateY -2px, back), the sulphur band floods the background from the bottom (scaleY), the halftone barcode prints, dither "sparks" (a burst of ink pixels from the total, canvas-based, part of the `barcode` scene: it gets `p` and should explode dots outward around p 0.6..1), then `DZIĘKUJEMY ZA WSZYSTKIE DANE` and the torn bottom edge. Closing lines use FINDINGS section 1: cache reads 64% (74 600 USD), cache writes 22% (26 000 USD), output 9%, fresh input 5%, coffee break cache breaks 9 223 USD, tool results context rent 30 746 USD, never-used tool results about 10 000 USD, pushback turns 16 548 USD, harness writes 75% of the prompt, human hours 8,6x tokens.

## Two variants (client request)

- Variant A `index.html`: as above, with halftone stamps in every section.
- Variant B `paragon.html`: identical copy and data, pure thermal receipt look: narrow strip (about 30rem), all text in `--font-mono` uppercase dot-matrix feel, block-character bars, dashed rules, no halftone stamps (figures hidden, no canvases registered), same GSAP printing reveal and count-ups. Implemented as `<body class="rx-page rx-page--paper">` plus `css/paper.css` overrides loaded after the other CSS; render.js checks `document.body.classList.contains('rx-page--paper')` to skip stamps and to add an ASCII bar string `.chart-bars__ascii` next to each bar (e.g. `▓▓▓▓▓▓░░░░`). A tiny `A / B` switch link in the header points between the two files.

## Slide mode (client request, binding for both variants)

Scrolling must behave like a slide deck: one section = one slide, the page snaps so a slide is shown whole or not at all, and every slide fits a laptop screen (design target: 1280x800 and 1440x900 CSS px, usable height about 760px after the sticky header; must also survive 1366x768).

### Layout (tokens.css, receipt.css, paper.css, render.js)

- `:root { --header-h: 3rem; --slide-h: calc(100svh - var(--header-h)); }`. Header is `height: var(--header-h)` exactly, sticky.
- `html { scroll-snap-type: y mandatory; scroll-padding-top: var(--header-h); }` at `min-width: 900px` and `min-height: 620px`; below that `proximity` and no forced slide height (normal flow, single column).
- `.rx-section { min-height: var(--slide-h); scroll-snap-align: start; scroll-snap-stop: always; display: grid; align-content: center; padding-block: clamp(1rem, 3svh, 2rem); }`. The strip becomes wide enough for two columns: `--strip-w: min(100% - 3rem, 84rem)` in variant A, `min(100% - 3rem, 72rem)` in variant B (B stays mono and thermal but widens for slides). Strip vertical margins and teeth stay only at the very top and bottom of the whole receipt; the first slide (hero) starts right after the top teeth, so hero `min-height` subtracts the teeth height.
- render.js wraps every thesis section's content in a slide grid: `.rx-print > .rx-slide > (.rx-slide__copy, .rx-slide__data)`. `__copy` (left, about 42%): `.rx-lineitem`, `h2.rx-title`, `p.rx-lede`, `.rx-big`, `.rx-callouts`, `.rx-gap`, `figure.rx-stamp`, `p.rx-footnote`. `__data` (right, about 58%): `.rx-charts` with all charts. Hero: `.rx-slide--hero` with `__copy` = stars, h1, lede, highlight; `__data` = `.rx-lines` + `figure.rx-stamp`. Closing: `.rx-slide--closing` with `__copy` = `.rx-lineitem`, `.rx-lines` (ten lines), `__data` = `.rx-total`, `.rx-gap--unpaid`, `figure.rx-stamp` (barcode), `.rx-thanks`, `.rx-sources`, and in variant B the CSS barcode.
- Fit rules: `.rx-slide { display: grid; grid-template-columns: 42fr 58fr; gap: clamp(1.5rem, 3vw, 3.5rem); align-items: center; max-height: calc(var(--slide-h) - 2 * padding); }`. `.rx-slide__data { max-height: 100%; overflow-y: auto; scrollbar-width: thin; }` as a safety valve only (content should fit without it). Vertical rhythm inside slides scales with viewport height: margins use `clamp(0.4rem, 1.2svh, 1rem)` style values. Type: section `.rx-title` `clamp(1.7rem, 3.2vw, 2.7rem)`, hero title `clamp(2.6rem, 5vw, 4.4rem)`, `.rx-big .rx-num` `clamp(2.4rem, 7svh, 4.6rem)`, lede `clamp(0.95rem, 1.1vw, 1.1rem)` max 34em, footnote 0.68rem. Stamp canvas: `width: 100%; height: clamp(120px, 24svh, 260px); aspect-ratio: auto;` (the engine sizes the buffer from the CSS box, scenes adapt to any w/h). Charts compact: chart title 0.65rem, bar rows `padding-block: 0.18rem`, bar track height 10px, histogram area `clamp(80px, 13svh, 140px)`, waffle cells 9px gap 2px, table font 0.68rem and at most 8 rows, chart-to-chart gap `clamp(0.6rem, 1.6svh, 1.25rem)`. The section separator (dashed rule + perforation dots) stays at the top edge of each slide.
- A slide counter in the header: render.js adds `span.rx-header__slide` (mono, e.g. `03 / 08`) inside `.rx-header__meta` area; motion.js updates it. A right-edge dot nav `nav.rx-dots > a.rx-dots__dot[href="#s-t1"]` (one per section, fixed, vertically centered, 6px ink squares, active one filled vermilion) is added by render.js; hidden below 900px.
- Variant B keeps: mono everywhere, thermal banding, star rules, block bars, no stamps (the `__copy` column simply has no figure; give `__copy` in B a large mono ornament instead: a `.rx-slide__ornament` div with a `* * *` / `=====` text block generated in CSS `::before`, so the column is not empty).

### Motion (motion.js)

- No scrub anywhere except nothing: the print reveal becomes a per-slide timeline played once when the slide snaps in: `ScrollTrigger.create({ trigger: section, start: 'top 55%', end: 'bottom 45%', onEnter, onEnterBack })` -> `playSlide(section)` (idempotent, plays once). The slide timeline: (1) `.rx-print` clip-path `inset(0 0 100% 0)` to `inset(0 0 0% 0)` over 1.0 s `power1.inOut`, printhead follows the edge via onUpdate (rect.top + rect.height * progress) and hides at the end, halftone `p` driven by the same progress; (2) at 0.25 s the line item slides in; (3) at 0.45 s count-ups start; (4) at 0.6 s charts grow in (stagger as before); (5) at 0.9 s callouts fade, highlighter sweeps, gap stamp thuds. Slides that are not yet played stay clipped (`inset(0 0 100% 0)`) so the deck feels printed page by page. The closing finale keeps its own timeline, triggered by the same enter logic.
- Keyboard: ArrowDown / PageDown / Space -> next slide, ArrowUp / PageUp -> previous, Home / End; implemented with `section.scrollIntoView({ behavior: 'smooth', block: 'start' })` (respect reduced motion: `auto`). Wheel is left to native CSS snap.
- Slide counter: update `span.rx-header__slide` and the active `.rx-dots__dot` from the same enter/enterBack callbacks (`is-active` class).
- Ticker: unchanged (adds on enter, subtracts on leaveBack) but use the slide trigger's callbacks so it stays in sync with the counter.
- Reduced motion: everything printed and final immediately, snapping still on.
- Mobile / short viewports (below 900px width or 620px height, via `gsap.matchMedia`): no slide timelines, fall back to the previous one-shot per-element triggers at 'top 85%' with the print reveal as a 0.8 s one-shot on enter.

## Pitch cut (client feedback, binding, overrides earlier content mapping)

This is a hackathon pitch deck, not a report. Target: about 10% of the previous text. Per slide: one line item, ONE headline sentence (the hero of the slide, big), ONE number, at most ONE small chart with at most 5 rows/bins, no footnotes, no callouts, no method sentences. Amounts under 1 000 USD are never shown anywhere (they read as noise next to 116 677 USD). No per-model splits where the model does not matter.

- Hero: `Kartą czy gotówką?`, lede `Wystawiamy wam rachunek za spalone tokeny. 9 770 sesji, pozycja po pozycji.`; lines: SESJI 9 770, WYWOŁAŃ API 933 529, DO ZAPŁATY 116 677 USD (big). Remove the highlight line entirely (`highlight: null`). Stamp sun stays.
- t1 `01 LINIE W COMMICIE` 32 993 USD. Headline: `Połowa wygenerowanego kodu nie dożywa commita.` Number: `51%` label `linii z trybu vibe trafia do commita`. Chart: bars, 3 rows, vibe only: claude_code 51%, opencode 25,4%, codex 17,2% (tone bad). Nothing else. Scene sharks.
- t2 `02 NIEPRZECZYTANE`, no amount, `usdDisplay: 'TL;DR'`, usd 0, no note. Headline: `Płacicie za odpowiedzi, których nikt nie czyta.` Number: `21%` label `tokenów końcowych odpowiedzi trafia do nikogo`. Chart: ONE stacked bar, all harnesses summed: przeczytane 57 613, nieprzeczytane 8 915 (of 66 528 final replies; unread hatched). Scene skulls.
- t3 `03 SUBAGENCI` 2 164 USD. Headline: `Sesja z subagentami kosztuje trzy razy więcej.` Number: `3x` (value 3, suffix 'x') label `mediana kosztu sesji vibe: 4,44 USD z Taskiem, 1,45 USD bez`. Chart: bars, 2 rows: `bez Task` 1,45 USD (ink), `z Task` 4,44 USD (bad). Keep the gap stamp `LUKA W DANYCH: transkrypty subagentów nieobecne`. Scene fish.
- t4 `04 KOMPAKCJA` 36 593 USD. Headline: `Po kompakcji model czyta te same pliki od nowa.` Number: `59%` label `odczytów po kompakcji to pliki już czytane w tej sesji`. Chart: bars, 2 rows: codex 25,9% sesji z kompakcją (bad), claude_code 10,3% (ink). No table. Scene vortex.
- t5 `05 SLEEP` 1 360 USD. Headline: `Agent przespał 245 godzin w pętli sleep.` Number: `202` suffix ` h` label `w samych wywołaniach sleep 300 s i dłuższych`. Chart: histogram, 5 bins (hours slept: 2,8 / 6,2 / 4,7 / 29,4 / 202). Scene beach.
- t6 `06 GORĄCE PLIKI`, `usdDisplay: '2 908 par'`, usd 0, no note. Headline: `Jeden plik, 120 sesji, 8 osób, w tym samym czasie.` Number: `2 908` label `par sesji edytujących ten sam plik jednocześnie`. Chart: bars, 3 rows, top hot files by overlapping pairs (manual_commit_condensation.go 45, committed.go 40, explain.go 37), labels = file name only, sub = repo. Scene surfers.
- Closing `RAZEM`: 5 lines only: Odczyty cache 74 600 USD, Wyniki narzędzi w kontekście 30 746 USD, Zapisy cache 26 000 USD, Pushback 16 548 USD, Przerwa na kawę 9 223 USD. Total DO ZAPŁATY 116 677 USD, stamp NIEZAPŁACONE, thanks, sources line reduced to `SWE-chat enhanced 2026-07-05 · analiza Quesma`. Barcode stays.
- Ledes on thesis slides: none (the headline is the sentence). `footnote: null`, `callouts: []` everywhere.

Layout consequences (receipt.css, paper.css): the headline `.rx-title` on slides gets bigger (`clamp(2rem, 3.6vw, 3.4rem)`, line-height 1.02), the big number gets smaller (`clamp(2rem, 5.5svh, 3.4rem)`) and sits on one line with its label to the right (`.rx-big { display: flex; align-items: baseline; gap: 1rem }`, label max-width 18em), chart labels bigger (0.85rem, values 0.95rem, tracks 14px, histogram bins with bigger value labels), lede on the hero bigger (`clamp(1.05rem, 1.4vw, 1.3rem)`). Copy and data columns 50/50. Everything else unchanged.

Correction to the pitch cut (client): never write "bez wyceny" or "nie umiemy wycenić" anywhere. Where there is no exact amount, do not show one, but say concretely where the tokens go:
- t2 line item shows `usdDisplay: 'CZYNSZ ZA KONTEKST'` (no amount). Headline `Płacicie za odpowiedzi, których nikt nie czyta.`, number 21% as above, and ONE short sub-line under the number (`.rx-big__label`): `każdy nieprzeczytany akapit zostaje w kontekście i jest opłacany przy każdym kolejnym wywołaniu`.
- t6 line item shows `usdDisplay: 'PODWÓJNA ROBOTA'` (no amount). Headline `Jeden plik, 120 sesji, 8 osób, w tym samym czasie.`, number `28%` label `edycji gorących plików to agent naprawiający to, co sam zepsuł`. Chart: bars, 3 rows: `hub architektury` 55%, `regresja agenta` 28% (bad), `plik testowy` 9%. The tokens are lost on conflicting edits and on the agent redoing its own work; no amount is shown.

## Receipt look, stronger (client feedback, binding, both variants)

- Torn paper edges must be obvious: teeth `--tooth-h: 18px`, `--tooth-w: 26px`, two-layer tear (a second, offset zigzag layer in `--paper-muted` 1px behind for depth), and a darker desk behind the paper in variant A too: `body` background `--paper-deep` with a subtle radial vignette, so the bright strip reads as a physical receipt. Keep the crumple shadow, make it stronger (like variant B).
- Hero gets a receipt header block above the stars line: `p.rx-invoice` with the word `RACHUNEK` in Fragment Mono, uppercase, `clamp(3rem, 8vw, 6.5rem)`, letter-spacing 0.18em, line-height 0.95, ink, with a dotted rule under it; then `ul.rx-meta` (mono, small, two columns) with rows from `hero.meta`: `NR` `0001/2026-07-05`, `DATA` `11.09.2026`, `KASA` `SWE-chat enhanced`, `KASJER` `Quesma`, `POZYCJI` `6`. Data fields: `hero.invoice: 'RACHUNEK'`, `hero.meta: [{k:'NR', v:'0001/2026-07-05'}, ...]`. In variant B the same, centered.
- Thermal look in A as well: faint horizontal banding on the strip (1px lines every 3px at 2% ink, like paper.css), and every `.rx-lineitem` gets a leading `#` style number box kept as is.
- Closing: `.rx-total` boxed with `border: 3px double var(--ink)` and padding, the word `DO ZAPŁATY` bigger; barcode stays; under the barcode a mono line `NIP 0000000000 · KASA 01 · W 2026.07.05` (decorative, from `closing.fiscal`).
- Slides must still fit (`--slide-h`); the hero copy column gains about 130px, so shrink the hero title to `clamp(2.2rem, 4.2vw, 3.6rem)` and the hero lede to one line if needed.
