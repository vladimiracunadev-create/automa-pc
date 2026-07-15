from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import url2pathname

import requests


def fetch_url(url: str, output_path: str | None = None, timeout: float = 15.0) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    result = {
        "url": url,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "content_length": len(response.text),
    }
    if output_path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(response.text, encoding="utf-8")
        result["output_path"] = str(target)
    return result


def check_urls(
    urls: list[str],
    timeout: float = 10.0,
    max_urls: int = 100,
    delay_seconds: float = 0.0,
) -> dict[str, Any]:
    """Verifica el estado de una lista de URLs en orden de entrada (determinista).

    - ``http(s)://`` → HEAD con redirects; fallback a GET si el server no
      soporta HEAD (405/501). ``ok`` = status < 400.
    - ``file://`` → existencia del archivo local (sirve para auditar links de
      páginas locales sin red).
    - Otros esquemas (``mailto:``, ``tel:``, ...) se reportan como ``skipped``.

    Cota explícita: se revisan a lo sumo ``max_urls``; si la lista era más
    larga, ``truncated=True`` lo deja registrado — nunca truncado silencioso.
    """
    all_urls = [str(u) for u in (urls or [])]
    truncated = len(all_urls) > int(max_urls)
    results: list[dict[str, Any]] = []
    for url in all_urls[: int(max_urls)]:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            local = Path(url2pathname(parsed.path))
            exists = local.exists()
            results.append(
                {
                    "url": url,
                    "ok": exists,
                    "status_code": None,
                    "detail": "archivo local existe" if exists else "archivo local no encontrado",
                }
            )
        elif parsed.scheme in ("http", "https"):
            entry: dict[str, Any] = {"url": url, "ok": False, "status_code": None}
            try:
                response = requests.head(url, timeout=timeout, allow_redirects=True)
                if response.status_code in (405, 501):
                    response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
                    response.close()
                entry["status_code"] = response.status_code
                entry["ok"] = response.ok
            except requests.RequestException as exc:
                entry["detail"] = str(exc)
            results.append(entry)
        else:
            results.append(
                {
                    "url": url,
                    "ok": None,
                    "skipped": True,
                    "detail": f"esquema no verificable: {parsed.scheme or '(vacío)'}",
                }
            )
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    checked = [r for r in results if not r.get("skipped")]
    broken = [r["url"] for r in checked if not r["ok"]]
    return {
        "total_input": len(all_urls),
        "checked_count": len(checked),
        "ok_count": len(checked) - len(broken),
        "broken_count": len(broken),
        "broken": broken,
        "skipped_count": len(results) - len(checked),
        "truncated": truncated,
        "results": results,
    }
