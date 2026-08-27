"""Acciones que actúan sobre la sesión de escritorio: teclado, ratón y procesos.

Es el bloque de **mayor riesgo del repositorio**: estas funciones mueven el
teclado y el ratón reales del operador y lanzan procesos en su sesión. Léase
entero antes de modificar nada.

**``dry_run`` es el mecanismo que hace testeable lo intestable.** Con
``dry_run=True`` la función devuelve exactamente el payload que habría producido,
con ``sent``/``typed``/``clicked``/``launched`` en ``False``, sin tocar el
sistema. Es lo que permite que ``tests/test_actions_basic.py`` las ejercite en la
CI sin efectos, y lo que un operador debe usar la primera vez que prueba un flow
de UI. Todos los flows de UI del catálogo exponen ``dry_run`` en su
``context.example.json``.

**``shell=True`` está prohibido a propósito** en :func:`launch_process`, para
cerrar el vector de command injection (CWE-78). El comando se tokeniza con
``shlex.split`` y se lanza con ``shell=False``. No reactive esa rama: si necesita
un binario con argumentos complejos, páselo como cadena tokenizable.

Nota para Windows: ``shlex`` usa reglas POSIX, así que una ruta con contrabarras
(``C:\\Users\\ejemplo``) puede tokenizarse de forma inesperada. Los flows del
repositorio pasan rutas con barra normal.

``pyautogui`` se importa **dentro** de la función (:func:`_import_pyautogui`)
para que el módulo siga siendo importable en un entorno sin escritorio gráfico —
por ejemplo, la CI.
"""
from __future__ import annotations

import shlex
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any


def _import_pyautogui():
    try:
        import pyautogui

        return pyautogui
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            'pyautogui no está disponible o el entorno no permite control de UI. '
            'Instálalo y ejecútalo en un escritorio real.'
        ) from exc


def open_url(url: str, new_tab: bool = True) -> dict[str, Any]:
    opened = webbrowser.open(url, new=2 if new_tab else 0)
    return {'url': url, 'opened': bool(opened)}


def open_file_in_browser(path: str, new_tab: bool = True) -> dict[str, Any]:
    target = Path(path).resolve()
    if not target.exists():
        raise FileNotFoundError(f'Archivo no encontrado: {path}')
    opened = webbrowser.open(target.as_uri(), new=2 if new_tab else 0)
    return {'path': str(target), 'opened': bool(opened), 'uri': target.as_uri()}


def launch_process(command: str, wait_seconds: float = 0.0, shell: bool = False, dry_run: bool = False) -> dict[str, Any]:
    command = command.strip()
    if not command:
        raise ValueError('Se requiere un comando no vacio para lanzar un proceso.')
    if shell:
        # Se elimina deliberadamente la rama shell=True para cerrar el vector de
        # command injection (CWE-78). Si se necesita un binario con argumentos
        # complejos, hay que pasarlo como string POSIX-tokenizable.
        raise ValueError(
            'launch_process: shell=True está deshabilitado por seguridad. '
            'Pasá el comando como string tokenizable (shlex) y dejá shell=false.'
        )
    if dry_run:
        return {'command': command, 'pid': None, 'launched': False, 'dry_run': True, 'shell': False}
    process = subprocess.Popen(shlex.split(command), shell=False)
    if wait_seconds > 0:
        time.sleep(wait_seconds)
    return {'command': command, 'pid': process.pid, 'launched': True, 'dry_run': False, 'shell': False}


def hotkey(keys: list[str], interval: float = 0.0, dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {'keys': keys, 'sent': False, 'dry_run': True}
    pyautogui = _import_pyautogui()
    pyautogui.hotkey(*keys, interval=interval)
    return {'keys': keys, 'sent': True, 'dry_run': False}


def type_text(text: str, interval: float = 0.01, dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {'text_length': len(text), 'typed': False, 'dry_run': True, 'preview': text[:200]}
    pyautogui = _import_pyautogui()
    pyautogui.write(text, interval=interval)
    return {'text_length': len(text), 'typed': True, 'dry_run': False}


def click(x: int, y: int, clicks: int = 1, interval: float = 0.0, button: str = 'left', dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {'x': x, 'y': y, 'clicks': clicks, 'button': button, 'clicked': False, 'dry_run': True}
    pyautogui = _import_pyautogui()
    pyautogui.click(x=x, y=y, clicks=clicks, interval=interval, button=button)
    return {'x': x, 'y': y, 'clicks': clicks, 'button': button, 'clicked': True, 'dry_run': False}


def click_bbox(bbox: dict[str, Any], clicks: int = 1, interval: float = 0.0, button: str = 'left', dry_run: bool = False) -> dict[str, Any]:
    if not bbox:
        raise ValueError('Se requiere un bbox para hacer click visual.')
    left = int(bbox.get('left', 0))
    top = int(bbox.get('top', 0))
    width = int(bbox.get('width', 0))
    height = int(bbox.get('height', 0))
    x = left + max(width // 2, 0)
    y = top + max(height // 2, 0)
    result = click(x=x, y=y, clicks=clicks, interval=interval, button=button, dry_run=dry_run)
    result['bbox'] = bbox
    return result
