/* render.js - builds the whole receipt DOM inside <main id="strip"> from
   window.RECEIPT_DATA, following the DOM contract, then hands every chart
   container to window.Charts.render.
   Exposes exactly one global: window.Render = { build(data) }.
   Nothing runs at load time. */

(function (window, document) {
  'use strict';

  /* ------------------------------------------------------------------ */
  /* helpers                                                             */
  /* ------------------------------------------------------------------ */

  var formatters = {};

  function nf(decimals) {
    var d = decimals || 0;
    if (!formatters[d]) {
      formatters[d] = new Intl.NumberFormat('pl-PL', {
        minimumFractionDigits: d,
        maximumFractionDigits: d
      });
    }
    return formatters[d];
  }

  function fmt(value, decimals) {
    return nf(decimals).format(value);
  }

  function h(tag, cls, text) {
    var el = document.createElement(tag);
    if (cls) { el.className = cls; }
    if (text !== undefined && text !== null) { el.textContent = String(text); }
    return el;
  }

  function append(parent) {
    for (var i = 1; i < arguments.length; i++) {
      var child = arguments[i];
      if (child) { parent.appendChild(child); }
    }
    return parent;
  }

  /* The only place any data string reaches innerHTML: headings, where a single
     <em> is allowed (it renders vermilion). Everything else is escaped. */
  function setTitleHtml(el, raw) {
    var escaped = String(raw)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
    el.innerHTML = escaped
      .replace(/&lt;em&gt;/g, '<em>')
      .replace(/&lt;\/em&gt;/g, '</em>');
  }

  /* The same string without any markup, for aria-label on the dot nav. */
  function plainText(raw) {
    return String(raw).replace(/<[^>]*>/g, '');
  }

  function pad2(n) {
    return (n < 10 ? '0' : '') + n;
  }

  function leader() {
    var el = h('span', 'rx-leader');
    el.setAttribute('aria-hidden', 'true');
    return el;
  }

  function numSpan(value, decimals, suffix) {
    var el = h('span', 'rx-num');
    var sfx = suffix || '';
    el.setAttribute('data-count', String(value));
    el.setAttribute('data-decimals', String(decimals || 0));
    el.setAttribute('data-suffix', sfx);
    el.setAttribute('data-final', fmt(value, decimals || 0) + sfx);
    el.textContent = '0' + sfx;
    return el;
  }

  function receiptLine(line) {
    var li = h('li', 'rx-line' + (line.big ? ' rx-line--big' : ''));
    append(li, h('span', 'rx-line__label', line.label));
    if (line.note) { append(li, h('span', 'rx-line__note', line.note)); }
    append(li, leader(), numSpan(line.value, line.decimals, line.suffix));
    return li;
  }

  /* One slide = .rx-slide > (.rx-slide__copy, .rx-slide__data). Above the
     slide breakpoint css turns this into a 42fr / 58fr grid; below it the
     three wrappers are plain blocks and the receipt flows as before. */
  function slide(variant) {
    var wrap = h('div', 'rx-slide' + (variant ? ' rx-slide--' + variant : ''));
    var copy = h('div', 'rx-slide__copy');
    var data = h('div', 'rx-slide__data');
    append(wrap, copy, data);
    return { root: wrap, copy: copy, data: data };
  }

  /* Variant B has no halftone stamp, so the column would be empty where the
     figure used to sit. A printed mono ornament takes its place; the glyphs
     themselves come from css so the DOM carries no decorative text. */
  function ornament() {
    var el = h('div', 'rx-slide__ornament');
    el.setAttribute('aria-hidden', 'true');
    return el;
  }

  /* Variant B (body.rx-page--paper) prints no halftone at all: no figure and
     no canvas, so the engine finds nothing to register. */
  function stampFigure(scene, label, paper) {
    if (paper) { return ornament(); }

    var fig = h('figure', 'rx-stamp');
    fig.setAttribute('data-scene', scene);

    var canvas = document.createElement('canvas');
    canvas.className = 'rx-stamp__canvas';
    canvas.setAttribute('data-scene', scene);
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', 'Ilustracja rastrowa drukowana punktami: ' + label);
    append(fig, canvas);

    append(fig, h('figcaption', 'rx-stamp__label', label));
    return fig;
  }

  function chartContainer(spec) {
    var el = h('div', 'chart');
    el.setAttribute('data-chart', spec.type);
    el.setAttribute('data-chart-id', spec.id);
    return el;
  }

  /* ------------------------------------------------------------------ */
  /* sections                                                            */
  /* ------------------------------------------------------------------ */

  /* Ten block characters, filled in proportion to a bar's --w (e.g. 62%
     becomes the first six). Variant B only. */
  function asciiBar(percent) {
    var filled = Math.round((percent / 100) * 10);
    if (!(filled > 0)) { filled = 0; }
    if (filled > 10) { filled = 10; }
    var out = '';
    for (var i = 0; i < 10; i++) { out += (i < filled) ? '▓' : '░'; }
    return out;
  }

  /* Reads each fill's inline --w and prints the block string in front of the
     value text. Everything is guarded: a missing node just skips the row. */
  function addAsciiBars(root) {
    if (!root || typeof root.querySelectorAll !== 'function') { return; }

    var rows = root.querySelectorAll('.chart-bars__row, .chart-paired__row');
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var fill = row.querySelector('.chart-bars__fill, .chart-paired__fill');
      var value = row.querySelector('.chart-bars__value, .chart-paired__value');
      if (!fill || !value) { continue; }
      if (value.querySelector('.chart-bars__ascii')) { continue; }

      var w = fill.style ? fill.style.getPropertyValue('--w') : '';
      var percent = parseFloat(String(w).replace(',', '.'));
      if (!isFinite(percent)) { percent = 0; }

      var span = h('span', 'chart-bars__ascii', asciiBar(percent));
      span.setAttribute('aria-hidden', 'true');
      value.insertBefore(span, value.firstChild);
    }
  }

  function buildHero(hero, pending, paper) {
    var section = h('section', 'rx-section rx-section--hero');
    section.id = 's-hero';
    section.setAttribute('data-section', 'hero');

    var print = h('div', 'rx-print');
    var s = slide('hero');

    /* left: receipt header block, stars, headline, lede, highlighter */
    if (hero.invoice) { append(s.copy, h('p', 'rx-invoice', hero.invoice)); }

    if (hero.meta && hero.meta.length) {
      var meta = h('ul', 'rx-meta');
      hero.meta.forEach(function (row) {
        var li = h('li', 'rx-meta__row');
        append(li,
          h('span', 'rx-meta__k', row.k),
          h('span', 'rx-meta__v', row.v)
        );
        append(meta, li);
      });
      append(s.copy, meta);
    }

    append(s.copy, h('p', 'rx-stars', hero.stars));

    var title = h('h1', 'rx-title');
    setTitleHtml(title, hero.title);
    append(s.copy, title);

    if (hero.lede) { append(s.copy, h('p', 'rx-lede', hero.lede)); }

    if (hero.highlight) {
      var p = h('p', 'rx-highlight');
      append(p, h('span', 'rx-hl', hero.highlight));
      append(s.copy, p);
    }

    /* right: the receipt lines and the stamp */
    var lines = h('ul', 'rx-lines');
    hero.lines.forEach(function (line) { append(lines, receiptLine(line)); });
    append(s.data, lines);

    append(s.data, stampFigure(hero.scene, hero.sceneLabel, paper));

    append(print, s.root);
    append(section, print);
    return section;
  }

  function buildSection(data, pending, paper) {
    var section = h('section', 'rx-section');
    section.id = 's-' + data.id;
    section.setAttribute('data-section', data.id);
    section.setAttribute('data-usd', String(data.usd || 0));

    var print = h('div', 'rx-print');
    var s = slide(null);

    /* ---- left column: the words ---- */

    /* the bill row */
    var item = h('div', 'rx-lineitem');
    append(item,
      h('span', 'rx-lineitem__no', data.number),
      h('span', 'rx-lineitem__name', data.lineItem),
      leader(),
      h('span', 'rx-lineitem__usd',
        data.usdDisplay || (fmt(data.usd || 0, 0) + ' USD'))
    );
    if (data.usdNote) { append(item, h('span', 'rx-lineitem__note', data.usdNote)); }
    append(s.copy, item);

    var title = h('h2', 'rx-title');
    setTitleHtml(title, data.title);
    append(s.copy, title);

    /* pitch cut: thesis slides carry no lede, the headline is the sentence */
    if (data.lede) { append(s.copy, h('p', 'rx-lede', data.lede)); }

    if (data.big) {
      var big = h('div', 'rx-big');
      append(big,
        numSpan(data.big.value, data.big.decimals, data.big.suffix),
        h('span', 'rx-big__label', data.big.label)
      );
      append(s.copy, big);
    }

    if (data.callouts && data.callouts.length) {
      var callouts = h('div', 'rx-callouts');
      data.callouts.forEach(function (text) {
        append(callouts, h('p', 'rx-callout', text));
      });
      append(s.copy, callouts);
    }

    if (data.gap) { append(s.copy, h('p', 'rx-gap', data.gap)); }

    append(s.copy, stampFigure(data.scene, data.sceneLabel, paper));

    if (data.footnote) { append(s.copy, h('p', 'rx-footnote', data.footnote)); }

    /* ---- right column: the evidence ---- */

    if (data.charts && data.charts.length) {
      var charts = h('div', 'rx-charts');
      data.charts.forEach(function (spec) {
        var el = chartContainer(spec);
        append(charts, el);
        pending.push({ el: el, spec: spec });
      });
      append(s.data, charts);
    }

    append(print, s.root);
    append(section, print);
    return section;
  }

  function buildClosing(closing, paper) {
    var section = h('section', 'rx-section rx-section--closing');
    section.id = 's-closing';
    section.setAttribute('data-section', 'closing');

    /* sulphur band lives behind the print wrapper */
    var band = h('div', 'rx-band');
    band.setAttribute('aria-hidden', 'true');
    append(section, band);

    var print = h('div', 'rx-print');
    var s = slide('closing');

    /* ---- left column: the heading and the ten lines ---- */

    var item = h('div', 'rx-lineitem');
    append(item,
      h('span', 'rx-lineitem__no', '=='),
      h('span', 'rx-lineitem__name', closing.heading),
      leader(),
      h('span', 'rx-lineitem__usd', fmt(closing.total.value, 0) + (closing.total.suffix || ''))
    );
    append(s.copy, item);

    if (closing.lede) { append(s.copy, h('p', 'rx-lede', closing.lede)); }

    var lines = h('ul', 'rx-lines');
    closing.lines.forEach(function (line) { append(lines, receiptLine(line)); });
    append(s.copy, lines);

    /* ---- right column: the finale ---- */

    var total = h('div', 'rx-total');
    append(total,
      h('span', 'rx-total__label', closing.total.label),
      numSpan(closing.total.value, closing.total.decimals, closing.total.suffix)
    );
    append(s.data, total);

    if (closing.stamp) {
      append(s.data, h('p', 'rx-gap rx-gap--unpaid', closing.stamp));
    }

    append(s.data, stampFigure(closing.scene, closing.sceneLabel || 'KOD KRESKOWY', paper));
    append(s.data, h('p', 'rx-thanks', closing.thanks));
    append(s.data, h('p', 'rx-sources', closing.sources));

    /* variant B closes on a CSS barcode instead of the halftone one */
    if (paper) {
      var barcode = h('div', 'rx-barcode');
      barcode.setAttribute('aria-hidden', 'true');
      append(s.data, barcode);
      append(s.data, h('p', 'rx-barcode__digits', '9770 0116677 2026 0705'));
    }

    /* decorative fiscal footer, under the barcode in both variants */
    if (closing.fiscal) { append(s.data, h('p', 'rx-fiscal', closing.fiscal)); }

    append(print, s.root);
    append(section, print);
    return section;
  }

  /* ------------------------------------------------------------------ */
  /* deck chrome: slide counter and right edge dot nav                   */
  /* ------------------------------------------------------------------ */

  /* The counter is appended to the existing .rx-header__meta, so the meta
     text stays where it is and the counter reads as its right hand end.
     motion.js rewrites the text content on every slide change. */
  function buildSlideCounter(total) {
    var meta = document.querySelector('.rx-header__meta');
    if (!meta) { return; }

    var old = meta.querySelector('.rx-header__slide');
    if (old) { meta.removeChild(old); }

    var span = h('span', 'rx-header__slide', '01 / ' + pad2(total));
    append(meta, span);
  }

  /* One 6px square per slide, fixed to the right edge. motion.js moves the
     is-active class; the href keeps it usable before and without JS. */
  function buildDots(slides) {
    var old = document.querySelector('.rx-dots');
    if (old && old.parentNode) { old.parentNode.removeChild(old); }

    var nav = h('nav', 'rx-dots');
    nav.setAttribute('aria-label', 'Slajdy');

    slides.forEach(function (item, i) {
      var a = h('a', 'rx-dots__dot' + (i === 0 ? ' is-active' : ''));
      a.setAttribute('href', '#s-' + item.id);
      a.setAttribute('aria-label', item.title);
      append(nav, a);
    });

    document.body.appendChild(nav);
  }

  /* hero, the six theses, closing: the order the dots and the counter use */
  function slideIndex(data) {
    var list = [{ id: 'hero', title: plainText(data.hero.title) }];

    (data.sections || []).forEach(function (section) {
      list.push({
        id: section.id,
        title: section.number + ' ' + plainText(section.title)
      });
    });

    list.push({ id: 'closing', title: plainText(data.closing.heading) });
    return list;
  }

  /* ------------------------------------------------------------------ */
  /* public                                                              */
  /* ------------------------------------------------------------------ */

  function build(data) {
    var paper = document.body.classList.contains('rx-page--paper');
    var strip = document.getElementById('strip');
    if (!strip || !data) { return; }

    strip.textContent = '';

    var pending = [];
    var frag = document.createDocumentFragment();

    append(frag, buildHero(data.hero, pending, paper));

    (data.sections || []).forEach(function (section) {
      append(frag, buildSection(section, pending, paper));
    });

    append(frag, buildClosing(data.closing, paper));

    strip.appendChild(frag);

    var slides = slideIndex(data);
    buildSlideCounter(slides.length);
    buildDots(slides);

    if (window.Charts && typeof window.Charts.render === 'function') {
      pending.forEach(function (job) {
        try {
          window.Charts.render(job.el, job.spec);
          if (paper && (job.spec.type === 'bars' || job.spec.type === 'pairedBars')) {
            addAsciiBars(job.el);
          }
        } catch (err) {
          if (window.console) { window.console.error('Charts.render', job.spec.id, err); }
        }
      });
    }
  }

  window.Render = { build: build };

})(window, document);
