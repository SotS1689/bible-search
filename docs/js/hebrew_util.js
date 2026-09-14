// hebrew_util.js — JS port of the Hebrew helpers in src/search.py
(function (global) {
  'use strict';

  function isHebrewText(s) {
    for (const c of s) {
      const cp = c.codePointAt(0);
      if (cp >= 0x05D0 && cp <= 0x05EA) return true;
    }
    return false;
  }

  // search.py's strip_niqqud: NFD-normalize and drop all Unicode category
  // Mn (nonspacing mark) characters, then lowercase. In practice, for Hebrew
  // input the only Mn characters present are Hebrew points/cantillation
  // marks (U+0591-05BD, 05BF, 05C1-05C2, 05C4-05C5, 05C7), so restricting
  // the strip to that block is equivalent for real Hebrew search terms.
  function stripNiqqud(s) {
    const nfd = s.normalize('NFD');
    const bare = nfd.replace(/[֑-ׇֽֿׁׂׅׄ]/g, '');
    return bare.toLowerCase();
  }

  global.HebrewUtil = { isHebrewText, stripNiqqud };
})(window);
