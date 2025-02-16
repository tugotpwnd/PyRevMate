# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ("Dict/AttributeDictionary.json5", "Dict"),
        ('assets/PyRevMateLogo.ico', 'assets'),  # Include the JSON5 file in the build
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebSockets',
        'PyQt5.QtNetwork',
        'PyQt5.QtSensors',
        'PyQt5.QtPositioning',
        'PyQt5.QtQuick',
        'PyQt5.QtPrintSupport',
        'matplotlib',
        'scipy',
    ],
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
    name='PyRevMateV_1.8',
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
    icon='assets/PyRevMateLogo.ico',  # Path to the .ico file for the executable and tray icon
)

# Use COLLECT instead of a single-file EXE
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="PyRevMateV_1.8",
)
