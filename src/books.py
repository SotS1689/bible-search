"""
Book name/abbreviation resolver for the BibleWorks-style 'l' (limit) command.
Supports full names, standard abbreviations, and BibleWorks-style short codes.
Returns BW book numbers (OT 1-39, NT 40-66).
"""

# Each entry: (book_number, [list of accepted names/abbreviations], canonical_name)
# All lookups are case-insensitive.
BOOK_TABLE = [
    # ── Old Testament ──
    ( 1, ['gen','ge','genesis'],                          'Genesis'),
    ( 2, ['exod','ex','exo','exodus'],                    'Exodus'),
    ( 3, ['lev','le','lv','leviticus'],                   'Leviticus'),
    ( 4, ['num','nu','nm','numbers'],                     'Numbers'),
    ( 5, ['deut','dt','de','deu','deuteronomy'],          'Deuteronomy'),
    ( 6, ['josh','jos','jsh','joshua'],                   'Joshua'),
    ( 7, ['judg','jdg','jg','jud','judges'],              'Judges'),
    ( 8, ['ruth','ru','rth'],                             'Ruth'),
    ( 9, ['1sam','1sa','1sm','1samuel','isamuel','isam'], '1 Samuel'),
    (10, ['2sam','2sa','2sm','2samuel','iisamuel','iisam'],'2 Samuel'),
    (11, ['1kgs','1ki','1kg','1kings','ikings'],          '1 Kings'),
    (12, ['2kgs','2ki','2kg','2kings','iikings'],         '2 Kings'),
    (13, ['1chr','1ch','1chron','1chronicles','ichronicles'], '1 Chronicles'),
    (14, ['2chr','2ch','2chron','2chronicles','iichronicles'],'2 Chronicles'),
    (15, ['ezra','ezr'],                                  'Ezra'),
    (16, ['neh','ne','nehemiah'],                         'Nehemiah'),
    (17, ['esth','es','est','esther'],                    'Esther'),
    (18, ['job','jb'],                                    'Job'),
    (19, ['ps','psa','pss','psalm','psalms'],              'Psalms'),
    (20, ['prov','pr','prv','proverbs'],                  'Proverbs'),
    (21, ['eccl','ec','ecc','qoh','ecclesiastes'],        'Ecclesiastes'),
    (22, ['song','ss','sg','sos','songofsongs','canticles','songofsolomon','solomon'],'Song of Songs'),
    (23, ['isa','is','isaiah'],                           'Isaiah'),
    (24, ['jer','je','jeremiah'],                         'Jeremiah'),
    (25, ['lam','la','lamentations'],                     'Lamentations'),
    (26, ['ezek','eze','ezekiel'],                        'Ezekiel'),
    (27, ['dan','da','dn','daniel'],                      'Daniel'),
    (28, ['hos','ho','hosea'],                            'Hosea'),
    (29, ['joel','jl','joe'],                             'Joel'),
    (30, ['amos','am'],                                   'Amos'),
    (31, ['obad','ob','obadiah'],                         'Obadiah'),
    (32, ['jonah','jon','jnh'],                           'Jonah'),
    (33, ['mic','mi','micah'],                            'Micah'),
    (34, ['nah','na','nahum'],                            'Nahum'),
    (35, ['hab','hb','habakkuk'],                         'Habakkuk'),
    (36, ['zeph','zp','zep','zephaniah'],                 'Zephaniah'),
    (37, ['hag','hg','haggai'],                           'Haggai'),
    (38, ['zech','zc','zec','zechariah'],                 'Zechariah'),
    (39, ['mal','ml','malachi'],                          'Malachi'),
    # ── New Testament ──
    (40, ['matt','mt','mat','matthew'],                   'Matthew'),
    (41, ['mark','mk','mrk','mar','marc','mr','mark'],    'Mark'),
    (42, ['luke','lk','luk','lu'],                        'Luke'),
    (43, ['john','jn','joh','jhn'],                       'John'),
    (44, ['acts','ac','act'],                             'Acts'),
    (45, ['rom','ro','rm','romans'],                      'Romans'),
    (46, ['1cor','1co','1cor','1corinthians','icorinthians'], '1 Corinthians'),
    (47, ['2cor','2co','2corinthians','iicorinthians'],   '2 Corinthians'),
    (48, ['gal','ga','galatians'],                        'Galatians'),
    (49, ['eph','ephesians'],                             'Ephesians'),
    (50, ['phil','php','ph','philippians'],               'Philippians'),
    (51, ['col','colos','colossians'],                    'Colossians'),
    (52, ['1thess','1th','1thes','1thessalonians'],       '1 Thessalonians'),
    (53, ['2thess','2th','2thes','2thessalonians'],       '2 Thessalonians'),
    (54, ['1tim','1ti','1timothy'],                       '1 Timothy'),
    (55, ['2tim','2ti','2timothy'],                       '2 Timothy'),
    (56, ['titus','tit','ti'],                            'Titus'),
    (57, ['phlm','phm','philem','philemon'],              'Philemon'),
    (58, ['heb','hebrews'],                               'Hebrews'),
    (59, ['jas','jm','jam','james'],                      'James'),
    (60, ['1pet','1pe','1pt','1peter','ipeter'],          '1 Peter'),
    (61, ['2pet','2pe','2pt','2peter','iipeter'],         '2 Peter'),
    (62, ['1john','1jn','1jo','ijohn'],                   '1 John'),
    (63, ['2john','2jn','2jo','iijohn'],                  '2 John'),
    (64, ['3john','3jn','3jo','iiijohn'],                 '3 John'),
    (65, ['jude','jud','jd'],                             'Jude'),
    (66, ['rev','re','rv','revelation','apocalypse'],     'Revelation'),
    # ── LXX-only / deuterocanonical books ──
    (67, ['1esd','1esdras','iesdras'],                    '1 Esdras'),
    (68, ['2esd','2esdras','iiesdras'],                   '2 Esdras'),
    (69, ['jdt','judith'],                                'Judith'),
    (70, ['tob','tobit'],                                 'Tobit'),
    (71, ['1macc','1maccabees','imaccabees'],             '1 Maccabees'),
    (72, ['2macc','2maccabees','iimaccabees'],            '2 Maccabees'),
    (73, ['3macc','3maccabees','iiimaccabees'],           '3 Maccabees'),
    (74, ['4macc','4maccabees','ivmaccabees'],            '4 Maccabees'),
    (75, ['odes','ode'],                                  'Odes'),
    (76, ['wis','wisd','wisdom','wisdomofsolomon'],       'Wisdom of Solomon'),
    (77, ['sir','sirach','ecclesiasticus','ecclus'],      'Sirach'),
    (78, ['pssol','psalmsofsolomon'],                     'Psalms of Solomon'),
    (79, ['bar','baruch'],                                'Baruch'),
    (80, ['epjer','letterofjeremiah','epistleofjeremiah'],'Epistle of Jeremiah'),
    (81, ['sus','susanna'],                               'Susanna'),
    (82, ['bel','belandthedragon'],                       'Bel and the Dragon'),
]

# Build fast lookup dict: normalised_name -> book_number
_LOOKUP = {}
_CANONICAL = {}
for bnum, aliases, canonical in BOOK_TABLE:
    _CANONICAL[bnum] = canonical
    for a in aliases:
        _LOOKUP[a.lower().replace(' ', '').replace('.', '')] = bnum

def resolve_book(name: str) -> int | None:
    """Return book number for a name/abbreviation, or None if not found."""
    key = name.lower().replace(' ', '').replace('.', '').replace('-', '')
    return _LOOKUP.get(key)

def canonical_name(book_num: int) -> str:
    return _CANONICAL.get(book_num, str(book_num))

def book_sort_key(book_num: int) -> int:
    """Display/search-result ordering. Internal book numbers are
    1-39 = OT, 40-66 = NT, 67-82 = Apocrypha (LXX-only books), so a plain
    numeric sort puts Apocrypha after the NT. Desired display order is
    OT -> Apocrypha -> NT, so remap onto contiguous bands in that order:
      OT (1-39)         -> 1-39
      Apocrypha (67-82) -> 40-55
      NT (40-66)        -> 56-82
    """
    if book_num <= 39:
        return book_num
    if 67 <= book_num <= 82:
        return 39 + (book_num - 66)
    return 55 + (book_num - 39)

def parse_limit(limit_str: str) -> tuple[int, int] | None:
    """
    Parse a limit string like 'Rom', 'Gen-Deut', 'NT', 'OT', 'Gospels'.
    Returns (book_from, book_to) or None if unparseable.
    Supports special ranges: OT, NT, Gospels, Pentateuch, Pauline, etc.
    """
    s = limit_str.strip()

    # Special named ranges
    named = {
        'ot':         (1,  39),
        'oldtestament':(1, 39),
        'nt':         (40, 66),
        'newtestament':(40,66),
        'pentateuch': (1,   5),
        'torah':      (1,   5),
        'gospels':    (40, 43),
        'pauline':    (45, 57),
        'paulineepistle':(45,57),
        'paulineepistles':(45,57),
        'general':    (58, 65),
        'generalepistles':(58,65),
        'lxx':        (1,  39),   # LXX text of the canonical OT books
        'apocrypha':  (67, 82),
        'deuterocanon':(67,82),
    }
    key = s.lower().replace(' ','').replace('.','')
    if key in named:
        return named[key]

    # Range: Book1-Book2
    if '-' in s:
        parts = s.split('-', 1)
        b1 = resolve_book(parts[0].strip())
        b2 = resolve_book(parts[1].strip())
        if b1 and b2:
            return (min(b1, b2), max(b1, b2))
        return None

    # Single book
    b = resolve_book(s)
    if b:
        return (b, b)
    return None

if __name__ == '__main__':
    for test in ['Rom', 'Gen-Deut', 'NT', 'OT', 'Gospels', 'Pentateuch',
                 'Matthew', '1Cor', '1 Cor', 'Pauline', 'Genesis-Malachi']:
        result = parse_limit(test)
        if result:
            b1, b2 = result
            print(f'{test:25} -> {canonical_name(b1)} ({b1}) – {canonical_name(b2)} ({b2})')
        else:
            print(f'{test:25} -> NOT FOUND')
