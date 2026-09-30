# A harvester skill: what it must contain

A skill is a folder with a `SKILL.md`. The student's goes in their fleet
repository at `.claude/skills/<name>/SKILL.md`. Its frontmatter has a `name`
and a `description` saying when Claude should use it.

The body is finished only when it answers four questions in plain sentences:

1. **The metric.** The full operationalization sentence: what is counted, what
   is left out, what the terms mean.
2. **The source.** Which resource, how it is reached, what its terms of use say,
   and the name of the environment variable that holds the key. The key itself
   is never in the skill.
3. **The losses.** What this source cannot tell you about the metric, and where
   it is uneven by country, decade, or language.
4. **The output.** Where the data is stored, in what shape, and what each run
   records: date, query, source. A dataset nobody can trace is not data to
   defend.

Key file: the student copies `.env` to the root of their repository, where the
starter's `.gitignore` already ignores it. Harvested data stays local unless
the instructor says otherwise; add its folder to `.gitignore`.

## Test it cold

In a fresh session, ask for the metric in one sentence without explaining how.
If Claude asks something the skill should have answered, fix the skill, not
the prompt. Then run it for a second case and confirm each output says which
run it is.

## Skeleton

```markdown
---
name: <short-name>
description: <when to use it, in one sentence>
---

# <Metric, in words>

## Metric
<the operationalization sentence>

## Source
<resource, how reached, terms, key variable name>

## Losses
<what this cannot tell you>

## Output
<folder, file shape, run record>

## Steps
1. ...
```
