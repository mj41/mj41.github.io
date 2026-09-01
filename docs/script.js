// One program, four ways: notebook page, typeset listing, PMD 85 screen, fixed
// version. Cross-fades on a timer while visible; prev / next / pause / dots and
// the arrow keys steer it. Pausing is sticky - the timer stays off until asked.
(function () {
    'use strict';

    var cycle = document.getElementById('screen-cycle');
    if (!cycle) {
        return;
    }

    var views = [].slice.call(cycle.querySelectorAll('.screen-view'));
    var caption = document.getElementById('screen-caption');
    var controls = cycle.querySelector('.screen-controls');
    var dotBox = cycle.querySelector('.dots');
    var playBtn = cycle.querySelector('[data-act="play"]');
    var reduced = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    var INTERVAL = 6500;
    var index = 0;
    var timer = null;
    var hovered = false;
    var paused = reduced;
    var visible = false;
    var dots = [];

    views.forEach(function (view, i) {
        var dot = document.createElement('button');
        dot.type = 'button';
        dot.className = 'dot';
        dot.setAttribute('aria-label', 'Slide ' + (i + 1) + ' of ' + views.length);
        dot.addEventListener('click', function (e) {
            e.stopPropagation();
            show(i);
            restart();
        });
        dotBox.appendChild(dot);
        dots.push(dot);
    });

    function show(next) {
        index = (next + views.length) % views.length;
        views.forEach(function (view, i) {
            var on = i === index;
            view.classList.toggle('is-active', on);
            view.setAttribute('aria-hidden', on ? 'false' : 'true');
            if (on && caption) {
                caption.textContent = view.getAttribute('data-caption') || '';
            }
        });
        dots.forEach(function (dot, i) {
            dot.classList.toggle('is-on', i === index);
            dot.setAttribute('aria-current', i === index ? 'true' : 'false');
        });
    }

    function tick() {
        if (!hovered) {
            show(index + 1);
        }
    }

    function restart() {
        clearInterval(timer);
        timer = null;
        if (!paused && visible) {
            timer = setInterval(tick, INTERVAL);
        }
    }

    function setPaused(value) {
        paused = value;
        playBtn.textContent = paused ? '▶' : '❚❚';
        playBtn.setAttribute('aria-label', paused
            ? 'Play the slideshow' : 'Pause the slideshow');
        playBtn.setAttribute('aria-pressed', paused ? 'true' : 'false');
        restart();
    }

    controls.addEventListener('click', function (e) {
        var act = e.target.getAttribute && e.target.getAttribute('data-act');
        if (!act) {
            return;
        }
        e.stopPropagation();
        if (act === 'prev') {
            show(index - 1);
            restart();
        } else if (act === 'next') {
            show(index + 1);
            restart();
        } else if (act === 'play') {
            setPaused(!paused);
        }
    });

    cycle.addEventListener('click', function () {
        show(index + 1);
        restart();
    });
    cycle.addEventListener('mouseenter', function () { hovered = true; });
    cycle.addEventListener('mouseleave', function () { hovered = false; });
    cycle.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') {
            show(index - 1);
            restart();
        } else if (e.key === 'ArrowRight') {
            show(index + 1);
            restart();
        } else {
            return;
        }
        e.preventDefault();
    });

    show(0);
    setPaused(paused);

    // Only run the timer while the figure is actually on screen.
    if (window.IntersectionObserver) {
        new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                visible = entry.isIntersecting;
                restart();
            });
        }, { threshold: 0.2 }).observe(cycle);
    } else {
        visible = true;
        restart();
    }
}());
