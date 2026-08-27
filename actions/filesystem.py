"""Acciones de sistema de archivos: inventariar, leer, clasificar y escribir.

Siete acciones sin ninguna dependencia externa, y por eso las más usadas del
catálogo: ``filesystem.write_json`` aparece en 16 de los 27 flows como paso final
que persiste el reporte.

Contrato común: todas devuelven un ``dict`` serializable a JSON, crean el
directorio padre cuando escriben, y levantan ``FileNotFoundError`` si la ruta de
entrada no existe.

Detalles no obvios que conviene conocer al escribir un flow:

* ``list_directory`` devuelve **solo archivos**, nunca subcarpetas.
* ``write_json`` **sobrescribe sin avisar** si el archivo ya existe.
* ``move_file`` con ``overwrite=True`` hace ``unlink()`` del destino **antes** de
  mover: si el ``shutil.move`` falla después, el destino ya se perdió.
* ``summarize_text_folder`` corta en ``max_files`` (10 por defecto) y solo acepta
  cinco extensiones (``.txt``, ``.md``, ``.log``, ``.csv``, ``.json``). **No
  declara cuántos archivos quedaron fuera**: es la única cota del sistema que no
  se reporta, a diferencia de los ``*_truncated`` del resto de acciones.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def ensure_directory(path: str) -> dict[str, Any]:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return {"path": str(directory), "exists": directory.exists()}



def list_directory(path: str, recursive: bool = False) -> dict[str, Any]:
    directory = Path(path)
    if not directory.exists():
        raise FileNotFoundError(f"La carpeta no existe: {path}")

    items = []
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    for item in iterator:
        if item.is_file():
            items.append(
                {
                    "name": item.name,
                    "path": str(item),
                    "size_bytes": item.stat().st_size,
                    "extension": item.suffix.lower(),
                }
            )
    return {"path": str(directory), "files": items, "total_files": len(items)}



def write_json(path: str, data: Any) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return {"path": str(target), "written": True}



def read_text_file(path: str, max_chars: int = 4000) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    text = target.read_text(encoding="utf-8", errors="replace")
    return {
        "path": str(target),
        "chars": len(text),
        "preview": text[:max_chars],
    }



def classify_file_inventory(files: list[dict[str, Any]]) -> dict[str, Any]:
    by_extension: dict[str, int] = {}
    total_size = 0
    largest: dict[str, Any] | None = None

    for item in files:
        ext = item.get("extension") or "[sin_ext]"
        by_extension[ext] = by_extension.get(ext, 0) + 1
        size = int(item.get("size_bytes", 0))
        total_size += size
        if largest is None or size > int(largest.get("size_bytes", 0)):
            largest = item

    return {
        "total_files": len(files),
        "total_size_bytes": total_size,
        "by_extension": dict(sorted(by_extension.items(), key=lambda kv: kv[0])),
        "largest_file": largest,
    }



def summarize_text_folder(path: str, max_files: int = 10, max_chars_per_file: int = 800) -> dict[str, Any]:
    directory = Path(path)
    if not directory.exists():
        raise FileNotFoundError(f"La carpeta no existe: {path}")

    summaries = []
    processed = 0
    for item in sorted(directory.iterdir()):
        if not item.is_file() or item.suffix.lower() not in {".txt", ".md", ".log", ".csv", ".json"}:
            continue
        text = item.read_text(encoding="utf-8", errors="replace")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        summaries.append(
            {
                "name": item.name,
                "path": str(item),
                "chars": len(text),
                "preview": text[:max_chars_per_file],
                "line_count": len(lines),
            }
        )
        processed += 1
        if processed >= max_files:
            break

    return {"path": str(directory), "processed_files": processed, "summaries": summaries}



def move_file(source_path: str, destination_path: str, overwrite: bool = False) -> dict[str, Any]:
    source = Path(source_path)
    destination = Path(destination_path)
    if not source.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {source_path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"El archivo destino ya existe: {destination_path}")
    if destination.exists() and overwrite:
        destination.unlink()
    shutil.move(str(source), str(destination))
    return {"source": str(source), "destination": str(destination), "moved": True}
