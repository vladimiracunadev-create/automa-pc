"""Analizador de metadatos: dimensiones, modo de color y huella SHA-256.

El más barato de los tres: no interpreta la imagen, solo la describe. El
``sha256`` sobre los bytes del archivo permite comparar dos capturas y saber si
son idénticas sin guardarlas ambas.

Registrado en ``actions/vision.py::ANALYZERS`` como ``metadata``, pero **ningún
flow del catálogo lo pide**: está disponible para quien escriba uno nuevo.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from PIL import Image


class MetadataImageAnalyzer:
    def analyze(self, image_path: Path) -> dict[str, Any]:
        raw = image_path.read_bytes()
        sha256 = hashlib.sha256(raw).hexdigest()
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "sha256": sha256,
                "summary": "Analizador local de metadatos de imagen.",
            }
