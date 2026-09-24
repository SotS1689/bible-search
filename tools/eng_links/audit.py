import json, collections
exec(open('compare.py', encoding='utf-8').read().split("if SHOW:")[0].replace("print(", "(lambda *a, **k: None)("))
d = json.load(open('rules.json'))
stats = collections.defaultdict(lambda: [0, 0, []])
for k, suf in d['affix'].items():
    w, stem = k.split('|')
    if w not in E or stem not in E: continue
    ok = stem in E[w]
    s = stats[suf]; s[0] += ok; s[1] += 1
    if not ok: s[2].append(f'{w}>{stem}')
for suf, (ok, n, bad) in sorted(stats.items(), key=lambda x: x[1][0] / x[1][1]):
    print(f'{suf:10} {ok:4}/{n:<4} {ok/n:5.0%}  bad: {bad[:10]}')
