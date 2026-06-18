# 📊 Snapshot del Task Manager

## 🎯 Para qué sirve

Capturar de un click qué está corriendo en este momento: abre Task Manager con su atajo nativo `Ctrl+Shift+Esc`, espera a que renderice, saca un PNG del escritorio y pasa la imagen por OCR para extraer los nombres de procesos visibles a un JSON con timestamp.

Útil para auditoría puntual sin depender de `tasklist`/`psutil`, o para dejar evidencia visual + textual cuando se investiga lentitud o consumo anómalo.

## 🧭 Flujo paso a paso

1. **open_taskmgr** → envía `Ctrl+Shift+Esc` (atajo nativo de Windows).
2. **wait_render** → espera 1.5 s a que Task Manager renderice la lista.
3. **capture_screen** → PNG del escritorio completo a `output/screenshots/taskmgr_{now}.png`.
4. **ocr_processes** → OCR con `pytesseract` sobre la imagen.
5. **save_snapshot** → JSON con metadata del screenshot + texto OCR a `output/reports/taskmgr_snapshot_{now}.json`.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `dry_run` | bool | `false` | Si `true`, no manda el hotkey ni captura. |

## 📋 Requisitos

- Sesión Windows interactiva.
- `pyautogui`, `mss`, `pytesseract` (dependencias base).
- Tesseract OCR instalado en el sistema (binario, no Python).

## ⚠️ Limitaciones honestas

- El OCR captura **todo el escritorio**, no solo la ventana de Task Manager. Si tenés otras apps visibles, su texto también queda en el JSON.
- 1.5 s puede ser corto en equipos lentos — ajustá `wait_render` si la captura sale con Task Manager aún cargando.
- El UI de Task Manager varía entre Windows 10 y 11 (vista compacta vs detallada). El OCR funciona igual pero los nombres de columnas cambian.

## 📤 Salidas

- `output/screenshots/taskmgr_<timestamp>.png`
- `output/reports/taskmgr_snapshot_<timestamp>.json` (metadata + OCR)

## ⚡ Ejecución

CLI:

```bash
flujo run flows/17_taskmgr_snapshot
```
