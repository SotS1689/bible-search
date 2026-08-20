"""
A small parser + evaluator for the BibleWorks-style Command Line grammar
(subset: AND '.', phrase ''', OR '/', NOT '!', proximity ';N', compound '(...)',
wildcards * and ?, and morphological lemma@code matching).

Design: parse into an AST of Term / Phrase / And / Or / Not / Proximity nodes,
then evaluate against an in-memory corpus of tagged words (list of dicts with
book/chapter/verse/surface/lemma/bw_code, in document order).
"""
import re
from dataclasses import dataclass, field
from typing import List


# ---------- Wildcard matching ----------

def wildcard_to_regex(pattern: str) -> re.Pattern:
    # '*' -> any sequence, '?' -> any single char. Case-insensitive for text;
    # morph-code matching is handled separately (case sensitive).
    esc = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
    return re.compile(f'^{esc}$', re.IGNORECASE)


def morph_code_matches(query_code: str, actual_code: str) -> bool:
    """
    query_code may contain '*', '?' wildcards and the grouping operators
    '(' ')' '|' for OR-ing sub-patterns, e.g. '((n-)|(ap))*'
    """
    # Expand '(A|B)' groups into a regex alternation directly.
    # Convert to a regex: outside-of-group '*'/'?' become wildcards,
    # parentheses/| pass through as regex groups (already valid regex syntax).
    out = []
    i = 0
    while i < len(query_code):
        c = query_code[i]
        if c == '*':
            out.append('.*')
        elif c == '?':
            out.append('.')
        elif c in '()|':
            out.append(c)
        else:
            out.append(re.escape(c))
        i += 1
    pattern = '^' + ''.join(out) + '$'
    return re.match(pattern, actual_code, re.IGNORECASE) is not None


# ---------- AST ----------

@dataclass
class Word:
    """A single search term: plain text, or lemma@morphcode for morph versions."""
    raw: str

    def lemma_and_code(self):
        if '@' in self.raw:
            lemma, code = self.raw.split('@', 1)
            return lemma, code
        return self.raw, None


@dataclass
class Phrase:
    words: List[Word]
    max_gap: int = 0  # '*N' between words allows up to N intervening words; 0 = exact phrase


@dataclass
class And:
    positive: List  # terms required present
    negative: List  # terms required absent ('!')
    proximity: int = None  # ';N' verse window; None = same verse


@dataclass
class Or:
    options: List


@dataclass
class Not:
    inner: object


# ---------- Tokenizing / parsing the command line ----------
# Supported subset for this prototype:
#   .term1 term2!term3;N      (AND, with NOT and proximity)
#   /term1 term2              (OR)
#   'term1 term2 *N term3     (PHRASE, with gap)
#   (subexpr).(subexpr)       (compound AND of two parenthesized groups)
#   (subexpr)/(subexpr)       (compound OR)
#   (subexpr).!(subexpr)      (compound AND-NOT)

def parse(cmdline: str):
    cmdline = cmdline.strip()
    if cmdline.startswith('('):
        return _parse_compound(cmdline)
    if cmdline.startswith('.'):
        return _parse_and(cmdline[1:])
    if cmdline.startswith('/'):
        return _parse_or(cmdline[1:])
    if cmdline.startswith("'"):
        return _parse_phrase(cmdline[1:])
    raise ValueError(f"Unrecognized command line start: {cmdline!r}")


def _split_top_level(s: str, sep_chars: str):
    """Split on sep_chars, but not inside parentheses."""
    parts, depth, cur = [], 0, ''
    for c in s:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        if c in sep_chars and depth == 0:
            parts.append(cur); cur = ''
        else:
            cur += c
    parts.append(cur)
    return parts


def _parse_and(s: str) -> And:
    prox = None
    if ';' in s:
        s, prox_str = s.rsplit(';', 1)
        prox = int(prox_str)
    tokens = s.split()
    pos, neg = [], []
    for t in tokens:
        if t.startswith('!'):
            neg.append(Word(t[1:]))
        else:
            pos.append(Word(t))
    return And(pos, neg, prox)


def _parse_or(s: str) -> Or:
    return Or([Word(t) for t in s.split()])


def _parse_phrase(s: str) -> Phrase:
    tokens = s.split()
    words, gap = [], 0
    i = 0
    while i < len(tokens):
        t = tokens[i]
        m = re.match(r'^\*(\d*)$', t)
        if m:
            gap = int(m.group(1)) if m.group(1) else 99999  # bare '*' = any number of words
        else:
            words.append(Word(t))
        i += 1
    return Phrase(words, gap)


def _parse_compound(s: str):
    # find matching close-paren for the first group
    depth = 0
    for i, c in enumerate(s):
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                first = s[1:i]
                rest = s[i+1:]
                break
    else:
        raise ValueError("Unbalanced parentheses")
    left = parse_subexpr(first)
    if not rest:
        return left
    if rest.startswith('.!'):
        frag = rest[2:]
        if frag.startswith('(') and frag.endswith(')'):
            frag = frag[1:-1]
        right = parse_subexpr(frag)
        return And([left], [right])
    if rest.startswith('.'):
        right_str = rest[1:]
        right = parse_subexpr(right_str)
        return And([left, right], [])
    if rest.startswith('/'):
        right = parse_subexpr(rest[1:])
        return Or([left, right])
    if rest[0].isdigit() or rest.startswith('.') is False:
        # proximity form like (...)N(...)
        m = re.match(r'^(\d+)', rest)
        if m:
            n = int(m.group(1))
            right = parse_subexpr(rest[m.end():])
            return And([left, right], [], proximity=n)
    raise ValueError(f"Unsupported compound continuation: {rest!r}")


def parse_subexpr(s: str):
    """Parse a fragment that may itself start with ( . / ' or be bare (treated as AND term list)."""
    s = s.strip()
    if s.startswith('('):
        return _parse_compound(s)
    if s.startswith('.'):
        return _parse_and(s[1:])
    if s.startswith('/'):
        return _parse_or(s[1:])
    if s.startswith("'"):
        return _parse_phrase(s[1:])
    # bare term list inside parens (e.g. 'barnabas' in (barnabaj))
    return _parse_and('.' + s if not s.startswith('.') else s)
