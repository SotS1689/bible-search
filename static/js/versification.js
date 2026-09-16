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
//  Jeremiah 25-51: Greek (CATSS/Rahlfs LXX) reorders the oracles-against-
//  the-nations block relative to the Hebrew/English text -- not a simple
//  offset, but a permutation of whole chapters (and a few sub-chapter
//  ranges) mapped explicitly below (JER_HEB_GRK_SEGMENTS). A handful of
//  individual verses genuinely have no CATSS counterpart (e.g. Heb
//  Jeremiah 27:1, 29:16-20) or split across a chapter boundary in a way
//  too fine-grained to map 1:1 (e.g. Heb 25:13-14, 49:36b); for those,
//  hebToGrk/grkToHeb return null rather than a wrong or coincidentally-
//  colliding reference. Primary source: "Table Shewing the Order of
//  Several Chapters and Verses in Jeremiah, as They Appear in the Hebrew
//  and Septuagint Respectively," in L.C.L. Brenton, The Septuagint
//  Version of the Old Testament (Bagster, 1851), via
//  https://www.ccel.org/bible/brenton/Jeremiah/appendix.html (CATSS
//  column); the Jer 49/Grk 30 oracle order was corrected against
//  BibleWorks 10's bgt.vmf versification map and this app's own live
//  Greek text, which both disagreed with Brenton there.
//
//  Proverbs: despite published sources describing LXX Proverbs as
//  reordering chapters 24-31 the way Jeremiah 25-51 is reordered, this
//  app's own CATSS Greek text does NOT show that reorder -- see
//  hebProvToGrk/grkProvToHeb below for what's actually there (one
//  confirmed swap, everything else unchanged).
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

  // Psalms where the Hebrew title is its own separately-numbered verse 1
  // (shifting every body verse after it by this many), rather than being
  // folded into verse 1 together with the start of the actual content the
  // way English translations render it. This is NOT the same question as
  // "does this psalm have a title" -- e.g. Psalm 16's Hebrew verse 1 is
  // "מִכְתָּם לְדָוִד שָׁמְרֵנִי אֵל..." ("A Miktam of David. Preserve me,
  // O God...") in ONE verse, matching English exactly, with no separate
  // title verse at all. Verified empirically against this app's own OSHB
  // (Hebrew) and BLB (English) verse counts per psalm -- a psalm belongs
  // here only where Hebrew genuinely has one more verse than English.
  const PSALM_TITLE_OFFSET_1 = new Set([
    3,4,5,6,7,8,9,12,18,19,20,21,22,30,31,34,36,38,39,40,41,42,44,45,46,47,
    48,49,53,55,56,57,58,59,61,62,63,64,65,67,68,69,70,75,76,77,80,81,83,
    84,85,88,89,92,102,108,140,142,
  ]);
  // Unusually long titles (attribution + occasion) that occupy 2 Hebrew
  // verses, shifting the body by 2 instead of 1 -- also verified against
  // actual Hebrew/English verse counts.
  const PSALM_TITLE_OFFSET_2 = new Set([51,52,54,60]);

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

  // ---------- Hebrew <-> Greek, Jeremiah 25-51 (CATSS/Rahlfs reorders the
  // oracles-against-the-nations block; see file header). Each segment maps
  // a same-length Hebrew verse range to its Greek chapter/verse (verse
  // numbers are usually unchanged, just moved to a different chapter --
  // except the Jer 31/38 vv35-37 reorder and the Jer 49/30 three-way
  // reorder below, which use gv0 to point at the shifted starting verse).
  const JER_HEB_GRK_SEGMENTS = [
    { hch: 25, hv0: 15, hv1: 38, gch: 32, gv0: 15 },
    { hch: 26, hv0: 1,  hv1: 24, gch: 33, gv0: 1 },
    { hch: 27, hv0: 2,  hv1: 6,  gch: 34, gv0: 2 },
    { hch: 27, hv0: 8,  hv1: 12, gch: 34, gv0: 8 },
    { hch: 27, hv0: 14, hv1: 16, gch: 34, gv0: 14 },
    { hch: 27, hv0: 18, hv1: 20, gch: 34, gv0: 18 },
    { hch: 27, hv0: 22, hv1: 22, gch: 34, gv0: 22 },
    { hch: 28, hv0: 1,  hv1: 17, gch: 35, gv0: 1 },
    { hch: 29, hv0: 1,  hv1: 15, gch: 36, gv0: 1 },
    { hch: 29, hv0: 21, hv1: 32, gch: 36, gv0: 21 },
    { hch: 30, hv0: 1,  hv1: 9,  gch: 37, gv0: 1 },
    { hch: 30, hv0: 12, hv1: 14, gch: 37, gv0: 12 },
    { hch: 30, hv0: 16, hv1: 21, gch: 37, gv0: 16 },
    { hch: 30, hv0: 23, hv1: 24, gch: 37, gv0: 23 },
    { hch: 31, hv0: 1,  hv1: 34, gch: 38, gv0: 1 },
    { hch: 31, hv0: 35, hv1: 35, gch: 38, gv0: 36 }, // Heb 35,36,37 -> Grk 36,37,35
    { hch: 31, hv0: 36, hv1: 36, gch: 38, gv0: 37 },
    { hch: 31, hv0: 37, hv1: 37, gch: 38, gv0: 35 },
    { hch: 31, hv0: 38, hv1: 40, gch: 38, gv0: 38 },
    { hch: 32, hv0: 1,  hv1: 44, gch: 39, gv0: 1 },
    { hch: 33, hv0: 1,  hv1: 13, gch: 40, gv0: 1 },
    { hch: 34, hv0: 1,  hv1: 22, gch: 41, gv0: 1 },
    { hch: 35, hv0: 1,  hv1: 19, gch: 42, gv0: 1 },
    { hch: 36, hv0: 1,  hv1: 32, gch: 43, gv0: 1 },
    { hch: 37, hv0: 1,  hv1: 21, gch: 44, gv0: 1 },
    { hch: 38, hv0: 1,  hv1: 28, gch: 45, gv0: 1 },
    { hch: 39, hv0: 1,  hv1: 3,  gch: 46, gv0: 1 },
    { hch: 39, hv0: 14, hv1: 18, gch: 46, gv0: 14 },
    { hch: 40, hv0: 1,  hv1: 16, gch: 47, gv0: 1 },
    { hch: 41, hv0: 1,  hv1: 18, gch: 48, gv0: 1 },
    { hch: 42, hv0: 1,  hv1: 22, gch: 49, gv0: 1 },
    { hch: 43, hv0: 1,  hv1: 13, gch: 50, gv0: 1 },
    { hch: 44, hv0: 1,  hv1: 30, gch: 51, gv0: 1 },
    { hch: 45, hv0: 1,  hv1: 5,  gch: 51, gv0: 31 },
    { hch: 46, hv0: 2,  hv1: 25, gch: 26, gv0: 2 },
    { hch: 46, hv0: 27, hv1: 28, gch: 26, gv0: 27 },
    { hch: 47, hv0: 1,  hv1: 7,  gch: 29, gv0: 1 },
    { hch: 48, hv0: 1,  hv1: 44, gch: 31, gv0: 1 },
    { hch: 49, hv0: 1,  hv1: 6,  gch: 30, gv0: 17 }, // Ammon
    { hch: 49, hv0: 7,  hv1: 22, gch: 30, gv0: 1 },  // Edom
    { hch: 49, hv0: 23, hv1: 27, gch: 30, gv0: 29 }, // Damascus
    { hch: 49, hv0: 28, hv1: 33, gch: 30, gv0: 23 }, // Kedar/Hazor
    { hch: 49, hv0: 34, hv1: 34, gch: 25, gv0: 20 },
    { hch: 49, hv0: 35, hv1: 39, gch: 25, gv0: 15 },
    { hch: 50, hv0: 1,  hv1: 46, gch: 27, gv0: 1 },
    { hch: 51, hv0: 1,  hv1: 64, gch: 28, gv0: 1 },
  ];

  // Jer 1-24 (minus the ch8/9 boundary, handled by ENG_HEB_SEGMENTS), Jer
  // 25:1-13, and Jer 52 are unaffected by the reorder and pass through
  // unchanged; Jer 25:14-51:64 is the range CATSS actually permutes, so a
  // verse in that range with no matching segment above genuinely has no
  // CATSS counterpart -- see file header.
  function hebJerToGrk(chapter, verse) {
    if (chapter < 25 || chapter > 51) return { chapter, verse };
    if (chapter === 25 && verse <= 13) return { chapter, verse };
    for (const s of JER_HEB_GRK_SEGMENTS) {
      if (chapter === s.hch && verse >= s.hv0 && verse <= s.hv1) {
        return { chapter: s.gch, verse: s.gv0 + (verse - s.hv0) };
      }
    }
    return null;
  }

  function grkJerToHeb(chapter, verse) {
    if (chapter < 25 || chapter > 51) return { chapter, verse };
    if (chapter === 25 && verse <= 13) return { chapter, verse };
    for (const s of JER_HEB_GRK_SEGMENTS) {
      const gv1 = s.gv0 + (s.hv1 - s.hv0);
      if (chapter === s.gch && verse >= s.gv0 && verse <= gv1) {
        return { chapter: s.hch, verse: s.hv0 + (verse - s.gv0) };
      }
    }
    return null;
  }

  // ---------- Hebrew <-> Greek, Proverbs. Hebrew chapters 1-24 and 30-31
  // keep their ordinary numbering in Greek. Hebrew 25-29 ("these also are
  // proverbs of Solomon, which the men of Hezekiah... copied out") is
  // relocated as a block to the END of the Greek book, after chs 30
  // (Agur) and 31 (Lemuel) -- Grk 32-36, same verse numbers, a clean +7
  // chapter offset (verified against this app's own live CATSS Greek
  // text: Grk 32:1-36:end match Heb 25:1-29:end verse-for-verse, and
  // 25-29 have no Greek text at all under their own chapter numbers).
  // Within the untouched 30-31 range there's one confirmed verse swap at
  // 31:25/26. A few other spots BibleWorks 10's bgt.vmf versification map
  // flags (Prov 1:10-11, 3:3-4, 11:10-11, 16:6-9, 22:8-9, 31:27-28)
  // turned out on inspection to either match the Hebrew numbering exactly
  // already or involve a genuine LXX doublet/plus-verse with no single
  // clean Hebrew counterpart -- left unmapped like Jeremiah's own
  // single-verse gaps, see file header.
  function hebProvToGrk(chapter, verse) {
    if (chapter >= 25 && chapter <= 29) return { chapter: chapter + 7, verse };
    if (chapter === 31 && verse === 25) return { chapter: 31, verse: 26 };
    if (chapter === 31 && verse === 26) return { chapter: 31, verse: 25 };
    return { chapter, verse };
  }

  function grkProvToHeb(chapter, verse) {
    if (chapter >= 32 && chapter <= 36) return { chapter: chapter - 7, verse };
    if (chapter === 31 && verse === 25) return { chapter: 31, verse: 26 };
    if (chapter === 31 && verse === 26) return { chapter: 31, verse: 25 };
    return { chapter, verse };
  }

  // ---------- Hebrew <-> Greek (Psalms — LXX merges Ps 9/10, splits
  // Ps 114-116, splits Ps 147, and runs one psalm-number lower than the
  // Hebrew/English from Ps 11 through Ps 146; Jeremiah 25-51 — see
  // hebJerToGrk/grkJerToHeb above; Proverbs — see hebProvToGrk/
  // grkProvToHeb above. Every other OT book's LXX chapter/verse numbering
  // matches the Hebrew as used here.) ----------

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
    if (book === 20) return hebProvToGrk(chapter, verse);
    if (book === 24) return hebJerToGrk(chapter, verse);
    return { chapter, verse };
  }

  function grkToHeb(book, chapter, verse) {
    if (book === 19) return grkPsalmToHeb(chapter, verse);
    if (book === 20) return grkProvToHeb(chapter, verse);
    if (book === 24) return grkJerToHeb(chapter, verse);
    return { chapter, verse };
  }

  // ---------- Convenience: English <-> "native" (whatever the active
  // display language's own text uses -- Hebrew for OT books, Greek/LXX
  // for OT books shown in Greek mode, straight passthrough for NT/eng) ----------

  // hebToGrk/grkToHeb can return null for a Hebrew/Greek Jeremiah verse
  // with no counterpart in the other language's numbering (see file
  // header) -- these convenience wrappers surface that as a `noEnglish` /
  // `noNative` flag rather than crash, so callers can skip rendering a
  // translation line for that verse instead of guessing.

  function engToNative(book, chapter, verse, lang) {
    if (book > 39 || lang === 'eng') return { chapter, verse };
    const heb = engToHeb(book, chapter, verse);
    if (lang === 'grk') {
      const grk = hebToGrk(book, heb.chapter, heb.verse);
      return grk || { chapter: heb.chapter, verse: heb.verse, noNative: true };
    }
    return heb; // lang === 'heb'
  }

  function nativeToEng(book, chapter, verse, lang) {
    if (book > 39 || lang === 'eng') return { chapter, verse };
    if (lang === 'grk') {
      const heb = grkToHeb(book, chapter, verse);
      if (!heb) return { chapter, verse, noEnglish: true };
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
    else if (fromLang === 'grk') heb = grkToHeb(book, chapter, verse) || { chapter, verse };
    else heb = { chapter, verse }; // fromLang === 'heb'
    if (toLang === 'heb') return heb;
    if (toLang === 'grk') return hebToGrk(book, heb.chapter, heb.verse) || heb;
    if (toLang === 'eng') return hebToEng(book, heb.chapter, heb.verse);
    return heb;
  }

  global.Versification = {
    engToHeb, hebToEng, hebToGrk, grkToHeb, engToNative, nativeToEng,
    convertRef, psalmTitleOffset,
  };
})(typeof window !== 'undefined' ? window : globalThis);
