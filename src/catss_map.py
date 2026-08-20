"""
Loads CATSS/Packard-tagged .mlxx LXX files (beta code + morph analysis)
and translates them into the same BibleWorks-style bw_code scheme already
used for the MorphGNT-derived NT data (see greek_map.py), so morphology
search (@code) works identically across NT and LXX.

.mlxx line format (whitespace-separated):
    <verse header lines>:  "Gen 1:1"
    <word lines>:          surface  TYPE  [PARSE]  lemma  [prefix...]

TYPE is a 1-3 char part-of-speech/declension-class code (e.g. N1, N3E, VAI,
RA, A1B). PARSE is present only for inflected forms (N/R/A/V) and absent
for indeclinables (C/X/I/M/P/D), in which case the token right after TYPE
is the lemma.

PARSE field order (per #Morph-Coding.txt):
    Nouns/pronouns/proper-nouns (3 cols): case, number, gender
    Adjectives   (up to 4 cols): case, number, gender, [degree]
    Verbs, finite (up to 5 cols): tense, voice, mood, person, number
    Verbs, participle (6 cols):  tense, voice, mood(=P), case, number, gender

These single-letter codes are (almost) identical to the Robinson tags
MorphGNT uses, so we reuse greek_map's lookup tables directly.
"""
import re, os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)

from greek_map import CASE, GENDER, TENSE, VOICE, MOOD, PERSON, DEGREE, _f
from lxx_betacode import betacode_to_unicode

# CATSS parse strings can carry Dual number ('D'), which MorphGNT's NUMBER
# table doesn't need. Extend locally rather than mutate the shared dict.
NUMBER = {'S': 's', 'P': 'p', 'D': 'd'}

INDECLINABLE_TYPES = {'C', 'X', 'I', 'M', 'P', 'D'}
INFLECTED_TYPES    = {'N', 'R', 'A', 'V'}


def catss_to_bw(type_code: str, parse: str) -> str:
    """Convert a CATSS TYPE+PARSE pair to a BW-style code string
    (no lemma/@ prefix -- caller adds that)."""
    t = (type_code or '').strip()
    p = (parse or '').strip()
    base = t[0] if t else '?'

    if base == 'N':  # noun (incl. bare 'N' = indeclinable proper noun)
        case, number, gender = (p + '???')[:3]
        return f"n{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}?"

    if base == 'R':  # pronoun / article
        two = t[:2]
        if two == 'RA':
            case, number, gender = (p + '???')[:3]
            return f"d{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}?"
        type_map = {'RP': 'p', 'RR': 'r', 'RD': 'd', 'RI': 'i', 'RX': 'x'}
        case, number, gender = (p + '???')[:3]
        return f"r{type_map.get(two, '?')}{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}"

    if base == 'A':  # adjective
        case, number, gender, degree = (p + '????')[:4]
        return f"an{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}{_f(DEGREE, degree, 'n')}"

    if base == 'V':  # verb
        if len(p) >= 3 and p[2] == 'P':  # mood=P -> participle, declines like adj
            tense, voice, mood = p[0], p[1], p[2]
            case, number, gender = (p[3:] + '???')[:3]
            return f"vp{_f(TENSE, tense)}{_f(VOICE, voice)}{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}"
        if len(p) >= 3 and p[2] == 'N':  # mood=N -> infinitive
            tense, voice = p[0], p[1]
            return f"vn{_f(TENSE, tense)}{_f(VOICE, voice)}???"
        tense, voice, mood, person, number = (p + '?????')[:5]
        return f"v{_f(MOOD, mood)}{_f(TENSE, tense)}{_f(VOICE, voice)}{_f(PERSON, person)}{_f(NUMBER, number)}"

    if base == 'C': return "c????"
    if base == 'X': return "x????"
    if base == 'D': return "b????"   # adverb (Packard 'D'); matches MorphGNT's 'b' output
    if base == 'I': return "i????"
    if base == 'P': return f"p{_f(CASE, p[0:1] if p else '-')}???"
    if base == 'M': return "m????"
    return "z????"  # unknown / unhandled


VERSE_RE       = re.compile(r'^(.+?)\s+(\d+):(\d+)\.?$')
VERSE_RE_NOCHP = re.compile(r'^(.+?)\s+(\d+)\.?$')  # 'Label V' -> chapter 1, verse V


def load_mlxx(path, book_num, edition=None):
    """Parse one .mlxx file. Returns list of word dicts:
    {book, chapter, verse, pos, surface, lemma, bw_code, edition}
    `pos` is assigned sequentially per call; caller should offset it
    if concatenating multiple files/editions into one book."""
    out = []
    chapter = verse = None
    pos_ctr = 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.rstrip('\n\r')
            if not line.strip():
                continue
            stripped = line.strip()
            m = VERSE_RE.match(stripped)
            if m:
                chapter, verse = int(m.group(2)), int(m.group(3))
                continue
            m2 = VERSE_RE_NOCHP.match(stripped)
            if m2:
                chapter, verse = 1, int(m2.group(2))
                continue
            if chapter is None:
                continue  # skip anything before the first verse header
            tokens = line.split()
            if len(tokens) < 3:
                continue
            surface_bc, type_code = tokens[0], tokens[1]
            base = type_code[0] if type_code else '?'
            if base in INDECLINABLE_TYPES:
                parse_code = ''
                lemma_bc = tokens[2]
            else:
                if len(tokens) < 4:
                    continue
                parse_code = tokens[2]
                lemma_bc = tokens[3]
            # remaining tokens (compound-verb prefixes) are ignored for now

            surface = betacode_to_unicode(surface_bc)
            lemma   = betacode_to_unicode(lemma_bc)
            bw_code = catss_to_bw(type_code, parse_code)

            out.append({
                'book': book_num, 'chapter': chapter, 'verse': verse,
                'pos': pos_ctr, 'surface': surface, 'lemma': lemma,
                'bw_code': bw_code, 'edition': edition,
            })
            pos_ctr += 1
    return out


if __name__ == '__main__':
    words = load_mlxx('/home/claude/bw/data/lxx/01.Gen.1.mlxx', book_num=1)
    print(f"{len(words)} words loaded")
    for w in words[:11]:
        print(f"  {w['chapter']}:{w['verse']:<3} {w['surface']:12} {w['lemma']:12} {w['bw_code']}")
