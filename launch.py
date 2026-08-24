"""
Desktop launcher for BibleSearch.

Starts the existing Flask app (unmodified route logic) behind Waitress (a
real production WSGI server -- no more "development server" warning), then
opens it in a native app window via pywebview instead of a browser tab.
Closing that window is the app's quit gesture.

Because the packaged executable is built with console=False (no visible
terminal), nothing printed here is visible to the user in normal use --
so startup is wrapped in a broad try/except that writes any failure to a
log file next to the executable and shows a native error dialog, instead
of the app just silently failing to appear.

Not meant to be imported; this is the PyInstaller entry point.
"""
import sys, os, socket, threading, time, logging, traceback

# Same frozen/non-frozen root resolution as app.py and src/corpus.py use.
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    ROOT = sys._MEIPASS
    # Bundled data (src/static/data) lives in _MEIPASS, but the *log file*
    # should sit next to the actual executable so it's easy for a user to
    # find -- _MEIPASS is a temp dir that vanishes when the app closes.
    LOG_DIR = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))
    LOG_DIR = ROOT
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))

LOG_PATH = os.path.join(LOG_DIR, 'biblesearch.log')
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
log = logging.getLogger('biblesearch')

PREFERRED_PORT = 7070


def _free_port(preferred):
    """Return `preferred` if it's open, otherwise let the OS hand out any
    free port. Avoids a hard failure if something else is already bound
    to 7070 (e.g. the user has two copies running)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', preferred))
            return preferred
        except OSError:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]


def _run_server(app, port):
    from waitress import serve
    serve(app, host='127.0.0.1', port=port, _quiet=True)


def _show_error_dialog(message):
    """Best-effort native error popup. tkinter is in the Python standard
    library, so this doesn't add a dependency, but it can still fail on a
    truly broken environment -- in which case the log file is the actual
    fallback, and this just logs that the dialog itself didn't work."""
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror('BibleSearch', message)
        root.destroy()
    except Exception:
        log.error('Could not show error dialog: %s', traceback.format_exc())


def main():
    from app import app as flask_app

    port = _free_port(PREFERRED_PORT)
    t = threading.Thread(target=_run_server, args=(flask_app, port), daemon=True)
    t.start()

    # Give Waitress a moment to bind before pointing the window at it.
    time.sleep(0.8)
    url = f'http://127.0.0.1:{port}/'
    log.info('Serving at %s', url)

    import webview
    webview.create_window('BibleSearch', url, width=1400, height=900, min_size=(700, 500))
    webview.start()  # blocks until the window is closed; that's the app's quit gesture
    log.info('Window closed, exiting.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        log.error('Fatal error on startup:\n%s', tb)
        _show_error_dialog(
            'BibleSearch could not start.\n\n'
            f'Details were written to:\n{LOG_PATH}'
        )
        sys.exit(1)
