/* motion.js - GSAP / ScrollTrigger motion layer for the "Rachunek za tokeny" receipt page.
 *
 * Slide mode: one section = one slide. The print reveal is a per slide timeline
 * played once when the slide snaps in, not a scrub. CSS owns the snapping, this
 * file owns the printing, the counter, the dots, the ticker and the keyboard.
 *
 * Exposes exactly two globals on one object: window.Motion = { init(), refresh() }.
 * Nothing runs at load time; main.js calls Motion.init() after Render.build() and
 * Halftone.init().
 *
 * Depends on (loaded before this file):
 *   - window.gsap, window.ScrollTrigger (cdnjs 3.12.5)
 *   - window.Halftone.setProgress(canvas, p)   (optional, every call is guarded)
 *
 * DOM contract used here (see CONTRACT.md, "Slide mode"):
 *   .rx-section (in DOM order, one per slide), #s-hero, #s-closing,
 *   .rx-print > .rx-slide > (.rx-slide__copy, .rx-slide__data),
 *   .rx-printhead (fixed), .rx-num[data-count][data-decimals][data-suffix],
 *   .rx-big, .rx-total, .rx-hl, .rx-lineitem, .rx-lines li, .rx-callout, .rx-gap,
 *   .rx-band, .rx-thanks, .rx-sources, .rx-stamp, canvas[data-scene],
 *   .rx-ticker__value, span.rx-header__slide, nav.rx-dots > a.rx-dots__dot[href="#s-..."],
 *   section[data-usd], #strip,
 *   .chart, .chart-bars__fill, .chart-stacked__part, .chart-paired__fill,
 *   .chart-hist__bar, .chart-waffle__cell, table.chart-table tbody tr
 * Every query is guarded: a missing hook disables that effect, never the page.
 */
(function () {
  'use strict';

  var CLOSING_ID = 's-closing';
  var HERO_ID = 's-hero';

  /* Slide deck only on a screen that can actually show a whole slide. */
  var DECK_QUERY = '(min-width: 900px) and (min-height: 620px)';
  var SMALL_QUERY = '(max-width: 899px), (max-height: 619px)';

  var KEY_DELAY = 500;          /* a held key advances at most every 500 ms */
  var SLIDE_START = 'top 55%';
  var SLIDE_END = 'bottom 45%';
  var FLOW_START = 'top 85%';   /* small / short viewports, one shot per element */
  var FLOW_NAV_START = 'top 60%';
  var FLOW_NAV_END = 'bottom 40%';

  var mm = null;
  var afterBuild = null;        /* re-checked once ScrollTrigger positions are known */

  /* ---------------------------------------------------------------- helpers */

  var formatters = {};

  function formatNumber(v, decimals) {
    var d = decimals || 0;
    if (!formatters[d]) {
      try {
        formatters[d] = new Intl.NumberFormat('pl-PL', {
          minimumFractionDigits: d,
          maximumFractionDigits: d
        });
      } catch (err) {
        formatters[d] = { format: function (n) { return Number(n).toFixed(d); } };
      }
    }
    return formatters[d].format(v);
  }

  function toNumber(raw) {
    if (raw === null || raw === undefined) return 0;
    var s = String(raw).replace(/\s| /g, '').replace(',', '.');
    var n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }

  function all(selector, root) {
    var scope = root || document;
    if (!scope || typeof scope.querySelectorAll !== 'function') return [];
    return Array.prototype.slice.call(scope.querySelectorAll(selector));
  }

  function one(selector, root) {
    var scope = root || document;
    if (!scope || typeof scope.querySelector !== 'function') return null;
    return scope.querySelector(selector);
  }

  function inClosing(el) {
    return !!(el && el.closest && el.closest('#' + CLOSING_ID));
  }

  function pad2(n) {
    var s = String(n);
    return s.length < 2 ? '0' + s : s;
  }

  function callAll(list) {
    for (var i = 0; i < list.length; i++) {
      if (typeof list[i] === 'function') {
        try { list[i](); } catch (err) { /* one broken cleanup must not block the rest */ }
      }
    }
  }

  /* Reads the count-up metadata a .rx-num element carries. */
  function numMeta(el) {
    var decimals = el.hasAttribute('data-decimals') ? parseInt(el.getAttribute('data-decimals'), 10) : 0;
    if (isNaN(decimals) || decimals < 0) decimals = 0;
    return {
      target: toNumber(el.getAttribute('data-count')),
      decimals: decimals,
      suffix: el.getAttribute('data-suffix') || ''
    };
  }

  /* Builds the { obj, vars } pair for a count-up so it can be used standalone
   * (gsap.to) or inserted at a position inside a timeline (tl.to). The zero is
   * painted in onStart, never at build time, so a number whose tween never runs
   * keeps the final value render.js printed into the DOM. */
  function countSpec(el, target, decimals, suffix, duration) {
    var obj = { v: 0 };
    var inc = decimals ? 1 / Math.pow(10, decimals) : 1;
    function paint() {
      el.textContent = formatNumber(obj.v, decimals) + suffix;
    }
    return {
      obj: obj,
      vars: {
        v: target,
        duration: duration,
        ease: 'power2.out',
        snap: { v: inc },
        onStart: paint,
        onUpdate: paint,
        onComplete: function () {
          el.textContent = formatNumber(target, decimals) + suffix;
        }
      }
    };
  }

  function countTo(el, target, decimals, suffix, duration) {
    var spec = countSpec(el, target, decimals, suffix, duration);
    return gsap.to(spec.obj, spec.vars);
  }

  function setFinalNumber(el) {
    var m = numMeta(el);
    el.textContent = formatNumber(m.target, m.decimals) + m.suffix;
  }

  function setScene(canvas, p) {
    if (!canvas) return;
    if (window.Halftone && typeof window.Halftone.setProgress === 'function') {
      try {
        window.Halftone.setProgress(canvas, p);
      } catch (err) {
        /* a broken scene must never break the scroll */
      }
    }
  }

  /* The sulphur highlighter lives in a CSS pseudo element, and GSAP cannot tween
   * pseudo elements. So we tween a plain proxy and push the value into the custom
   * property --hl (CSS: background-size: calc(var(--hl) * 100%) 100%) and, as a
   * fallback for stylesheets that ignore the var, straight into inline
   * background-size. Both carry the same value, so they never disagree. */
  function paintHighlight(el, v) {
    el.style.setProperty('--hl', String(v));
    el.style.backgroundSize = (v * 100) + '% 100%';
  }

  function clearHighlight(el) {
    el.style.removeProperty('--hl');
    el.style.removeProperty('background-size');
  }

  function setClip(print, p) {
    /* p = 0 fully clipped, p = 1 fully printed */
    var bottom = (1 - p) * 100;
    print.style.clipPath = 'inset(0 0 ' + bottom.toFixed(3) + '% 0)';
  }

  function scrollToSection(section, behavior) {
    if (!section || typeof section.scrollIntoView !== 'function') return;
    try {
      section.scrollIntoView({ behavior: behavior, block: 'start' });
    } catch (err) {
      section.scrollIntoView(true);
    }
  }

  function sectionList() {
    return all('.rx-section');
  }

  function heroIndex(sections) {
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].id === HERO_ID) return i;
    }
    return -1;
  }

  /* --------------------------------------------------------- the printhead */

  /* The fixed ink line that follows the printing edge. Shared by every slide;
   * a small use counter keeps it visible while at least one slide prints. */
  function createPrinthead(enabled) {
    var head = enabled ? one('.rx-printhead') : null;
    if (!head) {
      return {
        move: function () {},
        use: function () {},
        cleanup: function () {
          var el = one('.rx-printhead');
          if (el) gsap.set(el, { opacity: 0 });
        }
      };
    }

    var setY = gsap.quickSetter(head, 'y', 'px');
    var users = 0;
    var shown = null;

    gsap.set(head, { y: -20, opacity: 0 });

    function show(visible) {
      if (shown === visible) return;
      shown = visible;
      gsap.to(head, { opacity: visible ? 1 : 0, duration: 0.18, ease: 'none', overwrite: true });
    }

    return {
      move: function (y) { setY(y); },
      use: function (on) {
        users = on ? users + 1 : users - 1;
        if (users < 0) users = 0;
        show(users > 0);
      },
      cleanup: function () {
        gsap.killTweensOf(head);
        head.style.removeProperty('transform');
        head.style.removeProperty('opacity');
      }
    };
  }

  /* ---------------------------------------------------------- sticky ticker */

  function createTicker(animate) {
    var ticker = one('.rx-ticker__value');
    if (!ticker) {
      return { add: function () {}, set: function () {}, cleanup: function () {} };
    }

    var state = { total: 0, shown: 0 };
    var tween = null;
    var pulseTimer = null;

    function paint() {
      ticker.textContent = formatNumber(Math.round(state.shown), 0) + ' USD';
    }

    function pulse() {
      ticker.classList.add('is-ticking');
      if (pulseTimer) clearTimeout(pulseTimer);
      pulseTimer = setTimeout(function () {
        pulseTimer = null;
        ticker.classList.remove('is-ticking');
      }, 300);
    }

    function setTotal(next, silent) {
      var value = Math.round(next * 100) / 100;
      if (value < 0) value = 0;
      if (value === state.total && !silent) return;
      state.total = value;
      ticker.setAttribute('data-total', String(value));
      if (tween) { tween.kill(); tween = null; }
      if (!animate || silent) {
        state.shown = value;
        paint();
        if (!silent) pulse();
        return;
      }
      pulse();
      tween = gsap.to(state, {
        shown: value,
        duration: 0.6,
        ease: 'power2.out',
        snap: { shown: 1 },
        onUpdate: paint,
        onComplete: paint
      });
    }

    setTotal(0, true);

    return {
      add: function (delta) { setTotal(state.total + delta); },
      set: function (value, silent) { setTotal(value, silent); },
      cleanup: function () {
        if (tween) { tween.kill(); tween = null; }
        if (pulseTimer) { clearTimeout(pulseTimer); pulseTimer = null; }
        ticker.classList.remove('is-ticking');
      }
    };
  }

  /* ------------------------------------------- slide counter, dots, keyboard */

  function createNav(sections, reduced) {
    var label = one('.rx-header__slide');
    var dots = all('.rx-dots__dot');
    var count = sections.length;
    var behavior = reduced ? 'auto' : 'smooth';
    var index = -1;
    var lastKey = 0;

    var byId = {};
    dots.forEach(function (dot) {
      var href = dot.getAttribute('href') || '';
      if (href.charAt(0) === '#') byId[href.slice(1)] = dot;
    });

    var dotFor = sections.map(function (section, i) {
      return byId[section.id] || dots[i] || null;
    });

    function setIndex(i) {
      if (!count) return;
      if (i < 0) i = 0;
      if (i > count - 1) i = count - 1;
      if (i === index) return;
      index = i;
      if (label) label.textContent = pad2(i + 1) + ' / ' + pad2(count);
      for (var d = 0; d < dotFor.length; d++) {
        if (!dotFor[d]) continue;
        if (d === i) dotFor[d].classList.add('is-active');
        else dotFor[d].classList.remove('is-active');
      }
    }

    function goTo(i) {
      if (!count) return;
      if (i < 0) i = 0;
      if (i > count - 1) i = count - 1;
      scrollToSection(sections[i], behavior);
      setIndex(i);
    }

    /* Dots are real anchors so they work without JS; here we take over so the
     * URL hash does not fight the CSS snap. */
    function onDotClick(event) {
      var anchor = event.currentTarget;
      var href = anchor ? anchor.getAttribute('href') || '' : '';
      if (href.charAt(0) !== '#') return;
      var target = document.getElementById(href.slice(1));
      if (!target) return;
      event.preventDefault();
      scrollToSection(target, behavior);
      for (var i = 0; i < sections.length; i++) {
        if (sections[i] === target) { setIndex(i); break; }
      }
    }

    function isTypingTarget(node) {
      if (!node || node.nodeType !== 1) return false;
      if (node.isContentEditable) return true;
      var tag = (node.tagName || '').toLowerCase();
      return tag === 'input' || tag === 'textarea' || tag === 'select' || tag === 'button';
    }

    function onKeyDown(event) {
      if (event.defaultPrevented) return;
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (isTypingTarget(event.target)) return;

      var key = event.key;
      var isSpace = key === ' ' || key === 'Spacebar' || key === 'Space';
      if (event.shiftKey && !isSpace) return;

      var step = 0;
      var absolute = -1;

      if (key === 'ArrowDown' || key === 'PageDown') step = 1;
      else if (key === 'ArrowUp' || key === 'PageUp') step = -1;
      else if (isSpace) step = event.shiftKey ? -1 : 1;
      else if (key === 'Home') absolute = 0;
      else if (key === 'End') absolute = count - 1;
      else return;

      event.preventDefault();

      var now = Date.now();
      if (now - lastKey < KEY_DELAY) return;
      lastKey = now;

      if (absolute >= 0) goTo(absolute);
      else goTo((index < 0 ? 0 : index) + step);
    }

    dots.forEach(function (dot) { dot.addEventListener('click', onDotClick); });
    window.addEventListener('keydown', onKeyDown);

    setIndex(0);

    return {
      setIndex: setIndex,
      goTo: goTo,
      cleanup: function () {
        window.removeEventListener('keydown', onKeyDown);
        dots.forEach(function (dot) {
          dot.removeEventListener('click', onDotClick);
          dot.classList.remove('is-active');
        });
      }
    };
  }

  /* -------------------------------------------------- per section plumbing */

  /* One trigger per section drives everything that must stay in sync: the slide
   * counter, the dots, the running total and (in deck mode) the slide timeline. */
  function wireSections(sections, nav, ticker, opts) {
    var triggers = [];

    sections.forEach(function (section, i) {
      var usd = toNumber(section.getAttribute('data-usd'));
      var isHero = section.id === HERO_ID;

      triggers.push(ScrollTrigger.create({
        trigger: section,
        start: opts.start,
        end: opts.end,
        onEnter: function () {
          nav.setIndex(i);
          if (usd) ticker.add(usd);
          if (opts.onEnter) opts.onEnter(i);
        },
        onEnterBack: function () {
          nav.setIndex(i);
          if (isHero) ticker.set(0);
          if (opts.onEnter) opts.onEnter(i);
        },
        onLeaveBack: function () {
          nav.setIndex(i - 1);
          if (usd) ticker.add(-usd);
        }
      }));
    });

    return triggers;
  }

  /* Runs once ScrollTrigger knows the real positions: the slide that is already
   * on screen at load must print itself, and the running total must match the
   * scroll position even after a reload halfway down the deck. */
  function makeAfterBuild(sections, triggers, nav, ticker, play) {
    return function () {
      var total = 0;
      var i;

      for (i = 0; i < triggers.length; i++) {
        var st = triggers[i];
        if (!st) continue;
        if (st.progress > 0) total += toNumber(sections[i].getAttribute('data-usd'));
        if (st.isActive) {
          nav.setIndex(i);
          if (play) play(i);
        }
      }

      /* Safety net: the hero is in view at load, so it must print even if its
       * trigger reported nothing during the first refresh. */
      var hi = heroIndex(sections);
      if (hi >= 0 && (!triggers[hi] || !triggers[hi].isActive) && window.scrollY < 10) {
        nav.setIndex(hi);
        if (play) play(hi);
      }

      ticker.set(total, true);
    };
  }

  /* ------------------------------------------------------- slide timelines */

  /* One paused timeline per slide, played once when the slide snaps in.
   * Initial states are applied in prime(), which runs on the first play, so a
   * slide whose timeline never runs still renders complete and readable. */
  function buildSlideTimeline(section, printhead) {
    var print = one('.rx-print', section);
    if (!print) return null;

    var canvas = one('canvas[data-scene]', section);
    var isHero = section.id === HERO_ID;

    var lineitems = all('.rx-lineitem', section);
    if (isHero) lineitems = lineitems.concat(all('.rx-lines li', section));

    var nums = all('.rx-num[data-count]', section);
    var callouts = all('.rx-callout', section);
    var highlights = all('.rx-hl', section);
    var gaps = all('.rx-gap', section);

    var fills = all('.chart-bars__fill, .chart-stacked__part, .chart-paired__fill', section);
    var histBars = all('.chart-hist__bar', section);
    var cells = all('.chart-waffle__cell', section);
    var rows = all('table.chart-table tbody tr', section);

    gsap.set(print, { clipPath: 'inset(0 0 100% 0)' });
    setScene(canvas, 0);

    var played = false;
    var tl = gsap.timeline({ paused: true, defaults: { ease: 'power2.out' } });

    function prime() {
      if (lineitems.length) gsap.set(lineitems, { x: -8, opacity: 0 });
      if (callouts.length) gsap.set(callouts, { opacity: 0, y: 6 });
      if (gaps.length) gsap.set(gaps, { opacity: 0 });
      if (fills.length) gsap.set(fills, { scaleX: 0, transformOrigin: 'left center' });
      if (histBars.length) gsap.set(histBars, { scaleY: 0, transformOrigin: 'center bottom' });
      if (cells.length) gsap.set(cells, { opacity: 0, scale: 0.4, transformOrigin: 'center center' });
      if (rows.length) gsap.set(rows, { opacity: 0, y: 6 });
      highlights.forEach(function (el) { paintHighlight(el, 0); });
      print.style.willChange = 'clip-path';
    }

    /* 1. the paper prints: clip-path wipe, printhead on the edge, halftone p */
    var prog = { p: 0 };
    tl.to(prog, {
      p: 1,
      duration: 1,
      ease: 'power1.inOut',
      onStart: function () { printhead.use(true); },
      onUpdate: function () {
        var p = prog.p;
        setClip(print, p);
        var rect = print.getBoundingClientRect();
        printhead.move(rect.top + rect.height * p);
        setScene(canvas, p);
      },
      onComplete: function () {
        setClip(print, 1);
        setScene(canvas, 1);
        printhead.use(false);
        print.style.willChange = 'auto';
      }
    }, 0);

    /* 2. the line item slides in */
    if (lineitems.length) {
      tl.to(lineitems, {
        x: 0,
        opacity: 1,
        duration: 0.4,
        stagger: lineitems.length > 1 ? 0.05 : 0,
        clearProps: 'transform,opacity'
      }, 0.25);
    }

    /* 3. the numbers count up */
    nums.forEach(function (el) {
      var m = numMeta(el);
      var big = !!(el.closest('.rx-big') || el.closest('.rx-total') || el.classList.contains('rx-num--big'));
      var spec = countSpec(el, m.target, m.decimals, m.suffix, big ? 1.6 : 1.2);
      tl.to(spec.obj, spec.vars, 0.45);
      if (big) {
        tl.fromTo(el,
          { scale: 0.96 },
          { scale: 1, duration: 0.9, ease: 'back.out(2)', immediateRender: false, clearProps: 'transform' },
          0.45
        );
      }
    });

    /* 4. the charts grow in */
    if (fills.length) {
      tl.to(fills, {
        scaleX: 1, duration: 0.9, ease: 'expo.out', stagger: 0.05, clearProps: 'transform'
      }, 0.6);
    }
    if (histBars.length) {
      tl.to(histBars, {
        scaleY: 1, duration: 0.9, ease: 'expo.out', stagger: 0.08, clearProps: 'transform'
      }, 0.6);
    }
    if (cells.length) {
      tl.to(cells, {
        opacity: 1,
        scale: 1,
        duration: 0.4,
        stagger: { each: 0.004, grid: 'auto', from: 'start' },
        clearProps: 'transform,opacity'
      }, 0.6);
    }
    if (rows.length) {
      tl.to(rows, {
        opacity: 1, y: 0, duration: 0.4, stagger: 0.04, clearProps: 'transform,opacity'
      }, 0.6);
    }

    /* 5. callouts, highlighter sweep, data gap stamp plus the ink jolt */
    if (callouts.length) {
      tl.to(callouts, {
        opacity: 1, y: 0, duration: 0.5, stagger: 0.08, clearProps: 'transform,opacity'
      }, 0.9);
    }

    highlights.forEach(function (el) {
      var hl = { v: 0 };
      tl.to(hl, {
        v: 1,
        duration: 0.6,
        onUpdate: function () { paintHighlight(el, hl.v); },
        onComplete: function () { paintHighlight(el, 1); }
      }, 0.9);
    });

    gaps.forEach(function (el) {
      tl.fromTo(el,
        { scale: 1.6, opacity: 0, rotate: -14 },
        { scale: 1, opacity: 1, rotate: -6, duration: 0.5, ease: 'back.out(3)', immediateRender: false },
        0.9
      );
      tl.fromTo(print,
        { y: -2 },
        { y: 0, duration: 0.08, ease: 'power2.out', immediateRender: false },
        0.9
      );
    });

    function play() {
      if (played) return;
      played = true;
      prime();
      tl.play(0);
    }

    function cleanup() {
      tl.kill();
      print.style.removeProperty('clip-path');
      print.style.removeProperty('will-change');
      var touched = lineitems
        .concat(callouts, gaps, fills, histBars, cells, rows)
        .concat([print]);
      if (touched.length) gsap.set(touched, { clearProps: 'all' });
      nums.forEach(setFinalNumber);
      highlights.forEach(clearHighlight);
      setScene(canvas, 1);
    }

    return { play: play, cleanup: cleanup };
  }

  /* ----------------------------------------------------------- the finale */

  /* One paused timeline, about 4 s long. It owns everything inside #s-closing:
   * the ten summary lines, their count-ups, the total slam plus screen shake,
   * the NIEZAPLACONE stamp, the sulphur band, the barcode print with its
   * particle burst, and the closing credits. The caller decides when to play. */
  function buildFinale() {
    var closing = document.getElementById(CLOSING_ID);
    if (!closing) return null;

    var print = one('.rx-print', closing);
    if (print) gsap.set(print, { clipPath: 'inset(0 0 0% 0)' });

    var strip = document.getElementById('strip');
    var lines = all('.rx-lines li', closing);
    var total = one('.rx-total', closing);
    var totalNum = total ? one('.rx-num[data-count]', total) : null;
    var stamp = one('.rx-gap', closing);
    var band = one('.rx-band', closing) || one('.rx-band');
    var canvas = one('canvas[data-scene="barcode"]', closing) || one('canvas[data-scene]', closing);
    var thanks = one('.rx-thanks', closing);
    var sources = one('.rx-sources', closing);

    var STAGGER = 0.07;
    var BAND_AT = 1.2;
    var BARCODE_AT = 1.2;
    var SLAM_AT = 1.45;
    var STAMP_AT = 1.95;
    var CREDITS_AT = 3.0;

    var played = false;
    var tl = gsap.timeline({ paused: true, defaults: { ease: 'power2.out' } });

    setScene(canvas, 0);

    /* 1. the ten lines print, dot matrix style. These states render at build
     * time on purpose: the closing print is never clipped, so its content must
     * already be hidden before the finale plays. cleanup() clears them again. */
    if (lines.length) {
      tl.from(lines, {
        opacity: 0,
        y: 4,
        duration: 0.35,
        stagger: STAGGER
      }, 0);

      lines.forEach(function (li, i) {
        var num = one('.rx-num[data-count]', li);
        if (!num) return;
        var m = numMeta(num);
        var spec = countSpec(num, m.target, m.decimals, m.suffix, 0.5);
        tl.to(spec.obj, spec.vars, i * STAGGER);
      });
    }

    /* 2. the sulphur band floods up from the bottom, just before the slam */
    if (band) {
      tl.fromTo(band,
        { scaleY: 0, transformOrigin: 'center bottom' },
        { scaleY: 1, duration: 0.8, ease: 'power3.out' },
        BAND_AT
      );
    }

    /* 3. the barcode prints; the scene fires its particle burst around p 0.6..1 */
    if (canvas) {
      var proxy = { p: 0 };
      tl.to(proxy, {
        p: 1,
        duration: 1.6,
        ease: 'none',
        onUpdate: function () { setScene(canvas, proxy.p); },
        onComplete: function () { setScene(canvas, 1); }
      }, BARCODE_AT);
    }

    /* 4. DO ZAPLATY slams in, the paper jolts, the screen shakes */
    if (total) {
      tl.fromTo(total,
        { scale: 1.25, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.5, ease: 'expo.out' },
        SLAM_AT
      );
    }
    if (totalNum) {
      var tm = numMeta(totalNum);
      var totalSpec = countSpec(totalNum, tm.target, tm.decimals, tm.suffix, 1);
      tl.to(totalSpec.obj, totalSpec.vars, SLAM_AT);
    }
    if (strip) {
      tl.to(strip, {
        keyframes: [
          { x: -4, duration: 0.05 },
          { x: 4, duration: 0.06 },
          { x: -3, duration: 0.06 },
          { x: 3, duration: 0.06 },
          { x: -1, duration: 0.06 },
          { x: 0, duration: 0.06 }
        ],
        ease: 'none'
      }, SLAM_AT);
      /* immediateRender: false so the strip is not nudged up from page load */
      tl.fromTo(strip,
        { y: -2 },
        { y: 0, duration: 0.2, ease: 'power2.out', immediateRender: false },
        SLAM_AT
      );
    }

    /* 5. the red stamp thuds onto the total, bigger than the in-page ones */
    if (stamp) {
      tl.fromTo(stamp,
        { scale: 2.2, opacity: 0, rotate: -14 },
        { scale: 1, opacity: 1, rotate: -6, duration: 0.5, ease: 'back.out(2)' },
        STAMP_AT
      );
      if (strip) {
        tl.fromTo(strip,
          { y: -2 },
          { y: 0, duration: 0.12, ease: 'power2.out', immediateRender: false },
          STAMP_AT + 0.1
        );
      }
    }

    /* 6. credits */
    var credits = [];
    if (thanks) credits.push(thanks);
    if (sources) credits.push(sources);
    if (credits.length) {
      tl.from(credits, {
        opacity: 0,
        y: 6,
        duration: 0.6,
        stagger: 0.15
      }, CREDITS_AT);
    }

    return {
      play: function () {
        if (played) return;
        played = true;
        tl.play(0);
      },
      cleanup: function () {
        tl.kill();
        var touched = lines.concat(credits);
        if (total) touched.push(total);
        if (stamp) touched.push(stamp);
        if (band) touched.push(band);
        if (strip) touched.push(strip);
        if (print) touched.push(print);
        if (touched.length) gsap.set(touched, { clearProps: 'all' });
        all('.rx-num[data-count]', closing).forEach(setFinalNumber);
        setScene(canvas, 1);
      }
    };
  }

  /* --------------------------------------------------- hero mouse parallax */

  function buildHeroParallax() {
    var hero = document.getElementById(HERO_ID);
    var strip = document.getElementById('strip');
    if (!hero) return null;
    var figure = one('.rx-stamp', hero);
    if (!figure && !strip) return null;

    var xTo = figure ? gsap.quickTo(figure, 'x', { duration: 0.6, ease: 'power3' }) : null;
    var yTo = figure ? gsap.quickTo(figure, 'y', { duration: 0.6, ease: 'power3' }) : null;

    var shadow = { v: 0 };
    var shadowTo = strip
      ? gsap.quickTo(shadow, 'v', {
          duration: 0.8,
          ease: 'power3',
          onUpdate: function () {
            strip.style.setProperty('--shadow-x', shadow.v.toFixed(2) + 'px');
          }
        })
      : null;

    function onMove(event) {
      var rect = hero.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      var nx = (event.clientX - rect.left) / rect.width - 0.5;   /* -0.5 .. 0.5 */
      var ny = (event.clientY - rect.top) / rect.height - 0.5;
      if (xTo) xTo(nx * 12);   /* up to 6 px each way */
      if (yTo) yTo(ny * 12);
      if (shadowTo) shadowTo(nx * -8);
    }

    function onLeave() {
      if (xTo) xTo(0);
      if (yTo) yTo(0);
      if (shadowTo) shadowTo(0);
    }

    hero.addEventListener('mousemove', onMove);
    hero.addEventListener('mouseleave', onLeave);

    return function cleanup() {
      hero.removeEventListener('mousemove', onMove);
      hero.removeEventListener('mouseleave', onLeave);
      if (figure) gsap.set(figure, { clearProps: 'transform' });
      if (strip) strip.style.removeProperty('--shadow-x');
    };
  }

  /* ------------------------------------------- small viewport, one shot mode */

  function buildFlowPrint(sections, printhead) {
    var cleanups = [];

    sections.forEach(function (section) {
      if (section.id === CLOSING_ID) return;
      var print = one('.rx-print', section);
      if (!print) return;
      var canvas = one('canvas[data-scene]', section);

      gsap.set(print, { clipPath: 'inset(0 0 100% 0)' });
      setScene(canvas, 0);

      var prog = { p: 0 };
      var tween = null;

      ScrollTrigger.create({
        trigger: section,
        start: FLOW_START,
        once: true,
        onEnter: function () {
          print.style.willChange = 'clip-path';
          printhead.use(true);
          tween = gsap.to(prog, {
            p: 1,
            duration: 0.8,
            ease: 'power1.inOut',
            onUpdate: function () {
              setClip(print, prog.p);
              var rect = print.getBoundingClientRect();
              printhead.move(rect.top + rect.height * prog.p);
              setScene(canvas, prog.p);
            },
            onComplete: function () {
              setClip(print, 1);
              setScene(canvas, 1);
              printhead.use(false);
              print.style.willChange = 'auto';
            }
          });
        }
      });

      cleanups.push(function () {
        if (tween) tween.kill();
        print.style.removeProperty('clip-path');
        print.style.removeProperty('will-change');
        setScene(canvas, 1);
      });
    });

    return function () { callAll(cleanups); };
  }

  function buildFlowCountUps() {
    all('.rx-num[data-count]').forEach(function (el) {
      if (inClosing(el)) return; /* the finale drives the closing numbers */
      var m = numMeta(el);
      var big = !!(el.closest('.rx-big') || el.closest('.rx-total') || el.classList.contains('rx-num--big'));

      ScrollTrigger.create({
        trigger: el,
        start: 'top 80%',
        once: true,
        onEnter: function () {
          countTo(el, m.target, m.decimals, m.suffix, big ? 1.6 : 1.2);
          if (big) {
            gsap.fromTo(el,
              { scale: 0.96 },
              { scale: 1, duration: 0.9, ease: 'back.out(2)', clearProps: 'transform' }
            );
          }
        }
      });
    });
  }

  /* Initial states are set inside onEnter (never at build time) so that a chart
   * whose trigger never fires still renders complete and readable. */
  function animateChart(root) {
    var fills = all('.chart-bars__fill, .chart-stacked__part, .chart-paired__fill', root);
    if (fills.length) {
      gsap.set(fills, { scaleX: 0, transformOrigin: 'left center' });
      gsap.to(fills, {
        scaleX: 1, duration: 0.9, ease: 'expo.out', stagger: 0.05, clearProps: 'transform'
      });
    }

    var bars = all('.chart-hist__bar', root);
    if (bars.length) {
      gsap.set(bars, { scaleY: 0, transformOrigin: 'center bottom' });
      gsap.to(bars, {
        scaleY: 1, duration: 0.9, ease: 'expo.out', stagger: 0.08, clearProps: 'transform'
      });
    }

    var cells = all('.chart-waffle__cell', root);
    if (cells.length) {
      gsap.set(cells, { opacity: 0, scale: 0.4, transformOrigin: 'center center' });
      gsap.to(cells, {
        opacity: 1,
        scale: 1,
        duration: 0.4,
        ease: 'power2.out',
        stagger: { each: 0.004, grid: 'auto', from: 'start' },
        clearProps: 'transform,opacity'
      });
    }

    var rows = all('table.chart-table tbody tr', root);
    if (rows.length) {
      gsap.set(rows, { opacity: 0, y: 6 });
      gsap.to(rows, {
        opacity: 1, y: 0, duration: 0.4, ease: 'power2.out', stagger: 0.04, clearProps: 'transform,opacity'
      });
    }
  }

  function buildFlowCharts() {
    all('.chart').forEach(function (root) {
      ScrollTrigger.create({
        trigger: root,
        start: FLOW_START,
        once: true,
        onEnter: function () { animateChart(root); }
      });
    });
  }

  function buildFlowHighlights() {
    var touched = all('.rx-hl');
    touched.forEach(function (el) {
      paintHighlight(el, 0);
      ScrollTrigger.create({
        trigger: el,
        start: FLOW_START,
        once: true,
        onEnter: function () {
          var hl = { v: 0 };
          gsap.to(hl, {
            v: 1,
            duration: 0.6,
            ease: 'power2.out',
            onUpdate: function () { paintHighlight(el, hl.v); },
            onComplete: function () { paintHighlight(el, 1); }
          });
        }
      });
    });
    return function () { touched.forEach(clearHighlight); };
  }

  function buildFlowLineItems() {
    all('.rx-lineitem').forEach(function (el) {
      ScrollTrigger.create({
        trigger: el,
        start: FLOW_START,
        once: true,
        onEnter: function () {
          gsap.fromTo(el,
            { x: -8, opacity: 0 },
            { x: 0, opacity: 1, duration: 0.4, ease: 'power2.out', clearProps: 'transform,opacity' }
          );
        }
      });
    });
  }

  function buildFlowGapStamps() {
    all('.rx-gap').forEach(function (el) {
      if (inClosing(el)) return; /* the closing stamp belongs to the finale */
      var section = el.closest('.rx-section');
      var print = section ? one('.rx-print', section) : null;

      ScrollTrigger.create({
        trigger: el,
        start: FLOW_START,
        once: true,
        onEnter: function () {
          gsap.fromTo(el,
            { scale: 1.6, opacity: 0, rotate: -14 },
            { scale: 1, opacity: 1, rotate: -6, duration: 0.5, ease: 'back.out(3)' }
          );
          /* one frame of ink jolt: the paper kicks when the stamp lands */
          if (print) {
            gsap.fromTo(print, { y: -2 }, { y: 0, duration: 0.08, ease: 'power2.out' });
          }
        }
      });
    });
  }

  /* ---------------------------------------------------------- build modes */

  /* Desktop slide deck: one timeline per slide, played once on snap in. */
  function buildDeckMode() {
    var sections = sectionList();
    var nav = createNav(sections, false);
    var ticker = createTicker(true);
    var printhead = createPrinthead(true);
    var cleanups = [nav.cleanup, ticker.cleanup];

    var slides = sections.map(function (section) {
      if (section.id === CLOSING_ID) return buildFinale();
      return buildSlideTimeline(section, printhead);
    });

    slides.forEach(function (slide) {
      if (slide && slide.cleanup) cleanups.push(slide.cleanup);
    });
    /* the printhead is parked last, after every slide timeline is killed */
    cleanups.push(printhead.cleanup);

    function play(i) {
      if (slides[i] && slides[i].play) slides[i].play();
    }

    var triggers = wireSections(sections, nav, ticker, {
      start: SLIDE_START,
      end: SLIDE_END,
      onEnter: play
    });

    afterBuild = makeAfterBuild(sections, triggers, nav, ticker, play);

    var parallax = buildHeroParallax();
    if (parallax) cleanups.push(parallax);

    var raf = window.requestAnimationFrame(function () { runAfterBuild(); });

    return function () {
      window.cancelAnimationFrame(raf);
      afterBuild = null;
      callAll(cleanups);
    };
  }

  /* Small or short viewports: no slide timelines, per element one shots. */
  function buildSmallMode() {
    var sections = sectionList();
    var nav = createNav(sections, false);
    var ticker = createTicker(true);
    var printhead = createPrinthead(true);
    var cleanups = [nav.cleanup, ticker.cleanup];

    cleanups.push(buildFlowPrint(sections, printhead));
    buildFlowCountUps();
    buildFlowCharts();
    cleanups.push(buildFlowHighlights());
    buildFlowLineItems();
    buildFlowGapStamps();
    cleanups.push(printhead.cleanup);

    var finale = buildFinale();
    if (finale) {
      cleanups.push(finale.cleanup);
      var closing = document.getElementById(CLOSING_ID);
      if (closing) {
        ScrollTrigger.create({
          trigger: closing,
          start: 'top 70%',
          once: true,
          onEnter: function () { finale.play(); }
        });
      }
    }

    var triggers = wireSections(sections, nav, ticker, {
      start: FLOW_NAV_START,
      end: FLOW_NAV_END
    });

    afterBuild = makeAfterBuild(sections, triggers, nav, ticker, null);

    var raf = window.requestAnimationFrame(function () { runAfterBuild(); });

    return function () {
      window.cancelAnimationFrame(raf);
      afterBuild = null;
      callAll(cleanups);
    };
  }

  /* prefers-reduced-motion: the page is printed and final, snapping stays on. */
  function buildReducedMode() {
    var sections = sectionList();

    all('.rx-print').forEach(function (print) {
      gsap.set(print, { clipPath: 'inset(0 0 0% 0)' });
      print.style.willChange = 'auto';
    });

    var printhead = one('.rx-printhead');
    if (printhead) gsap.set(printhead, { opacity: 0 });

    all('.rx-num[data-count]').forEach(setFinalNumber);
    all('.rx-hl').forEach(function (el) { paintHighlight(el, 1); });
    all('canvas[data-scene]').forEach(function (canvas) { setScene(canvas, 1); });

    var nav = createNav(sections, true);
    var ticker = createTicker(false);
    var triggers = wireSections(sections, nav, ticker, {
      start: FLOW_NAV_START,
      end: FLOW_NAV_END
    });

    afterBuild = makeAfterBuild(sections, triggers, nav, ticker, null);

    var raf = window.requestAnimationFrame(function () { runAfterBuild(); });

    return function () {
      window.cancelAnimationFrame(raf);
      afterBuild = null;
      nav.cleanup();
      ticker.cleanup();
      all('.rx-hl').forEach(clearHighlight);
    };
  }

  /* ------------------------------------------------------------------ init */

  function runAfterBuild() {
    if (typeof afterBuild !== 'function') return;
    try {
      afterBuild();
    } catch (err) {
      /* never let the deck bookkeeping break the page */
    }
  }

  function init() {
    if (!window.gsap || !window.ScrollTrigger) {
      console.error('[receipt] GSAP or ScrollTrigger missing, motion disabled');
      return;
    }

    gsap.registerPlugin(ScrollTrigger);
    ScrollTrigger.config({ ignoreMobileResize: true });

    if (mm) {
      try { mm.revert(); } catch (err) { /* ignore */ }
    }
    mm = gsap.matchMedia();

    mm.add({
      reduce: '(prefers-reduced-motion: reduce)',
      deck: DECK_QUERY,
      small: SMALL_QUERY
    }, function (context) {
      var c = context.conditions;
      if (c.reduce) return buildReducedMode();
      if (c.deck) return buildDeckMode();
      return buildSmallMode();
    });

    ScrollTrigger.refresh();
    runAfterBuild();
  }

  function refresh() {
    if (window.ScrollTrigger) ScrollTrigger.refresh();
    runAfterBuild();
  }

  window.Motion = { init: init, refresh: refresh };
})();
