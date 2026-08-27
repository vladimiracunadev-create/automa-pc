"""Motor de condiciones del manifest: los ``when`` de pasos y transiciones.

Trece operadores más los combinadores ``all`` / ``any`` / ``not``, evaluados
sobre el contexto de la corrida. Es lo que permite que un flow tenga ramas sin
escribir una línea de Python.

Trampas conocidas de este módulo:

* ``get_path`` navega diccionarios anidados por notación de punto, pero **no
  soporta índices de lista**: ``steps.0.status`` devuelve ``None``.
* Una condición vacía o ``None`` devuelve ``True``. Es lo que hace que un paso
  sin ``when`` se ejecute siempre, y también que ``{"all": []}`` deje pasar todo.
* ``contains`` normaliza **ambos** lados a minúsculas: es una búsqueda insensible
  a mayúsculas por diseño. El operador homónimo de :mod:`actions.rules` **sí**
  distingue mayúsculas — son dos motores distintos.
* Los comparadores de orden protegen contra ``None``, pero no contra tipos
  incompatibles: un umbral escrito como texto (``"80"``) frente a un número
  levanta ``TypeError`` en ejecución.
"""
from __future__ import annotations

import re
from typing import Any


def get_path(data: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split('.'):
        if isinstance(current, dict):
            current = current.get(part, default)
        else:
            return default
    return current


def matches(actual: Any, operator: str, expected: Any = None) -> bool:
    if operator == 'eq':
        return actual == expected
    if operator == 'ne':
        return actual != expected
    if operator == 'gt':
        return actual is not None and actual > expected
    if operator == 'gte':
        return actual is not None and actual >= expected
    if operator == 'lt':
        return actual is not None and actual < expected
    if operator == 'lte':
        return actual is not None and actual <= expected
    if operator == 'contains':
        return actual is not None and str(expected).lower() in str(actual).lower()
    if operator == 'in':
        return actual in expected if isinstance(expected, list) else False
    if operator == 'exists':
        return actual is not None
    if operator == 'not_exists':
        return actual is None
    if operator == 'truthy':
        return bool(actual)
    if operator == 'falsy':
        return not bool(actual)
    if operator == 'regex':
        return actual is not None and re.search(str(expected), str(actual)) is not None
    raise ValueError(f'Operador no soportado: {operator}')


def evaluate_condition(condition: dict[str, Any] | None, context: dict[str, Any]) -> bool:
    if not condition:
        return True
    if 'all' in condition:
        return all(evaluate_condition(item, context) for item in condition['all'])
    if 'any' in condition:
        return any(evaluate_condition(item, context) for item in condition['any'])
    if 'not' in condition:
        return not evaluate_condition(condition['not'], context)

    path = condition.get('path')
    operator = condition.get('operator', 'eq')
    expected = condition.get('value')
    actual = get_path(context, path, None) if path else None
    return matches(actual, operator, expected)
