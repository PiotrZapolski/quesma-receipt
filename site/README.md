# Rachunek za tokeny

Statyczna strona (jedna długa "paragonowa" taśma) prezentująca sześć tez z analizy
zbioru SWE-chat enhanced. Polski, jasny motyw, system projektowy Quesma.

Bez builda. Bez npm. Bez modułów ES. Zwykłe `<script defer>` w ustalonej kolejności,
GSAP i ScrollTrigger 3.12.5 z cdnjs.

## Struktura

```
site/
  index.html          szkielet: header, main#strip, print head, filtr ziarna
  css/tokens.css      zmienne: paleta, typografia, easing, odstępy
  css/receipt.css     taśma, rozdarte brzegi, header, ticker, typografia
  css/charts.css      wykresy (słupki, waffle, histogram, tabele)
  js/data.js          WSZYSTKIE liczby i cała treść (window.RECEIPT_DATA)
  js/charts.js        renderery wykresów (window.Charts)
  js/halftone/*.js    silnik rastra i sceny (window.Halftone, window.Scenes)
  js/render.js        buduje DOM z danych (window.Render)
  js/motion.js        GSAP / ScrollTrigger (window.Motion)
  js/main.js          boot
```

## Jak zmieniać treść

Cała treść i wszystkie liczby są w `js/data.js`. Nic innego nie trzeba ruszać.

- `hero` - nagłówek, lede, linie paragonu, zdanie z żółtym zakreślaczem.
- `sections[]` - sześć tez. Każda ma `number`, `lineItem`, `usd` (dolicza się do
  tickera "SUMA DOTĄD"), `title` (dozwolony jeden `<em>`, renderuje się na
  wermilion), `lede`, `big`, `charts[]`, `callouts[]`, `gap`, `footnote`,
  `scene`, `sceneLabel`.
- `closing` - dziesięć linii podsumowania, suma, stempel, podziękowanie, źródła.

Zasady przy edycji:

1. Liczby do animacji (`value`) zapisujemy surowo (`116677`, `17.8`).
   Liczby pokazywane jako gotowy tekst (`display`) zapisujemy już po polsku
   (`'116 677 USD'`, `'17,2%'`).
2. Żadnych długich myślników (em dash, en dash). Tylko zwykły `-`.
3. Kolory tylko z `css/tokens.css`. W danych podajemy `tone`:
   `ink | bad | good | neutral | warn | focus`.
4. Nowa sekcja = nowy obiekt w `sections[]` plus istniejąca nazwa sceny
   (`sun`, `sharks`, `skulls`, `fish`, `vortex`, `beach`, `surfers`, `barcode`).

Typy wykresów: `bars`, `stackedBars`, `waffle`, `histogram`, `pairedBars`, `table`.
Kształty specyfikacji opisuje `CONTRACT.md`.

## Podgląd lokalny

`index.html` otwiera się prosto z dysku (`file://`) - wszystkie ścieżki są
względne, a GSAP leci z cdnjs. Serwer nie jest potrzebny.

## Deploy

Katalog `site/` wrzuca się jak leży, bez kroku budowania.

**Cloudflare Pages**

1. Połącz repozytorium.
2. Build command: puste. Build output directory: `site`.
3. Deploy.

**GitHub Pages**

1. Ustawienia repozytorium, Pages, źródło: gałąź `main`, katalog `/site`
   (albo skopiuj zawartość `site/` do `/docs` i wskaż `/docs`).
2. Zapisz.

**Dowolny inny hosting statyczny**: skopiuj zawartość `site/` do katalogu
serwowanego. Jedyne zasoby zewnętrzne to Google Fonts i cdnjs.
