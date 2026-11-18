/* The page's core: data, walkthrough, trace, rebuild, and Git. No DOM here,
   so the tests run it under Node. Everything lives in one object, WF. */
var WF = (function () {
  "use strict";

  var DEFAULT_LANES = [
    { id: "sources", name: "Sources", kind: "sources", icon: "database" },
    { id: "me", name: "Me", kind: "me", icon: "user" },
    { id: "claude", name: "Claude", kind: "claude", icon: "sparkles" },
    { id: "other", name: "Someone or a script", kind: "other", icon: "cog" }
  ];
  var LANE_KINDS = ["sources", "me", "claude", "other"];
  var STATES = ["not tried", "tried", "works", "broken"];
  var KIND_ICON = { sources: "database", me: "user", claude: "sparkles", other: "cog" };
  var SOURCE_ICON = { "api": "globe", "download": "download", "by hand": "user", "someone else": "users" };
  var STEP_WORDS = [
    [/gather|collect|download|fetch|scrape|pull/i, "download"],
    [/tag|label|code|classif/i, "tag"],
    [/close.?read|read|annotat/i, "book-open"],
    [/write|draft|essay|argument/i, "pen-line"],
    [/compar|contrast|diff/i, "git-compare"],
    [/search|find|look up|query/i, "search"],
    [/edit|cut|trim|assembl/i, "scissors"],
    [/interview|record|listen/i, "mic"],
    [/transcri/i, "file-text"],
    [/watch|screen|view/i, "tv"],
    [/chart|plot|graph|visuali|map/i, "chart-column"],
    [/note/i, "notebook-pen"],
    [/publish|post|share|send/i, "send"],
    [/photo|image|frame|still/i, "image"],
    [/sort|filter|select|choose/i, "filter"],
    [/check|verify|review/i, "list-checks"],
    [/cite|quote/i, "quote"]
  ];

  function str(v) { return v === null || v === undefined ? "" : String(v); }
  function arr(v) {
    if (Array.isArray(v)) return v.map(str).filter(function (x) { return x !== ""; });
    return v === null || v === undefined || v === "" ? [] : [str(v)];
  }
  function isObj(v) { return v !== null && typeof v === "object" && !Array.isArray(v); }
  function slug(t) {
    var s = str(t).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48);
    return s.replace(/-+$/, "") || "workflow";
  }
  function clone(v) { return JSON.parse(JSON.stringify(v)); }
  function low(v) { return str(v).trim().toLowerCase(); }

  function guessIcon(name, kind) {
    if (kind && SOURCE_ICON[kind]) return SOURCE_ICON[kind];
    for (var i = 0; i < STEP_WORDS.length; i++) if (STEP_WORDS[i][0].test(str(name))) return STEP_WORDS[i][1];
    return kind === undefined ? "workflow" : "database";
  }

  function laneForWho(who, lanes) {
    var w = low(who), work = lanes.filter(function (l) { return l.kind !== "sources"; });
    function byKind(k) { return work.filter(function (l) { return l.kind === k; })[0]; }
    var hit = (w === "me" && byKind("me")) || (w === "claude" && byKind("claude")) ||
      work.filter(function (l) { return low(l.name) === w && w !== ""; })[0] || byKind("other") ||
      work[work.length - 1];
    return hit ? hit.id : "other";
  }

  function whoForLane(lane, currentWho) {
    if (lane.kind === "me") return "me";
    if (lane.kind === "claude") return "Claude";
    var c = low(currentWho);
    return c === "a script" || c === "someone else" ? c : "someone else";
  }

  function normLanes(raw) {
    var lanes = (Array.isArray(raw) && raw.length ? raw : clone(DEFAULT_LANES)).filter(isObj).map(function (l) {
      var kind = LANE_KINDS.indexOf(l.kind) >= 0 ? l.kind : "other";
      var id = str(l.id) || slug(l.name);
      return Object.assign({}, l, { id: id, name: str(l.name) || id, kind: kind, icon: str(l.icon) || KIND_ICON[kind] });
    });
    var src = lanes.filter(function (l) { return l.kind === "sources"; })[0] || clone(DEFAULT_LANES[0]);
    var rest = lanes.filter(function (l) { return l.kind !== "sources"; });
    if (!rest.length) rest = clone(DEFAULT_LANES.slice(1));
    return [src].concat(rest);
  }

  function normalize(data) {
    var d = isObj(data) ? data : {};
    var m = Object.assign({}, d), problems = [];
    m.title = str(d.title) || "My workflow";
    m.question = str(d.question);
    m.begun = str(d.begun);
    m.id = d.id ? slug(d.id) : slug(m.title);
    m.kind = str(d.kind);
    var r = isObj(d.repo) ? d.repo : {};
    m.repo = Object.assign({}, r, { owner: str(r.owner), name: str(r.name), branch: str(r.branch) || "main" });
    var g = isObj(d.git) ? d.git : {};
    m.git = {
      pulled: str(g.pulled),
      committed: Math.max(0, Number(g.committed) || 0),
      pending: (Array.isArray(g.pending) ? g.pending : []).filter(isObj).map(function (p) {
        return { message: str(p.message), date: str(p.date), changes: arr(p.changes), snapshot: isObj(p.snapshot) ? p.snapshot : null };
      })
    };
    m.icons = isObj(d.icons) ? d.icons : {};
    m.lanes = normLanes(d.lanes);
    var laneIds = {};
    m.lanes.forEach(function (l) { laneIds[l.id] = l; });

    m.sources = (Array.isArray(d.sources) ? d.sources : []).filter(isObj).map(function (s) {
      var id = str(s.id);
      if (id.indexOf("src-") !== 0) id = "src-" + slug(id || s.name);
      return Object.assign({}, s, {
        id: id, name: str(s.name) || id.slice(4), kind: str(s.kind), link: str(s.link), gives: str(s.gives),
        icon: str(s.icon) || guessIcon(s.name, str(s.kind) || "other"), unsure: arr(s.unsure)
      });
    });

    var seen = {};
    m.steps = (Array.isArray(d.steps) ? d.steps : []).filter(isObj).map(function (s, i) {
      var c = s.check, check;
      if (isObj(c)) check = Object.assign({}, c, { by: str(c.by), how: str(c.how) });
      else check = { by: str(c), how: "" };
      var n = s.n === undefined || s.n === null || s.n === "" ? String(i + 1) : s.n;
      var key = String(n);
      if (seen[key]) problems.push("Two steps are numbered " + key + ".");
      seen[key] = true;
      var lane = laneIds[str(s.lane)] && laneIds[str(s.lane)].kind !== "sources" ? str(s.lane) : laneForWho(s.who, m.lanes);
      return Object.assign({}, s, {
        n: typeof n === "number" ? n : str(n), name: str(s.name), "in": str(s["in"]), out: str(s.out),
        who: str(s.who) || "UNSURE", check: check, run: str(s.run),
        state: STATES.indexOf(s.state) >= 0 ? s.state : "not tried",
        state_date: str(s.state_date), state_note: str(s.state_note),
        you_or_it: str(s.you_or_it) || "UNSURE", credited: str(s.credited) || "UNSURE",
        mine: s.mine === true, unsure: arr(s.unsure), lane: lane,
        col: typeof s.col === "number" && isFinite(s.col) ? s.col : i,
        icon: str(s.icon) || guessIcon(s.name)
      });
    });

    var nodes = {};
    m.sources.forEach(function (s) { nodes[s.id] = true; });
    m.steps.forEach(function (s) { nodes[String(s.n)] = true; });
    m.arrows = (Array.isArray(d.arrows) ? d.arrows : []).filter(isObj).map(function (a) {
      var o = Object.assign({}, a, { from: str(a.from), to: str(a.to), loop: a.loop === true, unsure: a.unsure === true, label: str(a.label) });
      if (!nodes[o.from] || !nodes[o.to]) {
        problems.push("The arrow from " + o.from + " to " + o.to + " joins a step or source that is not on the map.");
      }
      return o;
    });
    m.changes = (Array.isArray(d.changes) ? d.changes : []).map(function (c) {
      return isObj(c) ? Object.assign({}, c, { date: str(c.date), what: str(c.what) }) : { date: "", what: str(c) };
    });
    m.problems = problems;
    return m;
  }

  function parse(text) {
    try { return { model: normalize(JSON.parse(text)) }; }
    catch (e) {
      return { error: "The map's data has an error (" + str(e && e.message) + "). Ask Claude to fix the JSON block." };
    }
  }

  function stripInternal(v) {
    if (Array.isArray(v)) return v.map(stripInternal);
    if (!isObj(v)) return v;
    var o = {};
    Object.keys(v).forEach(function (k) { if (k !== "problems" && k.charAt(0) !== "_") o[k] = stripInternal(v[k]); });
    return o;
  }

  function serializeData(model) {
    return JSON.stringify(stripInternal(model), null, 2).replace(/<\//g, "<\\/");
  }

  /* ---------- walkthrough ---------- */

  function stepKey(s) { return String(s.n); }

  function order(model) {
    var steps = model.steps.slice().sort(function (a, b) { return a.col - b.col; });
    var keys = steps.map(stepKey), isStep = {};
    keys.forEach(function (k) { isStep[k] = true; });
    var indeg = {}, out = {};
    keys.forEach(function (k) { indeg[k] = 0; out[k] = []; });
    model.arrows.forEach(function (a) {
      if (isStep[a.from] && isStep[a.to] && !a.loop && a.from !== a.to) { indeg[a.to]++; out[a.from].push(a.to); }
    });
    var done = {}, result = [];
    while (result.length < keys.length) {
      var next = keys.filter(function (k) { return !done[k] && indeg[k] === 0; })[0] ||
        keys.filter(function (k) { return !done[k]; })[0];
      done[next] = true;
      result.push(next);
      out[next].forEach(function (t) { indeg[t]--; });
    }
    return result;
  }

  function walk(model) {
    var events = [], seq = order(model), idx = {};
    seq.forEach(function (k, i) { idx[k] = i; });
    var isSource = {};
    model.sources.forEach(function (s) { isSource[s.id] = true; events.push({ kind: "visit", node: s.id, pass: 1 }); });
    var valid = model.arrows.filter(function (a) { return (isSource[a.from] || idx[a.from] !== undefined) && idx[a.to] !== undefined; });
    function isBack(a) { return !isSource[a.from] && idx[a.to] <= idx[a.from]; }
    function edge(a) { events.push({ kind: "edge", from: a.from, to: a.to, label: a.label, loop: isBack(a) }); }
    var visited = {}, usedBack = {};
    seq.forEach(function (k, i) {
      valid.forEach(function (a) {
        if (a.to === k && !isBack(a) && (isSource[a.from] || visited[a.from])) edge(a);
      });
      events.push({ kind: "visit", node: k, pass: 1 });
      visited[k] = true;
      valid.forEach(function (a, ai) {
        if (a.from !== k || !isBack(a) || usedBack[ai]) return;
        usedBack[ai] = true;
        edge(a);
        for (var j = idx[a.to]; j <= i; j++) {
          if (j > idx[a.to]) {
            valid.forEach(function (b) { if (b.from === seq[j - 1] && b.to === seq[j] && !isBack(b)) edge(b); });
          }
          events.push({ kind: "visit", node: seq[j], pass: 2 });
        }
      });
    });
    return events;
  }

  function trace(model, events) {
    var steps = {}, sources = {}, lanes = {};
    model.steps.forEach(function (s) { steps[stepKey(s)] = s; });
    model.sources.forEach(function (s) { sources[s.id] = s; });
    model.lanes.forEach(function (l) { lanes[l.id] = l; });
    var rows = [];
    events.forEach(function (e) {
      if (e.kind !== "visit") return;
      if (sources[e.node]) {
        var src = sources[e.node];
        if (src.unsure.length) rows.push({ node: e.node, source: true, pass: e.pass, name: src.name, lane: "sources",
          out: src.gives, check: { by: "", how: "" }, result: "none", warnings: ["source UNSURE: " + src.unsure.join("; ")] });
        return;
      }
      var s = steps[e.node], by = low(s.check.by), warnings = [];
      if (by === "unsure") warnings.push("UNSURE: who checks");
      else if (by === "") warnings.push("nobody is named to check this step");
      else if (by === low(s.who) || (lanes[s.lane] && lanes[s.lane].kind === "other" && by === low(lanes[s.lane].name)))
        warnings.push("checked by the same worker who does it");
      rows.push({ node: e.node, pass: e.pass, name: s.name, lane: s.lane, out: s.out, check: s.check,
        result: s.state === "works" ? "pass" : s.state === "broken" ? "fail" : "none", warnings: warnings });
    });
    return rows;
  }

  /* ---------- rebuild (the page saving itself) ---------- */

  function esc(t) {
    return str(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function rebuild(p) {
    return "<!doctype html><html><head><meta charset=utf8><meta name=viewport " +
      "content=\"width=device-width,initial-scale=1,viewport-fit=cover\"><style>" + str(p.reset) +
      "</style></head><body><title>" + esc(p.title) + "</title>" + (p.styles || []).join("") +
      "<script type=\"application/json\" id=\"workflow\">" + p.dataText + "</script><div id=\"app\"></div>" +
      (p.scripts || []).join("") + "</body></html>";
  }

  /* ---------- Git: pull, commit, push ---------- */

  var GITHUB = { server: "GitHub", tools: { read: "get_file_contents", write: "push_files", head: "list_commits" } };

  function paths(model) {
    var base = "workflow/" + model.id + "/";
    return { md: base + "map.md", html: base + "map.html", runs: base + "runs.jsonl" };
  }

  function mapMd(model) {
    return "## " + model.title + "\n\n```json\n" + serializeData(model) + "\n```\n";
  }

  function mapFromMd(text) {
    var m = /```json\s*\n([\s\S]*?)\n```/.exec(str(text));
    return m ? parse(m[1]) : { error: "The repository's map.md has no JSON block." };
  }

  function uncommitted(model) { return Math.max(0, model.changes.length - model.git.committed); }

  function snapshotOf(model) {
    var s = stripInternal(model);
    delete s.git;
    return s;
  }

  function commit(model, message, date) {
    var m = clone(stripInternal(model));
    m = normalize(m);
    var n = uncommitted(m);
    var lines = m.changes.slice(0, n).map(function (c) { return c.what; });
    m.git.committed = m.changes.length;
    m.git.pending.push({ message: str(message) || lines[0] || "update the map", date: str(date) || today(),
      changes: lines, snapshot: snapshotOf(m) });
    return m;
  }

  function today() {
    var d = new Date();
    return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
  }

  function status(model, head) {
    var behind = !!head && !!model.git.pulled && head !== model.git.pulled;
    var pending = model.git.pending.length, unc = uncommitted(model);
    if (behind) return pending || unc ? "diverged" : "behind";
    if (pending) return "ahead";
    if (unc) return "changes";
    return "clean";
  }

  function errMessage(e) { return str(e && (e.message || e.code)) || "The connector did not answer."; }

  async function push(model, gh, pageHtml) {
    var m = normalize(clone(stripInternal(model)));
    if (!m.git.pending.length) return { model: m, ok: true, message: "Nothing to push." };
    if (!m.repo.owner || !m.repo.name) return { model: m, ok: false, message: "No repository is set for this map." };
    var p = paths(m), head;
    try {
      head = await gh.head(m.repo);
      if (m.git.pulled ? head !== m.git.pulled : head && await gh.read(m.repo, p.md)) {
        return { model: m, ok: false, message: "The repository has newer commits. Pull first." };
      }
    } catch (e) { return { model: m, ok: false, message: errMessage(e) }; }
    while (m.git.pending.length) {
      var c = m.git.pending[0];
      var snap = normalize(Object.assign({}, c.snapshot || snapshotOf(m), {
        git: { pulled: head || "", committed: (c.snapshot || m).changes ? (c.snapshot || m).changes.length : 0, pending: [] }
      }));
      try {
        head = await gh.write(m.repo, [{ path: p.md, content: mapMd(snap) }, { path: p.html, content: pageHtml(snap) }], c.message);
      } catch (e) { return { model: m, ok: false, message: errMessage(e) }; }
      m.git.pending.shift();
      m.git.pulled = str(head);
    }
    return { model: m, ok: true, message: "Pushed to " + m.repo.owner + "/" + m.repo.name + "." };
  }

  async function pull(model, gh) {
    var m = normalize(clone(stripInternal(model))), head, file;
    if (!m.repo.owner || !m.repo.name) return { model: m, ok: false, message: "No repository is set for this map." };
    try {
      head = await gh.head(m.repo);
      file = await gh.read(m.repo, paths(m).md);
    } catch (e) { return { model: m, ok: false, message: errMessage(e) }; }
    if (!file) return { model: m, ok: false, message: "Nothing in the repository yet. Commit and push to create it." };
    var got = mapFromMd(file.text);
    if (got.error) return { model: m, ok: false, message: got.error };
    var theirs = got.model;
    theirs.git = { pulled: str(head), committed: theirs.changes.length, pending: [] };
    theirs.repo = m.repo;
    if (m.git.pending.length || uncommitted(m)) {
      return { model: m, ok: true, choice: { mine: m, theirs: theirs }, message: "Both the page and the repository have changed. Keep one." };
    }
    return { model: theirs, ok: true, message: "Pulled from " + m.repo.owner + "/" + m.repo.name + "." };
  }

  function keepAfterChoice(choice, which, date) {
    var keep = normalize(clone(stripInternal(which === "theirs" ? choice.theirs : choice.mine)));
    var other = which === "theirs" ? choice.mine : choice.theirs;
    var setAside = (which === "theirs" ? "set aside the page's changes: " : "set aside the repository's changes: ") +
      other.changes.slice(0, 3).map(function (c) { return c.what; }).join("; ");
    keep.changes.unshift({ date: str(date) || today(), what: setAside });
    if (which === "mine") keep.git.pulled = choice.theirs.git.pulled;
    return keep;
  }

  /* ---------- connector adapter ---------- */

  function findSha(v, depth) {
    if (depth > 4 || v === null || v === undefined) return "";
    if (Array.isArray(v)) return v.length ? findSha(v[0], depth + 1) : "";
    if (isObj(v)) {
      if (typeof v.sha === "string") return v.sha;
      var keys = ["object", "commit", "commits", "data", "ref"];
      for (var i = 0; i < keys.length; i++) { var s = findSha(v[keys[i]], depth + 1); if (s) return s; }
    }
    return "";
  }

  function decode64(b) {
    var bin = atob(str(b).replace(/\s+/g, ""));
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder().decode(bytes);
  }

  function fileText(result) {
    var blocks = (result && result.content) || [];
    for (var i = 0; i < blocks.length; i++) {
      var b = blocks[i];
      if (b && b.type === "resource" && b.resource && typeof b.resource.text === "string") return b.resource.text;
    }
    var p = result && result.payload;
    if (isObj(p) && typeof p.content === "string") return p.encoding === "base64" ? decode64(p.content) : p.content;
    if (isObj(p) && typeof p.text === "string") return p.text;
    if (typeof p === "string") return p;
    return null;
  }

  function notFound(e) { return /not.?found|404|409|empty|no commit/i.test(errMessage(e)); }

  function makeAdapter(mcp, config) {
    var c = config || GITHUB;
    return {
      head: async function (repo) {
        try {
          var r = await mcp.callTool(c.server, c.tools.head, { owner: repo.owner, repo: repo.name, sha: repo.branch, perPage: 1 });
          return findSha(r && r.payload, 0) || null;
        } catch (e) { if (notFound(e)) return null; throw e; }
      },
      read: async function (repo, path) {
        try {
          var r = await mcp.callTool(c.server, c.tools.read, { owner: repo.owner, repo: repo.name, path: path, ref: repo.branch });
          var text = fileText(r);
          return text === null ? null : { text: text };
        } catch (e) { if (notFound(e)) return null; throw e; }
      },
      write: async function (repo, files, message) {
        var r = await mcp.callTool(c.server, c.tools.write, { owner: repo.owner, repo: repo.name, branch: repo.branch, files: files, message: message });
        return findSha(r && r.payload, 0);
      }
    };
  }

  var api = {
    DEFAULT_LANES: DEFAULT_LANES, GITHUB: GITHUB, normalize: normalize, parse: parse, serializeData: serializeData,
    laneForWho: laneForWho, whoForLane: whoForLane, guessIcon: guessIcon, slug: slug, esc: esc, clone: clone,
    order: order, walk: walk, trace: trace, rebuild: rebuild, paths: paths, mapMd: mapMd, mapFromMd: mapFromMd,
    uncommitted: uncommitted, commit: commit, status: status, push: push, pull: pull,
    keepAfterChoice: keepAfterChoice, makeAdapter: makeAdapter, today: today, stripInternal: stripInternal
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  return api;
})();
