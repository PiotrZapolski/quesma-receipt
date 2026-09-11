/* Quesma "Rachunek za tokeny" - chart renderers.
 * Exposes exactly one global: window.Charts = { render(el, spec) }.
 * Nothing runs at load time. No innerHTML with data, textContent only.
 * Fill sizes are inline custom properties (--w / --h); CSS reads them.
 * Motion.js animates transform/opacity only, so nothing here sets a transform.
 */
(function (window, document) {
  'use strict';

  /* ---------------------------------------------------------------- utils */

  var TONES = { ink: 1, bad: 1, good: 1, neutral: 1, warn: 1, focus: 1 };

  function tone(t) {
    return (t && TONES[t]) ? t : 'ink';
  }

  function elem(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) { node.className = cls; }
    if (text !== undefined && text !== null && text !== '') { node.textContent = String(text); }
    return node;
  }

  function num(v) {
    var n = typeof v === 'number' ? v : parseFloat(v);
    return isFinite(n) ? n : 0;
  }

  var NF_CACHE = {};

  function nf(minFrac, maxFrac) {
    var key = minFrac + '/' + maxFrac;
    if (!NF_CACHE[key]) {
      /* 'always' keeps the thousands space on 4 digit numbers too
         (pl-PL groups from 5 digits by default): 9 770, not 9770 */
      NF_CACHE[key] = new Intl.NumberFormat('pl-PL', {
        minimumFractionDigits: minFrac,
        maximumFractionDigits: maxFrac,
        useGrouping: 'always'
      });
    }
    return NF_CACHE[key];
  }

  /* pl-PL: space thousands, comma decimals. Integers stay integers,
     small fractions keep enough digits to stay honest (0,0029). */
  function formatNumber(v) {
    if (typeof v !== 'number' || !isFinite(v)) {
      return (v === undefined || v === null) ? '' : String(v);
    }
    if (Math.round(v) === v) { return nf(0, 0).format(v); }
    var abs = Math.abs(v);
    if (abs < 1) { return nf(2, 4).format(v); }
    return nf(1, 2).format(v);
  }

  function withUnit(text, unit) {
    if (!unit) { return text; }
    var u = String(unit);
    if (u.charAt(0) === ' ' || u === '%') { return text + u; }
    return text + ' ' + u;
  }

  /* Value shown at the end of a bar: preformatted `display` wins. */
  function valueText(row, unit) {
    if (row && row.display !== undefined && row.display !== null && row.display !== '') {
      return String(row.display);
    }
    return withUnit(formatNumber(num(row && row.value)), unit);
  }

  function pct(n) {
    if (!isFinite(n)) { n = 0; }
    if (n < 0) { n = 0; }
    return (Math.round(n * 100) / 100) + '%';
  }

  function share(value, total) {
    if (!(total > 0)) { return 0; }
    return Math.max(0, Math.min(100, (value / total) * 100));
  }

  function text(v) {
    return (v === undefined || v === null) ? '' : String(v);
  }

  /* Visually hidden data table, so the numbers survive without sight. */
  function srTable(head, rows, caption) {
    var table = elem('table', 'sr-only');
    if (caption) { table.appendChild(elem('caption', null, caption)); }
    var thead = document.createElement('thead');
    var hr = document.createElement('tr');
    for (var i = 0; i < head.length; i++) {
      var th = elem('th', null, head[i]);
      th.setAttribute('scope', 'col');
      hr.appendChild(th);
    }
    thead.appendChild(hr);
    table.appendChild(thead);
    var tbody = document.createElement('tbody');
    for (var r = 0; r < rows.length; r++) {
      var tr = document.createElement('tr');
      for (var c = 0; c < rows[r].length; c++) {
        tr.appendChild(elem('td', null, rows[r][c]));
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    return table;
  }

  /* ----------------------------------------------------------------- bars */

  function buildBars(spec) {
    var rows = spec.rows || [];
    var max = num(spec.max);
    if (!(max > 0)) {
      max = rows.reduce(function (m, r) { return Math.max(m, num(r.value)); }, 0);
    }
    if (!(max > 0)) { max = 1; }

    var wrap = elem('div', 'chart-bars');
    var sr = { head: ['Pozycja', 'Wartość'], rows: [] };

    rows.forEach(function (r) {
      var row = elem('div', 'chart-bars__row');

      var label = elem('div', 'chart-bars__label', text(r.label));
      if (r.sub) { label.appendChild(elem('span', 'chart-bars__sub', text(r.sub))); }
      row.appendChild(label);

      var value = num(r.value);
      var over = value > max;
      var track = elem('div', 'chart-bars__track');
      var fill = elem('div', 'chart-bars__fill');
      fill.setAttribute('data-tone', tone(r.tone));
      fill.style.setProperty('--w', pct(share(value, max)));
      track.appendChild(fill);
      if (over) {
        /* clamped at 100%, marked as running off the scale */
        track.appendChild(elem('span', 'chart-bars__over', '▸'));
      }
      row.appendChild(track);

      var val = elem('div', 'chart-bars__value', valueText(r, spec.unit));
      if (r.note) { val.appendChild(elem('span', 'chart-bars__note', text(r.note))); }
      row.appendChild(val);

      wrap.appendChild(row);
      sr.rows.push([
        text(r.label) + (r.sub ? ' (' + text(r.sub) + ')' : ''),
        valueText(r, spec.unit) + (r.note ? ' ' + text(r.note) : '') + (over ? ' (poza skalą)' : '')
      ]);
    });

    return { body: wrap, sr: sr };
  }

  /* ---------------------------------------------------------- stackedBars */

  function buildStacked(spec) {
    var rows = spec.rows || [];
    var wrap = elem('div', 'chart-stacked');
    var sr = { head: ['Pozycja', 'Razem', 'Składniki'], rows: [] };

    rows.forEach(function (r) {
      var parts = r.parts || [];
      var sum = parts.reduce(function (s, p) { return s + num(p.value); }, 0);
      var total = num(r.total);
      if (!(total > 0)) { total = sum; }

      var row = elem('div', 'chart-stacked__row');
      row.appendChild(elem('div', 'chart-stacked__label', text(r.label)));

      var track = elem('div', 'chart-stacked__track');
      var described = [];
      parts.forEach(function (p) {
        var part = elem('div', 'chart-stacked__part');
        part.setAttribute('data-tone', tone(p.tone));
        part.style.setProperty('--w', pct(share(num(p.value), total)));
        var caption = text(p.label);
        var pv = withUnit(formatNumber(num(p.value)), spec.unit);
        part.setAttribute('title', caption ? caption + ': ' + pv : pv);
        track.appendChild(part);
        described.push((caption ? caption + ' ' : '') + pv);
      });
      row.appendChild(track);

      row.appendChild(elem('div', 'chart-stacked__value',
        (r.display !== undefined && r.display !== null && r.display !== '')
          ? String(r.display)
          : withUnit(formatNumber(total), spec.unit)));

      wrap.appendChild(row);
      sr.rows.push([
        text(r.label),
        (r.display !== undefined && r.display !== null && r.display !== '')
          ? String(r.display)
          : withUnit(formatNumber(total), spec.unit),
        described.join(', ')
      ]);
    });

    return { body: wrap, sr: sr };
  }

  /* --------------------------------------------------------------- waffle */

  /* Round a cell value up to a readable step: 1, 2, 2.5, 5, 10 x 10^n. */
  function niceStep(v) {
    if (!(v > 0)) { return 1; }
    var mag = Math.pow(10, Math.floor(Math.log(v) / Math.LN10));
    var steps = [1, 2, 2.5, 5, 10];
    for (var i = 0; i < steps.length; i++) {
      var candidate = steps[i] * mag;
      if (candidate >= v - 1e-9) { return candidate; }
    }
    return 10 * mag;
  }

  function waffleCounts(groups, cellValue, maxCells) {
    var cv = cellValue > 0 ? cellValue : 1;
    var counts = [];
    var guard = 0;
    while (guard++ < 40) {
      counts = groups.map(function (g) {
        return Math.max(0, Math.round(num(g.value) / cv));
      });
      var total = counts.reduce(function (s, n) { return s + n; }, 0);
      if (total <= maxCells) { break; }
      var next = niceStep(cv * (total / maxCells));
      if (!(next > cv)) { next = cv * 2; }
      cv = next;
    }
    return { counts: counts, cellValue: cv };
  }

  /* '■ = 10 sesji' -> '■ = 25 sesji' when the cell value had to grow. */
  function retuneLegend(legend, cellValue, changed) {
    var s = text(legend);
    if (!changed) { return s; }
    var formatted = formatNumber(cellValue);
    if (/\d/.test(s)) {
      return s.replace(/\d+(?:[  ]\d{3})*(?:[.,]\d+)?/, formatted);
    }
    return s ? s + ' (■ = ' + formatted + ')' : '■ = ' + formatted;
  }

  function buildWaffle(spec) {
    var groups = spec.groups || [];
    var maxCells = num(spec.maxCells) > 0 ? num(spec.maxCells) : 100;
    var base = num(spec.cellValue) > 0 ? num(spec.cellValue) : 1;
    var tuned = waffleCounts(groups, base, maxCells);

    var wrap = elem('div', 'chart-waffle');
    var grid = elem('div', 'chart-waffle__grid');

    groups.forEach(function (g, gi) {
      var t = tone(g.tone);
      for (var i = 0; i < tuned.counts[gi]; i++) {
        var cell = elem('span', 'chart-waffle__cell');
        cell.setAttribute('data-tone', t);
        grid.appendChild(cell);
      }
    });
    wrap.appendChild(grid);

    var legend = elem('div', 'chart-waffle__legend');
    var legendText = retuneLegend(spec.legend, tuned.cellValue, tuned.cellValue !== base);
    if (legendText) {
      legend.appendChild(elem('span', 'chart-waffle__legend-note', legendText));
    }
    groups.forEach(function (g, gi) {
      var item = elem('span', 'chart-waffle__legend-item');
      var swatch = elem('span', 'chart-waffle__swatch');
      swatch.setAttribute('data-tone', tone(g.tone));
      swatch.setAttribute('aria-hidden', 'true');
      item.appendChild(swatch);
      item.appendChild(elem('span', 'chart-waffle__legend-label', text(g.label)));
      item.appendChild(elem('span', 'chart-waffle__legend-value',
        withUnit(formatNumber(num(g.value)), spec.unit)));
      legend.appendChild(item);
      void gi;
    });
    wrap.appendChild(legend);

    var sr = { head: ['Grupa', 'Wartość', 'Kwadraty'], rows: [] };
    groups.forEach(function (g, gi) {
      sr.rows.push([
        text(g.label),
        withUnit(formatNumber(num(g.value)), spec.unit),
        formatNumber(tuned.counts[gi])
      ]);
    });

    return { body: wrap, sr: sr };
  }

  /* ------------------------------------------------------------ histogram */

  function buildHistogram(spec) {
    var bins = spec.bins || [];
    var max = bins.reduce(function (m, b) { return Math.max(m, num(b.value)); }, 0);
    if (!(max > 0)) { max = 1; }

    var wrap = elem('div', 'chart-hist');
    var sr = { head: ['Przedział', 'Wartość'], rows: [] };

    bins.forEach(function (b) {
      var bin = elem('div', 'chart-hist__bin');
      var label = (b.display !== undefined && b.display !== null && b.display !== '')
        ? String(b.display)
        : withUnit(formatNumber(num(b.value)), spec.unit);

      bin.appendChild(elem('div', 'chart-hist__value', label));

      var bar = elem('div', 'chart-hist__bar');
      bar.setAttribute('data-tone', tone(b.tone));
      bar.style.setProperty('--h', pct(share(num(b.value), max)));
      bin.appendChild(bar);

      bin.appendChild(elem('div', 'chart-hist__label', text(b.label)));
      wrap.appendChild(bin);
      sr.rows.push([text(b.label), label]);
    });

    return { body: wrap, sr: sr };
  }

  /* ----------------------------------------------------------- pairedBars */

  function pairedRow(side, defaultTone, max, unit) {
    var row = elem('div', 'chart-paired__row');
    row.appendChild(elem('div', 'chart-paired__rowlabel', text(side && side.label)));
    var track = elem('div', 'chart-paired__track');
    var fill = elem('div', 'chart-paired__fill');
    fill.setAttribute('data-tone', tone(side && side.tone ? side.tone : defaultTone));
    fill.style.setProperty('--w', pct(share(num(side && side.value), max)));
    track.appendChild(fill);
    row.appendChild(track);
    row.appendChild(elem('div', 'chart-paired__value', valueText(side || {}, unit)));
    return row;
  }

  function buildPaired(spec) {
    var pairs = spec.pairs || [];
    var max = num(spec.max);
    if (!(max > 0)) {
      max = pairs.reduce(function (m, p) {
        return Math.max(m, num(p.a && p.a.value), num(p.b && p.b.value));
      }, 0);
    }
    if (!(max > 0)) { max = 1; }

    var wrap = elem('div', 'chart-paired');
    var sr = { head: ['Grupa', 'Pozycja', 'Wartość'], rows: [] };

    pairs.forEach(function (p) {
      var group = elem('div', 'chart-paired__group');
      group.appendChild(elem('div', 'chart-paired__label', text(p.label)));
      group.appendChild(pairedRow(p.a, 'ink', max, spec.unit));
      group.appendChild(pairedRow(p.b, 'bad', max, spec.unit));
      wrap.appendChild(group);
      sr.rows.push([text(p.label), text(p.a && p.a.label), valueText(p.a || {}, spec.unit)]);
      sr.rows.push([text(p.label), text(p.b && p.b.label), valueText(p.b || {}, spec.unit)]);
    });

    return { body: wrap, sr: sr };
  }

  /* ---------------------------------------------------------------- table */

  var NUMERIC = /^[+\-−]?\d[\d\s .,]*\s*(%|USD|GB|MB|kB|s|min|h|x|pkt)?$/i;

  function looksNumeric(v) {
    var s = text(v).trim();
    if (!s) { return false; }
    return NUMERIC.test(s);
  }

  function buildTable(spec) {
    var columns = spec.columns || [];
    var rows = spec.rows || [];
    var mono = {};
    (spec.mono || []).forEach(function (i) { mono[i] = true; });

    /* a column is numeric when every filled cell in it looks like a number */
    var numericCol = columns.map(function (c, i) {
      var seen = 0;
      for (var r = 0; r < rows.length; r++) {
        var cell = rows[r] ? rows[r][i] : '';
        if (text(cell).trim() === '') { continue; }
        seen++;
        if (!looksNumeric(cell)) { return false; }
      }
      void c;
      return seen > 0;
    });

    var wrap = elem('div', 'chart-table-wrap');
    var table = elem('table', 'chart-table');

    var thead = document.createElement('thead');
    var headRow = document.createElement('tr');
    columns.forEach(function (c, i) {
      var th = elem('th', null, text(c));
      th.setAttribute('scope', 'col');
      if (mono[i]) { th.classList.add('is-mono'); }
      if (numericCol[i]) { th.classList.add('is-num'); }
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = document.createElement('tbody');
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      for (var i = 0; i < columns.length; i++) {
        var cell = r ? r[i] : '';
        var td = elem('td', null, text(cell));
        if (mono[i]) { td.classList.add('is-mono'); }
        if (numericCol[i] || looksNumeric(cell)) { td.classList.add('is-num'); }
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    wrap.appendChild(table);
    return { body: wrap, sr: null, table: table };
  }

  /* --------------------------------------------------------------- render */

  var BUILDERS = {
    bars: buildBars,
    stackedBars: buildStacked,
    waffle: buildWaffle,
    histogram: buildHistogram,
    pairedBars: buildPaired,
    table: buildTable
  };

  function render(el, spec) {
    if (!el || !spec) { return; }
    while (el.firstChild) { el.removeChild(el.firstChild); }

    var type = text(spec.type);
    if (!el.getAttribute('data-chart') && type) { el.setAttribute('data-chart', type); }
    if (!el.getAttribute('data-chart-id') && spec.id) { el.setAttribute('data-chart-id', text(spec.id)); }
    if (!el.classList.contains('chart')) { el.classList.add('chart'); }

    var title = text(spec.title);
    if (title) { el.appendChild(elem('div', 'chart__title', title)); }

    var builder = BUILDERS[type];
    if (!builder) {
      el.appendChild(elem('p', 'chart__note', 'Nieznany typ wykresu: ' + (type || '?')));
      return;
    }

    var out = builder(spec);

    /* The root stays a group so the hidden data table below the graphic
       remains readable; the graphic itself is the role="img". */
    el.setAttribute('role', 'group');
    if (title) { el.setAttribute('aria-label', title); }

    if (type === 'table') {
      if (title && out.table) { out.table.setAttribute('aria-label', title); }
    } else {
      out.body.setAttribute('role', 'img');
      out.body.setAttribute('aria-label', title || 'Wykres');
    }

    el.appendChild(out.body);

    if (out.sr) { el.appendChild(srTable(out.sr.head, out.sr.rows, title)); }

    if (spec.note) { el.appendChild(elem('p', 'chart__note', text(spec.note))); }
  }

  window.Charts = { render: render };

}(window, document));
