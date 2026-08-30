---
name: ledger
description: Use when the student installs, vendors, or borrows anything from another project, or asks to record what their fleet is made of. Appends a correctly shaped entry to notes/INTEGRATIONS.md or notes/PATTERNS.md.
---

# Recording what you borrowed

Two ledgers, and one question sorts them: **does their code run in your fleet?**

- Yes, it executes here: `notes/INTEGRATIONS.md`. This is a bill of materials.
- No, you read it and wrote your own: `notes/PATTERNS.md`. This is a bibliography.

Log the entry **before** installing anything, so the pause is structural.

## Appending to INTEGRATIONS.md

Ask for anything missing, then append:

    ## <project name>
    - Source: <repo URL or package> @ <version or commit>
    - Mode: depend | vendor
    - License: <license identifier> (<what it requires of you>)
    - Why: <the capability you lacked>
    - Changed: <what you altered, or "nothing">
    - Risk if it goes away: <what stops working>

`depend` means installed and unmodified. `vendor` means copied into this
repo and modified, which means the license travelled with the file and you
now own maintenance.

## Appending to PATTERNS.md

    ## <the idea, named>
    - Source: <project and file, or text and page>
    - Idea taken: <the design in one or two sentences>
    - How mine differs: <what you did instead>
    - Why rebuilt rather than installed: <the reason>

## Rules

- Never invent a license. Open the LICENSE file and record what it actually
  says: the SPDX identifier when the project publishes one (`MIT`,
  `Apache-2.0`, `CC-BY-NC-SA-4.0`), otherwise the license's name exactly as
  the file words it, because not every license has an SPDX id. A project
  with no LICENSE file at all is `unlicensed` - write that down and say it
  out loud, because unlicensed code carries no permission to use it.
  The seed entry already in `notes/INTEGRATIONS.md` is a worked example of
  the shape.
- One entry per borrowing. Appending twice for the same project is a sign
  the mode changed, so update the existing entry instead.
- A borrowed repo is code about to run on this laptop with these
  credentials present. Say so before installing.
