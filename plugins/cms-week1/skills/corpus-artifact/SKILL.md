---
name: corpus-artifact
description: "Use when asked to make anything from a folder of course readings — a map, a genealogy, a timeline, a glossary, a staged debate, a table — where the result must be checkable. Applies fixed rules to whatever shape is asked for: every claim sourced to a file and a quotation, every relation between texts stated as a line, every gap declared, every conversion loss named."
---

# Making an artifact from a corpus you did not write

A folder of readings is not yet a corpus. It becomes one when you can ask it a
question and check the answer.

This skill does not fix what you make. It fixes what makes it checkable. The
failure it guards against is not a wrong answer but a **fluent** one: an
artifact with every gap papered over, no indication of which claims were read
and which were guessed, and no way to tell the difference without redoing the
work.

## The shape is the student's

Take the shape the request asks for: a table, a genealogy of one idea, a
timeline of arguments, a glossary with cross-references, a debate staged
between authors, anything else. If no shape is given, ask for one before
producing anything. If the request cannot be made to relate texts to each
other, say so and ask again; "summarise each reading" is not an artifact under
these rules, because it relates nothing.

Produce one Markdown file. It will be committed to a repository next week and
compared with other students' files, so it needs a title line, the shape
named in one sentence under it, and the sections below in the order given.

## Four requirements

**1. Every claim carries its source.** After each claim about a text, name the
file it came from and give a quotation short enough to find by searching: a
few words, not a paragraph. A claim you cannot quote is a claim you inferred,
and it belongs in the gaps section instead.

**2. Every relation between texts is stated as a line.** Wherever the artifact
says that one text bears on another, add a line in this exact form, and
collect all such lines under a heading `## Relations` at the end:

    A — relation — B — evidence

where A and B are author surnames, the relation is one word or two (argues
with, extends, cites, contradicts, answers, borrows from), and the evidence is
a quotation from A or B short enough to search for. The artifact must contain
at least one such line. These lines are what next month's graph is built
from, so make them countable rather than eloquent.

**3. Declare what you could not determine.** End with a section headed
`## Could not determine`, listing every claim you guessed at, every cell or
entry you left empty, and every relation you suspected but could not quote,
with the reason. Reasons worth distinguishing:

- the text does not say
- the file is unreadable or badly converted at that point
- the answer is not in the corpus at all (an assignment week, for instance,
  lives in the syllabus rather than in the reading)
- two passages conflict and choosing between them is a judgement

**Never fill a gap to avoid leaving it empty.** A declared gap is a result. A
plausible sentence covering a gap is a fabrication, and it costs the reader
their ability to trust anything else in the file.

**4. Name what the conversion cost.** These readings are PDFs, and reading
them means extracting a text layer first. End with a section headed
`## What the conversion lost`, naming what is now missing or damaged: page
numbers, figures and their captions, tables, footnote anchors, columns run
together, characters garbled by OCR or a bad encoding. Be specific: name
files, not categories.

## Rules

- Never present the artifact as *what these texts say*. Present it as what you
  could establish from these files, in this form, today.
- If a reading is named in the syllabus but absent from the folder, say so. A
  hole in the corpus is worth more to the reader than a silent omission.
- Prefer "unknown" over a hedge. "Possibly extends Moretti" is a filled gap
  pretending to be an empty one.
- Do not add sections the shape did not ask for beyond the three required
  headings. The student chose the shape; keep it theirs.
