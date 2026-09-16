# How this course works

Coding for Media Studies, autumn 2026. Version 2026.09.06.

This page is the whole term in one sitting. Each session has its own sheet
in this folder, `week-01.md` onward, with that night's clock and steps. Read
this once, then read the sheet for the week.

---

## In one sentence

Over thirteen weeks you build a small fleet of research agents, run it on
your own thesis topic, and study what it did. The thing you build is the
thing you study.

No coding experience is needed. The course asks you to be precise and to
check. Everything runs on the Claude Pro account you bought before term.

---

## Three places

Every session moves through the same places, in the same order.

- **Cowork** is Claude working on a folder you chose, inside the Claude
  desktop app. Here you do the week's research task by hand: read, compare,
  classify, search, and watch where it goes wrong.
- **Claude Code** is Claude with a terminal and your repository. Here you turn
  what you just did by hand into something that runs again without you.
- **Cloudflare** hosts what you built, from Week 6. Your fleet's tools become
  a small service on the web that the fleet can call.

Two beats a session: by hand first, then in code. In Week 1 both beats run
in Cowork. The third beat arrives in Week 6 and returns in a few later weeks.

Week 1 has no terminal. The terminal comes in Week 2, in the room, with both
of us present, so nobody meets an install alone at home.

---

## The artifact

In Week 1 you make one thing from the course readings, in Cowork: a map, a
genealogy of one idea, a timeline of the arguments, a glossary with
cross-references, a debate staged between three authors. Your choice, inside
one shape: every claim cites a file, at least two texts are related and the
relation is named, and it is one Markdown file. That file is the spine of the
first six weeks.

| Week | What happens to it |
|---|---|
| 1 | You make it, prove part of it wrong, and make it again under fixed rules. |
| 2 | It becomes the first commit in your repository. Claude Code checks every citation in it against your folder. |
| 3 | It gains metadata from the open scholarly web, and you meet the wall in front of the licensed one. |
| 4 | The conversion underneath it, PDF to text, is named, logged, and made yours. |
| 5 | A shared core of agents reproduces it, and you compare the two. |
| 6 | Its relation lines become edges in a graph. |

From Week 7 the artifact is the graph, and the graph belongs to your fleet.
The second half of the term builds your specialist, runs the fleet on your
own research, and ends with you critiquing what it did.

---

## Your repository

In Week 2 you clone a repository that was made for you before term, named
`cms-f26-fleet-` followed by your GitHub username. It starts nearly empty and
grows about one file a week. It is yours: you push to it, the rest of the
class can read it, and nobody else writes to it.

Everything about working inside it is documented from the inside. Start at
its `README.md`, then `docs/map.md`.

It has two remotes. `origin` is your repository. `upstream` is the course
starter, and `/checkpoint` restores the course scaffold from it while leaving
your own files alone. You run it once as Week 2 homework, so that you have
met it before the week something breaks.

---

## What is yours, and what travels

| Folder | What it holds | Leaves your machine? |
|---|---|---|
| `corpus/` | The readings, converted to text | **Never.** The readings are copyrighted, and a conversion is a copy. Git ignores this folder on purpose. |
| `cowork/` | The passes you did by hand | Yes, it is committed. |
| `runs/` | What your fleet produced | Yes. |
| `graph/` | Nodes and edges, one line each | Yes. This is the part made to be shared and compared. |
| `notes/` | Two ledgers, below | Yes. |

The two ledgers are `notes/INTEGRATIONS.md`, which records code that runs in
your fleet and where it came from, and `notes/PATTERNS.md`, which records
ideas that shaped it. A classmate's idea counts as an idea and goes in the
second ledger with their name. Borrowing is expected here; the mistake is
leaving it unrecorded.

---

## The plugins

Capability arrives as plugins from the course marketplace,
`columbia-university-school-of-the-arts/cms-f26`. Each is installed once, in
the room, the week it is needed.

| Week | Plugin | Where | What it adds |
|---|---|---|---|
| 1 | `cms-corpus` | Cowork | `/corpus-artifact`, which makes your artifact under fixed rules and says what it could not determine. |
| 2 | `cms-starter` | Claude Code | The ledger skill and `/checkpoint`. |
| 5 | `cms-scholarly` | Claude Code | Scholarly search that replaces a general-purpose fetch, and the question of why. |
| 6 | `cms-graph` | Claude Code | The graph. |

The marketplace syncs automatically, so a fix reaches you without your doing
anything. In Week 9 the direction reverses: you publish to the place you have
been installing from.

---

## When stuck

- In the room, say so. Every week has two instructors and a projector. Read
  us the exact text on your screen rather than retyping it from memory.
- The week's sheet, in this folder, has that night's steps and what to do
  when each one fails.
- Installing, or on Windows: the `README.md` and `WINDOWS.md` at the top of
  this repository.
- Your repository broke: its `docs/recovering.md`, then `/checkpoint`.
- Between sessions: the course site on Courseworks.
