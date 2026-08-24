# BibleSearch — desktop distribution

Packages the existing Flask app + a prebuilt `corpus.db` into a single
double-clickable executable per platform (Windows/macOS/Linux), via
PyInstaller. No server, no account, no ongoing cost, works offline forever.

## One-time setup (you, before the first release)

1. **Host `corpus.db` somewhere CI can fetch it.** It's 129MB, which is
   over GitHub's 100MB hard limit for files committed directly to a repo,
   so it can't just live in the repo. Easiest free option:
   - Create a GitHub Release in this repo (any tag name works, e.g.
     `corpus-v1`) and upload `corpus.db` to it as a release asset
     (Releases allow files up to 2GB, and asset downloads for public
     repos aren't bandwidth-limited the way Git LFS is).
   - Copy that asset's download URL.
   - Paste it into `CORPUS_DB_URL` near the top of
     `.github/workflows/build.yml`.
2. Push this repo to GitHub.
3. Tag a release: `git tag v1.0.0 && git push origin v1.0.0`. GitHub
   Actions will build all three platforms and attach them to the Release
   automatically. Manual re-runs (no tag needed) are available from the
   Actions tab -> "Run workflow"; those builds show up under that run's
   Artifacts instead of a Release.

If `corpus.db` ever changes, upload the new version as a new release
asset and update `CORPUS_DB_URL` (or reuse the same asset URL if you
just overwrite the same release's asset).

## Building locally (any one platform, for testing)

```bash
pip install -r requirements.txt
# put your corpus.db at data/corpus.db first
pyinstaller biblesearch.spec
./dist/biblesearch          # or dist\biblesearch.exe on Windows
```

PyInstaller does **not** cross-compile — a Windows build must run on
Windows, a macOS build on macOS. That's exactly what the GitHub Actions
matrix in `build.yml` is for: it builds all three from one push, for free.

## What users actually do

Download the file matching their OS, double-click it. A native app window
opens directly (no browser, no console/terminal) with the app already
loaded. Closing that window quits the app — that's the only quit gesture
now, there's no console to close instead.

**Expect one security prompt on first run**, since these are unsigned
binaries:
- **Windows:** SmartScreen says "Windows protected your PC" -> "More
  info" -> "Run anyway".
- **macOS:** Gatekeeper blocks it outright the first time -> System
  Settings -> Privacy & Security -> "Open Anyway" (or right-click the
  file -> Open, which offers the bypass directly).

Removing this prompt requires paying for a code-signing certificate
(~$99/yr for Apple, similar for Windows), which conflicts with the
zero-ongoing-cost goal, so it's left as a one-time click-through and
documented here instead.

**Linux only:** the native window needs WebKit2GTK present on the user's
machine (most desktop Linux distros already have it, since a lot of
GTK-based apps depend on it — but it's not guaranteed on a minimal/server
install). If the app fails to open on someone's Linux machine, that's the
first thing to check; the fix is just installing their distro's
`webkit2gtk` package (e.g. `sudo apt install gir1.2-webkit2-4.1` on
Ubuntu/Debian).

**If something goes wrong on someone's machine:** since there's no
console anymore, errors don't print anywhere visible. A log file
(`biblesearch.log`) is written next to the executable instead, and a
small error popup appears on a fatal startup failure telling the user
where to find it.

## Design notes / what changed from the original app

- `src/corpus.py` and `app.py`: path resolution now checks
  `sys.frozen`/`sys._MEIPASS` so bundled `data/`, `src/`, and `static/`
  resolve correctly whether running as `python app.py` or as a frozen
  PyInstaller executable. No behavior change in normal (non-frozen) use.
- `app.py`'s `/api/resolve_limit` had a redundant, PyInstaller-unsafe
  re-computation of `sys.path`; removed (the top-of-file setup already
  covers it).
- `launch.py`: serves the app via **Waitress** (a real production WSGI
  server) instead of Flask's built-in dev server, and opens it in a
  **native app window via pywebview** instead of a browser tab. Startup
  is wrapped in a try/except that logs to `biblesearch.log` next to the
  executable and shows a native error dialog on fatal failure, since
  `console=False` means there's no terminal for errors to print to.
- `static/index.html`: every `localStorage` call now goes through small
  `lsGet`/`lsSet`/`lsRemove` wrapper functions (see near the top of the
  script) instead of calling `localStorage` directly. This mattered in
  practice, not just in theory: pywebview's Linux (GTK/WebKit2GTK) window
  doesn't expose `localStorage` as a global at all, and the app used to
  call it directly and unprotected at the very top of page load (theme/
  font preference restoration) — that threw immediately and silently
  prevented the rest of the page's startup code from running at all. The
  wrappers degrade to "preferences just don't persist" instead.
- `biblesearch.spec`: `console=False` (no terminal window), plus
  platform-specific hidden-imports pywebview's backend needs on each OS
  (GTK/WebKit2 on Linux, pythonnet/WebView2 on Windows, PyObjC/Cocoa on
  Mac) — see the comments in the spec file itself.
- `.github/workflows/build.yml`: the Linux runner now installs
  WebKit2GTK's build/runtime GObject-introspection packages before
  `pip install`, since PyGObject (pywebview's Linux backend dependency)
  needs the dev headers present to build, and the actual `.typelib`
  bindings to run.

## Known limits worth knowing about

- Onefile executables unpack to a temp directory on every launch (a few
  seconds of startup delay, more noticeable on first run of the session).
  If startup time matters more than a single-file download, PyInstaller's
  `--onedir` mode instead ships a folder (faster start, more files to
  distribute) — a one-line change to `biblesearch.spec` if you want to
  compare.
- No auto-update mechanism. New corpus or code = new tag = new release;
  users re-download manually.
- The Windows and macOS builds are validated by their own CI runs, not by
  me directly (I can only build/run the Linux target myself) — their
  native webview components ship with the OS already, so they're expected
  to work, but if either build fails or misbehaves, the Actions log and
  the platform-specific hidden-imports section in `biblesearch.spec` are
  the first places to look.
