# 🕸️ Extractor de contenido web

## 🎯 Para qué sirve

Leer una página web **como datos**, no como imagen: título, texto visible, links, metadatos y tablas del DOM ya renderizado por Chromium. Es la base de la familia de casos web (22–27). Al renderizar con navegador real, funciona también en páginas que arman su contenido con JavaScript.

## 🧭 Flujo paso a paso

1. **extract_page** → `browser.extract_content` abre `target_url` headless y devuelve `{title, text, links, meta, tables, content_hash}`.
2. **capture_evidence** → (solo si `take_screenshot` es `true`) `browser.capture_page` deja un PNG full-page de evidencia.
3. **write_report** → `filesystem.write_json` persiste todo en `output/reports/web_content_<ts>.json`.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `target_url` | string | `data/web/demo_page.html` | URL `http(s)://` o ruta a un `.html` local. |
| `include_tables` | bool | `true` | Extraer también las tablas HTML como matrices de celdas. |
| `max_links` | int | `100` | Cota explícita de links extraídos (deduplicados, en orden de aparición). |
| `wait_seconds` | float | `0.5` | Espera post-load para dar tiempo al JS de la página. |
| `take_screenshot` | bool | `true` | Dejar además un PNG de evidencia. |

## 📋 Requisitos

- `playwright` Python: `pip install playwright`
- Chromium descargado: `python -m playwright install chromium`
- Internet solo si `target_url` es remota (el default es local).

## ⚠️ Limitaciones honestas

- El contenido de una web remota **cambia entre corridas** — lo determinista es el comportamiento (cotas, orden, estructura de salida), no lo que el sitio publique.
- No ejecuta scroll infinito ni clicks: extrae lo que el DOM tiene tras `load` + `wait_seconds`.
- Páginas detrás de login quedan fuera (no gestiona sesiones ni credenciales).

## 📤 Salidas

- `output/reports/web_content_<ts>.json` — contenido estructurado completo.
- `output/screenshots/web_content_<ts>.png` — evidencia visual (opcional).

## ⚡ Ejecución

CLI:

```bash
automa run flows/21_web_content_extract
```
