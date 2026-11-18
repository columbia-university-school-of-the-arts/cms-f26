"""Standard library only: python3 -m unittest plugins/workflow-interactive/tests/test_interactive_map.py"""
import json, pathlib, re, shutil, subprocess, tempfile, unittest

PLUGIN = pathlib.Path(__file__).resolve().parents[1]
HUB = PLUGIN.parents[1]
SKILL = PLUGIN / "skills" / "interactive-map"
REF = SKILL / "references"
TEMPLATE = REF / "page-template.html"
DATA_RE = re.compile(r'<script type="application/json" id="workflow">(.*?)</script>', re.S)
HAS_NODE = shutil.which("node") is not None


def run_js(expr, extra=""):
    """Evaluate expr (which may await) with icons.js and core.js loaded; return its JSON."""
    code = "\n".join([
        "var document = undefined;",
        (REF / "icons.js").read_text(),
        (REF / "core.js").read_text(),
        extra,
        "(async function(){ var r = await (async function(){ return " + expr + "; })();"
        " process.stdout.write(JSON.stringify(r)); })().catch(function(e){"
        " process.stdout.write(JSON.stringify({thrown: String(e && e.message || e)})); });",
    ])
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(code)
    out = subprocess.run(["node", f.name], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def step(n, name, **kw):
    s = {"n": n, "name": name, "in": "a", "out": "b", "who": "me",
         "check": {"by": "Rob", "how": "read it"}, "run": "ask Cowork", "state": "not tried",
         "state_date": "", "state_note": "", "you_or_it": "it", "credited": "me",
         "mine": False, "unsure": []}
    s.update(kw)
    return s


def old_map(steps, arrows, **kw):
    m = {"title": "Close reading of archival TV", "question": "Q", "begun": "2026-11-18",
         "steps": steps, "arrows": arrows, "changes": []}
    m.update(kw)
    return m


SAMPLE_OLD = old_map(
    [step(1, "Gather"), step(2, "Tag scenes", who="Claude", state="broken"),
     step(3, "Close-read", mine=True, state="works"), step(4, "Compare", who="UNSURE"),
     step(5, "Write up", check={"by": "me", "how": "reread"})],
    [{"from": 1, "to": 2}, {"from": 2, "to": 3}, {"from": 3, "to": 4},
     {"from": 4, "to": 2, "loop": True}, {"from": 4, "to": 5}])


def J(v):
    return json.dumps(v)


class PluginTest(unittest.TestCase):
    def test_manifest(self):
        m = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(m["name"], "workflow-interactive")
        self.assertEqual(m["version"], "0.1.0")
        self.assertEqual(m["skills"], ["./skills/interactive-map"])
        self.assertEqual(m["license"], "CC-BY-NC-SA-4.0")

    def test_marketplace_lists_plugin(self):
        m = json.loads((HUB / ".claude-plugin" / "marketplace.json").read_text())
        entries = [p for p in m["plugins"] if p["name"] == "workflow-interactive"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "./plugins/workflow-interactive")

    def test_no_em_dashes(self):
        for f in PLUGIN.rglob("*"):
            if f.is_file() and f.suffix in {".md", ".html", ".json", ".py", ".js", ".css"}:
                self.assertNotIn(chr(0x2014), f.read_text(), f.name)

    def test_icon_set(self):
        text = (REF / "icons.js").read_text()
        icons = json.loads(text[text.index("{"):text.rindex("}") + 1])
        for b in ("themoviedatabase", "youtube", "vimeo", "internetarchive", "zotero",
                  "wikipedia", "googledrive", "github", "imdb", "letterboxd", "spotify",
                  "soundcloud", "reddit", "instagram", "tiktok", "x", "arxiv", "googlescholar"):
            self.assertIn(b, icons["brand"])
            self.assertRegex(icons["brand"][b]["color"], r"^#[0-9A-Fa-f]{6}$")
        for g in ("film", "globe", "mic", "database", "file-text", "folder", "tag", "book-open",
                  "pen-line", "git-compare", "download", "search", "camera", "chart-column",
                  "user", "sparkles", "cog", "scissors", "message-square", "image", "music",
                  "upload", "list-checks", "quote", "map", "calendar", "link", "archive",
                  "clapperboard", "newspaper"):
            self.assertIn(g, icons["generic"])
        self.assertEqual(icons["versions"], {"simple-icons": "16.36.0", "lucide-static": "1.66.0"})


@unittest.skipUnless(HAS_NODE, "node not installed")
class ModelTest(unittest.TestCase):
    def norm(self, m):
        return run_js("WF.normalize(" + J(m) + ")")

    def test_old_map_gets_defaults(self):
        m = self.norm(SAMPLE_OLD)
        self.assertEqual([l["id"] for l in m["lanes"]], ["sources", "me", "claude", "other"])
        self.assertEqual([l["name"] for l in m["lanes"]],
                         ["Sources", "Me", "Claude", "Someone or a script"])
        self.assertEqual(m["sources"], [])
        self.assertEqual([s["lane"] for s in m["steps"]], ["me", "claude", "me", "other", "me"])
        self.assertEqual([s["col"] for s in m["steps"]], [0, 1, 2, 3, 4])
        self.assertTrue(all(s["icon"] for s in m["steps"]))
        self.assertEqual(m["id"], "close-reading-of-archival-tv")
        self.assertEqual(m["repo"]["branch"], "main")
        self.assertEqual(m["git"]["pending"], [])

    def test_string_numbers_and_malformed_fields(self):
        m = self.norm(old_map([step("1", "A"), step("2a", "B", unsure="one doubt", check="me",
                                                         mine="false")],
                              [{"from": 1, "to": "2a"}]))
        b = m["steps"][1]
        self.assertEqual(b["n"], "2a")
        self.assertEqual(b["unsure"], ["one doubt"])
        self.assertEqual(b["check"], {"by": "me", "how": ""})
        self.assertFalse(b["mine"])
        self.assertEqual(m["arrows"][0]["from"], "1")
        self.assertEqual(m["arrows"][0]["to"], "2a")
        self.assertEqual(m["problems"], [])

    def test_unknown_fields_are_kept(self):
        m = self.norm(old_map([step(1, "A", extra_field=7)], [], notes_for_rob="x"))
        self.assertEqual(m["steps"][0]["extra_field"], 7)
        self.assertEqual(m["notes_for_rob"], "x")

    def test_unsure_who_lands_in_other_lane(self):
        m = self.norm(old_map([step(1, "A", who="UNSURE")], [], lanes=[]))
        self.assertEqual(m["steps"][0]["lane"], "other")

    def test_custom_lane_and_sources_lane_first(self):
        lanes = [{"id": "me", "name": "Me", "kind": "me"},
                 {"id": "rob", "name": "Rob", "kind": "other"}]
        m = self.norm(old_map([step(1, "A", who="Rob")], [], lanes=lanes))
        self.assertEqual([l["id"] for l in m["lanes"]], ["sources", "me", "rob"])
        self.assertEqual(m["steps"][0]["lane"], "rob")

    def test_who_for_lane(self):
        r = run_js("[WF.whoForLane({kind:'me'}, 'Claude'), WF.whoForLane({kind:'claude'}, 'me'),"
                   " WF.whoForLane({kind:'other', name:'Rob'}, 'a script'),"
                   " WF.whoForLane({kind:'other', name:'Rob'}, 'me')]")
        self.assertEqual(r, ["me", "Claude", "a script", "someone else"])

    def test_sources_get_ids_and_icons(self):
        m = self.norm(old_map([step(1, "A")], [{"from": "src-tmdb", "to": 1}],
                              sources=[{"id": "src-tmdb", "name": "TMDB", "icon": "themoviedatabase",
                                        "kind": "api"}, {"name": "Interviews", "kind": "by hand"}]))
        self.assertEqual(m["sources"][1]["id"], "src-interviews")
        self.assertEqual(m["sources"][1]["icon"], "user")
        self.assertEqual(m["problems"], [])

    def test_broken_json(self):
        r = run_js("WF.parse('{\"title\": \"T\",}')")
        self.assertIn("The map's data has an error", r["error"])
        self.assertIn("Ask Claude to fix the JSON block", r["error"])

    def test_arrow_to_missing_step_is_a_problem(self):
        m = self.norm(old_map([step(1, "A")], [{"from": 1, "to": 9}]))
        self.assertEqual(len(m["problems"]), 1)
        self.assertIn("9", m["problems"][0])


@unittest.skipUnless(HAS_NODE, "node not installed")
class WalkTest(unittest.TestCase):
    def visits(self, m):
        ev = run_js("WF.walk(WF.normalize(" + J(m) + "))")
        return [(e["node"], e["pass"]) for e in ev if e["kind"] == "visit"]

    def test_sample_walk(self):
        m = dict(SAMPLE_OLD, sources=[{"id": "src-a", "name": "A"}, {"id": "src-b", "name": "B"}],
                 arrows=SAMPLE_OLD["arrows"] + [{"from": "src-a", "to": 1}, {"from": "src-b", "to": 2}])
        self.assertEqual(self.visits(m), [("src-a", 1), ("src-b", 1), ("1", 1), ("2", 1), ("3", 1),
                                          ("4", 1), ("2", 2), ("3", 2), ("4", 2), ("5", 1)])

    def test_edges_carry_labels(self):
        m = dict(SAMPLE_OLD, arrows=[{"from": 1, "to": 2, "label": "12 clips"}])
        ev = run_js("WF.walk(WF.normalize(" + J(m) + "))")
        edges = [e for e in ev if e["kind"] == "edge"]
        self.assertEqual(edges[0]["label"], "12 clips")

    def test_all_loop_cycle_ends(self):
        m = old_map([step(1, "A"), step(2, "B")],
                    [{"from": 1, "to": 2, "loop": True}, {"from": 2, "to": 1, "loop": True}])
        v = self.visits(m)
        self.assertLessEqual(len(v), 6)
        self.assertEqual(v[0], ("1", 1))

    def test_missing_target_is_skipped(self):
        m = old_map([step(1, "A")], [{"from": 1, "to": 9}])
        self.assertEqual(self.visits(m), [("1", 1)])


@unittest.skipUnless(HAS_NODE, "node not installed")
class TraceTest(unittest.TestCase):
    def test_warnings_and_results(self):
        m = old_map([step(1, "A", state="works"),
                     step(2, "B", state="broken", check={"by": "UNSURE", "how": ""}),
                     step(3, "C", check={"by": "", "how": ""}),
                     step(4, "D", check={"by": "me", "how": "x"}),
                     step(5, "E", who="someone else", lane="rob", check={"by": "Rob", "how": "x"})],
                    [], lanes=[{"id": "me", "name": "Me", "kind": "me"},
                               {"id": "rob", "name": "Rob", "kind": "other"}])
        rows = run_js("(function(){var m=WF.normalize(" + J(m) + "); return WF.trace(m, WF.walk(m));})()")
        self.assertEqual([r["result"] for r in rows], ["pass", "fail", "none", "none", "none"])
        self.assertIn("UNSURE: who checks", rows[1]["warnings"])
        self.assertIn("nobody is named to check this step", rows[2]["warnings"])
        self.assertIn("checked by the same worker who does it", rows[3]["warnings"])
        self.assertIn("checked by the same worker who does it", rows[4]["warnings"])
        self.assertEqual(rows[0]["warnings"], [])


@unittest.skipUnless(HAS_NODE, "node not installed")
class RebuildTest(unittest.TestCase):
    def test_script_close_tag_round_trips(self):
        m = old_map([step(1, "A </script><b>x</b>")], [])
        r = run_js("(function(){var t=WF.serializeData(WF.normalize(" + J(m) + "));"
                   " return {raw: t, back: WF.parse(t).model.steps[0].name};})()")
        self.assertNotIn("</script>", r["raw"])
        self.assertEqual(r["back"], "A </script><b>x</b>")
        self.assertNotIn("problems", json.loads(r["raw"]))

    def test_rebuild_keeps_styles_and_scripts(self):
        parts = {"reset": "*{margin:0}", "title": "My <map>",
                 "styles": ["<style data-wf>.lane{fill:red}</style>"],
                 "scripts": ["<script data-wf>var x = 1;</script>"],
                 "dataText": "{\"a\":1}"}
        html = run_js("WF.rebuild(" + J(parts) + ")")
        self.assertTrue(html.startswith(
            "<!doctype html><html><head><meta charset=utf8><meta name=viewport "
            "content=\"width=device-width,initial-scale=1,viewport-fit=cover\"><style>*{margin:0}"
            "</style></head><body><title>My &lt;map&gt;</title>"))
        self.assertIn("<style data-wf>.lane{fill:red}</style>", html)
        self.assertIn('<script type="application/json" id="workflow">{"a":1}</script>'
                      '<div id="app"></div><script data-wf>var x = 1;</script>', html)
        self.assertTrue(html.endswith("</body></html>"))


FAKE_GH = """
function fakeGh(state){
  return {
    calls: [],
    head: async function(){ return state.head; },
    read: async function(repo, path){ return state.files[path] ? {text: state.files[path]} : null; },
    write: async function(repo, files, message){
      if (state.fail) throw {code: 'tool_error', message: state.fail};
      this.calls.push({files: files.map(function(f){return f.path;}), message: message});
      files.forEach(function(f){ state.files[f.path] = f.content; });
      state.head = 'sha' + (this.calls.length + 1); return state.head; }
  };
}
"""


def gitmap(**kw):
    m = old_map([step(1, "A")], [], repo={"owner": "o", "name": "r"},
                changes=[{"date": "2026-11-18", "what": "added A"},
                         {"date": "2026-11-17", "what": "begun"}])
    m.update(kw)
    return m


@unittest.skipUnless(HAS_NODE, "node not installed")
class GitTest(unittest.TestCase):
    def test_paths_and_map_md(self):
        r = run_js("(function(){var m=WF.normalize(" + J(gitmap()) + ");"
                   " return [WF.paths(m), WF.mapMd(m)];})()")
        self.assertEqual(r[0], {"md": "workflow/close-reading-of-archival-tv/map.md",
                                "html": "workflow/close-reading-of-archival-tv/map.html",
                                "runs": "workflow/close-reading-of-archival-tv/runs.jsonl"})
        self.assertTrue(r[1].startswith("## Close reading of archival TV\n\n```json\n"))
        self.assertTrue(r[1].rstrip().endswith("```"))

    def test_commit_takes_uncommitted_lines(self):
        r = run_js("(function(){var m=WF.normalize(" + J(gitmap()) + ");"
                   " var a=WF.uncommitted(m); m=WF.commit(m,'first');"
                   " return [a, WF.uncommitted(m), m.git.pending.length, m.git.pending[0].message,"
                   " m.git.pending[0].changes];})()")
        self.assertEqual(r, [2, 0, 1, "first", ["added A", "begun"]])

    def test_push_writes_each_commit(self):
        r = run_js("(async function(){var s={head:null, files:{}}; var gh=fakeGh(s);"
                   " var m=WF.normalize(" + J(gitmap()) + "); m=WF.commit(m,'one');"
                   " m.changes.unshift({date:'2026-11-18', what:'renamed A'}); m=WF.commit(m,'two');"
                   " var res=await WF.push(m, gh, function(mm){return '<html>'+mm.git.pending.length+'</html>';});"
                   " return {ok: res.ok, calls: gh.calls, pending: res.model.git.pending.length,"
                   " pulled: res.model.git.pulled};})()", FAKE_GH)
        self.assertTrue(r["ok"])
        self.assertEqual([c["message"] for c in r["calls"]], ["one", "two"])
        self.assertEqual(r["calls"][0]["files"], ["workflow/close-reading-of-archival-tv/map.md",
                                                  "workflow/close-reading-of-archival-tv/map.html"])
        self.assertEqual(r["pending"], 0)
        self.assertEqual(r["pulled"], "sha3")

    def test_push_refused_when_branch_moved(self):
        r = run_js("(async function(){var s={head:'other', files:{}}; var gh=fakeGh(s);"
                   " var m=WF.normalize(" + J(gitmap(git={"pulled": "sha1", "pending": []})) + ");"
                   " m=WF.commit(m,'one'); var res=await WF.push(m, gh, function(){return 'x';});"
                   " return {ok: res.ok, message: res.message, calls: gh.calls.length,"
                   " pending: res.model.git.pending.length};})()", FAKE_GH)
        self.assertEqual(r, {"ok": False, "message": "The repository has newer commits. Pull first.",
                             "calls": 0, "pending": 1})

    def test_first_push_refused_when_file_exists(self):
        r = run_js("(async function(){var s={head:'h', files:{'workflow/close-reading-of-archival-tv/map.md':'x'}};"
                   " var m=WF.normalize(" + J(gitmap()) + "); m=WF.commit(m,'one');"
                   " var res=await WF.push(m, fakeGh(s), function(){return 'x';}); return res.ok;})()", FAKE_GH)
        self.assertFalse(r)

    def test_push_failure_keeps_pending(self):
        r = run_js("(async function(){var s={head:null, files:{}, fail:'Resource not accessible'};"
                   " var m=WF.normalize(" + J(gitmap()) + "); m=WF.commit(m,'one');"
                   " var res=await WF.push(m, fakeGh(s), function(){return 'x';});"
                   " return {ok: res.ok, message: res.message, pending: res.model.git.pending.length};})()",
                   FAKE_GH)
        self.assertEqual(r, {"ok": False, "message": "Resource not accessible", "pending": 1})

    def test_pull_takes_theirs_when_clean(self):
        theirs = gitmap(title="Close reading of archival TV", question="Theirs")
        r = run_js("(async function(){var t=WF.normalize(" + J(theirs) + ");"
                   " var s={head:'h9', files:{}}; s.files[WF.paths(t).md]=WF.mapMd(t);"
                   " var m=WF.normalize(" + J(gitmap()) + "); m=WF.commit(m,'c'); m.git.pending=[];"
                   " var res=await WF.pull(m, fakeGh(s));"
                   " return {ok: res.ok, q: res.model.question, pulled: res.model.git.pulled};})()",
                   FAKE_GH)
        self.assertEqual(r, {"ok": True, "q": "Theirs", "pulled": "h9"})

    def test_pull_offers_choice_when_diverged(self):
        theirs = gitmap(question="Theirs")
        r = run_js("(async function(){var t=WF.normalize(" + J(theirs) + ");"
                   " var s={head:'h9', files:{}}; s.files[WF.paths(t).md]=WF.mapMd(t);"
                   " var m=WF.normalize(" + J(gitmap(git={"pulled": "h1", "pending": []})) + ");"
                   " m=WF.commit(m,'mine'); var res=await WF.pull(m, fakeGh(s));"
                   " return {ok: res.ok, choice: !!res.choice, theirs: res.choice && res.choice.theirs.question};})()",
                   FAKE_GH)
        self.assertEqual(r, {"ok": True, "choice": True, "theirs": "Theirs"})

    def test_status(self):
        r = run_js("(function(){var m=WF.normalize(" + J(gitmap(git={"pulled": "a", "pending": []})) + ");"
                   " var out=[WF.status(m,'a')]; m=WF.commit(m,'x'); out.push(WF.status(m,'a'));"
                   " out.push(WF.status(m,'b')); m.git.pending=[]; out.push(WF.status(m,'b'));"
                   " m.changes.unshift({date:'d', what:'w'}); out.push(WF.status(m,'a')); return out;})()")
        self.assertEqual(r, ["changes", "ahead", "diverged", "behind", "changes"])

    def test_adapter_reads_payloads(self):
        fake_mcp = """
        var fakeMcp = { callTool: async function(server, tool, input){
          if (tool === 'list_commits') return {payload: [{sha: 'abc'}]};
          if (tool === 'get_file_contents') return {payload: {content: Buffer.from('hello').toString('base64'), encoding: 'base64', sha: 's'}};
          if (tool === 'push_files') return {payload: {object: {sha: 'new'}}};
        }};"""
        r = run_js("(async function(){var gh=WF.makeAdapter(fakeMcp, WF.GITHUB); var repo={owner:'o',name:'r',branch:'main'};"
                   " return [await gh.head(repo), (await gh.read(repo,'p')).text,"
                   " await gh.write(repo,[{path:'p',content:'c'}],'m')];})()", fake_mcp)
        self.assertEqual(r, ["abc", "hello", "new"])


def build_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_page", PLUGIN / "tools" / "build_page.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PageTest(unittest.TestCase):
    def test_template_is_built_from_its_parts(self):
        self.assertEqual(TEMPLATE.read_text(), build_module().build(),
                         "page-template.html is stale: run tools/build_page.py")

    def test_template_is_self_contained(self):
        t = TEMPLATE.read_text()
        for bad in ("src=", 'href="http', "@import", "url(http"):
            self.assertNotIn(bad, t)

    def test_template_has_one_data_block_and_marked_code(self):
        t = TEMPLATE.read_text()
        blocks = DATA_RE.findall(t)
        self.assertEqual(len(blocks), 1)
        d = json.loads(blocks[0])
        self.assertEqual(len(d["steps"]), 5)
        self.assertEqual([s["icon"] for s in d["sources"]], ["internetarchive", "themoviedatabase", "mic"])
        self.assertEqual(t.count('<div id="app"></div><script data-wf>'), 1)
        self.assertEqual(t.count("</script><script data-wf>"), 3)
        self.assertEqual(t.count("</title><style data-wf>"), 1)
        self.assertTrue(t.startswith("<title>"))

    def test_template_supports_dark_phone_and_motion(self):
        t = TEMPLATE.read_text()
        for needle in ("prefers-color-scheme: dark", ':root[data-theme="dark"]', "max-width: 860px",
                       "prefers-reduced-motion", "overflow-wrap"):
            self.assertIn(needle, t)

    @unittest.skipUnless(HAS_NODE, "node not installed")
    def test_render_svg(self):
        sample = json.loads((REF / "sample.json").read_text())
        sample["steps"][0]["name"] = "Gather <b>clips</b>"
        svg = run_js("(function(){var m=WF.normalize(" + J(sample) + "); return WF.renderSvg(m, WF.layout(m));})()",
                     (REF / "render.js").read_text())
        for needle in ("Sources", "Me", "Claude", "Someone or a", "Internet Archive", "TMDB", "2 Tag scenes",
                       "&lt;b&gt;", 'data-node="src-tmdb"', 'class="edge loop"'):
            self.assertIn(needle, svg)
        self.assertNotIn("<b>", svg)
        self.assertEqual(svg.count('class="edge'), 8)

    @unittest.skipUnless(HAS_NODE, "node not installed")
    def test_sources_sit_left_of_their_first_step(self):
        sample = json.loads((REF / "sample.json").read_text())
        r = run_js("(function(){var m=WF.normalize(" + J(sample) + "); var L=WF.layout(m);"
                   " return [L.nodes['src-archive'].x, L.nodes['1'].x, L.nodes['src-tmdb'].x, L.nodes['2'].x];})()",
                   (REF / "render.js").read_text())
        self.assertLess(r[0], r[1])
        self.assertLess(r[2], r[3])

    @unittest.skipUnless(HAS_NODE, "node not installed")
    def test_lane_colour_must_be_hex(self):
        r = run_js("WF.laneColor(WF.normalize({lanes:[{id:'x',name:'X',kind:'me',color:'red;}</style>'}]}), 'x')",
                   (REF / "render.js").read_text())
        self.assertEqual(r, "#c2410c")


if __name__ == "__main__":
    unittest.main()
