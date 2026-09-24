"""
English link-stemming table for the BLB vocabulary, built only from
redistributable sources:
  * AGID rev 4 (Copyright 2000-2003 Kevin Atkinson; permissive license) -- inflections
  * Open English WordNet 2025 (CC-BY 4.0) -- derivation / pertainym links
  * hand-written English grammar: closed-class table, affix and compound rules,
    irregular derivational families (families.txt), never-link pairs (never.txt)
Output: links.tsv  (word \t head1,head2,...)   and rules.json (audit trail)

usage: python build_links.py <data folder> [fix1,fix2,...|all|none]
"""
import re, sys, sqlite3, collections, json, os, xml.etree.ElementTree as ET
from functools import lru_cache

HERE = sys.argv[1] if len(sys.argv) > 1 else '.'
# 'splitcompounds' is off by default: the user chose not to link compound words
# (housetop, herdsman, grandson...) to their parts.
ALL_FIXES = {'proper', 'homograph', 'agidquirk', 'compound2', 'prefix2', 'suffix2',
             'gentilic', 'families', 'never'}
arg = sys.argv[2] if len(sys.argv) > 2 else 'all'
FIX = ALL_FIXES if arg == 'all' else set() if arg == 'none' else set(arg.split(','))
if len(sys.argv) > 3 and sys.argv[3] == 'splitcompounds':
    FIX.add('splitcompounds')
SPLIT = 'splitcompounds' in FIX

# ---------- vocabulary ----------
con = sqlite3.connect(f'{HERE}/c.db')
freq, capcount = collections.Counter(), collections.Counter()
TOK = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
for (t,) in con.execute("select text from translations where version='BLB'"):
    for m in TOK.finditer(t):
        w = m.group().replace('’', "'")
        lw = w.lower()
        freq[lw] += 1
        if w[0].isupper():
            capcount[lw] += 1
V = set(freq)

# ---------- AGID ----------
infl = collections.defaultdict(set)      # form -> {base}
agid_bases, agid_common = set(), set()   # headwords / headwords written lowercase
agid_entries = []
agid_verbs = set()
for ln in open(f'{HERE}/agid-4/infl.txt', encoding='latin-1'):
    head, rest = ln.rstrip('\n').split(': ', 1)
    base, pos = head.rsplit(' ', 1)
    if not pos.endswith('?'):
        agid_bases.add(base.lower())
        if base.islower():
            agid_common.add(base)
    agid_entries.append((base.lower(), pos, rest))
    if pos == 'V':
        agid_verbs.add(base.lower())
for base, pos, rest in agid_entries:
    for group in rest.split(' | '):
        for entry in group.split(', '):
            entry = re.sub(r'\s*\{.*?\}', '', entry).strip()
            form = entry.split(' ')[0]
            if '~' in form or '!' in form:
                continue
            form = form.rstrip('<?').lower()
            if form == base or len(base) <= 1:
                continue
            # AGID guesses comparatives/forms that are really separate words:
            # priest < prey, number < numb, liver < live, muster < must
            if 'agidquirk' in FIX and form in agid_bases and (pos[0] == 'A' or pos.endswith('?')):
                continue
            infl[form].add(base)

# ---------- WordNet ----------
wn_lemmas, wn_common = set(), set()
wn_links = collections.defaultdict(set)
wn_forms = collections.defaultdict(set)
sense_lemma, rels = {}, []
for ev, el in ET.iterparse(f'{HERE}/oewn.xml'):
    if el.tag == 'LexicalEntry':
        raw = el.find('Lemma').get('writtenForm')
        lem = raw.lower()
        if re.fullmatch(r"[a-z']+", lem):
            wn_lemmas.add(lem)
            if raw.islower():
                wn_common.add(lem)
            for f in el.findall('Form'):
                wn_forms[f.get('writtenForm').lower()].add(lem)
            for s in el.findall('Sense'):
                sense_lemma[s.get('id')] = lem
                for r in s.findall('SenseRelation'):
                    if r.get('relType') in ('derivation', 'pertainym', 'participle'):
                        rels.append((s.get('id'), r.get('target')))
        el.clear()
for a, b in rels:
    la, lb = sense_lemma.get(a), sense_lemma.get(b)
    if la and lb and la != lb:
        wn_links[la].add(lb)

def is_proper(w):
    return ('proper' in FIX and freq[w] and capcount[w] / freq[w] >= 0.9
            and w not in agid_common and w not in wn_common)

def common_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y: break
        n += 1
    return n

# ---------- hand-maintained lists ----------
def read_pairs(name):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    rows = []
    if os.path.exists(p):
        for ln in open(p, encoding='utf-8'):
            ln = ln.split('#', 1)[0].strip()
            if ln:
                rows.append(ln.split())
    return rows

NEVER = {frozenset(r[:2]) for r in read_pairs('never.txt')} if 'never' in FIX else set()
PREFIX_OK = {r[0] for r in read_pairs('prefixed.txt')} if 'prefix2' in FIX else set()
FAMILY = {}   # word -> family head
if 'families' in FIX:
    for row in read_pairs('families.txt'):
        for w in row:
            FAMILY[w] = row[0]

# ---------- affix rules ----------
SUFFIXES = [  # (suffix, replacements to try on the stem)
    ('lessness', ['']), ('fulness', ['', 'y:i']), ('fullness', ['']), ('iness', ['y']),
    ('ness', ['']), ('lessly', ['']), ('less', ['', 'y:i']), ('fully', ['']), ('ful', ['', 'y:i']),
    ('hood', ['']), ('ship', ['']), ('dom', ['']),
    *([('kind', [''])] if SPLIT else []), ('soever', ['']), ('eous', ['']), ('ous', ['', 'e']),
    ('ment', ['']), ('ments', ['']), ('ance', ['', 'e']),
    ('ation', ['e', '']), ('ition', ['']), ('ive', ['e', '']),
    ('able', ['', 'e']), ('ible', ['']), ('ward', ['']), ('wards', ['']),
    ('ess', ['']), ('esses', ['']),
    ('ite', ['']), ('ites', ['']), ('ian', ['', 'e']), ('ians', ['', 'e']), ('ity', ['', 'e']),
]
SUFFIXES2 = [  # added by 'suffix2'; stems must be >= 4 letters
    ('er', ['e', '', 'dup']), ('ers', ['e', '', 'dup']), ('en', ['', 'e']), ('ern', ['']),
    ('ly', ['', 'le']), ('ling', ['']), ('lings', ['']), ('itess', ['']),
    *([('man', ['', 's:']), ('men', ['', 's:']), ('smith', ['']), ('smiths', [''])] if SPLIT else []),
]
PREFIXES = ['un', 'non']
PREFIXES2 = ['grand', 'arch'] if SPLIT else []
PREFIX_ANY = ['fore', 'be', 'a', 'en', 'em', 're', 'dis', 'mis', 'im', 'in', 'out', 'over',
              'under', 'up', 'sur', 'with']   # only for words listed in prefixed.txt
GENTILIC = ('itess', 'ites', 'ite', 'ians', 'ian', 'itical', 'ical', 'ic')

AFFIX_HIT = {}
ORDINALS = {  # ordinal -> cardinal
    'third': 'three', 'fourth': 'four', 'fifth': 'five', 'sixth': 'six', 'seventh': 'seven',
    'eighth': 'eight', 'ninth': 'nine', 'tenth': 'ten', 'twelfth': 'twelve',
    'hundredth': 'hundred', 'thousandth': 'thousand', 'twentieth': 'twenty',
    'thirtieth': 'thirty', 'fortieth': 'forty', 'fiftieth': 'fifty'}

def ok_link(w, stem):
    """Guards shared by every rule."""
    if frozenset((w, stem)) in NEVER:
        return False
    if 'proper' in FIX and is_proper(stem) != is_proper(w) and        not w.endswith(('ian', 'ians', 'ite', 'ites', 'itess')):
        return False            # Sinite !-> sin, Midian !-> mid
    return True

def lookup_stem(stem, reps, w):
    for r in reps:
        if r == 'y:i':
            cand = stem[:-1] + 'y' if stem.endswith('i') else None
        elif r == 'dup':            # sinner -> sin
            cand = stem[:-1] if len(stem) > 2 and stem[-1] == stem[-2] else None
        elif r == 's:':             # herdsman -> herd
            cand = stem[:-1] if stem.endswith('s') else None
        else:
            cand = stem + r
        if cand and cand != w and (cand in V or cand in agid_bases and cand in wn_common) \
           and ok_link(w, cand):
            return cand
    return None

def affix_stems(w):
    out = set()
    proper = is_proper(w)
    rules = [] if proper else list(SUFFIXES)
    if proper:
        rules = [s for s in SUFFIXES if s[0] in ('ite', 'ites', 'ian', 'ians', 'ess', 'esses')]
    if 'suffix2' in FIX:
        rules += [s for s in SUFFIXES2 if not proper or s[0] == 'itess']
    for suf, reps in rules:
        minstem = 4 if (suf, reps) in SUFFIXES2 else 3
        if w.endswith(suf) and len(w) - len(suf) >= minstem - (1 if 'dup' in reps else 0):
            cand = lookup_stem(w[:-len(suf)], reps, w)
            if cand and suf in ('er', 'ers') and cand not in agid_verbs:
                cand = None          # agent nouns only: sinner < sin, not mother < moth
            if cand and (len(cand) >= minstem or suf in ('er', 'ers')):
                out.add(cand)
                AFFIX_HIT[(w, cand)] = '-' + suf
    if not proper:
        prefixes = PREFIXES + (PREFIXES2 if 'prefix2' in FIX else []) +                    (PREFIX_ANY if w in PREFIX_OK else [])
        for p in prefixes:
            rest = w[len(p):]
            minrest = 4 if p in PREFIXES else 3
            if w.startswith(p) and len(rest) >= minrest and rest in V and ok_link(w, rest) \
               and (p in PREFIXES or freq[rest] >= 2):
                out.add(rest)
                AFFIX_HIT[(w, rest)] = p + '-'
    if 'gentilic' in FIX and proper:
        # Levites -> Levi, Benjamite -> Benjamin, Manassite -> Manasseh, Assyrian -> Assyria
        for suf in GENTILIC:
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                stem = w[:-len(suf)]
                best = None
                for c in V:
                    if c == w or not is_proper(c) or c.endswith(GENTILIC):
                        continue
                    cp = common_prefix(c, stem)
                    if cp >= max(3, len(stem) - 1) and len(c) - cp <= 2:
                        key = (cp, -abs(len(c) - len(stem)), freq[c])
                        if best is None or key > best[0]:
                            best = (key, c)
                if best:
                    out.add(best[1])
                    AFFIX_HIT[(w, best[1])] = 'gentilic'
                    break
    return out

# ---------- compounds ----------
COMPOUND_STOP = set("""the a an for with be as is it in on at to of by he his her me my we us so or
and but all out over up that under some before after through may can will not no one man""".split())
COMPOUND_LEAD = {'where', 'there', 'here', 'no', 'any', 'some', 'every', 'ever'}
COMPOUND_LEAD2 = {'back', 'mid', 'man', 'men'}
COMPOUND_TAIL_SHORT = {'man', 'men', 'way'}

def compound_split(w):
    if not SPLIT or len(w) < 7 or is_proper(w):
        return None
    best = None
    for i in range(3, len(w) - 1):
        a, b = w[:i], w[i:]
        if a not in V or b not in V or is_proper(a) or is_proper(b):
            continue
        if 'compound2' in FIX:
            if freq[a] < 2 or freq[b] < 2 or frozenset((w, a)) in NEVER or frozenset((w, b)) in NEVER:
                continue
            if a in COMPOUND_LEAD and len(b) >= 2:
                best = (a, b)
            elif (a in COMPOUND_LEAD2 or a not in COMPOUND_STOP) and b not in COMPOUND_STOP \
                 and (len(b) >= 4 or b in COMPOUND_TAIL_SHORT or
                      (len(w) >= 7 and b in wn_common and b not in infl and b not in FUNCTION)):
                best = (a, b)
        else:
            if freq[a] >= 5 and freq[b] >= 5 and len(b) >= 2 and \
               (a in COMPOUND_LEAD or (a not in COMPOUND_STOP and b not in COMPOUND_STOP and len(b) >= 3)):
                best = (a, b)
    return best

# ---------- closed-class words (hand-written English grammar) ----------
CLOSED = {}
for head, forms in {
    'i': 'i me my mine', 'we': 'we us our ours',
    'you': 'you your yours thee thou thy thine ye',
    'he': 'he him his', 'she': 'she her hers', 'it': 'it its',
    'they': 'they them their theirs',
    'who': 'who whom whose whomever whoever whosoever',
    'this': 'this these', 'that': 'that those', 'a': 'a an',
    'no': 'no not none nor', 'to': 'to unto', 'on': 'on upon',
}.items():
    for f in forms.split():
        CLOSED[f] = {head}
for f, h in {'myself': 'i', 'ourselves': 'we', 'yourself': 'you', 'yourselves': 'you',
             'thyself': 'you', 'himself': 'he', 'herself': 'she', 'itself': 'it',
             'themselves': 'they', 'oneself': 'one'}.items():
    CLOSED[f] = {h, 'self'} if SPLIT else {h}
CLOSED.update({'onto': {'on', 'to'}, 'into': {'into'},
               'can': {'can'}, 'could': {'can'}, 'cannot': {'can'},
               'would': {'would'}, 'should': {'should'},
               'might': {'might'}, 'may': {'may'}, 'will': {'will'}, 'shall': {'shall'}})
AGID_EXCLUDE = {('might', 'may'), ('could', 'can'), ('would', 'will'), ('should', 'shall'),
                ('more', 'many'), ('most', 'many'), ('more', 'much'), ('most', 'much'),
                ('people', 'person'), ('art', 'be'), ('wast', 'be'), ('hisses', 'his'),
                ('wicked', 'wick'), ('less', 'little'), ('least', 'little'), ('lesser', 'little')}
FUNCTION = set('''out not no less but by for that as so of in at with from off should would could
shall can has ha now even many more most the and or if than then when what which how why'''.split())
RULE = {}

# ---------- head resolution ----------
def inflection_bases(w):
    bases = {b for b in set(infl.get(w, ())) | set(wn_forms.get(w, ()))
             if (w, b) not in AGID_EXCLUDE and frozenset((w, b)) not in NEVER}
    if not bases:
        return {w}
    if w in agid_bases:      # the form is also a word in its own right (saw, left, rose)
        bases.add(w)
    return bases

def follow(c, depth):
    """Heads reached from a derivational stem c."""
    bases = inflection_bases(c)
    if 'homograph' in FIX and len(bases) > 1 and c in bases:
        bases = {c}          # foundation -> found, not -> find
    res = set()
    for b in bases:
        res |= root(b, depth + 1)
    return res

@lru_cache(None)
def root(w, depth=0):
    """Reduce a base word to its derivational root(s)."""
    if w in FAMILY:
        return frozenset([FAMILY[w]])
    if depth > 4:
        return frozenset([w])
    cands = set()
    for r in wn_links.get(w, ()):
        if len(r) < len(w) and common_prefix(r, w) >= max(3, len(r) - 2) and \
           (len(r) >= 4 or w[len(r):] in ('r', 'er', 'ers', 'ing', 'ings')) and ok_link(w, r):
            cands.add(r)
    cands |= affix_stems(w)
    if w in ORDINALS:
        cands.add(ORDINALS[w])
    if not cands:
        sp = compound_split(w)
        if sp:
            RULE.setdefault(w, 'compound')
            res = set()
            for part in sp:
                res |= follow(part, depth)
            return frozenset(res)
        return frozenset([w])
    RULE.setdefault(w, 'wn' if any(c in wn_links.get(w, ()) for c in cands) else 'affix')
    res = set()
    for c in cands:
        res |= follow(c, depth)
    return frozenset(res)

def heads(w):
    if w in CLOSED:
        RULE[w] = 'closed'
        return set(CLOSED[w])
    if w.endswith("'s"):
        w = w[:-2]
    elif w.endswith("s'"):
        w = w[:-1]
    res = set()
    for b in inflection_bases(w):
        res |= root(b)
    if RULE.get(w) != 'compound':
        res = {h if h not in FUNCTION or h == w else w for h in res}
    return res

CREDITS = """\
# English link-stemming table for BibleSearch (word<TAB>link heads).
# Built with tools/eng_links/build_links.py from:
#  - AGID (Automatically Generated Inflection Database), Rev. 4.
#    Copyright 2000-2003 by Kevin Atkinson. Permission to use, copy, modify,
#    distribute and sell this database, the associated scripts, the output
#    created from the scripts and its documentation for any purpose is hereby
#    granted without fee, provided that the above copyright notice appears in
#    all copies. http://wordlist.aspell.net/
#  - Open English WordNet 2025, by the Open English WordNet Community,
#    CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), derived from
#    Princeton WordNet 3.0, Copyright 2006 by Princeton University.
#    https://en-word.net/
"""

if __name__ == '__main__':
    out = {w: sorted(heads(w)) for w in V}
    json.dump({'rule': RULE, 'affix': {f'{a}|{b}': s for (a, b), s in AFFIX_HIT.items()},
               'proper': sorted(w for w in V if is_proper(w))},
              open(f'{HERE}/rules.json', 'w'))
    with open(f'{HERE}/links.tsv', 'w', encoding='utf-8', newline='\n') as f:
        f.write(CREDITS)
        for w in sorted(out):
            f.write(f"{w}\t{','.join(out[w])}\n")
    print('wrote', len(out), 'words; fixes', sorted(FIX) or 'none')
