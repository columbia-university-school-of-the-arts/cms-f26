# From five reviews to a hundred

For a final project. This is the route the instructor took for *Parasite*
(107 reviews, 4,026 sentences, 2,045 opinions), with each place it went
wrong. Read it before you start; most of the work is not annotation.

## 1. Find the reviews

- **A ready-made dataset** is the legally safer start. The Kaggle "Massive
  Rotten Tomatoes Movies & Reviews" set (scraped April 2023, CC0 as declared
  by the uploader) has 1,444,963 critic reviews of 69,263 films. Each row is a
  one-line snippet plus a link to the full review. The CC0 label is the
  uploader's claim; the review texts still belong to their publications.
- **Read the dataset page like a source.** "Usability 10.00" scores how well
  the page is documented, not how clean the data is. "Expected update:
  annually" on a page last updated years ago is a promise, not a fact. Reviews
  dated 1 January 1800 are placeholders. The column is spelled
  `publicatioName` in the original.

## 2. Do not open it in Excel

- Excel stops at **1,048,576 rows**. The review file has 1,444,963: Excel
  shows a warning once, then drops the rest. A pivot table whose grand total
  is 1,048,575 is measuring Excel, not the data.
- Excel turns a critic's `4/5` into a date (4 May, in a European locale).
- Ask Claude Code instead: "Open the reviews CSV with pandas, keep the rows
  for `<movie id>`, and count unique `reviewId`s." Count unique IDs, not rows:
  *Parasite* had 954 rows for 477 reviews.
- Never double-click a downloaded CSV into a spreadsheet you have not
  inspected; open it as text or with pandas first.

## 3. Get the full texts, politely

- Filter before fetching: English, a real review (not a podcast, a list or a
  "best of the year" page), a working link. *Parasite*: 477 reviews became
  344 candidates.
- Fetch with an honest script: `requests` plus `trafilatura` in a
  project `.venv`, one request every few seconds, cache every page to disk so
  you never fetch twice, respect `robots.txt`. Never disguise the script as a
  browser and never work around a login, paywall or bot block. In Claude
  Code, every new website asks for your approval; *Parasite*'s 344 links
  sat on 323 different sites.
- Expect low yield. About 4 in 10 approved sites gave usable text; in the end
  108 of 344.
- Guard every page: keep it only if it names the film or the director and is
  longer than 400 characters. That caught a review of a different 1982 film
  called *Parasite* and a site that had turned into gambling spam. It did not
  catch a page that was a quotation about CinemaScope, or a page whose text
  appeared twice; `absa.py split` now warns about repeated sentences.

## 4. Build the codebook from a pilot

Read the literature (see `menu.md`), read 20 to 30 reviews, then draft. Write
a definition, include and exclude lists, and at least one confusion rule per
category. Keep the full schema as the document of record and give the
annotator a short digest of it: shorter prompts were cheaper and no worse.

## 5. Pilot the prompt on the same few reviews

Ask for a pilot of five reviews and **stop**. Read every tuple. Change one
thing, rerun on the same five, compare. On *Parasite*, three pilots on the
same five reviews gave 200, then 59, then 143 tuples:

- Pilot 1 asked for everything (neutral, emotions, implicit opinions):
  65 neutral rows, mostly plot summary; emotions mostly "none"; unpleasant
  characters coded as bad writing.
- Pilot 2, explicit pairs only: 76% cheaper and four times faster, but too
  strict, and three adjectives ended up in one row.
- Pilot 3 kept: opinion words required, aspect optional, one row per opinion
  word. It also caught sentences about *Shoplifters* credited to *Parasite*.

A cheaper model tier, tested on the same prompt, lost recall exactly on the
negative reviews the corpus was short of. Test before you economise.

## 6. Validate with code, then with people

- **Code** (`absa.py check` does the core of this): every quote found again
  in the text, every label from the allowed set, the intensity rule, no
  overlapping spans, one row per opinion word, rows naming another film
  dropped. A rule written in a prompt is a wish; a rule in the validator is a
  rule. On *Parasite*: 0 offset mismatches in 2,045 rows.
- **Self-consistency**: re-annotate ten reviews in fresh sessions and compare
  (`absa.py agree`). Stability is not accuracy.
- **People**: two humans annotate a random sample (10 to 20%) without seeing
  each other's work or the model's; report agreement (Cohen's kappa,
  Krippendorff's alpha) and the model's agreement with them. The *Parasite*
  corpus does not have this yet. It is the step that turns a dataset into
  evidence.
- **Read the output.** The most important *Parasite* errors were found by
  reading, not by code: 11% of opinions were lone adverbs; "film", "movie",
  "picture" and "Parasite" were counted as separate things; only two very
  negative opinions existed because the intensity check could only
  downgrade, so a hand audit of all 168 negatives upgraded 20 and flipped 5
  signs ("a searing social commentary" had been read as an attack).

## 7. Keep the files in step

Derive every summary from the tuple file, in code, every time. *Parasite*'s
`reviews.csv` kept counts from before the audit until someone noticed the
numbers disagreed. Keep raw model outputs, so a fix can be re-applied without
re-annotating.

## 8. Know what your corpus is

102 of the 107 *Parasite* reviews were fresh. "The sentiment of *Parasite*" is
really a statement about Rotten Tomatoes' sample of English-language critics
whose pages could be fetched. Say so on every chart. `rt_added_date` is when
Rotten Tomatoes added a review, not when it was published.

## 9. Copyright and sharing

The analysis is yours; the review texts are not. Keep full texts local and out
of any repository. Share the tuples, the sentence offsets, the URLs and short
quotations. If you build a dashboard that shows sentences, put it behind a
password, as the *Parasite* explorer does. Rules differ by country (US fair
use; the EU's text-and-data-mining exceptions for research); for anything you
publish, ask the library.
