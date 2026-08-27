"""Lectura del catálogo de flows desde el disco, enriquecida con la base.

Une lo que hay en ``flows/`` (la verdad sobre qué casos existen) con lo que hay
en SQLite (configuración guardada, horario, corridas). El panel y el CLI leen
siempre de aquí.

Detalle importante: **el catálogo lo define el disco, no la tabla ``flows``**.
``list_flows`` recorre las carpetas; la tabla es un espejo que ``sync_flows``
actualiza al arrancar y que nunca borra filas — un flow eliminado del disco deja
su fila huérfana.

Este módulo define su propio ``root_dir`` local en lugar de importar el de
:mod:`engine.paths`. Ambos devuelven lo mismo en desarrollo, pero **el de aquí
ignora ``AUTOMA_ROOT`` y ``sys._MEIPASS``**, así que en el binario empaquetado
podrían divergir.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.database import get_events, get_flow_config, get_run, get_schedule, get_steps
from engine.database import list_runs as db_list_runs


def root_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def flows_dir() -> Path:
    return root_dir() / 'flows'


def list_flow_folders() -> list[Path]:
    return sorted([p for p in flows_dir().iterdir() if p.is_dir()])


def load_manifest(flow_folder: Path) -> dict[str, Any]:
    return json.loads((flow_folder / 'manifest.json').read_text(encoding='utf-8'))


def list_flows() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for folder in list_flow_folders():
        manifest = load_manifest(folder)
        items.append(
            {
                'folder': folder.name,
                'id': manifest['id'],
                'name': manifest['name'],
                'family': manifest.get('family', 'general'),
                'description': manifest.get('description', ''),
                'steps': manifest.get('steps', []),
                'flow_path': str(folder),
            }
        )
    return items


def get_flow_by_folder(folder_name: str) -> dict[str, Any] | None:
    folder = flows_dir() / folder_name
    if not folder.exists() or not folder.is_dir():
        return None
    manifest = load_manifest(folder)
    return {
        'folder': folder.name,
        'id': manifest['id'],
        'name': manifest['name'],
        'family': manifest.get('family', 'general'),
        'description': manifest.get('description', ''),
        'steps': manifest.get('steps', []),
        'flow_path': str(folder),
        'readme_path': str(folder / 'README.md'),
        'context_example_path': str(folder / 'context.example.json'),
        'config': get_flow_config(folder.name),
        'schedule': get_schedule(folder.name),
    }


def list_runs(flow_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    return db_list_runs(flow_id=flow_id, limit=limit)


def find_run(flow_id: str, run_id: str) -> dict[str, Any] | None:
    run = get_run(run_id)
    if not run or run.get('flow_id') != flow_id:
        return None
    return run


def load_run_events(flow_id: str, run_id: str) -> list[dict[str, Any]]:
    run = get_run(run_id)
    if not run or run.get('flow_id') != flow_id:
        return []
    return get_events(run_id)


def load_run_steps(flow_id: str, run_id: str) -> list[dict[str, Any]]:
    run = get_run(run_id)
    if not run or run.get('flow_id') != flow_id:
        return []
    return get_steps(run_id)
