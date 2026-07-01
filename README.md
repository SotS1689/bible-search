# BibleSearch — BibleWorks-style Greek & Hebrew Search

A self-contained Bible search engine modelled on BibleWorks's Command Line grammar.

## Contents
- `app.py`            — Flask web server + REST API
- `src/`              — Python engine modules:
  - `query.py`        — Command-line grammar parser (AST)
  - `search.py`       — Query evaluator against SQLite corpus
  - `corpus.py`       — Corpus builder (re-run to regenerate DB)
  - `greek_map.py`    — MorphGNT → BibleWorks code translator
  - `hebrew_map.py`   — OSHB → BibleWorks code translator
  - `greek_translit.py` — BW keyboard transliteration + accent normalization
- `static/index.html` — Full web UI (browse + search windows)
- `data/corpus.db`    — SQLite database: 444,339 words (Hebrew OT + Greek NT)

## Running

```bash
pip install flask
python3 app.py          # starts on http://localhost:7070
```

## Search Syntax (BibleWorks-compatible)

| Example | Meaning |
|---|---|
| `.word1 word2` | AND: both words in same verse |
| `'word1 word2` | Phrase: consecutive (lemma order) |
| `/word1 word2` | OR: either word |
| `.word1 !word2` | AND-NOT |
| `.word1 word2;3` | Both within 3 verses of each other |
| `.word@code` | Morph filter, e.g. `.cristoj@n*` |
| `.*@viia3s` | Any impf. indic. active 3sg verb |
| `(word1).(word2)` | Compound AND |
| `(word1).!(word2)` | Compound AND-NOT |

**Greek:** Use BibleWorks keyboard (j=ς, c=χ, q=θ, h=η, w=ω, etc.) or Unicode.
**Hebrew:** Use Strong's numbers for lemma (e.g. `1254` = בָּרָא).

## Morph Code Format

Greek: `<pos><mood><tense><voice><person><number>` for verbs, `<pos><case><gender><number>` for nominals.
Hebrew: `<pos><stem><tense><person><gender><number>Rq` for verbs, `<pos><type><gender><number><state>Rq` for nouns.

## Data Sources
- Greek NT: MorphGNT / SBLGNT (CC0)
- Hebrew OT: OpenScriptures Hebrew Bible / WLC (CC-BY 4.0)
