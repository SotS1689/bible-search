import sqlite3, re, sys, os

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)

from query import parse, Word, Phrase, And, Or, wildcard_to_regex, morph_code_matches
from greek_translit import translit_query_to_greek, strip_accents_lower
from corpus import DB_PATH, BOOK_NAMES
from books import book_sort_key

def get_con():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def is_hebrew_text(s):
    return any('\u05D0' <= c <= '\u05EA' for c in s)

def strip_niqqud(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()

def normalize_term(raw, lang):
    if lang == 'grk':
        return strip_accents_lower(translit_query_to_greek(raw))
    if lang == 'heb' and is_hebrew_text(raw):
        return strip_niqqud(raw)
    return raw

def heb_text_to_strongs(heb_bare, cur):
    """Look up a Hebrew lemma text in the index; return list of Strong's numbers.
    Supports * and ? wildcards via SQL LIKE."""
    if '*' in heb_bare or '?' in heb_bare:
        like = heb_bare.replace('*', '%').replace('?', '_')
        rows = cur.execute(
            "SELECT strong_num FROM heb_lemma_index WHERE lemma_bare LIKE ?", (like,)
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT strong_num FROM heb_lemma_index WHERE lemma_bare=?", (heb_bare,)
        ).fetchall()
    return [r[0] for r in rows]

def term_refs(term, lang, cur):
    raw = term.raw
    has_morph = '@' in raw
    lemma_pat, code_pat = (raw.split('@', 1) if has_morph else (raw, None))
    norm = normalize_term(lemma_pat, lang)
    has_wc = '*' in norm or '?' in norm

    if has_wc:
        like = norm.replace('*', '%').replace('?', '_')
        cond   = "(surface_norm LIKE ? OR lemma_norm LIKE ?)"
        params = [like, like]
    elif lang == 'heb' and is_hebrew_text(norm):
        # Hebrew text: resolve to Strong's number(s) via lemma index,
        # then search exactly like .1254 — by lemma_norm.
        strong_nums = heb_text_to_strongs(norm, cur)
        if not strong_nums:
            return set()
        placeholders = ','.join('?' * len(strong_nums))
        cond   = f"lemma_norm IN ({placeholders})"
        params = strong_nums
    else:
        cond   = "(surface_norm = ? OR lemma_norm = ?)"
        params = [norm, norm]

    if lang:
        cond += " AND lang = ?"
        params.append(lang)

    rows = cur.execute(f"SELECT book,chapter,verse,bw_code FROM words WHERE {cond}", params).fetchall()

    if code_pat:
        result = set()
        for r in rows:
            if morph_code_matches(code_pat, r['bw_code']):
                result.add((r['book'], r['chapter'], r['verse']))
        return result
    return {(r['book'], r['chapter'], r['verse']) for r in rows}

def phrase_refs(phrase, lang, cur):
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
        idx, ok = start, True
        for term in phrase.words:
            raw = term.raw
            lemma_pat, code_pat = (raw.split('@', 1) if '@' in raw else (raw, None))
            norm = normalize_term(lemma_pat, lang)
            pat  = wildcard_to_regex(norm)
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

def eval_ast(node, lang, cur, all_refs=None):
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
            result = _prox_filter(node.positive, result, node.proximity, lang, cur)
        for term in node.negative:
            result -= eval_ast(term, lang, cur, all_refs)
        return result
    if isinstance(node, Or):
        result = set()
        for opt in node.options:
            result |= eval_ast(opt, lang, cur, all_refs)
        return result
    raise ValueError(f"Unknown node: {node}")

def _prox_filter(positive_terms, candidate_refs, n_verses, lang, cur):
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

def collect_highlight_terms(ast, lang, cur):
    """Walk the AST and collect all normalized lemma/surface terms for highlighting.
    For Hebrew text input, also resolve to Strong's numbers."""
    terms = set()
    strong_nums = set()

    def walk(node):
        if isinstance(node, Word):
            raw = node.raw
            lemma_pat = raw.split('@')[0] if '@' in raw else raw
            norm = normalize_term(lemma_pat, lang)
            if lang == 'heb' and is_hebrew_text(norm):
                # Hebrew text (with or without wildcard) → resolve to Strong's numbers
                for snum in heb_text_to_strongs(norm, cur):
                    strong_nums.add(snum)
            elif lang == 'heb' and norm and norm not in ('*', '?', '.*', '.?'):
                # Strong's number search (e.g. 1254 or 1254*)
                has_wc = '*' in norm or '?' in norm
                if has_wc:
                    like = norm.replace('*', '%').replace('?', '_')
                    rows = cur.execute(
                        "SELECT DISTINCT lemma_norm FROM words WHERE lang='heb' AND lemma_norm LIKE ?",
                        (like,)).fetchall()
                    for r in rows:
                        strong_nums.add(r[0])
                else:
                    strong_nums.add(norm)
            elif lang != 'heb' and norm and norm not in ('*', '?'):
                # Greek: add normalized term (including wildcards for regex matching in JS)
                terms.add(norm)
        elif isinstance(node, Phrase):
            for w in node.words:
                walk(w)
        elif isinstance(node, (And, Or)):
            lst = (node.positive + node.negative) if isinstance(node, And) else node.options
            for child in lst:
                walk(child)
    walk(ast)
    return list(terms), list(strong_nums)


# ─── English (BLB) search ────────────────────────────────────────────────────
# Uses SQL LIKE for all matching — avoids Python regex issues on Windows.

def _term_to_like(raw):
    """Convert wildcard term to SQL LIKE pattern."""
    return raw.replace('*', '%').replace('?', '_')

def _build_eng_sql(node, params, book_from=None, book_to=None):
    """
    Build a SQL WHERE clause from the query AST.
    Returns (where_str, params_list).
    Falls back to None for unsupported node types (handled in Python).
    """
    base = "version='BLB'"
    if book_from: base += f" AND book >= {int(book_from)}"
    if book_to:   base += f" AND book <= {int(book_to)}"

    def node_sql(n):
        if isinstance(n, Word):
            like = '%' + _term_to_like(n.raw) + '%'
            params.append(like)
            return f"text LIKE ? ESCAPE '\\'"
        if isinstance(n, Phrase):
            # Simple phrase: all words must appear (in order approximation via LIKE chain)
            parts = []
            for w in n.words:
                like = '%' + _term_to_like(w.raw) + '%'
                params.append(like)
                parts.append("text LIKE ?")
            return ' AND '.join(parts)
        if isinstance(n, And):
            pos = [node_sql(t) for t in n.positive]
            neg = [f"NOT ({node_sql(t)})" for t in n.negative]
            return ' AND '.join(pos + neg)
        if isinstance(n, Or):
            return '(' + ' OR '.join(node_sql(o) for o in n.options) + ')'
        return "1=1"

    return base + " AND " + node_sql(node)

def _extract_eng_terms(node):
    """Collect search terms for client-side highlighting."""
    terms = []
    if isinstance(node, Word):
        terms.append(node.raw.lower())
    elif isinstance(node, Phrase):
        for w in node.words: terms.append(w.raw.lower())
    elif isinstance(node, And):
        for t in node.positive: terms.extend(_extract_eng_terms(t))
    elif isinstance(node, Or):
        for o in node.options: terms.extend(_extract_eng_terms(o))
    return terms

def search_english(cmdline, book_from=None, book_to=None):
    """Search the BLB English translation using SQL LIKE matching."""
    import sqlite3, os
    ast = parse(cmdline)

    root    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(root, 'data', 'corpus.db')

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    params  = []
    where   = _build_eng_sql(ast, params, book_from, book_to)
    sql     = f"SELECT book, chapter, verse, text FROM translations WHERE {where} ORDER BY book, chapter, verse"

    rows     = cur.execute(sql, params).fetchall()
    con.close()

    hl_terms = list(set(_extract_eng_terms(ast)))
    results  = []
    for row in rows:
        b, c, v, text = row[0], row[1], row[2], row[3]
        results.append({
            'book': b, 'chapter': c, 'verse': v,
            'ref':  f"{BOOK_NAMES.get(b, str(b))} {c}:{v}",
            'text': text,
        })
    return results, hl_terms, []


def search(cmdline, lang='grk', book_from=None, book_to=None):
    ast = parse(cmdline)
    con = get_con()
    cur = con.cursor()
    refs = eval_ast(ast, lang, cur)

    # Apply book range limit if set
    if book_from is not None or book_to is not None:
        lo = book_from if book_from is not None else 1
        hi = book_to   if book_to   is not None else 999
        refs = {r for r in refs if lo <= r[0] <= hi}

    hl_terms, hl_strongs = collect_highlight_terms(ast, lang, cur)

    results = []
    for ref in sorted(refs, key=lambda r: (book_sort_key(r[0]), r[1], r[2])):
        b, c, v = ref
        words = cur.execute(
            "SELECT surface,edition FROM words WHERE book=? AND chapter=? AND verse=? ORDER BY edition,pos",
            (b, c, v)).fetchall()
        by_edition, order = {}, []
        for w in words:
            ed = w['edition']
            by_edition.setdefault(ed, []).append(w['surface'])
            if ed not in order:
                order.append(ed)
        texts = [{'edition': ed, 'text': ' '.join(by_edition[ed])} for ed in order]
        results.append({
            'book': b, 'chapter': c, 'verse': v,
            'ref':  f"{BOOK_NAMES.get(b, str(b))} {c}:{v}",
            'text': texts[0]['text'],   # backward-compatible single-text field
            'texts': texts,             # full edition breakdown (>1 entry for dual-tradition books)
        })
    con.close()
    return results, hl_terms, hl_strongs
