# 04 · Mapa completo del código

> Inventario jerárquico del repositorio en el commit `ff246ab`. Para cada elemento:
> ubicación, responsabilidad, dependencias, quién lo usa y **estado aparente**
> (activo · legado · duplicado · experimental · no determinado).

---

## 1. Árbol de primer nivel

```text
automa-pc/
├── actions/        12 archivos · las 36 acciones ejecutables
├── app/             3 archivos · panel HTTP y ventana nativa
├── engine/         20 archivos · motor, contrato, política, persistencia
├── decision/        3 archivos · stubs sin uso (ver §6)
├── plugins/         6 archivos · analizadores de imagen intercambiables
├── flows/          27 carpetas · el catálogo declarativo
├── schemas/         1 archivo  · JSON Schema del manifest
├── scripts/         2 archivos versionados · validador y smoke test
├── installer/       4 archivos · PyInstaller, Inno Setup, entry point, build local
├── tests/          17 archivos · 150 pruebas
├── data/                      · HTML de demo, dataset semilla, carpeta de entrada
├── configs/                   · contexto persistido por flow
├── db/ logs/ state/ output/ secrets/   · almacenes en tiempo de ejecución
├── docs/                      · documentación previa + esta carpeta
└── .github/workflows/  6 workflows de CI
```

Conteo verificado con `git ls-files`: **210 archivos versionados**, de los cuales **64 son
`.py`** (47 de producción, 17 de pruebas).

## 2. `engine/` — el motor

20 archivos, 1 841 líneas. Es el núcleo del sistema y ningún módulo suyo depende de
`actions/` ni de `app/`.

| Archivo | Líneas | Responsabilidad | Depende de | Lo usan | Estado |
|---|---:|---|---|---|---|
| `orchestrator.py` | 263 | Bucle de ejecución, política, transiciones, persistencia | Casi todo `engine/` | `app/server.py`, `runner.py`, `scheduler.py`, `smoke_test.py` | **Activo · crítico** |
| `database.py` | 378 | Las 7 tablas SQLite y todo el SQL del sistema | `paths.py`, `cron.py` (import diferido) | `orchestrator`, `logger`, `catalog`, `metrics`, `scheduler`, `app/server` | **Activo · crítico** |
| `action_registry.py` | 109 | Registro perezoso de las 36 acciones + entry points | `importlib` | `orchestrator`, `validate_project` | **Activo · crítico** |
| `sandbox.py` | 112 | `SandboxPolicy`: acciones, rutas, secretos, tiempo | `os`, `pathlib` | `orchestrator` | **Activo · crítico** |
| `cron.py` | 114 | Cron de 5 campos, cálculo de próxima ejecución | `datetime` | `database.set_schedule`, `mark_schedule_run`, `app/server` | **Activo** |
| `metrics.py` | 107 | Agregados SQL y exposición Prometheus | `database.connect` | `app/server` | **Activo** |
| `catalog.py` | 87 | Lectura de `flows/` y unión con datos de la base | `database` | `app/server`, `runner`, `scheduler` | **Activo** |
| `scheduler.py` | 86 | Bucle de disparo por horario con lock | `catalog`, `database`, `orchestrator` | `app/server`, `runner` | **Activo** |
| `loader.py` | 74 | `manifest.json` → dataclasses; resolución del contexto | `models` | `orchestrator` | **Activo · crítico** |
| `introspection.py` | 69 | Detecta qué archivos de `output/` produjo la corrida | `pathlib` | `orchestrator._refresh_outputs` | **Activo** |
| `manifest_schema.py` | 64 | Validación contra JSON Schema con respaldo estructural | `jsonschema` (opcional), `paths` | **Solo** `scripts/validate_project.py` | **Activo · no en runtime** |
| `template.py` | 63 | `render_value`: `{clave}` y `{obj.campo}` | `re`, `datetime` | `orchestrator` | **Activo · crítico** |
| `paths.py` | 61 | `root_dir()` de solo lectura y `data_dir()` escribible | `os`, `sys` | `database`, `secrets`, `orchestrator`, `app/server`, `manifest_schema` | **Activo · crítico** |
| `conditions.py` | 61 | 13 operadores + `all`/`any`/`not` | `re` | `orchestrator` | **Activo · crítico** |
| `secrets.py` | 59 | Entorno primero, archivo después | `paths` | `actions/notify`, `app/server` | **Activo** |
| `runner.py` | 49 | CLI `list` / `run` / `scheduler` | `catalog`, `database`, `orchestrator`, `scheduler` | Entry point `automa` | **Activo · con defecto conocido** |
| `models.py` | 38 | `FlowDefinition`, `StepDefinition`, `TransitionDefinition` | `dataclasses` | `loader`, `orchestrator` | **Activo · crítico** |
| `logger.py` | 26 | JSONL + inserción en la tabla `events` | `database` | `orchestrator` | **Activo** |
| `state_store.py` | 21 | Volcado del estado a `state/*.json` | `json`, `pathlib` | `orchestrator` | **Activo** |
| `__init__.py` | 0 | Marcador de paquete | — | — | **Activo** |

**Nota sobre `runner.py`:** su `main()` termina imprimiendo JSON con
`ensure_ascii=False`, lo que provoca `UnicodeEncodeError` en una consola Windows
`cp1252`. Verificado durante el análisis. Detalle en
[02 §5](02-installation-and-execution.md#5-comandos-disponibles-tras-instalar) y
[15](15-risks-and-technical-debt.md).

**Nota sobre `catalog.py`:** define su propio `root_dir()` local
(`Path(__file__).resolve().parent.parent`) en vez de importar `engine.paths.root_dir`.
Ambas devuelven lo mismo en desarrollo, pero **la de `catalog.py` ignora `AUTOMA_ROOT` y
`sys._MEIPASS`**. `INFERENCIA`: en el binario empaquetado, `catalog.flows_dir()` no
apuntaría a los flows extraídos por PyInstaller. Duplicación con consecuencia, registrada
en [15](15-risks-and-technical-debt.md).

## 3. `actions/` — el trabajo efectivo

12 archivos, 1 832 líneas. Cada función pública es una acción invocable desde un manifest.

| Archivo | Líneas | Acciones que expone | Dependencia externa | Estado |
|---|---:|---|---|---|
| `browser_extract.py` | 567 | `browser.extract_content`, `browser.crawl_site` | Playwright, requests | **Activo** |
| `browser_form.py` | 204 | `browser.fill_form` | Playwright | **Activo** |
| `vision.py` | 197 | `vision.analyze_image`, `ocr_image`, `find_text_in_image`, `select_image`, `inspect_screen_target` | Pillow (vía plugins) | **Activo (parcial)** |
| `system.py` | 162 | `system.wait_seconds`, `read_clipboard`, `run_powershell`, `snapshot_system`, `top_processes`, `watch_processes` | psutil, pyperclip, PowerShell | **Activo** |
| `screen.py` | 158 | `screen.capture_screenshot`, `capture_region`, `capture_active_window` | mss, Pillow, PyGetWindow | **Activo** |
| `filesystem.py` | 121 | `filesystem.ensure_directory`, `list_directory`, `write_json`, `read_text_file`, `classify_file_inventory`, `summarize_text_folder`, `move_file` | Ninguna | **Activo (parcial)** |
| `http_actions.py` | 97 | `http.fetch_url`, `http.check_urls` | requests | **Activo (parcial)** |
| `browser_capture.py` | 93 | `browser.capture_page` | Playwright | **Activo** |
| `ui.py` | 91 | `ui.open_url`, `open_file_in_browser`, `launch_process`, `hotkey`, `type_text`, `click`, `click_bbox` | pyautogui, webbrowser | **Activo (parcial)** |
| `notify.py` | 78 | `notify.send` | requests (import perezoso) | **Activo** |
| `rules.py` | 64 | `rules.evaluate` | Ninguna | **Activo** |
| `__init__.py` | 0 | Marcador de paquete | — | **Activo** |

### Las 10 acciones que ningún flow usa

Verificado leyendo los 27 manifests y comparando con `_BUILT_IN_ACTIONS`: de las **36
acciones registradas, solo 26 aparecen en algún flow**. Las diez restantes existen,
están registradas, funcionan y no tienen ningún caso que las ejerza:

| Acción | Módulo | Estado |
|---|---|---|
| `filesystem.ensure_directory` | `actions/filesystem.py` | Disponible sin uso |
| `filesystem.read_text_file` | `actions/filesystem.py` | Disponible sin uso |
| `filesystem.move_file` | `actions/filesystem.py` | Disponible sin uso |
| `http.fetch_url` | `actions/http_actions.py` | Disponible sin uso |
| `ui.open_file_in_browser` | `actions/ui.py` | Disponible sin uso |
| `ui.click` | `actions/ui.py` | Disponible sin uso |
| `ui.click_bbox` | `actions/ui.py` | Disponible sin uso |
| `vision.select_image` | `actions/vision.py` | Disponible sin uso |
| `vision.find_text_in_image` | `actions/vision.py` | Disponible sin uso |
| `vision.inspect_screen_target` | `actions/vision.py` | Disponible sin uso · **única vía al adaptador de visión multimodal** |

No son código muerto en sentido estricto —forman parte del contrato público del
registro y del `pyproject.toml`— pero sí superficie sin cobertura de caso. La última es
la más relevante: es el único camino hacia `VisionModelAnalyzer`, y al no usarla ningún
flow, **el catálogo publicado no puede llamar a un proveedor de IA**. Ver
[09 §5](09-apis-and-integrations.md#5-adaptador-opcional-de-visión-multimodal-no-usado-por-ningún-flow).

### Discrepancia entre el registro y los entry points

`engine/action_registry.py::_BUILT_IN_ACTIONS` declara **36** acciones.
`pyproject.toml`, sección `[project.entry-points."automa.actions"]`, declara **31**.
Las cinco que faltan en el `pyproject.toml`:

```text
browser.capture_page
browser.crawl_site
browser.extract_content
browser.fill_form
http.check_urls
```

En la práctica no rompe nada, porque `LazyActionRegistry` consulta primero su diccionario
interno y solo carga los entry points si no encuentra el nombre. Pero un paquete de
terceros que inspeccione el grupo `automa.actions` verá un catálogo incompleto.
Registrado en [15](15-risks-and-technical-debt.md).

## 4. `app/` — presentación

| Archivo | Líneas | Responsabilidad | Estado |
|---|---:|---|---|
| `server.py` | 1 753 | Panel HTML+CSS+JS embebido, API JSON, 10 rutas GET y 7 POST, autorización | **Activo · crítico · voluminoso** |
| `desktop.py` | 114 | Arranca el servidor en un hilo y abre la ventana `pywebview` | **Activo** |
| `__init__.py` | 0 | Marcador de paquete | **Activo** |

`app/server.py` es el 29 % del Python de producción. Su estructura interna, por bloques:

| Rango aproximado | Contenido |
|---|---|
| 1–105 | Imports, `_FOLDER_RE`, `_safe_folder`, `_is_preview`, `_resolve_under_root`, **arranque del scheduler al importar** |
| 107–300 | `_run_status_payload`: estado paso a paso de una corrida |
| 300–730 | Hoja de estilo del panel como cadena Python |
| 734–1400 | Funciones de renderizado: `html_page`, `badge`, tarjetas, historial, `_smart_summary`, detalle de corrida, dashboard de métricas |
| 1401–1745 | `AppHandler`: helpers de respuesta, autorización, `do_GET`, `do_POST` |
| 1746–1753 | `run_server` |

**Efecto secundario de importación** (líneas 100–104): al importar el módulo se arranca
el scheduler, se inicializa la base y se sincroniza el catálogo. Cualquier `import
app.server` —incluido el de `tests/test_panel_endpoints.py`— levanta un hilo de
scheduler.

## 5. `flows/` — el catálogo declarativo

27 carpetas, cada una con `manifest.json`, `context.example.json` y `README.md`.
Inventario completo verificado leyendo los 27 manifests:

| Carpeta | `id` | Familia | Pasos | Acciones | `allowed_actions` | `allowed_paths` | `max_runtime_seconds` |
|---|---|---|---:|---|:--:|:--:|---:|
| `01_screen_capture_analyze` | `screen_capture_analyze` | pantalla | 3 | screen, vision, filesystem | — | — | — |
| `02_screen_capture_browser` | `screen_capture_browser` | navegador | 1 | browser.capture_page | — | — | — |
| `03_folder_inventory` | `folder_inventory` | filesystem | 3 | filesystem ×3 | — | — | — |
| `04_document_drop_pipeline` | `document_drop_pipeline` | documentos | 4 | filesystem ×4 | — | — | — |
| `05_system_healthcheck` | `system_healthcheck` | sistema | 3 | system, rules, filesystem | — | — | — |
| `06_process_watchdog` | `process_watchdog` | sistema | 3 | system ×2, filesystem | — | — | — |
| `07_browser_form_filler` | `browser_form_filler` | navegador | 1 | browser.fill_form | — | — | — |
| `08_windows_lock_workstation` | `windows_lock_workstation` | sistema | 1 | ui.hotkey | ✅ | — | 5 |
| `09_show_desktop_capture` | `show_desktop_capture` | pantalla | 3 | ui, system, screen | ✅ | ✅ | 10 |
| `10_explorer_open_path` | `explorer_open_path` | sistema | 1 | ui.launch_process | ✅ | — | 5 |
| `11_settings_open_section` | `settings_open_section` | sistema | 1 | ui.open_url | ✅ | — | 5 |
| `12_desktop_ocr_inventory` | `desktop_ocr_inventory` | pantalla | 3 | screen, vision, filesystem | ✅ | ✅ | 30 |
| `13_notepad_quick_note` | `notepad_quick_note` | sistema | 3 | ui, system, ui | ✅ | — | 15 |
| `14_run_dialog_command` | `run_dialog_command` | sistema | 4 | ui, system, ui ×2 | ✅ | — | 10 |
| `15_clipboard_capture` | `clipboard_capture` | sistema | 2 | system, filesystem | ✅ | ✅ | 5 |
| `16_active_window_screenshot` | `active_window_screenshot` | pantalla | 1 | screen.capture_active_window | ✅ | ✅ | 10 |
| `17_taskmgr_snapshot` | `taskmgr_snapshot` | pantalla | 5 | ui, system, screen, vision, filesystem | ✅ | ✅ | 30 |
| `18_powershell_audit` | `powershell_audit` | sistema | 2 | system.run_powershell, filesystem | ✅ | ✅ | 40 |
| `19_taskbar_capture` | `taskbar_capture` | pantalla | 1 | screen.capture_region | ✅ | ✅ | 10 |
| `20_volume_mute_toggle` | `volume_mute_toggle` | sistema | 1 | ui.hotkey | ✅ | — | 3 |
| `21_web_content_extract` | `web_content_extract` | navegador | 3 | browser ×2, filesystem | — | — | — |
| `22_web_site_map` | `web_site_map` | navegador | 2 | browser.crawl_site, filesystem | — | — | — |
| `23_web_change_detector` | `web_change_detector` | navegador | 4 | browser, rules, notify, filesystem | — | — | — |
| `24_web_link_audit` | `web_link_audit` | navegador | 4 | browser, http, rules, filesystem | — | — | — |
| `25_web_table_extract` | `web_table_extract` | navegador | 2 | browser, filesystem | — | — | — |
| `26_web_value_monitor` | `web_value_monitor` | navegador | 4 | browser, rules, notify, filesystem | — | — | — |
| `27_web_page_archive` | `web_page_archive` | navegador | 3 | browser ×2, filesystem | — | — | — |

**Lectura del cuadro, y es el hallazgo más importante de este inventario:**

- **13 de 27 flows declaran `allowed_actions`** — exactamente los del bloque 08–20, la
  tanda añadida en la v0.2.0.
- **7 de 27 declaran `allowed_paths`** — 09, 12, 15, 16, 17, 18, 19.
- **14 flows corren con `SandboxPolicy` completamente permisiva**: los 01–07 y los 21–27.
  Entre ellos, `07_browser_form_filler` (lanza un navegador visible y escribe archivos) y
  los siete de la familia web (salen a internet si se les cambia la URL).
- **Ningún flow declara `required_secrets`.** El campo existe en el schema y el motor lo
  aplica, pero el catálogo no lo ejercita.
- **Ningún flow está marcado `preview: true`.** Los 27 son operativos.

Análisis de las consecuencias en [11 · Seguridad](11-security.md).

## 6. `decision/` — stubs sin uso

| Archivo | Líneas | Símbolo | Estado |
|---|---:|---|---|
| `rules.py` | 9 | `prioritize_steps(step_ids, context)` — devuelve la lista sin tocar | **Muerto** |
| `optional_ai.py` | 9 | `suggest_step_order(step_ids, context)` — devuelve la lista sin tocar | **Muerto** |
| `__init__.py` | 0 | Marcador de paquete | — |

Verificado con búsqueda en todo el repositorio: **ningún módulo importa `decision`**, y
ninguna de las dos funciones se invoca desde ningún sitio. Sin embargo, el paquete sí
aparece en `[tool.hatch.build.targets.wheel].packages` y en la cobertura de `pytest`
(`--cov=decision`), donde figura con **0 %**.

La docstring de `optional_ai.py` documenta la intención original: «Stub para futura
integración IA. La IA solo debe sugerir orden o prioridad, nunca reemplazar la ejecución
del motor». Es una decisión de diseño registrada, aunque el código nunca se llegó a
escribir. Ver [15](15-risks-and-technical-debt.md).

## 7. `plugins/analyzers/` — analizadores de imagen

| Archivo | Líneas | Clase | Qué hace | Usado por | Estado |
|---|---:|---|---|---|---|
| `vision_model_analyzer.py` | 222 | `VisionModelAnalyzer` | `mock` local, `openai_compatible`, `ollama` | Solo `vision.inspect_screen_target`, que ningún flow usa | **Experimental · sin uso** |
| `ocr_image_analyzer.py` | 87 | `OCRImageAnalyzer` | pytesseract con degradación explícita | `vision.ocr_image`, flows 12 y 17 | **Activo** |
| `mock_image_analyzer.py` | 40 | `MockImageAnalyzer` | Brillo medio y estado visual con Pillow | `vision.analyze_image` por defecto, flow 01 | **Activo** |
| `metadata_image_analyzer.py` | 21 | `MetadataImageAnalyzer` | Dimensiones, modo y SHA-256 | Registrado en `ANALYZERS`, sin flow que lo pida | **Disponible sin uso** |
| `base.py` | 9 | `AnalyzerProtocol` | Contrato tipado | Los cuatro anteriores | **Activo** |

> `VisionModelAnalyzer` se **instancia al importar `actions/vision.py`**
> (`VISION_ANALYZER = VisionModelAnalyzer()`), pero el constructor no hace nada y ningún
> método se llama sin pasar por `inspect_screen_target`. No hay tráfico de red implícito.

## 8. `tests/` — 17 módulos, 150 pruebas

| Archivo | Líneas | Qué cubre |
|---|---:|---|
| `test_browser_extract.py` | 358 | Lógica pura de la familia web: links, hash, parseo numérico, tracking, markdown, CSV, BFS, robots |
| `test_actions_basic.py` | 235 | Acciones de filesystem, sistema, reglas, UI en modo `dry_run` |
| `test_security_hardening.py` | 175 | `_safe_folder`, path traversal en `/file`, allowlist de PowerShell, `shell=True` prohibido |
| `test_orchestrator.py` | 139 | Ejecución completa, transiciones, reintentos, condiciones |
| `test_panel_endpoints.py` | 117 | Rutas del panel y autorización |
| `test_sandbox.py` | 83 | `SandboxPolicy` en sus cuatro dimensiones |
| `test_cron.py` | 57 | Parseo y cálculo de próxima ejecución |
| `test_secrets_and_notify.py` | 52 | Resolución de secretos y backends de notificación |
| `test_manifest_schema.py` | 52 | Validación con y sin `jsonschema` |
| `test_metrics.py` | 49 | Agregados y formato Prometheus |
| `test_loader.py` | 49 | Manifest → dataclasses y precedencia del contexto |
| `test_template.py` | 39 | Placeholders exactos, compuestos y llaves literales |
| `test_run_locks.py` | 36 | Adquisición, liberación y liberación forzada |
| `test_conditions.py` | 33 | Los 13 operadores y los combinadores |
| `test_action_registry.py` | 23 | Registro estático y dinámico |
| `conftest.py` | 28 | Fixtures compartidas |
| `__init__.py` | 0 | Marcador de paquete |

Cobertura medida por módulo y huecos priorizados en
[12 · Pruebas y calidad](12-testing-and-quality.md).

## 9. `scripts/` e `installer/`

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `scripts/validate_project.py` | JSON Schema + acciones registradas + transiciones resueltas + `start_step` válido | **Activo · gate de CI** |
| `scripts/smoke_test.py` | Corre tres flows de punta a punta y comprueba la base | **Activo · gate de CI** |
| `scripts/build_docs_pdf.py` | Genera los PDF de esta documentación | **Activo · añadido por este análisis** |
| `installer/automa.spec` | Spec de PyInstaller: datafiles, `hiddenimports`, `COLLECT` | **Activo · con hallazgo abierto** |
| `installer/Automa.iss` | Script de Inno Setup: instalación por usuario, dos idiomas | **Activo** |
| `installer/automa_entry.py` | Entry point del bundle: fija `AUTOMA_ROOT` y hace `chdir(data_dir())` | **Activo** |
| `installer/build_local.ps1` | Ayuda de compilación local | **Activo** |

> **Hallazgo en `installer/automa.spec`.** Su lista `hiddenimports` enumera diez módulos
> de `actions/` pero **no incluye `actions.browser_extract`**, añadido en la v0.3.0. El
> registro carga las acciones con `import_module` dinámico, que PyInstaller no rastrea.
> `INFERENCIA`: los siete flows de la familia web (21–27) fallarían con
> `ModuleNotFoundError` dentro del `.exe`. `REQUIERE VALIDACIÓN`: confirmar compilando.
> Detalle en [15](15-risks-and-technical-debt.md).

## 10. `.github/workflows/` — seis workflows

| Workflow | Dispara | Qué hace | Estado |
|---|---|---|---|
| `ci.yml` | push y PR a `main` | Matriz 2 SO × 3 Python: ruff, `validate_project`, pytest. Job `smoke` aparte | **Activo · gate** |
| `security.yml` | push, PR, lunes 06:00 UTC, manual | CodeQL `security-extended`, `detect-secrets` sobre filesystem e historial de 50 commits, Trojan Source, ofuscación, `pip-audit` | **Activo · gate** |
| `workflow-security.yml` | push, PR, programado | `actionlint` con verificación de checksum, `zizmor`, `pin-check` con parser YAML real | **Activo · gate** |
| `markdown-docs.yml` | PR que toque `**/*.md` | Verifica que **todos** los enlaces relativos de todos los `.md` resuelvan | **Activo · gate** |
| `dependency-hygiene.yml` | PR, lunes 04:00 UTC, manual | `pip list --outdated` (informativo, `continue-on-error`) | **Activo · informativo** |
| `release.yml` | tag `v*.*.*` o manual | PyInstaller + Inno Setup en `windows-latest`, sube el `.exe` al release | **Activo** |

`markdown-docs.yml` es el verificador que valida esta propia documentación: recorre
`rglob('*.md')` y falla si algún enlace relativo apunta a un archivo inexistente.

## 11. Directorios de datos

| Directorio | Versionado | Contenido | Ignorado por `.gitignore` |
|---|:--:|---|---|
| `data/web/` | ✅ | 7 HTML de demo: `form_demo`, `control_page`, `demo_page`, `site_demo/` ×4 | — |
| `data/seeds/` | ✅ (`form_seeds.json`) | 100 registros para el flow 07 | `.used_indices.json` sí |
| `data/inbox/`, `data/dropbox/inbox/` | ✅ | Archivos de ejemplo para los flows 03 y 04 | — |
| `data/web_watch/` | ❌ | Tracking de los flows 23 y 26 | ✅ |
| `configs/` | ✅ (`03_folder_inventory.json`) | Contexto persistido desde el panel | — |
| `db/` | Solo `.gitkeep` | `runs.db` | `db/*.db` |
| `logs/`, `state/` | Solo `.gitkeep` | JSONL y snapshots | `logs/*.jsonl`, `state/*.json` |
| `output/reports/`, `output/screenshots/` | Solo `.gitkeep` | Salidas de los flows | `output/**/*` por extensión |
| `secrets/` | Solo `.gitkeep` | `secrets.json` | `secrets/*.json` |

**Carpeta que NO está y sorprende al clonar:** `data/web_watch/`. Los flows 23 y 26 la
necesitan para su tracking; la crean solas en la primera corrida
(`apply_tracking` hace `path.parent.mkdir(parents=True, exist_ok=True)`), pero está en
`.gitignore` y no existe en un clon limpio. No es un error, es diseño: la primera corrida
establece la línea base y lo reporta con `first_run: true`.

## 12. Resumen del estado del código

| Estado | Elementos |
|---|---|
| **Activo y crítico** | `engine/orchestrator.py`, `database.py`, `sandbox.py`, `loader.py`, `models.py`, `template.py`, `conditions.py`, `paths.py`, `action_registry.py`, `app/server.py` |
| **Activo** | El resto de `engine/`, las 26 acciones con flow, `app/desktop.py`, los tres analizadores en uso, los seis workflows |
| **Disponible sin uso** | 10 acciones registradas sin flow, `MetadataImageAnalyzer` |
| **Experimental sin uso** | `VisionModelAnalyzer` y su único punto de entrada `vision.inspect_screen_target` |
| **Muerto** | `decision/rules.py::prioritize_steps`, `decision/optional_ai.py::suggest_step_order` |
| **Duplicado** | `engine/catalog.py::root_dir` frente a `engine/paths.py::root_dir` |
| **No en runtime** | `engine/manifest_schema.py` (solo lo usa el validador de CI) |
| **No determinado** | `installer/build_local.ps1`: no se ejecutó en este análisis |

---

**Documentos relacionados:**
[03 · Arquitectura](03-architecture.md) ·
[05 · Referencia técnica](05-technical-reference.md) ·
[06 · Explicación profunda](06-deep-code-explanation.md) ·
[15 · Riesgos](15-risks-and-technical-debt.md) ·
[19 · Matriz de trazabilidad](19-traceability-matrix.md)
