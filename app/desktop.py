"""Wrapper de escritorio para el panel HTTP de Automa.

Arranca ``app.server`` en un thread daemon, espera a que el puerto esté
listening, y abre una ventana nativa con `pywebview` apuntando a
``http://127.0.0.1:<port>/``. Cerrar la ventana corta el proceso entero.

Entry-point: ``automa-desktop`` (ver pyproject.toml).
"""
from __future__ import annotations

import socket
import sys
import threading
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_TITLE = "Automa"
DEFAULT_SIZE = (1200, 800)


def _port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_server(host: str, port: int, timeout_seconds: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _port_open(host, port):
            return True
        time.sleep(0.1)
    return False


def _start_server_in_thread(host: str, port: int) -> threading.Thread:
    from app.server import run_server

    def _runner() -> None:
        try:
            run_server(host=host, port=port)
        except Exception:  # noqa: BLE001  - swallow para que la ventana decida cuando cerrar
            pass

    thread = threading.Thread(target=_runner, name="automa-panel-http", daemon=True)
    thread.start()
    return thread


def launch(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    title: str = DEFAULT_TITLE,
    size: tuple[int, int] = DEFAULT_SIZE,
    fullscreen: bool = False,
) -> int:
    """Abre la ventana de escritorio. Retorna exit code para el CLI."""
    try:
        import webview
    except ImportError:
        print(
            "ERROR: pywebview no esta instalado. Instalar con: pip install pywebview",
            file=sys.stderr,
        )
        return 2

    _start_server_in_thread(host, port)
    if not _wait_for_server(host, port):
        print(
            f"ERROR: el servidor HTTP no respondio en {host}:{port} tras 8s.",
            file=sys.stderr,
        )
        return 1

    url = f"http://{host}:{port}/"
    width, height = size
    webview.create_window(
        title=title,
        url=url,
        width=width,
        height=height,
        resizable=True,
        fullscreen=fullscreen,
    )
    # Backend nativo: edgechromium en Windows 10/11, gtk/qt en otros.
    webview.start()
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="automa-desktop", description="Ventana nativa de Automa.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--width", type=int, default=DEFAULT_SIZE[0])
    parser.add_argument("--height", type=int, default=DEFAULT_SIZE[1])
    parser.add_argument("--fullscreen", action="store_true")
    args = parser.parse_args(argv)
    return launch(
        host=args.host,
        port=args.port,
        title=args.title,
        size=(args.width, args.height),
        fullscreen=args.fullscreen,
    )


if __name__ == "__main__":
    raise SystemExit(main())
