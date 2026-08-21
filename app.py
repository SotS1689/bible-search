import sys, sqlite3, json, os

# Under a PyInstaller --onefile build, bundled files (src/, static/, data/)
# are unpacked to a temp dir at sys._MEIPASS on each launch; __file__ can't
# be relied on the same way it can for a normal script. Not frozen -> same
# behavior as always (folder containing this file).
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from flask import Flask, request, jsonify, send_from_directory
from search import search, search_english, get_con, BOOK_NAMES
from books import book_sort_key

app = Flask(__name__, static_folder=os.path.join(ROOT, 'static'))

@app.route('/')
def index():
    return send_from_directory(os.path.join(ROOT, 'static'), 'index.html')

def _search_english_inline(cmdline, book_from=None, book_to=None):
    """English BLB search: proper word-boundary matching, phrase gaps, proximity."""
    import sqlite3, os, re
    from corpus import DB_PATH, BOOK_NAMES
    from query import parse, Word, Phrase, And, Or

    # ── helpers ──────────────────────────────────────────────────────────────
    def word_re(raw):
        """Build a word-boundary regex for a term, supporting * and ? wildcards."""
        pat = re.escape(raw).replace(r'\*', r'\w*').replace(r'\?', r'\w')
        return re.compile(r'\b' + pat + r'\b', re.IGNORECASE)

    def word_match(text, raw):
        raw = raw.lstrip(".'!/\\")   # strip any leading operator chars the parser may include
        if not raw: return False
        return bool(word_re(raw).search(text))

    def phrase_match(text, phrase):
        words = [w.raw for w in phrase.words]
        if phrase.max_gap == 0:
            pat = r'\s+'.join(r'\b' + re.escape(w) + r'\b' for w in words)
        else:
            gap = r'(?:\s+\S+){0,' + str(phrase.max_gap) + r'}\s+'
            pat = gap.join(r'\b' + re.escape(w) + r'\b' for w in words)
        return bool(re.search(pat, text, re.IGNORECASE))

    def eval_node(node, text):
        if isinstance(node, Word):   return word_match(text, node.raw)
        if isinstance(node, Phrase): return phrase_match(text, node)
        if isinstance(node, And):
            return (all(eval_node(t, text) for t in node.positive) and
                    not any(eval_node(t, text) for t in node.negative))
        if isinstance(node, Or):
            return any(eval_node(o, text) for o in node.options)
        return False

    def extract_terms(node):
        if isinstance(node, Word):   return [node.raw]
        if isinstance(node, Phrase): return [w.raw for w in node.words]
        if isinstance(node, And):
            return [t for n in node.positive for t in extract_terms(n)]
        if isinstance(node, Or):
            return [t for o in node.options for t in extract_terms(o)]
        return []

    # ── parse query ──────────────────────────────────────────────────────────
    ast      = parse(cmdline)
    all_terms = extract_terms(ast)
    hl       = list(set(t.lower() for t in all_terms))

    # ── connect ──────────────────────────────────────────────────────────────
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
        cur.execute("SELECT 1 FROM translations LIMIT 1")
    except Exception:
        con.close()
        return [], hl, []

    # ── proximity: requires cross-verse lookup ────────────────────────────────
    if isinstance(ast, And) and ast.proximity is not None:
        N = ast.proximity
        # Collect verse sets per positive term
        term_verse_sets = []
        for term in ast.positive:
            t_terms = extract_terms(term)
            sql = ("SELECT book,chapter,verse,text FROM translations WHERE version='BLB'"
                   + (f" AND book>={book_from}" if book_from else "")
                   + (f" AND book<={book_to}"   if book_to   else ""))
            rows = cur.execute(sql).fetchall()
            hits = set()
            for row in rows:
                if eval_node(term, row[3]):
                    hits.add((row[0], row[1], row[2]))
            term_verse_sets.append(hits)
        # Find verses where all terms co-occur within N verses
        all_hit_refs = set().union(*term_verse_sets)
        results = []
        seen = set()
        for (b, c, v) in sorted(all_hit_refs):
            if (b, c, v) in seen: continue
            window = {(b, c, vv) for vv in range(v-N, v+N+1)}
            if all(bool(ts & window) for ts in term_verse_sets):
                for (b2, c2, v2) in sorted(window & all_hit_refs):
                    if (b2, c2, v2) not in seen:
                        seen.add((b2, c2, v2))
                        row = cur.execute(
                            "SELECT text FROM translations WHERE book=? AND chapter=? AND verse=? AND version='BLB'",
                            (b2, c2, v2)).fetchone()
                        if row:
                            results.append({'book':b2,'chapter':c2,'verse':v2,
                                'ref':f"{BOOK_NAMES.get(b2,str(b2))} {c2}:{v2}",
                                'text':row[0]})
        con.close()
        return results, hl, []

    # ── standard search: SQL pre-filter + Python evaluation ───────────────────
    conditions = ["version='BLB'"]
    params     = []
    if book_from: conditions.append(f"book>={int(book_from)}")
    if book_to:   conditions.append(f"book<={int(book_to)}")

    # Pre-filter: LIKE to narrow candidates before Python evaluation
    # For OR queries use OR-LIKE; for AND queries use AND-LIKE
    def make_like(t):
        return '%' + t.lstrip(".'!/").replace('*','%').replace('?','_') + '%'

    if isinstance(ast, Or):
        if all_terms:
            or_likes = ['text LIKE ?' for _ in all_terms]
            conditions.append('(' + ' OR '.join(or_likes) + ')')
            params.extend(make_like(t) for t in all_terms)
    else:
        for t in all_terms:
            conditions.append("text LIKE ?")
            params.append(make_like(t))

    sql  = ("SELECT book,chapter,verse,text FROM translations WHERE "
            + " AND ".join(conditions) + " ORDER BY book,chapter,verse")
    rows = cur.execute(sql, params).fetchall()
    con.close()

    # Python evaluation for precise word-boundary and phrase matching
    results = []
    for row in rows:
        b, c, v, text = row[0], row[1], row[2], row[3]
        if eval_node(ast, text):
            results.append({'book':b,'chapter':c,'verse':v,
                'ref':f"{BOOK_NAMES.get(b,str(b))} {c}:{v}",'text':text})
    return results, hl, []


@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    lang = request.args.get('lang', 'grk')
    if not q:
        return jsonify({'results': [], 'count': 0, 'error': None})
    book_from = request.args.get('book_from', type=int)
    book_to   = request.args.get('book_to',   type=int)
    try:
        if lang == 'eng':
            results, hl_terms, hl_strongs = _search_english_inline(q, book_from, book_to)
        else:
            results, hl_terms, hl_strongs = search(q, lang, book_from, book_to)
        return jsonify({
            'results': results,
            'count': len(results),
            'hl_terms': hl_terms,
            'hl_strongs': hl_strongs,
            'error': None,
        })
    except Exception as e:
        return jsonify({'results': [], 'count': 0, 'hl_terms': [], 'hl_strongs': [], 'error': str(e)})

EDITION_LABELS = {
    'A': 'Codex A (Alexandrinus)', 'B': 'Codex B (Vaticanus)',
    'OG': 'Old Greek', 'TH': 'Theodotion',
    'BA': 'Vaticanus/Alexandrinus text', 'S': 'Sinaiticus text',
}

def _primary_edition(editions):
    """Pick a single deterministic edition to display for books that have
    more than one Greek text tradition, until the frontend supports
    rendering both stacked. Prefers the un-edition-tagged case (NT/Hebrew/
    most LXX books), else the alphabetically-first edition code."""
    if None in editions:
        return None
    return sorted(editions)[0] if editions else None

@app.route('/api/verse')
def api_verse():
    book    = int(request.args.get('book', 40))
    chapter = int(request.args.get('chapter', 1))
    verse   = int(request.args.get('verse', 1))
    lang    = request.args.get('lang') or ('heb' if book <= 39 else 'grk')
    # Optional explicit edition selector (e.g. 'A', 'B', 'OG', 'TH'...). When
    # present -- even as an empty string, meaning "the untagged/None edition"
    # -- it overrides the default "pick one primary edition" behavior below,
    # so callers can fetch each edition of a dual-tradition verse in turn.
    edition_param = request.args.get('edition')
    con = get_con()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT surface,surface_norm,lemma,lemma_norm,bw_code,lang,edition FROM words "
        "WHERE book=? AND chapter=? AND verse=? AND lang=? ORDER BY edition,pos",
        (book, chapter, verse, lang)).fetchall()
    con.close()
    if edition_param is not None:
        chosen = edition_param if edition_param not in ('', 'null', 'None') else None
    else:
        editions = {r['edition'] for r in rows}
        chosen = _primary_edition(editions)
    out = [dict(r) for r in rows if r['edition'] == chosen]
    for d in out:
        d.pop('edition', None)
    return jsonify(out)

@app.route('/api/passage')
def api_passage():
    book    = int(request.args.get('book', 40))
    chapter = int(request.args.get('chapter', 1))
    lang    = request.args.get('lang') or ('heb' if book <= 39 else 'grk')
    con = get_con()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT verse,surface,pos,edition FROM words WHERE book=? AND chapter=? AND lang=? ORDER BY verse,edition,pos",
        (book, chapter, lang)).fetchall()
    con.close()
    by_verse_ed = {}
    for r in rows:
        by_verse_ed.setdefault(r['verse'], {}).setdefault(r['edition'], []).append(r['surface'])
    out = []
    for v in sorted(by_verse_ed):
        editions = by_verse_ed[v]
        ed_keys = sorted(editions.keys(), key=lambda e: (e is not None, e or ''))
        texts = [{'edition': ed, 'label': EDITION_LABELS.get(ed), 'text': ' '.join(editions[ed])}
                 for ed in ed_keys]
        primary = _primary_edition(set(ed_keys))
        primary_text = ' '.join(editions[primary]) if primary in editions else texts[0]['text']
        # 'text' stays for backward compatibility (single primary edition);
        # 'texts' is the full per-edition breakdown (length 1 for the
        # common single-tradition case, >1 for books like Judges A/B).
        out.append({'verse': v, 'text': primary_text, 'texts': texts})
    return jsonify(out)

@app.route('/api/gloss')
def api_gloss():
    """Lexicon lookup for word-hover glosses. `key` must already be
    normalized the same way words.lemma_norm is: accent-stripped lowercase
    Greek text for lang='grk', or a bare Strong's number string for
    lang='heb' -- i.e. exactly what the frontend already has on hand as
    each word-span's `lemmaNorm` dataset attribute, so no extra
    normalization is needed here."""
    lang = request.args.get('lang', 'grk')
    key  = request.args.get('key', '').strip()
    if not key:
        return jsonify(None)
    con = get_con()
    cur = con.cursor()
    try:
        row = cur.execute(
            "SELECT estrong, translit, gloss, meaning FROM lexicon WHERE lang=? AND key_norm=?",
            (lang, key)).fetchone()
    except sqlite3.OperationalError:
        row = None  # corpus.db predates the lexicon table -- no gloss available
    con.close()
    return jsonify(dict(row) if row else None)

@app.route('/api/books')
def api_books():
    con = get_con()
    cur = con.cursor()
    rows = cur.execute("SELECT DISTINCT book FROM words").fetchall()
    con.close()
    nums = sorted((r['book'] for r in rows), key=book_sort_key)
    return jsonify([{'num': n, 'name': BOOK_NAMES.get(n, str(n))} for n in nums])

@app.route('/api/chapters')
def api_chapters():
    book = int(request.args.get('book', 40))
    con = get_con()
    cur = con.cursor()
    rows = cur.execute("SELECT DISTINCT chapter FROM words WHERE book=? ORDER BY chapter", (book,)).fetchall()
    con.close()
    return jsonify([r['chapter'] for r in rows])

@app.route('/api/translation')
def api_translation():
    """Return English translation verses for a whole chapter."""
    book    = int(request.args.get('book', 40))
    chapter = int(request.args.get('chapter', 1))
    version = request.args.get('version', 'BLB')
    con = get_con()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT verse, text FROM translations WHERE book=? AND chapter=? AND version=? ORDER BY verse",
        (book, chapter, version)).fetchall()
    con.close()
    return jsonify({r['verse']: r['text'] for r in rows})

@app.route('/api/resolve_limit')
def api_resolve_limit():
    from books import parse_limit, canonical_name
    s = request.args.get('q', '').strip()
    result = parse_limit(s)
    if result:
        b1, b2 = result
        return jsonify({'book_from': b1, 'book_to': b2,
                        'label': canonical_name(b1) if b1 == b2
                                 else f"{canonical_name(b1)} – {canonical_name(b2)}"})
    return jsonify({'error': f'Unknown book or range: "{s}"'})

if __name__ == '__main__':
    app.run(port=7070, debug=False)
