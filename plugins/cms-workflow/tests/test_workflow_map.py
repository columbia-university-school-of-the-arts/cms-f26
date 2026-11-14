"""Standard library only: python3 -m unittest plugins/cms-workflow/tests/test_workflow_map.py"""
import json, pathlib, re, shutil, subprocess, tempfile, unittest

PLUGIN = pathlib.Path(__file__).resolve().parents[1]
HUB = PLUGIN.parents[1]
SKILL = PLUGIN / "skills" / "workflow-map"
TEMPLATE = SKILL / "references" / "map-template.html"
EXAMPLE = SKILL / "references" / "example-chaplin.html"
KEYS = {"title", "question", "begun", "steps", "arrows", "changes"}
DATA_RE = re.compile(r'<script type="application/json" id="workflow">(.*?)</script>', re.S)


def data_of(path):
    blocks = DATA_RE.findall(path.read_text())
    assert len(blocks) == 1, f"{path.name}: {len(blocks)} data blocks"
    return json.loads(blocks[0])


def renderer_of(path):
    """The page with its data block emptied: what must stay identical between maps."""
    return DATA_RE.sub("", path.read_text())


def render_with_node(page, data, raw=False):
    scripts = re.findall(r"<script>(.*?)</script>", page.read_text(), re.S)
    arg = json.dumps(data if raw else json.dumps(data))
    code = "\n".join(scripts) + "\nprocess.stdout.write(loadWorkflow(" + arg + "));"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("var document = undefined;\n" + code)
    return subprocess.run(["node", f.name], capture_output=True, text=True, check=True).stdout


class PluginTest(unittest.TestCase):
    def test_manifest(self):
        m = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(m["name"], "cms-workflow")
        self.assertEqual(m["version"], "0.1.0")
        self.assertEqual(m["skills"], ["./skills/workflow-map"])
        self.assertEqual(m["license"], "CC-BY-NC-SA-4.0")

    def test_marketplace_lists_plugin(self):
        m = json.loads((HUB / ".claude-plugin" / "marketplace.json").read_text())
        entries = [p for p in m["plugins"] if p["name"] == "cms-workflow"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "./plugins/cms-workflow")

    def test_skill_name_matches_folder(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertRegex(text, r"(?m)^name: workflow-map\s*$")
        self.assertRegex(text, r"(?m)^description: ")

    def test_skill_states_the_rules(self):
        text = (SKILL / "SKILL.md").read_text()
        for needle in ("UNSURE", "no step", "photo", "workflow.md", "thesis", "you_or_it",
                       "credited", "mine", "change log", "workflow/map.md", "Cowork",
                       "in place", "paste"):
            self.assertIn(needle, text)

    def test_no_em_dashes(self):
        for f in PLUGIN.rglob("*"):
            if f.is_file() and f.suffix in {".md", ".html", ".json", ".py"}:
                self.assertFalse(chr(0x2014) in f.read_text(), f.name)


class TemplateTest(unittest.TestCase):
    def test_template_has_one_data_block(self):
        d = data_of(TEMPLATE)
        self.assertEqual(set(d), KEYS)
        self.assertEqual(len(d["steps"]), 2)
        self.assertIn("UNSURE", json.dumps(d))

    def test_template_is_self_contained(self):
        t = TEMPLATE.read_text()
        for bad in ("src=", 'href="http', "@import", "url(http"):
            self.assertNotIn(bad, t)

    def test_template_supports_dark_and_phone(self):
        t = TEMPLATE.read_text()
        for needle in ("prefers-color-scheme: dark", 'name="viewport"', "overflow-wrap"):
            self.assertIn(needle, t)

    @unittest.skipIf(shutil.which("node") is None, "node not installed")
    def test_renders_steps_and_loop(self):
        step = lambda n, name, who="me": {
            "n": n, "name": name, "in": "a", "out": "b", "who": who,
            "check": {"by": "me", "how": "read it"}, "run": "ask Cowork", "state": "not tried",
            "state_date": "", "state_note": "", "you_or_it": "it", "credited": "me",
            "mine": n == 3, "unsure": []}
        data = {"title": "T", "question": "Q", "begun": "2026-11-18",
                "steps": [step(1, "Gather"), step(2, "Sort <b>", "UNSURE"), step(3, "Write")],
                "arrows": [{"from": 1, "to": 2, "loop": False}, {"from": 2, "to": 3, "loop": False},
                           {"from": 3, "to": 1, "loop": True}],
                "changes": []}
        out = render_with_node(TEMPLATE, data)
        for needle in ("Gather", "Write", "loops back to 1", "UNSURE", "Sort &lt;b&gt;"):
            self.assertIn(needle, out)
        self.assertNotIn("<b>", out)


def step_(n, name, **kw):
    s = {"n": n, "name": name, "in": "a", "out": "b", "who": "me",
         "check": {"by": "me", "how": "read it"}, "run": "ask Cowork", "state": "not tried",
         "state_date": "", "state_note": "", "you_or_it": "it", "credited": "me",
         "mine": False, "unsure": []}
    s.update(kw)
    return s


def map_(steps, arrows):
    return {"title": "T", "question": "Q", "begun": "2026-11-18", "steps": steps,
            "arrows": arrows, "changes": []}


@unittest.skipIf(shutil.which("node") is None, "node not installed")
class RobustRenderTest(unittest.TestCase):
    def test_broken_json_shows_a_message(self):
        out = render_with_node(TEMPLATE, '{"title": "T",}', raw=True)
        self.assertIn("The map's data has an error", out)
        self.assertIn("Ask Claude to fix the JSON block", out)

    def test_string_step_numbers_keep_arrows(self):
        out = render_with_node(TEMPLATE, map_([step_("1", "A"), step_("2a", "B")],
                                              [{"from": 1, "to": "2a", "loop": False}]))
        self.assertIn("goes to 2a", out)

    def test_arrow_to_missing_step_is_listed(self):
        out = render_with_node(TEMPLATE, map_([step_(1, "A")], [{"from": 1, "to": 9, "loop": False}]))
        self.assertIn("UNSURE arrows", out)

    def test_unsure_arrow_is_highlighted(self):
        out = render_with_node(TEMPLATE, map_([step_(1, "A"), step_(2, "B")],
                                              [{"from": 1, "to": 2, "loop": False, "unsure": True}]))
        self.assertRegex(out, r'class="unsure"[^<]*UNSURE</span>[^<]*goes to 2|goes to 2[^<]*<span class="unsure">UNSURE')

    def test_backward_arrow_is_a_loop(self):
        out = render_with_node(TEMPLATE, map_([step_(1, "A"), step_(2, "B")],
                                              [{"from": 2, "to": 1, "loop": False}]))
        self.assertIn("loops back to 1", out)

    def test_malformed_fields_do_not_blank_the_page(self):
        out = render_with_node(TEMPLATE, map_([step_(1, "A", unsure="one doubt", check="me", mine="false")], []))
        self.assertIn("one doubt", out)
        self.assertIn("Who checks it</dt><dd>me", out)
        self.assertNotIn("badge mine", out)


class SkillRobustnessTest(unittest.TestCase):
    def test_existing_map_is_read_first(self):
        text = (SKILL / "SKILL.md").read_text()
        reading = text[text.index("## What to read"):text.index("## The rules")]
        self.assertLess(reading.index("existing map"), reading.index("photo"))

    def test_skill_covers_data_safety_and_saving(self):
        text = " ".join((SKILL / "SKILL.md").read_text().split())
        for needle in ("<\\/", '"unsure": true', "one section per map", "in the chat"):
            self.assertIn(needle, text)

    def test_no_bytecode_tracked(self):
        out = subprocess.run(["git", "ls-files", str(PLUGIN)], cwd=HUB, capture_output=True, text=True).stdout
        self.assertNotIn("__pycache__", out)
        self.assertIn("__pycache__/", (HUB / ".gitignore").read_text())


class ExampleTest(unittest.TestCase):
    NAMES = ["Find trade-press pages", "Read the pages", "Find secondary literature",
             "Primary-material mapping", "Concept mapping", "New research", "Chapter planning"]
    ARROWS = {(1, 2), (2, 4), (3, 5), (4, 5), (4, 6), (5, 6), (6, 1), (4, 7), (5, 7)}

    def test_example_map(self):
        d = data_of(EXAMPLE)
        self.assertEqual([s["name"] for s in d["steps"]], self.NAMES)
        self.assertEqual({(a["from"], a["to"]) for a in d["arrows"]}, self.ARROWS)
        self.assertEqual([(a["from"], a["to"]) for a in d["arrows"] if a["loop"]], [(6, 1)])
        last = d["steps"][6]
        self.assertEqual(last["who"], "me")
        self.assertTrue(last["mine"])
        self.assertEqual(renderer_of(EXAMPLE), renderer_of(TEMPLATE))
        names = {s["n"] for s in d["steps"]}
        for a in d["arrows"]:
            self.assertIn(a["from"], names)
            self.assertIn(a["to"], names)
        for s in d["steps"][:6]:
            self.assertIn("not yet tried in Cowork", s["state_note"])


if __name__ == "__main__":
    unittest.main()
