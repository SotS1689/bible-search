"""
Beta Code -> Unicode Greek decoder for CCAT/CATSS/TLG-style materials,
per the coding table in 00.betacode.txt.

Rules:
  - Base letters A-Z (case-insensitive on input; CATSS files use uppercase
    throughout) map to lowercase Greek letters. 'J' is final sigma.
  - Diacritics are POSTFIX: they immediately follow the base letter they
    modify, and may stack (e.g. A)RXH=| -> alpha, then rho-chi-eta with
    rough... actually smooth breathing, circumflex, iota subscript).
  - A leading '*' capitalizes the *next* letter (proper nouns/sentence-
    initial forms), e.g. *IAKWB -> Ἰακώβ.
  - '+' is diaeresis, "'" (apostrophe) is elision and passes through as-is.

Output is NFC-normalized precomposed Unicode, matching the format already
used by the MorphGNT-derived Greek text in this corpus.
"""
import unicodedata

BASE = {
    'A': 'α', 'B': 'β', 'G': 'γ', 'D': 'δ', 'E': 'ε', 'Z': 'ζ', 'H': 'η',
    'Q': 'θ', 'I': 'ι', 'K': 'κ', 'L': 'λ', 'M': 'μ', 'N': 'ν', 'C': 'ξ',
    'O': 'ο', 'P': 'π', 'R': 'ρ', 'S': 'σ', 'T': 'τ', 'U': 'υ', 'F': 'φ',
    'X': 'χ', 'Y': 'ψ', 'W': 'ω', 'J': 'ς',   # J = final sigma
    'V': 'ϝ',                                  # digamma (rare)
}

# Postfix diacritic marks -> combining Unicode codepoints.
# Order of application doesn't matter; NFC normalization reorders correctly.
DIACRITICS = {
    ')': '\u0313',  # smooth breathing (psili)
    '(': '\u0314',  # rough breathing (dasia)
    '/': '\u0301',  # acute
    '\\': '\u0300', # grave
    '=': '\u0342',  # circumflex (perispomeni)
    '|': '\u0345',  # iota subscript (ypogegrammeni)
    '+': '\u0308',  # diaeresis
}

UPPER_BASE = {k: v.upper() for k, v in BASE.items()}

# Canonical emission order for stacked diacritics (Unicode's own decomposition
# order for precomposed Greek characters puts breathing before diaeresis
# before accent; iota subscript always sorts last via its own combining
# class, so order doesn't matter for it, but we place it last anyway).
_MARK_PRIORITY = {')': 0, '(': 0, '+': 1, '/': 2, '\\': 2, '=': 2, '|': 3}


def _flush(out, letter, marks):
    marks_sorted = sorted(marks, key=lambda c: _MARK_PRIORITY.get(c, 9))
    out.append(letter + ''.join(DIACRITICS[c] for c in marks_sorted))


def betacode_to_unicode(s: str) -> str:
    """Decode one Beta-Code token (e.g. a single word) to Unicode Greek."""
    out = []
    capitalize_next = False
    cur_letter = None
    cur_marks = []

    def close_pending():
        if cur_letter is not None:
            _flush(out, cur_letter, cur_marks)

    for ch in s:
        if ch == '*':
            capitalize_next = True
            continue
        if ch in DIACRITICS:
            if cur_letter is not None:
                cur_marks.append(ch)
            continue
        if ch.upper() in BASE:
            close_pending()
            cur_letter = UPPER_BASE[ch.upper()] if capitalize_next else BASE[ch.upper()]
            cur_marks = []
            capitalize_next = False
            continue
        # Anything else (elision apostrophe, punctuation, digits, spaces)
        close_pending()
        cur_letter = None
        cur_marks = []
        out.append(ch)

    close_pending()

    # Resolve final sigma: a plain medial sigma at the very end of the
    # token (this dataset uses 'S' for both medial and final sigma) is
    # rendered as the final form.
    if out and out[-1] and out[-1][0] == '\u03c3':
        out[-1] = '\u03c2' + out[-1][1:]

    return unicodedata.normalize('NFC', ''.join(out))


if __name__ == '__main__':
    tests = [
        ("E)N", "ἐν"),
        ("A)RXH=|", "ἀρχῇ"),
        ("E)POI/HSEN", "ἐποίησεν"),
        ("QEO\\S", "θεὸς"),       # grave accent (pre-positive word form), final sigma
        ("*I)AKW/B", "Ἰακώβ"),   # lemma form carries the diacritics
        ("*IAKWB", "Ιακωβ"),     # inflected surface form here has none
        ("A)LL'", "ἀλλ'"),
        ("PRWI/+", "πρωΐ"),      # diaeresis + acute, order-independent
    ]
    for beta, expected in tests:
        got = betacode_to_unicode(beta)
        ok = "OK " if got == expected else "!! "
        print(f"{ok}{beta:15} -> {got:12} (expected {expected})")
