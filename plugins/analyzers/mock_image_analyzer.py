"""Analizador heurístico local: brillo medio, RGB medio y estado visual.

Es el analizador **por defecto** de ``vision.analyze_image`` y el que usa el flow
01. No hay nada de inteligencia artificial aquí: abre la imagen con Pillow,
promedia los canales y clasifica el resultado en ``oscuro`` / ``medio`` /
``claro`` con dos umbrales fijos (60 y 180 sobre 255).

Su valor no es la precisión sino el desacoplamiento: da a un flow un dato
utilizable sobre la captura sin depender de nada externo, y deja el hueco para
que otro analizador —OCR, visión por computador local, o un proveedor externo—
ocupe su lugar cambiando una cadena en el manifest.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


class MockImageAnalyzer:
    """Analizador base sin IA externa.

    Hace una lectura heurística simple como base local para desacoplar el análisis
    del flujo. Luego puede reemplazarse por OCR, CV local o un conector IA.
    """

    def analyze(self, image_path: Path) -> dict[str, Any]:
        with Image.open(image_path) as img:
            rgb = img.convert("RGB")
            stat = ImageStat.Stat(rgb)
            mean_rgb = [round(value, 2) for value in stat.mean]
            avg_brightness = round(sum(mean_rgb) / 3, 2)

        if avg_brightness < 60:
            visual_state = "oscuro"
        elif avg_brightness < 180:
            visual_state = "medio"
        else:
            visual_state = "claro"

        return {
            "width": rgb.width,
            "height": rgb.height,
            "mean_rgb": mean_rgb,
            "avg_brightness": avg_brightness,
            "visual_state": visual_state,
            "summary": (
                "Análisis heurístico local completado. "
                "No usa IA externa; sirve como punto de extensión para OCR o visión."
            ),
        }
