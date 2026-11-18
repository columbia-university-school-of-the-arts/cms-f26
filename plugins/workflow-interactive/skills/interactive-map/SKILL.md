---
name: interactive-map
description: "Use when a student wants to make, open, change, or record a run on an interactive map of a workflow: their research process from a Week 10 drawing, Claude's reading of it, a workflow.md, an existing workflow map, or a description of any other kind of work (editing, publishing, anything they draw). Makes a page in swimlanes with their sources, steps, and checks, a walkthrough they play, and a copy saved into their fleet repository's folder. Also use when they ask to change how the map page looks or works, or to add an icon for a service."
---

# Your workflow, as a page you work on

A workflow map is a page that shows how a piece of work gets done: the
sources it draws on, each step, who does it, who checks it, and how to run
it in Cowork. It is drawn in swimlanes, one lane for each kind of worker
(you, Claude, someone or a script), so the hand-offs are what you see first.
The student plays a walkthrough to watch data move from the sources through
every step, and reads each step's check in a debug trace.

The page opens in **View** mode: each card shows how many times it has run,
opening a card shows **What it did** on every run (each pass through a loop
kept separately, with its outputs, note, and check), and **Play** replays the
real runs in order. **Edit** mode is where the workflow changes: drag cards,
drag from a card's right-hand dot to another card to add an arrow (an arrow
back to an earlier step becomes a loop), change fields, add steps, sources,
and lanes. The student looks first and
decides when to edit.

A box above the map, **Tell the map what to change**, takes the same edits
in words, typed or spoken: "move step 4 to the Me lane", "add a loop from 4
back to 2", "record that step 2 worked, it wrote notes/tags.csv". The page
asks Claude on the student's own account, shows the changes Claude plans as
change log lines, and changes nothing until the student presses **Apply**;
Save keeps them, as with any edit. Each message uses the student's
own Claude plan, the same usage Cowork draws on, so the page uses the
fastest model and sends only the last few messages; the forms cost nothing. Claude there can only make the changes the
page offers; it never touches the page's code. Where Claude is not available
to the page, the box hides and the forms and this chat remain.

The student owns the page. They edit it on the page itself and press
**Save**, and they can ask you in the chat to change the workflow or the
page. When they ask, you save the map's files into their fleet repository's
folder, and they commit, push, and open a pull request themselves, in the
terminal. They can keep several maps, one for each workflow and project.

Nothing runs on the page. Steps run in Cowork, by the student or with you,
and the student records each run on the map.

## What to read

Use what the student already has, in this order:

0. **Existing maps.** First, list the workflows already in the repository
   (`workflow/*/map.md` in the attached fleet folder) and in this chat, and
   ask whether the student is changing one of them or starting a new one.
   Never start a new map over one they asked to change. A map made by
   `cms-workflow` (a section in `workflow/map.md`, or JSON pasted from it) is
   converted, never rebuilt: keep its steps, arrows, and change log, add
   lanes, sources, and icons, and give it its own folder `workflow/<id>/`.
   Leave the old section where it is.
1. Claude's corrected reading of their drawing, earlier in this project's
   chat (the Week 10 reading, a Markdown list of steps and arrows).
2. The photo of the drawing, in this chat or the project's files.
3. `workflow/workflow.md`, and `workflow/stages/` if it exists.
4. A description the student types now.

Read `thesis.md`, in the project's knowledge or the attached folder, for
abbreviations and terms. Ask for a drawing or a description only when none
of these exists.

## The rules

- **Add no step that is not in the drawing or the student's words.** Do not
  improve the workflow while mapping it. Suggestions go in the chat, never on
  the map, until the student accepts them.
- **Mark every guess UNSURE.** A word you cannot read, an arrow you are not
  sure of, a step with no one to do it or check it, a source you inferred:
  put `UNSURE` in that field and say what you think it is in the `unsure`
  list. Settle each one with the student before calling the map done.
- **At least one step is the student's alone.** Mark it `mine`. If the
  drawing does not say which, ask.
- **"You" or "it" is the student's answer.** For each step, ask whether
  Claude is a "you" there (someone they consult) or an "it" (a tool they use),
  and who is credited with what the step produces. Write their answers in
  `you_or_it` and `credited`. Never fill these in yourself.
- **How to run each step in Cowork.** Write `run` as what the student would
  ask Cowork, in their words where possible. A step done by hand says so.
- **Sources are cards too.** Ask which data sources each step draws on (an
  archive, an API, a library, interviews, someone else's data) and make a
  source card for each, with an arrow to the step that uses it.

## The map's data

The page keeps the whole workflow in one JSON block,
`<script type="application/json" id="workflow">`. Its fields:

- `title`, `question` (one line, from the thesis), `begun` (`YYYY-MM-DD`).
- `id`: a short name made from the title (lower case, digits, hyphens). It
  names the workflow's folder, `workflow/<id>/`. `kind`: what kind of flow
  this is, in the student's words ("research", "rough-cut editing").
- `repo`: `{"owner", "name", "branch"}`, the fleet repository, from the
  attached folder's `git remote -v` or by asking. Branch defaults to `main`.
  Leave owner and name empty when there is no repository yet.
- `lanes`: in order, each `{"id", "name", "kind", "icon"}`, `kind` one of
  `sources`, `me`, `claude`, `other`. The default is Sources, Me, Claude, and
  Someone or a script. Propose lanes that suit the kind of flow (an editing
  flow might have Me, Claude, My editor, A script) and settle them with the
  student like any UNSURE. Sources is always first.
- `sources`: each `{"id", "name", "icon", "kind", "link", "gives", "unsure"}`.
  `id` starts with `src-`. `kind`: `api`, `download`, `by hand`, or
  `someone else`. `gives`: what comes out of it, in a few words.
- `steps`: in order, each with `n` (a number or a label such as `2a`), `name`,
  `in`, `out`, `who` (`me`, `Claude`, `a script`, `someone else`, or
  `UNSURE`), `check` (`by` and `how`), `run`, `state` (`not tried`, `tried`,
  `works`, `broken`) with `state_date` and `state_note`, `you_or_it`,
  `credited`, `mine`, `unsure`, and `lane` (the lane's id), `col` (its place
  from left to right, 0 first), `icon`.
- `arrows`: each `{"from", "to"}`, with `"loop": true` when it goes back to an
  earlier step, `"unsure": true` when you are not sure of it, and an optional
  `label`, what moves along it ("12 clips"). `from` may be a source's id.
  Keep every arrow in the drawing, loops included.
- `changes`: the change log, newest first, each `{"date", "what"}`.
- `icons`: icons fetched for this map (see "Icons").
- `runs`: what each step did, oldest first, each `{"id", "date", "step",
  "round", "pass", "result", "note", "outputs", "check"}`. `result` is
  `works`, `broken`, or `tried`; `outputs` lists file paths in the fleet
  repository; `check` is `{"by", "result", "note"}` with `result` one of
  `pass`, `fail`, `not checked`. `pass` counts the step's runs within the
  round, so a step a loop sends back to runs as pass 1, pass 2, and so on.
  Never rewrite or drop a run; a wrong one is corrected by a later run.
- `round`: the current round, a whole run of the workflow from the start.
  The student starts the next with **New round** in View mode.

The block must stay valid JSON, or the page shows an error in place of the
map: escape double quotes inside strings as `\"`, leave no trailing commas,
and write `<\/` wherever a string contains `</`.

## Icons

Every source and step has an `icon`. The page carries about forty brand
icons (TMDB `themoviedatabase`, YouTube `youtube`, Vimeo `vimeo`, Internet
Archive `internetarchive`, Zotero `zotero`, Wikipedia `wikipedia`, Google
Drive `googledrive`, GitHub `github`, IMDb `imdb`, Letterboxd `letterboxd`,
Spotify, SoundCloud, Reddit, Instagram, TikTok, X, arXiv, Google Scholar,
Notion, Obsidian, and more) and about sixty generic ones from Lucide (`film`,
`globe`, `mic`, `database`, `file-text`, `folder`, `tag`, `book-open`,
`pen-line`, `git-compare`, `download`, `search`, `camera`, `chart-column`,
`scissors`, `tv`, `notebook-pen`, `send`, `users`, and so on). Use a brand
icon for every named service.

**Getting a new icon.** When a service is not among them, fetch its icon
instead of settling for a generic one, and add it to the map's `icons` under
the name you give the card's `icon`. Try, in order:

1. **Simple Icons 16.36.0** (CC0). Find the brand's slug at simpleicons.org
   (lower case, letters and digits). In Cowork, download the package from the
   npm registry:
   `curl -sL https://registry.npmjs.org/simple-icons/-/simple-icons-16.36.0.tgz | tar xz package/icons/<slug>.svg package/data/simple-icons.json`
   In Claude Code, `https://cdn.jsdelivr.net/npm/simple-icons@16.36.0/icons/<slug>.svg`
   also works. Take the `d` of its `<path>`, and the brand's `hex` from
   `data/simple-icons.json`. Add
   `"<slug>": {"path": "<d>", "color": "#<hex>", "source": "simple-icons 16.36.0", "license": "CC0-1.0"}`.
2. **Lucide 1.66.0** (ISC), for a generic thing the page lacks, from
   `https://registry.npmjs.org/lucide-static/-/lucide-static-1.66.0.tgz`
   (`package/icons/<name>.svg`). Add the elements inside its `<svg>` as
   `"<name>": {"svg": "<the elements>", "source": "lucide 1.66.0", "license": "ISC"}`.
   The page keeps only `path`, `circle`, `rect`, `line`, `polyline`, `polygon`,
   and `ellipse` elements and their geometry; anything else is dropped.
3. **The student's own SVG**, when neither has it (Simple Icons drops some
   brands at their owners' request): ask them for the logo as SVG, for example
   from the service's press page, keep one path scaled to 24 by 24, and record
   where it came from in `source`.
4. **Otherwise the generic icon** for its kind, with a line in `unsure`.

If the sandbox cannot reach the registry, say so and keep the generic icon;
the student can fetch it later from Claude Code.

## Making the page

Start from `references/page-template.html` in this skill. Replace only the
JSON block and the `<title>` text; keep everything else exactly as it is.
Name the artifact with the map's title, so a student with several maps can
tell them apart.

**Publishing.** Publish the page as the student's own artifact with the
capabilities `{"artifact": {}, "sample": {}, "dictation": {}}`, when your
artifact tool accepts them: `artifact` lets the page save itself, `sample`
runs the **Tell the map what to change** box, and `dictation` its microphone.
Declare nothing else: the page does not use connectors.

If the publish refuses `sample` or `dictation`, publish again with
`{"artifact": {}}` alone; the box then hides itself. If it refuses `artifact`
too, publish without capabilities and tell the student in one line that this
page cannot save itself yet; they keep changes by pressing **Copy the map**
and pasting into the chat. Never fall back to the `cms-workflow` template.

**Then tell the student, briefly:** the page opens in **View**: open a card
to see what it did, and record each run there. Switch to **Edit** to change
the workflow, or type the change in **Tell the map what to change** and
press **Apply** on Claude's plan (the first time, the page asks to use their
Claude account). The box runs on their own Claude plan, so small edits are
better made in the forms, which are free. Press **Save** (or Cmd or Ctrl + S) to keep any change; every
save reloads the page. Press **Play** or **Step** to
watch the walkthrough. To keep a copy in the repository, they ask you to save
the map to their fleet folder, then commit and push it themselves. Then go
through every `UNSURE`
with them, one step at a time.

## Changing the map or the page in the chat

- **Start from the page's current data.** The page saves itself, so your copy
  of the data may be old. Read the live page if you can. If you cannot, or the
  student has edited on the page since your last publish, ask them to press
  **Copy the map** and paste it here, and take the data from that. Your copy
  of the code is current: only you change it.
- Update the artifact in place, in the same conversation, with the same
  capabilities. In a later chat, start from `workflow/<id>/map.html` in the
  attached folder, or from the student's published page, never from this
  skill's template, so their version carries on.
- Add a change log line for every change, newest first. A change to the page
  itself reads like "page: wider Claude lane".
- Never drop a step, a source, an arrow, a lane, or a change log line unless
  the student asks.
- **Recording a run** adds one entry to `runs`: `round` is the map's
  `round`, `pass` is one more than the step's runs already in that round,
  `id` is `run-` and the next unused number. Ask the student what it made
  (`outputs`), how it went (`result`, `note`), and whether it was checked,
  by whom, and what the check found. Then set the step's `state`,
  `state_date`, and `state_note` to the run's, and add a change log line
  like "ran step 2 (pass 2): works, re-tagged with intertitles". With the
  fleet folder attached, also append the run to `workflow/<id>/runs.jsonl`
  as one line:
  `{"date", "step", "round", "pass", "result", "note", "outputs", "check"}`.

**Changing how the page looks or works.** The page's code is in the
`<style data-wf>` and `<script data-wf>` elements. Edit inside them. Keep:

- the `data-wf` mark on every style and script of the page's own (the page
  saves by copying exactly those elements, so code without the mark is lost
  on the next save);
- the JSON block, the empty `<div id="app"></div>`, and the order: title,
  styles, JSON block, app, scripts;
- the save code in `WF.rebuild` and `WF.serializeData`;
- no `src=`, `href="http`, `@import`, or `url(http`: the page loads nothing
  from the network;
- no `</script>` inside a script: write `<\/script>`.

A change that would break one of these is explained to the student instead of
made.

## Saving a copy in the repository

The page saves itself; it never writes to the repository. When the student
asks ("Save my map to my fleet folder"), with the fleet folder attached:

1. Start from the page's current data, as above: read the live page, or ask
   the student to press **Copy the map** and paste it.
2. Write three files into `workflow/<id>/`: `map.md` (the JSON, fenced as
   `json`, under `## <title>`), `map.html` (the whole page as published,
   with that data in its JSON block), and `runs.jsonl` (one line per run, as
   above) once any run is recorded.
3. Tell the student the commands to run themselves, in the terminal (Cowork's
   sandbox cannot push):

       cd ~/cms-f26-fleet-<username>
       git add workflow/<id>/
       git commit -m "<what changed>"
       git push

   and, if they work on a branch, to open a pull request on GitHub. Never
   commit or push for them.

With no folder attached, give the student the whole JSON block, fenced, in the
chat, and tell them to keep it: it is what they paste to continue in a later
chat or save to the folder later.
