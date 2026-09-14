// books.js — JS port of src/books.py (book name/abbreviation resolver for
// the 'l' limit command) plus the BOOK_NAMES / EDITION_LABELS tables from
// corpus.py and app.py used for display and result refs.
(function (global) {
  'use strict';

  const BOOK_TABLE = [
    [1, ['gen', 'ge', 'genesis'], 'Genesis'],
    [2, ['exod', 'ex', 'exo', 'exodus'], 'Exodus'],
    [3, ['lev', 'le', 'lv', 'leviticus'], 'Leviticus'],
    [4, ['num', 'nu', 'nm', 'numbers'], 'Numbers'],
    [5, ['deut', 'dt', 'de', 'deu', 'deuteronomy'], 'Deuteronomy'],
    [6, ['josh', 'jos', 'jsh', 'joshua'], 'Joshua'],
    [7, ['judg', 'jdg', 'jg', 'jud', 'judges'], 'Judges'],
    [8, ['ruth', 'ru', 'rth'], 'Ruth'],
    [9, ['1sam', '1sa', '1sm', '1samuel', 'isamuel', 'isam'], '1 Samuel'],
    [10, ['2sam', '2sa', '2sm', '2samuel', 'iisamuel', 'iisam'], '2 Samuel'],
    [11, ['1kgs', '1ki', '1kg', '1kings', 'ikings'], '1 Kings'],
    [12, ['2kgs', '2ki', '2kg', '2kings', 'iikings'], '2 Kings'],
    [13, ['1chr', '1ch', '1chron', '1chronicles', 'ichronicles'], '1 Chronicles'],
    [14, ['2chr', '2ch', '2chron', '2chronicles', 'iichronicles'], '2 Chronicles'],
    [15, ['ezra', 'ezr'], 'Ezra'],
    [16, ['neh', 'ne', 'nehemiah'], 'Nehemiah'],
    [17, ['esth', 'es', 'est', 'esther'], 'Esther'],
    [18, ['job', 'jb'], 'Job'],
    [19, ['ps', 'psa', 'pss', 'psalm', 'psalms'], 'Psalms'],
    [20, ['prov', 'pr', 'prv', 'proverbs'], 'Proverbs'],
    [21, ['eccl', 'ec', 'ecc', 'qoh', 'ecclesiastes'], 'Ecclesiastes'],
    [22, ['song', 'ss', 'sg', 'sos', 'songofsongs', 'canticles', 'songofsolomon', 'solomon'], 'Song of Songs'],
    [23, ['isa', 'is', 'isaiah'], 'Isaiah'],
    [24, ['jer', 'je', 'jeremiah'], 'Jeremiah'],
    [25, ['lam', 'la', 'lamentations'], 'Lamentations'],
    [26, ['ezek', 'eze', 'ezekiel'], 'Ezekiel'],
    [27, ['dan', 'da', 'dn', 'daniel'], 'Daniel'],
    [28, ['hos', 'ho', 'hosea'], 'Hosea'],
    [29, ['joel', 'jl', 'joe'], 'Joel'],
    [30, ['amos', 'am'], 'Amos'],
    [31, ['obad', 'ob', 'obadiah'], 'Obadiah'],
    [32, ['jonah', 'jon', 'jnh'], 'Jonah'],
    [33, ['mic', 'mi', 'micah'], 'Micah'],
    [34, ['nah', 'na', 'nahum'], 'Nahum'],
    [35, ['hab', 'hb', 'habakkuk'], 'Habakkuk'],
    [36, ['zeph', 'zp', 'zep', 'zephaniah'], 'Zephaniah'],
    [37, ['hag', 'hg', 'haggai'], 'Haggai'],
    [38, ['zech', 'zc', 'zec', 'zechariah'], 'Zechariah'],
    [39, ['mal', 'ml', 'malachi'], 'Malachi'],
    [40, ['matt', 'mt', 'mat', 'matthew'], 'Matthew'],
    [41, ['mark', 'mk', 'mrk', 'mar', 'marc', 'mr'], 'Mark'],
    [42, ['luke', 'lk', 'luk', 'lu'], 'Luke'],
    [43, ['john', 'jn', 'joh', 'jhn'], 'John'],
    [44, ['acts', 'ac', 'act'], 'Acts'],
    [45, ['rom', 'ro', 'rm', 'romans'], 'Romans'],
    [46, ['1cor', '1co', '1corinthians', 'icorinthians'], '1 Corinthians'],
    [47, ['2cor', '2co', '2corinthians', 'iicorinthians'], '2 Corinthians'],
    [48, ['gal', 'ga', 'galatians'], 'Galatians'],
    [49, ['eph', 'ephesians'], 'Ephesians'],
    [50, ['phil', 'php', 'ph', 'philippians'], 'Philippians'],
    [51, ['col', 'colos', 'colossians'], 'Colossians'],
    [52, ['1thess', '1th', '1thes', '1thessalonians'], '1 Thessalonians'],
    [53, ['2thess', '2th', '2thes', '2thessalonians'], '2 Thessalonians'],
    [54, ['1tim', '1ti', '1timothy'], '1 Timothy'],
    [55, ['2tim', '2ti', '2timothy'], '2 Timothy'],
    [56, ['titus', 'tit', 'ti'], 'Titus'],
    [57, ['phlm', 'phm', 'philem', 'philemon'], 'Philemon'],
    [58, ['heb', 'hebrews'], 'Hebrews'],
    [59, ['jas', 'jm', 'jam', 'james'], 'James'],
    [60, ['1pet', '1pe', '1pt', '1peter', 'ipeter'], '1 Peter'],
    [61, ['2pet', '2pe', '2pt', '2peter', 'iipeter'], '2 Peter'],
    [62, ['1john', '1jn', '1jo', 'ijohn'], '1 John'],
    [63, ['2john', '2jn', '2jo', 'iijohn'], '2 John'],
    [64, ['3john', '3jn', '3jo', 'iiijohn'], '3 John'],
    [65, ['jude', 'jud', 'jd'], 'Jude'],
    [66, ['rev', 're', 'rv', 'revelation', 'apocalypse'], 'Revelation'],
    [67, ['1esd', '1esdras', 'iesdras'], '1 Esdras'],
    [68, ['2esd', '2esdras', 'iiesdras'], '2 Esdras'],
    [69, ['jdt', 'judith'], 'Judith'],
    [70, ['tob', 'tobit'], 'Tobit'],
    [71, ['1macc', '1maccabees', 'imaccabees'], '1 Maccabees'],
    [72, ['2macc', '2maccabees', 'iimaccabees'], '2 Maccabees'],
    [73, ['3macc', '3maccabees', 'iiimaccabees'], '3 Maccabees'],
    [74, ['4macc', '4maccabees', 'ivmaccabees'], '4 Maccabees'],
    [75, ['odes', 'ode'], 'Odes'],
    [76, ['wis', 'wisd', 'wisdom', 'wisdomofsolomon'], 'Wisdom of Solomon'],
    [77, ['sir', 'sirach', 'ecclesiasticus', 'ecclus'], 'Sirach'],
    [78, ['pssol', 'psalmsofsolomon'], 'Psalms of Solomon'],
    [79, ['bar', 'baruch'], 'Baruch'],
    [80, ['epjer', 'letterofjeremiah', 'epistleofjeremiah'], 'Epistle of Jeremiah'],
    [81, ['sus', 'susanna'], 'Susanna'],
    [82, ['bel', 'belandthedragon'], 'Bel and the Dragon'],
  ];

  const LOOKUP = {};
  const CANONICAL = {};
  for (const [bnum, aliases, canonical] of BOOK_TABLE) {
    CANONICAL[bnum] = canonical;
    for (const a of aliases) {
      LOOKUP[a.toLowerCase().replace(/ /g, '').replace(/\./g, '')] = bnum;
    }
  }

  function resolveBook(name) {
    const key = name.toLowerCase().replace(/ /g, '').replace(/\./g, '').replace(/-/g, '');
    return Object.prototype.hasOwnProperty.call(LOOKUP, key) ? LOOKUP[key] : null;
  }

  function canonicalName(bookNum) {
    return Object.prototype.hasOwnProperty.call(CANONICAL, bookNum) ? CANONICAL[bookNum] : String(bookNum);
  }

  function bookSortKey(bookNum) {
    if (bookNum <= 39) return bookNum;
    if (bookNum >= 67 && bookNum <= 82) return 39 + (bookNum - 66);
    return 55 + (bookNum - 39);
  }

  const NAMED_RANGES = {
    ot: [1, 39], oldtestament: [1, 39],
    nt: [40, 66], newtestament: [40, 66],
    pentateuch: [1, 5], torah: [1, 5],
    gospels: [40, 43],
    pauline: [45, 57], paulineepistle: [45, 57], paulineepistles: [45, 57],
    general: [58, 65], generalepistles: [58, 65],
    lxx: [1, 39],
    apocrypha: [67, 82], deuterocanon: [67, 82],
  };

  function parseLimit(limitStr) {
    const s = (limitStr || '').trim();
    const key = s.toLowerCase().replace(/ /g, '').replace(/\./g, '');
    if (Object.prototype.hasOwnProperty.call(NAMED_RANGES, key)) return NAMED_RANGES[key].slice();

    if (s.includes('-')) {
      const idx = s.indexOf('-');
      const b1 = resolveBook(s.slice(0, idx).trim());
      const b2 = resolveBook(s.slice(idx + 1).trim());
      if (b1 && b2) return [Math.min(b1, b2), Math.max(b1, b2)];
      return null;
    }

    const b = resolveBook(s);
    if (b) return [b, b];
    return null;
  }

  // BOOK_NAMES: short display abbreviations, from src/corpus.py. Used for
  // 'ref' strings in search results and for /api/books display names.
  const BOOK_NAMES = {
    1: 'Gen', 2: 'Exod', 3: 'Lev', 4: 'Num', 5: 'Deut', 6: 'Josh', 7: 'Judg', 8: 'Ruth',
    9: '1Sam', 10: '2Sam', 11: '1Kgs', 12: '2Kgs', 13: '1Chr', 14: '2Chr', 15: 'Ezra',
    16: 'Neh', 17: 'Esth', 18: 'Job', 19: 'Ps', 20: 'Prov', 21: 'Eccl', 22: 'Song',
    23: 'Isa', 24: 'Jer', 25: 'Lam', 26: 'Ezek', 27: 'Dan', 28: 'Hos', 29: 'Joel',
    30: 'Amos', 31: 'Obad', 32: 'Jonah', 33: 'Mic', 34: 'Nah', 35: 'Hab', 36: 'Zeph',
    37: 'Hag', 38: 'Zech', 39: 'Mal',
    40: 'Matt', 41: 'Mark', 42: 'Luke', 43: 'John', 44: 'Acts', 45: 'Rom',
    46: '1Cor', 47: '2Cor', 48: 'Gal', 49: 'Eph', 50: 'Phil', 51: 'Col',
    52: '1Thess', 53: '2Thess', 54: '1Tim', 55: '2Tim', 56: 'Titus', 57: 'Phlm',
    58: 'Heb', 59: 'Jas', 60: '1Pet', 61: '2Pet', 62: '1John', 63: '2John',
    64: '3John', 65: 'Jude', 66: 'Rev',
    67: '1Esd', 68: '2Esd', 69: 'Jdt', 70: 'Tob',
    71: '1Macc', 72: '2Macc', 73: '3Macc', 74: '4Macc',
    75: 'Odes', 76: 'Wis', 77: 'Sir', 78: 'PsSol',
    79: 'Bar', 80: 'EpJer', 81: 'Sus', 82: 'Bel',
  };

  const EDITION_LABELS = {
    A: 'Codex A (Alexandrinus)', B: 'Codex B (Vaticanus)',
    OG: 'Old Greek', TH: 'Theodotion',
    BA: 'Vaticanus/Alexandrinus text', S: 'Sinaiticus text',
  };

  global.Books = {
    BOOK_TABLE, BOOK_NAMES, EDITION_LABELS,
    resolveBook, canonicalName, bookSortKey, parseLimit,
  };
})(window);
