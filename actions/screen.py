from __future__ import annotations

from pathlib import Path
from typing import Any


def _capture_with_mss(output_path: Path) -> dict[str, Any]:
    import mss
    import mss.tools

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(output_path))
        return {
            "image_path": str(output_path),
            "width": sct_img.width,
            "height": sct_img.height,
            "method": "mss",
        }


def _capture_with_pillow(output_path: Path) -> dict[str, Any]:
    from PIL import ImageGrab

    img = ImageGrab.grab()
    img.save(output_path)
    return {
        "image_path": str(output_path),
        "width": img.width,
        "height": img.height,
        "method": "pillow",
    }


def capture_screenshot(output_path: str) -> dict[str, Any]:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        return _capture_with_mss(target)
    except Exception:
        try:
            return _capture_with_pillow(target)
        except Exception as exc:
            raise RuntimeError(
                "No fue posible capturar la pantalla. Revisa si el entorno tiene escritorio gráfico disponible."
            ) from exc


def _resolve_bbox(bbox: dict[str, int], screen_w: int, screen_h: int) -> tuple[int, int, int, int]:
    """Normaliza un bbox de usuario a (left, top, width, height) en pixeles.

    Acepta:
    - ``{left, top, width, height}`` o ``{left, top, right, bottom}``.
    - ``top``/``left`` negativos = relativo al borde opuesto (estilo CSS).
    - ``width``/``height`` mayores al monitor se clampean al borde.
    """
    left = int(bbox.get("left", 0))
    top = int(bbox.get("top", 0))
    if left < 0:
        left = screen_w + left
    if top < 0:
        top = screen_h + top
    if "width" in bbox and "height" in bbox:
        width = int(bbox["width"])
        height = int(bbox["height"])
    else:
        width = int(bbox["right"]) - left
        height = int(bbox["bottom"]) - top
    if width <= 0 or height <= 0:
        raise ValueError(f"bbox produce dimensiones invalidas: {width}x{height}")
    width = min(width, screen_w - left)
    height = min(height, screen_h - top)
    return left, top, width, height


def _capture_region_mss(target: Path, bbox: dict[str, int]) -> dict[str, Any]:
    import mss
    import mss.tools

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        left, top, width, height = _resolve_bbox(bbox, monitor["width"], monitor["height"])
        region = {"left": monitor["left"] + left, "top": monitor["top"] + top, "width": width, "height": height}
        sct_img = sct.grab(region)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(target))
        return {
            "image_path": str(target),
            "width": sct_img.width,
            "height": sct_img.height,
            "bbox": {"left": left, "top": top, "width": width, "height": height},
            "method": "mss",
        }


def _capture_region_pillow(target: Path, bbox: dict[str, int]) -> dict[str, Any]:
    from PIL import ImageGrab

    full = ImageGrab.grab()
    left, top, width, height = _resolve_bbox(bbox, full.width, full.height)
    cropped = full.crop((left, top, left + width, top + height))
    cropped.save(target)
    return {
        "image_path": str(target),
        "width": cropped.width,
        "height": cropped.height,
        "bbox": {"left": left, "top": top, "width": width, "height": height},
        "method": "pillow",
    }


def capture_active_window(output_path: str) -> dict[str, Any]:
    """Captura solo la ventana actualmente en foco.

    Resuelve el rectángulo de la ventana activa vía ``pygetwindow`` y
    delega el screenshot a :func:`capture_region`. Si no se puede
    identificar la ventana activa (sesión headless, ningún foco),
    levanta ``RuntimeError`` con motivo legible.
    """
    try:
        import pygetwindow as gw
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError(f"pygetwindow no disponible: {exc}") from exc

    win = gw.getActiveWindow()
    if win is None:
        raise RuntimeError("No hay ventana activa identificable (sesion headless o sin foco).")

    title = getattr(win, "title", "") or ""
    left = max(int(win.left), 0)
    top = max(int(win.top), 0)
    width = int(win.width)
    height = int(win.height)
    if width <= 0 or height <= 0:
        raise RuntimeError(f"Ventana activa con dimensiones invalidas: {width}x{height} (titulo='{title}').")

    result = capture_region(output_path, {"left": left, "top": top, "width": width, "height": height})
    result["window_title"] = title
    return result


def capture_region(output_path: str, bbox: dict[str, int]) -> dict[str, Any]:
    """Captura una región rectangular del escritorio principal.

    Ver :func:`_resolve_bbox` para el formato del ``bbox``.
    """
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        return _capture_region_mss(target, bbox)
    except Exception:
        try:
            return _capture_region_pillow(target, bbox)
        except Exception as exc:
            raise RuntimeError(
                "No fue posible capturar la región. Revisa si hay escritorio gráfico disponible."
            ) from exc
