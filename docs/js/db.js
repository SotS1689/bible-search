// db.js — loads sql.js (WebAssembly SQLite) and the corpus database.
//
// Loading strategy: corpus.db (~134MB) is bundled *same-origin* inside this
// site as three chunk files under data/ (split so no single git blob
// exceeds GitHub's 100MB limit). We tried sql.js-httpvfs streaming against
// the GitHub Releases asset URL first (see docs/README.md for details) but
// GitHub's release-asset CDN does not send CORS headers, so browser fetch()
// — ranged or not — is blocked cross-origin. Serving the bytes from the
// same origin as the page sidesteps CORS entirely; we fetch all chunks
// (small enough to be practical), concatenate them, and hand the buffer to
// plain sql.js, which loads the whole database into an in-memory VFS.
(function (global) {
  'use strict';

  const CHUNK_URLS = [
    'data/corpus.db.part00',
    'data/corpus.db.part01',
    'data/corpus.db.part02',
  ];

  let dbPromise = null;

  async function fetchWithProgress(url, onBytes) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch ${url}: HTTP ${res.status}`);
    const total = Number(res.headers.get('Content-Length')) || 0;
    if (!res.body || !res.body.getReader) {
      // Fallback for environments without streaming fetch bodies.
      const buf = new Uint8Array(await res.arrayBuffer());
      if (onBytes) onBytes(buf.length, total || buf.length);
      return buf;
    }
    const reader = res.body.getReader();
    const chunks = [];
    let received = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      received += value.length;
      if (onBytes) onBytes(received, total);
    }
    const out = new Uint8Array(received);
    let offset = 0;
    for (const c of chunks) { out.set(c, offset); offset += c.length; }
    return out;
  }

  async function loadDb(onProgress) {
    if (dbPromise) return dbPromise;
    dbPromise = (async () => {
      const SQL = await initSqlJs({ locateFile: (f) => 'vendor/' + f });

      const perChunkLoaded = new Array(CHUNK_URLS.length).fill(0);
      const perChunkTotal = new Array(CHUNK_URLS.length).fill(0);
      function report() {
        if (!onProgress) return;
        const loaded = perChunkLoaded.reduce((a, b) => a + b, 0);
        const total = perChunkTotal.reduce((a, b) => a + b, 0);
        onProgress(loaded, total);
      }

      const buffers = [];
      for (let i = 0; i < CHUNK_URLS.length; i++) {
        const buf = await fetchWithProgress(CHUNK_URLS[i], (loaded, total) => {
          perChunkLoaded[i] = loaded;
          perChunkTotal[i] = total || loaded;
          report();
        });
        buffers.push(buf);
      }
      const totalLen = buffers.reduce((s, b) => s + b.length, 0);
      const merged = new Uint8Array(totalLen);
      let offset = 0;
      for (const b of buffers) { merged.set(b, offset); offset += b.length; }

      const db = new SQL.Database(merged);
      return db;
    })();
    return dbPromise;
  }

  function tableExists(db, name) {
    const stmt = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name=?");
    stmt.bind([name]);
    const found = stmt.step();
    stmt.free();
    return found;
  }

  function queryAll(db, sql, params) {
    const stmt = db.prepare(sql);
    if (params && params.length) stmt.bind(params);
    const rows = [];
    while (stmt.step()) rows.push(stmt.getAsObject());
    stmt.free();
    return rows;
  }

  function queryOne(db, sql, params) {
    const rows = queryAll(db, sql, params);
    return rows.length ? rows[0] : null;
  }

  global.DB = { loadDb, tableExists, queryAll, queryOne };
})(window);
