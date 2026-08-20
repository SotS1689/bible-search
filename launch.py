"""
Desktop launcher for BibleSearch.

Starts the existing Flask app (unmodified route logic) on a local port and
opens it in the user's default browser -- so double-clicking the packaged
executable feels like opening an application, not running a server.

Not meant to be imported; this is the PyInstaller entry point.
"""
import sys, os, socket, threading, time, webbrowser

# Same frozen/non-frozen root resolution as app.py and src/corpus.py use.
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))

from app import app  # noqa: E402  (import after sys.path setup, intentional)

PREFERRED_PORT = 7070


def _free_port(preferred):
    """Return `preferred` if it's open, otherwise let the OS hand out any
    free port. Avoids a hard failure if something else is already bound
    to 7070 (e.g. the user has two copies running, or a dev server up)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', preferred))
            return preferred
        except OSError:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]


def _run_server(port):
    # use_reloader must stay off: the reloader re-execs the process, which
    # breaks PyInstaller onefile bundles (it tries to re-launch a python.exe
    # that doesn't exist in a frozen build).
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


def main():
    port = _free_port(PREFERRED_PORT)
    t = threading.Thread(target=_run_server, args=(port,), daemon=True)
    t.start()

    # Give Flask a moment to bind before pointing the browser at it.
    time.sleep(0.8)
    url = f'http://127.0.0.1:{port}/'
    print(f'BibleSearch running at {url}  (close this window to stop it)')
    webbrowser.open(url)

    try:
        t.join()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
