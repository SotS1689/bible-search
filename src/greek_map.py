"""
Translates MorphGNT (Robinson-tagged SBLGNT) tags into BibleWorks-style
morphology codes, per the scheme in Morphology_Scheme.docx.

MorphGNT line format:
  <ref> <POS> <8-char-parse> <text> <word> <norm> <lemma>
POS values: N- C- RA P- V- A- D- I- X- M- (etc.)
Parse fields (8 chars, Robinson order): Person Tense Voice Mood Case Number Gender Degree
"""

CASE = {'N': 'n', 'G': 'g', 'D': 'd', 'A': 'a', 'V': 'v'}
GENDER = {'M': 'm', 'F': 'f', 'N': 'n'}
NUMBER = {'S': 's', 'P': 'p'}
TENSE = {'P': 'p', 'F': 'f', 'A': 'a', 'I': 'i', 'X': 'x', 'Y': 'y', 'T': 'z'}  # T=future perfect
VOICE = {'A': 'a', 'M': 'm', 'P': 'p', 'E': 'e'}
MOOD = {'I': 'i', 'D': 'd', 'S': 's', 'O': 'o', 'N': 'n', 'P': 'p'}  # N=infinitive, P=participle
PERSON = {'1': '1', '2': '2', '3': '3'}
DEGREE = {'C': 'c', 'S': 's'}


def _f(d, c, default='?'):
    return d.get(c, default) if c != '-' else '?'


def morphgnt_to_bw(pos: str, parse: str) -> str:
    """
    Returns a BibleWorks-style code string: <pos-letter><fields...>
    (no lemma/@ prefix -- that's added by the caller).
    """
    pos = pos.strip()
    p = parse  # 8 chars: [Person][Tense][Voice][Mood][Case][Number][Gender][Degree]
    person, tense, voice, mood, case, number, gender, degree = list(p.ljust(8, '-'))

    if pos == 'N-':  # noun
        # BW noun: n <case><gender><number><type>  (type c/p not in MorphGNT -> wildcard)
        return f"n{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}?"
    if pos == 'RA':  # definite article
        return f"d{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}?"
    if pos in ('RP', 'RR', 'RD', 'RI', 'RX'):  # pronoun types
        type_map = {'RP': 'p', 'RR': 'r', 'RD': 'd', 'RI': 'i', 'RX': 'x'}
        return f"r{type_map.get(pos,'?')}{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}"
    if pos == 'A-':  # adjective
        return f"an{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}{_f(DEGREE, degree, 'n')}"
    if pos == 'C-':
        return "c????"
    if pos == 'P-':
        return f"p{_f(CASE, case)}???"
    if pos == 'D-':
        return "b????"
    if pos == 'X-':
        return "x????"
    if pos == 'I-':
        return "i????"
    if pos == 'V-':  # verb
        if mood == 'P':  # participle
            return f"vp{_f(TENSE, tense)}{_f(VOICE, voice)}{_f(CASE, case)}{_f(GENDER, gender)}{_f(NUMBER, number)}"
        if mood == 'N':  # infinitive
            return f"vn{_f(TENSE, tense)}{_f(VOICE, voice)}???"
        # finite verb: indicative/imperative/subjunctive/optative
        return f"v{_f(MOOD, mood)}{_f(TENSE, tense)}{_f(VOICE, voice)}{_f(PERSON, person)}{_f(NUMBER, number)}"
    return "z????"  # unknown lemma / unhandled POS


def load_morphgnt(path):
    """Yields dicts: {ref, bw_code, lemma, surface} per word, in document order."""
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ref, pos, parse, text, word, norm, lemma = line.split(' ')
            bw = morphgnt_to_bw(pos, parse)
            book = int(ref[:2]); chapter = int(ref[2:4]); verse = int(ref[4:6])
            out.append({
                'book': book, 'chapter': chapter, 'verse': verse,
                'surface': text, 'lemma': lemma, 'bw_code': bw,
            })
    return out


if __name__ == '__main__':
    words = load_morphgnt('/home/claude/bw/data/1thess.txt')
    for w in words[:10]:
        print(w['chapter'], w['verse'], w['surface'], '->', f"{w['lemma']}@{w['bw_code']}")
