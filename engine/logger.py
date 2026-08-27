"""Registro de eventos de una corrida, por duplicado y a propósito.

Cada llamada a :meth:`JsonlLogger.write` deja el evento en **dos sitios**: una
línea en ``logs/<flow_id>_<run_id>.jsonl`` y una fila en la tabla ``events``.

La redundancia es deliberada y tiene un reparto claro de papeles:

* El archivo JSONL es **append-only**: nada lo reescribe, sobrevive a un borrado
  de la base de datos y se puede leer con cualquier herramienta de texto.
* La tabla permite consultar y agregar desde el panel.

El costo es duplicar el volumen de la traza. Y como el archivo se escribe antes
que la fila, un corte entre ambas operaciones deja el evento en el archivo pero
no en la base.

Los nueve tipos de evento que emite el orquestador: ``flow_started``,
``flow_finished``, ``flow_blocked``, ``step_started``, ``step_finished``,
``step_failed``, ``step_skipped``, ``step_blocked`` y ``step_recovered``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.database import insert_event


class JsonlLogger:
    def __init__(self, log_path: Path, run_id: str) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id

    def write(self, event_type: str, payload: dict[str, Any]) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        record = {
            'timestamp': timestamp,
            'event': event_type,
            **payload,
        }
        with self.log_path.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + '\n')
        insert_event(self.run_id, event_type, payload, event_time=timestamp)
