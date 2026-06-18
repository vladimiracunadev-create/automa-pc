from __future__ import annotations

import platform
import time
from datetime import datetime, timezone
from typing import Any

import psutil


def wait_seconds(seconds: float) -> dict[str, Any]:
    time.sleep(seconds)
    return {"waited_seconds": seconds}



def snapshot_system() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "memory_percent": memory.percent,
        "memory_used_mb": round(memory.used / 1024 / 1024, 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
    }



def top_processes(limit: int = 10, sort_by: str = "memory") -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = proc.info
            mem_bytes = int(info.get("memory_info").rss) if info.get("memory_info") else 0
            entries.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name") or "desconocido",
                    "cpu_percent": float(info.get("cpu_percent") or 0.0),
                    "memory_mb": round(mem_bytes / 1024 / 1024, 2),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_percent" if sort_by == "cpu" else "memory_mb"
    top = sorted(entries, key=lambda item: item[key], reverse=True)[:limit]
    return {"sort_by": key, "processes": top, "total_seen": len(entries)}



def watch_processes(processes: list[dict[str, Any]], memory_mb_threshold: float = 250.0, cpu_percent_threshold: float = 60.0) -> dict[str, Any]:
    alerts = []
    for proc in processes:
        reasons = []
        if float(proc.get("memory_mb", 0.0)) >= memory_mb_threshold:
            reasons.append(f"memory>={memory_mb_threshold}MB")
        if float(proc.get("cpu_percent", 0.0)) >= cpu_percent_threshold:
            reasons.append(f"cpu>={cpu_percent_threshold}%")
        if reasons:
            alerts.append({**proc, "reasons": reasons})
    return {
        "alerts": alerts,
        "alert_count": len(alerts),
        "thresholds": {
            "memory_mb_threshold": memory_mb_threshold,
            "cpu_percent_threshold": cpu_percent_threshold,
        },
    }

def read_clipboard(max_chars: int = 10000) -> dict[str, Any]:
    """Lee el texto actual del portapapeles del sistema.

    Trunca a ``max_chars`` para evitar volcar volumenes grandes a logs/JSON.
    Devuelve siempre un payload con ``available: bool`` — si no hay backend
    de portapapeles (servidor headless, sesion SSH sin DISPLAY), retorna
    available=False con ``reason`` legible, en vez de tirar excepcion.
    """
    try:
        import pyperclip
    except Exception as exc:
        return {"available": False, "reason": f"pyperclip no instalado: {exc}", "text": "", "length": 0, "truncated": False}
    try:
        raw = pyperclip.paste()
    except Exception as exc:
        return {"available": False, "reason": f"backend de portapapeles no disponible: {exc}", "text": "", "length": 0, "truncated": False}
    if raw is None:
        raw = ""
    text = str(raw)
    length = len(text)
    truncated = length > max_chars
    if truncated:
        text = text[:max_chars]
    return {"available": True, "text": text, "length": length, "truncated": truncated, "max_chars": max_chars}


# Allowlist por defecto: comandos read-only seguros para auditoria.
_PS_DEFAULT_ALLOWLIST = (
    "Get-Date",
    "Get-Process",
    "Get-Service",
    "Get-ComputerInfo",
    "Get-CimInstance",
    "Get-WmiObject",
    "Get-Disk",
    "Get-Volume",
    "Get-NetAdapter",
    "Get-NetIPAddress",
    "Get-EventLog",
    "Get-Host",
    "Get-Location",
)


def run_powershell(command: str, allowlist: list[str] | None = None, timeout_seconds: float = 30.0) -> dict[str, Any]:
    """Ejecuta un comando PowerShell con allowlist estricta.

    El ``command`` debe empezar EXACTAMENTE con uno de los verbos permitidos
    (case-sensitive). Cualquier intento de chain (``;``, ``|``, ``&&``, backtick)
    o redireccion (``>``, ``<``) se rechaza antes de invocar PowerShell.

    Sin allowlist explicito usa :data:`_PS_DEFAULT_ALLOWLIST` (read-only).
    Para escenarios mas amplios, pasar ``allowlist`` con los verbos deseados.
    """
    import subprocess

    if not command or not isinstance(command, str):
        raise ValueError("command vacio o no es string")
    trimmed = command.strip()
    forbidden_chars = (";", "|", "&", "`", ">", "<", "$(", "$_")
    for token in forbidden_chars:
        if token in trimmed:
            raise ValueError(f"PowerShell command contiene token prohibido: {token!r}")

    verbs = tuple(allowlist) if allowlist else _PS_DEFAULT_ALLOWLIST
    head = trimmed.split()[0]
    if head not in verbs:
        raise ValueError(f"comando '{head}' fuera del allowlist: {verbs}")

    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", trimmed],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    return {
        "command": trimmed,
        "exit_code": proc.returncode,
        "stdout": stdout[:50000],
        "stderr": stderr[:5000],
        "stdout_truncated": len(stdout) > 50000,
        "stderr_truncated": len(stderr) > 5000,
        "allowlist_used": list(verbs),
    }

