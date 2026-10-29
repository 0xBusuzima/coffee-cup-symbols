# Turkish Coffee Cup Reading Symbols (Falyora)

A small, structured, bilingual (Turkish and English) dataset of 40 symbols
from Turkish coffee cup reading (*kahve falı*), a form of tasseography.

Each record is a set of short gists summarising one page of Falyora's
symbol dictionary (written with AI assistance and checked twice before
publishing; see https://falyora.app/en/about#editorial): what folk tradition says about the symbol,
how Falyora reads it instead, and what it says in each of the five parts of
the cup. The gists are compressed summaries written for this dataset, not
excerpts. The full text of every page is on the site:

- Turkish: https://falyora.app/semboller
- English: https://falyora.app/en/symbols

Dataset page with downloads: https://falyora.app/en/open-data

Version 0.1.0, released 2026-10-29.

## Files

| File | Contents |
|------|----------|
| `symbols.json` | Array of 40 objects, UTF-8. The source of truth. |
| `symbols.csv` | The same 40 records, one row each, UTF-8, zones flattened into five `zone_*` columns. Generated from the JSON. |
| `build.py` | Regenerates `symbols.csv` from `symbols.json` and validates the data (see below). |
| `CITATION.cff` | Citation metadata. |

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier; the Turkish URL slug, ASCII (e.g. `yilan`). |
| `name_tr` | string | Symbol name in Turkish (e.g. `Yılan`). |
| `name_en` | string | Symbol name in English (e.g. `Snake`). |
| `category` | string | One of `animals`, `shapes`, `objects`, `human`, `nature`. |
| `traditional_en` | string | What folk tradition says, as one phrase of at most 12 words. |
| `falyora_reading_en` | string | How Falyora reads the symbol, as one phrase of at most 12 words. |
| `traditional_tr` | string | The traditional gist in Turkish (at most 12 words). |
| `falyora_reading_tr` | string | Falyora's gist in Turkish (at most 12 words). |
| `zones` | object | Keys `rim`, `side`, `bottom`, `handle`, `saucer`; each value is a 3–8 word English gist of the symbol in that part of the cup, or `null` if the page has no section for it. In 0.1.0 every symbol covers all five zones. |
| `url_tr` | string | Full Turkish page: `https://falyora.app/semboller/<id>`. |
| `url_en` | string | Full English page: `https://falyora.app/en/symbols/<english-slug>`. |

In the CSV, `zones` becomes the columns `zone_rim`, `zone_side`,
`zone_bottom`, `zone_handle` and `zone_saucer`; a `null` zone is an empty cell.

### Categories

| `category` | Turkish | Symbols |
|------------|---------|---------|
| `animals` | hayvanlar | 12 |
| `objects` | nesneler | 11 |
| `nature` | doğa | 8 |
| `shapes` | şekiller | 5 |
| `human` | insan | 4 |

## The five cup zones

In Turkish coffee reading the same shape means different things depending on
where the grounds leave it. Falyora reads five zones:

| Key | Turkish | Where | What it usually speaks to |
|-----|---------|-------|---------------------------|
| `rim` | ağız | The upper edge of the cup | The present and the near term |
| `side` | yan duvar | The inner side wall | Something under way, still unfolding |
| `bottom` | dip | The bottom of the cup | The past, roots, long-held things |
| `handle` | kulp | The area around the handle | The person whose cup it is |
| `saucer` | tabak | The saucer | What comes from outside, from people around them |

## Example

```json
{
  "id": "yilan",
  "name_tr": "Yılan",
  "name_en": "Snake",
  "category": "animals",
  "traditional_en": "a rival posing as a friend",
  "falyora_reading_en": "something moving by winding rather than straight",
  "traditional_tr": "dost kılığındaki bir rakip",
  "falyora_reading_tr": "düz değil, kıvrılarak ilerleyen bir konu",
  "zones": {
    "rim": "a roundabout matter in the near term",
    "side": "an ongoing process not going straight",
    "bottom": "a matter carried for a long time",
    "handle": "your own hesitation or indirect path",
    "saucer": "a general situation from outside"
  },
  "url_tr": "https://falyora.app/semboller/yilan",
  "url_en": "https://falyora.app/en/symbols/snake"
}
```

## How the gists were written

Every phrase was written fresh as a compressed summary of the matching
dictionary page; none is a quoted sentence. The Falyora reading follows the
dictionary's own rules: it avoids fear-based readings, makes no predictions,
and promises no money, marriage or other outcomes. Where tradition attaches a
heavy meaning to a symbol (the snake, the eye, the cat), the `traditional_*`
fields record the folk reading in neutral words so it can be studied, and the
`falyora_reading_*` fields give Falyora's alternative.

## Validation

```bash
python build.py          # validate, then rewrite symbols.csv
python build.py --check  # validate only
```

`build.py` checks that there are exactly 40 records with unique ids; that
every id has a Turkish page and every `url_en` an English page paired with
it; that names and categories match the pages; the word limits above; a short
list of banned words; and that no run of 8 or more consecutive words in any
field appears verbatim in the source pages. It expects the dictionary sources
at `../../content/symbols/` (override with `--source`). Outside the Falyora
repository those pages are not present; the validator then skips the checks
that need them and runs the rest.

## Readings in the Falyora app

This dataset is a reference to the symbol dictionary only. Readings in the
Falyora app are written by AI from the user's cup photos and are for
entertainment.

## How to cite

> Falyora (2026). *Turkish Coffee Cup Reading Symbols (Falyora)*, version 0.1.0
> [Data set]. https://falyora.app/en/symbols

Machine-readable metadata is in `CITATION.cff`. If you use a single symbol,
please link its `url_en` or `url_tr` page.

## License

- **Data** (`symbols.json`, `symbols.csv`): [Creative Commons Attribution 4.0
  International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
  You may share and adapt it, including commercially, if you credit
  "Falyora (falyora.app)" and link the dataset or the symbol pages.
- **Code** (`build.py`): MIT, see `LICENSE`.
- The full symbol pages on falyora.app are not part of this dataset and are
  not licensed under CC BY; only the gists here are.
