"""Contrato tipado de un flow, como dataclasses.

Representación en memoria de lo que declara ``manifest.json``, producida por
:class:`engine.loader.FlowLoader` y consumida por
:class:`engine.orchestrator.Orchestrator`.

Los valores por defecto de estas dataclasses **son el comportamiento por defecto
del sistema**, no meros marcadores:

* ``allowed_actions = None`` y ``allowed_paths = None`` significan «sin
  restricción», no «lista vacía». Es la diferencia entre un flow con sandbox y un
  flow permisivo.
* ``max_steps_per_run = 200`` es la única protección contra un grafo de
  transiciones circular: sin ella, un flow mal escrito colgaría el proceso.
* ``retries = 0`` significa un solo intento, y no hay espera entre reintentos.
* ``TransitionDefinition.on = "success"`` hace que una transición sin ``on``
  explícito solo se dispare cuando el paso va bien.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransitionDefinition:
    on: str = "success"
    next_step: str | None = None
    end: bool = False
    when: dict[str, Any] | None = None


@dataclass
class StepDefinition:
    id: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    save_as: str | None = None
    retries: int = 0
    when: dict[str, Any] | None = None
    transitions: list[TransitionDefinition] = field(default_factory=list)


@dataclass
class FlowDefinition:
    id: str
    name: str
    steps: list[StepDefinition]
    description: str = ""
    family: str = "general"
    start_step: str | None = None
    max_steps_per_run: int = 200
    allowed_actions: list[str] | None = None
    required_secrets: list[str] = field(default_factory=list)
    allowed_paths: list[str] | None = None
    max_runtime_seconds: float | None = None
