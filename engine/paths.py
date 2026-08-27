"""Resolución de las dos raíces del sistema: la de lectura y la de escritura.

Separar ambas es la decisión de despliegue más importante del proyecto, y nació
de un fallo real: instalado bajo ``Program Files`` (de solo lectura para usuarios
sin admin), ``init_db()`` levantaba ``PermissionError [WinError 5]`` al intentar
crear su base de datos dentro del propio bundle.

* :func:`root_dir` — dónde viven ``flows/`` y ``schemas/``. En el binario
  empaquetado apunta a ``sys._MEIPASS``, la carpeta que PyInstaller extrae al
  arrancar.
* :func:`data_dir` — dónde viven ``db/``, ``state/``, ``logs/``, ``configs/``,
  ``secrets/`` y ``output/``. En modo desarrollo coincide con :func:`root_dir`;
  congelado apunta a ``%LOCALAPPDATA%\\Automa`` en Windows o a
  ``$XDG_DATA_HOME/automa-pc`` en el resto.

Ambas admiten override explícito (``AUTOMA_ROOT`` y ``AUTOMA_DATA_ROOT``), que es
lo que usan las pruebas y el entry point del bundle.

Nota para quien empaquete: ``engine/catalog.py`` define su **propia** versión de
``root_dir`` que ignora ``AUTOMA_ROOT`` y ``sys._MEIPASS``. En desarrollo ambas
coinciden; en el binario no tiene por qué.
"""
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
