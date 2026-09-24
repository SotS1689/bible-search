"""Benchmark links.tsv against BibleWorks' elm.txt over the BLB vocabulary.

For each BLB word q the *expansion* is every BLB word sharing at least one head
with q (what a link-stemmed search for q would match). We compare expansions,
not head spellings, since head choice is arbitrary.
"""
import sys, re, sqlite3, collections
HERE = sys.argv[1] if len(sys.argv) > 1 else '.'
SHOW = int(sys.argv[2]) if len(sys.argv) > 2 else 0

con = sqlite3.connect(f'{HERE}/c.db')
freq = collections.Counter()
TOK = re.compile(r"[A-Za-z]+(?:['\u2019][A-Za-z]+)?")
for (t,) in con.execute("select text from translations where version='BLB'"):
    freq.update(w.lower().replace('\u2019', "'") for w in TOK.findall(t))

elm = {}
for ln in open(r'C:/Program Files (x86)/BibleWorks 10/databases/elm.txt', encoding='cp1252'):
    if ln.startswith('//'): continue
    p = ln.rstrip('\r\n').split('\t')
    if len(p) >= 2: elm[p[0].lower()] = set(p[1].split(','))
ours = {}
for ln in open(f'{HERE}/links.tsv', encoding='utf-8'):
    w, h = ln.rstrip('\n').split('\t')
    ours[w] = set(h.split(','))

words = [w for w in freq if w in elm and w in ours]

def expansions(table):
    inv = collections.defaultdict(set)
    for w in words:
        for h in table[w]: inv[h].add(w)
    return {w: set().union(*(inv[h] for h in table[w])) for w in words}

E, O = expansions(elm), expansions(ours)
tot_tok = sum(freq[w] for w in words)
exact = [w for w in words if E[w] == O[w]]
P = R = Pt = Rt = 0.0
for w in words:
    inter = len(E[w] & O[w])
    p, r = inter / len(O[w]), inter / len(E[w])
    P += p; R += r; Pt += p * freq[w]; Rt += r * freq[w]
n = len(words)
print(f"BLB words compared: {n:,}  ({tot_tok:,} tokens)")
print(f"identical expansion:  {len(exact)/n:6.1%} of words   {sum(freq[w] for w in exact)/tot_tok:6.1%} of tokens")
print(f"precision (ours ⊆ BW): {P/n:6.1%} words   {Pt/tot_tok:6.1%} tokens")
print(f"recall    (BW ⊆ ours): {R/n:6.1%} words   {Rt/tot_tok:6.1%} tokens")

if SHOW:
    diffs = sorted((w for w in words if E[w] != O[w]), key=lambda w: -freq[w])
    print(f"\nTop {SHOW} disagreements by frequency (+ only ours, - only BW):")
    for w in diffs[:SHOW]:
        extra, miss = sorted(O[w] - E[w]), sorted(E[w] - O[w])
        print(f"{w:14} {freq[w]:6}  +{extra[:8]}  -{miss[:8]}")
