/* Halftone scenes.
 *
 * window.Scenes[name](ctx, t, p, w, h) paints GRAYSCALE ONLY into the low
 * resolution buffer of the halftone engine. Black is ink, white is paper,
 * every gray in between becomes a halftone dot ramp after the Bayer pass.
 *
 * Rules kept here on purpose:
 *  - no per pixel JavaScript, only paths, gradients and small rects,
 *  - loops are capped (24 fish, 400 particles, 14 skulls, 6 files),
 *  - every scene must read well at p = 1 and t = 0 (reduced motion frame),
 *  - no text rendering, captions are HTML,
 *  - Canvas 2D only, no colors.
 */
(function (global) {
  'use strict';

  var TAU = Math.PI * 2;
  var PI = Math.PI;
  var sin = Math.sin;
  var cos = Math.cos;

  /* ------------------------------------------------------------- utilities */

  /* Pre built gray strings, so animated grays never allocate per frame. */
  var GRAYS = (function () {
    var a = new Array(33);
    for (var i = 0; i < 33; i++) {
      var v = Math.round(i * 255 / 32);
      a[i] = 'rgb(' + v + ',' + v + ',' + v + ')';
    }
    return a;
  })();

  function gray(v) {
    var i = v <= 0 ? 0 : v >= 1 ? 32 : (v * 32 + 0.5) | 0;
    return GRAYS[i];
  }

  function clamp(v, a, b) {
    return v < a ? a : v > b ? b : v;
  }

  /* Deterministic PRNG so layouts are identical on every frame and reload. */
  function prng(seed) {
    var s = (seed >>> 0) || 1;
    return function () {
      s = (s * 1664525 + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  function px(ctx, x, y, s) {
    ctx.fillRect(Math.round(x), Math.round(y), s, s);
  }

  /* --------------------------------------------------------- primitive: sky */

  /* Vertical ramp over the rect (0,0,w,h). dir 1 = dark on top. */
  function sky(ctx, w, h, dir) {
    var g = ctx.createLinearGradient(0, 0, 0, h);
    if (dir < 0) {
      g.addColorStop(0, gray(1));
      g.addColorStop(0.55, gray(0.88));
      g.addColorStop(1, gray(0.55));
    } else {
      g.addColorStop(0, gray(0.52));
      g.addColorStop(0.45, gray(0.78));
      g.addColorStop(1, gray(0.99));
    }
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }

  /* --------------------------------------------------------- primitive: sun */

  function sun(ctx, cx, cy, r, rays, t) {
    /* Halo: dithers into a ring of halftone dots around the disc. */
    var g = ctx.createRadialGradient(cx, cy, r * 0.85, cx, cy, r * 4.2);
    g.addColorStop(0, gray(0.36));
    g.addColorStop(0.45, gray(0.72));
    g.addColorStop(1, gray(1));
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, cy, r * 4.2, 0, TAU);
    ctx.fill();

    /* Rotating triangular rays. */
    var n = rays || 10;
    var spin = t * 0.09;
    ctx.fillStyle = gray(0.32);
    for (var i = 0; i < n; i++) {
      var a = spin + i * TAU / n;
      var half = 0.055 + 0.02 * ((i & 1) ? 1 : 0);
      var len = r * (2.9 + ((i % 3) * 0.35));
      ctx.beginPath();
      ctx.moveTo(cx + cos(a - half) * r * 1.02, cy + sin(a - half) * r * 1.02);
      ctx.lineTo(cx + cos(a) * len, cy + sin(a) * len);
      ctx.lineTo(cx + cos(a + half) * r * 1.02, cy + sin(a + half) * r * 1.02);
      ctx.closePath();
      ctx.fill();
    }

    /* Solid disc. */
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, TAU);
    ctx.fill();
  }

  /* ------------------------------------------------------- primitive: water */

  function waveY(x, baseY, amp, t, speed) {
    return baseY
      + sin(x * 0.11 + t * 1.05 * speed) * amp
      + sin(x * 0.041 - t * 0.62 * speed) * amp * 0.65;
  }

  /* Pixel stepped sea from baseY down to h. */
  function water(ctx, w, baseY, h, t, speed, dark) {
    if (speed == null) speed = 1;
    var amp = Math.max(1.2, (h - baseY) * 0.09);
    var step = 2;
    var x, y;

    ctx.beginPath();
    ctx.moveTo(0, h);
    ctx.lineTo(0, waveY(0, baseY, amp, t, speed));
    for (x = 0; x <= w; x += step) {
      y = waveY(x, baseY, amp, t, speed);
      ctx.lineTo(x, y);
      ctx.lineTo(x + step, y);
    }
    ctx.lineTo(w, h);
    ctx.closePath();

    var g = ctx.createLinearGradient(0, baseY - amp, 0, h);
    g.addColorStop(0, gray(dark ? 0.42 : 0.58));
    g.addColorStop(0.55, gray(dark ? 0.18 : 0.3));
    g.addColorStop(1, gray(0.02));
    ctx.fillStyle = g;
    ctx.fill();

    /* Three lighter crest lines below the surface. */
    var gap = Math.max(2, (h - baseY) * 0.13);
    ctx.fillStyle = gray(0.92);
    for (var k = 1; k <= 3; k++) {
      var off = k * gap;
      for (x = 0; x < w; x += step) {
        y = waveY(x + k * 9, baseY, amp * (1 - k * 0.12), t, speed) + off;
        if (y > h - 1) continue;
        ctx.fillRect(x, Math.round(y), step, 1);
      }
    }
  }

  /* ------------------------------------------------------- primitive: shark */

  function shark(ctx, x, y, s, flip, rim) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(flip ? -s : s, s);

    ctx.fillStyle = '#000';
    ctx.strokeStyle = gray(1);
    ctx.lineWidth = 0.55;
    ctx.lineJoin = 'round';

    /* Body with tail fork. */
    ctx.beginPath();
    ctx.moveTo(11, 0);
    ctx.quadraticCurveTo(3, -3.4, -6, -2.2);
    ctx.lineTo(-11.5, -5.2);
    ctx.lineTo(-8.6, 0);
    ctx.lineTo(-11.5, 5.2);
    ctx.lineTo(-6, 2.2);
    ctx.quadraticCurveTo(3, 3.4, 11, 0);
    ctx.closePath();
    ctx.fill();
    if (rim) ctx.stroke();

    /* Dorsal fin. */
    ctx.beginPath();
    ctx.moveTo(-0.4, -2.8);
    ctx.lineTo(2.1, -7.6);
    ctx.lineTo(4.4, -2.1);
    ctx.closePath();
    ctx.fill();
    if (rim) ctx.stroke();

    /* Pectoral fin. */
    ctx.beginPath();
    ctx.moveTo(1.4, 1.6);
    ctx.lineTo(-1.8, 6.2);
    ctx.lineTo(3.6, 2.3);
    ctx.closePath();
    ctx.fill();
    if (rim) ctx.stroke();

    /* Gills. */
    ctx.fillStyle = gray(1);
    for (var i = 0; i < 3; i++) ctx.fillRect(2.4 + i * 1.1, -1.4, 0.35, 2.4);

    /* Eye. */
    ctx.beginPath();
    ctx.arc(7.6, -1.0, 0.75, 0, TAU);
    ctx.fill();

    ctx.restore();
  }

  /* -------------------------------------------------------- primitive: fish */

  function fish(ctx, x, y, s, a) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(a);
    ctx.scale(s, s);
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.moveTo(2.6, 0);
    ctx.lineTo(-0.7, -1.2);
    ctx.lineTo(-2.4, 0);
    ctx.lineTo(-0.7, 1.2);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(-2.0, 0);
    ctx.lineTo(-3.6, -1.4);
    ctx.lineTo(-3.6, 1.4);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  /* ------------------------------------------------------- primitive: skull */

  /* Black skull with a white rim, so it reads on paper and on the black pile. */
  function skull(ctx, x, y, s) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);

    ctx.fillStyle = '#000';
    ctx.strokeStyle = gray(1);
    ctx.lineWidth = 0.5;

    /* Jaw. */
    ctx.beginPath();
    ctx.moveTo(-2.7, 1.6);
    ctx.lineTo(2.7, 1.6);
    ctx.lineTo(2.3, 5.2);
    ctx.lineTo(-2.3, 5.2);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    /* Cranium. */
    ctx.beginPath();
    ctx.arc(0, -0.4, 4, 0, TAU);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = gray(1);

    /* Eye sockets. */
    ctx.beginPath();
    ctx.arc(-1.65, -0.5, 1.3, 0, TAU);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(1.65, -0.5, 1.3, 0, TAU);
    ctx.fill();

    /* Nose. */
    ctx.beginPath();
    ctx.moveTo(0, 1.0);
    ctx.lineTo(-0.85, 2.5);
    ctx.lineTo(0.85, 2.5);
    ctx.closePath();
    ctx.fill();

    /* Four teeth gaps. */
    for (var i = 0; i < 4; i++) ctx.fillRect(-1.95 + i * 1.3, 2.7, 0.4, 2.4);

    ctx.restore();
  }

  /* -------------------------------------------------------- primitive: palm */

  function palm(ctx, x, y, s, lean) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = '#000';
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1.15;
    ctx.lineCap = 'round';

    var tx = lean * 4.2;
    var ty = -13;

    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(lean * 1.1, -7, tx, ty);
    ctx.stroke();

    for (var i = 0; i < 6; i++) {
      var a = -PI * 0.95 + i * (PI * 0.9 / 5);
      var L = 6.4 + (i % 2) * 1.3;
      var ex = tx + cos(a) * L;
      var ey = ty + sin(a) * L * 0.55 + 2.8;
      ctx.beginPath();
      ctx.moveTo(tx, ty);
      ctx.quadraticCurveTo(tx + cos(a) * L * 0.6, ty + sin(a) * L * 0.5 - 1.4, ex, ey);
      ctx.quadraticCurveTo(tx + cos(a) * L * 0.5, ty + sin(a) * L * 0.45 + 1.7, tx, ty);
      ctx.fill();
    }

    ctx.restore();
  }

  /* ---------------------------------------------------- primitive: umbrella */

  function umbrella(ctx, x, y, s) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = '#000';

    ctx.fillRect(-0.45, -9.2, 0.9, 9.2);

    ctx.beginPath();
    ctx.moveTo(-8, -9.2);
    for (var i = 0; i < 4; i++) {
      var x0 = -8 + i * 4;
      ctx.quadraticCurveTo(x0 + 2, -7.4, x0 + 4, -9.2);
    }
    ctx.quadraticCurveTo(0, -16.2, -8, -9.2);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }

  /* ----------------------------------------------------- primitive: lounger */

  function lounger(ctx, x, y, s, flip) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(flip ? -s : s, s);
    ctx.fillStyle = '#000';
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1.1;
    ctx.lineCap = 'round';

    /* Deck chair. */
    ctx.beginPath();
    ctx.moveTo(-5.2, 0);
    ctx.lineTo(-1, 0);
    ctx.lineTo(3.2, -3.6);
    ctx.lineTo(1.7, -4.6);
    ctx.lineTo(-5.2, -1);
    ctx.closePath();
    ctx.fill();

    /* Body and head. */
    ctx.beginPath();
    ctx.moveTo(-4.6, -1.8);
    ctx.lineTo(-0.6, -2.1);
    ctx.lineTo(2.3, -4.6);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(3.2, -5.5, 1.05, 0, TAU);
    ctx.fill();

    ctx.restore();
  }

  /* ------------------------------------------------------ primitive: surfer */

  function surfer(ctx, x, y, s, t) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = '#000';
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 0.95;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    var lean = sin(t * 1.7 + x * 0.09) * 0.35;

    /* Board. */
    ctx.beginPath();
    ctx.moveTo(-5.2, 1.3);
    ctx.quadraticCurveTo(0, -0.7, 5.6, 0.3);
    ctx.quadraticCurveTo(0, 2.6, -5.2, 1.3);
    ctx.closePath();
    ctx.fill();

    /* Legs, torso, arms. */
    ctx.beginPath();
    ctx.moveTo(-1.7, 0.7);
    ctx.lineTo(-0.4, -1.7);
    ctx.lineTo(1.5, 0.5);
    ctx.moveTo(-0.4, -1.7);
    ctx.lineTo(0.2 + lean, -4.3);
    ctx.moveTo(0.2 + lean, -3.7);
    ctx.lineTo(-2.4, -4.9);
    ctx.moveTo(0.2 + lean, -3.7);
    ctx.lineTo(2.6, -4.6);
    ctx.stroke();

    /* Head. */
    ctx.beginPath();
    ctx.arc(0.4 + lean, -5.2, 0.95, 0, TAU);
    ctx.fill();

    ctx.restore();
  }

  /* -------------------------------------------------------- primitive: boat */

  function boat(ctx, x, y, s) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.moveTo(-3.2, 0);
    ctx.lineTo(3.2, 0);
    ctx.lineTo(2.2, 1.7);
    ctx.lineTo(-2.2, 1.7);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(-0.2, -0.2);
    ctx.lineTo(-0.2, -4.8);
    ctx.lineTo(2.8, -0.2);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  /* ------------------------------------------------------- primitive: vortex */

  function vortexField(ctx, cx, cy, R, t) {
    var rings = 16;
    var segs = 22;
    var step = R / rings;
    var pulse = 0.62 + 0.38 * sin(t * 0.33);

    ctx.lineCap = 'butt';
    ctx.lineWidth = step * 1.25;

    for (var ri = rings; ri >= 1; ri--) {
      var r = ri * step;
      var rr = r / R;
      /* Inner rings spin faster, which reads as the pull toward the center. */
      var twist = t * 0.5 + (1 - rr) * 3.4;
      for (var si = 0; si < segs; si++) {
        var a0 = si / segs * TAU + twist;
        var a1 = (si + 1) / segs * TAU + twist + 0.01;
        var th = (si + 0.5) / segs * TAU;
        var v = (sin(th * 3 + r * 0.25) + 1) / 2;
        var g = (0.06 + 0.94 * rr) * (0.5 + pulse * (v - 0.5) * 1.7);
        ctx.strokeStyle = gray(clamp(g, 0, 1));
        ctx.beginPath();
        ctx.arc(cx, cy, r, a0, a1);
        ctx.stroke();
      }
    }

    /* Dark eye of the spiral. */
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(cx, cy, step * 1.1, 0, TAU);
    ctx.fill();
  }

  /* --------------------------------------------------------- primitive: file */

  function fileIcon(ctx, x, y, s, rot) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.scale(s, s);

    ctx.fillStyle = gray(1);
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 0.9;
    ctx.lineJoin = 'miter';

    ctx.beginPath();
    ctx.moveTo(-3, -4);
    ctx.lineTo(1.2, -4);
    ctx.lineTo(3, -2.2);
    ctx.lineTo(3, 4);
    ctx.lineTo(-3, 4);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    /* Folded corner. */
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.moveTo(1.2, -4);
    ctx.lineTo(3, -2.2);
    ctx.lineTo(1.2, -2.2);
    ctx.closePath();
    ctx.fill();

    /* Two content lines. */
    ctx.fillRect(-1.8, -0.8, 3.6, 0.7);
    ctx.fillRect(-1.8, 1.0, 3.6, 0.7);

    ctx.restore();
  }

  /* -------------------------------------------------------- primitive: clock */

  function hand(ctx, cx, cy, len, a, sz) {
    var steps = Math.max(3, Math.round(len / Math.max(0.8, sz * 0.75)));
    var s = Math.max(1, Math.round(sz));
    for (var i = 1; i <= steps; i++) {
      var f = i / steps;
      px(ctx, cx + cos(a) * len * f - sz / 2, cy + sin(a) * len * f - sz / 2, s);
    }
  }

  function clock(ctx, cx, cy, r, t) {
    ctx.fillStyle = gray(1);
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, TAU);
    ctx.fill();

    var d = Math.max(1.4, r * 0.15);
    ctx.fillStyle = '#000';

    var n = 36;
    for (var i = 0; i < n; i++) {
      var a = i / n * TAU;
      var big = (i % 3) === 0;
      var sz = Math.max(1, Math.round(big ? d : d * 0.6));
      px(ctx, cx + cos(a) * r - sz / 2, cy + sin(a) * r - sz / 2, sz);
    }

    /* One minute turn per 8 seconds, the hour hand crawls. */
    hand(ctx, cx, cy, r * 0.82, t / 8 * TAU - PI / 2, d * 0.6);
    hand(ctx, cx, cy, r * 0.5, t / 96 * TAU - PI / 2, d * 0.85);

    ctx.beginPath();
    ctx.arc(cx, cy, Math.max(1, d * 0.7), 0, TAU);
    ctx.fill();
  }

  /* ------------------------------------------------------- primitive: bars */

  function bars(ctx, x, y, w, h, seed) {
    var r = prng(seed);
    var cx = x;
    var ink = true;
    ctx.fillStyle = '#000';
    while (cx < x + w) {
      var bw = 1 + Math.floor(r() * 4);
      if (cx + bw > x + w) bw = x + w - cx;
      if (bw <= 0) break;
      if (ink) ctx.fillRect(Math.round(cx), Math.round(y), Math.max(1, Math.round(bw)), Math.round(h));
      cx += bw;
      ink = !ink;
    }
  }

  /* Small stepped mound, used as an island / headland. */
  function mound(ctx, cx, baseY, rw, rh) {
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.moveTo(cx - rw, baseY);
    ctx.quadraticCurveTo(cx - rw * 0.35, baseY - rh * 1.9, cx, baseY - rh);
    ctx.quadraticCurveTo(cx + rw * 0.45, baseY - rh * 0.4, cx + rw, baseY);
    ctx.closePath();
    ctx.fill();
  }

  /* ================================================================ scenes */

  /* 1. SUN: the BinaryAudit surface. */
  function sceneSun(ctx, t, p, w, h) {
    var horizon = h * 0.60;

    sky(ctx, w, horizon, 1);
    sun(ctx, w * 0.23, horizon * 0.44, h * 0.15, 12, t);

    water(ctx, w, horizon, h, t, 1, false);

    /* Island with three palms, sitting on the waterline. */
    var ix = w * 0.17;
    mound(ctx, ix, horizon + h * 0.035, w * 0.15, h * 0.07);
    var ps = h * 0.024;
    palm(ctx, ix - w * 0.055, horizon + h * 0.01, ps, -0.5);
    palm(ctx, ix + w * 0.005, horizon - h * 0.005, ps * 1.25, 0.2);
    palm(ctx, ix + w * 0.06, horizon + h * 0.015, ps * 0.9, 0.75);

    /* Two boats drifting right to left. */
    var span = w + 40;
    for (var i = 0; i < 2; i++) {
      var bx = span - (((t * 4.5 + i * span * 0.52) % span)) - 20;
      var by = horizon + h * 0.12 + sin(t * 1.2 + i * 2.1) * h * 0.012;
      boat(ctx, bx, by, h * 0.018 * (1 + i * 0.35));
    }
  }

  /* 2. SHARKS: generated lines sinking under the waterline. */
  function sceneSharks(ctx, t, p, w, h) {
    var line = h * 0.19;

    /* Light strip above the water. */
    var gs = ctx.createLinearGradient(0, 0, 0, line);
    gs.addColorStop(0, gray(1));
    gs.addColorStop(1, gray(0.74));
    ctx.fillStyle = gs;
    ctx.fillRect(0, 0, w, line);

    /* Deep water. */
    var gw = ctx.createLinearGradient(0, line, 0, h);
    gw.addColorStop(0, gray(0.76));
    gw.addColorStop(0.42, gray(0.46));
    gw.addColorStop(1, gray(0.05));
    ctx.fillStyle = gw;
    ctx.fillRect(0, line, w, h - line);

    /* Pixel stepped waterline. */
    var amp = Math.max(1, h * 0.022);
    ctx.fillStyle = '#000';
    for (var x = 0; x < w; x += 2) {
      var y = line + sin(x * 0.13 + t * 0.9) * amp + sin(x * 0.047 - t * 0.5) * amp * 0.6;
      ctx.fillRect(x, Math.round(y), 2, 2);
    }

    /* Faint sinking lines. */
    ctx.fillStyle = gray(0.82);
    var r = prng(31);
    for (var i = 0; i < 9; i++) {
      var lx = Math.round(r() * w);
      var ph = r() * 40;
      for (var k = 0; k < 6; k++) {
        var ly = line + ((t * 7 + ph + k * 11) % (h - line));
        ctx.fillRect(lx, Math.round(ly), 1, 1);
      }
    }

    /* Four sharks drifting at different depths and speeds. */
    var conf = [
      [0.34, 1.00, 9.0, 0, 0.0],
      [0.52, 0.72, 5.5, 0, 1.7],
      [0.44, 0.52, 13.0, 1, 3.1],
      [0.66, 0.38, 3.4, 0, 4.6]
    ];
    var span = w + 60;
    for (var s = 0; s < conf.length; s++) {
      var c = conf[s];
      var sx = ((t * c[2] + c[4] * span * 0.31) % span) - 30;
      if (c[3]) sx = span - sx - 30;
      var sy = h * c[0] + sin(t * 0.8 + c[4]) * h * 0.02;
      shark(ctx, sx, sy, h * 0.055 * c[1], !!c[3], c[0] > 0.5);
    }
  }

  /* 3. SKULLS: the pile builds while the stamp prints. */
  function sceneSkulls(ctx, t, p, w, h) {
    var top = h * 0.50;

    var g = ctx.createLinearGradient(0, 0, 0, top);
    g.addColorStop(0, gray(1));
    g.addColorStop(0.5, gray(0.86));
    g.addColorStop(1, gray(0.26));
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, top);

    ctx.fillStyle = '#000';
    ctx.fillRect(0, top, w, h - top);

    /* Deterministic pile layout, same on every frame. */
    var r = prng(1977);
    var n = Math.max(0, Math.min(14, Math.floor(p * 14)));
    for (var i = 0; i < 14; i++) {
      var left = (i % 2) === 0;
      var k = i >> 1;
      var col = k % 3;
      var row = (k / 3) | 0;
      var s = h * 0.055 * (0.78 + r() * 0.6);
      var jx = r() * w * 0.03;
      var jy = r() * h * 0.035;
      var bx = left ? (w * 0.07 + col * w * 0.072 + jx) : (w * 0.93 - col * w * 0.072 - jx);
      var by = h * 0.93 - row * h * 0.155 - jy;
      if (i >= n) continue;
      /* A few of them breathe. */
      if ((i % 4) === 0) s *= 1 + sin(t * 0.9 + i) * 0.02;
      skull(ctx, bx, by, s);
    }
  }

  /* 4. FISH: subagents streaming around the parent. */
  function sceneFish(ctx, t, p, w, h) {
    var cx = w * 0.5;
    var cy = h * 0.5;

    var g = ctx.createRadialGradient(cx, cy, h * 0.05, cx, cy, w * 0.62);
    g.addColorStop(0, gray(0.88));
    g.addColorStop(0.6, gray(0.64));
    g.addColorStop(1, gray(0.42));
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    /* Faint trailing spiral of dots. */
    ctx.fillStyle = gray(0.95);
    for (var i = 0; i < 64; i++) {
      var f = i / 64;
      var a = f * 11 + t * 0.18;
      var rr = h * 0.09 + f * h * 0.52;
      ctx.fillRect(Math.round(cx + cos(a) * rr * 1.75), Math.round(cy + sin(a) * rr), 1, 1);
    }

    /* Parent. */
    shark(ctx, cx, cy, h * 0.072, false, false);

    /* 24 small fish with boid style sinusoidal offsets. */
    var fs = h * 0.026;
    for (var j = 0; j < 24; j++) {
      var ph = j * (TAU / 24);
      var sp = 0.20 + (j % 3) * 0.055;
      var ang = ph + t * sp;
      var rx = w * 0.20 + (j % 4) * w * 0.052 + sin(t * 0.85 + j * 0.7) * w * 0.024;
      var ry = h * 0.20 + (j % 4) * h * 0.07 + cos(t * 0.65 + j * 0.5) * h * 0.05;
      var fx = cx + cos(ang) * rx;
      var fy = cy + sin(ang) * ry;
      fish(ctx, fx, fy, fs, ang + PI / 2);
    }
  }

  /* 5. VORTEX: files pulled in and spat back out. */
  function sceneVortex(ctx, t, p, w, h) {
    ctx.fillStyle = gray(1);
    ctx.fillRect(0, 0, w, h);

    var cx = w * 0.5;
    var cy = h * 0.5;
    var R = w * 0.62;
    var squash = clamp(h / w * 1.75, 0.35, 1);

    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(1, squash);
    vortexField(ctx, 0, 0, R, t);
    ctx.restore();

    /* Six file icons riding the spiral. */
    for (var i = 0; i < 6; i++) {
      var u = (t * 0.15 + i / 6) % 1;
      var rr = R * 0.78 * (1 - u) + h * 0.05;
      var a = u * 7.2 + i * 1.047;
      var s = h * 0.034 * (0.35 + 0.65 * (1 - u));
      fileIcon(ctx, cx + cos(a) * rr, cy + sin(a) * rr * squash, s, a * 0.6 + u * 2.2);
    }
  }

  /* 6. BEACH: the sun crosses, the clock spins, nothing else happens. */
  function sceneBeach(ctx, t, p, w, h) {
    var skyH = h * 0.54;
    var waterTop = h * 0.76;

    sky(ctx, w, skyH, 1);

    /* Sun on a slow 40 second arc. */
    var u = (t / 40) % 1;
    var sx = w * (0.06 + 0.58 * u);
    var sy = skyH * 0.92 - sin(u * PI) * skyH * 0.72;
    sun(ctx, sx, sy, h * 0.085, 10, t * 0.5);

    /* Beach band. */
    var gb = ctx.createLinearGradient(0, skyH, 0, waterTop);
    gb.addColorStop(0, gray(0.96));
    gb.addColorStop(1, gray(0.78));
    ctx.fillStyle = gb;
    ctx.fillRect(0, skyH, w, waterTop - skyH);

    /* Stepped sand edge. */
    ctx.fillStyle = gray(0.62);
    for (var x = 0; x < w; x += 2) {
      var ey = skyH + sin(x * 0.07) * h * 0.012;
      ctx.fillRect(x, Math.round(ey), 2, 1);
    }

    /* Umbrella and two loungers. */
    var us = h * 0.035;
    umbrella(ctx, w * 0.30, waterTop - h * 0.03, us);
    lounger(ctx, w * 0.20, waterTop - h * 0.03, us * 0.9, false);
    lounger(ctx, w * 0.40, waterTop - h * 0.03, us * 0.9, true);

    /* Calm water in the foreground. */
    water(ctx, w, waterTop, h, t, 0.45, false);

    /* Dot matrix clock. */
    clock(ctx, w * 0.84, h * 0.30, h * 0.19, t);
  }

  /* 7. SURFERS: many sessions on one wave. */
  function sceneSurfers(ctx, t, p, w, h) {
    sky(ctx, w, h * 0.55, 1);
    ctx.fillStyle = gray(0.99);
    ctx.fillRect(0, h * 0.55, w, h * 0.45);

    var crest = function (x) {
      return h * (0.58 - 0.24 * (x / w))
        + sin(x * 0.035 + t * 0.5) * h * 0.045
        + sin(x * 0.012 - t * 0.3) * h * 0.03;
    };

    /* Wave body. */
    ctx.beginPath();
    ctx.moveTo(0, h);
    ctx.lineTo(0, crest(0));
    for (var x = 0; x <= w; x += 2) {
      var y = crest(x);
      ctx.lineTo(x, y);
      ctx.lineTo(x + 2, y);
    }
    ctx.lineTo(w, h);
    ctx.closePath();
    var gw = ctx.createLinearGradient(0, h * 0.2, 0, h);
    gw.addColorStop(0, gray(0.5));
    gw.addColorStop(0.45, gray(0.22));
    gw.addColorStop(1, gray(0.02));
    ctx.fillStyle = gw;
    ctx.fill();

    /* Curling lip at the right. */
    var curlX = w * 0.86;
    var curlY = crest(curlX) + h * 0.13;
    var curlR = h * 0.15;
    ctx.fillStyle = gray(0.12);
    ctx.beginPath();
    ctx.arc(curlX, curlY, curlR, 0, TAU);
    ctx.fill();
    ctx.strokeStyle = gray(1);
    ctx.lineWidth = Math.max(1, h * 0.018);
    ctx.beginPath();
    ctx.arc(curlX, curlY, curlR * 0.62, PI * 1.05, PI * 2.35);
    ctx.stroke();

    /* Foam dots on the dark side of the crest. */
    var rf = prng(808);
    ctx.fillStyle = gray(1);
    for (var i = 0; i < 90; i++) {
      var fx = rf() * w;
      var depth = rf();
      var drift = (t * 6 * (0.4 + depth)) % w;
      var px1 = (fx + drift) % w;
      var fy = crest(px1) + depth * h * 0.12 + sin(t * 2 + i) * 0.8;
      ctx.fillRect(Math.round(px1), Math.round(fy), 1, 1);
    }

    /* Five surfers along the crest. */
    for (var s = 0; s < 5; s++) {
      var sxp = w * (0.13 + s * 0.155);
      var sy = crest(sxp) + h * 0.03 + sin(t * 1.4 + s * 1.3) * h * 0.012;
      surfer(ctx, sxp, sy, h * 0.028 * (1 - s * 0.05), t + s);
    }

    /* Halftone spray above the crest. */
    var rs = prng(4242);
    for (var k = 0; k < 70; k++) {
      var ax = rs() * w;
      var lift = rs();
      var sxx = (ax + t * 9 * (0.3 + lift)) % w;
      var syy = crest(sxx) - lift * h * 0.28 - 1;
      if (syy < 0) continue;
      ctx.fillStyle = gray(0.55 + lift * 0.4);
      ctx.fillRect(Math.round(sxx), Math.round(syy), 1, 1);
    }

    /* Palm silhouettes on the far left. */
    var ps = h * 0.028;
    palm(ctx, w * 0.045, crest(w * 0.045) + h * 0.02, ps, -0.6);
    palm(ctx, w * 0.105, crest(w * 0.105) + h * 0.04, ps * 0.82, 0.5);
  }

  /* 8. BARCODE: the finale. Barcode prints, then the total explodes. */
  function sceneBarcode(ctx, t, p, w, h) {
    ctx.fillStyle = gray(1);
    ctx.fillRect(0, 0, w, h);

    /* Quiet zones left and right. */
    var qz = Math.max(6, w * 0.06);
    var bx = qz;
    var bw = w - qz * 2;
    var by = h * 0.30;
    var bh = h * 0.42;

    /* Guard bars, slightly taller. */
    ctx.fillStyle = '#000';
    ctx.fillRect(Math.round(bx), Math.round(by - h * 0.06), 2, Math.round(bh + h * 0.12));
    ctx.fillRect(Math.round(bx + 4), Math.round(by - h * 0.06), 2, Math.round(bh + h * 0.12));
    ctx.fillRect(Math.round(bx + bw - 6), Math.round(by - h * 0.06), 2, Math.round(bh + h * 0.12));
    ctx.fillRect(Math.round(bx + bw - 2), Math.round(by - h * 0.06), 2, Math.round(bh + h * 0.12));

    bars(ctx, bx + 9, by, bw - 18, bh, 20260705);

    /* Finale: a burst of ink pixels from the center, p 0.55 to 1. */
    if (p > 0.55) {
      var q = clamp((p - 0.55) / 0.45, 0, 1);
      var cx = w * 0.5;
      var cy = h * 0.5;
      var maxR = Math.max(w, h) * 0.78;
      var r = prng(9770);
      var fade = gray(clamp(q * 0.85, 0, 0.85));
      ctx.fillStyle = fade;
      for (var i = 0; i < 400; i++) {
        var a = r() * TAU;
        var sp = 0.15 + r() * 0.85;
        var size = 1 + ((r() * 3) | 0);
        var rr = q * maxR * sp;
        var gx = cx + cos(a) * rr;
        var gy = cy + sin(a) * rr * 0.62 + q * q * h * 0.22;
        if (gx < -4 || gx > w + 4 || gy < -4 || gy > h + 4) continue;
        ctx.fillRect(Math.round(gx), Math.round(gy), size, size);
      }
    }
  }

  global.Scenes = {
    sun: sceneSun,
    sharks: sceneSharks,
    skulls: sceneSkulls,
    fish: sceneFish,
    vortex: sceneVortex,
    beach: sceneBeach,
    surfers: sceneSurfers,
    barcode: sceneBarcode
  };
})(window);
