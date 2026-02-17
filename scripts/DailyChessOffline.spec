# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all PySide6 modules, binaries, and data files
pyside6_datas = []
pyside6_binaries = []
pyside6_hiddenimports = []

tmp_ret = collect_all('PySide6')
pyside6_datas += tmp_ret[0]
pyside6_binaries += tmp_ret[1]
pyside6_hiddenimports += tmp_ret[2]

# Collect chess submodules
chess_hiddenimports = collect_submodules('chess')

# Collect SQLAlchemy submodules
sqlalchemy_hiddenimports = collect_submodules('sqlalchemy')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=pyside6_binaries,
    datas=[('dco', 'dco')] + pyside6_datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'shiboken6',
    ] + pyside6_hiddenimports + chess_hiddenimports + sqlalchemy_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas'],  # Exclude heavy unused packages
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DailyChessOffline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DailyChessOffline',
)
