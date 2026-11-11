"""Standard library only: python3 -m unittest plugins/cms-lab/tests/test_editor_skill.py"""
import json, pathlib, re, unittest

PLUGIN = pathlib.Path(__file__).resolve().parents[1]


class EditorSkillTest(unittest.TestCase):
    def test_plugin_lists_the_skill(self):
        manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        self.assertIn("./skills/editor", manifest["skills"])
        self.assertEqual(manifest["version"], "0.11.0")

    def test_skill_name_and_steps(self):
        text = (PLUGIN / "skills" / "editor" / "SKILL.md").read_text()
        self.assertRegex(text, r"(?m)^name: editor\s*$")
        for needle in ("scripts/fleet_editor.py", "git fetch upstream", "run_in_background",
                       "explorer.exe", "Ctrl-C", "commit"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
