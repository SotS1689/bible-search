"""
Full BibleWorks-style search engine against the SQLite corpus.
Evaluates parsed query ASTs from query.py.
"""
import sqlite3, re, sys, unicodedata
sys.path.insert(0, '/home/claude/bw/src')
from query import parse, Word, Phrase, And, Or, wildcard_to_regex, morph_code_matches
from greek_translit import translit_query_to_greek, strip_accents_lower
from corpus import DB_PATH, BOOK_NAMES

def get_con():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def normalize_term(raw: str, lang: str) -> str:
    """Normalize a query term to the same form as corpus lemma_norm / surface_norm."""
    if lang == 'grk':
        # Input might be BW-keyboard Latin or already Greek
        maybe_greek = translit_query_to_greek(raw)
        return strip_accents_lower(maybe_greek)
    else:
        return raw  # Hebrew: Strong's numbers or bare consonants

def wildcard_sql(pattern: str, column: str) -> tuple[str, list]:
    """Convert a wildcard pattern (*?) to SQL LIKE (% _) for fast pre-filtering."""
    like = pattern.replace('*', '%').replace('?', '_')
    return f"{column} LIKE ?", [like]

def term_refs(term: Word, lang: str, cur) -> set:
    """Return set of (book,chapter,verse) tuples containing this term."""
    raw = term.raw
    has_morph = '@' in raw
    if has_morph:
        lemma_pat, code_pat = raw.split('@', 1)
    else:
        lemma_pat, code_pat = raw, None

    norm = normalize_term(lemma_pat, lang)
    has_wildcard = '*' in norm or '?' in norm

    if has_wildcard:
        sql_cond, params = wildcard_sql(norm, 'surface_norm')
        sql2, p2 = wildcard_sql(norm, 'lemma_norm')
        cond = f"({sql_cond} OR {sql2})"
        params = params + p2
    else:
        cond = "(surface_norm = ? OR lemma_norm = ?)"
        params = [norm, norm]

    if lang:
        cond += " AND lang = ?"
        params.append(lang)

    rows = cur.execute(f"SELECT book,chapter,verse,bw_code FROM words WHERE {cond}", params).fetchall()

    if code_pat:
        # filter by morph code
        result = set()
        for r in rows:
            if morph_code_matches(code_pat, r['bw_code']):
                result.add((r['book'], r['chapter'], r['verse']))
        return result
    else:
        return {(r['book'], r['chapter'], r['verse']) for r in rows}

def phrase_refs(phrase: Phrase, lang: str, cur) -> set:
    """Find verses containing the phrase (with optional gap)."""
    # Get candidate verses from first term
    if not phrase.words:
        return set()
    candidates = term_refs(phrase.words[0], lang, cur)
    result = set()
    for ref in candidates:
        b, c, v = ref
        verse_words = cur.execute(
            "SELECT surface_norm,lemma_norm,bw_code FROM words WHERE book=? AND chapter=? AND verse=? ORDER BY pos",
            (b, c, v)).fetchall()
        if _phrase_in_words(phrase, verse_words, lang):
            result.add(ref)
    return result

def _phrase_in_words(phrase, verse_words, lang):
    n = len(verse_words)
    for start in range(n):
        idx = start
        ok = True
        for term in phrase.words:
            raw = term.raw
            if '@' in raw:
                lemma_pat, code_pat = raw.split('@', 1)
            else:
                lemma_pat, code_pat = raw, None
            norm = normalize_term(lemma_pat, lang)
            pat = wildcard_to_regex(norm)
            found = None
            for j in range(idx, min(idx + phrase.max_gap + 2, n)):
                w = verse_words[j]
                if pat.match(w['surface_norm']) or pat.match(w['lemma_norm']):
                    if code_pat is None or morph_code_matches(code_pat, w['bw_code']):
                        found = j
                        break
            if found is None:
                ok = False
                break
            idx = found + 1
        if ok:
            return True
    return False

def eval_ast(node, lang: str, cur, all_refs=None):
    if all_refs is None:
        rows = cur.execute("SELECT DISTINCT book,chapter,verse FROM words WHERE lang=?", (lang,)).fetchall()
        all_refs = {(r['book'], r['chapter'], r['verse']) for r in rows}

    if isinstance(node, Word):
        return term_refs(node, lang, cur)

    if isinstance(node, Phrase):
        return phrase_refs(node, lang, cur)

    if isinstance(node, And):
        result = None
        for term in node.positive:
            hits = eval_ast(term, lang, cur, all_refs)
            result = hits if result is None else (result & hits)
        if result is None:
            result = set()
        if node.proximity is not None:
            # re-check: all positive terms must appear within proximity verses of each other
            result = _prox_filter(node.positive, result, node.proximity, lang, cur)
        for term in node.negative:
            hits = eval_ast(term, lang, cur, all_refs)
            result -= hits
        return result

    if isinstance(node, Or):
        result = set()
        for opt in node.options:
            result |= eval_ast(opt, lang, cur, all_refs)
        return result

    raise ValueError(f"Unknown node: {node}")

def _prox_filter(positive_terms, candidate_refs, n_verses, lang, cur):
    """Keep only refs where all terms co-occur within n_verses of each other."""
    # Collect all refs for each term
    term_ref_sets = [eval_ast(t, lang, cur) for t in positive_terms]
    result = set()
    for ref in candidate_refs:
        b, c, v = ref
        for tset in term_ref_sets:
            window = {(b, c, vv) for vv in range(v - n_verses, v + n_verses + 1)}
            if not (tset & window):
                break
        else:
            result.add(ref)
    return result

def search(cmdline: str, lang: str = 'grk'):
    """Main entry point: returns sorted list of (book,chapter,verse) dicts with verse text."""
    ast = parse(cmdline)
    con = get_con()
    cur = con.cursor()
    refs = eval_ast(ast, lang, cur)
    # Fetch verse text for each hit
    results = []
    for ref in sorted(refs):
        b, c, v = ref
        words = cur.execute(
            "SELECT surface FROM words WHERE book=? AND chapter=? AND verse=? ORDER BY pos",
            (b, c, v)).fetchall()
        text = ' '.join(w['surface'] for w in words)
        results.append({
            'book': b, 'chapter': c, 'verse': v,
            'ref': f"{BOOK_NAMES.get(b, str(b))} {c}:{v}",
            'text': text,
        })
    con.close()
    return results

if __name__ == '__main__':
    print("=== Greek: .cristoj ===")
    for r in search('.cristoj', 'grk')[:5]:
        print(f"  {r['ref']}: {r['text'][:80]}")
    print(f"  total: {len(search('.cristoj','grk'))}")

    print("\n=== Greek phrase: 'ihsouj cristoj ===")
    for r in search("'ihsouj cristoj", 'grk')[:5]:
        print(f"  {r['ref']}: {r['text'][:80]}")

    print("\n=== Hebrew: .1254 (bara = create) ===")
    for r in search('.1254', 'heb')[:5]:
        print(f"  {r['ref']}: {r['text'][:80]}")

    print("\n=== Greek morph: .*@vii3s* (impf ind 3sg, any verb) ===")
    hits = search('.*@vii3s*', 'grk')
    print(f"  total: {len(hits)} | sample: {hits[0]['ref'] if hits else 'none'}")
