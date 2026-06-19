<br>
<div align="center">

# 🤖 Automa

### Control local de tareas y acciones efectivas sobre Windows

**Abre ventanas reales · Llena formularios · Captura escritorio y DOM · Audita el equipo · Todo declarativo en JSON**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/target-Windows-0078D4?logo=windows&logoColor=white)
![Desktop app](https://img.shields.io/badge/desktop-pywebview%20%2B%20PyInstaller-1F2937?logo=windows&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-headless%20%2B%20visible-2EAD33?logo=playwright&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-historial-003B57?logo=sqlite&logoColor=white)
![uv](https://img.shields.io/badge/packaging-uv-DE5FE9?logo=astral&logoColor=white)
![pytest](https://img.shields.io/badge/tests-115%20pytest-3DA639?logo=pytest&logoColor=white)
![Local First](https://img.shields.io/badge/local--first-sí-2D7A66)

[![CI](https://github.com/vladimiracunadev-create/automa-pc/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/automa-pc/actions/workflows/ci.yml)
[![Security](https://github.com/vladimiracunadev-create/automa-pc/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/automa-pc/actions/workflows/security.yml)
[![Workflow security](https://github.com/vladimiracunadev-create/automa-pc/actions/workflows/workflow-security.yml/badge.svg?branch=main)](https://github.com/vladimiracunadev-create/automa-pc/actions/workflows/workflow-security.yml)
[![License](https://img.shields.io/badge/license-MIT-15803d.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-0f766e)](CHANGELOG.md)
[![Security policy](https://img.shields.io/badge/security-policy-7c3aed.svg)](SECURITY.md)

</div>

![Automa cover](docs/assets/cover-automa-pc.svg)

---

## 🎯 ¿Para qué existe este repositorio?

Para **ejecutar acciones efectivas sobre el escritorio Windows** desde un panel local en `127.0.0.1`. La idea no es solo "ejecutar scripts en orden" — sino **abrir ventanas reales, interactuar con ellas, capturar evidencia y dejar trazabilidad**.

El objetivo a largo plazo: tener control declarativo sobre tareas operativas reales del PC — abrir aplicaciones, llenar formularios, automatizar pipelines de datos visuales, escalar de auditoría pasiva a operación activa.

> [!IMPORTANT]
> **Filtro de aceptación**: los casos que solo emiten JSON con datos del sistema (inventarios, healthcheck) son **utilidades básicas** — entran en el mínimo. Los casos que **abren ventanas, interactúan con DOM real, hacen capturas con datos contextualizados** son los que justifican el producto. La dirección de evolución apunta a más robustez visual e interactiva, no más reportes pasivos.

---

## 🗂️ Catálogo actual · 20 flows operativos

Clasificados por su nivel de interacción con el sistema. Hoja de ruta completa en [docs/ROADMAP.md](docs/ROADMAP.md).

### 🟢 Operaciones avanzadas (abren ventana o interactúan con componente Windows real)

| Caso | Familia | Qué hace efectivamente |
| --- | --- | --- |
| **`📷 01_screen_capture_analyze`** | pantalla | Captura el escritorio Windows completo (mss → PNG 1920×1080) y analiza brillo/RGB. |
| **`🌐 02_screen_capture_browser`** | navegador | Lanza Chromium headless con Playwright y captura el DOM renderizado de una URL configurable (input inline + atajo `Alt+2`). |
| **`📋 07_browser_form_filler`** | navegador | **Operación más avanzada del repo**: lanza Chromium *visible*, navega al formulario de 10 campos `data/web/form_demo.html`, elige uno de 100 registros del seed sin repetir, los rellena uno por uno con `slow_mo` (observable a ojo), submit, valida JS y guarda payload. |
| **`🔒 08_windows_lock_workstation`** | sistema | Bloquea el equipo (`Win+L`). Un clic = sesión bloqueada. |
| **`🖥️ 09_show_desktop_capture`** | pantalla | Minimiza todas las ventanas (`Win+D`), espera 800 ms y captura el escritorio limpio en PNG. |
| **`📁 10_explorer_open_path`** | sistema | Abre `explorer.exe` en una ruta configurable (por defecto `C:\Users`). |
| **`⚙️ 11_settings_open_section`** | sistema | Abre la app **Configuración** de Windows en sección configurable vía URI `ms-settings:` (red, pantalla, sonido…). |
| **`👁️ 12_desktop_ocr_inventory`** | pantalla | Captura el escritorio, ejecuta OCR sobre la imagen y guarda **todos los textos visibles** (con bboxes) como inventario JSON. |
| **`📝 13_notepad_quick_note`** | sistema | Abre Notepad y tipea una nota configurable. Scratchpad volátil de un click. |
| **`⌨️ 14_run_dialog_command`** | sistema | Abre el diálogo Ejecutar (`Win+R`), tipea un comando y lo lanza. |
| **`📋 15_clipboard_capture`** | sistema | Lee el portapapeles y lo persiste a JSON con timestamp. |
| **`🖼️ 16_active_window_screenshot`** | pantalla | PNG solo de la ventana en foco (sin escritorio ni otras apps). Incluye `window_title` en metadata. |
| **`📊 17_taskmgr_snapshot`** | pantalla | Abre Task Manager (`Ctrl+Shift+Esc`), captura screenshot y OCR de procesos visibles. |
| **`🛡️ 18_powershell_audit`** | sistema | Ejecuta un comando PowerShell de allowlist read-only y guarda stdout/stderr/exit_code a JSON. |
| **`🪟 19_taskbar_capture`** | pantalla | PNG solo de la franja inferior (barra de tareas + system tray). |
| **`🔇 20_volume_mute_toggle`** | sistema | Togglea el mute del audio maestro (tecla multimedia `volumemute`). |

### 🟡 Utilidades sobre el equipo (solo lectura · solo JSON)

| Caso | Familia | Qué hace |
| --- | --- | --- |
| `📁 03_folder_inventory` | filesystem | Lista archivos de una carpeta (input inline + atajo `Alt+3` con modal selector). |
| `📄 04_document_drop_pipeline` | documentos | Resume archivos `.txt`/`.md`/`.log`/`.csv`/`.json` de una carpeta. |
| `🖥️ 05_system_healthcheck` | sistema | Snapshot CPU/RAM/disco con `psutil` + reglas de alerta. |
| `⚙️ 06_process_watchdog` | sistema | Top 10 procesos con alertas por umbral de RAM/CPU. |

> Los flows 03–06 son **utilidades correctas pero pobres en valor**. La inversión próxima va a flows del bloque 🟢 (más interacción real, no más telemetría pasiva). Roadmap detallado → [docs/ROADMAP.md](docs/ROADMAP.md).

---

## 🚀 El panel en 3 tabs

```text
▶ Ejecutar         ⏰ Programadas         📜 Histórico
```

- **▶ Ejecutar** — cards por flow. Click ejecuta en tiempo real con progreso paso-a-paso. Atajos `Alt+1..Alt+7`.
- **⏰ Programadas** — scheduler con intervalo o cron de 5 campos. Lock SQLite contra ejecuciones paralelas.
- **📜 Histórico** — todas las corridas con filtro, badge de estado, duración y link al detalle.

**Detalle de cada run** muestra la imagen capturada en hero, un **resumen inteligente legible** (no JSON crudo), pasos clickeables con resultado completo en modal, y el contexto/eventos en `<details>` colapsables.

**Dashboard de cada flow** (`/flow/<folder>`) tiene **grid visual de las últimas 12 corridas** con preview real de cada una (PNG si hay, claves del JSON si no).

---

## ⚡ Inicio rápido

### Opción A · Instalador Windows (recomendado para usuarios)

1. Bajá **`Automa-Setup-vX.Y.Z.exe`** desde el [último release](https://github.com/vladimiracunadev-create/automa-pc/releases/latest).
2. Doble-click → wizard de instalación → "Launch Automa" al terminar.
3. Se abre una **ventana nativa** con el panel — sin browser, sin terminal.

El instalador no requiere admin (install per-user), agrega entrada al menú Inicio y opcional acceso directo en escritorio. Para desinstalar: Configuración → Aplicaciones → Automa.

### Opción B · Desde código (desarrollo / Linux / macOS)

```bash
uv sync --extra dev --extra schema
python -m playwright install chromium    # necesario para flows 02 y 07
uv run automa-desktop                    # ventana nativa pywebview
# o:
uv run automa-panel                      # solo HTTP en 127.0.0.1:8787
```

### Opción C · pip

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,schema]"
python -m playwright install chromium
automa-desktop
```

CLI tras instalar:

```bash
automa list                                    # lista flows
automa run flows/05_system_healthcheck         # corre uno
automa scheduler --interval 2                  # scheduler en bucle
automa-validate                                # JSON Schema + acciones + transitions
automa-panel                                   # panel HTTP en 127.0.0.1:8787
automa-desktop                                 # panel en ventana nativa pywebview
```

---

## 🎯 Demo de 5 minutos

1. 🟢 Levantá el panel.
2. 📋 Tab **Ejecutar** → atajo `Alt+7` → flow `browser_form_filler`. **Mirá**: se abre una ventana de Chromium, navega al form, **rellena los 10 campos uno por uno** con `slow_mo=250ms` (observable), submit, validación JS y cierra. Output JSON en `output/reports/form_submission_*.json` con el record elegido + tracking.
3. 🌐 Volvé al panel → atajo `Alt+2` → modal pide URL → escribe `https://github.com` o tu intranet → captura PNG real del DOM (sin pestañas en tu Chrome).
4. 📜 Tab **Histórico** → click el último run del flow 07 → verás los 10 datos enviados como **lista legible** (no JSON crudo) + el `submitted_payload` que la página renderizó.
5. ⏰ Tab **Programadas** → activá el flow 05 con cron `*/15 * * * *` → en 15 min ya tenés telemetría histórica del PC en SQLite.

---

## 🏗️ Arquitectura en una frase

Un `manifest.json` declara pasos y política de sandbox; el orquestador resuelve condiciones, templates y transiciones aplicando la política; las acciones se cargan bajo demanda; cada corrida persiste estado, eventos, salidas y métricas.

```mermaid
flowchart LR
    Flow["📋 flows/*/manifest.json"] --> Loader["FlowLoader"]
    Loader --> Orchestrator["⚙️ Orchestrator"]
    Schema["🧪 schemas/manifest.schema.json"] --> Validator["validate_project.py"]
    Config["⚙️ configs/*.json + context_overrides API"] --> Orchestrator
    Sandbox["🛡️ SandboxPolicy"] --> Orchestrator
    Orchestrator --> Registry["LazyActionRegistry · 33 acciones"]
    Registry --> Builtin["📦 actions/* (mss · psutil · playwright · pyautogui)"]
    Orchestrator --> DB["💾 db/runs.db"]
    Orchestrator --> Output["🖼️ output/screenshots + reports"]
    Panel["🖥️ app/server.py · 3 tabs · atajos Alt+N"] --> Orchestrator
    Scheduler["⏰ cron + lock SQLite"] --> Orchestrator
    Webhook["🪝 POST /api/hook (token)"] --> Orchestrator
```

---

## 📊 Estado del producto · v0.4.0

| Capa | Estado | Evidencia |
| --- | --- | --- |
| Panel 3-tabs + atajos teclado | 🟢 Operativo | [app/server.py](app/server.py) |
| Motor declarativo | 🟢 Operativo | [engine/orchestrator.py](engine/orchestrator.py) |
| Sandbox por flow | 🟢 Operativo | [engine/sandbox.py](engine/sandbox.py), [docs/SEGURIDAD.md](docs/SEGURIDAD.md) |
| Scheduler con cron + lock | 🟢 Operativo | [engine/scheduler.py](engine/scheduler.py) |
| Override de context vía API | 🟢 Operativo | `POST /api/run/<folder>` con body `{"context_overrides": {...}}` |
| Métricas Prometheus + dashboard | 🟢 Operativo | [engine/metrics.py](engine/metrics.py) |
| Webhooks IN | 🟢 Operativo | `POST /api/hook/<folder>` con `AUTOMA_WEBHOOK_TOKEN` |
| Plugins de terceros (entry-points) | 🟢 Operativo | [engine/action_registry.py](engine/action_registry.py) |
| **Casos avanzados (ventana real)** | 🟢 16 flows · 01 02 07–20 | [flows/](flows) |
| **Casos utilitarios (solo JSON)** | 🟡 4 flows · 03 04 05 06 | mínimo aceptable, no foco |
| **App de escritorio (instalador Windows)** | 🟢 v0.2.0 | [installer/](installer), [release.yml](.github/workflows/release.yml) |
| Suite pytest | 🟢 115 verde | [tests/](tests) |
| CI: lint + tests + smoke + security + docs | 🟢 Operativo | [.github/workflows/](.github/workflows) |
| CI hardening (SHA pin + zizmor + Trojan Source) | 🟢 Operativo | [SECURITY.md](SECURITY.md) §CI · [workflow-security.yml](.github/workflows/workflow-security.yml) |
| Multiusuario / RBAC | 🔴 No | un operador local |
| Aislamiento OS-level | 🟡 Sandbox declarativo, no proceso | [docs/SEGURIDAD.md](docs/SEGURIDAD.md) |

---

## ⌨️ Atajos del panel

| Tecla | Acción |
| --- | --- |
| `Alt+1`…`Alt+9` | Ejecutar flow 1…9 |
| `Alt+0` / `Alt+-` / `Alt+=` | Ejecutar flow 10 / 11 / 12 |
| `Alt+E` / `Alt+P` / `Alt+H` | Tab Ejecutar / Programadas / Histórico |
| `Alt+M` | Dashboard de Métricas |
| `?` o `F1` | Modal de ayuda |
| `Esc` | Cerrar modal |

Los flows 02, 03 y 07 abren un **modal especial pidiendo input** cuando se disparan por atajo (URL, ruta de carpeta, etc).

> [!NOTE]
> El panel mapea hasta 12 atajos `Alt`. Si el catálogo crece más allá de 12 flows, los nuevos casos se ejecutan haciendo clic en su card del panel.

---

## 🛡️ Seguridad

Dos frentes distintos, cada uno con su política dedicada:

### 1. Runtime — sandbox declarativo por flow

Cada flow declara su política directamente:

```json
{
  "id": "auditoria_segura",
  "allowed_actions": ["filesystem.list_directory", "filesystem.write_json"],
  "allowed_paths": ["data/auditorias", "output/reports"],
  "required_secrets": ["AUDIT_API_KEY"],
  "max_runtime_seconds": 60,
  "steps": [...]
}
```

El motor rechaza acciones fuera del allowlist, valida prefijos de paths y exige los secrets antes de iniciar. **Detalle completo → [docs/SEGURIDAD.md](docs/SEGURIDAD.md)**.

### 2. Supply chain — hardening del CI/CD

Este repo ejecuta acciones reales sobre tu escritorio Windows. Un commit malicioso fusionado a `main` se traduce en RCE local en cuanto haya `git pull`. Por eso el CI se trata como frontera de confianza con **12 capas de defensa**:

| # | Capa | Garantiza |
| --- | --- | --- |
| 1 | SHA pin en toda acción third-party | El código que se ejecuta es el aprobado al mergear |
| 2 | `pin-check` con parser YAML real | Imposible introducir un `uses:` sin SHA sin que falle CI |
| 3 | Allowlist vacía + excepciones documentadas | Cero excepciones silenciosas |
| 4 | `persist-credentials: false` | Token no queda accesible a steps posteriores |
| 5 | Permisos mínimos (`contents: read`) | Step comprometido no puede empujar a `main` |
| 6 | `concurrency: cancel-in-progress` | Ventana temporal de tokens reducida |
| 7 | Triggers prohibidos (`pull_request_target`) | Cierra el vector #1 de GitHub Actions |
| 8 | CodeQL `security-extended` | SAST sobre Python (CWE Top 25) |
| 9 | `actionlint` + `zizmor==1.5.2` | SAST sobre los propios workflows YAML |
| 10 | `detect-secrets==1.5.0` filesystem + 50 commits | Secretos commiteados detectados aunque se borren después |
| 11 | Trojan Source + ofuscación + URLs de exfil | Payloads que pasarían review humana |
| 12 | `pip-audit==2.7.3` (soft PR / hard main) | `main` sin CVEs publicadas |

> [!IMPORTANT]
> **Política completa con modelo de amenaza, justificación de cada capa y qué NO garantiza → [SECURITY.md §Hardening del CI/CD](SECURITY.md#hardening-del-cicd-supply-chain)**

Política de reporte de vulnerabilidades también en [SECURITY.md](SECURITY.md).

> [!WARNING]
> El webhook entrante está **deshabilitado por defecto** y requiere `AUTOMA_WEBHOOK_TOKEN`. Si lo expones más allá de localhost, ponelo detrás de un reverse proxy con TLS.

---

## ✅ Validación local antes de pushear

```bash
uv run pytest                          # 115 tests
uv run ruff check .                    # lint
uv run python scripts/validate_project.py   # JSON Schema + acciones (20 flows · 33 acciones)
```

Las tres deben pasar. CI corre lo mismo + `security.yml` (CodeQL `security-extended`, detect-secrets sobre filesystem **e historial**, Trojan Source CVE-2021-42574, ofuscación, exfiltración, pip-audit) + `workflow-security.yml` (actionlint + zizmor + pin-check sobre los propios YAML) + `markdown-docs.yml` (links rotos) + `dependency-hygiene.yml`.

Toda acción third-party va pinned a SHA — política completa en [SECURITY.md](SECURITY.md) §"Hardening del CI/CD".

---

## 📚 Documentación

### Operación

| Documento | Para qué |
| --- | --- |
| [📖 docs/MANUAL_USUARIO.md](docs/MANUAL_USUARIO.md) | Manual con casos resueltos en Windows real |
| [📕 RUNBOOK.md](RUNBOOK.md) | Procedimientos del día a día (reset, locks, queries) |
| [📊 docs/METRICAS.md](docs/METRICAS.md) | Endpoints, dashboard y formato Prometheus |
| [🔌 docs/INTEGRACIONES.md](docs/INTEGRACIONES.md) | Webhooks IN y notificaciones OUT |

### Diseño

| Documento | Para qué |
| --- | --- |
| [📐 docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Diseño técnico y flujo de ejecución |
| [🗂️ docs/FAMILIAS_Y_CASOS.md](docs/FAMILIAS_Y_CASOS.md) | Catálogo y matriz de compatibilidad |
| [✏️ docs/CREAR_FLUJOS.md](docs/CREAR_FLUJOS.md) | Contrato para escribir un flow nuevo |
| [🛡️ docs/SEGURIDAD.md](docs/SEGURIDAD.md) | Sandbox, secretos, modelo de confianza |
| [✅ docs/VALIDACION.md](docs/VALIDACION.md) | JSON Schema, pytest, CI, criterios |
| [🧩 docs/EXTENSION.md](docs/EXTENSION.md) | Publicar acciones de terceros vía entry-points |
| [🐛 docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Fallas comunes y diagnóstico |

### Proyecto

| Documento | Para qué |
| --- | --- |
| [📝 CHANGELOG.md](CHANGELOG.md) | Historial de versiones (Keep a Changelog) |
| [🤝 CONTRIBUTING.md](CONTRIBUTING.md) | Cómo contribuir |
| [🛡️ SECURITY.md](SECURITY.md) | Política de reporte de vulnerabilidades |
| [📜 LICENSE](LICENSE) | MIT |

---

## 🗃️ Estructura del repo

```text
/app          🖥️  Panel local + API JSON
/actions      📦 mss · psutil · playwright · pyautogui · webbrowser · ...
/engine       ⚙️  Motor: orquestador · sandbox · scheduler · cron · métricas · secretos
/flows        📋 20 casos operativos
/installer    📦 PyInstaller spec + Inno Setup script + build helper
/data
  /web        🌐 HTML local (form_demo · control_page)
  /seeds      🧬 100 registros del flow 07 + tracking de usados
  /inbox      📥 Carpeta de ejemplo para flow 03/04
/configs      ⚙️  Contexto persistido por flow
/secrets      🔐 Bóveda local (ignorada por git)
/schemas      🧪 JSON Schema del manifest
/db           💾 SQLite (runs.db)
/output       🖼️  reports/ + screenshots/
/state /logs  📂 Snapshots y eventos JSONL
/docs         📚 Documentación
/.github      🤖 CI · Security · Dependency hygiene · Markdown · Dependabot
```

---

## 🛣️ Próximos pasos

La dirección clara: **más operaciones avanzadas reales sobre Windows**, menos telemetría pasiva. El sistema **se construye agregando casos**, no refactorizando el motor.

**Roadmap completo y por fases → [docs/ROADMAP.md](docs/ROADMAP.md)**

Resumen:

- ✅ **Fase 1 (esta versión)**: 5 casos nuevos sobre componentes nativos de Windows usando solo acciones ya existentes (08–12).
- 📋 **Fase 2 (siguiente)**: 8 casos que requieren **acciones nuevas mínimas** en `actions/` (`system.read_clipboard`, `screen.capture_active_window`, `screen.capture_region`, `system.run_powershell`). Estrictamente aditivo — nada cambia en lo existente.
- 🔭 **Fase 3 (ideación)**: apps nativas (Excel, Word, PDF readers, Outlook, Edge) con sincronización determinista y anclaje visual por templates.

Si lo que aporta valor es solo "leer JSON del sistema y dejar reporte", probablemente exista una herramienta nativa más simple. La justificación de este producto es la **interacción declarativa con la sesión Windows**.

---

<div align="center">

**[⬆ Volver arriba](#-flujo-autónomo)** ·
**[📝 Changelog](CHANGELOG.md)** ·
**[🤝 Contribuir](CONTRIBUTING.md)** ·
**[🛡️ Reportar vulnerabilidad](SECURITY.md)** ·
**[🐛 Issues](https://github.com/vladimiracunadev-create/automa-pc/issues)**

Hecho con 🐍 Python · 🪟 sobre Windows · 💾 SQLite · 🛡️ Sandbox por flow

</div>
