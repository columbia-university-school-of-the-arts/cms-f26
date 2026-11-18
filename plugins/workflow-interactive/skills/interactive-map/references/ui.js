/* The page in the browser: editing, the walkthrough, the trace, saving, and Git.
   Runs only where there is a document. Keep the page's own code in elements
   marked data-wf: saving copies them as they are. */
(function (WF) {
  "use strict";
  if (typeof document === "undefined") return;

  var app = document.getElementById("app");
  var dataEl = document.getElementById("workflow");
  var parsed = WF.parse(dataEl ? dataEl.textContent : "");
  if (parsed.error) {
    app.innerHTML = '<div class="error"><h1>This map could not be drawn</h1><p></p></div>';
    app.querySelector("p").textContent = parsed.error;
    return;
  }

  /* The page's own source, captured once, before anything renders. */
  var OWN = {
    reset: (document.head && document.head.querySelector("style")) ? document.head.querySelector("style").textContent : "",
    styles: Array.prototype.map.call(document.querySelectorAll("style[data-wf]"), function (e) {
      return "<style data-wf>" + e.textContent + "</style>";
    }),
    scripts: Array.prototype.map.call(document.querySelectorAll("script[data-wf]"), function (e) {
      return "<script data-wf>" + e.textContent + "</scr" + "ipt>";
    })
  };
  function pageHtml(m) {
    return WF.rebuild({ reset: OWN.reset, title: m.title, styles: OWN.styles, scripts: OWN.scripts, dataText: WF.serializeData(m) });
  }

  var S = {
    model: parsed.model, dirty: false, selected: null, level: 1, artifact: null,
    readOnly: false, walk: null, edits: {}, saving: false,
    mode: "view", viewRound: null,
    sample: null, dictation: null, chat: { turns: [], items: [], busy: null, off: false }
  };
  var M = function () { return S.model; };

  /* ---------- helpers ---------- */
  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") e.textContent = attrs[k];
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== false && attrs[k] !== null && attrs[k] !== undefined) e.setAttribute(k, attrs[k] === true ? "" : attrs[k]);
    });
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function stepBy(key) { return M().steps.filter(function (s) { return String(s.n) === key; })[0]; }
  function sourceBy(id) { return M().sources.filter(function (s) { return s.id === id; })[0]; }
  function laneBy(id) { return M().lanes.filter(function (l) { return l.id === id; })[0]; }
  function change(what) {
    M().changes.unshift({ date: WF.today(), what: what });
    S.dirty = true;
  }
  function renormalize() {
    S.model = WF.normalize(WF.stripInternal(M()));
  }
  function flushEdits() {
    var keys = Object.keys(S.edits);
    if (!keys.length) return;
    keys.forEach(function (k) { change("edited " + k + ": " + S.edits[k].join(", ")); });
    S.edits = {};
  }
  function noteEdit(label, field) {
    S.edits[label] = S.edits[label] || [];
    if (S.edits[label].indexOf(field) < 0) S.edits[label].push(field);
    S.dirty = true;
    renderStatus();
  }
  function toast(msg) {
    var t = document.querySelector(".toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toast.t);
    toast.t = setTimeout(function () { t.classList.remove("show"); }, 4200);
  }
  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return fallbackCopy(text); });
    }
    return Promise.resolve(fallbackCopy(text));
  }
  function fallbackCopy(text) {
    var ta = h("textarea", { "class": "offscreen" });
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    ta.remove();
    return ok;
  }
  function stash() {
    try { sessionStorage.setItem("wf-ui", JSON.stringify({ selected: S.selected, scroll: canvasWrap().scrollLeft, mode: S.mode, round: S.viewRound,
      chat: { turns: S.chat.turns.slice(-12), items: S.chat.items.slice(-12).map(function (it) { return Object.assign({}, it, { live: false }); }) } })); } catch (e) { /* none */ }
  }
  function unstash() {
    try {
      var v = JSON.parse(sessionStorage.getItem("wf-ui") || "null");
      sessionStorage.removeItem("wf-ui");
      return v;
    } catch (e) { return null; }
  }

  /* ---------- skeleton ---------- */
  app.innerHTML = "";
  var header = h("header", { "class": "top" });
  var toolbar = h("div", { "class": "toolbar", role: "toolbar" });
  var banner = h("div", { "class": "banner", hidden: true });
  var chatEl = h("section", { "class": "chat", hidden: true, "aria-label": "Tell the map what to change" });
  var problems = h("div", { "class": "problems", hidden: true });
  var wrapEl = h("div", { "class": "canvas-wrap" });
  var traceEl = h("section", { "class": "trace" });
  var panel = h("aside", { "class": "panel", hidden: true, "aria-label": "Details" });
  var logEl = h("section", { "class": "log" });
  var main = h("div", { "class": "main" }, [h("div", { "class": "work" }, [wrapEl, traceEl]), panel]);
  [header, toolbar, chatEl, banner, problems, main, logEl, h("div", { "class": "toast", role: "status" })].forEach(function (e) { app.appendChild(e); });
  function canvasWrap() { return wrapEl; }

  /* ---------- header and toolbar ---------- */
  function renderHeader() {
    header.innerHTML = "";
    header.appendChild(h("h1", { text: M().title }));
    var meta = [];
    if (M().kind) meta.push(M().kind);
    if (M().begun) meta.push("begun " + M().begun);
    if (M().repo.owner && M().repo.name) meta.push(M().repo.owner + "/" + M().repo.name + " \u00b7 " + M().repo.branch);
    if (M().question) header.appendChild(h("p", { "class": "question", text: M().question }));
    header.appendChild(h("p", { "class": "meta", text: meta.join(" \u00b7 ") }));
  }

  var statusEl = h("span", { "class": "status", "aria-live": "polite" });
  var btn = {};
  function button(key, label, onclick, title) {
    btn[key] = h("button", { type: "button", "class": "btn btn-" + key, title: title || label, onclick: onclick }, [label]);
    return btn[key];
  }
  function renderToolbar() {
    toolbar.innerHTML = "";
    toolbar.appendChild(h("div", { "class": "group modes", role: "group", "aria-label": "Mode" }, [
      button("view", "View", function () { setMode("view"); }, "See what each step did"),
      button("edit", "Edit", function () { setMode("edit"); }, "Change the workflow")
    ]));
    roundSelect = h("select", { "class": "round-select", "aria-label": "Round" });
    roundSelect.addEventListener("change", function () { S.viewRound = parseInt(roundSelect.value, 10); resetWalk(); renderCanvas(); renderPanel(); });
    toolbar.appendChild(h("div", { "class": "group" }, [
      roundSelect,
      button("play", "\u25b6 Play", togglePlay, "Play what happened, or the plan"),
      button("step", "\u23ed Step", stepOnce, "Move one step along the walkthrough"),
      button("reset", "\u21ba Reset", resetWalk, "Clear the walkthrough")
    ]));
    toolbar.appendChild(h("div", { "class": "group" }, [
      button("addstep", "\uff0b Step", addStep), button("addsource", "\uff0b Source", addSource),
      button("addlane", "\uff0b Lane", addLane)
    ]));
    toolbar.lastChild.classList.add("edit-only");
    toolbar.appendChild(h("div", { "class": "group view-only" }, [
      button("round", "New round", startRound, "Start the next run of the whole workflow")
    ]));
    toolbar.appendChild(h("div", { "class": "group" }, [
      button("save", "Save", save, "Save this page (Cmd or Ctrl + S)"), statusEl,
      button("copy", "Copy the map", copyMap, "Copy the map's data to paste into the chat")
    ]));
    renderStatus();
  }

  var roundSelect = null;
  function currentRound() {
    var rs = WF.rounds(M());
    if (S.viewRound && (rs.indexOf(S.viewRound) >= 0 || S.viewRound === M().round)) return S.viewRound;
    return rs.length ? rs[rs.length - 1] : M().round;
  }
  function renderModes() {
    app.classList.toggle("is-view", S.mode === "view");
    app.classList.toggle("is-edit", S.mode === "edit");
    btn.view.setAttribute("aria-pressed", S.mode === "view");
    btn.edit.setAttribute("aria-pressed", S.mode === "edit");
    var rs = WF.rounds(M());
    if (rs.indexOf(M().round) < 0) rs.push(M().round);
    roundSelect.innerHTML = "";
    rs.forEach(function (r) { roundSelect.appendChild(h("option", { value: r, selected: r === currentRound() }, ["Round " + r])); });
    roundSelect.hidden = S.mode !== "view" || rs.length < 2;
  }
  function setMode(mode) {
    if (S.mode === mode) return;
    flushEdits();
    S.mode = mode;
    if (S.selected && S.selected.indexOf("lane:") === 0 && mode === "view") S.selected = null;
    resetWalk();
    renderAll();
  }
  function startRound() {
    flushEdits();
    S.model = WF.newRound(M());
    S.viewRound = M().round;
    S.dirty = true;
    resetWalk();
    renderAll();
    toast("Round " + M().round + " started. Runs you record now count as its passes.");
  }

  function renderStatus() {
    statusEl.textContent = S.readOnly ? "read only" : S.dirty || Object.keys(S.edits).length ? "unsaved changes" : "saved";
    statusEl.className = "status" + (S.dirty || Object.keys(S.edits).length ? " dirty" : "");
    btn.save.disabled = S.level < 2 || S.readOnly;
  }


  function renderBanner() {
    var msg = "";
    if (S.level === 1) msg = "Changes on this page are not kept here. Copy the map and paste it into the chat to keep them.";
    else if (S.readOnly) msg = "You can look at this map but not change it.";
    banner.hidden = !msg;
    banner.innerHTML = "";
    if (msg) {
      banner.appendChild(h("span", { text: msg }));
      if (S.level === 1) banner.appendChild(h("button", { type: "button", "class": "btn", onclick: copyMap }, ["Copy the map"]));
    }
  }

  function renderProblems() {
    var p = M().problems;
    problems.hidden = !p.length;
    problems.innerHTML = "";
    if (p.length) {
      problems.appendChild(h("strong", { text: "Check these: " }));
      problems.appendChild(h("ul", {}, p.map(function (t) { return h("li", { text: t }); })));
    }
  }

  /* ---------- canvas ---------- */
  var L = null;
  function renderCanvas() {
    L = WF.layout(M());
    var counts = {};
    if (S.mode === "view") M().runs.forEach(function (r) { if (r.round === currentRound()) counts[r.step] = (counts[r.step] || 0) + 1; });
    wrapEl.innerHTML = WF.renderSvg(M(), L, { counts: counts });
    var svg = wrapEl.querySelector("svg");
    svg.addEventListener("pointerdown", onPointerDown);
    svg.addEventListener("keydown", function (e) {
      var g = e.target.closest && e.target.closest(".card");
      if (g && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); select(g.getAttribute("data-node")); }
    });
    svg.querySelectorAll(".lane-head, .lane-name").forEach(function (el) {
      el.addEventListener("click", function () { if (S.mode === "edit") select("lane:" + el.closest(".lane").getAttribute("data-lane")); });
    });
    markSelected();
    if (S.walk) replayMarks();
  }
  function markSelected() {
    wrapEl.querySelectorAll(".card.selected").forEach(function (g) { g.classList.remove("selected"); });
    if (S.selected) {
      var g = wrapEl.querySelector('.card[data-node="' + cssEsc(S.selected) + '"]');
      if (g) g.classList.add("selected");
    }
  }
  function cssEsc(s) { return String(s).replace(/["\\]/g, "\\$&"); }

  var drag = null;
  function svgPoint(svg, e) {
    var r = svg.getBoundingClientRect();
    return { x: (e.clientX - r.left) * (L.width / r.width), y: (e.clientY - r.top) * (L.height / r.height) };
  }
  /* ---------- drag from a card's out port to another card: a new arrow ---------- */
  var link = null;
  function cardAt(x, y) {
    var el = document.elementFromPoint(x, y);
    var g = el && el.closest && el.closest(".card");
    return g && wrapEl.contains(g) ? g : null;
  }
  function startLink(e, g) {
    e.preventDefault();
    e.stopPropagation();
    var svg = wrapEl.querySelector("svg"), from = g.getAttribute("data-node"), n = L.nodes[from];
    var x0 = n.x + L.g.card, y0 = n.y + L.g.card / 2;
    var line = document.createElementNS("http://www.w3.org/2000/svg", "path");
    line.setAttribute("class", "connect-line");
    line.setAttribute("d", "M" + x0 + " " + y0 + "L" + x0 + " " + y0);
    svg.appendChild(line);
    g.classList.add("connect-from");
    link = { from: from, svg: svg, line: line, x0: x0, y0: y0, target: null, id: e.pointerId };
    svg.setPointerCapture(e.pointerId);
    svg.addEventListener("pointermove", onLinkMove);
    svg.addEventListener("pointerup", onLinkUp);
    svg.addEventListener("pointercancel", endLink);
  }
  function onLinkMove(e) {
    if (!link) return;
    var p = svgPoint(link.svg, e), dx = Math.max(40, Math.abs(p.x - link.x0) / 2);
    link.line.setAttribute("d", "M" + link.x0 + " " + link.y0 + "C" + (link.x0 + dx) + " " + link.y0 + " " +
      (p.x - dx) + " " + p.y + " " + p.x + " " + p.y);
    var g = cardAt(e.clientX, e.clientY), id = g && g.getAttribute("data-node");
    var ok = g && id !== link.from && id.indexOf("src-") !== 0 ? g : null;
    if (ok !== link.target) {
      if (link.target) link.target.classList.remove("connect-target");
      link.target = ok;
      if (ok) ok.classList.add("connect-target");
    }
  }
  function endLink() {
    if (!link) return;
    var l = link;
    link = null;
    l.svg.removeEventListener("pointermove", onLinkMove);
    l.svg.removeEventListener("pointerup", onLinkUp);
    l.svg.removeEventListener("pointercancel", endLink);
    try { l.svg.releasePointerCapture(l.id); } catch (e) { /* none */ }
    l.line.remove();
    wrapEl.querySelectorAll(".connect-from, .connect-target").forEach(function (g) { g.classList.remove("connect-from", "connect-target"); });
  }
  function onLinkUp(e) {
    if (!link) return;
    var from = link.from, g = cardAt(e.clientX, e.clientY), to = g && g.getAttribute("data-node");
    endLink();
    if (!to || to === from) return;
    flushEdits();
    var r = WF.connect(M(), from, to);
    if (!r.done.length) { toast("No arrow added: " + r.failed[0].why + "."); return; }
    S.model = r.model;
    S.dirty = true;
    afterChange();
    toast(r.done[0].charAt(0).toUpperCase() + r.done[0].slice(1) + ". Press Save to keep it.");
  }

  function onPointerDown(e) {
    if (e.target.closest && e.target.closest(".port-hit") && S.mode === "edit" && !S.readOnly) {
      startLink(e, e.target.closest(".card"));
      return;
    }
    var g = e.target.closest && e.target.closest(".card");
    if (!g) return;
    var svg = wrapEl.querySelector("svg"), id = g.getAttribute("data-node"), p = svgPoint(svg, e);
    drag = { id: id, g: g, start: p, moved: false, svg: svg };
    g.setPointerCapture(e.pointerId);
    g.addEventListener("pointermove", onPointerMove);
    g.addEventListener("pointerup", onPointerUp, { once: true });
    g.addEventListener("pointercancel", function () { drag = null; renderCanvas(); }, { once: true });
  }
  function onPointerMove(e) {
    if (!drag) return;
    var p = svgPoint(drag.svg, e), dx = p.x - drag.start.x, dy = p.y - drag.start.y;
    if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 6) return;
    if (S.readOnly || S.mode === "view") return;
    drag.moved = true;
    drag.g.classList.add("dragging");
    drag.g.setAttribute("transform", "translate(" + dx + "," + (drag.id.indexOf("src-") === 0 ? 0 : dy) + ")");
    drag.last = p;
  }
  function onPointerUp() {
    var d = drag;
    drag = null;
    if (!d) return;
    d.g.removeEventListener("pointermove", onPointerMove);
    if (!d.moved) { select(d.id); return; }
    var n = L.nodes[d.id], dx = d.last.x - d.start.x, dy = d.last.y - d.start.y;
    var col = Math.round((((n.x + dx) - L.g.head - L.g.padX) / L.g.colW - L.g.off) * 2) / 2;
    if (d.id.indexOf("src-") !== 0) col = Math.max(0, col);
    var laneIdx = Math.min(M().lanes.length - 1, Math.max(0, Math.floor((n.y + dy + L.g.card / 2) / L.g.lane)));
    if (d.id.indexOf("src-") === 0) {
      var src = sourceBy(d.id);
      if (src) { src.col = col; change("moved source " + src.name); }
    } else {
      var s = stepBy(d.id), lane = M().lanes[laneIdx];
      if (lane.kind === "sources") lane = M().lanes[1];
      var moved = [];
      if (s.lane !== lane.id) {
        s.lane = lane.id;
        s.who = WF.whoForLane(lane, s.who);
        moved.push("to the " + lane.name + " lane, so " + s.who + " does it");
      }
      if (s.col !== col) { s.col = col; moved.push("along the flow"); }
      if (moved.length) change("moved step " + s.n + " " + moved.join(" and "));
    }
    afterChange();
  }

  function afterChange() {
    renormalize();
    if (S.walk) resetWalk();
    renderAll();
  }

  /* ---------- side panel ---------- */
  function select(id) {
    flushEdits();
    S.selected = id;
    renderPanel();
    markSelected();
    renderStatus();
  }

  function field(label, value, onInput, opts) {
    opts = opts || {};
    var input;
    if (opts.options) {
      input = h("select", {}, opts.options.map(function (o) { return h("option", { value: o, selected: o === value }, [o]); }));
    } else if (opts.multi) {
      input = h("textarea", { rows: opts.rows || 2 });
      input.value = value;
    } else {
      input = h("input", { type: opts.type || "text", list: opts.list || null });
      if (opts.type === "checkbox") input.checked = !!value; else input.value = value;
    }
    input.disabled = S.readOnly;
    input.addEventListener(opts.type === "checkbox" || opts.options ? "change" : "input", function () {
      onInput(opts.type === "checkbox" ? input.checked : input.value);
      renderCanvasSoon();
    });
    var w = h("label", { "class": "field" + (opts.type === "checkbox" ? " check" : "") }, [h("span", { text: label }), input]);
    if (/UNSURE/.test(String(value))) w.classList.add("is-unsure");
    return w;
  }
  var canvasTimer = null;
  function renderCanvasSoon() {
    clearTimeout(canvasTimer);
    canvasTimer = setTimeout(function () { renormalize(); renderCanvas(); renderTrace(); }, 250);
  }

  function iconList() {
    var dl = document.getElementById("wf-icons");
    if (dl) return "wf-icons";
    dl = h("datalist", { id: "wf-icons" });
    Object.keys(M().icons || {}).concat(Object.keys(WF_ICONS.brand), Object.keys(WF_ICONS.generic)).forEach(function (k) {
      dl.appendChild(h("option", { value: k }));
    });
    document.body.appendChild(dl);
    return "wf-icons";
  }

  function arrowsSection(fromId, label) {
    var box = h("div", { "class": "arrows" }, [h("h3", { text: "Arrows from " + label })]);
    M().arrows.forEach(function (a, i) {
      if (a.from !== fromId) return;
      var row = h("div", { "class": "arrow-row" }, [
        h("span", { text: "\u2192 " + a.to + (a.loop ? " (loop)" : "") }),
        (function () {
          var inp = h("input", { type: "text", placeholder: "what moves", "aria-label": "What moves along this arrow" });
          inp.value = a.label;
          inp.disabled = S.readOnly;
          inp.addEventListener("input", function () { a.label = inp.value; noteEdit(label, "arrow label"); renderCanvasSoon(); });
          return inp;
        })(),
        h("button", { type: "button", "class": "btn small", disabled: S.readOnly, onclick: function () {
          M().arrows.splice(i, 1); change("removed the arrow from " + a.from + " to " + a.to); afterChange();
        } }, ["\u00d7"])
      ]);
      box.appendChild(row);
    });
    var targets = M().steps.map(function (s) { return String(s.n); }).filter(function (k) { return k !== fromId; });
    if (targets.length && !S.readOnly) {
      var sel = h("select", { "aria-label": "Add an arrow to" }, targets.map(function (k) { return h("option", { value: k }, [k + " " + stepBy(k).name]); }));
      var loop = h("input", { type: "checkbox", "aria-label": "Loops back" });
      box.appendChild(h("div", { "class": "arrow-add" }, [
        h("span", { text: "Add an arrow to" }), sel, h("label", { "class": "inline" }, [loop, " loops back"]),
        h("button", { type: "button", "class": "btn small", onclick: function () {
          M().arrows.push({ from: fromId, to: sel.value, loop: loop.checked, label: "" });
          change("added an arrow from " + fromId + " to " + sel.value);
          afterChange();
        } }, ["Add"])
      ]));
    }
    return box;
  }

  function renderPanel() {
    panel.innerHTML = "";
    var id = S.selected;
    if (!id) { panel.hidden = true; return; }
    panel.hidden = false;
    var close = h("button", { type: "button", "class": "btn small close", "aria-label": "Close", onclick: function () { select(null); } }, ["\u00d7"]);
    if (id.indexOf("lane:") === 0) return renderLanePanel(id.slice(5), close);
    var src = sourceBy(id);
    if (src) return S.mode === "view" ? renderSourceView(src, close) : renderSourcePanel(src, close);
    var s = stepBy(id);
    if (!s) { panel.hidden = true; return; }
    if (S.mode === "view") return renderStepView(s, close);
    var label = "step " + s.n;
    panel.appendChild(h("div", { "class": "panel-head" }, [h("h2", { text: s.n + " " + s.name }), close]));
    var lane = laneBy(s.lane);
    panel.appendChild(h("p", { "class": "who", text: "Done by " + s.who + " (the " + (lane ? lane.name : s.lane) + " lane). Drag the card to another lane to change who does it." }));
    panel.appendChild(field("Name", s.name, function (v) { s.name = v; noteEdit(label, "name"); }));
    panel.appendChild(field("What goes in", s["in"], function (v) { s["in"] = v; noteEdit(label, "in"); }, { multi: true }));
    panel.appendChild(field("What comes out", s.out, function (v) { s.out = v; noteEdit(label, "out"); }, { multi: true }));
    panel.appendChild(field("Who checks it", s.check.by, function (v) { s.check.by = v; noteEdit(label, "who checks"); }));
    panel.appendChild(field("How it is checked", s.check.how, function (v) { s.check.how = v; noteEdit(label, "how it is checked"); }, { multi: true }));
    panel.appendChild(field("Claude here is a \u201cyou\u201d or an \u201cit\u201d", s.you_or_it, function (v) { s.you_or_it = v; noteEdit(label, "you or it"); }, { options: ["UNSURE", "you", "it"] }));
    panel.appendChild(field("Credited", s.credited, function (v) { s.credited = v; noteEdit(label, "credited"); }));
    panel.appendChild(field("This step is mine alone", s.mine, function (v) { s.mine = v; noteEdit(label, "mine"); }, { type: "checkbox" }));
    panel.appendChild(field("Icon", s.icon, function (v) { s.icon = v; noteEdit(label, "icon"); }, { list: iconList() }));
    panel.appendChild(field("Still UNSURE (one per line)", s.unsure.join("\n"), function (v) {
      s.unsure = v.split("\n").map(function (x) { return x.trim(); }).filter(Boolean); noteEdit(label, "unsure");
    }, { multi: true, rows: 3 }));
    var runBox = h("div", { "class": "run" }, [h("h3", { text: "Run it in Cowork" }), h("p", { "class": "run-text", text: s.run || "No prompt yet." }),
      h("button", { type: "button", "class": "btn", onclick: function () {
        copyText(s.run).then(function () { toast("Copied. Paste it into the Cowork chat, with your fleet folder attached."); });
      } }, ["Copy the prompt"])]);
    panel.appendChild(runBox);
    panel.appendChild(field("The prompt", s.run, function (v) { s.run = v; noteEdit(label, "run"); }, { multi: true }));
    var note = h("input", { type: "text", placeholder: "What happened, in one line", "aria-label": "Run note" });
    function record(state) {
      flushEdits();
      S.model = WF.recordRun(M(), String(s.n), { result: state, note: note.value });
      S.dirty = true;
      afterChange();
    }
    panel.appendChild(h("div", { "class": "record" }, [h("h3", { text: "Record a run" }),
      h("p", { "class": "state-now", text: "Now: " + s.state + (s.state_date ? ", " + s.state_date : "") + (s.state_note ? ", " + s.state_note : "") }),
      note, h("div", { "class": "row" }, [
        h("button", { type: "button", "class": "btn ok", disabled: S.readOnly, onclick: function () { record("works"); } }, ["It works"]),
        h("button", { type: "button", "class": "btn bad", disabled: S.readOnly, onclick: function () { record("broken"); } }, ["It broke"]),
        h("button", { type: "button", "class": "btn", disabled: S.readOnly, onclick: function () { record("tried"); } }, ["Tried"])
      ])]));
    panel.appendChild(arrowsSection(String(s.n), label));
    panel.appendChild(removeButton("Remove this step", function () {
      M().steps = M().steps.filter(function (x) { return x !== s; });
      M().arrows = M().arrows.filter(function (a) { return a.from !== String(s.n) && a.to !== String(s.n); });
      change("removed step " + s.n + " " + s.name);
      S.selected = null;
      afterChange();
    }));
    var mine = M().changes.filter(function (c) { return c.what.indexOf("step " + s.n + " ") >= 0 || c.what.indexOf("step " + s.n + ":") >= 0; }).slice(0, 5);
    if (mine.length) panel.appendChild(h("div", { "class": "mini-log" }, [h("h3", { text: "Changes to this step" }),
      h("ul", {}, mine.map(function (c) { return h("li", { text: c.date + "  " + c.what }); }))]));
  }

  function removeButton(label, onConfirm) {
    var b = h("button", { type: "button", "class": "btn danger", disabled: S.readOnly }, [label]);
    b.addEventListener("click", function () {
      if (b.dataset.armed === "1") { onConfirm(); return; }
      b.dataset.armed = "1";
      b.textContent = "Click again to remove";
      setTimeout(function () { b.dataset.armed = "0"; b.textContent = label; }, 3000);
    });
    return b;
  }

  function renderSourcePanel(src, close) {
    var label = "source " + src.name;
    panel.appendChild(h("div", { "class": "panel-head" }, [h("h2", { text: src.name }), close]));
    panel.appendChild(field("Name", src.name, function (v) { src.name = v; noteEdit(label, "name"); }));
    panel.appendChild(field("How it is reached", src.kind, function (v) { src.kind = v; noteEdit(label, "kind"); },
      { options: ["", "api", "download", "by hand", "someone else"] }));
    panel.appendChild(field("What comes out of it", src.gives, function (v) { src.gives = v; noteEdit(label, "gives"); }));
    panel.appendChild(field("Link", src.link, function (v) { src.link = v; noteEdit(label, "link"); }, { type: "url" }));
    panel.appendChild(field("Icon", src.icon, function (v) { src.icon = v; noteEdit(label, "icon"); }, { list: iconList() }));
    var known = (M().icons && M().icons[src.icon]) || WF_ICONS.brand[src.icon] || WF_ICONS.generic[src.icon];
    if (!known) panel.appendChild(h("p", { "class": "hint", text: "No icon called \u201c" + src.icon + "\u201d on this page yet. Ask Claude in the chat to fetch it." }));
    panel.appendChild(field("Still UNSURE (one per line)", src.unsure.join("\n"), function (v) {
      src.unsure = v.split("\n").map(function (x) { return x.trim(); }).filter(Boolean); noteEdit(label, "unsure");
    }, { multi: true }));
    panel.appendChild(arrowsSection(src.id, label));
    panel.appendChild(removeButton("Remove this source", function () {
      M().sources = M().sources.filter(function (x) { return x !== src; });
      M().arrows = M().arrows.filter(function (a) { return a.from !== src.id; });
      change("removed source " + src.name);
      S.selected = null;
      afterChange();
    }));
  }

  function renderLanePanel(laneId, close) {
    var lane = laneBy(laneId);
    if (!lane) { panel.hidden = true; return; }
    var label = "lane " + lane.name;
    panel.appendChild(h("div", { "class": "panel-head" }, [h("h2", { text: lane.name }), close]));
    panel.appendChild(field("Name", lane.name, function (v) { lane.name = v; noteEdit(label, "name"); }));
    panel.appendChild(field("Icon", lane.icon, function (v) { lane.icon = v; noteEdit(label, "icon"); }, { list: iconList() }));
    if (lane.kind === "other") {
      var used = M().steps.some(function (s) { return s.lane === lane.id; });
      var others = M().lanes.filter(function (l) { return l.kind === lane.kind; }).length;
      if (!used && others > 1) panel.appendChild(removeButton("Remove this lane", function () {
        M().lanes = M().lanes.filter(function (l) { return l !== lane; });
        change("removed the " + lane.name + " lane");
        S.selected = null;
        afterChange();
      }));
      else panel.appendChild(h("p", { "class": "hint", text: used ? "Move its steps to another lane to remove it." : "" }));
    }
  }

  /* ---------- view mode: what each step did ---------- */
  var RESULT_MARK = { works: "✓", broken: "✕", tried: "•" };
  function outputLink(path) {
    var r = M().repo;
    if (/^https?:\/\//.test(path)) return h("a", { href: path, target: "_blank", rel: "noopener" }, [path]);
    if (r.owner && r.name) {
      return h("a", { href: "https://github.com/" + encodeURIComponent(r.owner) + "/" + encodeURIComponent(r.name) + "/blob/" +
        encodeURIComponent(r.branch) + "/" + path.split("/").map(encodeURIComponent).join("/"), target: "_blank", rel: "noopener" }, [path]);
    }
    return h("code", { text: path });
  }
  function fact(label, value) {
    return value ? h("div", { "class": "fact" }, [h("span", { text: label }), h("p", { text: value })]) : null;
  }
  function editButton(id) {
    return h("button", { type: "button", "class": "btn small", onclick: function () { setMode("edit"); select(id); } }, ["Edit"]);
  }
  function renderStepView(s, close) {
    var key = String(s.n), lane = laneBy(s.lane);
    panel.appendChild(h("div", { "class": "panel-head" }, [h("h2", { text: s.n + " " + s.name }), h("div", { "class": "row" }, [editButton(key), close])]));
    panel.appendChild(h("p", { "class": "who", text: "Done by " + s.who + " (" + (lane ? lane.name : s.lane) + "). Checked by " + (s.check.by || "nobody yet") + "." }));
    [fact("Goes in", s["in"]), fact("Comes out", s.out), fact("How it is checked", s.check.how),
     fact("Claude here is", s.you_or_it), fact("Credited", s.credited)].forEach(function (e) { if (e) panel.appendChild(e); });
    panel.appendChild(h("div", { "class": "run" }, [h("h3", { text: "Run it in Cowork" }), h("p", { "class": "run-text", text: s.run || "No prompt yet." }),
      h("button", { type: "button", "class": "btn", onclick: function () {
        copyText(s.run).then(function () { toast("Copied. Paste it into the Cowork chat, with your fleet folder attached."); });
      } }, ["Copy the prompt"])]));

    var did = h("div", { "class": "did" }, [h("h3", { text: "What it did" })]);
    var groups = WF.runsFor(M(), key);
    if (!groups.length) did.appendChild(h("p", { "class": "hint", text: "No runs recorded yet. Run it in Cowork, then record what happened below." }));
    groups.forEach(function (g) {
      var box = h("div", { "class": "round" + (g.round === currentRound() ? " current" : "") }, [
        h("div", { "class": "round-head", text: "Round " + g.round + (g.runs.length > 1 ? ", " + g.runs.length + " passes" : "") })]);
      g.runs.forEach(function (r) {
        var item = h("div", { "class": "pass p-" + r.result }, [
          h("div", { "class": "pass-head" }, [
            h("span", { "class": "mark", text: RESULT_MARK[r.result] }),
            h("strong", { text: "Pass " + r.pass }), h("span", { "class": "date", text: r.date }),
            h("span", { "class": "res", text: r.result })]),
          r.note ? h("p", { text: r.note }) : null,
          r.outputs.length ? h("ul", { "class": "outs" }, r.outputs.map(function (o) { return h("li", {}, [outputLink(o)]); })) : null,
          h("p", { "class": "chk", text: "Check: " + r.check.result + (r.check.by ? ", by " + r.check.by : "") + (r.check.note ? ". " + r.check.note : "") })
        ]);
        box.appendChild(item);
      });
      did.appendChild(box);
    });
    panel.appendChild(did);

    var note = h("input", { type: "text", placeholder: "What happened, in one line", "aria-label": "Run note" });
    var outs = h("textarea", { rows: 2, placeholder: "What it made: file paths in your fleet repository, one per line", "aria-label": "Outputs" });
    var chk = h("select", { "aria-label": "Check result" }, ["not checked", "pass", "fail"].map(function (o) { return h("option", { value: o }, [o]); }));
    var chkBy = h("input", { type: "text", placeholder: "Checked by", "aria-label": "Checked by" });
    chkBy.value = s.check.by && s.check.by !== "UNSURE" ? s.check.by : "";
    var chkNote = h("input", { type: "text", placeholder: "What the check found", "aria-label": "Check note" });
    function record(result) {
      S.model = WF.recordRun(M(), key, { result: result, note: note.value,
        outputs: outs.value.split("\n").map(function (x) { return x.trim(); }).filter(Boolean),
        check: { by: chkBy.value, result: chk.value, note: chkNote.value } });
      S.viewRound = M().round;
      S.dirty = true;
      resetWalk();
      renderAll();
      toast("Recorded. Press Save to keep it.");
    }
    var pass = M().runs.filter(function (r) { return r.step === key && r.round === M().round; }).length + 1;
    panel.appendChild(h("div", { "class": "record" }, [
      h("h3", { text: "Record a run (round " + M().round + ", pass " + pass + ")" }),
      note, outs, h("div", { "class": "row" }, [chk, chkBy]), chkNote,
      h("div", { "class": "row" }, [
        h("button", { type: "button", "class": "btn ok", disabled: S.readOnly, onclick: function () { record("works"); } }, ["It works"]),
        h("button", { type: "button", "class": "btn bad", disabled: S.readOnly, onclick: function () { record("broken"); } }, ["It broke"]),
        h("button", { type: "button", "class": "btn", disabled: S.readOnly, onclick: function () { record("tried"); } }, ["Tried"])
      ])]));
  }
  function renderSourceView(src, close) {
    panel.appendChild(h("div", { "class": "panel-head" }, [h("h2", { text: src.name }), h("div", { "class": "row" }, [editButton(src.id), close])]));
    [fact("Reached", src.kind), fact("Gives", src.gives)].forEach(function (e) { if (e) panel.appendChild(e); });
    if (src.link && /^https?:\/\//.test(src.link)) panel.appendChild(h("p", {}, [h("a", { href: src.link, target: "_blank", rel: "noopener" }, [src.link])]));
    var users = M().arrows.filter(function (a) { return a.from === src.id; }).map(function (a) {
      var s = stepBy(a.to); return s ? s.n + " " + s.name + (a.label ? " (" + a.label + ")" : "") : a.to;
    });
    if (users.length) panel.appendChild(fact("Feeds", users.join("; ")));
    if (src.unsure.length) panel.appendChild(fact("Still UNSURE", src.unsure.join("; ")));
  }

  /* ---------- adding ---------- */
  function addStep() {
    flushEdits();
    var nums = M().steps.map(function (s) { return parseInt(s.n, 10); }).filter(function (n) { return !isNaN(n); });
    var n = (nums.length ? Math.max.apply(null, nums) : 0) + 1;
    var cols = M().steps.map(function (s) { return s.col; });
    M().steps.push({ n: n, name: "New step", "in": "", out: "", who: "me", check: { by: "UNSURE", how: "" }, run: "",
      state: "not tried", state_date: "", state_note: "", you_or_it: "UNSURE", credited: "UNSURE", mine: false,
      unsure: ["new step: say what it does"], lane: "me", col: (cols.length ? Math.max.apply(null, cols) : -1) + 1 });
    change("added step " + n);
    S.selected = String(n);
    afterChange();
  }
  function addSource() {
    flushEdits();
    var i = M().sources.length + 1, id = "src-source-" + i;
    while (sourceBy(id)) id = "src-source-" + (++i);
    M().sources.push({ id: id, name: "New source", kind: "", link: "", gives: "", icon: "database", unsure: ["new source: name it"] });
    change("added a source");
    S.selected = id;
    afterChange();
  }
  function addLane() {
    flushEdits();
    var i = M().lanes.length, id = "lane-" + i;
    while (laneBy(id)) id = "lane-" + (++i);
    M().lanes.push({ id: id, name: "New lane", kind: "other", icon: "users" });
    change("added a lane");
    S.selected = "lane:" + id;
    afterChange();
  }

  /* ---------- walkthrough ---------- */
  function walkKind() {
    return S.mode === "view" && M().runs.some(function (r) { return r.round === currentRound(); }) ? "runs" : "plan";
  }
  function newWalk() {
    var kind = walkKind();
    var events = kind === "runs" ? WF.runEvents(M(), currentRound()) : WF.walk(M());
    return { kind: kind, events: events, i: 0, playing: false, raf: null, visits: [] };
  }
  function resetWalk() {
    if (S.walk && S.walk.raf) cancelAnimationFrame(S.walk.raf);
    S.walk = null;
    wrapEl.querySelectorAll(".badge.show, .pill.show, .card.hit, .edge.lit").forEach(function (e) { e.classList.remove("show", "hit", "lit"); });
    var dot = wrapEl.querySelector(".dot");
    if (dot) { dot.setAttribute("cx", -20); dot.setAttribute("cy", -20); }
    btn.play.textContent = "\u25b6 Play";
    renderTrace();
  }
  function edgeIndex(ev) {
    for (var i = 0; i < M().arrows.length; i++) if (M().arrows[i].from === ev.from && M().arrows[i].to === ev.to) return i;
    return -1;
  }
  function showVisit(ev) {
    S.walk.visits.push(ev);
    var g = wrapEl.querySelector('.card[data-node="' + cssEsc(ev.node) + '"]');
    if (g) { g.classList.remove("hit"); void g.getBoundingClientRect(); g.classList.add("hit"); }
    var row = (S.walk.kind === "runs" ? WF.runTrace(M(), [ev]) : WF.trace(M(), [ev]))[0];
    var badge = wrapEl.querySelector('.badge[data-badge="' + cssEsc(ev.node) + '"]');
    if (badge && row) {
      var kind = row.result === "fail" ? "fail" : row.warnings.length ? "warn" : row.result === "pass" ? "pass" : "none";
      badge.setAttribute("class", "badge show b-" + kind);
      badge.querySelector("text").textContent = ev.pass > 1 ? String(ev.pass) : { pass: "\u2713", fail: "\u2715", warn: "!", none: "\u2022" }[kind];
    }
    renderTrace();
  }
  function replayMarks() {
    var w = S.walk;
    w.events.slice(0, w.i).forEach(function (ev) {
      if (ev.kind === "edge") {
        var k = edgeIndex(ev), pill = wrapEl.querySelector('.pill[data-pill="' + k + '"]');
        if (pill) pill.classList.add("show");
      }
    });
    var visits = w.visits;
    w.visits = [];
    visits.forEach(showVisit);
  }
  function animateEdge(ev, done) {
    var k = edgeIndex(ev), path = wrapEl.querySelector("#wf-edge-" + k), dot = wrapEl.querySelector(".dot");
    if (!path || !dot) { done(); return; }
    var len = path.getTotalLength(), t0 = null, dur = reduceMotion() ? 1 : 650;
    var color = getComputedStyle(wrapEl.querySelector('.card[data-node="' + cssEsc(ev.from) + '"]') || path).getPropertyValue("--lane") || "";
    dot.style.fill = color.trim() || "";
    path.classList.add("lit");
    function frame(ts) {
      if (!S.walk) return;
      if (t0 === null) t0 = ts;
      var f = Math.min(1, (ts - t0) / dur), pt = path.getPointAtLength(len * f);
      dot.setAttribute("cx", pt.x); dot.setAttribute("cy", pt.y);
      if (f < 1) { S.walk.raf = requestAnimationFrame(frame); return; }
      var pill = wrapEl.querySelector('.pill[data-pill="' + k + '"]');
      if (pill) pill.classList.add("show");
      path.classList.remove("lit");
      done();
    }
    S.walk.raf = requestAnimationFrame(frame);
  }
  function reduceMotion() { return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches; }
  function advance(untilVisit, onDone) {
    var w = S.walk;
    if (!w || w.i >= w.events.length) { onDone && onDone(true); return; }
    var ev = w.events[w.i++];
    if (ev.kind === "edge") {
      animateEdge(ev, function () { advance(untilVisit, onDone); });
    } else {
      showVisit(ev);
      if (untilVisit) { onDone && onDone(w.i >= w.events.length); return; }
      setTimeout(function () { if (S.walk === w && w.playing) advance(false, onDone); }, reduceMotion() ? 50 : 420);
    }
  }
  function togglePlay() {
    if (S.walk && S.walk.playing) { S.walk.playing = false; btn.play.textContent = "\u25b6 Play"; return; }
    if (!S.walk || S.walk.i >= S.walk.events.length) { resetWalk(); S.walk = newWalk(); }
    S.walk.playing = true;
    btn.play.textContent = "\u275a\u275a Pause";
    (function go() {
      advance(true, function (finished) {
        if (!S.walk) return;
        if (finished) { S.walk.playing = false; btn.play.textContent = "\u25b6 Play again"; return; }
        if (S.walk.playing) setTimeout(go, reduceMotion() ? 50 : 420);
      });
    })();
  }
  function stepOnce() {
    if (S.walk && S.walk.playing) { S.walk.playing = false; btn.play.textContent = "\u25b6 Play"; }
    if (!S.walk || S.walk.i >= S.walk.events.length) { resetWalk(); S.walk = newWalk(); }
    advance(true, function () {
      var v = S.walk && S.walk.visits[S.walk.visits.length - 1];
      if (v) select(v.node);
    });
  }

  /* ---------- trace ---------- */
  function renderTrace() {
    traceEl.innerHTML = "";
    var kind0 = S.walk ? S.walk.kind : walkKind();
    traceEl.appendChild(h("div", { "class": "trace-head" }, [
      h("h2", { text: "Debug trace" }),
      h("span", { "class": "trace-kind", text: kind0 === "runs" ? "Round " + currentRound() + ": what happened" : "Walkthrough (planned checks)" })]));
    var visits = S.walk ? S.walk.visits : [];
    var rows;
    if (kind0 === "runs") {
      rows = WF.runTrace(M(), S.walk ? visits : WF.runEvents(M(), currentRound()));
    } else {
      if (!visits.length) {
        traceEl.appendChild(h("p", { "class": "hint", text: S.mode === "view"
          ? "No runs recorded in this round yet. Press Play to walk through the plan, or open a step and record a run."
          : "Press Play or Step. Each step's check appears here as the walkthrough reaches it." }));
        return;
      }
      rows = WF.trace(M(), visits);
    }
    var list = h("ol", { "class": "trace-rows" });
    rows.forEach(function (r) {
      var kind = r.result === "fail" ? "fail" : r.warnings.length ? "warn" : r.result === "pass" ? "pass" : "none";
      var by = String(r.check.by || "");
      var check = r.source || !by || by.toUpperCase() === "UNSURE" ? "" : "checked by " + by + (r.check.how ? ": " + r.check.how : "");
      var li = h("li", { "class": "trace-row r-" + kind, tabindex: "0", style: "--lane:" + WF.laneColor(M(), r.lane) }, [
        h("span", { "class": "mark", text: { pass: "\u2713", fail: "\u2715", warn: "!", none: "\u2022" }[kind] }),
        h("span", { "class": "t-step", text: (r.pass > 1 ? "\u21ba " : "") + (r.source ? r.name : r.node + " " + r.name) + (r.pass > 1 ? " (pass " + r.pass + ")" : "") }),
        h("span", { "class": "t-out", text: (r.date ? r.date + "  " : "") + (r.out ? "out: " + r.out : "") }),
        h("span", { "class": "t-check", text: [r.note || "", check].concat(r.warnings).filter(Boolean).join(" \u00b7 ") })
      ]);
      li.addEventListener("click", function () { select(r.node); });
      list.appendChild(li);
    });
    traceEl.appendChild(list);
  }

  /* ---------- change log ---------- */
  function renderLog() {
    logEl.innerHTML = "";
    logEl.appendChild(h("h2", { text: "Change log" }));
    var items = M().changes.slice(0, 40);
    if (!items.length) { logEl.appendChild(h("p", { "class": "hint", text: "No changes yet." })); return; }
    logEl.appendChild(h("ul", {}, items.map(function (c) {
      return h("li", {}, [h("span", { "class": "date", text: c.date }), " ", c.what]);
    })));
  }

  /* ---------- saving ---------- */
  async function save() {
    flushEdits();
    if (S.level < 2 || S.readOnly || S.saving) { renderStatus(); return false; }
    S.saving = true;
    statusEl.textContent = "saving\u2026";
    stash();
    try {
      await S.artifact.publish(pageHtml(M()));
      S.dirty = false;
      return true;
    } catch (e) {
      var code = e && e.code;
      if (code === "conflict") { toast("Reloaded to a newer version."); }
      else if (code === "not_writer" || code === "not_granted") { S.readOnly = true; renderAll(); toast("You can look at this map but not change it."); }
      else toast("Not saved: " + ((e && e.message) || code || "unknown error"));
      return false;
    } finally { S.saving = false; renderStatus(); }
  }
  function copyMap() {
    flushEdits();
    copyText(WF.serializeData(M())).then(function (ok) {
      toast(ok ? "Copied. Paste it into the chat and ask Claude to keep it." : "Could not copy. Select the change log and copy by hand.");
    });
  }


  /* ---------- the chat box: say what to change ---------- */
  var CHAT_OFF = ["not_granted", "sampling_disabled", "not_declared", "capability_disabled", "capability_removed"];
  var CHAT_COPY = {
    rate_limited: "Claude is busy for you right now. Wait a minute, then try again.",
    session_expired: "Sign in to Claude again, then try again.",
    invalid_json: "Claude's answer could not be read. Try again, or say it another way.",
    refused: "Claude would not make that change. Say it another way.",
    empty_completion: "Claude gave no answer. Say it another way.",
    prompt_too_large: "This map is too big to send to Claude. Ask in the Cowork chat instead.",
    cancelled: "Stopped."
  };
  var chatInput = null, chatLog = null, chatSend = null, chatMic = null, dictBase = "", dictFinal = "";

  function chatAvailable() { return !!S.sample && !S.chat.off && !S.readOnly; }

  function renderChat() {
    chatEl.hidden = !chatAvailable();
    if (chatEl.hidden) return;
    if (!chatInput) buildChat();
    renderChatLog();
    var busy = !!S.chat.busy;
    chatSend.textContent = busy ? "Stop" : "Go";
    chatSend.classList.toggle("stop", busy);
    chatMic.hidden = !S.dictation;
  }

  function buildChat() {
    chatLog = h("div", { "class": "chat-log", "aria-live": "polite" });
    chatInput = h("textarea", { rows: 1, placeholder: "Tell the map what to change: “move step 4 to the Me lane”, “record that step 2 worked”",
      "aria-label": "Tell the map what to change" });
    chatInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendChat(); }
    });
    chatInput.addEventListener("input", function () {
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(140, chatInput.scrollHeight) + "px";
    });
    chatSend = h("button", { type: "button", "class": "btn btn-go", onclick: function () {
      if (S.chat.busy) S.chat.busy.abort(); else sendChat();
    } }, ["Go"]);
    chatMic = h("button", { type: "button", "class": "btn mic", hidden: true, title: "Say it instead of typing",
      "aria-label": "Say it instead of typing", "aria-pressed": "false", onclick: toggleMic }, ["🎙"]);
    chatEl.appendChild(chatLog);
    chatEl.appendChild(h("div", { "class": "chat-form" }, [chatInput, chatMic, chatSend]));
    chatEl.appendChild(h("p", { "class": "chat-cost", text: "Uses your Claude plan. Small edits are free in the forms." }));
  }

  function chatItem(item) {
    var box = h("div", { "class": "chat-item " + item.role + (item.status ? " " + item.status : "") });
    if (item.role === "user") { box.appendChild(h("p", { text: item.text })); return box; }
    if (item.text) box.appendChild(h("p", { text: item.text }));
    if (item.lines && item.lines.length) {
      box.appendChild(h("ul", { "class": "plan" }, item.lines.map(function (l) { return h("li", { text: l }); })));
    }
    if (item.failed && item.failed.length) {
      box.appendChild(h("ul", { "class": "plan failed" }, item.failed.map(function (l) { return h("li", { text: "Could not: " + l }); })));
    }
    if (item.status === "proposed" && item.live) {
      box.appendChild(h("div", { "class": "row" }, [
        h("button", { type: "button", "class": "btn btn-save", onclick: function () { applyItem(item); } }, ["Apply"]),
        h("button", { type: "button", "class": "btn", onclick: function () { item.status = "discarded"; renderChat(); } }, ["Discard"])
      ]));
    } else if (item.status === "applied") {
      box.appendChild(h("p", { "class": "hint", text: "Applied." }));
    } else if (item.status === "discarded" || item.status === "proposed") {
      box.appendChild(h("p", { "class": "hint", text: "Not applied." }));
    }
    return box;
  }

  function renderChatLog() {
    chatLog.innerHTML = "";
    var items = S.chat.items.slice(-12);
    chatLog.hidden = !items.length && !S.chat.busy;
    items.forEach(function (it) { chatLog.appendChild(chatItem(it)); });
    if (S.chat.busy) chatLog.appendChild(h("div", { "class": "chat-item claude thinking" }, [h("p", { text: "Thinking…" })]));
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  async function sendChat() {
    var text = chatInput.value.trim();
    if (!text || S.chat.busy || !chatAvailable()) return;
    flushEdits();
    if (S.dictation && chatMic.getAttribute("aria-pressed") === "true") {
      try { await S.dictation.stop(); } catch (e) { /* none */ }
      text = chatInput.value.trim() || text;
    }
    var turns = WF.chatTurns(M(), S.chat.turns, text);
    S.chat.turns.push({ role: "user", content: text });
    S.chat.items.push({ role: "user", text: text });
    chatInput.value = "";
    chatInput.style.height = "";
    var ctl = new AbortController();
    S.chat.busy = ctl;
    renderChat();
    try {
      var reply = WF.readReply(await S.sample.json(turns, { signal: ctl.signal, cache: false, modelTier: "quick" }));
      var draft = WF.applyChanges(M(), reply.changes);
      S.chat.turns.push({ role: "assistant", content: JSON.stringify({ reply: reply.reply, changes: reply.changes }) });
      S.chat.items.push({ role: "claude", text: reply.reply || (draft.done.length ? "" : "No change."), changes: reply.changes,
        lines: draft.done, failed: draft.failed.map(function (f) { return f.why; }),
        status: draft.done.length ? "proposed" : "", live: true });
    } catch (e) {
      var code = e && e.code;
      if (CHAT_OFF.indexOf(code) >= 0) {
        S.chat.off = true;
        toast("Claude is not available on this page. Use the forms, or ask in the Cowork chat.");
      } else {
        S.chat.items.push({ role: "claude", status: "error", text: CHAT_COPY[code] || "Something went wrong reaching Claude. Try again." });
      }
    } finally {
      if (S.chat.busy === ctl) S.chat.busy = null;
      renderChat();
      if (chatAvailable()) chatInput.focus();
    }
  }

  function applyItem(item) {
    flushEdits();
    var r = WF.applyChanges(M(), item.changes);
    item.status = r.done.length ? "applied" : "discarded";
    item.lines = r.done;
    item.failed = r.failed.map(function (f) { return f.why; });
    item.live = false;
    if (!r.done.length) { renderChat(); toast("Nothing could be applied to the map as it is now."); return; }
    S.model = r.model;
    S.dirty = true;
    if (r.done.some(function (l) { return /^ran step|^started round/.test(l); })) S.viewRound = M().round;
    if (S.selected && S.selected.indexOf("lane:") !== 0 && !stepBy(S.selected) && !sourceBy(S.selected)) S.selected = null;
    resetWalk();
    renderAll();
    toast("Applied. Press Save to keep it.");
  }

  function toggleMic() {
    var d = S.dictation;
    if (!d) return;
    if (chatMic.getAttribute("aria-pressed") === "true") { d.stop().catch(function () { /* none */ }); return; }
    dictBase = chatInput.value ? chatInput.value.replace(/\s*$/, " ") : "";
    dictFinal = "";
    d.start().catch(function (e) {
      if (e && e.code === "not_granted") { S.dictation = null; renderChat(); }
      else toast("The microphone did not start. Type instead, or try again.");
    });
  }
  function wireDictation(d) {
    d.onPartial(function (p) { chatInput.value = dictBase + dictFinal + (p && p.text ? p.text : ""); });
    d.onFinal(function (p) { if (p && p.text) dictFinal += p.text + " "; chatInput.value = dictBase + dictFinal; });
    d.onState(function (st) {
      var on = !!st && st.state === "listening";
      chatMic.setAttribute("aria-pressed", on ? "true" : "false");
      chatMic.classList.toggle("listening", on);
    });
  }

  /* ---------- everything ---------- */
  function renderAll() {
    renderModes();
    renderHeader(); renderChat(); renderBanner(); renderProblems(); renderCanvas(); renderTrace(); renderPanel(); renderLog(); renderStatus();
  }

  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") { e.preventDefault(); save(); }
    if (e.key === "Escape" && link) { endLink(); return; }
    if (e.key === "Escape" && S.selected) select(null);
  });
  window.addEventListener("beforeunload", function (e) {
    if (S.level >= 2 && !S.saving && (S.dirty || Object.keys(S.edits).length)) { e.preventDefault(); e.returnValue = ""; }
  });

  renderToolbar();
  var back = unstash();
  if (back && back.selected) S.selected = back.selected;
  if (back && (back.mode === "view" || back.mode === "edit")) S.mode = back.mode;
  if (back && back.round) S.viewRound = back.round;
  if (back && back.chat && Array.isArray(back.chat.turns) && Array.isArray(back.chat.items)) {
    S.chat.turns = back.chat.turns;
    S.chat.items = back.chat.items;
  }
  renderAll();
  if (back && back.scroll) wrapEl.scrollLeft = back.scroll;

  function withTimeout(p, ms) {
    return Promise.race([p, new Promise(function (r) { setTimeout(function () { r(null); }, ms); })]);
  }
  (async function connect() {
    var c = window.claude;
    if (!c || typeof c.use !== "function") { renderAll(); return; }
    function use(name) { return withTimeout(Promise.resolve().then(function () { return c.use(name); }), 10000).catch(function () { return null; }); }
    var got = await Promise.all([use("artifact"), use("sample"), use("dictation")]);
    S.artifact = got[0];
    S.sample = typeof got[1] === "function" && typeof got[1].json === "function" ? got[1] : null;
    if (S.artifact) S.level = 2;
    renderAll();
    if (got[2] && chatMic) {
      try { wireDictation(got[2]); S.dictation = got[2]; } catch (e) { S.dictation = null; }
      renderChat();
    }
  })();
})(WF);
