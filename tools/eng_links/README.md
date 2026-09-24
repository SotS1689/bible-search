# English link-stemming table (first pass)

`links.tsv` maps every word in the BLB to one or more link heads
(`word<TAB>head1,head2`). A link-stemmed search for a word matches every word
that shares at least one head with it, the same model as BibleWorks' `elm.txt`.

## Sources (all redistributable)

- **AGID rev. 4**, Copyright 2000-2003 Kevin Atkinson. Inflected forms. Its
  license requires the copyright notice to accompany copies.
  https://sourceforge.net/projects/wordlist/files/AGID/Rev%204/
- **Open English WordNet 2025**, CC-BY 4.0, derived from Princeton WordNet.
  Derivation and pertainym links. https://en-word.net/
- Hand-written pronoun and particle table, affix rules and compound splitting
  (in `build_links.py`), plus three hand-maintained lists:
  - `families.txt`: irregular families sharing a root (die dead death, save salvation)
  - `prefixed.txt`: words where stripping fore-/be-/dis-/en-/... is correct
    (general prefix rules are too error-prone: return > turn, behold > hold)
  - `never.txt`: pairs no rule may link (knowledge / ledge, mother / moth)

`elm.txt` from BibleWorks is used **only** as a benchmark by `compare.py`. None
of its data is copied into `links.tsv`.

Compound words (housetop, herdsman, grandson, thereof) are deliberately *not*
linked to their parts. Pass `all splitcompounds` to `build_links.py` to turn
that back on.

The app reads copies of `links.tsv` at `src/eng_links.tsv` (desktop) and
`docs/data/eng_links.tsv` (web). Copy it to both after rebuilding.

## Rebuilding

Put these in one folder: `c.db` (concatenate `docs/data/corpus.db.part*`),
`agid-4/` (unpacked AGID) and `oewn.xml` (unzipped
`english-wordnet-2025.xml.gz`). Then run:

    python build_links.py <folder>      # writes links.tsv + rules.json
    python compare.py <folder> 400      # benchmark vs BibleWorks elm.txt
    python audit.py                     # per-affix-rule precision vs elm.txt
