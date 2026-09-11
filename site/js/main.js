/* main.js - boot sequence for the "Rachunek za tokeny" receipt page.
 *
 * Load order (plain <script defer>, no modules):
 *   gsap -> ScrollTrigger -> data.js -> charts.js -> halftone/engine.js ->
 *   halftone/scenes.js -> render.js -> motion.js -> main.js
 *
 * Boot: DOMContentLoaded -> document.fonts.ready (1500 ms timeout fallback) ->
 *   Render.build(RECEIPT_DATA) -> Halftone.init() -> Motion.init() -> ScrollTrigger.refresh()
 *
 * Every step is wrapped, so one broken module never blanks the page.
 */
(function () {
  'use strict';

  document.documentElement.classList.add('js');

  var RESIZE_DELAY = 200;
  var FONTS_TIMEOUT = 1500;

  function step(name, fn) {
    try {
      fn();
      return true;
    } catch (err) {
      console.error('[receipt] step failed', name, err);
      return false;
    }
  }

  function whenFontsReady(callback) {
    var done = false;

    function run() {
      if (done) return;
      done = true;
      callback();
    }

    var timer = setTimeout(run, FONTS_TIMEOUT);

    var ready = document.fonts && document.fonts.ready;
    if (ready && typeof ready.then === 'function') {
      ready.then(function () {
        clearTimeout(timer);
        run();
      }, function () {
        clearTimeout(timer);
        run();
      });
    } else {
      clearTimeout(timer);
      run();
    }
  }

  function bindResize() {
    var timer = null;

    window.addEventListener('resize', function () {
      if (timer) clearTimeout(timer);
      timer = setTimeout(function () {
        timer = null;
        step('halftone.refresh', function () {
          if (window.Halftone && typeof window.Halftone.refresh === 'function') {
            window.Halftone.refresh();
          }
        });
        step('scrolltrigger.refresh', function () {
          if (window.ScrollTrigger) window.ScrollTrigger.refresh();
        });
      }, RESIZE_DELAY);
    });
  }

  function boot() {
    step('render', function () {
      if (!window.Render || typeof window.Render.build !== 'function') {
        throw new Error('window.Render.build is missing');
      }
      if (!window.RECEIPT_DATA) {
        throw new Error('window.RECEIPT_DATA is missing');
      }
      window.Render.build(window.RECEIPT_DATA);
    });

    step('halftone', function () {
      if (window.Halftone && typeof window.Halftone.init === 'function') {
        window.Halftone.init();
      }
    });

    step('motion', function () {
      if (window.Motion && typeof window.Motion.init === 'function') {
        window.Motion.init();
      }
    });

    step('scrolltrigger.refresh', function () {
      if (window.ScrollTrigger) window.ScrollTrigger.refresh();
    });

    step('resize', bindResize);
  }

  function start() {
    whenFontsReady(boot);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
