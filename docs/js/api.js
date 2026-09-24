// api.js — JS port of the Flask route handlers in app.py, operating on the
// in-browser sql.js database. Each function returns a plain JS value with
// exactly the shape the corresponding Flask endpoint's jsonify() produced.
(function (global) {
  'use strict';

  const { queryAll, queryOne, tableExists } = DB;
  const { BOOK_NAMES, EDITION_LABELS, bookSortKey, canonicalName, parseLimit } = Books;
  const { search, searchEnglishInline } = SearchLib;

  function primaryEdition(editionsSet) {
    if (editionsSet.has(null)) return null;
    if (!editionsSet.size) return null;
    return Array.from(editionsSet).sort()[0];
  }

  function apiSearch(db, params) {
    const q = (params.get('q') || '').trim();
    const lang = params.get('lang') || 'grk';
    if (!q) return { results: [], count: 0, error: null };
    const bookFromRaw = params.get('book_from');
    const bookToRaw = params.get('book_to');
    const bookFrom = bookFromRaw !== null && bookFromRaw !== '' ? parseInt(bookFromRaw, 10) : null;
    const bookTo = bookToRaw !== null && bookToRaw !== '' ? parseInt(bookToRaw, 10) : null;
    try {
      let results, hlTerms, hlStrongs;
      if (lang === 'eng') {
        const stem = params.get('stem') === '1';
        ({ results, hl_terms: hlTerms, hl_strongs: hlStrongs } = searchEnglishInline(q, bookFrom, bookTo, db, stem));
      } else {
        ({ results, hl_terms: hlTerms, hl_strongs: hlStrongs } = search(q, lang, bookFrom, bookTo, db));
      }
      return { results, count: results.length, hl_terms: hlTerms, hl_strongs: hlStrongs, error: null };
    } catch (e) {
      return { results: [], count: 0, hl_terms: [], hl_strongs: [], error: String((e && e.message) || e) };
    }
  }

  function apiVerse(db, params) {
    const book = parseInt(params.get('book') || '40', 10);
    const chapter = parseInt(params.get('chapter') || '1', 10);
    const verse = parseInt(params.get('verse') || '1', 10);
    const lang = params.get('lang') || (book <= 39 ? 'heb' : 'grk');
    const editionParam = params.has('edition') ? params.get('edition') : undefined;

    const rows = queryAll(db,
      'SELECT surface,surface_norm,lemma,lemma_norm,bw_code,lang,edition FROM words ' +
      'WHERE book=? AND chapter=? AND verse=? AND lang=? ORDER BY edition,pos',
      [book, chapter, verse, lang]);

    let chosen;
    if (editionParam !== undefined) {
      chosen = (editionParam === '' || editionParam === 'null' || editionParam === 'None') ? null : editionParam;
    } else {
      const editions = new Set(rows.map((r) => r.edition));
      chosen = primaryEdition(editions);
    }
    const out = rows.filter((r) => r.edition === chosen).map((r) => {
      const d = Object.assign({}, r);
      delete d.edition;
      return d;
    });
    return out;
  }

  function apiPassage(db, params) {
    const book = parseInt(params.get('book') || '40', 10);
    const chapter = parseInt(params.get('chapter') || '1', 10);
    const lang = params.get('lang') || (book <= 39 ? 'heb' : 'grk');

    const rows = queryAll(db,
      'SELECT verse,surface,pos,edition FROM words WHERE book=? AND chapter=? AND lang=? ORDER BY verse,edition,pos',
      [book, chapter, lang]);

    const byVerseEd = new Map(); // verse -> Map(edition -> [surfaces])
    for (const r of rows) {
      if (!byVerseEd.has(r.verse)) byVerseEd.set(r.verse, new Map());
      const editions = byVerseEd.get(r.verse);
      if (!editions.has(r.edition)) editions.set(r.edition, []);
      editions.get(r.edition).push(r.surface);
    }

    const out = [];
    const verses = Array.from(byVerseEd.keys()).sort((a, b) => a - b);
    for (const v of verses) {
      const editions = byVerseEd.get(v);
      const edKeys = Array.from(editions.keys()).sort((a, b) => {
        const an = a === null ? 0 : 1, bn = b === null ? 0 : 1;
        if (an !== bn) return an - bn;
        return (a || '').localeCompare(b || '');
      });
      const texts = edKeys.map((ed) => ({
        edition: ed, label: EDITION_LABELS[ed] || null, text: editions.get(ed).join(' '),
      }));
      const primary = primaryEdition(new Set(edKeys));
      const primaryText = editions.has(primary) ? editions.get(primary).join(' ') : texts[0].text;
      out.push({ verse: v, text: primaryText, texts });
    }
    return out;
  }

  function apiGloss(db, params) {
    const lang = params.get('lang') || 'grk';
    const key = (params.get('key') || '').trim();
    if (!key) return null;
    if (!tableExists(db, 'lexicon')) return null; // predates the lexicon table
    const row = queryOne(db,
      'SELECT estrong, translit, gloss, meaning FROM lexicon WHERE lang=? AND key_norm=?',
      [lang, key]);
    return row || null;
  }

  function apiBooks(db) {
    const rows = queryAll(db, 'SELECT DISTINCT book FROM words');
    const nums = rows.map((r) => r.book).sort((a, b) => bookSortKey(a) - bookSortKey(b));
    return nums.map((n) => ({ num: n, name: BOOK_NAMES[n] || String(n) }));
  }

  function apiChapters(db, params) {
    const book = parseInt(params.get('book') || '40', 10);
    const rows = queryAll(db, 'SELECT DISTINCT chapter FROM words WHERE book=? ORDER BY chapter', [book]);
    return rows.map((r) => r.chapter);
  }

  function apiTranslation(db, params) {
    const book = parseInt(params.get('book') || '40', 10);
    const chapter = parseInt(params.get('chapter') || '1', 10);
    const version = params.get('version') || 'BLB';
    const rows = queryAll(db,
      'SELECT verse, text FROM translations WHERE book=? AND chapter=? AND version=? ORDER BY verse',
      [book, chapter, version]);
    const out = {};
    for (const r of rows) out[r.verse] = r.text;
    return out;
  }

  function apiResolveLimit(db, params) {
    const s = (params.get('q') || '').trim();
    const result = parseLimit(s);
    if (result) {
      const [b1, b2] = result;
      return {
        book_from: b1, book_to: b2,
        label: b1 === b2 ? canonicalName(b1) : `${canonicalName(b1)} – ${canonicalName(b2)}`,
      };
    }
    return { error: `Unknown book or range: "${s}"` };
  }

  global.Api = {
    apiSearch, apiVerse, apiPassage, apiGloss, apiBooks, apiChapters,
    apiTranslation, apiResolveLimit,
  };
})(window);
