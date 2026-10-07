#!/usr/bin/env python3
"""absa.py: the checker and chart maker for the CMS review lab.

Python 3.8+ standard library only. Run it from ~/cms-lab/absa:

    python3 absa.py split            number the sentences of every reviews/*.txt
    python3 absa.py check            validate tuples/*.json, write tuples.csv + check_report.md
    python3 absa.py agree A.json B.json   compare two annotations of the same review
    python3 absa.py chart            write results.html from tuples.csv

The model proposes tuples; this file decides whether they are well formed.
It checks form (quotes copied exactly, labels from the codebook, the
intensity rule). It cannot check whether a judgment was read correctly:
that is what the hand check and the agreement table are for.
"""
import csv
import datetime as _dt
import html
import json
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

ROOT = Path.cwd()
REVIEWS = ROOT / "reviews"
WORK = ROOT / "work"
TUPLES = ROOT / "tuples"

SCORES = {"very_negative": -2, "negative": -1, "neutral": 0, "mixed": 0,
          "positive": 1, "very_positive": 2}
DEFAULT_POLARITIES = ["very_negative", "negative", "positive", "very_positive"]
# Intensifiers, superlatives and extreme words. A trailing * matches any ending
# ("master*" matches masterful, masterpiece). Edit the list in codebook.json.
DEFAULT_REINFORCERS = [
    "very", "really", "truly", "so", "too", "most", "least", "extremely", "incredibly",
    "utterly", "absolutely", "totally", "entirely", "completely", "deeply",
    "hugely", "immensely", "enormously", "remarkably", "exceptionally",
    "extraordinar*", "profoundly", "thoroughly", "wildly", "insanely",
    "best", "worst", "greatest", "finest", "funniest", "scariest", "smartest",
    "boldest", "weakest", "dumbest", "laziest",
    "master*", "perfect*", "flawless*", "impeccab*", "unforgettable",
    "astonishing*", "stunning*", "dazzling*", "breathtaking*", "devastating*",
    "sublime*", "transcendent*", "triumph*", "genius", "landmark",
    "terrible", "terribly", "awful*", "dreadful*", "abysmal*", "atrocious*",
    "unwatchable", "disaster*", "garbage", "worthless", "insufferab*",
    "excruciating*", "horrendous*", "unbearab*",
]
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "st", "vs", "etc", "e.g", "i.e", "jr", "sr", "no",
    "vol", "fig", "u.s", "u.k", "dir", "prof", "mt", "ft", "approx", "inc",
    "ltd", "co", "cf", "ca", "pp", "ed", "eds", "n.b",
}
BOILERPLATE = ["subscribe", "sign in", "log in", "cookie", "newsletter",
               "all rights reserved", "advertisement", "create an account",
               "already a subscriber", "javascript"]


# ---------------------------------------------------------------- utilities

def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"Missing file: {path}")
    except json.JSONDecodeError as exc:
        die(f"{path} is not valid JSON: {exc}")


def load_codebook():
    path = ROOT / "codebook.json"
    if not path.exists():
        die("No codebook.json here. Write the categories first (Phase 1), "
            "then run this again.")
    cb = load_json(path)
    cats = cb.get("categories") or []
    if not cats:
        die("codebook.json has no categories.")
    ids = [c.get("id") for c in cats]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        die("Every category in codebook.json needs a unique 'id'.")
    cb.setdefault("polarities", DEFAULT_POLARITIES)
    cb.setdefault("max_opinion_words", 6)
    cb.setdefault("reinforcers", DEFAULT_REINFORCERS)
    cb.setdefault("guard_terms", [])
    for p in cb["polarities"]:
        if p not in SCORES:
            die(f"Unknown polarity '{p}' in codebook.json. Use: {', '.join(SCORES)}")
    return cb


FOLD = {"\u2018": "'", "\u2019": "'", "\u201b": "'", "\u2032": "'",
        "\u201c": '"', "\u201d": '"', "\u201f": '"', "\u2033": '"',
        "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " ",
        "\u2026": "..."}


def fold_index(text):
    """Fold typographic variants and runs of whitespace, keeping a map from
    every folded character back to its index in the original text."""
    out, idx = [], []
    for i, ch in enumerate(text):
        rep = " " if ch.isspace() else FOLD.get(ch, ch)
        if rep == " " and out and out[-1] == " ":
            continue
        for r in rep:
            out.append(r)
            idx.append(i)
    return "".join(out), idx


def locate(span, sentence):
    """Find span in sentence. Returns (start, end, how) or None.

    how = 'exact' | 'case' | 'typography'. The caller then stores
    sentence[start:end], so a stored quote is always verbatim source text."""
    span = (span or "").strip()
    if not span:
        return None
    i = sentence.find(span)
    if i >= 0:
        return i, i + len(span), "exact"
    folded, idx = fold_index(sentence)
    target, _ = fold_index(span)
    j = folded.find(target)
    how = "typography"
    if j < 0 and len(folded.lower()) == len(folded):
        j = folded.lower().find(target.lower())
        how = "case"
    if j < 0 or not target:
        return None
    return idx[j], idx[j + len(target) - 1] + 1, how


def words(s):
    return re.findall(r"[A-Za-zÀ-ɏ0-9]+(?:['’-][A-Za-zÀ-ɏ0-9]+)*", s)


def has_reinforcer(opinion, reinforcers):
    toks = [w.lower().replace("’", "'") for w in words(opinion)]
    for t in toks:
        for r in reinforcers:
            r = r.lower()
            if r.endswith("*"):
                if t.startswith(r[:-1]):
                    return t
            elif t == r:
                return t
    return None


# ---------------------------------------------------------------- split

def split_sentences(text):
    """Return [(start, end)] spans of sentences in text (offsets into text)."""
    spans = []
    for para in re.finditer(r"[^\n]+", text):
        p0, ptxt = para.start(), para.group()
        cut = 0
        for b in re.finditer(r"[.!?…]+[\"'”’)\]]*\s+", ptxt):
            last = re.search(r"(\S+)$", ptxt[:b.start() + 1])
            token = last.group(1).lower() if last else ""
            token = token.strip("([\"'“‘").rstrip(".")
            if token in ABBREVIATIONS or re.fullmatch(r"[a-z]", token):
                continue
            nxt = ptxt[b.end():b.end() + 2]
            if nxt and not re.match(r"[\"'“‘(\[]?[A-Z0-9À-Þ]", nxt):
                continue
            spans.append((p0 + cut, p0 + b.end()))
            cut = b.end()
        spans.append((p0 + cut, p0 + len(ptxt)))
    out = []
    for s, e in spans:
        seg = text[s:e]
        lead = len(seg) - len(seg.lstrip())
        s2, e2 = s + lead, s + len(seg.rstrip())
        if e2 > s2:
            out.append((s2, e2))
    return out


def ensure_reviews_csv(ids):
    path = REVIEWS / "reviews.csv"
    cols = ["review_id", "critic", "publication", "url", "verdict", "score", "accessed"]
    rows = OrderedDict()
    if path.exists():
        with path.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("review_id"):
                    rows[r["review_id"]] = r
    added = [i for i in ids if i not in rows]
    for i in added:
        rows[i] = {"review_id": i}
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows.values():
            w.writerow({c: r.get(c, "") for c in cols})
    return added


def cmd_split(_args):
    files = sorted(p for p in REVIEWS.glob("*.txt") if p.stat().st_size > 0) if REVIEWS.exists() else []
    if not files:
        die("No review text yet. Put each review in reviews/<id>.txt (r1.txt, r2.txt, ...).")
    cb_path = ROOT / "codebook.json"
    guard = []
    if cb_path.exists():
        guard = [g.lower() for g in load_json(cb_path).get("guard_terms", []) if g]
    WORK.mkdir(exist_ok=True)
    seen_texts = {}
    problems = 0
    print(f"{'review':10} {'sentences':>9} {'words':>6}  warnings")
    for f in files:
        rid = f.stem
        raw = f.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        if text.startswith("﻿"):
            text = text[1:]
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        spans = split_sentences(text)
        sents = [{"id": n + 1, "start": s, "end": e, "text": text[s:e]}
                 for n, (s, e) in enumerate(spans)]
        warn = []
        nwords = len(words(text))
        if len(text.strip()) < 400:
            warn.append("very short: a snippet, a paywall or a cookie banner?")
        low = text.lower()
        hits = sum(low.count(b) for b in BOILERPLATE)
        if hits >= 3:
            warn.append(f"{hits} page-furniture words (subscribe, cookie, ...): check the paste")
        if guard and not any(g in low for g in guard):
            warn.append("never mentions the film's guard terms: wrong page?")
        norm = Counter(re.sub(r"\W+", " ", s["text"].lower()).strip() for s in sents
                       if len(s["text"]) > 30)
        repeated = sum(c - 1 for c in norm.values() if c > 1)
        if repeated >= 3:
            warn.append(f"{repeated} sentences appear twice: the page text may be duplicated")
        key = re.sub(r"\W+", " ", low)[:2000]
        if key in seen_texts:
            warn.append(f"same text as {seen_texts[key]}")
        seen_texts[key] = rid
        if "�" in text:
            warn.append("contains undecodable characters: save the file as UTF-8")
        problems += bool(warn)
        (WORK / f"{rid}.sentences.json").write_text(json.dumps(
            {"review_id": rid, "source": f"reviews/{f.name}", "chars": len(text),
             "sentences": sents}, ensure_ascii=False, indent=1), encoding="utf-8")
        (WORK / f"{rid}.text").write_text(text, encoding="utf-8")
        print(f"{rid:10} {len(sents):>9} {nwords:>6}  {'; '.join(warn) or '-'}")
    added = ensure_reviews_csv([f.stem for f in files])
    if added:
        print(f"\nreviews/reviews.csv now lists {', '.join(added)}: fill in critic, publication, url, verdict.")
    print(f"\nWrote work/<id>.sentences.json for {len(files)} review(s).")
    if problems:
        print("Read the warnings before annotating: a bad paste becomes bad data.")


# ---------------------------------------------------------------- check

def read_annotation(path):
    data = load_json(path)
    if isinstance(data, list):
        data = {"review_id": Path(path).stem, "tuples": data}
    rid = str(data.get("review_id") or Path(path).stem)
    return rid, data.get("annotator", ""), data.get("tuples") or []


def check_tuples(rid, tuples, sents_doc, cb):
    """Validate one review's tuples. Returns (rows, errors, fixes)."""
    text_path = WORK / f"{rid}.text"
    full = text_path.read_text(encoding="utf-8") if text_path.exists() else None
    sents = {s["id"]: s for s in sents_doc["sentences"]}
    cats = {c["id"] for c in cb["categories"]}
    pols = set(cb["polarities"])
    rows, errors, fixes = [], 0, 0
    seen = set()
    for n, t in enumerate(tuples, 1):
        notes, status = [], "ok"
        sid = t.get("sentence")
        try:
            sid = int(sid)
        except (TypeError, ValueError):
            sid = None
        sent = sents.get(sid)
        cat = str(t.get("category", "")).strip()
        pol = str(t.get("polarity", "")).strip().lower()
        opinion = str(t.get("opinion") or "").strip()
        aspect = t.get("aspect")
        aspect = str(aspect).strip() if aspect not in (None, "", "NULL", "null") else None
        conf = str(t.get("confidence", "") or "").strip().lower()
        row = {"review_id": rid, "tuple": n, "sentence_id": sid if sid else t.get("sentence"),
               "category": cat, "aspect": aspect or "", "aspect_explicit": bool(aspect),
               "opinion": opinion, "polarity": pol, "score": SCORES.get(pol, ""),
               "confidence": conf, "start": "", "end": "", "status": "", "note": "",
               "sentence": sent["text"] if sent else ""}
        if sent is None:
            notes.append(f"sentence {t.get('sentence')!r} does not exist")
            status = "error"
        if cat not in cats:
            notes.append(f"category '{cat}' is not in codebook.json")
            status = "error"
        if pol not in pols:
            notes.append(f"polarity '{pol}' is not allowed (codebook: {', '.join(cb['polarities'])})")
            status = "error"
        if not opinion:
            notes.append("no opinion span")
            status = "error"
        if sent is not None and opinion:
            hit = locate(opinion, sent["text"])
            if hit is None:
                notes.append("opinion is not copied exactly from the sentence")
                status = "error"
            else:
                s, e, how = hit
                exact = sent["text"][s:e]
                if how != "exact":
                    notes.append(f"opinion matched after {how} folding; stored as written in the review")
                    fixes += 1
                    status = "fixed"
                opinion = exact
                row["opinion"] = exact
                if full is not None:
                    row["start"], row["end"] = sent["start"] + s, sent["start"] + e
                    if full[row["start"]:row["end"]] != exact:
                        notes.append("offset mismatch against the review text")
                        status = "error"
                if aspect:
                    ah = locate(aspect, sent["text"])
                    if ah is None:
                        notes.append("aspect not found in the sentence; recorded as implicit")
                        aspect, row["aspect"], row["aspect_explicit"] = None, "", False
                        fixes += 1
                        status = "fixed" if status == "ok" else status
                    else:
                        a0, a1, _ = ah
                        if a0 < e and s < a1:
                            notes.append("aspect overlapped the opinion; aspect dropped")
                            aspect, row["aspect"], row["aspect_explicit"] = None, "", False
                            fixes += 1
                            status = "fixed" if status == "ok" else status
                        else:
                            row["aspect"] = sent["text"][a0:a1]
        nw = len(words(opinion))
        if opinion and nw > int(cb["max_opinion_words"]):
            notes.append(f"opinion is {nw} words (limit {cb['max_opinion_words']}): "
                         "keep only the words that carry the judgment, or drop the tuple")
            status = "error"
        if pol.startswith("very_") and opinion and status != "error":
            r = has_reinforcer(opinion, cb["reinforcers"])
            if not r:
                down = pol.replace("very_", "")
                if down in pols:
                    notes.append(f"{pol} needs a reinforcing word in the span; downgraded to {down}")
                    pol = down
                    row["polarity"], row["score"] = down, SCORES[down]
                    fixes += 1
                    status = "fixed" if status == "ok" else status
                else:
                    notes.append(f"{pol} needs a reinforcing word in the span")
                    status = "error"
        key = (sid, cat, row["opinion"].lower())
        if status != "error" and key in seen:
            notes.append("duplicate of an earlier tuple; dropped")
            status = "duplicate"
        seen.add(key)
        if status == "error":
            errors += 1
        row["status"], row["note"] = status, "; ".join(notes)
        rows.append(row)
    return rows, errors, fixes


CSV_COLS = ["review_id", "tuple", "sentence_id", "category", "aspect", "aspect_explicit",
            "opinion", "polarity", "score", "confidence", "start", "end", "status",
            "note", "sentence"]


def cmd_check(_args):
    cb = load_codebook()
    files = sorted(TUPLES.glob("*.json")) if TUPLES.exists() else []
    if not files:
        die("No tuples yet: annotate into tuples/<review_id>.json first.")
    all_rows, report = [], []
    tot_err = tot_fix = 0
    for f in files:
        rid, annotator, tuples = read_annotation(f)
        sp = WORK / f"{rid}.sentences.json"
        if not sp.exists():
            die(f"No work/{rid}.sentences.json. Run: python3 absa.py split")
        rows, errs, fixes = check_tuples(rid, tuples, load_json(sp), cb)
        all_rows += rows
        tot_err += errs
        tot_fix += fixes
        dup = sum(r["status"] == "duplicate" for r in rows)
        report.append(f"## {rid}  ({annotator or 'annotator not recorded'})\n")
        report.append(f"{len(rows)} tuples: {len(rows) - errs - dup} usable, {errs} errors, "
                      f"{fixes} automatic fixes, {dup} duplicates.\n")
        for r in rows:
            if r["status"] != "ok":
                report.append(f"- [{r['status']}] tuple {r['tuple']}, sentence {r['sentence_id']}, "
                              f"{r['category']}, \"{r['opinion']}\": {r['note']}")
        report.append("")
    with (ROOT / "tuples.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS)
        w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k, "") for k in CSV_COLS})
    usable = [r for r in all_rows if r["status"] in ("ok", "fixed")]
    head = [f"# Check report, {_dt.datetime.now():%Y-%m-%d %H:%M}\n",
            f"{len(files)} review(s), {len(all_rows)} tuples, {len(usable)} usable, "
            f"{tot_err} errors, {tot_fix} automatic fixes.\n",
            "This report checks form only: quotes copied exactly, labels from the codebook, "
            "the intensity rule. It does not check whether a judgment was read correctly.\n"]
    (ROOT / "check_report.md").write_text("\n".join(head + report) + "\n", encoding="utf-8")
    print("\n".join(head))
    by_pol = Counter(r["polarity"] for r in usable)
    print("usable by polarity:", ", ".join(f"{k} {by_pol[k]}" for k in cb["polarities"]))
    print("Wrote tuples.csv and check_report.md")
    if tot_err:
        print(f"\n{tot_err} tuple(s) failed. Fix them by rereading the sentence, never by "
              "loosening the quote until it passes. See check_report.md.")
        sys.exit(1)


# ---------------------------------------------------------------- agree

def cmd_agree(args):
    if len(args) != 2:
        die("Usage: python3 absa.py agree <first.json> <second.json>")
    cb = load_codebook()
    sets = []
    for p in args:
        rid, who, tuples = read_annotation(p)
        sp = WORK / f"{rid}.sentences.json"
        if not sp.exists():
            die(f"No work/{rid}.sentences.json. Run: python3 absa.py split")
        rows, _, _ = check_tuples(rid, tuples, load_json(sp), cb)
        rows = [r for r in rows if r["status"] in ("ok", "fixed")]
        sets.append((rid, who or Path(p).parent.name, rows))
    (ra, wa, a), (rb, wb, b) = sets
    if ra != rb:
        die(f"These annotate different reviews ({ra} vs {rb}).")
    sa, sb = {r["sentence_id"] for r in a}, {r["sentence_id"] for r in b}
    jac = len(sa & sb) / len(sa | sb) if (sa | sb) else 1.0
    ka = defaultdict(list)
    kb = defaultdict(list)
    for r in a:
        ka[(r["sentence_id"], r["category"])].append(r)
    for r in b:
        kb[(r["sentence_id"], r["category"])].append(r)
    both = sorted(set(ka) & set(kb), key=lambda k: (k[0], k[1]))
    union = set(ka) | set(kb)
    same_pol = same_sign = 0
    lines = []
    for k in both:
        pa = Counter(r["polarity"] for r in ka[k]).most_common(1)[0][0]
        pb = Counter(r["polarity"] for r in kb[k]).most_common(1)[0][0]
        same_pol += pa == pb
        sign = lambda p: (SCORES[p] > 0) - (SCORES[p] < 0)
        same_sign += int(sign(pa) == sign(pb))
        if pa != pb:
            lines.append(f"| {k[0]} | {k[1]} | {pa} | {pb} |")
    out = [f"# Agreement on {ra}: {wa} vs {wb}\n",
           f"- Sentences either annotator used: {len(sa | sb)}; both used: {len(sa & sb)} "
           f"(Jaccard {jac:.2f})",
           f"- (sentence, category) pairs: {len(ka)} vs {len(kb)}; shared: {len(both)} of {len(union)}"
           f" ({(len(both) / len(union) * 100 if union else 100):.0f}%)",
           f"- Same polarity on shared pairs: {same_pol}/{len(both)}; same sign: {same_sign}/{len(both)}",
           "", "With this few tuples, read the rows below rather than the percentages.", ""]
    if lines:
        out += ["## Shared pairs, different polarity", "", "| sentence | category | " + wa + " | " + wb + " |",
                "|---|---|---|---|"] + lines + [""]
    only_a = sorted(set(ka) - set(kb), key=lambda k: (k[0], k[1]))
    only_b = sorted(set(kb) - set(ka), key=lambda k: (k[0], k[1]))
    for who, keys, src in ((wa, only_a, ka), (wb, only_b, kb)):
        if keys:
            out += [f"## Only {who}", ""]
            for k in keys:
                r = src[k][0]
                out.append(f"- sentence {k[0]}, {k[1]}, {r['polarity']}: \"{r['opinion']}\"")
            out.append("")
    text = "\n".join(out)
    dest = ROOT / f"agree_{ra}_{re.sub(r'[^A-Za-z0-9]+', '-', wa)}_vs_{re.sub(r'[^A-Za-z0-9]+', '-', wb)}.md"
    dest.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"Wrote {dest.name}")


# ---------------------------------------------------------------- chart

NEG2, NEG1, POS1, POS2, NEU = "#B2182B", "#EF8A62", "#67A9CF", "#2166AC", "#B9B4A8"
POL_COLOR = {"very_negative": NEG2, "negative": NEG1, "neutral": NEU, "mixed": NEU,
             "positive": POS1, "very_positive": POS2}
POL_LABEL = {"very_negative": "very negative", "negative": "negative", "neutral": "neutral",
             "mixed": "mixed", "positive": "positive", "very_positive": "very positive"}


def read_section(md_text, heading):
    m = re.search(r"^##\s+" + re.escape(heading) + r"\s*$(.*?)(?=^##\s|\Z)", md_text, re.M | re.S)
    if not m:
        return ""
    return re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip()


def esc(s):
    return html.escape(str(s), quote=True)


def bar_svg(counts, scale, width=360, height=22):
    """Diverging bar: negatives left of centre, positives right."""
    mid = width / 2
    unit = (mid - 2) / scale if scale else 0
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="{esc(", ".join(f"{POL_LABEL[k]} {v}" for k, v in counts.items() if v))}">']
    x = mid
    for k in ("negative", "very_negative"):
        w = counts.get(k, 0) * unit
        if w:
            x -= w
            parts.append(f'<rect x="{x:.1f}" y="3" width="{w:.1f}" height="{height - 6}" fill="{POL_COLOR[k]}"/>')
    x = mid
    for k in ("positive", "very_positive"):
        w = counts.get(k, 0) * unit
        if w:
            parts.append(f'<rect x="{x:.1f}" y="3" width="{w:.1f}" height="{height - 6}" fill="{POL_COLOR[k]}"/>')
            x += w
    n0 = counts.get("neutral", 0) + counts.get("mixed", 0)
    if n0:
        w = n0 * unit
        parts.append(f'<rect x="{mid - w / 2:.1f}" y="{height / 2 - 3:.1f}" width="{w:.1f}" height="6" fill="{NEU}"/>')
    parts.append(f'<line x1="{mid}" y1="0" x2="{mid}" y2="{height}" stroke="currentColor" stroke-opacity=".45"/>')
    parts.append("</svg>")
    return "".join(parts)


def mark_sentence(sentence, opinion, aspect):
    s = sentence
    spans = []
    i = s.find(opinion) if opinion else -1
    if i >= 0:
        spans.append((i, i + len(opinion), "mark"))
    if aspect:
        j = s.find(aspect)
        if j >= 0 and not (spans and j < spans[0][1] and spans[0][0] < j + len(aspect)):
            spans.append((j, j + len(aspect), "u"))
    spans.sort()
    out, pos = [], 0
    for a, b, tag in spans:
        out.append(esc(s[pos:a]))
        out.append(f"<{tag}>{esc(s[a:b])}</{tag}>")
        pos = b
    out.append(esc(s[pos:]))
    return "".join(out)


def cmd_chart(_args):
    cb = load_codebook()
    path = ROOT / "tuples.csv"
    if not path.exists():
        die("No tuples.csv yet. Run: python3 absa.py check")
    with path.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["status"] in ("ok", "fixed")]
    if not rows:
        die("tuples.csv has no usable tuples.")
    meta = {}
    mp = REVIEWS / "reviews.csv"
    if mp.exists():
        with mp.open(encoding="utf-8", newline="") as fh:
            meta = {r["review_id"]: r for r in csv.DictReader(fh)}
    exp = (ROOT / "experiment.md").read_text(encoding="utf-8") if (ROOT / "experiment.md").exists() else ""
    conceals = read_section(exp, "What this chart conceals")
    disagree = read_section(exp, "Where we disagree with Claude")
    labels = {c["id"]: c.get("label") or c["id"] for c in cb["categories"]}
    defs = {c["id"]: c.get("definition", "") for c in cb["categories"]}

    by_cat = defaultdict(Counter)
    for r in rows:
        by_cat[r["category"]][r["polarity"]] += 1
    order = sorted(by_cat, key=lambda c: (-sum(by_cat[c].values()), c))
    scale = max(max(c.get("negative", 0) + c.get("very_negative", 0),
                    c.get("positive", 0) + c.get("very_positive", 0)) for c in by_cat.values()) or 1
    unused = [c["id"] for c in cb["categories"] if c["id"] not in by_cat]

    cat_rows = []
    for c in order:
        cnt = by_cat[c]
        n = sum(cnt.values())
        neg = cnt.get("negative", 0) + cnt.get("very_negative", 0)
        cat_rows.append(
            f'<tr><th scope="row" title="{esc(defs.get(c, ""))}">{esc(labels.get(c, c))}</th>'
            f'<td class="bar">{bar_svg(cnt, scale)}</td><td class="num">{n}</td>'
            f'<td class="num">{neg / n * 100:.0f}%</td></tr>')

    by_rev = defaultdict(list)
    for r in rows:
        by_rev[r["review_id"]].append(r)
    rscale = max(max(sum(1 for t in v if SCORES.get(t["polarity"], 0) < 0),
                     sum(1 for t in v if SCORES.get(t["polarity"], 0) > 0)) for v in by_rev.values()) or 1
    rev_rows = []
    for rid in sorted(by_rev, key=lambda k: (len(k), k)):
        v = by_rev[rid]
        cnt = Counter(t["polarity"] for t in v)
        net = sum(int(t["score"]) for t in v if str(t["score"]).lstrip("-").isdigit()) / len(v)
        m = meta.get(rid, {})
        who = " · ".join(x for x in (m.get("critic", ""), m.get("publication", "")) if x) or rid
        verdict = (m.get("verdict") or "").strip()
        score = (m.get("score") or "").strip()
        top = ", ".join(labels.get(c, c) for c, _ in Counter(t["category"] for t in v).most_common(3))
        link = f'<a href="{esc(m["url"])}">{esc(who)}</a>' if m.get("url", "").startswith("http") else esc(who)
        rev_rows.append(
            f'<tr><th scope="row"><span class="rid">{esc(rid)}</span> {link}</th>'
            f'<td>{esc(verdict)}{(" · " + esc(score)) if score else ""}</td>'
            f'<td class="bar r">{bar_svg(cnt, rscale, 240)}</td><td class="num">{len(v)}</td>'
            f'<td class="num">{net:+.2f}</td><td class="small">{esc(top)}</td></tr>')

    ev = []
    for rid in sorted(by_rev, key=lambda k: (len(k), k)):
        m = meta.get(rid, {})
        who = " · ".join(x for x in (m.get("critic", ""), m.get("publication", "")) if x)
        ev.append(f'<h3>{esc(rid)}{(" · " + esc(who)) if who else ""}</h3><ol class="ev">')
        for t in sorted(by_rev[rid], key=lambda t: (int(t["sentence_id"]), int(t["tuple"]))):
            ev.append(
                f'<li><span class="sid">s{esc(t["sentence_id"])}</span>'
                f'<span class="chip">{esc(labels.get(t["category"], t["category"]))}</span>'
                f'<span class="pol p-{esc(t["polarity"])}">{esc(POL_LABEL.get(t["polarity"], t["polarity"]))}</span>'
                f'<span class="sent">{mark_sentence(t["sentence"], t["opinion"], t["aspect"])}</span>'
                + (f'<span class="note">{esc(t["note"])}</span>' if t["note"] else "") + "</li>")
        ev.append("</ol>")

    legend = "".join(f'<span><i style="background:{POL_COLOR[p]}"></i>{POL_LABEL[p]}</span>'
                     for p in ("very_negative", "negative", "positive", "very_positive")
                     if p in cb["polarities"])
    if "neutral" in cb["polarities"]:
        legend += f'<span><i style="background:{NEU}"></i>neutral</span>'
    film = cb.get("film") or "Untitled film"
    n_rev = len(by_rev)
    n_neg = sum(1 for r in rows if SCORES.get(r["polarity"], 0) < 0)
    codebook_items = "".join(
        f'<li><b>{esc(c.get("label") or c["id"])}</b> <code>{esc(c["id"])}</code>: {esc(c.get("definition", ""))}</li>'
        for c in cb["categories"])
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(film)}: what the critics judge</title>
<style>
:root{{--bg:#f7f3ea;--ink:#1d1c1a;--soft:#5b5850;--rule:#d9d2c3;--card:#fffdf8;--link:#1f5d9e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#191917;--ink:#efeae0;--soft:#b3ad9f;--rule:#3a3833;--card:#22211e;--link:#9cc7ef}}}}
a{{color:var(--link)}}
.scroll{{overflow-x:auto}}
th.num{{text-align:right}}
td.bar svg{{width:100%;height:auto;display:block}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:40px 20px 80px}}
h1{{font:600 40px/1.1 Georgia,"Times New Roman",serif;margin:0 0 6px}}
h2{{font:600 24px/1.2 Georgia,serif;margin:44px 0 10px;padding-top:14px;border-top:1px solid var(--rule)}}
h3{{font-size:16px;margin:22px 0 6px}}
.sub{{color:var(--soft);margin:0 0 18px}}
.kpis{{display:flex;gap:28px;flex-wrap:wrap;margin:18px 0 6px}}
.kpis div{{min-width:120px}} .kpis b{{display:block;font:600 34px/1 Georgia,serif}} .kpis span{{color:var(--soft);font-size:14px}}
.legend{{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;color:var(--soft);margin:6px 0 10px}}
.legend i{{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:6px;vertical-align:-1px}}
table{{border-collapse:collapse;width:100%}}
th,td{{padding:6px 8px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:middle}}
thead th{{font-size:13px;color:var(--soft);font-weight:600}}
th[scope=row]{{font-weight:600}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td.bar{{width:360px;min-width:120px;color:var(--ink)}} td.bar.r{{width:240px}} td.small{{font-size:14px;color:var(--soft)}}
.rid{{font:12px ui-monospace,Menlo,monospace;color:var(--soft);margin-right:4px}}
ol.ev{{list-style:none;padding:0;margin:0}}
ol.ev li{{display:grid;grid-template-columns:44px 170px 110px 1fr;gap:10px;padding:8px 0;border-bottom:1px solid var(--rule);align-items:baseline}}
.sid{{font:12px ui-monospace,Menlo,monospace;color:var(--soft)}}
.chip{{font-size:13px;font-weight:600}}
.pol{{font-size:13px;font-weight:700;padding:1px 8px;border-radius:999px;justify-self:start}}
.p-very_negative{{background:#B2182B;color:#fff}} .p-negative{{background:#EF8A62;color:#1d1c1a}}
.p-positive{{background:#67A9CF;color:#1d1c1a}} .p-very_positive{{background:#2166AC;color:#fff}}
.p-neutral,.p-mixed{{background:#B9B4A8;color:#1d1c1a}}
.sent mark{{background:#f3d27a;color:#1d1c1a;padding:0 2px;border-radius:2px}}
.sent u{{text-decoration-thickness:2px;text-underline-offset:3px}}
.note{{grid-column:2/-1;font-size:13px;color:var(--soft)}}
.box{{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:14px 18px;white-space:pre-wrap}}
.empty{{color:var(--soft);font-style:italic}}
footer{{margin-top:48px;font-size:13px;color:var(--soft)}}
@media (max-width:720px){{ol.ev li{{grid-template-columns:40px 1fr}} .sent{{grid-column:1/-1}} td.small,th.small{{display:none}} td.bar,td.bar.r{{width:140px}} th,td{{padding:6px 4px}}}}
</style></head><body><main>
<h1>{esc(film)}</h1>
<p class="sub">What {n_rev} critic review{"s" if n_rev != 1 else ""} judge, one opinion at a time. Aspect-based sentiment analysis with Claude, checked by absa.py.</p>
<div class="kpis"><div><b>{n_rev}</b><span>reviews</span></div><div><b>{len(rows)}</b><span>opinions (tuples)</span></div>
<div><b>{n_neg}</b><span>negative opinions</span></div><div><b>{len(by_cat)}</b><span>of {len(cb["categories"])} categories used</span></div></div>

<h2>What the critics judge</h2>
<p class="sub">Each bar is one category. Negative opinions extend left of the line, positive ones right. Sorted by how often critics judge it.</p>
<div class="legend">{legend}</div>
<div class="scroll"><table><thead><tr><th>Category</th><th>negative ◂ | ▸ positive</th><th class="num">n</th><th class="num">negative</th></tr></thead>
<tbody>{"".join(cat_rows)}</tbody></table></div>
{('<p class="sub">Never used: ' + esc(", ".join(labels.get(u, u) for u in unused)) + '. A category nobody uses is a finding about the reviews or about the codebook.</p>') if unused else ''}

<h2>Review by review</h2>
<p class="sub">Net = mean score per opinion (very negative −2 … very positive +2). A verdict is not the average of its parts: compare the two columns.</p>
<div class="scroll"><table><thead><tr><th>Review</th><th>Verdict</th><th>negative ◂ | ▸ positive</th><th class="num">n</th><th class="num">net</th><th class="small">Most judged</th></tr></thead>
<tbody>{"".join(rev_rows)}</tbody></table></div>

<h2>Where we disagree with Claude</h2>
<div class="box">{esc(disagree) if disagree else '<span class="empty">Not filled in yet: experiment.md, section “Where we disagree with Claude”.</span>'}</div>

<h2>What this chart conceals</h2>
<div class="box">{esc(conceals) if conceals else '<span class="empty">Not filled in yet: experiment.md, section “What this chart conceals”.</span>'}</div>

<h2>The evidence</h2>
<p class="sub">Every opinion with its sentence. <mark style="background:#f3d27a;color:#1d1c1a">Highlighted</mark>: the words that carry the judgment. <u>Underlined</u>: the aspect, when the critic names it.</p>
{"".join(ev)}

<h2>Codebook</h2>
<ul>{codebook_items}</ul>
<footer>Generated {_dt.datetime.now():%Y-%m-%d %H:%M} by absa.py from tuples.csv. Quotations are short spans kept for analysis and teaching; the full review texts stay on this machine.</footer>
</main></body></html>"""
    (ROOT / "results.html").write_text(page, encoding="utf-8")
    summary = {"film": film, "generated": _dt.datetime.now().isoformat(timespec="seconds"),
               "reviews": n_rev, "tuples": len(rows),
               "categories": {c: dict(by_cat[c]) for c in order},
               "by_review": {rid: dict(Counter(t["polarity"] for t in v)) for rid, v in by_rev.items()}}
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"Wrote results.html ({len(rows)} opinions, {n_rev} reviews) and summary.json")
    print("Open it:  open results.html   (WSL: explorer.exe \"$(wslpath -w results.html)\")")


COMMANDS = {"split": cmd_split, "check": cmd_check, "agree": cmd_agree, "chart": cmd_chart}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0 if len(sys.argv) < 2 else 2)
    COMMANDS[sys.argv[1]](sys.argv[2:])
