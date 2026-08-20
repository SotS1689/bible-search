"""
BibleWorks-style Greek keyboard transliteration: maps Latin-keyboard input
(as used in the Command Line examples: 'cristoj', 'pisteuw', 'ihsouj')
to lowercase, unaccented Greek text, for comparison against corpus lemmas
(which are accented Unicode Greek) normalized the same way.

Standard BW/Perseus-style mapping. Final sigma 'j' renders as plain sigma
since we compare in unaccented/unfinaled form.
"""
import unicodedata

LATIN_TO_GREEK = {
    'a': 'α', 'b': 'β', 'g': 'γ', 'd': 'δ', 'e': 'ε', 'z': 'ζ', 'h': 'η',
    'q': 'θ', 'i': 'ι', 'k': 'κ', 'l': 'λ', 'm': 'μ', 'n': 'ν', 'x': 'ξ',
    'o': 'ο', 'p': 'π', 'r': 'ρ', 's': 'σ', 't': 'τ', 'u': 'υ', 'f': 'φ',
    'c': 'χ', 'y': 'ψ', 'w': 'ω', 'j': 'σ',  # j = final sigma -> normalize to sigma
}


def translit_query_to_greek(s: str) -> str:
    """Convert a BW-keyboard Latin string to plain lowercase Greek (no accents)."""
    out = []
    for ch in s:
        out.append(LATIN_TO_GREEK.get(ch.lower(), ch))
    return ''.join(out)


def strip_accents_lower(greek: str) -> str:
    """Normalize accented Unicode Greek to bare lowercase letters (NFD strip combining marks),
    and fold final sigma 'ς' to 'σ' so forms compare equal regardless of position."""
    nfkd = unicodedata.normalize('NFD', greek)
    bare = ''.join(c for c in nfkd if not unicodedata.combining(c))
    bare = bare.lower().replace('ς', 'σ')
    return bare


if __name__ == '__main__':
    print(translit_query_to_greek('cristoj'), '==', strip_accents_lower('Χριστός'))
    print(translit_query_to_greek('ihsouj'), '==', strip_accents_lower('Ἰησοῦς'))
