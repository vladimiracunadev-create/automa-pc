"""Interfaz de línea de comandos: ``automa list``, ``run`` y ``scheduler``.

Entry point del comando ``automa`` declarado en ``pyproject.toml``. Es la vía de
uso sin panel: útil para probar un flow recién escrito, para integrarlo en un
script o para dejar el scheduler corriendo sin ventana.

.. warning::

   **Defecto conocido en Windows.** :func:`main` termina imprimiendo
   ``json.dumps(..., ensure_ascii=False)``. Varios manifests contienen caracteres
   no representables en la página de códigos ``cp1252`` de la consola de Windows
   (por ejemplo ``→``), así que tanto ``list`` como ``run`` terminan con
   ``UnicodeEncodeError``.

   Con ``run``, **el flow se ejecuta completo y correctamente** —la corrida queda
   persistida y el reporte escrito— y el error salta después, solo al volcar el
   JSON a la consola. No se pierde trabajo, pero el código de salida es de error.

   Solución para el usuario: ``PYTHONIOENCODING=utf-8`` antes del comando.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.catalog import list_flows
from engine.database import init_db, sync_flows
from engine.orchestrator import Orchestrator
from engine.scheduler import SchedulerService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Runner de flujos autónomos')
    subparsers = parser.add_subparsers(dest='command', required=True)

    run_parser = subparsers.add_parser('run', help='Ejecutar un flujo')
    run_parser.add_argument('flow_dir', help='Ruta a la carpeta del flujo')
    run_parser.add_argument('--context', dest='context_path', default=None, help='Ruta opcional a un archivo JSON de contexto')

    subparsers.add_parser('list', help='Listar flujos disponibles')

    schedule_parser = subparsers.add_parser('scheduler', help='Levantar scheduler en bucle')
    schedule_parser.add_argument('--interval', type=float, default=2.0, help='Segundos entre chequeos del scheduler')
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == 'run':
        init_db()
        sync_flows(list_flows())
        flow_dir = Path(args.flow_dir)
        context_path = Path(args.context_path) if args.context_path else None
        orchestrator = Orchestrator(flow_dir=flow_dir, context_path=context_path)
        state = orchestrator.run()
        print(json.dumps(state, ensure_ascii=False, indent=2))
    elif args.command == 'list':
        print(json.dumps(list_flows(), ensure_ascii=False, indent=2))
    elif args.command == 'scheduler':
        init_db()
        sync_flows(list_flows())
        SchedulerService(loop_sleep_seconds=args.interval).serve_forever()


if __name__ == '__main__':
    main()
