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

