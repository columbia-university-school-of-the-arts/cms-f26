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


def render_with_node(page, data):
    scripts = re.findall(r"<script>(.*?)</script>", page.read_text(), re.S)
    code = "\n".join(scripts) + "\nprocess.stdout.write(renderWorkflow(" + json.dumps(data) + "));"
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


if __name__ == "__main__":
    unittest.main()
