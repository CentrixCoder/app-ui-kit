/*
 * app-ui-kit.js — the shared page behaviour of every app in the family.
 *
 * Extracted from jointLab (assets/theme.js, workflow.js, run_gate.js,
 * plot_resize.js, 2026-11-14). THIS FILE IS THE ONE COPY: apps load it from
 * the installed package, never paste it. Load it at the end of <body>
 * (Dash does this for you). It needs no library; the Plotly parts only act
 * when Plotly is on the page.
 *
 *   1. theme      sets data-theme="light" on <html> and <body>; recolours every
 *                 Plotly figure from the CSS --plot-* tokens.
 *   2. steps      one <details class="step"> open at a time in the left pane.
 *   3. run gate   window.appUiKit.userChangedRecently(): true within 5 s of a real
 *                 keypress or pointer press. Gate an Auto-run on it, so values
 *                 that callbacks set (page load, restored state) do not run.
 *   4. plot size  makes every Plotly figure adopt its container's size after a
 *                 hidden tab is shown, a step opens, or the window is zoomed.
 *
 * Opt-outs: a figure inside an element with data-ui-keep-colors keeps its own
 * colours; a figure inside .plot-wrap is sized to that wrapper.
 */
(function () {
    "use strict";
    if (typeof window === "undefined" || window.appUiKit) { return; }

    function css(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    /* ---------------------------------------------------------------- 1. theme */
    function recolorPlots() {
        if (!window.Plotly) { return; }
        var update = {
            paper_bgcolor: css("--plot-paper"),
            plot_bgcolor: css("--plot-surface"),
            "font.color": css("--plot-axis"),
            "xaxis.color": css("--plot-axis"),
            "yaxis.color": css("--plot-axis"),
            "xaxis.gridcolor": css("--plot-grid"),
            "yaxis.gridcolor": css("--plot-grid"),
            "xaxis.zerolinecolor": css("--plot-grid"),
            "yaxis.zerolinecolor": css("--plot-grid")
        };
        var nodes = document.querySelectorAll(".js-plotly-plot");
        for (var i = 0; i < nodes.length; i += 1) {
            if (nodes[i].closest("[data-ui-keep-colors]")) { continue; }
            try { window.Plotly.relayout(nodes[i], update); } catch (err) { /* plot may still be mounting */ }
        }
    }

    function applyTheme() {
        document.documentElement.setAttribute("data-theme", "light");
        if (document.body) { document.body.setAttribute("data-theme", "light"); }
        window.setTimeout(recolorPlots, 0);
        window.setTimeout(recolorPlots, 250);
    }

    function watchNewPlots() {
        if (typeof MutationObserver === "undefined") { return; }
        var queued = false;
        // .dash-graph as well as .js-plotly-plot: Dash mounts the wrapper first and
        // Plotly attaches .js-plotly-plot later, so testing only for it misses every
        // figure a callback creates.
        var containsPlot = function (node) {
            return node && node.nodeType === 1 && (
                (node.matches && node.matches(".js-plotly-plot, .dash-graph")) ||
                (node.querySelector && node.querySelector(".js-plotly-plot, .dash-graph"))
            );
        };
        new MutationObserver(function (records) {
            if (queued || !records.some(function (record) {
                return Array.prototype.some.call(record.addedNodes, containsPlot);
            })) { return; }
            queued = true;
            window.setTimeout(function () { queued = false; recolorPlots(); }, 0);
            // the 0 ms pass often finds Plotly not yet initialised; this one catches it
            window.setTimeout(recolorPlots, 250);
        }).observe(document.body || document.documentElement, { childList: true, subtree: true });
    }

    /* ---------------------------------------------------------------- 2. steps */
    // Opening a step closes the others and brings its heading into view. Only
    // <details class="step"> are touched; their contents stay mounted.
    document.addEventListener("toggle", function (e) {
        var step = e.target;
        if (!step.classList || !step.classList.contains("step") || !step.open) { return; }
        document.querySelectorAll("details.step[open]").forEach(function (other) {
            if (other !== step) { other.open = false; }
        });
        step.scrollIntoView({ block: "nearest" });
        // a figure drawn while its step was closed measured zero width
        window.setTimeout(function () { window.dispatchEvent(new Event("resize")); }, 30);
    }, true);  // capture: a <details> toggle event does not bubble

    /* ---------------------------------------------------------------- 3. run gate */
    var GATE_MS = 5000;
    var lastUserInput = 0;
    function markInput() { lastUserInput = Date.now(); }
    document.addEventListener("keydown", markInput, true);
    document.addEventListener("pointerdown", markInput, true);

    /* ---------------------------------------------------------------- 4. plot size */
    // Plotly sizes a figure to its box when drawn; a figure drawn in a hidden tab
    // measures 0x0 and falls back to 700x450, and responsive:true only listens for
    // window resizes (switching a tab fires none). So: re-check on every DOM or
    // container change for a few seconds, then a slow watchdog. resize() is a
    // no-op unless a figure is genuinely the wrong size.
    var PLOT = ".js-plotly-plot";
    var RETRY_TICKS = 40, TICK_MS = 100, WATCHDOG_MS = 400;
    var resizeObserver = null;
    var observed = typeof WeakSet !== "undefined" ? new WeakSet() : null;
    var ticksLeft = 0, pumping = false, watchdog = null;

    function observeContainers(root) {
        if (!resizeObserver || !root) { return; }
        var list = [];
        if (root.matches && root.matches(PLOT)) { list.push(root); }
        if (root.querySelectorAll) { list = list.concat(Array.prototype.slice.call(root.querySelectorAll(PLOT))); }
        for (var i = 0; i < list.length; i++) {
            if (observed && observed.has(list[i])) { continue; }
            resizeObserver.observe(list[i]);
            if (observed) { observed.add(list[i]); }
        }
    }
    function needsResize(node) {
        if (!window.Plotly || !node || !node._fullLayout) { return false; }
        var wrap = node.closest && node.closest(".plot-wrap");
        var box = (wrap || node).getBoundingClientRect();
        if (box.width < 1 || box.height < 1) { return false; }  // hidden: nothing to size to yet
        return Math.abs(node._fullLayout.width - box.width) > 1 ||
               Math.abs(node._fullLayout.height - box.height) > 1;
    }
    function resizeAll() {
        var nodes = document.querySelectorAll(PLOT);
        for (var i = 0; i < nodes.length; i++) {
            if (!needsResize(nodes[i])) { continue; }
            try { window.Plotly.Plots.resize(nodes[i]); } catch (err) { /* plot may be mid-update */ }
        }
    }
    function scheduleNext() {
        // requestAnimationFrame is paused in a background tab; fall back to a timer there
        if (document.visibilityState !== "hidden" && typeof window.requestAnimationFrame === "function") {
            window.requestAnimationFrame(pump);
        } else {
            window.setTimeout(pump, TICK_MS);
        }
    }
    function pump() {
        resizeAll();
        ticksLeft -= 1;
        if (ticksLeft > 0) { scheduleNext(); } else { pumping = false; startWatchdog(); }
    }
    function startWatchdog() {
        if (watchdog !== null || typeof window.setInterval !== "function") { return; }
        watchdog = window.setInterval(function () {
            if (document.visibilityState !== "hidden") { resizeAll(); }
        }, WATCHDOG_MS);
    }
    function kick() {
        ticksLeft = RETRY_TICKS;
        if (!pumping) { pumping = true; pump(); }
    }
    function watchPixelRatio() {
        if (typeof window.matchMedia !== "function" || !window.devicePixelRatio) { return; }
        var query = window.matchMedia("(resolution: " + window.devicePixelRatio + "dppx)");
        var onChange = function () { kick(); watchPixelRatio(); };
        if (typeof query.addEventListener === "function") {
            query.addEventListener("change", onChange, { once: true });
        } else if (typeof query.addListener === "function") {
            query.addListener(onChange);
        }
    }
    function startPlotSizing() {
        kick();
        if (typeof MutationObserver !== "undefined") {
            new MutationObserver(function (records) {
                for (var i = 0; i < records.length; i++) {
                    for (var j = 0; j < records[i].addedNodes.length; j++) { observeContainers(records[i].addedNodes[j]); }
                }
                kick();
            }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["style", "class"] });
        }
        if (typeof ResizeObserver !== "undefined") {
            resizeObserver = new ResizeObserver(kick);
            observeContainers(document);
            resizeObserver.observe(document.body);
        }
        window.addEventListener("resize", kick);
        if (window.visualViewport) {
            window.visualViewport.addEventListener("resize", kick);
            window.visualViewport.addEventListener("scroll", kick);
        }
        document.addEventListener("visibilitychange", kick);
        watchPixelRatio();
        startWatchdog();
    }

    /* ---------------------------------------------------------------- start */
    window.appUiKit = {
        version: "0.1.1",
        recolorPlots: recolorPlots,
        resizePlots: kick,
        userChangedRecently: function () { return Date.now() - lastUserInput < GATE_MS; }
    };
    function start() { applyTheme(); watchNewPlots(); startPlotSizing(); }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
}());
