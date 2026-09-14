// query.js — faithful JS port of src/query.py
// A small parser + evaluator for the BibleWorks-style Command Line grammar
// (subset: AND '.', phrase ''', OR '/', NOT '!', proximity ';N', compound '(...)',
// wildcards * and ?, and morphological lemma@code matching).

(function (global) {
  'use strict';

  function reEscape(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // '*' -> any sequence, '?' -> any single char. Case-insensitive.
  function wildcardToRegex(pattern) {
    const esc = reEscape(pattern).replace(/\\\*/g, '.*').replace(/\\\?/g, '.');
    return new RegExp('^' + esc + '$', 'i');
  }

  // query_code may contain '*', '?' wildcards and the grouping operators
  // '(' ')' '|' for OR-ing sub-patterns, e.g. '((n-)|(ap))*'
  function morphCodeMatches(queryCode, actualCode) {
    let out = [];
    for (let i = 0; i < queryCode.length; i++) {
      const c = queryCode[i];
      if (c === '*') out.push('.*');
      else if (c === '?') out.push('.');
      else if (c === '(' || c === ')' || c === '|') out.push(c);
      else out.push(reEscape(c));
    }
    const pattern = '^' + out.join('') + '$';
    try {
      return new RegExp(pattern, 'i').test(actualCode == null ? '' : actualCode);
    } catch (e) {
      return false;
    }
  }

  class Word {
    constructor(raw) { this.raw = raw; }
    lemmaAndCode() {
      if (this.raw.includes('@')) {
        const idx = this.raw.indexOf('@');
        return [this.raw.slice(0, idx), this.raw.slice(idx + 1)];
      }
      return [this.raw, null];
    }
  }

  class Phrase {
    constructor(words, maxGap) { this.words = words; this.max_gap = maxGap || 0; }
  }

  class And {
    constructor(positive, negative, proximity) {
      this.positive = positive; this.negative = negative;
      this.proximity = (proximity === undefined) ? null : proximity;
    }
  }

  class Or {
    constructor(options) { this.options = options; }
  }

  // Python str.split() semantics: split on runs of whitespace, drop empties,
  // and return [] for an empty/whitespace-only string.
  function pysplit(s) {
    const t = s.trim();
    if (!t) return [];
    return t.split(/\s+/);
  }

  function parse(cmdline) {
    cmdline = cmdline.trim();
    if (cmdline.startsWith('(')) return parseCompound(cmdline);
    if (cmdline.startsWith('.')) return parseAnd(cmdline.slice(1));
    if (cmdline.startsWith('/')) return parseOr(cmdline.slice(1));
    if (cmdline.startsWith("'")) return parsePhrase(cmdline.slice(1));
    throw new Error(`Unrecognized command line start: ${JSON.stringify(cmdline)}`);
  }

  function splitTopLevel(s, sepChars) {
    const parts = [];
    let depth = 0, cur = '';
    for (const c of s) {
      if (c === '(') depth += 1;
      else if (c === ')') depth -= 1;
      if (sepChars.includes(c) && depth === 0) {
        parts.push(cur); cur = '';
      } else {
        cur += c;
      }
    }
    parts.push(cur);
    return parts;
  }

  function parseAnd(s) {
    let prox = null;
    const semiIdx = s.lastIndexOf(';');
    if (semiIdx !== -1) {
      const proxStr = s.slice(semiIdx + 1);
      s = s.slice(0, semiIdx);
      prox = parseInt(proxStr, 10);
    }
    const tokens = pysplit(s);
    const pos = [], neg = [];
    for (const t of tokens) {
      if (t.startsWith('!')) neg.push(new Word(t.slice(1)));
      else pos.push(new Word(t));
    }
    return new And(pos, neg, prox);
  }

  function parseOr(s) {
    return new Or(pysplit(s).map((t) => new Word(t)));
  }

  function parsePhrase(s) {
    const tokens = pysplit(s);
    const words = [];
    let gap = 0;
    for (const t of tokens) {
      const m = /^\*(\d*)$/.exec(t);
      if (m) {
        gap = m[1] ? parseInt(m[1], 10) : 99999; // bare '*' = any number of words
      } else {
        words.push(new Word(t));
      }
    }
    return new Phrase(words, gap);
  }

  function parseCompound(s) {
    let depth = 0, first = null, rest = null;
    for (let i = 0; i < s.length; i++) {
      const c = s[i];
      if (c === '(') depth += 1;
      else if (c === ')') {
        depth -= 1;
        if (depth === 0) {
          first = s.slice(1, i);
          rest = s.slice(i + 1);
          break;
        }
      }
    }
    if (first === null) throw new Error('Unbalanced parentheses');
    const left = parseSubexpr(first);
    if (!rest) return left;
    if (rest.startsWith('.!')) {
      let frag = rest.slice(2);
      if (frag.startsWith('(') && frag.endsWith(')')) frag = frag.slice(1, -1);
      const right = parseSubexpr(frag);
      return new And([left], [right]);
    }
    if (rest.startsWith('.')) {
      const right = parseSubexpr(rest.slice(1));
      return new And([left, right], []);
    }
    if (rest.startsWith('/')) {
      const right = parseSubexpr(rest.slice(1));
      return new Or([left, right]);
    }
    if (/^[0-9]/.test(rest[0] || '') || !rest.startsWith('.')) {
      const m = /^(\d+)/.exec(rest);
      if (m) {
        const n = parseInt(m[1], 10);
        const right = parseSubexpr(rest.slice(m[0].length));
        return new And([left, right], [], n);
      }
    }
    throw new Error(`Unsupported compound continuation: ${JSON.stringify(rest)}`);
  }

  function parseSubexpr(s) {
    s = s.trim();
    if (s.startsWith('(')) return parseCompound(s);
    if (s.startsWith('.')) return parseAnd(s.slice(1));
    if (s.startsWith('/')) return parseOr(s.slice(1));
    if (s.startsWith("'")) return parsePhrase(s.slice(1));
    return parseAnd(s.startsWith('.') ? s : '.' + s);
  }

  global.QueryLib = {
    Word, Phrase, And, Or,
    wildcardToRegex, morphCodeMatches,
    parse, parseSubexpr, splitTopLevel,
  };
})(window);
