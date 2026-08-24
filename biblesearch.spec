# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all

datas = [('static', 'static'), ('data', 'data'), ('src', 'src')]
binaries = []
hiddenimports = ['flask', 'werkzeug', 'xml.etree.ElementTree', 'waitress']

for pkg in ('flask', 'waitress', 'webview'):
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# pywebview's actual backend module needed is platform-specific, and each
# one pulls in packages that only exist/matter on that OS -- so this is
# built once here per-branch, and each CI runner (Windows/Mac/Linux) only
# ever executes its own branch when it builds from this same spec file.
if sys.platform.startswith('linux'):
    hiddenimports += ['gi', 'gi.repository.Gtk', 'gi.repository.WebKit2']
elif sys.platform == 'win32':
    hiddenimports += ['clr_loader', 'pythonnet']
elif sys.platform == 'darwin':
    hiddenimports += ['objc', 'Foundation', 'AppKit', 'WebKit', 'Quartz']


a = Analysis(
    ['launch.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='biblesearch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
