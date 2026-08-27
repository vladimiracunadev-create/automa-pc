"""Prueba de humo de extremo a extremo: motor, acciones, base y scheduler.

Complementa a ``pytest``: en vez de aislar componentes, ejecuta tres flows reales
del catálogo de principio a fin y comprueba que el sistema completo funciona
—orquestador, acciones, SQLite, configuración y scheduler— sobre la instalación
tal y como está.

La CI lo corre en un job propio (``ci.yml``, job ``smoke``), después de que pase
la matriz de pruebas.

.. warning::

   **Efecto secundario sobre el árbol de trabajo.** La llamada a
   ``set_flow_config('03_folder_inventory', ...)`` reescribe
   ``configs/03_folder_inventory.json``, que es un archivo **versionado**. Tras
   ejecutar este script, ``git status`` puede marcarlo como modificado; se
   restaura con ``git checkout -- configs/03_folder_inventory.json``.

   Revise siempre ``git status`` antes de confirmar tras ejecutar el smoke test.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.catalog import list_flows  # noqa: E402
from engine.database import (  # noqa: E402
    DB_PATH,
    get_run,
    init_db,
    list_runs,
    set_flow_config,
    set_schedule,
    sync_flows,
)
from engine.orchestrator import Orchestrator  # noqa: E402
from engine.paths import root_dir  # noqa: E402
from engine.scheduler import SchedulerService  # noqa: E402


def main() -> None:
    root = root_dir()
    init_db()
    sync_flows(list_flows())

    set_flow_config('03_folder_inventory', {'path_override': 'data/inbox'})

    state_a = Orchestrator(root / 'flows' / '03_folder_inventory').run()
    state_b = Orchestrator(root / 'flows' / '05_system_healthcheck').run()
    state_c = Orchestrator(root / 'flows' / '06_process_watchdog').run()

    assert state_a['status'] == 'completed'
    assert state_b['status'] == 'completed'
    assert state_c['status'] == 'completed'
    assert DB_PATH.exists()

    set_schedule('05_system_healthcheck', enabled=True, interval_seconds=1)
    scheduler = SchedulerService(loop_sleep_seconds=0.2)
    scheduler.run_pending_once()

    runs = list_runs(limit=20)
    assert len(runs) >= 3
    assert get_run(state_b['run_id']) is not None

    print(json.dumps({'ok': True, 'runs': len(runs), 'db_path': str(DB_PATH)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
