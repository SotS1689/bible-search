// fetch-shim.js — intercepts window.fetch calls to '/api/...' (as made
// throughout index.html) and routes them to the in-browser JS port of the
// Flask API, backed by sql.js. Everything else falls through to the real
// fetch(). This lets the rest of index.html's logic run completely
// unmodified.
(function () {
  'use strict';

  const realFetch = window.fetch.bind(window);
  let dbInstance = null;
  let dbLoadStarted = false;

  const overlay = document.createElement('div');
  overlay.id = 'bwLoadOverlay';
  overlay.style.cssText = [
    'position:fixed', 'inset:0', 'z-index:99999',
    'background:#0d1b2e', 'color:#dce8ff',
    'display:flex', 'flex-direction:column', 'align-items:center', 'justify-content:center',
    'font-family:Segoe UI,sans-serif', 'gap:14px',
  ].join(';');
  overlay.innerHTML =
    '<div style="font-size:18px;font-weight:600;letter-spacing:1px;">BIBLESEARCH</div>' +
    '<div style="font-size:13px;color:#7a9abf;" id="bwLoadMsg">Loading corpus database…</div>' +
    '<div style="width:320px;max-width:80vw;height:8px;background:#1a3a6e;border-radius:4px;overflow:hidden;">' +
    '  <div id="bwLoadBar" style="width:0%;height:100%;background:#53d8fb;transition:width .15s;"></div>' +
    '</div>' +
    '<div style="font-size:11px;color:#7a9abf;" id="bwLoadPct">Starting…</div>';

  function ensureOverlay() {
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', ensureOverlay, { once: true });
      return;
    }
    if (!overlay.isConnected) document.body.appendChild(overlay);
  }

  function updateOverlay(loaded, total) {
    ensureOverlay();
    const bar = document.getElementById('bwLoadBar');
    const pct = document.getElementById('bwLoadPct');
    if (total > 0) {
      const shown = Math.min(loaded, total);
      const p = Math.min(100, Math.round((shown / total) * 100));
      if (bar) bar.style.width = p + '%';
      if (pct) pct.textContent = `${p}%  (${(shown / 1e6).toFixed(1)} / ${(total / 1e6).toFixed(1)} MB)`;
    } else if (pct) {
      pct.textContent = `${(loaded / 1e6).toFixed(1)} MB…`;
    }
  }

  function hideOverlay() {
    const msg = document.getElementById('bwLoadMsg');
    if (msg) msg.textContent = 'Ready.';
    if (overlay.isConnected) overlay.remove();
  }

  async function getDb() {
    if (dbInstance) return dbInstance;
    if (!dbLoadStarted) {
      dbLoadStarted = true;
      ensureOverlay();
    }
    dbInstance = await DB.loadDb(updateOverlay);
    hideOverlay();
    return dbInstance;
  }

  function jsonResponse(data) {
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const ROUTES = {
    '/api/search': Api.apiSearch,
    '/api/verse': Api.apiVerse,
    '/api/passage': Api.apiPassage,
    '/api/gloss': Api.apiGloss,
    '/api/books': Api.apiBooks,
    '/api/chapters': Api.apiChapters,
    '/api/translation': Api.apiTranslation,
    '/api/resolve_limit': Api.apiResolveLimit,
  };

  window.fetch = async function (input, init) {
    let urlStr = typeof input === 'string' ? input : (input && input.url) || String(input);
    // Resolve relative URLs against the page location, same as the browser would.
    let url;
    try {
      url = new URL(urlStr, window.location.href);
    } catch (e) {
      return realFetch(input, init);
    }

    const handler = ROUTES[url.pathname];
    if (!handler) {
      return realFetch(input, init);
    }

    try {
      const db = await getDb();
      const data = handler(db, url.searchParams);
      return jsonResponse(data);
    } catch (e) {
      console.error('[fetch-shim]', url.pathname, e);
      return jsonResponse({ error: String((e && e.message) || e) });
    }
  };

  // Kick the DB load off eagerly so the first real search doesn't have to
  // wait for the whole chain to start cold.
  window.addEventListener('DOMContentLoaded', () => { getDb().catch((e) => console.error(e)); });
})();
