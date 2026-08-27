"""Toda la persistencia SQLite del sistema: siete tablas y su SQL.

Es el único módulo que abre una conexión a ``db/runs.db``. No hay ORM: el SQL se
escribe a mano y **todas** las consultas son parametrizadas con ``?``.

Decisiones de diseño y sus consecuencias:

* **Una conexión nueva por operación**, cerrada siempre en el ``finally``. Evita
  el clásico ``ProgrammingError`` por compartir conexiones entre hilos, a costa
  de abrir el archivo en cada consulta.
* **No hay ninguna ``FOREIGN KEY``.** Las relaciones entre ``flows``, ``runs``,
  ``steps`` y ``events`` las mantiene este módulo, no la base. Borrar una corrida
  a mano **no** borra sus pasos ni sus eventos: hay que limpiarlos tabla por
  tabla.
* **No hay índices explícitos**, solo los implícitos de las claves primarias.
  ``list_runs(flow_id=...)``, ``get_steps`` y ``get_events`` hacen escaneo
  completo. Irrelevante con cientos de corridas, no con decenas de miles.
* **No hay retención ni purga.** Las tablas crecen indefinidamente.
* ``acquire_run_lock`` se apoya en la clave primaria ``folder`` de ``run_locks``:
  el segundo insert viola la restricción y se traduce en ``False``. Elegante,
  pero **solo lo usa el scheduler**: las rutas del panel no adquieren el lock.
* ``set_flow_config`` escribe en **dos medios** —archivo y tabla— sin transacción
  que abarque ambos.
* Toda la maquinaria de migración es ``_ensure_column``, suficiente para añadir
  una columna e insuficiente para un cambio de tipo o un renombrado.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from engine.paths import data_dir

DB_PATH = data_dir() / 'db' / 'runs.db'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect() -> Iterable[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cols = {row['name'] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            '''
            CREATE TABLE IF NOT EXISTS flows (
                folder TEXT PRIMARY KEY,
                flow_id TEXT NOT NULL,
                name TEXT NOT NULL,
                family TEXT,
                description TEXT,
                manifest_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                flow_id TEXT NOT NULL,
                flow_folder TEXT NOT NULL,
                flow_name TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                duration_seconds REAL,
                context_json TEXT,
                outputs_json TEXT,
                error_json TEXT,
                state_path TEXT,
                log_path TEXT
            );

            CREATE TABLE IF NOT EXISTS steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                sequence_no INTEGER NOT NULL,
                step_id TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                params_json TEXT,
                result_json TEXT,
                error_text TEXT,
                started_at TEXT,
                finished_at TEXT,
                duration_seconds REAL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                event_time TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT
            );

            CREATE TABLE IF NOT EXISTS flow_configs (
                folder TEXT PRIMARY KEY,
                config_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS run_locks (
                folder TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                acquired_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS schedules (
                folder TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 0,
                interval_seconds INTEGER,
                cron_expression TEXT,
                next_run_at TEXT,
                last_run_at TEXT,
                updated_at TEXT NOT NULL
            );
            '''
        )
        # Migración suave para bases preexistentes:
        _ensure_column(conn, 'schedules', 'cron_expression', 'cron_expression TEXT')


def sync_flows(flows: list[dict[str, Any]]) -> None:
    now = utc_now()
    with connect() as conn:
        for flow in flows:
            conn.execute(
                '''
                INSERT INTO flows(folder, flow_id, name, family, description, manifest_json, updated_at)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(folder) DO UPDATE SET
                    flow_id=excluded.flow_id,
                    name=excluded.name,
                    family=excluded.family,
                    description=excluded.description,
                    manifest_json=excluded.manifest_json,
                    updated_at=excluded.updated_at
                ''',
                (
                    flow['folder'],
                    flow['id'],
                    flow['name'],
                    flow.get('family', 'general'),
                    flow.get('description', ''),
                    json.dumps(flow, ensure_ascii=False),
                    now,
                ),
            )


def upsert_run(state: dict[str, Any], flow_folder: str, state_path: str, log_path: str) -> None:
    with connect() as conn:
        conn.execute(
            '''
            INSERT INTO runs(run_id, flow_id, flow_folder, flow_name, status, created_at, started_at, finished_at,
                             duration_seconds, context_json, outputs_json, error_json, state_path, log_path)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(run_id) DO UPDATE SET
                status=excluded.status,
                started_at=excluded.started_at,
                finished_at=excluded.finished_at,
                duration_seconds=excluded.duration_seconds,
                context_json=excluded.context_json,
                outputs_json=excluded.outputs_json,
                error_json=excluded.error_json,
                state_path=excluded.state_path,
                log_path=excluded.log_path
            ''',
            (
                state['run_id'],
                state['flow_id'],
                flow_folder,
                state['flow_name'],
                state['status'],
                state['created_at'],
                state.get('started_at'),
                state.get('finished_at'),
                state.get('duration_seconds'),
                json.dumps(state.get('context', {}), ensure_ascii=False),
                json.dumps(state.get('outputs', []), ensure_ascii=False),
                json.dumps(state.get('error'), ensure_ascii=False),
                state_path,
                log_path,
            ),
        )


def insert_step(run_id: str, sequence_no: int, step_record: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            '''
            INSERT INTO steps(run_id, sequence_no, step_id, action, status, attempt, params_json, result_json,
                              error_text, started_at, finished_at, duration_seconds)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ''',
            (
                run_id,
                sequence_no,
                step_record['step_id'],
                step_record.get('action', ''),
                step_record['status'],
                int(step_record.get('attempt', 1)),
                json.dumps(step_record.get('params'), ensure_ascii=False),
                json.dumps(step_record.get('result'), ensure_ascii=False),
                step_record.get('error'),
                step_record.get('started_at'),
                step_record.get('finished_at'),
                step_record.get('duration_seconds'),
            ),
        )


def insert_event(run_id: str, event_type: str, payload: dict[str, Any], event_time: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            'INSERT INTO events(run_id, event_time, event_type, payload_json) VALUES(?,?,?,?)',
            (
                run_id,
                event_time or utc_now(),
                event_type,
                json.dumps(payload, ensure_ascii=False),
            ),
        )


def list_runs(flow_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    query = 'SELECT * FROM runs'
    params: list[Any] = []
    if flow_id:
        query += ' WHERE flow_id = ?'
        params.append(flow_id)
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_run(run_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute('SELECT * FROM runs WHERE run_id = ?', (run_id,)).fetchone()
    return dict(row) if row else None


def get_steps(run_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute('SELECT * FROM steps WHERE run_id = ? ORDER BY sequence_no ASC, id ASC', (run_id,)).fetchall()
    return [dict(row) for row in rows]


def get_events(run_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute('SELECT * FROM events WHERE run_id = ? ORDER BY id ASC', (run_id,)).fetchall()
    return [dict(row) for row in rows]


def get_flow_config(folder: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute('SELECT config_json FROM flow_configs WHERE folder = ?', (folder,)).fetchone()
    if not row:
        return None
    return json.loads(row['config_json'])


def set_flow_config(folder: str, config: dict[str, Any]) -> None:
    config_path = data_dir() / 'configs' / f'{folder}.json'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    with connect() as conn:
        conn.execute(
            '''
            INSERT INTO flow_configs(folder, config_json, updated_at)
            VALUES(?,?,?)
            ON CONFLICT(folder) DO UPDATE SET config_json=excluded.config_json, updated_at=excluded.updated_at
            ''',
            (folder, json.dumps(config, ensure_ascii=False), utc_now()),
        )


def get_schedule(folder: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute('SELECT * FROM schedules WHERE folder = ?', (folder,)).fetchone()
    if not row:
        return {
            'folder': folder,
            'enabled': 0,
            'interval_seconds': None,
            'next_run_at': None,
            'last_run_at': None,
        }
    return dict(row)


def list_schedules() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute('SELECT * FROM schedules ORDER BY folder ASC').fetchall()
    return [dict(row) for row in rows]


def set_schedule(
    folder: str,
    enabled: bool,
    interval_seconds: int | None = None,
    cron_expression: str | None = None,
) -> dict[str, Any]:
    now = utc_now()
    next_run_at: str | None = None
    if enabled:
        if cron_expression:
            from engine.cron import next_after  # import local para evitar ciclos
            next_run_at = next_after(cron_expression, datetime.now(timezone.utc)).isoformat()
        elif interval_seconds:
            next_run_at = now
    with connect() as conn:
        conn.execute(
            '''
            INSERT INTO schedules(folder, enabled, interval_seconds, cron_expression, next_run_at, last_run_at, updated_at)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(folder) DO UPDATE SET
                enabled=excluded.enabled,
                interval_seconds=excluded.interval_seconds,
                cron_expression=excluded.cron_expression,
                next_run_at=excluded.next_run_at,
                updated_at=excluded.updated_at
            ''',
            (folder, int(enabled), interval_seconds, cron_expression, next_run_at, None, now),
        )
    return get_schedule(folder)


def mark_schedule_run(
    folder: str,
    interval_seconds: int | None = None,
    cron_expression: str | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    next_run: str | None = None
    if cron_expression:
        from engine.cron import next_after
        try:
            next_run = next_after(cron_expression, now).isoformat()
        except Exception:
            next_run = None
    elif interval_seconds:
        next_run = datetime.fromtimestamp(now.timestamp() + interval_seconds, tz=timezone.utc).isoformat()
    with connect() as conn:
        conn.execute(
            'UPDATE schedules SET last_run_at = ?, next_run_at = ?, updated_at = ? WHERE folder = ?',
            (now.isoformat(), next_run, now.isoformat(), folder),
        )


def acquire_run_lock(folder: str, run_id: str) -> bool:
    """Lock por flow: True si se adquiere, False si ya hay una corrida activa."""
    with connect() as conn:
        try:
            conn.execute(
                'INSERT INTO run_locks(folder, run_id, acquired_at) VALUES(?,?,?)',
                (folder, run_id, utc_now()),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def release_run_lock(folder: str, run_id: str) -> None:
    with connect() as conn:
        conn.execute(
            'DELETE FROM run_locks WHERE folder = ? AND run_id = ?',
            (folder, run_id),
        )


def list_run_locks() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute('SELECT * FROM run_locks ORDER BY acquired_at ASC').fetchall()
    return [dict(row) for row in rows]


def force_release_lock(folder: str) -> None:
    with connect() as conn:
        conn.execute('DELETE FROM run_locks WHERE folder = ?', (folder,))
