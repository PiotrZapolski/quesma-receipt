/* Halftone illustration engine.
 * 1-bit ordered-dither renderer for the receipt "stamps".
 *
 * Every canvas[data-scene] gets a hidden low resolution grayscale buffer.
 * window.Scenes[name](ctx, t, p, w, h) paints grayscale into that buffer,
 * an 8x8 Bayer matrix turns it into ink / paper pixels, and the result is
 * blitted up to the visible canvas with smoothing off.
 *
 * Ink is rgb(23,20,17) (the --ink token). Paper is fully transparent so the
 * receipt grain underneath shows through.
 *
 * Exposes window.Halftone = { init, register, setProgress, start, stop, refresh, scenes }.
 * No modules, nothing runs at load time.
 */
(function (global) {
  'use strict';

  var doc = global.document;

  /* ---------------------------------------------------------------- config */

  var INK = [23, 20, 17];
  var DIV_SMALL = 4;          // low buffer divisor up to 1200 css px
  var DIV_LARGE = 3;          // low buffer divisor above 1200 css px
  var WIDE_AT = 1200;
  var MIN_LOW_W = 80;         // never go below this many buffer columns
  var MAX_LOW_W = 640;        // sanity cap, protects the per pixel loop
  var SOFT_ROWS = 6;          // soft print edge height, in buffer rows
  var WIPE_PAD = 8;           // extra rows so p = 1 clears the last row
  var BURN = 0.35;            // burn-in bias amplitude
  var SCAN_LIFT = 0.06;       // thermal scanline, 6 percent lighter
  var RESIZE_DEBOUNCE = 150;

  /* --------------------------------------------------------- bayer matrix */

  var BAYER8 = (function () {
    var base = [
      0, 32, 8, 40, 2, 34, 10, 42,
      48, 16, 56, 24, 50, 18, 58, 26,
      12, 44, 4, 36, 14, 46, 6, 38,
      60, 28, 52, 20, 62, 30, 54, 22,
      3, 35, 11, 43, 1, 33, 9, 41,
      51, 19, 59, 27, 49, 17, 57, 25,
      15, 47, 7, 39, 13, 45, 5, 37,
      63, 31, 55, 23, 61, 29, 53, 21
    ];
    var m = new Float32Array(64);
    for (var i = 0; i < 64; i++) m[i] = (base[i] + 0.5) / 64;
    return m;
  })();

  /* Pack the ink color once, in the platform byte order. */
  var INK32 = (function () {
    var buf = new ArrayBuffer(4);
    var u8 = new Uint8Array(buf);
    var u32 = new Uint32Array(buf);
    u8[0] = INK[0]; u8[1] = INK[1]; u8[2] = INK[2]; u8[3] = 255;
    return u32[0];
  })();

  /* ----------------------------------------------------------------- state */

  var entries = [];
  var rafId = 0;
  var running = false;
  var stopped = false;          // set by stop(), cleared by start()
  var frame = 0;
  var clock0 = 0;
  var resizeTimer = 0;
  var ro = null;
  var io = null;
  var mq = null;
  var reduced = false;
  var booted = false;

  function reducedMotion() {
    return !!(mq && mq.matches);
  }

  function find(canvas) {
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].canvas === canvas) return entries[i];
    }
    return null;
  }

  function figureOf(canvas) {
    var n = canvas.parentNode;
    while (n && n.nodeType === 1) {
      if (n.tagName === 'FIGURE') return n;
      n = n.parentNode;
    }
    return canvas.parentNode && canvas.parentNode.nodeType === 1 ? canvas.parentNode : null;
  }

  /* ---------------------------------------------------------------- sizing */
  /* Layout is read here only. Never inside the rAF loop. */

  function measure(e) {
    var rect = e.canvas.getBoundingClientRect();
    var cw = Math.round(rect.width);
    var ch = Math.round(rect.height);
    if (cw < 2 || ch < 2) { e.ready = false; return false; }

    var div = e.div || (cw > WIDE_AT ? DIV_LARGE : DIV_SMALL);
    var lw = Math.round(cw / div);
    if (lw < e.minW) lw = e.minW;
    if (lw > MAX_LOW_W) lw = MAX_LOW_W;
    var lh = Math.round(lw * ch / cw);
    if (lh < 8) lh = 8;

    var dpr = Math.min(global.devicePixelRatio || 1, 2);
    var ow = Math.max(1, Math.round(cw * dpr));
    var oh = Math.max(1, Math.round(ch * dpr));

    if (lw !== e.lw || lh !== e.lh) {
      e.lw = lw;
      e.lh = lh;
      e.low.width = lw;
      e.low.height = lh;
      e.img = e.lctx.createImageData(lw, lh);
      e.buf32 = new Uint32Array(e.img.data.buffer);
    }
    if (ow !== e.canvas.width || oh !== e.canvas.height) {
      e.canvas.width = ow;
      e.canvas.height = oh;
    }
    e.octx.imageSmoothingEnabled = false;
    if ('mozImageSmoothingEnabled' in e.octx) e.octx.mozImageSmoothingEnabled = false;
    if ('webkitImageSmoothingEnabled' in e.octx) e.octx.webkitImageSmoothingEnabled = false;
    e.ready = true;
    return true;
  }

  /* ------------------------------------------------------------- rendering */

  function paint(e, t) {
    var lctx = e.lctx;
    var lw = e.lw;
    var lh = e.lh;

    lctx.setTransform(1, 0, 0, 1, 0, 0);
    lctx.globalAlpha = 1;
    lctx.fillStyle = '#fff';
    lctx.fillRect(0, 0, lw, lh);

    var scenes = global.Scenes;
    var scene = scenes && scenes[e.name];
    if (typeof scene === 'function') {
      lctx.save();
      try {
        scene(lctx, t, e.p, lw, lh);
      } catch (err) {
        /* One bad scene must not kill the shared loop. */
        if (global.console && global.console.warn) {
          global.console.warn('Halftone scene "' + e.name + '" failed:', err);
        }
        e.name = '';
      }
      lctx.restore();
    }

    dither(e, lw, lh);

    lctx.setTransform(1, 0, 0, 1, 0, 0);
    lctx.putImageData(e.img, 0, 0);

    var octx = e.octx;
    octx.setTransform(1, 0, 0, 1, 0, 0);
    octx.clearRect(0, 0, e.canvas.width, e.canvas.height);
    octx.imageSmoothingEnabled = false;
    octx.drawImage(e.low, 0, 0, e.canvas.width, e.canvas.height);
  }

  function dither(e, lw, lh) {
    var src = e.lctx.getImageData(0, 0, lw, lh).data;
    var out = e.buf32;
    var wipe = e.p * (lh + WIPE_PAD);
    var bias = e.burn ? (1 - e.p) * BURN : 0;
    var scanOn = e.scanlines;
    var i = 0;
    var o = 0;
    var x, y, row, lift, d, adj, g;

    for (y = 0; y < lh; y++) {
      d = wipe - y;
      if (d <= 0) {
        /* Not printed yet: the whole row stays paper. */
        for (x = 0; x < lw; x++) { out[o++] = 0; i += 4; }
        continue;
      }
      row = (y & 7) << 3;
      lift = (scanOn && (y & 3) === 0) ? SCAN_LIFT : 0;
      /* Soft print edge: the leading rows burn dark, then settle over 6 rows. */
      adj = d < SOFT_ROWS ? (d / SOFT_ROWS - 1) : 0;
      adj += lift;
      for (x = 0; x < lw; x++) {
        g = src[i] * 0.00392156862745098 + adj;
        out[o] = g < BAYER8[row + (x & 7)] + bias ? INK32 : 0;
        o++;
        i += 4;
      }
    }
  }

  function drawOne(e, t) {
    if (!e.ready && !measure(e)) return;
    paint(e, t);
  }

  /* ------------------------------------------------------------- rAF loop */

  function tick(now) {
    rafId = 0;
    if (reduced || stopped) { running = false; return; }

    var t = (now - clock0) / 1000;
    frame++;

    var vis = null;
    var n = 0;
    var i, e;
    for (i = 0; i < entries.length; i++) {
      e = entries[i];
      if (e.visible && e.ready) {
        if (!vis) vis = [];
        vis[n++] = e;
      }
    }
    if (!n) { running = false; return; }

    var multi = n > 1;
    for (i = 0; i < n; i++) {
      e = vis[i];
      /* The first visible scene runs at full rate, extras drop to 30 fps. */
      if (multi && i > 0 && ((frame + i) & 1) === 1) continue;
      paint(e, t);
    }

    rafId = global.requestAnimationFrame(tick);
    running = true;
  }

  function kick() {
    if (running || reduced || stopped || rafId) return;
    var any = false;
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].visible && entries[i].ready) { any = true; break; }
    }
    if (!any) return;
    running = true;
    rafId = global.requestAnimationFrame(tick);
  }

  /* ----------------------------------------------------------- static pass */

  function drawStatic() {
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      if (reduced) e.p = 1;
      if (!e.ready && !measure(e)) continue;
      paint(e, reduced ? 0 : (global.performance ? (global.performance.now() - clock0) / 1000 : 0));
    }
  }

  /* ------------------------------------------------------------- observers */

  function setupObservers() {
    if (global.ResizeObserver && !ro) {
      ro = new global.ResizeObserver(function () {
        if (resizeTimer) global.clearTimeout(resizeTimer);
        resizeTimer = global.setTimeout(function () {
          resizeTimer = 0;
          for (var i = 0; i < entries.length; i++) measure(entries[i]);
          drawStatic();
          kick();
        }, RESIZE_DEBOUNCE);
      });
    }
    if (global.IntersectionObserver && !io) {
      io = new global.IntersectionObserver(function (recs) {
        for (var i = 0; i < recs.length; i++) {
          var e = find(recs[i].target);
          if (e) e.visible = recs[i].isIntersecting;
        }
        kick();
      }, { rootMargin: '200px 0px 200px 0px', threshold: 0 });
    }
  }

  function observe(e) {
    if (ro) { try { ro.observe(e.canvas); } catch (err) { /* ignore */ } }
    if (io) { try { io.observe(e.canvas); } catch (err) { /* ignore */ } }
    else e.visible = true;
  }

  function setupMedia() {
    if (mq || !global.matchMedia) return;
    mq = global.matchMedia('(prefers-reduced-motion: reduce)');
    reduced = mq.matches;
    var onChange = function () {
      reduced = mq.matches;
      if (reduced) {
        if (rafId) global.cancelAnimationFrame(rafId);
        rafId = 0;
        running = false;
        drawStatic();
      } else {
        clock0 = global.performance ? global.performance.now() : Date.now();
        kick();
      }
    };
    if (mq.addEventListener) mq.addEventListener('change', onChange);
    else if (mq.addListener) mq.addListener(onChange);
  }

  /* --------------------------------------------------------------- public */

  function register(canvas, sceneName, opts) {
    if (!canvas || canvas.tagName !== 'CANVAS') return null;
    var e = find(canvas);
    opts = opts || {};
    if (e) {
      if (sceneName) e.name = sceneName;
      if (opts.p != null) e.p = opts.p;
      return e;
    }

    var low, lctx, octx;
    try {
      low = doc.createElement('canvas');
      low.width = MIN_LOW_W;
      low.height = 8;
      lctx = low.getContext('2d', { willReadFrequently: true });
      octx = canvas.getContext('2d');
    } catch (err) {
      lctx = null;
    }
    if (!lctx || !octx) {
      var fig = figureOf(canvas);
      if (fig && fig.classList) fig.classList.add('is-fallback');
      return null;
    }

    e = {
      canvas: canvas,
      name: sceneName || canvas.getAttribute('data-scene') || '',
      low: low,
      lctx: lctx,
      octx: octx,
      img: null,
      buf32: null,
      lw: 0,
      lh: 0,
      /* p defaults to 1 so the stamp is fully printed if motion.js never runs. */
      p: opts.p != null ? opts.p : 1,
      div: opts.div || 0,
      minW: opts.minWidth || MIN_LOW_W,
      burn: opts.burn === false ? false : true,
      scanlines: opts.scanlines === false ? false : true,
      visible: false,
      ready: false
    };
    entries.push(e);

    measure(e);
    observe(e);
    return e;
  }

  function setProgress(canvas, p) {
    var e = find(canvas);
    if (!e) return;
    if (reduced) { e.p = 1; return; }
    p = p < 0 ? 0 : p > 1 ? 1 : p;
    if (e.p === p) return;
    e.p = p;
    if (!running && !stopped && e.visible) kick();
  }

  function start() {
    stopped = false;
    clock0 = clock0 || (global.performance ? global.performance.now() : Date.now());
    if (reduced) { drawStatic(); return; }
    kick();
  }

  function stop() {
    stopped = true;
    if (rafId) global.cancelAnimationFrame(rafId);
    rafId = 0;
    running = false;
  }

  function refresh() {
    for (var i = 0; i < entries.length; i++) measure(entries[i]);
    drawStatic();
    kick();
  }

  function init() {
    if (!doc) return;
    setupMedia();
    setupObservers();

    var list = doc.querySelectorAll('canvas[data-scene]');
    for (var i = 0; i < list.length; i++) {
      register(list[i], list[i].getAttribute('data-scene'), null);
    }

    clock0 = global.performance ? global.performance.now() : Date.now();
    booted = true;

    if (reduced) {
      drawStatic();
      return;
    }
    /* First frame right away so nothing flashes empty, then the loop. */
    drawStatic();
    kick();
  }

  global.Halftone = {
    init: init,
    register: register,
    setProgress: setProgress,
    start: start,
    stop: stop,
    refresh: refresh,
    /* Live registry, exposed for debugging. */
    scenes: entries,
    isReduced: reducedMotion,
    isBooted: function () { return booted; }
  };
})(window);
