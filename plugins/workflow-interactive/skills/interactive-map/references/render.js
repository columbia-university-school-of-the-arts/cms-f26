/* Layout and drawing: pure functions of the model that return SVG text.
   The tests run them under Node; ui.js puts the text on the page. */
(function (WF) {
  "use strict";

  var G = { head: 132, lane: 118, colW: 140, card: 60, padX: 34, top: 14, off: 0.8 };
  var KIND_COLOR = { sources: "#0f766e", me: "#c2410c", claude: "#7c3aed", other: "#475569" };
  var EXTRA = ["#be185d", "#1d4ed8", "#4d7c0f", "#b45309", "#0e7490", "#9333ea"];

  function laneColor(model, laneId) {
    var lanes = model.lanes, others = 0;
    for (var i = 0; i < lanes.length; i++) {
      var l = lanes[i];
      if (/^#[0-9a-fA-F]{3,8}$/.test(l.color || "")) { if (l.id === laneId) return l.color; continue; }
      var first = lanes.filter(function (x) { return x.kind === l.kind; })[0] === l;
      var c = first ? KIND_COLOR[l.kind] : EXTRA[others++ % EXTRA.length];
      if (l.id === laneId) return c;
    }
    return KIND_COLOR.other;
  }

  function layout(model) {
    var laneIndex = {};
    model.lanes.forEach(function (l, i) { laneIndex[l.id] = i; });
    var nodes = {}, taken = {};
    function place(id, laneId, col) {
      var li = laneIndex[laneId] === undefined ? model.lanes.length - 1 : laneIndex[laneId];
      var c = Math.max(-G.off, col);
      function busy(v) { return (taken[li] || []).some(function (t) { return Math.abs(t - v) < 0.75; }); }
      while (busy(c)) c += 0.5;
      (taken[li] = taken[li] || []).push(c);
      nodes[id] = { x: G.head + G.padX + (c + G.off) * G.colW, y: li * G.lane + G.top, w: G.card, h: G.card, lane: li, col: c };
    }
    var steps = model.steps.slice().sort(function (a, b) { return a.col - b.col; });
    steps.forEach(function (s) { place(String(s.n), s.lane, s.col); });
    var colOf = {};
    model.steps.forEach(function (s) { colOf[String(s.n)] = nodes[String(s.n)].col; });
    model.sources.forEach(function (src, i) {
      var col = typeof src.col === "number" ? src.col : null;
      if (col === null) {
        var targets = model.arrows.filter(function (a) { return a.from === src.id && colOf[a.to] !== undefined; })
          .map(function (a) { return colOf[a.to]; });
        col = targets.length ? Math.min.apply(null, targets) - 0.6 : i;
      }
      place(src.id, model.lanes[0].id, col);
    });
    var maxX = 0;
    Object.keys(nodes).forEach(function (k) { maxX = Math.max(maxX, nodes[k].x + G.card); });
    return { nodes: nodes, width: Math.max(maxX + 80, 640), height: model.lanes.length * G.lane, g: G };
  }

  /* A fetched icon is rebuilt from an allow list: only these shapes, only
     geometry attributes, values limited to numbers and path letters. Anything
     else in the string is dropped, never passed through. */
  var SHAPES = ["path", "circle", "rect", "line", "polyline", "polygon", "ellipse"];
  var GEOMETRY = ["d", "cx", "cy", "r", "rx", "ry", "x", "y", "x1", "y1", "x2", "y2", "width", "height", "points"];
  function safeSvg(text) {
    var out = [], el = /<\s*([a-zA-Z]+)\b([^<>]*?)\/?\s*>/g, m;
    while ((m = el.exec(String(text)))) {
      var tag = m[1].toLowerCase();
      if (SHAPES.indexOf(tag) < 0) continue;
      var attrs = [], at = /([a-zA-Z0-9-]+)\s*=\s*"([^"]*)"/g, a;
      while ((a = at.exec(m[2]))) {
        var name = a[1].toLowerCase(), value = a[2];
        if (GEOMETRY.indexOf(name) >= 0 && /^[0-9eE.,\s+\-MmLlHhVvCcSsQqTtAaZz]*$/.test(value)) attrs.push(name + '="' + value + '"');
      }
      if (attrs.length) out.push("<" + tag + " " + attrs.join(" ") + "/>");
    }
    return out.join("");
  }

  function iconMarkup(model, name, x, y, size, color) {
    var custom = model.icons && model.icons[name];
    var brand = WF_ICONS.brand[name], generic = WF_ICONS.generic[name];
    if (custom && custom.path) brand = { path: custom.path, color: /^#[0-9a-fA-F]{3,8}$/.test(custom.color || "") ? custom.color : color };
    else if (custom && typeof custom.svg === "string") { var safe = safeSvg(custom.svg); if (safe) generic = { svg: safe }; }
    if (brand) {
      var k = size / 24, r = size / 2 + 5;
      return '<g class="ico brand"><circle cx="' + (x + size / 2) + '" cy="' + (y + size / 2) + '" r="' + r +
        '" class="chip"/><g transform="translate(' + x + ',' + y + ') scale(' + k + ')"><path d="' + WF.esc(brand.path) +
        '" fill="' + WF.esc(brand.color || color) + '"/></g></g>';
    }
    if (!generic) generic = WF_ICONS.generic.workflow;
    return '<g class="ico" transform="translate(' + x + ',' + y + ') scale(' + size / 24 + ')" fill="none" stroke="' +
      color + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + generic.svg + "</g>";
  }

  function edgePath(L, a) {
    var f = L.nodes[a.from], t = L.nodes[a.to];
    if (!f || !t) return null;
    var S = L.g.card;
    var back = a.from.indexOf("src-") !== 0 && t.x <= f.x;
    if (back) {
      var x1 = f.x + S / 2, y1 = f.y + S, x2 = t.x + S / 2, y2 = t.y + S, dip = Math.max(y1, y2) + 52;
      return { d: "M" + x1 + " " + y1 + " C" + x1 + " " + dip + " " + x2 + " " + dip + " " + x2 + " " + y2,
        mid: [(x1 + x2) / 2, dip - 12], back: true };
    }
    var sx = f.x + S, sy = f.y + S / 2, ex = t.x, ey = t.y + S / 2, dx = Math.max(36, Math.abs(ex - sx) / 2);
    return { d: "M" + sx + " " + sy + " C" + (sx + dx) + " " + sy + " " + (ex - dx) + " " + ey + " " + ex + " " + ey,
      mid: [(sx + ex) / 2, (sy + ey) / 2 - 8], back: false };
  }

  function wrap(text, max) {
    var words = String(text).split(/\s+/), lines = [""];
    words.forEach(function (w) {
      var cur = lines[lines.length - 1];
      if ((cur + " " + w).trim().length > max && cur) lines.push(w); else lines[lines.length - 1] = (cur + " " + w).trim();
    });
    if (lines.length > 2) lines = [lines[0], lines.slice(1).join(" ").slice(0, max - 1) + "…"];
    return lines;
  }

  function renderSvg(model, L, opts) {
    var counts = (opts && opts.counts) || {};
    var S = L.g.card, out = [];
    out.push('<svg xmlns="http://www.w3.org/2000/svg" class="canvas" viewBox="0 0 ' + L.width + " " + L.height +
      '" width="' + L.width + '" height="' + L.height + '" role="img" aria-label="' + WF.esc(model.title) + '">');
    out.push('<defs><marker id="wf-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="arrowhead"/></marker></defs>');
    model.lanes.forEach(function (l, i) {
      var y = i * L.g.lane, c = laneColor(model, l.id);
      out.push('<g class="lane" data-lane="' + WF.esc(l.id) + '" style="--lane:' + c + '">');
      out.push('<rect class="lane-band" x="0" y="' + y + '" width="' + L.width + '" height="' + L.g.lane + '"/>');
      out.push('<rect class="lane-head" x="0" y="' + y + '" width="' + L.g.head + '" height="' + L.g.lane + '"/>');
      out.push('<rect class="lane-bar" x="0" y="' + y + '" width="6" height="' + L.g.lane + '"/>');
      out.push('<line class="lane-rule" x1="0" x2="' + L.width + '" y1="' + (y + L.g.lane) + '" y2="' + (y + L.g.lane) + '"/>');
      out.push(iconMarkup(model, l.icon, 18, y + 16, 22, c));
      wrap(l.name, 14).forEach(function (line, j) {
        out.push('<text class="lane-name" x="18" y="' + (y + 60 + j * 15) + '">' + WF.esc(line) + "</text>");
      });
      out.push("</g>");
    });
    model.arrows.forEach(function (a, i) {
      var p = edgePath(L, a);
      if (!p) return;
      out.push('<path class="edge' + (p.back || a.loop ? " loop" : "") + (a.unsure ? " unsure" : "") + '" id="wf-edge-' + i +
        '" data-edge="' + i + '" d="' + p.d + '" marker-end="url(#wf-arrow)"/>');
      if (a.label) {
        var w = Math.min(150, 14 + a.label.length * 6.2);
        out.push('<g class="pill" data-pill="' + i + '"><rect x="' + (p.mid[0] - w / 2) + '" y="' + (p.mid[1] - 9) +
          '" width="' + w + '" height="17" rx="8.5"/><text x="' + p.mid[0] + '" y="' + (p.mid[1] + 3.5) + '">' +
          WF.esc(a.label) + "</text></g>");
      }
    });
    function card(id, label, sub, laneId, icon, isSource, extra) {
      var n = L.nodes[id], c = laneColor(model, laneId), x = n.x, y = n.y;
      var shape = isSource
        ? "M" + (x + S / 2) + " " + y + "H" + (x + S - 9) + "a9 9 0 0 1 9 9v" + (S - 18) + "a9 9 0 0 1-9 9H" + (x + S / 2) +
          "a" + S / 2 + " " + S / 2 + " 0 0 1 0-" + S + "z"
        : "M" + (x + 9) + " " + y + "H" + (x + S - 9) + "a9 9 0 0 1 9 9v" + (S - 18) + "a9 9 0 0 1-9 9H" + (x + 9) +
          "a9 9 0 0 1-9-9V" + (y + 9) + "a9 9 0 0 1 9-9z";
      out.push('<g class="card' + (isSource ? " source" : " step") + (extra.unsure ? " is-unsure" : "") + '" data-node="' +
        WF.esc(id) + '" style="--lane:' + c + '" tabindex="0" role="button" aria-label="' + WF.esc(label) + '">');
      out.push('<path class="card-body" d="' + shape + '"/><path class="card-flash" d="' + shape + '"/>');
      out.push(iconMarkup(model, icon, x + S / 2 - 15, y + S / 2 - 15, 30, c));
      if (!isSource) out.push('<circle class="port in" cx="' + x + '" cy="' + (y + S / 2) + '" r="4.5"/>');
      out.push('<circle class="port out" cx="' + (x + S) + '" cy="' + (y + S / 2) + '" r="4.5"/>');
      out.push('<circle class="port-hit" cx="' + (x + S) + '" cy="' + (y + S / 2) + '" r="12"><title>Drag to another card to add an arrow</title></circle>');
      if (extra.state) out.push('<circle class="state s-' + extra.state.replace(/\s/g, "-") + '" cx="' + (x + 8) + '" cy="' + (y + S - 8) + '" r="4"/>');
      if (extra.runs) out.push('<g class="runs-pill"><rect x="' + (x + S - 20) + '" y="' + (y + S - 9) + '" width="28" height="15" rx="7.5"/>' +
        '<text x="' + (x + S - 6) + '" y="' + (y + S + 2) + '">\u00d7' + extra.runs + "</text></g>");
      if (extra.mine) out.push('<text class="mine" x="' + (x - 7) + '" y="' + (y + 5) + '">★</text>');
      out.push('<g class="badge" data-badge="' + WF.esc(id) + '"><circle cx="' + (x + S - 1) + '" cy="' + (y + 1) +
        '" r="9.5"/><text x="' + (x + S - 1) + '" y="' + (y + 5) + '"></text></g>');
      wrap(label, 18).forEach(function (line, j) {
        out.push('<text class="card-label" x="' + (x + S / 2) + '" y="' + (y + S + 15 + j * 13) + '">' + WF.esc(line) + "</text>");
      });
      if (sub) out.push('<text class="card-sub" x="' + (x + S / 2) + '" y="' + (y - 5) + '">' + WF.esc(sub) + "</text>");
      out.push("</g>");
    }
    model.sources.forEach(function (s) {
      card(s.id, s.name, s.kind, model.lanes[0].id, s.icon, true, { unsure: s.unsure.length > 0 });
    });
    model.steps.forEach(function (s) {
      var unsure = s.unsure.length > 0 || /UNSURE/.test(s.who + s.check.by + s.you_or_it + s.credited);
      card(String(s.n), s.n + " " + s.name, "", s.lane, s.icon, false, { unsure: unsure, state: s.state, mine: s.mine, runs: counts[String(s.n)] || 0 });
    });
    out.push('<circle class="dot" r="6" cx="-20" cy="-20"/>');
    out.push("</svg>");
    return out.join("");
  }

  WF.G = G;
  WF.laneColor = laneColor;
  WF.layout = layout;
  WF.renderSvg = renderSvg;
  WF.edgePath = edgePath;
  WF.iconMarkup = iconMarkup;
  WF.safeSvg = safeSvg;
})(WF);
