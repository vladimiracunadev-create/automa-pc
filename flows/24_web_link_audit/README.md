# 🔗 Auditor de links rotos

## 🎯 Para qué sirve

Detectar links muertos en una página propia (landing, docs, intranet) antes de que los encuentre un usuario. Extrae los links con navegador real y verifica el estado de cada uno, en orden de aparición.

## 🧭 Flujo paso a paso

1. **extract_links** → `browser.extract_content` saca los links absolutos, deduplicados, de `target_url`.
2. **check_links** → `http.check_urls`: HEAD con redirects para `http(s)` (fallback GET ante 405/501), existencia en disco para `file://`, `mailto:`/`tel:` reportados como `skipped`.
3. **evaluate_links** → `rules.evaluate`: `broken_count > 0` → `alerta`.
4. **write_report** → `output/reports/link_audit_<ts>.json` con el detalle por link.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `target_url` | string | `data/web/site_demo/index.html` | Página a auditar (URL o HTML local). |
| `max_links` | int | `100` | Cota de links extraídos y verificados. Si hay más, `truncated: true`. |
| `timeout` | float | `10` | Timeout por request HTTP. |
| `wait_seconds` | float | `0.2` | Espera post-load. |

## 📋 Requisitos

- `playwright` + Chromium para la extracción.
- Internet solo si la página o sus links son remotos (la demo local no lo necesita: el link roto es un `file://` inexistente).

## ⚠️ Limitaciones honestas

- Verifica **status**, no contenido: un link que responde 200 con "página no encontrada" en el body pasa como ok (soft-404).
- Algunos servers bloquean HEAD o responden distinto a bots; el fallback GET mitiga pero no elimina falsos positivos.
- No audita links dentro de JS (`onclick`), solo `<a href>`.

## 📤 Salidas

- `output/reports/link_audit_<ts>.json` — `results[]` por link (status, ok, detail), `broken[]`, contadores y decisión.

## ⚡ Ejecución

```bash
automa run flows/24_web_link_audit
# la demo incluye site_demo/no_existe.html → broken_count=1, status alerta
```
