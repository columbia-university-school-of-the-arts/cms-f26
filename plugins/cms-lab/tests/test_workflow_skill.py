"""Standard library only: python3 -m unittest plugins/cms-lab/tests/test_workflow_skill.py"""
import json, pathlib, re, unittest

PLUGIN = pathlib.Path(__file__).resolve().parents[1]


class WorkflowSkillTest(unittest.TestCase):
    def test_plugin_lists_both_skills(self):
        manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        self.assertIn("./skills/workflow", manifest["skills"])
        self.assertIn("./skills/icm-architect", manifest["skills"])
        self.assertEqual(manifest["version"], "0.10.0")

    def test_each_skill_name_matches_its_folder(self):
        for folder in ("workflow", "icm-architect"):
            text = (PLUGIN / "skills" / folder / "SKILL.md").read_text()
            self.assertRegex(text, rf"(?m)^name: {re.escape(folder)}\s*$")

    def test_upstream_names_a_commit(self):
        text = (PLUGIN / "skills" / "icm-architect" / "UPSTREAM").read_text()
        self.assertRegex(text, r"(?m)^commit: [0-9a-f]{40}$")
        self.assertIn("repository: https://github.com/RinDig/icm-architect", text)

    def test_wrapper_states_the_contract(self):
        text = (PLUGIN / "skills" / "workflow" / "SKILL.md").read_text()
        for needle in ("workflow/stages/", "kind:", "check:", "allow:", "run_workflow.py check",
                       "links.py", "no `model:`", "corpus/"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
