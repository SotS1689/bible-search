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

Download the file matching their OS, double-click it. A terminal/console
window opens (this is intentional — see below) and their browser opens to
the app a moment later. Closing the console window stops the app.

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

## Design notes / what changed from the original app

- `src/corpus.py` and `app.py`: path resolution now checks
  `sys.frozen`/`sys._MEIPASS` so bundled `data/`, `src/`, and `static/`
  resolve correctly whether running as `python app.py` or as a frozen
  PyInstaller executable. No behavior change in normal (non-frozen) use.
- `app.py`'s `/api/resolve_limit` had a redundant, PyInstaller-unsafe
  re-computation of `sys.path`; removed (the top-of-file setup already
  covers it).
- `launch.py` is new: starts the Flask app in a background thread, picks
  a free port if 7070 is taken, and opens the user's default browser.
  This is the PyInstaller entry point (not `app.py` directly), so users
  get an "app that opens," not a bare dev server they have to visit
  manually.
- The console window is left visible on purpose for v1: if something
  goes wrong, the user (or you, over their shoulder) can actually see the
  traceback instead of the app silently failing to open. Switching to
  `console=False` in `biblesearch.spec` later is a one-line change once
  you're confident in stability, at the cost of hiding errors from users
  entirely.

## Known limits worth knowing about

- Onefile executables unpack to a temp directory on every launch (a few
  seconds of startup delay, more noticeable on first run of the session).
  If startup time matters more than a single-file download, PyInstaller's
  `--onedir` mode instead ships a folder (faster start, more files to
  distribute) — a one-line change to `biblesearch.spec` if you want to
  compare.
- No auto-update mechanism. New corpus or code = new tag = new release;
  users re-download manually.
