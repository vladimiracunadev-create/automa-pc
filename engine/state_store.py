"""Snapshot completo del estado de una corrida en un archivo JSON.

Escribe ``state/<flow_id>_<run_id>.json`` con el estado íntegro: definición,
contexto, todos los pasos con sus resultados, la ruta recorrida y los outputs
detectados. Es un **superconjunto** de lo que guarda la tabla ``runs``, y sirve
para reconstruir una corrida si la base de datos se pierde.

El orquestador lo invoca tras **cada** paso, de modo que el archivo se reescribe
entero cada vez. Para un flow de 20 pasos con contexto grande son 20 escrituras
completas. El beneficio es que una corrida interrumpida por un corte deja rastro
de hasta dónde llegó.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, state_path: Path) -> None:
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: dict[str, Any]) -> None:
        with self.state_path.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)

    def load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        with self.state_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
