# BibleWorks Search — static build (GitHub Pages)

This folder is a fully static port of the Flask app in the repo root. It
needs no server at runtime — everything (search parsing, morphological
matching, Greek transliteration, Hebrew lemma resolution) runs client-side
in the browser against an in-page copy of `corpus.db`, loaded via
[sql.js](https://github.com/sql-js/sql.js) (SQLite compiled to WebAssembly).

## How it differs from the Flask app

* **No backend.** `app.py` and `src/*.py` are untouched and still work as
  the desktop/local-server build. This `docs/` folder is a separate,
  parallel build meant for GitHub Pages.
* **`index.html` is byte-for-byte the same UI**, except for one small
  insertion: a handful of `<script>` tags before the app's own script that
  load sql.js and a JS port of the Python search/query logic, then install
  a `window.fetch` override that intercepts every `fetch('/api/...')` call
  the page makes and answers it locally instead of hitting a server. The
  rest of `index.html`'s ~2300 lines of UI logic are unmodified.
* **The Python route handlers were ported to JavaScript** in `docs/js/`:
  - `query.js` — the BibleWorks-style command-line parser (`.`/`/`/`'`/`!`/`;N`
    grammar, wildcards, morph-code matching) — ports `src/query.py`.
  - `greek_translit.js` — BW-keyboard Latin → Greek transliteration and
    accent stripping — ports `src/greek_translit.py`.
  - `hebrew_util.js` — Hebrew-text detection and niqqud/cantillation
    stripping — ports the Hebrew helpers in `src/search.py`.
  - `books.js` — book name/abbreviation resolution, the `l`(imit) command,
    and the book-number → display-name tables — ports `src/books.py` and
    the `BOOK_NAMES`/`EDITION_LABELS` tables from `src/corpus.py` and
    `app.py`.
  - `search.js` — the Greek/Hebrew morphological search evaluator
    (`eval_ast`, phrase/proximity matching, highlight-term collection) and
    the English (BLB) search — ports `src/search.py` and app.py's
    `_search_english_inline`.
  - `api.js` — one function per Flask route (`/api/search`, `/api/verse`,
    `/api/passage`, `/api/gloss`, `/api/books`, `/api/chapters`,
    `/api/translation`, `/api/resolve_limit`), each returning the exact
    JSON shape the Flask endpoint used to return.
  - `db.js` — loads sql.js and the corpus database.
  - `fetch-shim.js` — the `window.fetch` override that routes `/api/*`
    requests to `api.js` and returns a `Response` wrapping the JSON.

## Database loading strategy — what we tried, what actually works

The plan was to stream `corpus.db` on demand via
[sql.js-httpvfs](https://github.com/phiresky/sql.js-httpvfs), using HTTP
Range requests against the existing GitHub Releases asset
(`https://github.com/SotS1689/bible-search/releases/download/corpus-v1/corpus.db`),
so the browser would only fetch the ~KB-sized SQLite pages it actually
touches instead of the whole 134 MB file.

**That does not work**, and not because of range-request support — GitHub's
release-asset CDN (it redirects to a signed Azure Blob Storage URL on
`release-assets.githubusercontent.com`) *does* support `Range` correctly
(verified: a ranged `GET` returns `206 Partial Content` with a correct
`Content-Range` header). The blocker is **CORS**: the response carries no
`Access-Control-Allow-Origin` header at all, and an `OPTIONS` preflight
against it returns `405 Method Not Allowed`. A browser `fetch()` from a
`github.io` origin (or any other origin) to that URL is therefore blocked
by the browser before JavaScript ever sees the response — for *any* cross-
origin fetch, ranged or not. So even the plain "fall back to downloading
the whole file" strategy doesn't work against that URL.

**What this build does instead:** the corpus database is bundled directly
in this `docs/` folder (same origin as the page), split into three ~45 MB
chunk files under `docs/data/` — `corpus.db.part00/01/02` — because GitHub
blocks any single git blob over 100 MB and the database is ~134 MB. On
page load, `db.js` fetches all three chunks (same-origin, so no CORS issue
whatsoever), concatenates them into one buffer, and hands it to sql.js's
`SQL.Database()`, which loads the whole thing into an in-memory SQLite
instance. A progress overlay shows download progress (tracked via
`Content-Length` and streamed `ReadableStream` reads) while this happens.

This means **the whole ~134 MB download happens once per browser
session** (cached by the browser's HTTP cache on repeat visits, same-origin
so no CORS friction) rather than being streamed page-by-page — it is the
"fall back to a full-file download" strategy the task anticipated, just
serving the bytes from the Pages origin instead of the (CORS-blocked)
Releases URL. If a future truly-lazy load is wanted, the path forward is
either (a) getting CORS headers added in front of the release asset (e.g.
a Cloudflare Worker / small proxy that adds `Access-Control-Allow-Origin`
and passes through `Range`), or (b) implementing a custom sql.js VFS that
does random-access reads across the three same-origin chunk files (plain
sql.js-httpvfs only understands a single URL).

## Updating `corpus.db`

If `data/corpus.db` is rebuilt (e.g. `python src/corpus.py` in the repo
root), regenerate the static build's chunks from the new file:

```sh
cd bible-search-repo
split -b 45m -d -a 2 data/corpus.db docs/data/corpus.db.part
```

This produces `corpus.db.part00`, `part01`, `part02`, ... — if the file's
size changes enough to add/remove a chunk, also update the `CHUNK_URLS`
list at the top of `docs/js/db.js` to match the new filenames.

## Vendored dependencies

`docs/vendor/sql-wasm.js` and `docs/vendor/sql-wasm.wasm` are sql.js
1.10.3's WASM build, vendored locally (rather than loaded from a CDN) so
the site has no runtime dependency on a third party.

## Deploying

1. Push this branch (or merge it into `main`) to the `SotS1689/bible-search`
   remote.
2. In the repo's GitHub settings: **Settings → Pages → Build and
   deployment → Source: "Deploy from a branch"**, then pick branch
   `main`, folder **`/docs`**, and save.
3. GitHub will publish the site at `https://sots1689.github.io/bible-search/`
   (or a custom domain if configured). No build step is required — `docs/`
   is served as-is.

## Testing locally

Any static file server that serves `docs/` with correct MIME types works,
e.g.:

```sh
cd docs
python -m http.server 8000
```

then open `http://localhost:8000/`. (A `file://` URL will *not* work —
`fetch()` of the `data/corpus.db.part*` chunks requires an HTTP origin.)
