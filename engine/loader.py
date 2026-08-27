"""Lectura del contrato de un flow: manifest y contexto.

Convierte ``flows/<carpeta>/manifest.json`` en las dataclasses de
:mod:`engine.models` y resuelve de dónde salen los valores del flow.

Dos comportamientos que sorprenden y conviene tener presentes:

* **El manifest NO se valida contra el JSON Schema aquí.** El schema solo lo
  aplica ``scripts/validate_project.py`` en la CI. En ejecución, los campos
  obligatorios se acceden con corchetes, así que un manifest incompleto produce
  un ``KeyError`` crudo en vez de un mensaje del validador.
* **``load_context`` devuelve la primera fuente que exista y descarta el resto.**
  No hay mezcla de claves. Guardar la configuración desde el panel crea
  ``configs/<carpeta>.json``, que a partir de ese momento oculta por completo el
  ``context.example.json`` del flow: si una versión posterior añade una clave
  nueva al ejemplo, el flow configurado no la verá.

Cuidado adicional: ``allowed_actions`` y ``allowed_paths`` se convierten con
``if raw.get(...)``, de modo que una **lista vacía** (falsy) pasa a ``None``, es
decir, a política permisiva. Escribir ``"allowed_actions": []`` con intención de
bloquear todo produce el efecto contrario.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.models import FlowDefinition, StepDefinition, TransitionDefinition


class FlowLoader:
    @staticmethod
    def load_manifest(flow_dir: Path) -> FlowDefinition:
        manifest_path = flow_dir / 'manifest.json'
        with manifest_path.open('r', encoding='utf-8') as fh:
            raw = json.load(fh)

        steps = []
        for step in raw['steps']:
            transitions = [
                TransitionDefinition(
                    on=item.get('on', 'success'),
                    next_step=item.get('next'),
                    end=item.get('end', False),
                    when=item.get('when'),
                )
                for item in step.get('transitions', [])
            ]
            steps.append(
                StepDefinition(
                    id=step['id'],
                    action=step['action'],
                    params=step.get('params', {}),
                    save_as=step.get('save_as'),
                    retries=step.get('retries', 0),
                    when=step.get('when'),
                    transitions=transitions,
                )
            )

        return FlowDefinition(
            id=raw['id'],
            name=raw.get('name', raw['id']),
            description=raw.get('description', ''),
            family=raw.get('family', 'general'),
            start_step=raw.get('start_step'),
            max_steps_per_run=int(raw.get('max_steps_per_run', 200)),
            steps=steps,
            allowed_actions=list(raw['allowed_actions']) if raw.get('allowed_actions') else None,
            required_secrets=list(raw.get('required_secrets') or []),
            allowed_paths=list(raw['allowed_paths']) if raw.get('allowed_paths') else None,
            max_runtime_seconds=(
                float(raw['max_runtime_seconds'])
                if raw.get('max_runtime_seconds') is not None
                else None
            ),
        )

    @staticmethod
    def load_context(flow_dir: Path, explicit_context_path: Path | None = None) -> dict[str, Any]:
        candidates = []
        if explicit_context_path:
            candidates.append(explicit_context_path)
        candidates.extend(
            [
                Path('configs') / f'{flow_dir.name}.json',
                flow_dir / 'context.user.json',
                flow_dir / 'context.example.json',
            ]
        )
        for candidate in candidates:
            if candidate.exists():
                with candidate.open('r', encoding='utf-8') as fh:
                    return json.load(fh)
        return {}
