"""
Import the STEPBible TBESG (Greek) and TBESH (Hebrew) brief lexicons into
corpus.db as a `lexicon` table, so the app can show a short gloss/definition
on word hover.

Source: STEPBible-Data (https://github.com/STEPBible/STEPBible-Data),
CC BY 4.0. Both files are plain tab-separated text with NO header row.
Each data line has 8 tab-separated fields (empirically confirmed against
the actual files -- ~11,000+ rows each in this format, a small number of
stray non-data lines are skipped):

    0  Base extended-Strong's number, e.g. 'G0001' / 'H0001'
    1  Variant/cross-reference label (often 'G0001G =' or similar -- not
       used here)
    2  Full extended Strong's id for THIS specific sense, e.g. 'G0001G',
       'H0001G' (also not used here; several rows can share the same base
       number in column 0 but represent distinct senses)
    3  Word form(s) in the original script (Greek/Hebrew). Occasionally a
       comma-separated list of variant spellings for the same sense.
    4  Transliteration
    5  Morph code (not used here -- this app has its own morph scheme)
    6  Short gloss (a few words)
    7  Longer meaning/definition, lightly HTML-tagged (<b>, <i>, <BR />,
       <ref='...'>...</ref> citations)

Run once, after corpus.py / import_blb.py / import_lxx.py have built the
base corpus.db:
    python src/import_lexicon.py [path-to-data/lexicon-folder]
"""
import os, re, sqlite3, sys

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
from greek_translit import strip_accents_lower
from corpus import DB_PATH

DATA_ROOT_DEFAULT = os.path.join(os.path.dirname(SRC), 'data', 'lexicon')

_ROW_RE = re.compile(r'^([GH])(\d+)')


def _clean_meaning(raw):
    """Light HTML cleanup: drop <ref='...'> wrapper (keep inner text),
    turn <BR />/<br> into '; ', strip any other tags except <b>/<i>
    (kept since the popup already renders innerHTML elsewhere), collapse
    whitespace. This is a readability pass, not a full HTML sanitizer --
    the source is a controlled, trusted dataset, not user input."""
    s = raw.strip()
    s = re.sub(r"<ref=['\"][^'\"]*['\"]>(.*?)</ref>", r'\1', s, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub(r'<br\s*/?>', '; ', s, flags=re.IGNORECASE)
    s = re.sub(r'</?(?!/?[bi]\b)[a-zA-Z][^>]*>', '', s)  # strip tags other than b/i
    s = re.sub(r'\s+', ' ', s).strip(' ;')
    return s


def _numeric_key(base_col0):
    """'H0001' -> '1', 'G0122' -> '122'. Matches how this app's own
    corpus.py normalizes Hebrew Strong's numbers in words.lemma_norm
    (leading zeros and any letter/'+' disambiguation suffix dropped)."""
    m = _ROW_RE.match(base_col0)
    return m.group(2).lstrip('0') or '0' if m else None


def _parse_file(path, lang):
    """Yields (key_norm, estrong, translit, gloss, meaning) tuples.
    lang='grk' keys on normalized Greek word text (possibly several rows
    per lexeme, one per spelling variant); lang='heb' keys on the bare
    Strong's number."""
    with open(path, encoding='utf-8-sig') as f:
        for line in f:
            line = line.rstrip('\n\r')
            if not line or not _ROW_RE.match(line):
                continue
            cols = line.split('\t')
            if len(cols) < 8:
                continue
            base, _label, estrong, word, translit, _morph, gloss, meaning = cols[:8]
            meaning = _clean_meaning(meaning)

            if lang == 'grk':
                for form in word.split(','):
                    form = form.strip()
                    if not form:
                        continue
                    key = strip_accents_lower(form)
                    if key:
                        yield key, estrong, translit.strip(), gloss.strip(), meaning
            else:
                key = _numeric_key(base)
                if key:
                    yield key, estrong, translit.strip(), gloss.strip(), meaning


def import_lexicon(lexicon_dir=None, db_path=None):
    lexicon_dir = lexicon_dir or DATA_ROOT_DEFAULT
    db_path = db_path or DB_PATH

    tbesg = os.path.join(lexicon_dir, 'TBESG.txt')
    tbesh = os.path.join(lexicon_dir, 'TBESH.txt')
    if not os.path.exists(tbesg) or not os.path.exists(tbesh):
        print(f"  TBESG.txt / TBESH.txt not found in {lexicon_dir} -- skipping lexicon import.")
        return

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS lexicon")
    cur.execute("""CREATE TABLE lexicon (
        lang     TEXT NOT NULL,
        key_norm TEXT NOT NULL,
        estrong  TEXT,
        translit TEXT,
        gloss    TEXT,
        meaning  TEXT
    )""")

    # First-seen-wins per (lang, key_norm): both files are ordered roughly
    # by ascending Strong's number, so the first entry for a given base
    # number/spelling is reliably the primary/most common sense rather
    # than a rarer homograph or proper-noun sense listed further down.
    seen = set()
    rows = []
    for lang, path in (('grk', tbesg), ('heb', tbesh)):
        count = 0
        for key_norm, estrong, translit, gloss, meaning in _parse_file(path, lang):
            dedup_key = (lang, key_norm)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            rows.append((lang, key_norm, estrong, translit, gloss, meaning))
            count += 1
        print(f"  {lang}: {count:,} lexicon keys parsed from {os.path.basename(path)}")

    cur.executemany(
        "INSERT INTO lexicon(lang,key_norm,estrong,translit,gloss,meaning) VALUES(?,?,?,?,?,?)",
        rows)
    cur.execute("CREATE INDEX idx_lexicon ON lexicon(lang, key_norm)")
    con.commit()
    con.close()
    print(f"  Lexicon import complete: {len(rows):,} total entries -> {db_path}")


if __name__ == '__main__':
    lexicon_dir = sys.argv[1] if len(sys.argv) > 1 else DATA_ROOT_DEFAULT
    import_lexicon(lexicon_dir)
