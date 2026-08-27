"""Acción ``rules.evaluate``: motor de reglas declarativas del manifest.

Permite que un flow tome una decisión —«si la memoria supera el 80 %, marca
alerta»— sin escribir Python: las reglas viven en los ``params`` del paso.

Semántica: las reglas se evalúan **en orden y gana la primera que coincide**. El
resultado incluye ``status`` (el de la regla que ganó, o ``default_status``),
``matched_rule`` y el detalle completo de ``evaluations``, de modo que el
histórico registra qué se comprobó aunque no coincidiera nada.

.. warning::

   **Este módulo NO es el mismo motor que** :mod:`engine.conditions`, aunque los
   nombres de operador se solapen. Aquí hay **seis** operadores (``eq``, ``ne``,
   ``gt``, ``lt``, ``contains``, ``in``); allí hay **trece**. Los ``when`` de
   pasos y transiciones usan el otro módulo, así que ``gte``, ``lte``, ``exists``,
   ``not_exists``, ``truthy``, ``falsy`` y ``regex`` **no funcionan dentro de
   ``rules.evaluate``** y levantan ``ValueError``.

   Además, ``contains`` aquí **distingue mayúsculas** (``str(expected) in
   str(value)``), mientras que en :mod:`engine.conditions` normaliza ambos lados
   a minúsculas. El mismo nombre de operador se comporta distinto según dónde se
   escriba.
"""
from __future__ import annotations

from typing import Any


def _get_path(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current



def _matches(value: Any, operator: str, expected: Any) -> bool:
    if operator == "eq":
        return value == expected
    if operator == "ne":
        return value != expected
    if operator == "gt":
        return value is not None and value > expected
    if operator == "lt":
        return value is not None and value < expected
    if operator == "contains":
        return value is not None and str(expected) in str(value)
    if operator == "in":
        return value in expected if isinstance(expected, list) else False
    raise ValueError(f"Operador no soportado: {operator}")



def evaluate_rules(input_data: dict[str, Any], rules: list[dict[str, Any]], default_status: str = "no_match") -> dict[str, Any]:
    evaluated = []
    for rule in rules:
        path = rule["path"]
        operator = rule.get("operator", "eq")
        expected = rule.get("value")
        actual = _get_path(input_data, path)
        matched = _matches(actual, operator, expected)
        result = {
            "id": rule.get("id", path),
            "path": path,
            "operator": operator,
            "expected": expected,
            "actual": actual,
            "matched": matched,
            "status": rule.get("status", "matched") if matched else rule.get("status_on_fail", "not_matched"),
            "message": rule.get("message"),
        }
        evaluated.append(result)
        if matched:
            return {
                "status": rule.get("status", "matched"),
                "matched_rule": result,
                "evaluations": evaluated,
            }

    return {
        "status": default_status,
        "matched_rule": None,
        "evaluations": evaluated,
    }
