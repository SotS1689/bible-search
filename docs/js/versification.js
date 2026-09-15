// ════════════════════════════════════════════════════════════
//  VERSIFICATION — English <-> Hebrew (Masoretic/OSHB) <-> Greek (LXX)
//  chapter/verse mapping.
//
//  The app's word tables store Hebrew and Greek text under each
//  language's own *native* chapter/verse numbering (OSHB for Hebrew,
//  CATSS/LXX for Greek), while typed references and the English
//  translation overlay use the familiar English (KJV-tradition)
//  numbering. In the majority of books these agree; in the books
//  below they diverge, sometimes by a whole trailing chapter (e.g.
//  Joel 3/4, Malachi 3/4), sometimes by a running one-verse offset
//  (e.g. every Psalm with a Hebrew title, counted there as verse 1).
//
//  Source: "Appendix B: English/Hebrew/Greek Versification," The SBL
//  Handbook of Style, 2nd ed. (SBL Press, 2014), pp. 265-268, via the
//  table at https://matthewbarron.org/bible-versification-compared/.
//
//  Known, intentionally unmapped gap: Greek (LXX) Jeremiah 25-51 and
//  Proverbs 15-31 reorder whole blocks of material relative to the
//  Hebrew/English text (not a simple chapter/verse offset), so Greek
//  in those ranges falls back to the Hebrew numbering here rather
//  than being precisely remapped.
// ════════════════════════════════════════════════════════════

(function (global) {
  // Book numbers match corpus.py's BOOK_NAMES (1-39 = OT).
  // Each segment: English chapter `ech`, verse range [ev0,ev1] -> Hebrew
  // chapter `hch`, starting verse `hv0` (same length range, so
  // hebVerse = hv0 + (engVerse - ev0)).
  const ENG_HEB_SEGMENTS = {
    1: [ // Genesis
      { ech: 31, ev0: 55, ev1: 55, hch: 32, hv0: 1 },
      { ech: 32, ev0: 1,  ev1: 32, hch: 32, hv0: 2 },
    ],
    2: [ // Exodus
      { ech: 8,  ev0: 1,  ev1: 4,  hch: 7,  hv0: 26 },
      { ech: 8,  ev0: 5,  ev1: 32, hch: 8,  hv0: 1 },
      { ech: 22, ev0: 1,  ev1: 1,  hch: 21, hv0: 37 },
      { ech: 22, ev0: 2,  ev1: 31, hch: 22, hv0: 1 },
    ],
    3: [ // Leviticus
      { ech: 6, ev0: 1, ev1: 7,  hch: 5, hv0: 20 },
      { ech: 6, ev0: 8, ev1: 30, hch: 6, hv0: 1 },
    ],
    4: [ // Numbers
      { ech: 16, ev0: 36, ev1: 50, hch: 17, hv0: 1 },
      { ech: 17, ev0: 1,  ev1: 13, hch: 17, hv0: 16 },
      { ech: 29, ev0: 40, ev1: 40, hch: 30, hv0: 1 },
      { ech: 30, ev0: 1,  ev1: 16, hch: 30, hv0: 2 },
    ],
    5: [ // Deuteronomy
      { ech: 12, ev0: 32, ev1: 32, hch: 13, hv0: 1 },
      { ech: 13, ev0: 1,  ev1: 18, hch: 13, hv0: 2 },
      { ech: 22, ev0: 30, ev1: 30, hch: 23, hv0: 1 },
      { ech: 23, ev0: 1,  ev1: 25, hch: 23, hv0: 2 },
      { ech: 29, ev0: 1,  ev1: 1,  hch: 28, hv0: 69 },
      { ech: 29, ev0: 2,  ev1: 29, hch: 29, hv0: 1 },
    ],
    9: [ // 1 Samuel
      { ech: 21, ev0: 1, ev1: 15, hch: 21, hv0: 2 },
      { ech: 24, ev0: 1, ev1: 22, hch: 24, hv0: 2 },
    ],
    10: [ // 2 Samuel
      { ech: 19, ev0: 1, ev1: 43, hch: 19, hv0: 2 },
    ],
    11: [ // 1 Kings
      { ech: 4,  ev0: 21, ev1: 34, hch: 5,  hv0: 1 },
      { ech: 5,  ev0: 1,  ev1: 18, hch: 5,  hv0: 15 },
      { ech: 22, ev0: 44, ev1: 53, hch: 22, hv0: 45 },
    ],
    12: [ // 2 Kings
      { ech: 12, ev0: 1, ev1: 21, hch: 12, hv0: 2 },
    ],
    13: [ // 1 Chronicles
      { ech: 6,  ev0: 1,  ev1: 15, hch: 5,  hv0: 27 },
      { ech: 6,  ev0: 16, ev1: 81, hch: 6,  hv0: 1 },
      { ech: 12, ev0: 5,  ev1: 40, hch: 12, hv0: 6 },
    ],
    14: [ // 2 Chronicles
      { ech: 2,  ev0: 1,  ev1: 1,  hch: 1,  hv0: 18 },
      { ech: 2,  ev0: 2,  ev1: 18, hch: 2,  hv0: 1 },
      { ech: 14, ev0: 1,  ev1: 1,  hch: 13, hv0: 23 },
      { ech: 14, ev0: 2,  ev1: 15, hch: 14, hv0: 1 },
    ],
    16: [ // Nehemiah
      { ech: 4,  ev0: 1,  ev1: 6,  hch: 3,  hv0: 33 },
      { ech: 4,  ev0: 7,  ev1: 23, hch: 4,  hv0: 1 },
      { ech: 9,  ev0: 38, ev1: 38, hch: 10, hv0: 1 },
      { ech: 10, ev0: 1,  ev1: 39, hch: 10, hv0: 2 },
    ],
    18: [ // Job
      { ech: 41, ev0: 1, ev1: 8,  hch: 40, hv0: 25 },
      { ech: 41, ev0: 9, ev1: 34, hch: 41, hv0: 1 },
    ],
    // 19 Psalms: handled separately via PSALM_TITLE_OFFSET below.
    21: [ // Ecclesiastes
      { ech: 5, ev0: 1, ev1: 1,  hch: 4, hv0: 17 },
      { ech: 5, ev0: 2, ev1: 20, hch: 5, hv0: 1 },
    ],
    22: [ // Song of Songs
      { ech: 6, ev0: 13, ev1: 13, hch: 7, hv0: 1 },
      { ech: 7, ev0: 1,  ev1: 13, hch: 7, hv0: 2 },
    ],
    23: [ // Isaiah
      { ech: 9,  ev0: 1,  ev1: 1,  hch: 8,  hv0: 23 },
      { ech: 9,  ev0: 2,  ev1: 21, hch: 9,  hv0: 1 },
      { ech: 64, ev0: 2,  ev1: 12, hch: 64, hv0: 1 },
    ],
    24: [ // Jeremiah (only the ch8/9 boundary; Hebrew=English through the
          // rest of the book -- it's only the Greek/LXX that reorders
          // chapters 25-51, which is not mapped here, see file header)
      { ech: 9, ev0: 1, ev1: 1,  hch: 8, hv0: 23 },
      { ech: 9, ev0: 2, ev1: 26, hch: 9, hv0: 1 },
    ],
    26: [ // Ezekiel
      { ech: 20, ev0: 45, ev1: 49, hch: 21, hv0: 1 },
      { ech: 21, ev0: 1,  ev1: 32, hch: 21, hv0: 6 },
    ],
    27: [ // Daniel
      { ech: 4, ev0: 1,  ev1: 3,  hch: 3, hv0: 31 },
      { ech: 4, ev0: 4,  ev1: 37, hch: 4, hv0: 1 },
      { ech: 5, ev0: 31, ev1: 31, hch: 6, hv0: 1 },
      { ech: 6, ev0: 1,  ev1: 28, hch: 6, hv0: 2 },
    ],
    28: [ // Hosea
      { ech: 1,  ev0: 10, ev1: 11, hch: 2,  hv0: 1 },
      { ech: 2,  ev0: 1,  ev1: 23, hch: 2,  hv0: 3 },
      { ech: 11, ev0: 12, ev1: 12, hch: 12, hv0: 1 },
      { ech: 12, ev0: 1,  ev1: 14, hch: 12, hv0: 2 },
      { ech: 13, ev0: 16, ev1: 16, hch: 14, hv0: 1 },
      { ech: 14, ev0: 1,  ev1: 9,  hch: 14, hv0: 2 },
    ],
    29: [ // Joel — the headline example: Eng 2:28-32 = Heb/Grk 3:1-5,
          // and all of Eng ch3 = Heb/Grk ch4.
      { ech: 2, ev0: 28, ev1: 32, hch: 3, hv0: 1 },
      { ech: 3, ev0: 1,  ev1: 21, hch: 4, hv0: 1 },
    ],
    32: [ // Jonah
      { ech: 1, ev0: 17, ev1: 17, hch: 2, hv0: 1 },
      { ech: 2, ev0: 1,  ev1: 10, hch: 2, hv0: 2 },
    ],
    33: [ // Micah
      { ech: 5, ev0: 1, ev1: 1,  hch: 4, hv0: 14 },
      { ech: 5, ev0: 2, ev1: 15, hch: 5, hv0: 1 },
    ],
    34: [ // Nahum
      { ech: 1, ev0: 15, ev1: 15, hch: 2, hv0: 1 },
      { ech: 2, ev0: 1,  ev1: 13, hch: 2, hv0: 2 },
    ],
    38: [ // Zechariah
      { ech: 1, ev0: 18, ev1: 21, hch: 2, hv0: 1 },
      { ech: 2, ev0: 1,  ev1: 13, hch: 2, hv0: 5 },
    ],
    39: [ // Malachi — the other headline example: all of Eng ch4 is
          // Heb ch3 vv19-24; Hebrew Malachi has no chapter 4 at all.
      { ech: 4, ev0: 1, ev1: 6, hch: 3, hv0: 19 },
    ],
  };

  // Psalms with a Hebrew title counted as verse 1 (shifting every body
  // verse after it by this many). Everything not listed (incl. 1, 2, 10,
  // 33, 43, 71, 91, 93-97, 99, 104-107, 109, 110, 111-138, 146-150) has no
  // shift: Eng verse == Heb verse for that psalm.
  const PSALM_TITLE_OFFSET_1 = new Set([
    3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,
    30,31,32,34,35,36,37,38,39,40,41,42,44,45,46,47,48,49,50,51,52,53,54,
    55,56,57,58,59,61,62,63,64,65,66,67,68,69,70,72,73,74,76,77,78,79,80,
    81,82,83,84,85,86,87,88,89,90,92,98,100,101,102,103,108,139,140,141,
    142,143,144,145,
  ]);
  const PSALM_TITLE_OFFSET_2 = new Set([60]); // unusually long title (attribution + occasion)

  function psalmTitleOffset(psalmNum) {
    if (PSALM_TITLE_OFFSET_2.has(psalmNum)) return 2;
    if (PSALM_TITLE_OFFSET_1.has(psalmNum)) return 1;
    return 0;
  }

  // ---------- English <-> Hebrew ----------

  function engToHeb(book, chapter, verse) {
    if (book === 19) {
      return { chapter, verse: verse + psalmTitleOffset(chapter) };
    }
    const segs = ENG_HEB_SEGMENTS[book];
    if (segs) {
      for (const s of segs) {
        if (chapter === s.ech && verse >= s.ev0 && verse <= s.ev1) {
          return { chapter: s.hch, verse: s.hv0 + (verse - s.ev0) };
        }
      }
    }
    return { chapter, verse };
  }

  function hebToEng(book, chapter, verse) {
    if (book === 19) {
      const off = psalmTitleOffset(chapter);
      if (verse <= off) return { chapter, verse: 1, isTitle: true };
      return { chapter, verse: verse - off };
    }
    const segs = ENG_HEB_SEGMENTS[book];
    if (segs) {
      for (const s of segs) {
        const hv1 = s.hv0 + (s.ev1 - s.ev0);
        if (chapter === s.hch && verse >= s.hv0 && verse <= hv1) {
          return { chapter: s.ech, verse: s.ev0 + (verse - s.hv0) };
        }
      }
    }
    return { chapter, verse };
  }

  // ---------- Hebrew <-> Greek (Psalms only — LXX merges Ps 9/10, splits
  // Ps 114-116, splits Ps 147, and runs one psalm-number lower than the
  // Hebrew/English from Ps 11 through Ps 146. Every other OT book's LXX
  // chapter/verse numbering matches the Hebrew as used here, except
  // Jeremiah 25-51 and Proverbs 15-31, which reorder material outright
  // and are not remapped — see file header.) ----------

  function hebPsalmToGrk(chapter, verse) {
    if (chapter <= 8) return { chapter, verse };
    if (chapter === 9) return { chapter: 9, verse };
    if (chapter === 10) return { chapter: 9, verse: verse + 21 };
    if (chapter >= 11 && chapter <= 113) return { chapter: chapter - 1, verse };
    if (chapter === 114) return { chapter: 113, verse };
    if (chapter === 115) return { chapter: 113, verse: verse + 8 };
    if (chapter === 116) {
      return verse <= 9 ? { chapter: 114, verse } : { chapter: 115, verse: verse - 9 };
    }
    if (chapter >= 117 && chapter <= 146) return { chapter: chapter - 1, verse };
    if (chapter === 147) {
      return verse <= 11 ? { chapter: 146, verse } : { chapter: 147, verse: verse - 11 };
    }
    return { chapter, verse }; // 148-150 unchanged
  }

  function grkPsalmToHeb(chapter, verse) {
    if (chapter <= 8) return { chapter, verse };
    if (chapter === 9) {
      return verse <= 21 ? { chapter: 9, verse } : { chapter: 10, verse: verse - 21 };
    }
    if (chapter >= 10 && chapter <= 112) return { chapter: chapter + 1, verse };
    if (chapter === 113) {
      return verse <= 8 ? { chapter: 114, verse } : { chapter: 115, verse: verse - 8 };
    }
    if (chapter === 114) return { chapter: 116, verse };
    if (chapter === 115) return { chapter: 116, verse: verse + 9 };
    if (chapter >= 116 && chapter <= 145) return { chapter: chapter + 1, verse };
    if (chapter === 146) return { chapter: 147, verse };
    if (chapter === 147) return { chapter: 147, verse: verse + 11 };
    return { chapter, verse }; // 148-150 unchanged
  }

  function hebToGrk(book, chapter, verse) {
    if (book === 19) return hebPsalmToGrk(chapter, verse);
    return { chapter, verse };
  }

  function grkToHeb(book, chapter, verse) {
    if (book === 19) return grkPsalmToHeb(chapter, verse);
    return { chapter, verse };
  }

  // ---------- Convenience: English <-> "native" (whatever the active
  // display language's own text uses -- Hebrew for OT books, Greek/LXX
  // for OT books shown in Greek mode, straight passthrough for NT/eng) ----------

  function engToNative(book, chapter, verse, lang) {
    if (book > 39 || lang === 'eng') return { chapter, verse };
    const heb = engToHeb(book, chapter, verse);
    if (lang === 'grk') return hebToGrk(book, heb.chapter, heb.verse);
    return heb; // lang === 'heb'
  }

  function nativeToEng(book, chapter, verse, lang) {
    if (book > 39 || lang === 'eng') return { chapter, verse };
    if (lang === 'grk') {
      const heb = grkToHeb(book, chapter, verse);
      return hebToEng(book, heb.chapter, heb.verse);
    }
    return hebToEng(book, chapter, verse); // lang === 'heb'
  }

  // General conversion between any two of 'eng' | 'heb' | 'grk', e.g. for
  // interpreting a typed reference in whichever language a user has
  // selected and converting it to whatever numbering the passage view
  // will display. Hebrew is used as the pivot between English and Greek.
  function convertRef(book, chapter, verse, fromLang, toLang) {
    if (fromLang === toLang || book > 39) return { chapter, verse };
    let heb;
    if (fromLang === 'eng') heb = engToHeb(book, chapter, verse);
    else if (fromLang === 'grk') heb = grkToHeb(book, chapter, verse);
    else heb = { chapter, verse }; // fromLang === 'heb'
    if (toLang === 'heb') return heb;
    if (toLang === 'grk') return hebToGrk(book, heb.chapter, heb.verse);
    if (toLang === 'eng') return hebToEng(book, heb.chapter, heb.verse);
    return heb;
  }

  global.Versification = {
    engToHeb, hebToEng, hebToGrk, grkToHeb, engToNative, nativeToEng,
    convertRef, psalmTitleOffset,
  };
})(typeof window !== 'undefined' ? window : globalThis);
