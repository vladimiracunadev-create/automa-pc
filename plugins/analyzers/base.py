"""Contrato de un analizador de imagen.

Protocolo estructural (PEP 544): cualquier clase con un método
``analyze(image_path) -> dict`` sirve como analizador, sin necesidad de heredar
de nada. Es lo que permite que ``actions/vision.py::ANALYZERS`` intercambie
implementaciones y que un tercero añada la suya.

El ``dict`` devuelto debe ser serializable a JSON: acaba en el contexto de la
corrida y de ahí en SQLite.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class AnalyzerProtocol(Protocol):
    def analyze(self, image_path: Path) -> dict[str, Any]:
        ...
