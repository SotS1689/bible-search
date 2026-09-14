// greek_translit.js — JS port of src/greek_translit.py
(function (global) {
  'use strict';

  const LATIN_TO_GREEK = {
    a: 'α', b: 'β', g: 'γ', d: 'δ', e: 'ε', z: 'ζ', h: 'η',
    q: 'θ', i: 'ι', k: 'κ', l: 'λ', m: 'μ', n: 'ν', x: 'ξ',
    o: 'ο', p: 'π', r: 'ρ', s: 'σ', t: 'τ', u: 'υ', f: 'φ',
    c: 'χ', y: 'ψ', w: 'ω', j: 'σ', // j = final sigma -> normalize to sigma
  };

  function translitQueryToGreek(s) {
    let out = '';
    for (const ch of s) {
      const lower = ch.toLowerCase();
      out += Object.prototype.hasOwnProperty.call(LATIN_TO_GREEK, lower) ? LATIN_TO_GREEK[lower] : ch;
    }
    return out;
  }

  // Normalize accented Unicode Greek to bare lowercase letters (NFD strip
  // combining marks in the Combining Diacritical Marks block, which is
  // where Greek accents/breathings/iota-subscript decompose to), and fold
  // final sigma 'ς' to 'σ'.
  function stripAccentsLower(greek) {
    const nfd = greek.normalize('NFD');
    const bare = nfd.replace(/[̀-ͯ]/g, '');
    return bare.toLowerCase().replace(/ς/g, 'σ');
  }

  global.GreekTranslit = { LATIN_TO_GREEK, translitQueryToGreek, stripAccentsLower };
})(window);
