# 🔔 Detector de cambios en página web

## 🎯 Para qué sirve

El patrón completo **detectar → decidir → alertar**: vigilar una página (precio, tablón de anuncios, fecha de resultados, changelog de un proveedor) y enterarse solo cuando cambia. Programado cada N minutos con el scheduler, reemplaza el F5 manual.

## 🧭 Flujo paso a paso

1. **extract_and_track** → `browser.extract_content` extrae el texto, calcula SHA-256 y lo compara contra `state_path` (tracking persistente; la primera corrida crea la línea base).
2. **evaluate_change** → `rules.evaluate`: `changed=true` → `alerta` · `first_run=true` → `baseline` · si no → `ok`.
3. **notify_change** → `notify.send` **solo si hubo cambio** (condición `when` sobre la decisión). Backend `log`, `file` o `webhook` (Slack/Discord-compatible).
4. **write_report** → persiste hash actual, anterior y decisión en `output/reports/web_change_<ts>.json`.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `target_url` | string | `data/web/demo_page.html` | Página a vigilar (URL o HTML local). |
| `state_path` | string | `data/web_watch/demo_page.json` | Archivo de tracking. Uno distinto por página vigilada. |
| `wait_seconds` | float | `0.5` | Espera post-load para el JS de la página. |
| `notify_backend` | string | `file` | `log` (stdout), `file` (append a `notify_target`) o `webhook` (POST JSON a `notify_target`). |
| `notify_target` | string | `output/notifications/web_changes.log` | Archivo o URL según backend. |

## 📋 Requisitos

- `playwright` + Chromium.
- Para backend `webhook`: URL accesible; token opcional vía `@secret:NOMBRE`.

## ⚠️ Limitaciones honestas

- Compara el **texto completo normalizado**: un banner rotativo o un contador visible dispara falsos positivos. Para vigilar un valor puntual usar el caso 26 (selector CSS).
- La detección es entre corridas: si la página cambia y vuelve a su estado anterior entre dos corridas, no se ve.
- Borrar `state_path` reinicia la línea base.

## 📤 Salidas

- `output/reports/web_change_<ts>.json` — hash actual/anterior + decisión.
- `output/notifications/web_changes.log` — una línea por cambio detectado (backend `file`).
- `data/web_watch/demo_page.json` — estado persistente entre corridas.

## ⚡ Ejecución

```bash
automa run flows/23_web_change_detector          # 1ª vez: baseline
# editar data/web/demo_page.html (p.ej. el precio) y repetir → alerta
automa run flows/23_web_change_detector
```
