# 🗺️ Mapa de sitio acotado (crawl BFS)

## 🎯 Para qué sirve

Generar un **sitemap por observación real** — qué páginas existen, a qué profundidad y cómo se enlazan — recorriendo el sitio con navegador, no leyendo el `sitemap.xml` declarado. Útil para inventariar una intranet, documentar un sitio propio o alimentar el auditor de links (caso 24).

## 🧭 Flujo paso a paso

1. **crawl** → `browser.crawl_site` hace BFS desde `start_url`: links del mismo dominio, en orden de aparición en el DOM, deduplicados, hasta `max_pages`/`max_depth`. Consulta `robots.txt` por host (http/https) si `respect_robots`.
2. **write_report** → persiste el inventario en `output/reports/site_map_<ts>.json`.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `start_url` | string | `data/web/site_demo/index.html` | Página de partida (URL o HTML local). |
| `max_pages` | int | `10` | Máximo de páginas visitadas. Cota dura — nunca crawl abierto. |
| `max_depth` | int | `2` | Profundidad máxima de links desde el inicio. |
| `same_domain_only` | bool | `true` | No salir del dominio de `start_url`. |
| `delay_seconds` | float | `0.2` | Pausa de cortesía entre páginas. |
| `respect_robots` | bool | `true` | Consultar y respetar `robots.txt` (solo aplica a http/https). |
| `wait_seconds` | float | `0.2` | Espera post-load por página. |

## 📋 Requisitos

- `playwright` + Chromium (`pip install playwright && python -m playwright install chromium`).
- Internet solo si `start_url` es remota (el default es el mini-sitio local del repo).

## ⚠️ Limitaciones honestas

- Si el sitio tiene más páginas que `max_pages`, el reporte queda `truncated: true` — lo dice explícito, no cubre "todo" en silencio.
- Un link roto no aborta el crawl: queda registrado en `errors` y se sigue.
- No ejecuta formularios ni sigue links generados por interacción (solo `<a href>` presentes tras `load`).

## 📤 Salidas

- `output/reports/site_map_<ts>.json` — `pages[]` con url, depth, título, links_count, text_chars y hash; más `robots_blocked`, `errors`, `truncated`.

## ⚡ Ejecución

CLI:

```bash
automa run flows/22_web_site_map
```
