# 🗂️ Familias Y Casos

> Catálogo completo, matriz de compatibilidad y honestidad sobre qué requiere cada flow.

![Familias y Casos](assets/cover-automa-pc.svg)

La documentación usa dos niveles:

- **Familia**: categoría conceptual del problema.
- **Caso**: flow ejecutable con manifest, contexto y README propio.

> [!IMPORTANT]
> Cada flow tiene un README con la lista exhaustiva de pasos, requisitos, limitaciones y control. **No son demos** — son procesos reales auditables. Los 27 fueron probados end-to-end en Windows 11 + Python 3.12.

---

## 🧱 Familias Actuales

| Familia | Uso | Riesgo de efectos colaterales |
| --- | --- | --- |
| 📷 `pantalla` | captura, análisis visual, OCR y decisiones sobre interfaz | 🟡 captura puede contener info sensible |
| 🖱️ `escritorio` | interacción directa con UI local (clicks, teclas) | 🔴 envía teclas/clicks reales |
| 🌐 `navegador` | apertura de recursos web/locales y captura asistida | 🟡 abre pestañas en el navegador |
| 🖥️ `sistema` | salud del equipo, procesos y métricas locales | 🟢 solo lee |
| 📄 `documentos` | entrada documental, resumen y routing | 🟢 solo lee y escribe en `output/` |
| 📁 `filesystem` | inventario y operaciones sobre archivos/carpetas | 🟢 lectura por defecto |

---

## 📊 Matriz De Compatibilidad

| # | Caso | Familia | Win | Linux | macOS | Headless | Internet | Tesseract | pyautogui | Detalle |
| - | ---- | ------- | --- | ----- | ----- | -------- | -------- | --------- | --------- | ------- |
| 01 | 📷 [screen_capture_analyze](../flows/01_screen_capture_analyze/README.md) | pantalla | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ solo si `analyzer=ocr` | ❌ | Sesión gráfica obligatoria |
| 02 | 🌐 [screen_capture_browser](../flows/02_screen_capture_browser/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ⚠️ si URL externa | ❌ | ❌ | Playwright headless captura DOM puro |
| 03 | 📁 [folder_inventory](../flows/03_folder_inventory/README.md) | filesystem | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | **Solo stdlib. Más portable.** |
| 04 | 📄 [document_drop_pipeline](../flows/04_document_drop_pipeline/README.md) | documentos | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Solo lee texto plano |
| 05 | 🖥️ [system_healthcheck](../flows/05_system_healthcheck/README.md) | sistema | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | psutil. **Más rápido (~0.7s)** |
| 06 | ⚙️ [process_watchdog](../flows/06_process_watchdog/README.md) | sistema | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Algunos procesos requieren admin en Windows |
| 07 | 📋 [browser_form_filler](../flows/07_browser_form_filler/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Playwright + form 10 campos + 100 seeds sin repetir |
| 08 | 🔒 [windows_lock_workstation](../flows/08_windows_lock_workstation/README.md) | sistema | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | `Win+L` — bloquea sesión |
| 09 | 🖥️ [show_desktop_capture](../flows/09_show_desktop_capture/README.md) | pantalla | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | `Win+D` + captura escritorio limpio |
| 10 | 📁 [explorer_open_path](../flows/10_explorer_open_path/README.md) | sistema | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | `explorer.exe <path>` |
| 11 | ⚙️ [settings_open_section](../flows/11_settings_open_section/README.md) | sistema | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | URI `ms-settings:...` |
| 12 | 👁️ [desktop_ocr_inventory](../flows/12_desktop_ocr_inventory/README.md) | pantalla | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | OCR de todo lo visible → JSON con bboxes |
| 13 | 📝 [notepad_quick_note](../flows/13_notepad_quick_note/README.md) | sistema | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | Abre Notepad y tipea |
| 14 | ⌨️ [run_dialog_command](../flows/14_run_dialog_command/README.md) | sistema | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | `Win+R` + comando + Enter |
| 15 | 📋 [clipboard_capture](../flows/15_clipboard_capture/README.md) | sistema | ✅ | ⚠️ xclip/xsel | ✅ | ❌ | ❌ | ❌ | ❌ | Snapshot del clipboard → JSON |
| 16 | 🖼️ [active_window_screenshot](../flows/16_active_window_screenshot/README.md) | pantalla | ✅ | ⚠️ X11 | ✅ | ❌ | ❌ | ❌ | ❌ | Solo la ventana en foco |
| 17 | 📊 [taskmgr_snapshot](../flows/17_taskmgr_snapshot/README.md) | pantalla | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | Task Manager + captura + OCR |
| 18 | 🛡️ [powershell_audit](../flows/18_powershell_audit/README.md) | sistema | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | PowerShell con allowlist read-only |
| 19 | 🪟 [taskbar_capture](../flows/19_taskbar_capture/README.md) | pantalla | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Recorte parcial del monitor |
| 20 | 🔇 [volume_mute_toggle](../flows/20_volume_mute_toggle/README.md) | sistema | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | Tecla multimedia `volumemute` |
| 21 | 🕸️ [web_content_extract](../flows/21_web_content_extract/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ⚠️ si URL externa | ❌ | ❌ | Lee el DOM como datos (Playwright) |
| 22 | 🗺️ [web_site_map](../flows/22_web_site_map/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ⚠️ si sitio externo | ❌ | ❌ | Crawl BFS acotado + robots.txt |
| 23 | 🔔 [web_change_detector](../flows/23_web_change_detector/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ⚠️ si URL externa | ❌ | ❌ | Hash vs corrida anterior + notify |
| 24 | 🔗 [web_link_audit](../flows/24_web_link_audit/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ⚠️ si links externos | ❌ | ❌ | HEAD/GET por link + alerta |
| 25 | 📊 [web_table_extract](../flows/25_web_table_extract/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ⚠️ si URL externa | ❌ | ❌ | Tablas HTML → CSV + JSON |
| 26 | 📈 [web_value_monitor](../flows/26_web_value_monitor/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ⚠️ si URL externa | ❌ | ❌ | Selector CSS + umbral + tracking |
| 27 | 🗄️ [web_page_archive](../flows/27_web_page_archive/README.md) | navegador | ✅ | ✅ | ✅ | ✅ | ⚠️ si URL externa | ❌ | ❌ | Markdown + PNG + SHA-256 |

Leyenda: ✅ funciona · ❌ NO requerido · ⚠️ requerido condicionalmente · 🟢🟡🔴 nivel de riesgo.

---

## 🎯 Para empezar

| Si estás | Empieza con |
| --- | --- |
| 🆕 Recién instalando, validando que el motor anda | **05** healthcheck — el más rápido y seguro |
| 🧪 Probando captura de pantalla en este equipo | **01** screen_capture_analyze con `analyzer=mock` |
| 🌐 Capturar página web headless (sin escritorio) | **02** screen_capture_browser (Playwright) |
| 📁 Necesitas auditar archivos | **03** folder_inventory |
| 📥 Procesas documentos en una carpeta | **04** document_drop_pipeline |
| ⚙️ Diagnosticar procesos pesados | **06** process_watchdog |
| 📋 Llenado automatizado de formularios web | **07** browser_form_filler (Playwright + 100 seeds) |
| 🔒 Atajo de teclado para bloquear el equipo | **08** windows_lock_workstation |
| 🖼️ Documentar una ventana específica con captura | **16** active_window_screenshot |
| 📋 Auditar/persistir contenido del portapapeles | **15** clipboard_capture |
| 🛡️ Snapshot de auditoría con PowerShell sin abrir consola | **18** powershell_audit |

---

## ✅ Criterios Para Agregar Un Caso

Un nuevo caso debe:

1. 🎯 Tener un problema operativo claro.
2. 📋 Incluir `manifest.json` válido contra `schemas/manifest.schema.json`.
3. ⚙️ Incluir `context.example.json`.
4. 📚 Incluir README con esta estructura: **🎯 para qué · 🧭 flujo paso a paso · ⚙️ configuración · 📋 requisitos · 🛡️ sandbox sugerido · ⚠️ limitaciones · 🎮 control · 📤 salidas · ⚡ ejecución**.
5. 🔌 Usar acciones registradas o agregar la acción correspondiente con su test.
6. ✅ Pasar `python scripts/validate_project.py` y `pytest`.
7. 🛡️ Evitar efectos destructivos por defecto. Si los hay, declararlos en la sección "Limitaciones" con `[!WARNING]`.

---

## 🔢 Nomenclatura

El prefijo numérico ordena los casos para lectura humana. No representa versión del producto. Si un nuevo caso reemplaza a otro, se documenta la relación en el README del caso en lugar de renombrar todo el árbol.
