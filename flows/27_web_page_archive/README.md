# 🗄️ Archivado offline de página web

## 🎯 Para qué sirve

Evidencia verificable de qué publicaba una web en un momento dado: términos y condiciones antes de aceptar, un precio ofertado, un aviso oficial. Guarda **contenido legible (Markdown) + evidencia visual (PNG) + metadatos con hash** — el trío que permite después demostrar y verificar.

## 🧭 Flujo paso a paso

1. **extract_and_save_markdown** → `browser.extract_content` escribe `output/archive/<slug>_<ts>.md` con título, metadatos, texto, tablas y links.
2. **capture_evidence** → `browser.capture_page` deja el PNG full-page del mismo momento.
3. **write_metadata** → JSON con URL, título, SHA-256 del texto y rutas de los otros dos archivos.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `target_url` | string | `data/web/demo_page.html` | Página a archivar. |
| `archive_slug` | string | `demo_page` | Prefijo de los archivos generados. |
| `wait_seconds` | float | `0.5` | Espera post-load. |

## 📋 Requisitos

- `playwright` + Chromium.
- Internet solo si `target_url` es remota.

## ⚠️ Limitaciones honestas

- No es un WARC ni un mirror navegable: guarda contenido y evidencia de UNA página, no el sitio con sus assets.
- El Markdown pierde el layout visual (para eso está el PNG al lado).
- Los pasos corren con segundos de diferencia: el timestamp del nombre puede variar en 1s entre archivos del mismo run.

## 📤 Salidas

- `output/archive/<slug>_<ts>.md` — contenido legible.
- `output/archive/<slug>_<ts>.png` — evidencia visual full-page.
- `output/archive/<slug>_<ts>.json` — metadatos + SHA-256.

## ⚡ Ejecución

```bash
automa run flows/27_web_page_archive
```
