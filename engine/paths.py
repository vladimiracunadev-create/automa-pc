from __future__ import annotations

import os
import sys
from pathlib import Path


def root_dir() -> Path:
    """Raíz lógica del proyecto (donde viven ``flows/``, ``schemas/``).

    Orden de resolución:
    1. ``$AUTOMA_ROOT`` si está definido (override explícito, útil en tests
       y en el bundle PyInstaller).
    2. ``sys._MEIPASS`` cuando el binario corre congelado por PyInstaller
       — los datafiles se extraen ahí.
    3. La carpeta padre de este archivo (modo desarrollo normal).
    """
    env_override = os.environ.get("AUTOMA_ROOT")
    if env_override:
        return Path(env_override).resolve()
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass).resolve()
    return Path(__file__).resolve().parent.parent
