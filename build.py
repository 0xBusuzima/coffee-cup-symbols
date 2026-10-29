#!/usr/bin/env python3
"""Regenerate symbols.csv from symbols.json and validate the dataset.

Usage:
    python build.py                 # validate, then write symbols.csv
    python build.py --check         # validate only, write nothing
    python build.py --source DIR    # symbol pages live somewhere else

The source pages default to ../../content/symbols (Turkish) and
../../content/symbols/en (English), relative to this file. Outside the
Falyora repository there are no source pages; then only the checks that need
the dataset alone run (count, ids, keys, word limits, banned words, URLs).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent.parent / "content" / "symbols"

EXPECTED_COUNT = 40
ZONES = ["rim", "side", "bottom", "handle", "saucer"]
CATEGORIES = {"animals", "shapes", "objects", "human", "nature"}
CATEGORY_MAP = {
    "hayvanlar": "animals",
    "sekiller": "shapes",
    "nesneler": "objects",
    "insan": "human",
    "doga": "nature",
}
PHRASE_FIELDS = ["traditional_en", "falyora_reading_en", "traditional_tr", "falyora_reading_tr"]
PHRASE_MAX_WORDS = 12
ZONE_MIN_WORDS, ZONE_MAX_WORDS = 3, 8
NGRAM = 8  # no run of this many words may appear verbatim in a source page
URL_TR = "https://falyora.app/semboller/"
URL_EN = "https://falyora.app/en/symbols/"

# Falyora content rules: no fear words, no money or marriage promises.
BANNED_WORDS = {
    # English
    "enemy", "enemies", "betrayal", "betray", "betrayed", "curse", "cursed",
    "illness", "ill", "sick", "sickness", "disease", "death", "die", "dies",
    "dying", "money", "wealth", "rich", "marriage", "marry", "wedding",
    "engagement", "engaged",
    # Turkish
    "düşman", "düşmana", "ihanet", "lanet", "büyü", "hastalık", "hasta",
    "ölüm", "para", "zenginlik", "evlilik", "evlenmek", "düğün", "nişan",
}

CSV_COLUMNS = [
    "id", "name_tr", "name_en", "category",
    "traditional_en", "falyora_reading_en", "traditional_tr", "falyora_reading_tr",
    *[f"zone_{z}" for z in ZONES],
    "url_tr", "url_en",
]


def lower_tr(text: str) -> str:
    """Lower-case with Turkish dotted/dotless I handled the same way everywhere."""
    return text.replace("İ", "i").replace("I", "ı").lower()


def words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+(?:['’][^\W_]+)*", lower_tr(text))


def frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def load_pages(source: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    tr, en = {}, {}
    for p in sorted(source.glob("*.md")):
        t = p.read_text(encoding="utf-8")
        tr[p.stem] = {"meta": frontmatter(t), "text": t}
    for p in sorted((source / "en").glob("*.md")):
        t = p.read_text(encoding="utf-8")
        en[p.stem] = {"meta": frontmatter(t), "text": t}
    return tr, en


def source_ngrams(pages: list[str], n: int) -> set[tuple[str, ...]]:
    grams: set[tuple[str, ...]] = set()
    for text in pages:
        body = re.sub(r"^---.*?---", " ", text, count=1, flags=re.S)
        # Treat headings and paragraph breaks as boundaries, not as joined text.
        for chunk in re.split(r"\n\s*\n|^##.*$", body, flags=re.M):
            w = words(chunk)
            for i in range(len(w) - n + 1):
                grams.add(tuple(w[i:i + n]))
    return grams


def validate(records: list[dict], source: Path) -> list[str]:
    errors: list[str] = []
    have_pages = source.is_dir()
    tr_pages, en_pages = load_pages(source) if have_pages else ({}, {})

    if not isinstance(records, list):
        return ["symbols.json must be a JSON array"]
    if len(records) != EXPECTED_COUNT:
        errors.append(f"expected {EXPECTED_COUNT} records, found {len(records)}")

    ids = [r.get("id") for r in records]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        errors.append(f"duplicate ids: {dupes}")
    missing_records = sorted(set(tr_pages) - set(ids)) if have_pages else []
    if missing_records:
        errors.append(f"Turkish pages with no record: {missing_records}")

    grams = source_ngrams([p["text"] for p in tr_pages.values()] +
                          [p["text"] for p in en_pages.values()], NGRAM)

    for r in records:
        rid = r.get("id", "?")
        where = f"[{rid}]"

        expected_keys = {"id", "name_tr", "name_en", "category", *PHRASE_FIELDS,
                         "zones", "url_tr", "url_en"}
        if set(r) != expected_keys:
            errors.append(f"{where} keys differ: extra {sorted(set(r) - expected_keys)}, "
                          f"missing {sorted(expected_keys - set(r))}")
            continue

        page = tr_pages.get(rid)
        if not have_pages:
            pass
        elif page is None:
            errors.append(f"{where} no Turkish page {rid}.md")
        else:
            if page["meta"].get("title") != r["name_tr"]:
                errors.append(f"{where} name_tr {r['name_tr']!r} != page title "
                              f"{page['meta'].get('title')!r}")
            if CATEGORY_MAP.get(page["meta"].get("category", "")) != r["category"]:
                errors.append(f"{where} category {r['category']!r} does not match page "
                              f"category {page['meta'].get('category')!r}")
        if r["category"] not in CATEGORIES:
            errors.append(f"{where} unknown category {r['category']!r}")

        if r["url_tr"] != URL_TR + rid:
            errors.append(f"{where} url_tr should be {URL_TR + rid}")
        if not r["url_en"].startswith(URL_EN):
            errors.append(f"{where} url_en must start with {URL_EN}")
        else:
            en_slug = r["url_en"][len(URL_EN):]
            en_page = en_pages.get(en_slug)
            if not have_pages:
                pass
            elif en_page is None:
                errors.append(f"{where} url_en: no English page en/{en_slug}.md")
            else:
                if en_page["meta"].get("pair") != rid:
                    errors.append(f"{where} en/{en_slug}.md has pair "
                                  f"{en_page['meta'].get('pair')!r}")
                if en_page["meta"].get("title") != r["name_en"]:
                    errors.append(f"{where} name_en {r['name_en']!r} != English title "
                                  f"{en_page['meta'].get('title')!r}")

        texts: list[tuple[str, str]] = []
        for f in PHRASE_FIELDS:
            v = r[f]
            if not isinstance(v, str) or not v.strip():
                errors.append(f"{where} {f} is empty")
                continue
            n = len(v.split())
            if n > PHRASE_MAX_WORDS:
                errors.append(f"{where} {f} has {n} words (max {PHRASE_MAX_WORDS})")
            texts.append((f, v))

        zones = r["zones"]
        if not isinstance(zones, dict) or list(zones) != ZONES:
            errors.append(f"{where} zones must have keys {ZONES} in order")
        else:
            for z in ZONES:
                v = zones[z]
                if v is None:
                    continue
                n = len(v.split())
                if not (ZONE_MIN_WORDS <= n <= ZONE_MAX_WORDS):
                    errors.append(f"{where} zones.{z} has {n} words "
                                  f"({ZONE_MIN_WORDS}-{ZONE_MAX_WORDS})")
                texts.append((f"zones.{z}", v))

        for f, v in texts:
            w = words(v)
            bad = sorted(set(w) & BANNED_WORDS)
            if bad:
                errors.append(f"{where} {f} uses banned word(s) {bad}")
            for i in range(len(w) - NGRAM + 1):
                if tuple(w[i:i + NGRAM]) in grams:
                    errors.append(f"{where} {f} copies {NGRAM}+ words from a source page: "
                                  f"{' '.join(w[i:i + NGRAM])!r}")
                    break

    return errors


def write_csv(records: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in records:
            row = {k: r[k] for k in CSV_COLUMNS if k in r}
            for z in ZONES:
                row[f"zone_{z}"] = r["zones"][z] if r["zones"][z] is not None else ""
            w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--check", action="store_true", help="validate only")
    args = ap.parse_args()

    records = json.loads((HERE / "symbols.json").read_text(encoding="utf-8"))
    errors = validate(records, args.source)
    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for e in errors:
            print("  - " + e)
        return 1

    print(f"OK: {len(records)} records, {len({r['id'] for r in records})} unique ids")
    print(f"OK: phrases <= {PHRASE_MAX_WORDS} words, zone gists {ZONE_MIN_WORDS}-{ZONE_MAX_WORDS} words; no banned words")
    if args.source.is_dir():
        print("OK: every id has content/symbols/<id>.md; every url_en has a paired en/<slug>.md")
        print(f"OK: no run of {NGRAM}+ words copied from the {args.source.name} pages")
    else:
        print(f"note: no source pages at {args.source}; page checks skipped")
    if not args.check:
        write_csv(records, HERE / "symbols.csv")
        print(f"wrote symbols.csv ({len(records)} rows, {len(CSV_COLUMNS)} columns)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
