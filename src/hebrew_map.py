"""
Loads OSHB XML files and translates their morphology codes into
BibleWorks-style Hebrew codes from Morphology_Scheme.docx.

OSHB morph format: H<type><fields>  e.g. HVqp3ms  HNcmpa  HR/Ncfsa
  H = Hebrew language prefix
  type chars: V=verb N=noun P=pronoun A=adjective D=adverb T=particle
              C=conjunction R=relative M=number K=preposition (etc.)
  Verb fields: stem(q/N/P/h/H/D/v/V/t/T/...) aspect(p/i/c/h/a/r/s/...)
               person(1/2/3) gender(m/f/b) number(s/p/d)
  Noun fields: gender(m/f/b/c) number(s/p/d) state(a/c/d)

BW Hebrew scheme from doc: pos fields + Rq/Rk/Rx suffix (Qere/Ketiv)
We default to Rq (Qere) for all words since OSHB uses final text.
"""

import re
from xml.etree import ElementTree as ET
from pathlib import Path

# OSHB Book names in canonical order with BW book numbers
OSHB_BOOKS = [
    ('Gen',1),('Exod',2),('Lev',3),('Num',4),('Deut',5),('Josh',6),('Judg',7),
    ('Ruth',8),('1Sam',9),('2Sam',10),('1Kgs',11),('2Kgs',12),('1Chr',13),('2Chr',14),
    ('Ezra',15),('Neh',16),('Esth',17),('Job',18),('Ps',19),('Prov',20),('Eccl',21),
    ('Song',22),('Isa',23),('Jer',24),('Lam',25),('Ezek',26),('Dan',27),('Hos',28),
    ('Joel',29),('Amos',30),('Obad',31),('Jonah',32),('Mic',33),('Nah',34),('Hab',35),
    ('Zeph',36),('Hag',37),('Zech',38),('Mal',39),
]
BOOK_NUM = {b:n for b,n in OSHB_BOOKS}

NS = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}

# OSHB stem -> BW stem code
OSHB_STEM_BW = {
    'q':'q','N':'N','P':'p','h':'h','H':'H','D':'d','v':'v','V':'V',
    't':'t','T':'T','i':'i','j':'j','u':'u','c':'c','f':'f','F':'F',
    'e':'e','E':'E','o':'o','n':'n','m':'m','M':'M','k':'k','K':'K',
    'r':'r','s':'s','p':'P',  # p=piel fallback
}

# OSHB aspect/tense -> BW tense  
OSHB_TENSE_BW = {
    'p':'p',   # perfect
    'i':'i',   # imperfect
    'c':'v',   # wayyiqtol (vav-consec-impf) -> BW 'v'
    'h':'c',   # cohortative -> BW 'c'
    'j':'j',   # jussive
    'v':'w',   # vav-consec-perfect -> BW 'w'
    'a':'a',   # imperative
    'r':'r',   # participle active
    's':'s',   # participle passive
    'f':'f',   # infinitive absolute
    'c2':'e',  # infinitive construct -> BW 'e'
    'e':'e',   # infinitive construct alt
}

def oshb_to_bw(morph: str) -> str:
    """Convert an OSHB morph code to a BibleWorks-style Hebrew code."""
    if not morph:
        return 'x???Rx'
    # Strip H prefix; handle compound words with '/' by taking the final segment
    parts = morph.split('/')
    m = parts[-1]  # use the last morphological segment (head word)
    if m.startswith('H'):
        m = m[1:]
    if not m:
        return 'x???Rx'

    c = m[0]  # primary POS code
    rest = m[1:]

    if c == 'V':  # verb
        # rest = stem(1) aspect(1) person(1) gender(1) number(1) [state(1)]
        stem   = OSHB_STEM_BW.get(rest[0:1], '?') if len(rest)>0 else '?'
        tense  = OSHB_TENSE_BW.get(rest[1:2], '?') if len(rest)>1 else '?'
        person = rest[2:3] if len(rest)>2 else '?'
        gender = rest[3:4] if len(rest)>3 else '?'
        number = rest[4:5] if len(rest)>4 else '?'
        return f"v{stem}{tense}{person}{gender}{number}Rq"

    if c == 'N':  # noun  (type, gender, number, state)
        ntype  = rest[0:1] if len(rest)>0 else '?'  # c=common, p=proper
        gender = rest[1:2] if len(rest)>1 else '?'
        number = rest[2:3] if len(rest)>2 else '?'
        state  = rest[3:4] if len(rest)>3 else '?'  # a=abs, c=const, d=det
        return f"n{ntype}{gender}{number}{state}Rq"

    if c == 'A':  # adjective
        gender = rest[1:2] if len(rest)>1 else '?'
        number = rest[2:3] if len(rest)>2 else '?'
        state  = rest[3:4] if len(rest)>3 else '?'
        return f"a?{gender}{number}{state}Rq"

    if c == 'P':  # pronoun
        ptype  = rest[0:1] if len(rest)>0 else '?'
        gender = rest[1:2] if len(rest)>1 else '?'
        number = rest[2:3] if len(rest)>2 else '?'
        return f"p{ptype}{gender}{number}Rq"

    if c == 'R':  # relative particle / conjunction
        return f"r????Rq"

    if c in ('C','c'):  # conjunction
        return f"c????Rq"

    if c in ('T','K','D','M','S','k'):  # particle/preposition/adverb/number/suffix
        type_map = {'T':'t','K':'k','D':'d','M':'m','S':'s','k':'k'}
        return f"{type_map.get(c,'x')}????Rq"

    return f"x????Rq"


def strip_niqqud(s: str) -> str:
    """Remove Hebrew vowel points and cantillation marks for bare consonant matching."""
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) not in ('Mn',) or ord(c) < 0x0591)


def load_oshb_book(xml_path: str, book_num: int) -> list:
    """Parse one OSHB XML book file; return list of word dicts."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    words = []
    for verse in root.iter('{http://www.bibletechnologies.net/2003/OSIS/namespace}verse'):
        osisID = verse.get('osisID', '')
        parts = osisID.split('.')
        if len(parts) < 3:
            continue
        ch, vs = int(parts[1]), int(parts[2])
        pos = 0
        for w in verse.iter('{http://www.bibletechnologies.net/2003/OSIS/namespace}w'):
            morph = w.get('morph', '')
            lemma_raw = w.get('lemma', '')
            # lemma may have slash-prefixed items; take last Strong number
            lemma = lemma_raw.split('/')[-1].strip() if lemma_raw else ''
            surface = (w.text or '').strip().replace('/', '')
            if not surface:
                continue
            bw_code = oshb_to_bw(morph)
            words.append({
                'lang': 'heb',
                'book': book_num, 'chapter': ch, 'verse': vs, 'pos': pos,
                'surface': surface,
                'surface_bare': strip_niqqud(surface),
                'lemma': lemma,
                'bw_code': bw_code,
                'morph_raw': morph,
            })
            pos += 1
    return words


if __name__ == '__main__':
    words = load_oshb_book('/home/claude/bw/data/heb/Gen.xml', 1)
    print(f"Genesis: {len(words)} words")
    for w in words[:8]:
        print(f"  {w['chapter']}:{w['verse']} {w['surface']:20} lemma={w['lemma']:8} code={w['bw_code']}")
