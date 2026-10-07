# Annotation rules: the annotator's contract

Hand this file, `codebook.json` and one `work/<id>.sentences.json` to the
annotator. Nothing else: not the students' hand annotations, not other
reviews' tuples.

## Output

Write `tuples/<id>.json`:

```json
{"review_id": "r1", "annotator": "claude",
 "tuples": [
  {"sentence": 3, "category": "ACTING", "aspect": "Mara Ellis",
   "opinion": "astonishing restraint", "polarity": "very_positive",
   "confidence": "high"},
  {"sentence": 7, "category": "PACING", "aspect": null,
   "opinion": "drags", "polarity": "negative", "confidence": "medium"}
 ]}
```

`sentence` is the number in `sentences.json`. `category` is an `id` from
`codebook.json`. `polarity` is one of the codebook's `polarities`.
`confidence` is `high`, `medium` or `low`. There is no field for reasons:
the quotation is the evidence.

## Read first, then annotate

Read the whole review before the first tuple: pronouns, irony and the
critic's overall stance depend on context. Then go sentence by sentence. A
sentence may give zero, one or several tuples.

## What counts

1. **Only the critic's own judgment of this film.** Skip plot summary,
   credits, running times, other people's opinions (audiences, other
   critics, "some have called it"), and judgments of other films. A comparison
   counts only for what it says about this film ("sharper than Snowpiercer"
   is a positive judgment of this film).
2. **The film's world is not the critic's judgment.** "The family lives in
   squalor" describes the film. "The squalor is played for cheap laughs"
   judges it. Dark subject matter is not a negative review: a horror film
   praised as horrifying is praised.
3. **The opinion is copied, not described.** The words that carry the
   judgment, copied exactly and contiguously from the sentence, 1 to 6 words.
   Never paraphrase, never join separated words with "...". If capturing the
   judgment needs a whole clause, skip it.
4. **The aspect is copied or empty.** The smallest noun phrase naming what is
   judged ("the score", "the final act", "Mara Ellis"), copied exactly, no
   leading "the" needed. Use `null` when the sentence does not name it (a bare
   "it" or "this"). Never write a name that is not in the sentence. The aspect
   and the opinion must not overlap: in "an insubstantial farce" the aspect
   is "farce" and the opinion "insubstantial".
5. **One row per opinion word.** "An enjoyable, elegant, scabrous movie" is
   three rows on the aspect "movie". A concessive pair ("flawed, yet deeply
   human") is two rows with opposite polarities.

## Category

Exactly one `id` from `codebook.json`. Prefer the specific category over the
catch-all whenever the sentence names a craft aspect ("beautifully shot" is
about the images, not the film as a whole). If nothing fits, use the closest
and set `confidence` to `low`.

## Polarity

- `positive` / `negative` is the normal case: "great", "moving",
  "horrible", "dull".
- `very_positive` / `very_negative` only when the opinion words themselves
  contain a reinforcing word: an intensifier ("very", "utterly"), a
  superlative ("the best", "finest"), an extreme word ("masterpiece",
  "unbearable"), or "too" ("too long"). `absa.py` downgrades any `very_*`
  without one.
- Negation flips the sign. Hedges ("a bit", "rather", "slightly") never
  intensify.
- Irony and sarcasm are labelled by intended meaning, but only with evidence
  in the text: scare quotes, overt exaggeration, a contradicting clause nearby.
- `neutral`, only if the codebook lists it: the aspect is discussed in an
  evaluative passage but no stance is taken.

## When unsure

Skip it. Precision beats coverage: a skipped sentence costs nothing; a
doubtful tuple costs the dataset. If you keep a doubtful one, set
`confidence` to `low`.
