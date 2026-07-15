# 📊 Extractor de tablas web a dataset

## 🎯 Para qué sirve

Convertir cualquier tabla HTML en dataset usable: precios de un proveedor, rankings, horarios, inventarios publicados en una web → CSV listo para Excel/pandas. Como lee el DOM renderizado, sirve también para tablas que arma JavaScript.

## 🧭 Flujo paso a paso

1. **extract_tables** → `browser.extract_content` con `include_tables` extrae cada `<table>` como matriz de celdas y escribe `table_NN.csv` por tabla en un directorio fechado.
2. **write_report** → `summary.json` en el mismo directorio con las rutas CSV y los datos crudos.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `target_url` | string | `data/web/demo_page.html` | Página con tablas (URL o HTML local). |
| `wait_seconds` | float | `0.5` | Espera post-load para tablas generadas por JS. |

## 📋 Requisitos

- `playwright` + Chromium.
- Internet solo si `target_url` es remota.

## ⚠️ Limitaciones honestas

- Celdas con `colspan`/`rowspan` se extraen como texto plano por fila: la matriz no reconstruye la geometría combinada.
- Tablas hechas con `<div>` + CSS grid (sin `<table>`) no se detectan.
- El CSV usa el texto visible de cada celda: pierde links y formato interno.

## 📤 Salidas

- `output/reports/web_tables_<ts>/table_01.csv`, `table_02.csv`, ... — una por tabla.
- `output/reports/web_tables_<ts>/summary.json` — rutas + datos crudos.

## ⚡ Ejecución

```bash
automa run flows/25_web_table_extract
```
