// search.js — JS port of src/search.py (Greek/Hebrew morphological search)
// plus app.py's _search_english_inline (BLB English search).
(function (global) {
  'use strict';

  const { Word, Phrase, And, Or, wildcardToRegex, morphCodeMatches, parse } = QueryLib;
  const { translitQueryToGreek, stripAccentsLower } = GreekTranslit;
  const { isHebrewText, stripNiqqud } = HebrewUtil;
  const { BOOK_NAMES, bookSortKey } = Books;
  const { queryAll, queryOne } = DB;

  // ---- ref-set helpers (refs are (book,chapter,verse) triples) ----------
  function refKey(b, c, v) { return b + ':' + c + ':' + v; }
  function unKey(k) { const p = k.split(':'); return [Number(p[0]), Number(p[1]), Number(p[2])]; }
  function setIntersect(a, b) { const out = new Set(); for (const x of a) if (b.has(x)) out.add(x); return out; }
  function setUnion(a, b) { const out = new Set(a); for (const x of b) out.add(x); return out; }
  function setSubtract(a, b) { const out = new Set(); for (const x of a) if (!b.has(x)) out.add(x); return out; }

  function normalizeTerm(raw, lang) {
    if (lang === 'grk') return stripAccentsLower(translitQueryToGreek(raw));
    if (lang === 'heb' && isHebrewText(raw)) return stripNiqqud(raw);
    return raw;
  }

  function hebTextToStrongs(hebBare, db) {
    let rows;
    if (hebBare.includes('*') || hebBare.includes('?')) {
      const like = hebBare.replace(/\*/g, '%').replace(/\?/g, '_');
      rows = queryAll(db, 'SELECT strong_num FROM heb_lemma_index WHERE lemma_bare LIKE ?', [like]);
    } else {
      rows = queryAll(db, 'SELECT strong_num FROM heb_lemma_index WHERE lemma_bare=?', [hebBare]);
    }
    return rows.map((r) => r.strong_num);
  }

  function splitAt(raw, sep) {
    const idx = raw.indexOf(sep);
    if (idx === -1) return [raw, null];
    return [raw.slice(0, idx), raw.slice(idx + 1)];
  }

  function termRefs(term, lang, db) {
    const raw = term.raw;
    const hasMorph = raw.includes('@');
    const [lemmaPat, codePat] = hasMorph ? splitAt(raw, '@') : [raw, null];
    const norm = normalizeTerm(lemmaPat, lang);
    const hasWc = norm.includes('*') || norm.includes('?');

    let cond, params;
    if (hasWc) {
      const like = norm.replace(/\*/g, '%').replace(/\?/g, '_');
      cond = '(surface_norm LIKE ? OR lemma_norm LIKE ?)';
      params = [like, like];
    } else if (lang === 'heb' && isHebrewText(norm)) {
      const strongNums = hebTextToStrongs(norm, db);
      if (!strongNums.length) return new Set();
      cond = `lemma_norm IN (${strongNums.map(() => '?').join(',')})`;
      params = strongNums;
    } else {
      cond = '(surface_norm = ? OR lemma_norm = ?)';
      params = [norm, norm];
    }

    if (lang) {
      cond += ' AND lang = ?';
      params = params.concat([lang]);
    }

    const rows = queryAll(db, `SELECT book,chapter,verse,bw_code FROM words WHERE ${cond}`, params);

    if (codePat !== null) {
      const result = new Set();
      for (const r of rows) {
        if (morphCodeMatches(codePat, r.bw_code)) result.add(refKey(r.book, r.chapter, r.verse));
      }
      return result;
    }
    const result = new Set();
    for (const r of rows) result.add(refKey(r.book, r.chapter, r.verse));
    return result;
  }

  function phraseInWords(phrase, verseWords, lang) {
    const n = verseWords.length;
    for (let start = 0; start < n; start++) {
      let idx = start, ok = true;
      for (const term of phrase.words) {
        const raw = term.raw;
        const [lemmaPat, codePat] = raw.includes('@') ? splitAt(raw, '@') : [raw, null];
        const norm = normalizeTerm(lemmaPat, lang);
        const pat = wildcardToRegex(norm);
        let found = null;
        const upper = Math.min(idx + phrase.max_gap + 2, n);
        for (let j = idx; j < upper; j++) {
          const w = verseWords[j];
          if (pat.test(w.surface_norm) || pat.test(w.lemma_norm)) {
            if (codePat === null || morphCodeMatches(codePat, w.bw_code)) {
              found = j;
              break;
            }
          }
        }
        if (found === null) { ok = false; break; }
        idx = found + 1;
      }
      if (ok) return true;
    }
    return false;
  }

  function phraseRefs(phrase, lang, db) {
    if (!phrase.words.length) return new Set();
    const candidates = termRefs(phrase.words[0], lang, db);
    const result = new Set();
    for (const key of candidates) {
      const [b, c, v] = unKey(key);
      const verseWords = queryAll(
        db,
        'SELECT surface_norm,lemma_norm,bw_code FROM words WHERE book=? AND chapter=? AND verse=? ORDER BY pos',
        [b, c, v]
      );
      if (phraseInWords(phrase, verseWords, lang)) result.add(key);
    }
    return result;
  }

  function proxFilter(positiveTerms, candidateRefs, nVerses, lang, db) {
    const termRefSets = positiveTerms.map((t) => evalAst(t, lang, db));
    const result = new Set();
    for (const key of candidateRefs) {
      const [b, c, v] = unKey(key);
      let allMatch = true;
      for (const tset of termRefSets) {
        let hit = false;
        for (let vv = v - nVerses; vv <= v + nVerses; vv++) {
          if (tset.has(refKey(b, c, vv))) { hit = true; break; }
        }
        if (!hit) { allMatch = false; break; }
      }
      if (allMatch) result.add(key);
    }
    return result;
  }

  function evalAst(node, lang, db) {
    if (node instanceof Word) return termRefs(node, lang, db);
    if (node instanceof Phrase) return phraseRefs(node, lang, db);
    if (node instanceof And) {
      let result = null;
      for (const term of node.positive) {
        const hits = evalAst(term, lang, db);
        result = result === null ? hits : setIntersect(result, hits);
      }
      if (result === null) result = new Set();
      if (node.proximity !== null && node.proximity !== undefined) {
        result = proxFilter(node.positive, result, node.proximity, lang, db);
      }
      for (const term of node.negative) {
        result = setSubtract(result, evalAst(term, lang, db));
      }
      return result;
    }
    if (node instanceof Or) {
      let result = new Set();
      for (const opt of node.options) result = setUnion(result, evalAst(opt, lang, db));
      return result;
    }
    throw new Error('Unknown node: ' + node);
  }

  function collectHighlightTerms(ast, lang, db) {
    const terms = new Set();
    const strongNums = new Set();

    function walk(node) {
      if (node instanceof Word) {
        const raw = node.raw;
        const lemmaPat = raw.includes('@') ? raw.split('@')[0] : raw;
        const norm = normalizeTerm(lemmaPat, lang);
        if (lang === 'heb' && isHebrewText(norm)) {
          for (const snum of hebTextToStrongs(norm, db)) strongNums.add(snum);
        } else if (lang === 'heb' && norm && !['*', '?', '.*', '.?'].includes(norm)) {
          const hasWc = norm.includes('*') || norm.includes('?');
          if (hasWc) {
            const like = norm.replace(/\*/g, '%').replace(/\?/g, '_');
            const rows = queryAll(db, "SELECT DISTINCT lemma_norm FROM words WHERE lang='heb' AND lemma_norm LIKE ?", [like]);
            for (const r of rows) strongNums.add(r.lemma_norm);
          } else {
            strongNums.add(norm);
          }
        } else if (lang !== 'heb' && norm && !['*', '?'].includes(norm)) {
          terms.add(norm);
        }
      } else if (node instanceof Phrase) {
        for (const w of node.words) walk(w);
      } else if (node instanceof And || node instanceof Or) {
        const lst = node instanceof And ? node.positive.concat(node.negative) : node.options;
        for (const child of lst) walk(child);
      }
    }
    walk(ast);
    return [Array.from(terms), Array.from(strongNums)];
  }

  function search(cmdline, lang, bookFrom, bookTo, db) {
    lang = lang || 'grk';
    const ast = parse(cmdline);
    let refs = evalAst(ast, lang, db);

    if (bookFrom !== null && bookFrom !== undefined || bookTo !== null && bookTo !== undefined) {
      const lo = (bookFrom !== null && bookFrom !== undefined) ? bookFrom : 1;
      const hi = (bookTo !== null && bookTo !== undefined) ? bookTo : 999;
      refs = new Set(Array.from(refs).filter((k) => { const [b] = unKey(k); return b >= lo && b <= hi; }));
    }

    const [hlTerms, hlStrongs] = collectHighlightTerms(ast, lang, db);

    const sortedRefs = Array.from(refs).map(unKey).sort((a, b) => {
      const ka = bookSortKey(a[0]), kb = bookSortKey(b[0]);
      if (ka !== kb) return ka - kb;
      if (a[1] !== b[1]) return a[1] - b[1];
      return a[2] - b[2];
    });

    const results = [];
    for (const [b, c, v] of sortedRefs) {
      const words = queryAll(
        db,
        'SELECT surface,edition FROM words WHERE book=? AND chapter=? AND verse=? AND lang=? ORDER BY edition,pos',
        [b, c, v, lang]
      );
      const byEdition = new Map();
      const order = [];
      for (const w of words) {
        const ed = w.edition;
        if (!byEdition.has(ed)) { byEdition.set(ed, []); order.push(ed); }
        byEdition.get(ed).push(w.surface);
      }
      const texts = order.map((ed) => ({ edition: ed, text: byEdition.get(ed).join(' ') }));
      results.push({
        book: b, chapter: c, verse: v,
        ref: `${BOOK_NAMES[b] || b} ${c}:${v}`,
        text: texts.length ? texts[0].text : '',
        texts,
      });
    }
    return { results, hl_terms: hlTerms, hl_strongs: hlStrongs };
  }

  // ─── English (BLB) search — mirrors app.py's _search_english_inline ────
  function reEscape(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function wordRe(raw) {
    const pat = reEscape(raw).replace(/\\\*/g, '\\w*').replace(/\\\?/g, '\\w');
    return new RegExp('\\b' + pat + '\\b', 'i');
  }

  function wordMatch(text, raw) {
    raw = raw.replace(/^[.'!/\\]+/, '');
    if (!raw) return false;
    return wordRe(raw).test(text);
  }

  function phraseMatchEng(text, phrase) {
    const words = phrase.words.map((w) => w.raw);
    let pat;
    if (phrase.max_gap === 0) {
      pat = words.map((w) => '\\b' + reEscape(w) + '\\b').join('\\s+');
    } else {
      const gap = '(?:\\s+\\S+){0,' + phrase.max_gap + '}\\s+';
      pat = words.map((w) => '\\b' + reEscape(w) + '\\b').join(gap);
    }
    return new RegExp(pat, 'i').test(text);
  }

  function evalNodeEng(node, text) {
    if (node instanceof Word) return wordMatch(text, node.raw);
    if (node instanceof Phrase) return phraseMatchEng(text, node);
    if (node instanceof And) {
      return node.positive.every((t) => evalNodeEng(t, text)) &&
        !node.negative.some((t) => evalNodeEng(t, text));
    }
    if (node instanceof Or) return node.options.some((o) => evalNodeEng(o, text));
    return false;
  }

  function extractTermsEng(node) {
    if (node instanceof Word) return [node.raw];
    if (node instanceof Phrase) return node.words.map((w) => w.raw);
    if (node instanceof And) return node.positive.flatMap(extractTermsEng);
    if (node instanceof Or) return node.options.flatMap(extractTermsEng);
    return [];
  }

  function searchEnglishInline(cmdline, bookFrom, bookTo, db) {
    const ast = parse(cmdline);
    const allTerms = extractTermsEng(ast);
    const hl = Array.from(new Set(allTerms.map((t) => t.toLowerCase())));

    if (!DB.tableExists(db, 'translations')) {
      return { results: [], hl_terms: hl, hl_strongs: [] };
    }

    if (ast instanceof And && ast.proximity !== null && ast.proximity !== undefined) {
      const N = ast.proximity;
      const termVerseSets = [];
      for (const term of ast.positive) {
        let sql = "SELECT book,chapter,verse,text FROM translations WHERE version='BLB'";
        if (bookFrom) sql += ` AND book>=${parseInt(bookFrom, 10)}`;
        if (bookTo) sql += ` AND book<=${parseInt(bookTo, 10)}`;
        const rows = queryAll(db, sql);
        const hits = new Set();
        for (const row of rows) {
          if (evalNodeEng(term, row.text)) hits.add(refKey(row.book, row.chapter, row.verse));
        }
        termVerseSets.push(hits);
      }
      let allHitRefs = new Set();
      for (const s of termVerseSets) allHitRefs = setUnion(allHitRefs, s);

      const results = [];
      const seen = new Set();
      const sortedHits = Array.from(allHitRefs).map(unKey).sort((a, b) =>
        a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
      for (const [b, c, v] of sortedHits) {
        const key = refKey(b, c, v);
        if (seen.has(key)) continue;
        const window = new Set();
        for (let vv = v - N; vv <= v + N; vv++) window.add(refKey(b, c, vv));
        const allWithinWindow = termVerseSets.every((ts) => {
          for (const w of window) if (ts.has(w)) return true;
          return false;
        });
        if (allWithinWindow) {
          const windowHits = Array.from(setIntersect(window, allHitRefs)).map(unKey)
            .sort((a, b2) => a[0] - b2[0] || a[1] - b2[1] || a[2] - b2[2]);
          for (const [b2, c2, v2] of windowHits) {
            const key2 = refKey(b2, c2, v2);
            if (!seen.has(key2)) {
              seen.add(key2);
              const row = queryOne(db,
                "SELECT text FROM translations WHERE book=? AND chapter=? AND verse=? AND version='BLB'",
                [b2, c2, v2]);
              if (row) {
                results.push({ book: b2, chapter: c2, verse: v2,
                  ref: `${BOOK_NAMES[b2] || b2} ${c2}:${v2}`, text: row.text });
              }
            }
          }
        }
      }
      return { results, hl_terms: hl, hl_strongs: [] };
    }

    // ── standard search: SQL pre-filter + JS evaluation ──
    const conditions = ["version='BLB'"];
    const params = [];
    if (bookFrom) conditions.push(`book>=${parseInt(bookFrom, 10)}`);
    if (bookTo) conditions.push(`book<=${parseInt(bookTo, 10)}`);

    function makeLike(t) {
      return '%' + t.replace(/^[.'!/]+/, '').replace(/\*/g, '%').replace(/\?/g, '_') + '%';
    }

    if (ast instanceof Or) {
      if (allTerms.length) {
        conditions.push('(' + allTerms.map(() => 'text LIKE ?').join(' OR ') + ')');
        for (const t of allTerms) params.push(makeLike(t));
      }
    } else {
      for (const t of allTerms) {
        conditions.push('text LIKE ?');
        params.push(makeLike(t));
      }
    }

    const sql = 'SELECT book,chapter,verse,text FROM translations WHERE ' +
      conditions.join(' AND ') + ' ORDER BY book,chapter,verse';
    const rows = queryAll(db, sql, params);

    const results = [];
    for (const row of rows) {
      if (evalNodeEng(ast, row.text)) {
        results.push({
          book: row.book, chapter: row.chapter, verse: row.verse,
          ref: `${BOOK_NAMES[row.book] || row.book} ${row.chapter}:${row.verse}`,
          text: row.text,
        });
      }
    }
    return { results, hl_terms: hl, hl_strongs: [] };
  }

  global.SearchLib = {
    search, searchEnglishInline, evalAst, termRefs, phraseRefs,
    collectHighlightTerms, normalizeTerm, refKey, unKey,
  };
})(window);
