"""Entry-point del binario empaquetado por PyInstaller.

Resuelve la ruta a los datafiles (flows/, schemas/) cuando el codigo
corre desde un bundle PyInstaller (``sys._MEIPASS`` apunta a la carpeta
extraida en tiempo de arranque) y delega en ``app.desktop.main``.
"""
from __future__ import annotations

import os
import sys


def _set_data_root_from_bundle() -> None:
    """Si corremos desde un bundle PyInstaller, configura paths."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        # engine.paths lee AUTOMA_ROOT como override del root del proyecto.
        os.environ.setdefault("AUTOMA_ROOT", meipass)
        # Tambien cwd para que rutas relativas (output/) caigan junto al exe.
        exe_dir = os.path.dirname(sys.executable)
        try:
            os.chdir(exe_dir)
        except OSError:
            pass


def main() -> int:
    _set_data_root_from_bundle()
    from app.desktop import main as desktop_main

    return desktop_main()


if __name__ == "__main__":
    raise SystemExit(main())
