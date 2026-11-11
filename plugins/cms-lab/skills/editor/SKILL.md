---
name: editor
description: "Open the fleet editor: a page on the student's own machine that shows their workflow as a pipeline and opens each agent, workflow stage, and skill in a form, with a draft from Claude and a Save that writes only what meets the course contract. Run it in Claude Code in the fleet repository."
---

# Open the fleet editor

The student wants to see and edit their fleet in a browser. Say what each
step does in one sentence before doing it.

1. Make sure you are in the student's fleet repository and that it holds
   `scripts/fleet_editor.py`. If it does not, tell them to bring in the
   course starter first, and stop:

       git fetch upstream && git merge upstream/main

2. Start the editor with the Bash tool, with `run_in_background` set, so it
   keeps running while you talk:

       python3 scripts/fleet_editor.py

3. Read its first line of output: `Fleet editor: http://127.0.0.1:<port>/?token=...`.
   Open that address for the student: `open "<address>"` on a Mac,
   `explorer.exe "<address>"` in Ubuntu on Windows. If opening fails, give
   them the address to paste into their browser. The address is theirs
   alone: give it to them, and again whenever they ask for it (for example
   after closing the tab), but never post it anywhere else.

4. Tell them, in a few lines:
   - the pipeline is their workflow; click a stage, an agent, or a skill to
     open it;
   - Form shows fields, File shows the file itself, and nested settings such
     as an agent's hooks are edited in File;
   - Draft asks Claude Code, on their own login, for a first version; it
     writes nothing until they save;
   - Save writes only what passes the course's checks and never commits, so
     they commit in the terminal when they are ready;
   - to stop the editor, ask Claude to stop it, and Claude stops the
     background task it started. If they started it themselves with
     `python3 scripts/fleet_editor.py` in a terminal, Ctrl-C there stops it.

If they ask you to stop it, stop the background task you started.
