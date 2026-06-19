"""Entry-point del binario empaquetado por PyInstaller.

Resuelve la ruta a los datafiles (flows/, schemas/) cuando el codigo
corre desde un bundle PyInstaller (``sys._MEIPASS`` apunta a la carpeta
extraida en tiempo de arranque) y delega en ``app.desktop.main``.
"""
from __future__ import annotations

import os
import sys


def _set_data_root_from_bundle() -> None:
    """Si corremos desde un bundle PyInstaller, configura paths.

    Separa el root **read-only** (datafiles en _MEIPASS, embebidos en el bundle)
    del root **writable** (db, configs, state, logs, output — en %LOCALAPPDATA%).

    Cambia cwd al directorio writable: muchos flows escriben en rutas
    relativas (``output/screenshots/...``) y el sandbox las resuelve contra cwd.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return

    # engine.paths.root_dir lee AUTOMA_ROOT como override del root del proyecto
    # (donde viven flows/ y schemas/ — read-only en el bundle).
    os.environ.setdefault("AUTOMA_ROOT", meipass)

    # data_dir() resuelve a %LOCALAPPDATA%\Automa cuando el binario esta frozen.
    # cwd debe quedar ahi para que rutas relativas (output/...) escriban OK.
    from engine.paths import data_dir
    try:
        os.chdir(data_dir())
    except OSError:
        pass


def main() -> int:
    _set_data_root_from_bundle()
    from app.desktop import main as desktop_main

    return desktop_main()


if __name__ == "__main__":
    raise SystemExit(main())
