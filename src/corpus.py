import sqlite3, sys, os, glob

def _app_root():
    """Resolve the project root for both normal 'python app.py' execution
    and a PyInstaller-frozen executable.

    Frozen (--onefile): bundled data (read-only) is unpacked to a temp dir
    at sys._MEIPASS each launch. corpus.db is only ever read from here
    (never written), so it's safe to use straight out of _MEIPASS.

    Not frozen: behaves exactly as before (two dirs up from this file)."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT    = _app_root()
DATA    = os.path.join(ROOT, 'data')
DB_PATH = os.path.join(DATA, 'corpus.db')
SRC     = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)

from greek_map import load_morphgnt
from hebrew_map import load_oshb_book, OSHB_BOOKS
from greek_translit import strip_accents_lower

MORPHGNT_BOOK_NUMS = {
    '61-Mt':40,'62-Mk':41,'63-Lk':42,'64-Jn':43,'65-Ac':44,
    '66-Ro':45,'67-1Co':46,'68-2Co':47,'69-Ga':48,'70-Eph':49,
    '71-Php':50,'72-Col':51,'73-1Th':52,'74-2Th':53,'75-1Ti':54,
    '76-2Ti':55,'77-Tit':56,'78-Phm':57,'79-Heb':58,'80-Jas':59,
    '81-1Pe':60,'82-2Pe':61,'83-1Jn':62,'84-2Jn':63,'85-3Jn':64,
    '86-Jud':65,'87-Re':66,
}
BOOK_NAMES = {
    1:'Gen',2:'Exod',3:'Lev',4:'Num',5:'Deut',6:'Josh',7:'Judg',8:'Ruth',
    9:'1Sam',10:'2Sam',11:'1Kgs',12:'2Kgs',13:'1Chr',14:'2Chr',15:'Ezra',
    16:'Neh',17:'Esth',18:'Job',19:'Ps',20:'Prov',21:'Eccl',22:'Song',
    23:'Isa',24:'Jer',25:'Lam',26:'Ezek',27:'Dan',28:'Hos',29:'Joel',
    30:'Amos',31:'Obad',32:'Jonah',33:'Mic',34:'Nah',35:'Hab',36:'Zeph',
    37:'Hag',38:'Zech',39:'Mal',
    40:'Matt',41:'Mark',42:'Luke',43:'John',44:'Acts',45:'Rom',
    46:'1Cor',47:'2Cor',48:'Gal',49:'Eph',50:'Phil',51:'Col',
    52:'1Thess',53:'2Thess',54:'1Tim',55:'2Tim',56:'Titus',57:'Phlm',
    58:'Heb',59:'Jas',60:'1Pet',61:'2Pet',62:'1John',63:'2John',
    64:'3John',65:'Jude',66:'Rev',
    # LXX-only / deuterocanonical books (no Hebrew-canon equivalent)
    67:'1Esd',68:'2Esd',69:'Jdt',70:'Tob',
    71:'1Macc',72:'2Macc',73:'3Macc',74:'4Macc',
    75:'Odes',76:'Wis',77:'Sir',78:'PsSol',
    79:'Bar',80:'EpJer',81:'Sus',82:'Bel',
}

def build(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    # Back up translations table if it exists (so rebuild doesn't wipe BLB data)
    _has_trans = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='translations'"
    ).fetchone() is not None
    _trans_rows = []
    if _has_trans:
        _trans_rows = cur.execute("SELECT book,chapter,verse,version,text FROM translations").fetchall()
        print(f"  Preserving {len(_trans_rows):,} translation rows across rebuild...")

    # Back up any previously-imported LXX rows (lang='grk' in book 1-39 or
    # 67-82) so rebuilding the NT/Hebrew corpus doesn't wipe them out.
    _has_words = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='words'"
    ).fetchone() is not None
    _lxx_rows = []
    if _has_words:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(words)").fetchall()]
        if 'edition' in cols:
            _lxx_rows = cur.execute(
                "SELECT lang,book,chapter,verse,pos,surface,surface_norm,lemma,lemma_norm,bw_code,edition "
                "FROM words WHERE lang='grk' AND (book<=39 OR book>=67)").fetchall()
            if _lxx_rows:
                print(f"  Preserving {len(_lxx_rows):,} LXX word rows across rebuild...")

    cur.execute('DROP TABLE IF EXISTS words')
    cur.execute('''CREATE TABLE words (
        id INTEGER PRIMARY KEY,
        lang TEXT, book INTEGER, chapter INTEGER, verse INTEGER, pos INTEGER,
        surface TEXT, surface_norm TEXT, lemma TEXT, lemma_norm TEXT, bw_code TEXT,
        edition TEXT
    )''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_ref   ON words(book,chapter,verse)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_lemma ON words(lemma_norm)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_code  ON words(bw_code)')

    rows = []

    gnt_dir = DATA
    for fname in sorted(glob.glob(os.path.join(gnt_dir, '*-morphgnt.txt'))):
        key = os.path.basename(fname).replace('-morphgnt.txt', '')
        book_num = MORPHGNT_BOOK_NUMS.get(key)
        if book_num is None:
            continue
        words = load_morphgnt(fname)
        for w in words:
            lemma_n = strip_accents_lower(w['lemma'])
            rows.append(('grk', book_num, w['chapter'], w['verse'],
                         len(rows),
                         w['surface'], strip_accents_lower(w['surface']),
                         w['lemma'], lemma_n, w['bw_code']))
        print(f"  GNT {key}: {len(words)} words")

    for book_name, book_num in OSHB_BOOKS:
        xml_path = os.path.join(DATA, 'heb', f'{book_name}.xml')
        if not os.path.exists(xml_path):
            continue
        words = load_oshb_book(xml_path, book_num)
        for w in words:
            rows.append(('heb', book_num, w['chapter'], w['verse'], w['pos'],
                         w['surface'], w['surface_bare'],
                         w['lemma'], w['lemma'],
                         w['bw_code']))
        print(f"  OT  {book_name}: {len(words)} words")

    cur.executemany(
        'INSERT INTO words(lang,book,chapter,verse,pos,surface,surface_norm,lemma,lemma_norm,bw_code,edition) VALUES(?,?,?,?,?,?,?,?,?,?,NULL)',
        rows)
    if _lxx_rows:
        cur.executemany(
            'INSERT INTO words(lang,book,chapter,verse,pos,surface,surface_norm,lemma,lemma_norm,bw_code,edition) '
            'VALUES(?,?,?,?,?,?,?,?,?,?,?)', _lxx_rows)
        print(f"  Restored {len(_lxx_rows):,} LXX word rows.")
    # Normalize Hebrew lemma disambiguation suffixes (' a', ' b', ' c')
    con.execute("UPDATE words SET lemma_norm = TRIM(SUBSTR(lemma, 1, CASE WHEN INSTR(lemma,' ') > 0 THEN INSTR(lemma,' ')-1 ELSE LENGTH(lemma) END)) WHERE lang='heb'")
    # Restore translations table
    if _trans_rows:
        cur.execute('''CREATE TABLE IF NOT EXISTS translations (
            book    INTEGER NOT NULL,
            chapter INTEGER NOT NULL,
            verse   INTEGER NOT NULL,
            version TEXT    NOT NULL,
            text    TEXT    NOT NULL,
            PRIMARY KEY (book, chapter, verse, version)
        )''')
        cur.execute("CREATE INDEX IF NOT EXISTS idx_trans ON translations(book,chapter,version)")
        cur.executemany(
            "INSERT OR REPLACE INTO translations(book,chapter,verse,version,text) VALUES(?,?,?,?,?)",
            _trans_rows)
        print(f"  Restored {len(_trans_rows):,} translation rows.")
    con.commit()

    # Build Hebrew lemma text -> Strong's number lookup table
    # using the OpenScriptures Hebrew Lexicon (HebrewStrong.xml) which gives
    # the authoritative lemma text (with niqqud) for each Strong's number.
    print("  Building Hebrew lemma-text index from lexicon...")
    import unicodedata
    from xml.etree import ElementTree as ET

    lex_path = os.path.join(DATA, 'HebrewStrong.xml')
    cur2 = con.cursor()
    cur2.execute("DROP TABLE IF EXISTS heb_lemma_index")
    cur2.execute("""CREATE TABLE heb_lemma_index (
        lemma_bare TEXT NOT NULL,
        strong_num TEXT NOT NULL
    )""")
    cur2.execute("CREATE INDEX idx_hli ON heb_lemma_index(lemma_bare)")

    index_rows = []
    if os.path.exists(lex_path):
        NS_LEX = 'http://openscriptures.github.com/morphhb/namespace'
        tree = ET.parse(lex_path)
        def _strip(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s)
                            if unicodedata.category(c) != 'Mn').lower()
        for entry in tree.findall(f'{{{NS_LEX}}}entry'):
            eid = entry.get('id', '')          # e.g. "H1254"
            if not eid.startswith('H'):
                continue
            snum = eid[1:]                     # "1254"
            w_el = entry.find(f'{{{NS_LEX}}}w')
            if w_el is None or not w_el.text:
                continue
            bare = _strip(w_el.text.strip())
            if bare:
                index_rows.append((bare, snum))
    else:
        print("  WARNING: HebrewStrong.xml not found — run setup.py to download it.")

    cur2.executemany("INSERT INTO heb_lemma_index(lemma_bare, strong_num) VALUES(?,?)", index_rows)
    con.commit()
    con.close()
    print(f"  Hebrew lemma index: {len(index_rows):,} entries")
    print(f"\nCorpus built: {len(rows):,} words -> {db_path}")

if __name__ == '__main__':
    build()
