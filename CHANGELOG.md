# Changelog

Todas las versiones notables de Automa se documentan acá. El formato sigue
[Keep a Changelog](https://keepachangelog.com/) y la versión sigue [SemVer](https://semver.org/lang/es/).

## [Unreleased]

## [0.3.0] · 2026-07-15

### 🕸️ Familia de extracción y vigilancia web · 7 flows nuevos (21–27)

Chromium headless que **lee** el DOM como datos (no solo lo fotografía). Todos los flows corren offline por defecto contra HTML de demo del propio repo (`data/web/demo_page.html` y el mini-sitio `data/web/site_demo/`), así la demo es determinista y sin internet.

| # | Slug | Qué hace |
| --- | --- | --- |
| 21 | `web_content_extract` | Extrae título, texto, links absolutos, metadatos y tablas de una URL + PNG de evidencia opcional. |
| 22 | `web_site_map` | Crawl BFS acotado (`max_pages`/`max_depth`, mismo dominio, respeta robots.txt) → inventario de páginas. |
| 23 | `web_change_detector` | SHA-256 del texto vs corrida anterior (tracking persistente en `data/web_watch/`) → `notify.send` solo si cambió. |
| 24 | `web_link_audit` | Verifica cada link de una página (HEAD + fallback GET; `file://` por existencia) → alerta si hay rotos. |
| 25 | `web_table_extract` | Cada `<table>` del DOM → `table_NN.csv` + JSON. Funciona con tablas generadas por JS. |
| 26 | `web_value_monitor` | Un valor puntual vía selector CSS, parseado a número, contra umbral y contra la corrida anterior. |
| 27 | `web_page_archive` | Archivado con evidencia: Markdown + PNG full-page + JSON con SHA-256. |

Los casos 23 y 24 **estrenan** las familias `notify` y `http` en flows (las acciones existían sin caso que las usara).

### 📦 3 acciones nuevas (33 → 36)

- [`browser.extract_content`](actions/browser_extract.py): título, texto normalizado, links (deduplicados, en orden de aparición, con cota `max_links`), metadatos, tablas, valor por selector CSS con parseo numérico (`$ 1.499,90` → `1499.9`), hash SHA-256, tracking persistente (`first_run`/`changed`/`previous_value`), export Markdown y CSV.
- [`browser.crawl_site`](actions/browser_extract.py): BFS determinista con cotas explícitas, filtro de dominio, `robots.txt` por host (`RobotsCache`), delay de cortesía, y recuperación ante navegación fallida (un link roto no aborta el crawl). Reporta `truncated`/`errors`/`robots_blocked` — nunca truncado silencioso.
- [`http.check_urls`](actions/http_actions.py): verificación de lista de URLs en orden de entrada — HEAD con redirects (fallback GET ante 405/501), `file://` por existencia en disco, `mailto:`/`tel:` como `skipped`.

### ⚙️ Motor: placeholders con punto dentro de strings

`engine/template.py` ahora resuelve claves aplanadas dentro de strings compuestos — `"hash {content.content_hash}"` funciona en mensajes de notify. Antes, `str.format_map` crasheaba con `AttributeError` ante cualquier clave con punto embebida. Además, un placeholder exacto que resuelve a `None` devuelve `None` real (JSON null) en vez de caer al render de string, y las llaves que no son placeholders (JSON embebido en comandos) quedan intactas. Cambio aditivo: los 20 flows previos rinden idéntico.

### 🧪 Tests y validación

- Suite: **150 tests pasando** (era 119). Los 31 nuevos cubren toda la lógica de la familia web **sin Playwright** (FakePage/fetcher fake): links, hash, parseo numérico, tracking, markdown, CSV, BFS con cotas/errores/robots, `check_urls`. Cobertura 58.9% (gate en 54%).
- Ruff limpio, schema validation OK (**27 flows · 36 acciones registradas**).
- Los 7 flows ejecutados de punta a punta en Windows real: crawl con profundidades 0/1/1/2 correctas, link roto detectado (`broken_count=1` → alerta), valor `$ 1.499,90` parseado a `1499.9` sobre umbral 1000 → notificación emitida, ciclo baseline→cambio→alerta verificado.

## [0.2.1] · 2026-06-18

### 🐛 Fix · Bundle: `PermissionError` al escribir en `C:\Program Files\Automa\_internal\db`

Cuando el instalador deja la app bajo `Program Files` (read-only para usuarios sin admin), `engine.database.init_db()` levantaba `PermissionError [WinError 5]` al intentar crear `_internal/db/`. Causa: el bundle frozen usaba `root_dir()` (= `_MEIPASS`, read-only) tanto para datafiles como para state writable.

**Fix:** se separa el root **read-only** del **writable**:

- Nueva función [`engine.paths.data_dir()`](engine/paths.py): en modo frozen apunta a `%LOCALAPPDATA%\Automa\` (Windows) o `$XDG_DATA_HOME/automa-pc` (otros). En modo desarrollo coincide con `root_dir()` — backward-compat total.
- Override explícito con `$AUTOMA_DATA_ROOT`.
- Migrados a `data_dir()`: `engine.database.DB_PATH`, `engine.database.set_flow_config`, `engine.secrets.SECRETS_PATH`, `engine.orchestrator` (log_path, state_path).
- `installer/automa_entry.py` ahora hace `os.chdir(data_dir())` cuando arranca frozen, para que rutas relativas de los flows (`output/screenshots/...`) caigan en disco writable y el sandbox las resuelva contra cwd correctamente.

Tests: 3 casos nuevos cubren `data_dir()` en dev mode (== root_dir), con `$AUTOMA_DATA_ROOT`, y frozen + LOCALAPPDATA. Suite: 119/119, cobertura 54.78%.

## [0.2.0] · 2026-06-18

### 🪟 App de escritorio Windows + instalador

Automa ahora se distribuye como **app nativa de Windows**:

- Nuevo módulo [`app/desktop.py`](app/desktop.py): arranca el HTTP server en thread daemon y abre el panel dentro de una ventana `pywebview` (EdgeChromium en Windows 10/11). Entry-point `automa-desktop`.
- [`installer/automa.spec`](installer/automa.spec): bundle PyInstaller one-folder con todos los datafiles (`flows/`, `schemas/`, pywebview data) y los hidden imports necesarios. Output: `dist/Automa/Automa.exe` (~31 MB).
- [`installer/Automa.iss`](installer/Automa.iss): script Inno Setup 6+ que empaqueta el bundle como `Automa-Setup-vX.Y.Z.exe`. Install per-user (sin admin), shortcuts en Start Menu y opcional desktop, idiomas es/en.
- [`.github/workflows/release.yml`](.github/workflows/release.yml): workflow que dispara en push de tag `v*.*.*`, builda en `windows-latest`, compila el instalador con Inno Setup (preinstalado en el runner) y sube el `.exe` al release. Inputs sanitizados via env + regex contra inyección.
- [`engine/paths.py`](engine/paths.py): `root_dir()` respeta `$AUTOMA_ROOT` y `sys._MEIPASS` además del default basado en `__file__` — los flows y schemas se resuelven correctamente desde el bundle frozen.

### 🚀 Fase 2 del roadmap completa · 8 flows nuevos (13–20)

Los 8 casos planeados en [docs/ROADMAP.md](docs/ROADMAP.md) §Fase 2 ahora son operativos:

| # | Slug | Qué hace |
| --- | --- | --- |
| 13 | `notepad_quick_note` | Abre Notepad y tipea una nota configurable. |
| 14 | `run_dialog_command` | `Win+R` + tipea comando + Enter. |
| 15 | `clipboard_capture` | Lee el portapapeles y lo persiste a JSON. |
| 16 | `active_window_screenshot` | PNG solo de la ventana en foco (`pygetwindow`). |
| 17 | `taskmgr_snapshot` | Abre Task Manager y captura + OCR. |
| 18 | `powershell_audit` | Ejecuta PowerShell de allowlist read-only. |
| 19 | `taskbar_capture` | PNG solo de la barra de tareas. |
| 20 | `volume_mute_toggle` | Togglea el mute (tecla multimedia). |

Catálogo total: **20 flows operativos** (12 → 20).

### 🧰 4 acciones nuevas (~95 LOC)

Estrictamente aditivas — ningún cambio rompe acciones existentes:

- `screen.capture_region(output_path, bbox)` — recorte rectangular del monitor principal con `mss` (fallback PIL). `bbox` admite `{left, top, width, height}` o `{left, top, right, bottom}`; valores negativos = anclaje al borde opuesto (estilo CSS); valores grandes se clampean al borde.
- `screen.capture_active_window(output_path)` — resuelve el rect de la ventana en foco con `pygetwindow` y delega en `capture_region`. Devuelve `window_title` para auditoría.
- `system.read_clipboard(max_chars=10000)` — lee el portapapeles via `pyperclip`. Trunca a `max_chars`, reporta `length` real y `truncated`. Si el backend no está disponible, retorna `available=False` con `reason` legible — no levanta.
- `system.run_powershell(command, allowlist=None, timeout_seconds=30)` — corre PowerShell con allowlist estricta por verbo inicial (default read-only: `Get-Date`, `Get-Process`, …). Pre-rechaza tokens de chain/redirección (`;|&` `` ` `` `><` `$(` `$_`) **antes** de invocar pwsh.

### 📦 Dependencias agregadas

- `pyperclip>=1.8.2,<2` — portapapeles cross-platform.
- `PyGetWindow>=0.0.9,<1` — explícito (era transitivo via pyautogui).
- `pywebview>=5.4,<6` — ventana nativa para la app de escritorio.

### 🛡️ Calidad

- Suite: **115 tests pasando** (era 95). 20 tests nuevos cubren las 4 acciones y el wrapper desktop.
- Cobertura: **54.68%** (sobre el alcance `engine + actions + app + decision`).
- Ruff limpio, schema validation OK (20 flows · 33 acciones registradas).

### 🧹 Chore

- `.claude/` agregado a `.gitignore` para evitar staging accidental de worktrees locales.
- Markers `.disabled` removidos de los flows 08–12 (residuo del commit que introdujo el campo `preview`).

### 🚧 Preview: flows 08–12 visibles pero no operativos

Los 5 casos nuevos agregados en Fase 1 del roadmap (08 lock, 09 desktop capture, 10 explorer, 11 settings, 12 desktop OCR) ahora aparecen en el panel **marcados como preview**:

- Card del panel muestra badge `🚧 preview` y el botón Ejecutar queda deshabilitado con texto "🚧 Preview · no operativo".
- Atajos `Alt+8..Alt+=` reconocen el flow pero muestran toast informativo en lugar de ejecutar.
- Backend rechaza con HTTP 409 cualquier intento de ejecutar/programar/webhook un flow preview: `/api/run/`, `/api/hook/`, `/run`, `/flow/<folder>/schedule`.
- **Mecanismo canónico**: campo `"preview": true` en el manifest. Schema actualizado para aceptarlo como propiedad opcional booleana (`schemas/manifest.schema.json`). Documentado en `docs/CREAR_FLUJOS.md`.
- **Mecanismo override local**: archivo marcador `flows/NN_<slug>/.disabled` (no requiere tocar el manifest). Cualquiera de los dos dispara el estado preview — defense in depth.
- Cero cambios al motor — el catálogo, sandbox, orquestador y scheduler no saben de `preview`. La lógica vive solo en [app/server.py](app/server.py) (`_is_preview`).

CLI (`flujo run flows/NN_...`) **sí** los ejecuta — está pensado para desarrollo/test local.

### 🧰 Calidad: piso de cobertura + pre-commit hooks

- **Piso de cobertura**: `pytest` ahora exige `--cov-fail-under=54` con el alcance ampliado (`engine + actions + app + decision`, antes faltaba `decision`). Línea base 54.46% medida en CI 2026-06-02. Cualquier PR que baje de 54% rompe CI. Subir el piso es un PR aparte cuando suba la cobertura real.
- **Pre-commit hooks**: nuevo `.pre-commit-config.yaml` con `ruff` (check + format), `markdownlint-cli2`, validadores de `yaml/json/toml`, trailing-whitespace, EOF y bloqueo de archivos > 500 KB. Setup: `uv run pre-commit install`. Reduce ~50× el feedback loop vs esperar a GitHub Actions.

### 🎨 Rebrand: `flujo-autonomo-repo` → `automa-pc`

Renombre del proyecto a **Automa**. Es un cambio cosmético pero con superficie técnica: package name, CLI, env vars y URLs cambian. Migración (una vez):

| Antes | Después |
| --- | --- |
| Paquete: `flujo-autonomo` | `automa-pc` |
| CLI: `flujo`, `flujo-panel`, `flujo-validate` | `automa`, `automa-panel`, `automa-validate` |
| Env: `FLUJO_WEBHOOK_TOKEN`, `FLUJO_PANEL_TOKEN` | `AUTOMA_WEBHOOK_TOKEN`, `AUTOMA_PANEL_TOKEN` |
| Header HTTP: `X-Flujo-Token` | `X-Automa-Token` |
| Entry-point group: `flujo.actions` | `automa.actions` |
| Repo: `vladimiracunadev-create/flujo-autonomo-repo` | `vladimiracunadev-create/automa-pc` |
| Carpeta local sugerida: `flujo-autonomo-repo/` | `automa-pc/` |

**Breaking** para quien tenga variables de entorno seteadas o webhooks externos llamando con el header viejo — actualizar nombres. La palabra "flujo" como sustantivo común en docs no se renombra; sólo el brand "Flujo Autónomo" → "Automa".

### 🔒 Hardening del panel HTTP y acciones (auditoría 2026-06-01)

Auditoría interna sobre `app/server.py`, `actions/` y `engine/`. Cierra 8 hallazgos: 2 críticos, 3 altos, 2 medios, 1 bajo. Detalle completo en [docs/SEGURIDAD.md §"Auditoría 2026-06"](docs/SEGURIDAD.md#-auditoría-2026-06--hallazgos-y-fixes).

- **CSRF → RCE (crítico, CWE-352+78)**: todos los POST mutadores (`/api/run/`, `/run`, `/flow/<folder>/config`, `/flow/<folder>/schedule`, `/api/form/submit`) pasan ahora por `_authorize_mutation`. Dos modos: (a) `AUTOMA_PANEL_TOKEN` con `X-Automa-Token` (constant-time compare), (b) sin token, exige `Host` loopback y `Origin/Referer` consistentes. Bloquea el caso real "sitio web malicioso hace fetch a `127.0.0.1:8787`".
- **Command injection (crítico, CWE-78)**: `ui.launch_process(shell=True)` queda **rechazado por código** con `ValueError`. La rama `subprocess.Popen(command, shell=True)` se eliminó.
- **Path traversal (alto, CWE-22)**: `/file` validaba con `str.startswith(ROOT)`, que en Windows permitía bypass por prefijo (`...repo-evil` startswith `...repo`). Reemplazado por `Path.is_relative_to(ROOT.resolve())`. Además: allowlist de extensiones que bloquea `.html .htm .xhtml .xml .svg .js .mjs .css` (vector XSS reflejado) + header `X-Content-Type-Options: nosniff`.
- **XSS en panel (alto, CWE-79)**: `status.innerHTML` interpolaba `data.error/name` sin escape. Agregada función `_esc()` en cliente; todos los sinks dinámicos pasan por ahí.
- **Timing attack en token (medio, CWE-208)**: `_check_webhook_token` usaba `==`. Migrado a `hmac.compare_digest`.
- **Deps sin pinear (medio, CWE-1104)**: `requirements.txt` y `pyproject.toml` listaban `requests`, `Pillow`, etc. sin versión. Agregadas cotas `>=X.Y.Z,<MAJOR+1` con piso = primera versión sin CVE conocida al 2026-06-01.
- **MIME guessing en `/file` (bajo, CWE-117)**: cualquier archivo bajo ROOT se servía con MIME adivinado. Combinado con `/api/form/submit` (que ahora también exige auth) permitía XSS reflejado same-origin. Cerrado por allowlist + nosniff.
- **Regresión cubierta** en [`tests/test_security_hardening.py`](tests/test_security_hardening.py) (7 tests nuevos).

### 🔒 Hardening del CI/CD (supply chain)

Motivación: este repo ejecuta acciones de teclado/mouse/captura sobre el escritorio del operador. Un commit malicioso fusionado a `main` se traduce en RCE local. Por eso el CI pasa a tratarse como superficie de ataque crítica.

- **SHA pinning** de toda acción third-party (no más tags movibles tipo `@v4`):
  - `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683` (v4.2.2)
  - `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065` (v5.4.0)
  - `github/codeql-action/{init,analyze}@5c8a8a642e79153f5d047b10ec1cba1d1cc65699` (v3.28.10)
  - `astral-sh/setup-uv@caf0cab7a618c569241d31dcd442f54681755d39` (v3.2.4) — allowlist queda **vacía**.
- **`persist-credentials: false`** en todos los `actions/checkout` — el `GITHUB_TOKEN` ya no queda expuesto a steps posteriores.
- **Permisos mínimos** por workflow (`contents: read`) y solo se elevan en CodeQL (`security-events: write`, `actions: read`).
- **Concurrencia** con `cancel-in-progress: true` en CI/security/deps/markdown — reduce ventana de runs huérfanos con tokens vivos.
- **CodeQL** con `security-extended,security-and-quality` (antes: queries default).
- **detect-secrets pinned** (`==1.5.0`) + escaneo de los **últimos 50 commits** para detectar secretos commiteados y borrados después.
- **Trojan Source** (CVE-2021-42574): falla CI si aparecen Unicode bidi (`U+202A..E`, `U+2066..9`, `U+200F`, `U+061C`).
- **Homoglyphs / zero-width** (`U+200B/C/D`, `U+FEFF`) en `.py/.js/.ts/.yml`.
- **Patrones de ofuscación**: `exec(base64...)`, `eval()` dinámico, `os.system()` con concat, `subprocess(shell=True)` interpolado, `pickle.loads`, `__import__` dinámico.
- **URLs de exfiltración hardcodeadas**: webhooks de Discord/Slack/webhook.site/requestbin/burp/ngrok/pastebin.
- **pip-audit pinned** (`==2.7.3`) con enforcement progresivo (soft en PR, hard en push a main / schedule).
- **Workflow nuevo `workflow-security.yml`** que audita los propios YAML:
  - `actionlint 1.7.7` con verificación de checksum.
  - `zizmor==1.5.2` (template injection en `${{ }}`, permisos excesivos, `pull_request_target` peligroso, unpinned-uses, cache poisoning).
  - `pin-check` propio: falla CI si aparece un `uses:` third-party sin SHA de 40 chars (allowlist explícita única para `astral-sh/setup-uv`).
- **SECURITY.md** ampliada con sección "Hardening del CI/CD": política de pinning, triggers prohibidos (`pull_request_target`, `workflow_run`), tabla de detecciones y SHAs activos.
- **dependabot.yml**: label `security` en updates de actions + checklist de revisión manual antes de merge (verificar SHA upstream + changelog de permisos).

---

## [0.4.0] — 2026-05-02

### ✨ Nuevos casos operativos

- 🌐 **02 `screen_capture_browser`** (era 12): captura DOM con Playwright headless. Tiene **input inline en la card** para escribir la URL, atajo `Alt+2` abre modal pidiendo URL.
- 📋 **07 `browser_form_filler`**: operación avanzada sobre formularios web reales.
  - Lanza Chromium **visible** (`headless: false` por defecto), navega a `data/web/form_demo.html` (10 campos: nombre, apellido, email, teléfono, dirección, ciudad, país select, fecha nacimiento, profesión, comentario textarea).
  - Carga **dataset de 100 registros estables** (`data/seeds/form_seeds.json`) y elige uno **al azar sin repetir** entre corridas. Tracking persistente en `data/seeds/.used_indices.json` (ignorado por git). Cuando se agotan los 100, reset automático.
  - Llena los 10 campos uno por uno con `slow_mo=250ms` (visualmente observable), submit, espera validación JS de la página y captura `validation_text` + `submitted_payload` renderizado.
  - **Sin PNG**: solo datos. El JSON resultado queda en `output/reports/` y se muestra en el detalle del run.

### 🗑️ Eliminados (decisión consciente tras auditoría honesta)

- ❌ `02_screen_watchdog_rules` — heurística de brillo demasiado simple, no aportaba valor real.
- ❌ `07_browser_assisted_capture` — redundante con `02_screen_capture_browser` (Playwright es mejor).
- ❌ `08_ui_macro_recovery` — wrapper trivial sobre `ui.hotkey`, sin caso de uso único.
- ❌ `09_branching_document_router` — era demo del feature `transitions`, no caso productivo.
- ❌ `10_screen_ocr_click_recovery` — requería Tesseract instalado para tener valor real.
- ❌ `11_screen_tri_mode_operator` — alta complejidad de mantenimiento vs valor entregado.

### 🎨 UI

- ⌨️ **Atajos de teclado** en el panel: `Alt+1..Alt+=` para ejecutar flow N, `Alt+E/P/H/M` navegación, `?` o `F1` para modal de ayuda, `Esc` para cerrar.
- 📋 Cada card muestra su atajo como `<kbd>` en la esquina.
- 🔍 **Detalle de run rediseñado**:
  - Imagen capturada **prominente** (hero) con **lightbox** al hacer click.
  - Bloque "Qué pasó en esta corrida" con **resumen inteligente** específico por flow (RGB swatch, mini-tabla de procesos, lista de archivos, etc).
  - Pasos **clickeables** abren modal con resultado completo del paso.
  - Eventos técnicos y contexto crudo **colapsables** en `<details>` (no contaminan la vista).
- 📊 **Dashboard del flow** (`/flow/<folder>`):
  - Hero card con descripción + ejecutar inline.
  - 5 KPI cards (total / OK / fail / avg / scheduler).
  - **Grid visual** de últimas 12 corridas con preview (PNG real o claves del JSON).
- ⊘ Pasos de **rama no tomada** ahora se muestran como `NOT_TAKEN` con borde dashed (antes confundían con `PENDING`).

### 🔌 Override de context vía API

- `POST /api/run/<folder>` ahora acepta body JSON `{"context_overrides": {...}}` que se mergea con el context del flow. Usado por:
  - Flow 02: `target_url` desde input inline o modal.
  - Flow 03: `path_override` desde input inline o modal con sugerencias.
  - Flow 07: `headless`, `slow_mo_ms`, etc.

### 🛡️ Endpoint nuevo

- `POST /api/form/submit` recibe el JSON desde la página `form_demo.html` y lo persiste en `output/reports/form_submission_panel_<ts>.json`.

### 🐛 Bugs arreglados

- `extract_existing_paths` fallaba en Linux con `OSError: File name too long` cuando el state contenía strings largos (descripciones de 250+ chars). Fix: heurística de longitud + `try/except OSError`.
- OCR analyzer detecta ahora si Tesseract binario falta y devuelve `status: "unavailable"` en lugar de crashear.
- CSS `step-row`: las duraciones quedaban fuera del card verde — grid simplificado.
- Layout `two-col` se rompía por overflow horizontal del `<pre>` — fix con `min-width: 0` y `pre { white-space: pre-wrap }`.
- `setup-uv@v3` en CI fallaba buscando `uv.lock` inexistente — fix con `cache-dependency-glob: pyproject.toml`.

### 🛠️ CI / Calidad

- Nuevo workflow `security.yml`: CodeQL, detect-secrets, pip-audit, schedule semanal.
- Nuevo workflow `dependency-hygiene.yml`: detección de paquetes desactualizados.
- Nuevo workflow `markdown-docs.yml`: validación de links internos en MDs.
- Nuevo `.github/dependabot.yml`: actualización automática de pip + actions.

### 📚 Docs

- Nuevos: `LICENSE` (MIT), `SECURITY.md` (política de reporte), `CONTRIBUTING.md`, `RUNBOOK.md`.
- Manual de usuario actualizado con flow 02 (Playwright) y flow 07 (form filler).
- `FAMILIAS_Y_CASOS.md`: matriz de compatibilidad reducida a 7 flows reales.

### 🔧 Otros

- Acción `browser.capture_page` (Playwright) registrada (28 → 29 acciones tras agregar `browser.fill_form`).
- 100 seeds de datos sintéticos en `data/seeds/form_seeds.json`.

---

## [0.3.0] — 2026-05-01

### ✨ UI

- 🎨 **Panel rediseñado a 3 tabs**: `▶ Ejecutar`, `⏰ Programadas`, `📜 Histórico`. Single-page, sin framework, hash-based routing.
- ⚡ **Click-to-run en tiempo real**: nuevo `POST /api/run/<folder>`, spinner, toasts y badge de estado live por card.
- 🖼️ **Detalle de run con thumbnails**: capturas e imágenes generadas se muestran inline; archivos no-imagen como mini-cards.
- 📊 **Dashboard de métricas con KPI cards**: completadas, falladas, en curso, duración promedio.
- 🎨 Diseño refinado con CSS variables, gradientes suaves, animaciones sutiles, responsive con grid auto-fit.

### 🛠️ CI

- ✅ `setup-uv@v3` ahora cachea sobre `pyproject.toml` (antes fallaba buscando `uv.lock`).

### 🧪 Tests

- 5 tests del nuevo panel HTTP (live server contra puerto efímero). Suite total **82 verde**.

---

## [0.2.0] — 2026-05-01

### 🛡️ Sandbox por flow

- `allowed_actions`: lista blanca de acciones por manifest.
- `required_secrets`: variables requeridas antes de iniciar.
- `allowed_paths`: prefijos de ruta donde el flow puede operar.
- `max_runtime_seconds`: corta la corrida si excede tiempo total.
- Las violaciones quedan registradas como `sandbox_violation` en SQLite.

### ⏰ Scheduler con cron

- Nuevo parser cron de 5 campos sin dependencias externas (`engine/cron.py`).
- `next_after()` calcula próxima ejecución; soporta listas, rangos, pasos.
- Tabla `run_locks` en SQLite para evitar ejecución paralela del mismo flow.
- Migración suave para bases preexistentes.

### 📊 Observabilidad

- Endpoints: `/healthz`, `/api/flows`, `/api/runs`, `/api/metrics`, `/metrics` (Prometheus), `/metrics/dashboard`.
- Agregaciones: totales por estado, ventana móvil, top acciones lentas/fallidas/con retries.

### 🔌 Extensibilidad

- `LazyActionRegistry` descubre acciones de terceros via entry-point `flujo.actions`.
- Bóveda de secretos local (`engine/secrets.py`): env > file con prioridad.
- Acción `notify.send` con backends `log`, `file` y `webhook`. Tokens via `@secret:NOMBRE`.
- Webhook entrante `POST /api/hook/<folder>` autenticado por `AUTOMA_WEBHOOK_TOKEN`.

### 🧪 Calidad

- `pyproject.toml` con extras `dev`, `schema` y entry-points para CLI (`automa`, `automa-panel`, `automa-validate`).
- JSON Schema canónico en `schemas/manifest.schema.json`.
- Suite **77 tests pytest** (template, conditions, loader, registry, orquestador, sandbox, cron, locks, métricas, secrets, notify, schema vs manifests reales).
- CI con `uv` en matriz Linux/Windows × Python 3.10–3.12 + lint ruff + smoke job.

### 📚 Documentación

- 9 docs actualizados + 3 nuevos: `METRICAS.md`, `INTEGRACIONES.md`, `EXTENSION.md`.

---

## [0.1.0] — Versión inicial

- Motor declarativo `manifest.json` con `when`, `transitions`, retries y `max_steps_per_run`.
- Panel local en `127.0.0.1:8787`, persistencia en SQLite + JSON snapshots + JSONL events.
- 11 flows ejecutables: filesystem, sistema, navegador, pantalla, OCR, visión, branching documental.
- CLI `python -m engine.runner` con `list`, `run`, `scheduler`.
- Validador estructural de manifests.
- Smoke test integral.
