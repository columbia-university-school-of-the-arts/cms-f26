---
name: corpus-map
description: Use when asked specifically for a table of a folder of course readings — each reading, its central claim, the week it is assigned, one text it argues with. A fixed-shape request handled by corpus-artifact; kept as its own command for the table.
---

# corpus-map

This is `corpus-artifact` with the shape fixed. Follow the `corpus-artifact`
skill in this plugin exactly, with the requested shape set to this table:

| Column | Contents |
|---|---|
| Reading | Author surname and short title |
| Central claim | One sentence, in the author's terms rather than yours |
| Week | The week it is assigned, or `unknown` |
| Argues with | One other text in this corpus, and the point of contact |

Every "Argues with" cell must also appear as a line under `## Relations`, in
`corpus-artifact`'s form. All four of that skill's requirements apply.
