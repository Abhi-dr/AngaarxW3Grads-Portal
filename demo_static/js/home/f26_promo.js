/**
 * FLAMES '26 Promotional Logic  |  f26_promo.js
 * Loaded with defer — does NOT block page render.
 *
 * Responsibilities:
 *  1. Show/hide the floating pill bar (per session via sessionStorage)
 *  2. Position the pill just below the fixed navbar (JS measurement)
 *  3. Re-sync on resize / orientation change
 *  4. Trigger slide-in promo card after 5 s (once per 24 h via localStorage)
 */
(function () {
    'use strict';

    var BAR_KEY  = 'f26_bar_closed_session';
    var CARD_KEY = 'f26_card_last_shown';
    var CARD_TTL = 24 * 60 * 60 * 1000; // 24 hours
    var PILL_GAP = 10; // px gap between navbar bottom and pill top

    // ── Helpers ────────────────────────────────────────────────
    function el(id) { return document.getElementById(id); }

    /**
     * Position the pill just below the navbar.
     * Pill is position:fixed so we set its `top` in px.
     */
    function positionPill() {
        var bar    = el('f26-bar');
        var navbar = document.querySelector('.navbar-custom');
        if (!bar || !navbar) return;

        var navH = navbar.getBoundingClientRect().height;
        // The navbar itself may have a top offset due to its margin/position.
        // getBoundingClientRect().bottom gives us the exact bottom of the navbar.
        var navBottom = navbar.getBoundingClientRect().bottom;

        bar.style.top = Math.round(navBottom + PILL_GAP) + 'px';
    }

    // ── Announcement bar ────────────────────────────────────────
    function initBar() {
        var bar = el('f26-bar');
        if (!bar) return;

        if (sessionStorage.getItem(BAR_KEY)) {
            // Already dismissed this session — keep hidden, no layout cost
            bar.style.display = 'none';
            return;
        }

        // Show the pill and position it
        bar.style.display = 'inline-flex';
        // Wait a frame so the browser has painted the navbar first
        requestAnimationFrame(function () {
            requestAnimationFrame(positionPill);
        });
    }

    window.closeF26Bar = function () {
        var bar = el('f26-bar');
        if (!bar) return;

        bar.classList.add('f26-bar-hidden');
        sessionStorage.setItem(BAR_KEY, '1');

        // After transition, fully remove from interaction
        setTimeout(function () {
            bar.style.display = 'none';
        }, 400);
    };

    // ── Slide-in promo card ─────────────────────────────────────
    function initCard() {
        var lastShown  = localStorage.getItem(CARD_KEY);
        var shouldShow = !lastShown || (Date.now() - parseInt(lastShown, 10)) > CARD_TTL;
        if (!shouldShow) return;

        setTimeout(function () {
            var card = el('f26-card');
            if (card) card.classList.add('show');
        }, 5000);
    }

    window.closeF26Card = function () {
        var card = el('f26-card');
        if (!card) return;
        card.style.transition = 'transform .4s ease, opacity .35s ease';
        card.style.transform  = 'translateX(calc(100% + 40px))';
        card.style.opacity    = '0';
        localStorage.setItem(CARD_KEY, Date.now().toString());
    };

    // ── Re-sync pill position on resize ─────────────────────────
    var resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(positionPill, 80);
    });

    // ── Boot ────────────────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            initBar();
            initCard();
        });
    } else {
        initBar();
        initCard();
    }
})();
