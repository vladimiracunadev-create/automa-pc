# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para Automa desktop app.

Construye un one-folder bundle en dist/Automa/ con el binario Automa.exe
como launcher. Incluye:
  - flows/ y schemas/ (datafiles necesarios en runtime).
  - hidden imports de los modulos de acciones (cargados via entry-points).
  - hooks de pywebview/mss/pyautogui/pyperclip/pygetwindow.

Build local (desde la raiz del repo):
    pyinstaller installer/automa.spec --noconfirm

CI Windows (windows-latest, ver .github/workflows/release.yml):
    uv run pyinstaller installer/automa.spec --noconfirm
"""
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 - SPECPATH lo provee PyInstaller


# Datafiles del repo que el runtime necesita disponibles fisicamente.
datas = [
    (str(ROOT / "flows"), "flows"),
    (str(ROOT / "schemas"), "schemas"),
]
datas += collect_data_files("webview", include_py_files=False)


# Hidden imports: registry de acciones via entry-points + plugins lazy.
hiddenimports = []
hiddenimports += [
    "actions.filesystem",
    "actions.screen",
    "actions.vision",
    "actions.system",
    "actions.rules",
    "actions.ui",
    "actions.http_actions",
    "actions.notify",
    "actions.browser_capture",
    "actions.browser_form",
]
hiddenimports += collect_submodules("webview")
hiddenimports += ["mss", "mss.tools", "pyautogui", "pygetwindow", "pyperclip"]
hiddenimports += ["PIL.Image", "PIL.ImageGrab"]
hiddenimports += ["pytesseract"]


block_cipher = None


a = Analysis(
    [str(ROOT / "installer" / "automa_entry.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Automa",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,   # GUI app — sin consola flotante al arrancar.
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Automa",
)
