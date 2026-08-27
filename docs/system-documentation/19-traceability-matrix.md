# 19 · Matriz de trazabilidad

> Cada fila permite seguir una funcionalidad **en una sola línea**, desde la interfaz hasta
> la persistencia y sus pruebas. Los datos proceden de la lectura de los 27 manifests, del
> registro de acciones y de la ejecución de la suite en el commit `ff246ab`.

---

## Cómo leer estas tablas

| Columna | Significado |
|---|---|
| **Interfaz** | Cómo se dispara: tarjeta del panel, ruta HTTP, comando |
| **Manifest** | La receta que la implementa |
| **Pasos → acciones** | La cadena de acciones, en orden |
| **Módulo · función** | El código Python que hace el trabajo |
| **Persistencia** | Dónde acaban los datos |
| **Prueba** | El archivo de pruebas que la cubre, o el hueco |
| **Doc** | Dónde se explica |
| **Estado** | ✅ verificado · ⚠️ parcial · ❌ sin cobertura · 🔬 requiere validación manual |

---

## 1. Los 27 casos operativos

### 1.1 Familia `pantalla` — 6 casos

| # | Funcionalidad | Interfaz | Manifest | Pasos → acciones | Módulo · función | Persistencia | Prueba | Doc | Estado |
|---|---|---|---|---|---|---|---|---|---|
| F-01 | Capturar el escritorio y analizar brillo/RGB | Tarjeta · `Alt+1` · `POST /api/run/01_screen_capture_analyze` | `01_screen_capture_analyze` | `capture_screen`→`screen.capture_screenshot`; `analyze_capture`→`vision.analyze_image`; `write_report`→`filesystem.write_json` | `actions/screen.py::capture_screenshot`; `plugins/analyzers/mock_image_analyzer.py::MockImageAnalyzer`; `actions/filesystem.py::write_json` | `output/screenshots/*.png`, `output/reports/*.json`, `runs`, `steps`, `events` | ❌ Sin prueba de la captura real | [05 §1.2](05-technical-reference.md), [06 §13](06-deep-code-explanation.md) | 🔬 |
| F-09 | Minimizar todo y capturar escritorio limpio | Tarjeta · `POST /api/run/09_show_desktop_capture` | `09_show_desktop_capture` | `minimize_all_windows`→`ui.hotkey`; `wait_animation`→`system.wait_seconds`; `capture_desktop`→`screen.capture_screenshot` | `actions/ui.py::hotkey`; `actions/system.py::wait_seconds`; `actions/screen.py::capture_screenshot` | `output/screenshots/desktop_clean_*.png` + histórico | ⚠️ `test_actions_basic.py` cubre `hotkey` en `dry_run` | [05 §1.5](05-technical-reference.md) | 🔬 |
| F-12 | Inventario OCR de todo el texto visible | Tarjeta · `POST /api/run/12_desktop_ocr_inventory` | `12_desktop_ocr_inventory` | `capture_desktop`→`screen.capture_screenshot`; `ocr_full_image`→`vision.ocr_image`; `save_inventory`→`filesystem.write_json` | `actions/vision.py::ocr_image`; `plugins/analyzers/ocr_image_analyzer.py::OCRImageAnalyzer` | `output/screenshots/`, `output/reports/` + histórico | ❌ `actions/vision.py` al **0 %**; `plugins/` fuera del ámbito de cobertura | [09 §4.5](09-apis-and-integrations.md), [06 §13](06-deep-code-explanation.md) | 🔬 |
| F-16 | Captura solo de la ventana en foco | Tarjeta · `POST /api/run/16_active_window_screenshot` | `16_active_window_screenshot` | `capture_active_window`→`screen.capture_active_window` | `actions/screen.py::capture_active_window` + `pygetwindow` | `output/screenshots/*.png` + histórico | ❌ Requiere ventana con foco | [05 §1.2](05-technical-reference.md) | 🔬 |
| F-17 | Snapshot del Administrador de tareas con OCR | Tarjeta · `POST /api/run/17_taskmgr_snapshot` | `17_taskmgr_snapshot` | `ui.hotkey`; `system.wait_seconds`; `screen.capture_screenshot`; `vision.ocr_image`; `filesystem.write_json` (5 pasos) | Los cuatro módulos anteriores | `output/screenshots/`, `output/reports/` + histórico | ❌ | [04 §5](04-code-map.md) | 🔬 |
| F-19 | Captura de la barra de tareas | Tarjeta · `POST /api/run/19_taskbar_capture` | `19_taskbar_capture` | `capture_taskbar`→`screen.capture_region` con `bbox` de `top: -48` | `actions/screen.py::capture_region`, `_resolve_bbox` | `output/screenshots/taskbar_*.png` + histórico | ❌ | [05 §1.2](05-technical-reference.md) | 🔬 |

### 1.2 Familia `navegador` — 9 casos

| # | Funcionalidad | Interfaz | Manifest | Pasos → acciones | Módulo · función | Persistencia | Prueba | Doc | Estado |
|---|---|---|---|---|---|---|---|---|---|
| F-02 | Capturar el DOM renderizado de una URL | Tarjeta · `Alt+2` (pide URL) | `02_screen_capture_browser` | `browser.capture_page` | `actions/browser_capture.py::capture_page`, `_to_url` | `output/screenshots/*.png` + histórico | ⚠️ **18 %**: solo `_to_url` | [09 §4.1](09-apis-and-integrations.md) | 🔬 |
| F-07 | Rellenar un formulario de 10 campos sin repetir registro | Tarjeta · `Alt+7` | `07_browser_form_filler` | `fill_and_submit_form`→`browser.fill_form` | `actions/browser_form.py::fill_form`, `_pick_record`, `_save_used_ids` | `output/reports/form_submission_*.json`; **tracking en `data/seeds/.used_indices.json`** | ❌ **0 %** | [05 §1.8](05-technical-reference.md), [06 §8](06-deep-code-explanation.md), [08 §10.3](08-data-flow.md) | 🔬 |
| F-21 | Extraer título, texto, links, metadatos y tablas | Tarjeta · `POST /api/run/21_web_content_extract` | `21_web_content_extract` | `browser.extract_content`; `browser.capture_page`; `filesystem.write_json` | `actions/browser_extract.py::extract_content`, `build_result`, `resolve_links`, `normalize_text`, `content_hash` | `output/reports/*.json`, PNG opcional + histórico | ✅ `test_browser_extract.py` — **91 %** de la lógica pura | [05 §1.8](05-technical-reference.md), [06 §7](06-deep-code-explanation.md) | ⚠️ |
| F-22 | Mapa de sitio con BFS acotado y `robots.txt` | Tarjeta · `POST /api/run/22_web_site_map` | `22_web_site_map` | `browser.crawl_site`; `filesystem.write_json` | `actions/browser_extract.py::crawl_site`, `crawl_pages`, `RobotsCache` | `output/reports/*.json` + histórico | ✅ `test_browser_extract.py` con `fetch_page` falso | [06 §7.5–7.7](06-deep-code-explanation.md) | ⚠️ |
| F-23 | Detectar cambios en una página y notificar | Tarjeta · `POST /api/run/23_web_change_detector` | `23_web_change_detector` | `extract_and_track`→`browser.extract_content` (`retries: 1`); `evaluate_change`→`rules.evaluate`; `notify_change`→`notify.send` **condicionado**; `write_report`→`filesystem.write_json` | `browser_extract.py::apply_tracking`, `content_hash`; `actions/rules.py::evaluate_rules`; `actions/notify.py::send_notification` | `output/reports/`, `output/notifications/web_changes.log`; **tracking en `data/web_watch/demo_page.json`** | ✅ `apply_tracking` y `content_hash` cubiertos; ⚠️ el `when` del paso 3, en `test_orchestrator.py` | [08 §10.2](08-data-flow.md), [14 §5.3](14-troubleshooting.md) | ⚠️ |
| F-24 | Auditar enlaces rotos de una página | Tarjeta · `POST /api/run/24_web_link_audit` | `24_web_link_audit` | `extract_links`→`browser.extract_content`; `check_links`→`http.check_urls`; `evaluate_links`→`rules.evaluate`; `write_report`→`filesystem.write_json` | `browser_extract.py::resolve_links`; `actions/http_actions.py::check_urls` | `output/reports/link_audit_*.json` + histórico | ✅ `resolve_links` y `check_urls` en `test_browser_extract.py` | [05 §1.6](05-technical-reference.md) | ⚠️ |
| F-25 | Extraer cada `<table>` a CSV y JSON | Tarjeta · `POST /api/run/25_web_table_extract` | `25_web_table_extract` | `browser.extract_content` con `include_tables`; `filesystem.write_json` | `browser_extract.py::save_tables_csv`, `build_result` | `output/reports/*.json`, `table_NN.csv` + histórico | ✅ `save_tables_csv` cubierto | [05 §1.8](05-technical-reference.md) | ⚠️ |
| F-26 | Vigilar un valor por selector CSS y alertar | Tarjeta · `POST /api/run/26_web_value_monitor` | `26_web_value_monitor` | `read_value`→`browser.extract_content` (selector `#precio`); `evaluate_value`→`rules.evaluate`; `notify_value`→`notify.send` **condicionado**; `write_report`→`filesystem.write_json` | `browser_extract.py::parse_number`, `apply_tracking` | `output/reports/`, `output/notifications/value_monitor.log`; **tracking en `data/web_watch/precio_demo.json`** | ✅ `parse_number` con formatos mixtos | [06 §7.2](06-deep-code-explanation.md), [14 §5.5](14-troubleshooting.md) | ⚠️ |
| F-27 | Archivar una página: Markdown + PNG + hash | Tarjeta · `POST /api/run/27_web_page_archive` | `27_web_page_archive` | `extract_and_save_markdown`→`browser.extract_content`; `capture_evidence`→`browser.capture_page`; `write_metadata`→`filesystem.write_json` | `browser_extract.py::render_markdown`, `content_hash`; `browser_capture.py::capture_page` | `output/*.md`, `output/screenshots/*.png`, `output/reports/*.json` | ✅ `render_markdown` cubierto | [05 §1.8](05-technical-reference.md) | ⚠️ |

### 1.3 Familia `sistema` — 10 casos

| # | Funcionalidad | Interfaz | Manifest | Pasos → acciones | Módulo · función | Persistencia | Prueba | Doc | Estado |
|---|---|---|---|---|---|---|---|---|---|
| F-05 | Snapshot de CPU/RAM/disco con reglas | Tarjeta · `POST /api/run/05_system_healthcheck` | `05_system_healthcheck` | `take_snapshot`→`system.snapshot_system`; `evaluate_snapshot`→`rules.evaluate`; `write_snapshot`→`filesystem.write_json` | `actions/system.py::snapshot_system`; `actions/rules.py::evaluate_rules` | `output/reports/system_health_*.json` + histórico | ✅ `test_actions_basic.py` + `smoke_test.py` | [06 §14](06-deep-code-explanation.md) | ✅ |
| F-06 | Top 10 procesos con alertas por umbral | Tarjeta · `POST /api/run/06_process_watchdog` | `06_process_watchdog` | `top_processes`→`system.top_processes`; `watch_processes`→`system.watch_processes`; `write_report`→`filesystem.write_json` | `actions/system.py::top_processes`, `watch_processes` | `output/reports/process_watchdog_*.json` + histórico | ✅ `test_actions_basic.py` + `smoke_test.py` | [05 §1.4](05-technical-reference.md) | ✅ |
| F-08 | Bloquear la estación de trabajo | Tarjeta · `POST /api/run/08_windows_lock_workstation` | `08_windows_lock_workstation` | `lock_workstation`→`ui.hotkey` `["win","l"]` | `actions/ui.py::hotkey` | Histórico | ⚠️ Solo en `dry_run` | [05 §1.5](05-technical-reference.md) | 🔬 |
| F-10 | Abrir el Explorador en una ruta | Tarjeta · `POST /api/run/10_explorer_open_path` | `10_explorer_open_path` | `open_explorer`→`ui.launch_process` | `actions/ui.py::launch_process` con `shlex` y `shell=False` | Histórico | ⚠️ `test_security_hardening.py` verifica que `shell=True` se rechaza | [11 §2.2](11-security.md) | 🔬 |
| F-11 | Abrir una sección de Configuración de Windows | Tarjeta · `POST /api/run/11_settings_open_section` | `11_settings_open_section` | `open_settings`→`ui.open_url` con URI `ms-settings:` | `actions/ui.py::open_url` + `webbrowser` | Histórico | ❌ | [09 §6](09-apis-and-integrations.md) | 🔬 |
| F-13 | Nota rápida en el Bloc de notas | Tarjeta · `POST /api/run/13_notepad_quick_note` | `13_notepad_quick_note` | `ui.launch_process`; `system.wait_seconds`; `ui.type_text` | `actions/ui.py::launch_process`, `type_text` | Histórico | ⚠️ Solo en `dry_run` | [05 §1.5](05-technical-reference.md) | 🔬 |
| F-14 | Ejecutar un comando desde el diálogo Ejecutar | Tarjeta · `POST /api/run/14_run_dialog_command` | `14_run_dialog_command` | `ui.hotkey`; `system.wait_seconds`; `ui.type_text`; `ui.hotkey` (4 pasos) | `actions/ui.py::hotkey`, `type_text` | Histórico | ⚠️ Solo en `dry_run` | [05 §1.5](05-technical-reference.md) | 🔬 |
| F-15 | Capturar el portapapeles a JSON | Tarjeta · `POST /api/run/15_clipboard_capture` | `15_clipboard_capture` | `read_clipboard`→`system.read_clipboard`; `save_clipboard`→`filesystem.write_json` | `actions/system.py::read_clipboard` + `pyperclip` | `output/reports/clipboard_*.json` + **`runs.context_json`** | ⚠️ La rama de degradación sí, el contenido real no | [08 §10.1](08-data-flow.md), [11 §6](11-security.md) | 🔬 |
| F-18 | Auditoría PowerShell con allowlist | Tarjeta · `POST /api/run/18_powershell_audit` | `18_powershell_audit` | `run_audit_command`→`system.run_powershell`; `save_audit_report`→`filesystem.write_json` | `actions/system.py::run_powershell`, `_PS_DEFAULT_ALLOWLIST` | `output/reports/*.json` + histórico | ✅ `test_security_hardening.py` cubre los dos controles | [11 §5](11-security.md) | ⚠️ |
| F-20 | Alternar el silencio del audio | Tarjeta · `POST /api/run/20_volume_mute_toggle` | `20_volume_mute_toggle` | `toggle_mute`→`ui.hotkey` `["volumemute"]` | `actions/ui.py::hotkey` | Histórico | ⚠️ Solo en `dry_run` | [05 §1.5](05-technical-reference.md) | 🔬 |

### 1.4 Familias `filesystem` y `documentos` — 2 casos

| # | Funcionalidad | Interfaz | Manifest | Pasos → acciones | Módulo · función | Persistencia | Prueba | Doc | Estado |
|---|---|---|---|---|---|---|---|---|---|
| F-03 | Inventario de una carpeta | Tarjeta · `Alt+3` (pide ruta) | `03_folder_inventory` | `scan_folder`→`filesystem.list_directory`; `classify_inventory`→`filesystem.classify_file_inventory`; `write_inventory`→`filesystem.write_json` | `actions/filesystem.py::list_directory`, `classify_file_inventory`, `write_json` | `output/reports/folder_inventory_*.json` + histórico | ✅ `test_actions_basic.py` + `smoke_test.py` | [06 §14](06-deep-code-explanation.md) | ✅ |
| F-04 | Pipeline documental de una carpeta de entrada | Tarjeta · `POST /api/run/04_document_drop_pipeline` | `04_document_drop_pipeline` | `scan_dropbox`; `classify_dropbox`; `summarize_texts`→`filesystem.summarize_text_folder`; `write_pipeline_report` | `actions/filesystem.py::summarize_text_folder` | `output/reports/document_drop_pipeline_*.json` + histórico | ✅ `test_actions_basic.py` | [08 §4](08-data-flow.md) | ✅ |

---

## 2. Capacidades del motor

| # | Capacidad | Interfaz | Módulo · función | Persistencia | Prueba | Doc | Estado |
|---|---|---|---|---|---|---|---|
| M-01 | Cargar un manifest y convertirlo en objetos | Interna | `engine/loader.py::FlowLoader.load_manifest` → `engine/models.py` | — | ✅ `test_loader.py` — **100 %** | [06 §5.1](06-deep-code-explanation.md) | ✅ |
| M-02 | Resolver el contexto por precedencia | Interna | `engine/loader.py::load_context` | Lee `configs/`, `context.user.json`, `context.example.json` | ✅ `test_loader.py` | [10 §3.1](10-configuration.md) | ✅ |
| M-03 | Sustituir placeholders | Interna | `engine/template.py::render_value`, `flatten_context` | `steps.params_json` | ✅ `test_template.py` — **100 %** | [06 §2](06-deep-code-explanation.md) | ✅ |
| M-04 | Evaluar condiciones (13 operadores) | `when` de pasos y transiciones | `engine/conditions.py::evaluate_condition`, `matches` | `steps.status = skipped` | ✅ `test_conditions.py` — **90 %** | [06 §4](06-deep-code-explanation.md) | ✅ |
| M-05 | Ejecutar el bucle con transiciones | Interna | `engine/orchestrator.py::run`, `_resolve_transition`, `_default_next` | `runs`, `steps`, `events`, `state/`, `logs/` | ✅ `test_orchestrator.py` — **87 %** | [06 §1](06-deep-code-explanation.md) | ✅ |
| M-06 | Reintentar y recuperarse por transición | `retries` y `on: "failure"` | `engine/orchestrator.py::run` | `steps.attempt`, evento `step_recovered` | ✅ `test_orchestrator.py` | [06 §1.2](06-deep-code-explanation.md) | ✅ |
| M-07 | Aplicar la política de sandbox | `allowed_actions`, `allowed_paths`, `required_secrets`, `max_runtime_seconds` | `engine/sandbox.py::SandboxPolicy` | `runs.context_json → policy`, `error_json.kind` | ✅ `test_sandbox.py` — **95 %** | [11 §4](11-security.md) | ✅ |
| M-08 | Resolver acciones de forma perezosa | Interna | `engine/action_registry.py::LazyActionRegistry.get` | — | ✅ `test_action_registry.py` — **84 %** | [03 §4](03-architecture.md) | ✅ |
| M-09 | Cargar acciones de terceros por entry point | `pyproject.toml` del tercero | `LazyActionRegistry._maybe_load_entry_points` | — | ⚠️ Parcial | [09 §7](09-apis-and-integrations.md) | ⚠️ |
| M-10 | Detectar los archivos de salida | Interna | `engine/introspection.py::extract_existing_paths` | `runs.outputs_json` | ✅ **90 %** | [06 §12](06-deep-code-explanation.md) | ✅ |
| M-11 | Persistir estado, pasos y eventos | Interna | `engine/database.py`, `logger.py`, `state_store.py` | Las 7 tablas + `logs/` + `state/` | ✅ `test_orchestrator.py`, `test_metrics.py` | [07](07-database.md) | ✅ |
| M-12 | Separar raíz de lectura y de escritura | `AUTOMA_ROOT`, `AUTOMA_DATA_ROOT` | `engine/paths.py::root_dir`, `data_dir` | Determina dónde vive todo | ✅ 3 pruebas en `test_actions_basic.py` — **86 %** | [10 §5](10-configuration.md) | ✅ |
| M-13 | Resolver secretos (entorno, después archivo) | `secrets/secrets.json`, entorno | `engine/secrets.py::get_secret`, `set_secret`, `list_secret_names` | `secrets/secrets.json` **sin cifrar** | ✅ `test_secrets_and_notify.py` — **73 %** | [11 §6](11-security.md) | ✅ |
| M-14 | Calcular la próxima ejecución de un cron | Panel · pestaña Programadas | `engine/cron.py::next_after`, `parse_cron` | `schedules.next_run_at` | ✅ `test_cron.py` — **87 %** | [06 §9](06-deep-code-explanation.md) | ⚠️ |
| M-15 | Disparar tareas programadas | Automático cada 2 s | `engine/scheduler.py::SchedulerService` | `schedules.last_run_at`, `run_locks` | ⚠️ 51–76 %, **variable** | [06 §10](06-deep-code-explanation.md) | ⚠️ |
| M-16 | Evitar ejecución doble por lock | Automático · **solo scheduler** | `engine/database.py::acquire_run_lock`, `release_run_lock` | `run_locks` | ✅ `test_run_locks.py` | [15 · R-07](15-risks-and-technical-debt.md) | ⚠️ |
| M-17 | Validar manifests contra el JSON Schema | `automa-validate`, CI | `engine/manifest_schema.py`; `scripts/validate_project.py` | — | ✅ `test_manifest_schema.py` — **53 %** | [06 §14](06-deep-code-explanation.md) | ✅ |
| M-18 | Agregar métricas | `GET /metrics`, `/api/metrics` | `engine/metrics.py::overview`, `by_flow`, `prometheus_text` | Consulta `runs` y `steps` | ✅ `test_metrics.py` — **100 %** | [09 §3](09-apis-and-integrations.md) | ✅ |
| M-19 | Listar y ejecutar desde el CLI | `automa list`, `automa run`, `automa scheduler` | `engine/runner.py::main`, `build_parser` | Igual que el panel | ❌ **0 %** — y ahí vive el defecto R-06 | [15 · R-06](15-risks-and-technical-debt.md) | ❌ |

---

## 3. Capacidades del panel

| # | Capacidad | Ruta | Módulo · función | Persistencia | Prueba | Doc | Estado |
|---|---|---|---|---|---|---|---|
| P-01 | Panel de 3 pestañas | `GET /` | `app/server.py::render_home`, `_flow_card_run_tab`, `_flow_card_schedule_tab`, `_history_row` | Lee `flows` y `runs` | ⚠️ `test_panel_endpoints.py` | [09 §1.1](09-apis-and-integrations.md) | ⚠️ |
| P-02 | Ejecutar un flow de forma asíncrona | `POST /api/run/<folder>` | `app/server.py::do_POST` + `threading.Thread` | `runs`, `steps`, `events` | ⚠️ | [09 §2](09-apis-and-integrations.md) | ⚠️ |
| P-03 | Ejecutar de forma síncrona desde formulario | `POST /run?flow=<folder>` | `app/server.py::do_POST` | Igual | ⚠️ | [09 §1.2](09-apis-and-integrations.md) | ⚠️ |
| P-04 | Polling del estado paso a paso | `GET /api/runs/<run_id>/status` | `app/server.py::_run_status_payload` | Lee `runs`, `steps`, manifest | ⚠️ | [09 §2](09-apis-and-integrations.md) | ⚠️ |
| P-05 | Detalle de una corrida | `GET /run/<flow_id>/<run_id>` | `render_run_detail`, `_smart_summary`, `_output_thumb` | Lee `runs`, `steps`, `events` | ❌ | [08 §6](08-data-flow.md) | ❌ |
| P-06 | Resumen legible por flow | Dentro de P-05 | `app/server.py::_smart_summary` | — | ❌ | [15 · R-15](15-risks-and-technical-debt.md) | ❌ **Solo 6 de 27 flows** |
| P-07 | Editar el contexto de un flow | `GET`/`POST /flow/<f>/config` | `render_flow_config`; `database.set_flow_config` | `flow_configs` + `configs/<f>.json` | ⚠️ | [10 §3](10-configuration.md) | ⚠️ |
| P-08 | Programar un flow | `POST /flow/<f>/schedule` | `database.set_schedule`; `engine/cron.py` | `schedules` | ✅ Vía `test_cron.py` y `test_metrics.py` | [09 §2](09-apis-and-integrations.md) | ⚠️ |
| P-09 | Histórico por flow | `GET /flow/<f>/history` | `render_flow_history` | Lee `runs` | ❌ | [09 §1.1](09-apis-and-integrations.md) | ❌ |
| P-10 | Dashboard de métricas | `GET /metrics/dashboard` | `render_metrics_dashboard` | Lee agregados | ❌ | [09 §3](09-apis-and-integrations.md) | ❌ |
| P-11 | Servir archivos de salida | `GET /file?path=…` | `app/server.py::do_GET`, 4 controles | Lee `output/` | ✅ `test_security_hardening.py` | [11 §2.3](11-security.md) | ✅ |
| P-12 | Webhook entrante | `POST /api/hook/<folder>` | `_check_webhook_token`; ejecución **síncrona** | `runs`, `steps`, `events` | ⚠️ | [09 §2](09-apis-and-integrations.md) | ⚠️ |
| P-13 | Guardar un envío de formulario | `POST /api/form/submit` | `app/server.py::do_POST` | `output/reports/form_submission_panel_*.json` | ❌ | [09 §1.2](09-apis-and-integrations.md) | ❌ |
| P-14 | Autorizar mutaciones | Todos los POST salvo el webhook | `_authorize_mutation`, `_check_token` con `hmac.compare_digest` | — | ✅ `test_panel_endpoints.py`, `test_security_hardening.py` | [11 §3.2](11-security.md) | ✅ |
| P-15 | Validar el slug de la URL | Las 7 rutas con `<folder>` | `_safe_folder`, `_FOLDER_RE` | — | ✅ `test_security_hardening.py` | [11 §2.2](11-security.md) | ✅ |
| P-16 | Marcar un flow como preview | Manifest o archivo `.disabled` | `app/server.py::_is_preview` | Responde `409` | ❌ | [10 §5](10-configuration.md) | ❌ |
| P-17 | Ventana nativa de escritorio | `automa-desktop` | `app/desktop.py::launch`, `_wait_for_server` | — | ⚠️ **48 %** | [02 §6](02-installation-and-execution.md) | ⚠️ |
| P-18 | Sonda de vida | `GET /healthz` | `app/server.py::do_GET` | — | ✅ `test_panel_endpoints.py` | [09 §1.1](09-apis-and-integrations.md) | ✅ |

---

## 4. Reglas de negocio verificables

| # | Regla | Dónde se implementa | Cómo comprobarla | Prueba | Estado |
|---|---|---|---|---|---|
| RN-01 | Un paso cuyo `when` no se cumple se registra como `skipped` con `attempt: 0`, no se omite | `engine/orchestrator.py::run` | Ver la fila en `steps` con `status='skipped'` | ✅ `test_orchestrator.py` | ✅ |
| RN-02 | Un flow se recupera de un fallo **solo si** la transición `on: "failure"` apunta a un paso distinto del siguiente por defecto | `engine/orchestrator.py::run` | Evento `step_recovered` en `events` | ✅ `test_orchestrator.py` | ✅ |
| RN-03 | La primera corrida de un flow con tracking **nunca** reporta cambio | `browser_extract.py::apply_tracking` | `first_run: true` en el resultado | ✅ `test_browser_extract.py` | ✅ |
| RN-04 | El flow 07 no repite registro hasta agotar los 100; entonces reinicia y lo declara | `browser_form.py::_pick_record` | `cycle_resetted` en el resultado | ❌ | ❌ |
| RN-05 | `rules.evaluate` se detiene en la **primera** regla que coincide | `actions/rules.py::evaluate_rules` | `matched_rule` y `evaluations` | ✅ `test_actions_basic.py` | ✅ |
| RN-06 | El crawl respeta `robots.txt`, y si no lo puede leer **permite y lo declara** | `browser_extract.py::RobotsCache` | `robots_checked_hosts` y `robots_blocked` | ✅ `test_browser_extract.py` | ✅ |
| RN-07 | Un enlace caído durante el crawl no aborta el recorrido | `browser_extract.py::crawl_pages` | Array `errors` en el reporte | ✅ `test_browser_extract.py` | ✅ |
| RN-08 | `system.run_powershell` rechaza encadenamiento y verbos fuera de la allowlist | `actions/system.py::run_powershell` | `ValueError` con el motivo | ✅ `test_security_hardening.py` | ✅ |
| RN-09 | `ui.launch_process` **prohíbe** `shell=True` | `actions/ui.py::launch_process` | `ValueError` explicativo | ✅ `test_security_hardening.py` | ✅ |
| RN-10 | El sandbox bloquea la corrida entera, no solo el paso | `engine/orchestrator.py::run` | `runs.status='failed'`, `error_json.kind='sandbox_violation'` | ✅ `test_sandbox.py`, `test_orchestrator.py` | ✅ |
| RN-11 | Toda cota aplicada se declara en el resultado | `check_urls`, `extract_content`, `read_clipboard`, `run_powershell`, `crawl_pages` | Campos `*_truncated` | ✅ `test_browser_extract.py` | ⚠️ **Dos excepciones**: `summarize_text_folder` y `apply_tracking` (ver [15 · R-24](15-risks-and-technical-debt.md)) |
| RN-12 | Un flow sin `allowed_actions` corre con política permisiva, y el histórico lo registra | `engine/sandbox.py::is_permissive`, `summary` | `runs.context_json → policy.permissive` | ✅ `test_sandbox.py` | ✅ |
| RN-13 | El motor corta a `max_steps_per_run` (200) para evitar ciclos infinitos | `engine/orchestrator.py::run` | `FlowExecutionError` con el mensaje | ⚠️ | ⚠️ |
| RN-14 | Una acción de terceros **nunca** puede sobrescribir una interna | `LazyActionRegistry._maybe_load_entry_points` con `setdefault` | Registrar un entry point homónimo | ❌ | ❌ |
| RN-15 | Un placeholder exacto devuelve el valor **con su tipo original** | `engine/template.py::render_value` | `"{{ headless }}"` llega como `False`, no `"False"` | ✅ `test_template.py` | ✅ |
| RN-16 | Solo se consideran salidas los archivos bajo `output/` | `engine/introspection.py::extract_existing_paths` | `runs.outputs_json` | ✅ | ✅ |

---

## 5. De la persistencia hacia atrás

Camino inverso: dado un archivo o una tabla, quién lo produce.

| Almacén | Escribe | Desde el flow | Se lee en |
|---|---|---|---|
| `runs` | `engine/database.py::upsert_run` ← `Orchestrator._persist` | Todos | `catalog.list_runs`, `metrics.*`, panel |
| `steps` | `insert_step` ← `Orchestrator.run` | Todos | `_run_status_payload`, `render_run_detail`, `metrics` |
| `events` | `insert_event` ← `JsonlLogger.write` | Todos | `render_run_detail` |
| `flows` | `sync_flows` ← import de `app.server`, `runner` | — | Panel |
| `flow_configs` | `set_flow_config` ← `POST /flow/<f>/config` | — | `get_flow_by_folder` |
| `schedules` | `set_schedule`, `mark_schedule_run` | — | `scheduler.run_pending_once` |
| `run_locks` | `acquire_run_lock` ← **solo** `scheduler._run_job` | — | `RUNBOOK.md` |
| `logs/*.jsonl` | `JsonlLogger.write` | Todos | Manual |
| `state/*.json` | `StateStore.save` ← `_persist` | Todos | Manual |
| `output/screenshots/*.png` | `screen.capture_*`, `browser.capture_page` | 01, 02, 09, 12, 16, 17, 19, 21, 27 | `GET /file` |
| `output/reports/*.json` | `filesystem.write_json` | 16 de 27 flows | `GET /file`, panel |
| `output/reports/*.csv` | `browser_extract.save_tables_csv` | 25 | `GET /file` |
| `output/*.md` | `browser_extract.render_markdown` | 27 | `GET /file` |
| `output/notifications/*.log` | `notify.send` con `backend: "file"` | 23, 26 | Manual |
| `data/seeds/.used_indices.json` | `browser_form._save_used_ids` | 07 | El propio flow, corrida siguiente |
| `data/web_watch/*.json` | `browser_extract.apply_tracking` | 23, 26 | El propio flow, corrida siguiente |
| `configs/<folder>.json` | `set_flow_config` | — | `FlowLoader.load_context` |
| `secrets/secrets.json` | `engine.secrets.set_secret` | — | `get_secret` |

---

## 6. Resumen de cobertura de trazabilidad

| Categoría | Total | ✅ Verificado | ⚠️ Parcial | ❌ Sin cobertura | 🔬 Requiere validación manual |
|---|---:|---:|---:|---:|---:|
| Casos operativos (F) | 27 | 4 | 8 | 0 | 15 |
| Capacidades del motor (M) | 19 | 13 | 5 | 1 | 0 |
| Capacidades del panel (P) | 18 | 4 | 8 | 6 | 0 |
| Reglas de negocio (RN) | 16 | 11 | 3 | 2 | 0 |
| **Total** | **80** | **32** | **24** | **9** | **15** |

**Lectura del cuadro:**

- **El motor está bien cubierto**: 13 de 19 capacidades verificadas por pruebas
  automáticas. Es el activo mejor protegido del proyecto.
- **Los 15 casos marcados 🔬 no son un defecto de las pruebas**: dependen de un escritorio
  Windows interactivo, de Chromium o del binario `tesseract`. La CI no puede ejecutarlos.
  La mitigación existente —`dry_run` en las acciones de UI— es la correcta.
- **Los 9 sin cobertura son huecos reales y abordables**: `engine/runner.py` (donde vive el
  defecto R-06), seis capacidades de renderizado del panel, y las reglas RN-04 y RN-14. La
  propuesta priorizada está en [12 §10](12-testing-and-quality.md).

---

**Documentos relacionados:**
[04 · Mapa del código](04-code-map.md) ·
[05 · Referencia técnica](05-technical-reference.md) ·
[07 · Base de datos](07-database.md) ·
[12 · Pruebas y calidad](12-testing-and-quality.md) ·
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md)
