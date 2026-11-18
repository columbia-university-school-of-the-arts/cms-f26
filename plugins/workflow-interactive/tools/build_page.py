"""Instructor tool: assemble references/page-template.html from its parts.

Run from the hub root: python3 plugins/workflow-interactive/tools/build_page.py
The template is what the skill publishes, with only the JSON block replaced.
Its styles and scripts are marked data-wf, which is how the page finds its own
code when it saves itself. Students never run this.
"""
import json, pathlib, re, sys

REF = pathlib.Path(__file__).resolve().parents[1] / "skills" / "interactive-map" / "references"
OUT = REF / "page-template.html"
SCRIPTS = ["icons.js", "core.js", "render.js", "ui.js"]


def data_text(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False).replace("</", "<\\/")


def build():
    sample = json.loads((REF / "sample.json").read_text())
    css = (REF / "page.css").read_text()
    parts = ["<title>" + sample["title"] + "</title>",
             "<style data-wf>" + css + "</style>",
             '<script type="application/json" id="workflow">' + data_text(sample) + "</script>",
             '<div id="app"></div>']
    for name in SCRIPTS:
        js = (REF / name).read_text()
        if re.search(r"</script", js, re.I):
            sys.exit(f"{name} contains a closing script tag; write it as <\\/script>")
        parts.append("<script data-wf>" + js + "</script>")
    return "".join(parts)


if __name__ == "__main__":
    OUT.write_text(build())
    print(f"wrote {OUT.name}, {OUT.stat().st_size} bytes")
