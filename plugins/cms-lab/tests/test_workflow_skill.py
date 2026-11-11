"""Standard library only: python3 -m unittest plugins/cms-lab/tests/test_workflow_skill.py"""
import json, pathlib, re, unittest

PLUGIN = pathlib.Path(__file__).resolve().parents[1]


class WorkflowSkillTest(unittest.TestCase):
    def test_plugin_lists_only_workflow(self):
        manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        self.assertIn("./skills/workflow", manifest["skills"])
        self.assertNotIn("./skills/icm-architect", manifest["skills"])
        self.assertEqual(manifest["version"], "0.10.0")

    def test_icm_architect_is_gone(self):
        self.assertFalse((PLUGIN / "skills" / "icm-architect").exists())

    def test_skill_name_matches_its_folder(self):
        text = (PLUGIN / "skills" / "workflow" / "SKILL.md").read_text()
        self.assertRegex(text, r"(?m)^name: workflow\s*$")

    def test_wrapper_states_the_contract(self):
        text = (PLUGIN / "skills" / "workflow" / "SKILL.md").read_text()
        for needle in ("workflow/stages/", "kind:", "check:", "allow:", "run_workflow.py check",
                       "no `model:`", "corpus/", "PATTERNS.md",
                       "Interpretable Context Methodology"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
