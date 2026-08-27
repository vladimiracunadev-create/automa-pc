"""Sustitución de placeholders en los ``params`` de un paso.

Resuelve ``{clave}`` y ``{objeto.campo}`` contra el contexto de la corrida,
aplanado previamente para que las claves con punto funcionen.

La decisión central del módulo son **dos modos de sustitución**:

* **Placeholder exacto** — la cadena entera es un único placeholder. Se devuelve
  el valor **con su tipo original**: un booleano sigue siendo booleano, un dict
  sigue siendo dict, y ``None`` se convierte en ``null`` JSON. Por eso
  ``"headless": "{{ headless }}"`` llega a la acción como ``False`` y no como la
  cadena ``"False"``.
* **Placeholder embebido** — la cadena contiene texto alrededor. Se sustituye
  textualmente y **lo que no existe queda literal**, sin error.

Por qué no se usa ``str.format_map``, que sería lo obvio:

1. Interpretaría el punto como acceso a atributo, así que
   ``"{content.content_hash}"`` lanzaría ``AttributeError`` sobre un dict.
2. Reventaría ante una llave que no es placeholder (JSON embebido en un comando).

El centinela ``_MISSING`` existe para distinguir «la clave no está» de «la clave
está y vale ``None``»; sin él, un placeholder que resuelve a ``None`` caería al
render de string y produciría el texto ``"None"``.

``{now}`` se inyecta en cada llamada: dentro de un mismo paso todos los ``{now}``
coinciden, pero **entre pasos pueden diferir** si cruzan el cambio de segundo.
Los flows del repositorio lo evitan pasando la ruta por el contexto con
``save_as`` en lugar de recomputar ``{now}``.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

# Sentinela para distinguir "clave ausente" de "clave presente con valor None":
# un placeholder exacto que resuelve a None debe devolver None (JSON null),
# no caer al render de string.
_MISSING = object()

_PLACEHOLDER = re.compile(r"\{\s*([^{}]+?)\s*\}")


def flatten_context(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        compound = f"{prefix}.{key}" if prefix else key
        result[compound] = value
        if isinstance(value, dict):
            result.update(flatten_context(value, compound))
    return result


def _resolve_exact_placeholder(text: str, flat: dict[str, Any]) -> Any:
    match = re.fullmatch(r"\{\s*([^{}]+?)\s*\}", text)
    if not match:
        return _MISSING
    return flat.get(match.group(1).strip(), _MISSING)


def _substitute_placeholders(text: str, flat: dict[str, Any]) -> str:
    """Reemplaza cada ``{clave}`` presente en el contexto aplanado.

    Soporta claves con punto (``{content.content_hash}``) y espacios internos
    (``{ clave }``). Un placeholder cuya clave no existe queda literal, y las
    llaves que no son placeholders (p.ej. JSON embebido en un comando) no se
    tocan — a diferencia de ``str.format_map``, que crashea con ellas.
    """

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if key in flat:
            return str(flat[key])
        return match.group(0)

    return _PLACEHOLDER.sub(_replace, text)


def render_value(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        prepared = value.replace("{{", "{").replace("}}", "}")
        flat = flatten_context(context)
        flat["now"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        exact = _resolve_exact_placeholder(prepared, flat)
        if exact is not _MISSING:
            return exact
        return _substitute_placeholders(prepared, flat)
    if isinstance(value, dict):
        return {k: render_value(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [render_value(v, context) for v in value]
    return value
