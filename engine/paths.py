from __future__ import annotations

import os
import sys
from pathlib import Path


def root_dir() -> Path:
    """Raíz **read-only** del proyecto (donde viven ``flows/``, ``schemas/``).

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


def _is_frozen() -> bool:
    return bool(getattr(sys, "_MEIPASS", None)) or getattr(sys, "frozen", False)


def data_dir() -> Path:
    """Raíz **writable** para state, db, configs, secrets, output, logs.

    En modo desarrollo coincide con :func:`root_dir` — el repo es el árbol
    de trabajo y se puede escribir libremente.

    En el bundle PyInstaller (que típicamente se instala bajo Program
    Files, read-only para usuarios sin admin) apunta a un directorio
    per-user fuera del bundle: ``%LOCALAPPDATA%\\Automa`` en Windows,
    ``$XDG_DATA_HOME/automa-pc`` o ``~/.local/share/automa-pc`` en otros.

    Override explícito con ``$AUTOMA_DATA_ROOT``.
    """
    env_override = os.environ.get("AUTOMA_DATA_ROOT")
    if env_override:
        target = Path(env_override).resolve()
        target.mkdir(parents=True, exist_ok=True)
        return target

    if not _is_frozen():
        return root_dir()

    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
        target = Path(base) / "Automa"
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        target = Path(base) / "automa-pc"

    target.mkdir(parents=True, exist_ok=True)
    return target.resolve()
