# 📈 Monitor de valor web con umbral

## 🎯 Para qué sirve

Vigilar **un número concreto** publicado en una web — precio de un producto, stock disponible, versión de un software, tipo de cambio — y recibir alerta cuando cruza un umbral o cambia. Es la variante quirúrgica del caso 23: al mirar solo el elemento del selector, el resto de la página puede cambiar sin generar ruido.

## 🧭 Flujo paso a paso

1. **read_value** → `browser.extract_content` lee el elemento del `selector` CSS, lo parsea a número (`$ 1.499,90` → `1499.9`) y lo compara contra la corrida anterior (tracking persistente).
2. **evaluate_value** → `rules.evaluate` en orden: selector inexistente → `error` · valor > `threshold` → `alerta` · valor cambió → `aviso` · si no → `ok`.
3. **notify_value** → `notify.send` solo si el status no es `ok`.
4. **write_report** → `output/reports/value_monitor_<ts>.json`.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `target_url` | string | `data/web/demo_page.html` | Página a vigilar. |
| `selector` | string | `#precio` | Selector CSS del elemento con el valor. |
| `threshold` | number | `1000` | Umbral: `valor > threshold` → alerta. |
| `state_path` | string | `data/web_watch/precio_demo.json` | Tracking persistente. Uno por valor vigilado. |
| `notify_backend` | string | `file` | `log`, `file` o `webhook`. |
| `notify_target` | string | `output/notifications/value_monitor.log` | Archivo o URL según backend. |

## 📋 Requisitos

- `playwright` + Chromium.
- Conocer el selector CSS del valor (inspeccionar la página con F12 → copy selector).

## ⚠️ Limitaciones honestas

- Si el sitio cambia su HTML, el selector muere — por eso la regla `selector_no_encontrado` avisa con `error` en vez de fallar en silencio.
- El parseo numérico es heurístico (documentado en `actions/browser_extract.py`): formatos exóticos pueden requerir ajuste.
- Umbral solo `>` en la demo; para bandas (min/max) agregar una segunda regla `lt` en el manifest.

## 📤 Salidas

- `output/reports/value_monitor_<ts>.json` — valor actual/anterior + decisión.
- `output/notifications/value_monitor.log` — una línea por evento (backend `file`).
- `data/web_watch/precio_demo.json` — estado persistente.

## ⚡ Ejecución

```bash
automa run flows/26_web_value_monitor
# la demo: $ 1.499,90 > 1000 → alerta en la primera corrida
```
