"""Bóveda de secretos local.

Estrategia simple, suficiente para uso de un único usuario en su PC:

1. Variables de entorno (prioridad alta).
2. Archivo ``secrets/secrets.json`` (permisos del FS son el control de acceso).

El archivo NUNCA debe versionarse — se ignora por ``.gitignore``. Esto
evita meter tokens en ``configs/*.json`` (que se exportan/comparten) y
permite que los flows declaren ``required_secrets`` para ser bloqueados
por el sandbox si faltan.
"""
from __future__ import annotations

import json
import os
from typing import Any

from engine.paths import data_dir

SECRETS_PATH = data_dir() / 'secrets' / 'secrets.json'


def _load_file_secrets() -> dict[str, Any]:
    if not SECRETS_PATH.exists():
        return {}
    try:
        return json.loads(SECRETS_PATH.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {}


def get_secret(name: str, default: str | None = None) -> str | None:
    """Resuelve un secreto. Devuelve ``default`` si no existe."""
    if name in os.environ and os.environ[name] != '':
        return os.environ[name]
    file_secrets = _load_file_secrets()
    if name in file_secrets:
        return str(file_secrets[name])
    return default


def set_secret(name: str, value: str) -> None:
    """Persiste un secreto en disco. Crea ``secrets/`` si no existe."""
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    current = _load_file_secrets()
    current[name] = value
    SECRETS_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')


def list_secret_names() -> dict[str, str]:
    """Devuelve los nombres conocidos sin exponer los valores."""
    names: dict[str, str] = {}
    for key in _load_file_secrets():
        names[key] = 'file'
    for key in os.environ:
        if key.startswith('AUTOMA_') or key.endswith('_API_KEY') or key.endswith('_TOKEN'):
            names.setdefault(key, 'env')
    return names
