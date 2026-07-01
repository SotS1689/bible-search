import sys, sqlite3, json
sys.path.insert(0, '/home/claude/bw/src')
from flask import Flask, request, jsonify, send_from_directory
from search import search, get_con, BOOK_NAMES
from corpus import DB_PATH

app = Flask(__name__, static_folder='/home/claude/bw/static')

NT_BOOKS = list(range(40, 67))
OT_BOOKS = list(range(1, 40))

@app.route('/')
def index():
    return send_from_directory('/home/claude/bw/static', 'index.html')

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    lang = request.args.get('lang', 'grk')
    if not q:
        return jsonify({'results': [], 'count': 0, 'error': None})
    try:
        results = search(q, lang)
        return jsonify({'results': results[:500], 'count': len(results), 'error': None})
    except Exception as e:
        return jsonify({'results': [], 'count': 0, 'error': str(e)})

@app.route('/api/verse')
def api_verse():
    """Return all words with morph info for a given verse."""
    book = int(request.args.get('book', 40))
    chapter = int(request.args.get('chapter', 1))
    verse = int(request.args.get('verse', 1))
    con = get_con()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT surface,lemma,bw_code,lang FROM words WHERE book=? AND chapter=? AND verse=? ORDER BY pos",
        (book, chapter, verse)).fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/passage')
def api_passage():
    """Return full chapter or range of verses."""
    book = int(request.args.get('book', 40))
    chapter = int(request.args.get('chapter', 1))
    con = get_con()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT verse,surface,pos FROM words WHERE book=? AND chapter=? ORDER BY verse,pos",
        (book, chapter)).fetchall()
    con.close()
    # Group by verse
    verses = {}
    for r in rows:
        verses.setdefault(r['verse'], []).append(r['surface'])
    return jsonify([{'verse': v, 'text': ' '.join(words)} for v, words in sorted(verses.items())])

@app.route('/api/books')
def api_books():
    con = get_con()
    cur = con.cursor()
    rows = cur.execute("SELECT DISTINCT book FROM words ORDER BY book").fetchall()
    con.close()
    return jsonify([{'num': r['book'], 'name': BOOK_NAMES.get(r['book'], str(r['book']))} for r in rows])

@app.route('/api/chapters')
def api_chapters():
    book = int(request.args.get('book', 40))
    con = get_con()
    cur = con.cursor()
    rows = cur.execute("SELECT DISTINCT chapter FROM words WHERE book=? ORDER BY chapter", (book,)).fetchall()
    con.close()
    return jsonify([r['chapter'] for r in rows])

if __name__ == '__main__':
    app.run(port=7070, debug=False)
