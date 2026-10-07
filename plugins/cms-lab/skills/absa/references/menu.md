# The menu: codebooks other people built — released after your own

You wrote your categories first. Now compare. Nothing here is the right
answer; each codebook below is a set of decisions made for a purpose. For
every idea you borrow, say what it lets you see and what it makes easier to
overlook, and record it under **Borrowed** in `experiment.md`.

Fill this in before and after:

> We sort opinions about ___ into ___ because our question is ___.
> A category nobody uses means ___.

## 1. The format: SemEval

The SemEval shared tasks on aspect-based sentiment analysis (Pontiki et al.,
2014, 2015, 2016) fixed the shape most work uses: an **opinion target
expression** (the words naming what is judged, or NULL), an **aspect
category** written `ENTITY#ATTRIBUTE` (`FOOD#QUALITY`, `SERVICE#GENERAL`),
and a **polarity** (positive, negative, neutral; 2014 also had "conflict").
Domains: restaurants, laptops, hotels, and from 2016 eight languages.

## 2. Codebooks from easier domains: SentEMO

SentEMO (LT3, Ghent University; De Geyndt et al., 2022) annotated Dutch
reviews and customer messages for six domains. Each has entities with
attributes, plus `general` and `misc` fallbacks. Hotels, for example:

| Entity | Attributes |
|---|---|
| ROOM | ambiance, cleanliness, comfort, price, general, misc |
| PERSONNEL | communication, friendliness, hospitality, service, general, misc |
| FOOD & DRINKS | appearance, availability, options, price, quality, general, misc |
| HOTEL | appearance, cleanliness, comfort, location, price, quality, reliability, general, misc |

Their polarity scale has five levels, and **very positive / very negative
only when an intensifier is explicitly present** ("very friendly"). Hotels
are easier than films: guests judge things you can point at.

## 3. Earlier film schemas

| Study | Aspects |
|---|---|
| Zhuang, Jing & Zhu (2006), movie review mining | six film-element classes (overall, screenplay, character design, vision effects, music and sound, special effects) and six people classes (producer, director, screenwriter, actor, music, technicians) |
| Thet, Na & Khoo (2010), discussion boards | overall, cast, director, story, scene, music |
| Parkhe & Biswas (2014) | movie, plot, acting, direction, screenplay, music |

## 4. A worked example: the instructor's *Parasite* codebook

23 categories, built from the three studies above plus a pilot reading of
about 30 reviews: 10 mapped from earlier work, 4 refinements, 9 new. During
annotation CHARACTER#DESIGN was retired (critics judged how roles were
written without a compact sentiment phrase) and folded into ACTING#GENERAL.

| id | name | covers | vs. earlier work |
|---|---|---|---|
| `MOVIE#GENERAL` | Overall judgement | a verdict on the film as one object, no craft aspect attached | mapped |
| `MOVIE#REWATCHABILITY` | Rewatch value | whether it rewards a second viewing | new |
| `STORY#PLOT` | Plot and premise | events, premise, plausibility | mapped |
| `STORY#TWIST` | The mid-film reveal | the turn, discussed as a turn | refinement |
| `STORY#ENDING` | Ending and coda | the final movement | refinement |
| `STORY#PACING` | Pacing | rhythm, runtime, sagging or accelerating | refinement |
| `STORY#GENRE` | Genre blend | mode and mixing: comedy, thriller, satire | new |
| `THEME#SOCIAL_COMMENTARY` | Class politics | the argument, and how well it is made | new |
| `THEME#SYMBOLISM` | Symbols and motifs | stairs, smell, the stone, read as signs | new |
| `CHARACTER#DESIGN` | Characterisation | roles as written (retired) | mapped |
| `ACTING#GENERAL` | Performances | delivery, restraint, the ensemble | mapped |
| `DIRECTION#GENERAL` | Direction | authorial control, staging, command of tone | mapped |
| `SCREENPLAY#STRUCTURE` | Screenplay | setup and payoff, construction | mapped |
| `SCREENPLAY#DIALOGUE` | Dialogue | individual lines and exchanges | refinement |
| `CINEMATOGRAPHY#GENERAL` | Cinematography | framing, movement, light, the look | mapped |
| `PRODUCTION_DESIGN#GENERAL` | Production design | the houses as built sets, props, costume | mapped |
| `MUSIC#GENERAL` | Score and sound | score, cues, sound design | mapped |
| `EDITING#GENERAL` | Editing | cuts, montage | mapped |
| `TONE#HUMOR` | Humour | whether it is funny | new |
| `TONE#TENSION` | Tension | suspense, dread, shock as experience | new |
| `TRANSLATION#SUBTITLES` | Subtitles | the English subtitles | new |
| `CULTURAL_CONTEXT#GENERAL` | Korean context | local referents, universal or not | new |
| `RECEPTION#AWARDS` | Awards and hype | the prizes and the discourse, not the film | new |

What the 2,045 opinions in 107 reviews showed: one in five landed in
`MOVIE#GENERAL`, the catch-all; music, editing and subtitles together drew 22.
A category almost nobody uses is a finding about the reviews, or about the
codebook. The schema's rule for that: below 2% of opinions, a category is a
merge candidate unless it is central to the question.

**A useful pattern: core plus extensions.** A small core works for most
films (the film overall, story, acting, direction, screenplay, images, sound,
themes). Extensions belong to one film or one question: the twist in
*Parasite*, the subtitles of a foreign-language release, the effects of a
blockbuster, a star's persona.

## 5. Hard cases, with one rule each

| Case | Rule |
|---|---|
| The house as set or sign | Judged as a built object: design. Read as meaning: symbolism. Both: two tuples. |
| The film's world vs. the critic's judgment | Describing squalor, cruelty or horror is not a negative opinion. Only the critic's evaluation of the film counts. |
| Another film in the sentence | Annotate only what it says about this film; never record sentiment about the other. |
| Someone else's opinion | "Audiences gasped", "some call it overrated": skip, or route to reception if the hype itself is the topic. |
| Mixed in one sentence | Decompose first: different aspects, separate tuples. Same aspect both ways: two tuples, opposite polarity. |
| The prize vs. the film | "A worthy Palme d'Or winner" judges the film; "the Academy finally got one right" judges the award. |
| Plot summary | No opinion. Either skip it or code it neutral, and say which. |
| Irony | Label the intended meaning, only with evidence in the text. |

## 6. Polarity choices

- **Neutral or not.** Without neutral, "no tuple" stands in for it. In the
  *Parasite* corpus, 69% of sentences carried no opinion: reviews are mostly
  description. Either choice is defensible; say which you made.
- **Intensity.** A reinforcing-word rule (SentEMO) keeps "very" honest in a
  genre that writes in superlatives. Decide whether "too" counts: "too long"
  marks excess, which you may or may not want to call intensity.
- **Conflict.** One aspect praised and criticised in the same breath: SemEval
  2014 had a label for it; later editions dropped it.

## 7. How sure are you?

- **Self-consistency**: run the same annotator twice. *Parasite*: 98% same
  polarity on matching opinions, but only 77% of opinions picked both times.
  Stability, not correctness: a model can be consistently wrong.
- **Inter-annotator agreement**: two people annotate the same sample without
  seeing each other's work. Report Cohen's kappa (two annotators), Fleiss'
  kappa (more) or Krippendorff's alpha (any number, missing data allowed).
  For spans, report F1 between annotators, as SemEval does.
- **Baseline**: before quoting an accuracy, say what "always positive" would
  score on your data.

## Sources

- Pontiki, M., et al. SemEval-2014 Task 4; SemEval-2015 Task 12; SemEval-2016 Task 5: Aspect Based Sentiment Analysis. Proceedings of SemEval.
- De Geyndt, E., et al. (2022). SentEMO: A Multilingual Adaptive Platform for Aspect-based Sentiment and Emotion Analysis. WASSA 2022, pp. 51–61. Annotation guidelines: LT3, Ghent University.
- Zhuang, L., Jing, F., & Zhu, X. (2006). Movie review mining and summarization. CIKM '06.
- Thet, T. T., Na, J.-C., & Khoo, C. S. G. (2010). Aspect-based sentiment analysis of movie reviews on discussion boards. Journal of Information Science 36(6).
- Parkhe, V., & Biswas, B. (2014). Aspect based sentiment analysis of movie reviews: finding the polarity directing aspects.
- Campregher Paiva, I., & Diecke, J. (2024). Revisiting Weimar Film Reviewers' Sentiments. Journal of Cultural Analytics 9(4).
