# 10 · Configuración

> Todos los puntos de configuración del sistema: archivos, variables de entorno, valores
> por defecto, precedencias, diferencias entre entornos y **qué pasa exactamente cuando
> algo está mal configurado**. Ningún valor de este documento es real: los ejemplos usan
> marcadores explícitos y dominios reservados.

---

## 1. Mapa de la configuración

Automa no tiene un archivo de configuración global. La configuración vive repartida en
seis sitios, cada uno con un alcance distinto:

| Nivel | Dónde | Alcance | Versionado |
|---|---|---|:--:|
| 1 · Manifest | `flows/<carpeta>/manifest.json` | Estructura y política de **un flow** | ✅ |
| 2 · Contexto por defecto | `flows/<carpeta>/context.example.json` | Valores del flow, provistos por su autor | ✅ |
| 3 · Contexto local | `flows/<carpeta>/context.user.json` | Override local del operador | ❌ |
| 4 · Contexto del panel | `configs/<carpeta>.json` | Lo que guarda `POST /flow/<f>/config` | ✅ (solo existe uno) |
| 5 · Overrides de invocación | Body de `POST /api/run/<folder>` | Una sola corrida | — |
| 6 · Entorno y secretos | Variables de entorno, `secrets/secrets.json` | Todo el proceso | ❌ |

**No hay archivo `.env`, ni `settings.py`, ni `config.toml`.** Verificado con
`git ls-files`. El único manifiesto del proyecto es `pyproject.toml`, y no contiene
configuración de runtime.

## 2. El manifest: contrato de un flow

`schemas/manifest.schema.json` es el contrato completo. `additionalProperties: false` en
la raíz y en cada paso: **un campo desconocido es un error de validación**, no una clave
ignorada.

### 2.1 Campos de la raíz

| Campo | Tipo | Obligatorio | Por defecto | Qué pasa si falta o está mal |
|---|---|:--:|---|---|
| `id` | string `^[a-z0-9_]+$` | ✅ | — | `KeyError` en `load_manifest`; la CI lo detecta antes |
| `name` | string no vacío | ✅ | — | Igual |
| `steps` | array ≥ 1 elemento | ✅ | — | Igual |
| `description` | string | — | `""` | Se muestra vacía en el panel |
| `family` | string | — | `"general"` | El panel agrupa por familia |
| `start_step` | string | — | Primer paso del array | Si apunta a un paso inexistente: `FlowExecutionError` en la primera iteración |
| `max_steps_per_run` | integer 1–10000 | — | `200` | Un flow con transiciones circulares se corta al alcanzarlo |
| `allowed_actions` | array de strings únicos | — | `null` = **sin restricción** | Ver §2.2 |
| `required_secrets` | array de strings únicos | — | `[]` | Si el secreto no está en `os.environ`, el flow **no arranca** |
| `allowed_paths` | array de strings únicos | — | `null` = **sin restricción** | Ver §2.2 |
| `max_runtime_seconds` | number ≥ 0 | — | `null` = sin límite | Se comprueba **entre pasos**, no interrumpe uno en curso |
| `preview` | boolean | — | `false` | `true` → el panel muestra badge y los endpoints de ejecución responden `409` |

### 2.2 La trampa de la lista vacía

```python
# engine/loader.py::load_manifest
allowed_actions=list(raw['allowed_actions']) if raw.get('allowed_actions') else None
```

`raw.get('allowed_actions')` con una **lista vacía es falsy**, así que
`"allowed_actions": []` se convierte en `None`, es decir, en **política permisiva**.

Escribir una lista vacía con la intención de bloquear todas las acciones produce el efecto
exactamente contrario. Lo mismo vale para `allowed_paths`. Es un caso límite real,
verificado en el código y no cubierto por ninguna prueba. Registrado en
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md).

### 2.3 Configuración de sandbox en el catálogo real

| Configuración | Flows que la declaran | Cuáles |
|---|---:|---|
| `allowed_actions` | **13 de 27** | 08–20 |
| `allowed_paths` | **7 de 27** | 09, 12, 15, 16, 17, 18, 19 |
| `max_runtime_seconds` | **13 de 27** | 08–20, entre 3 y 40 segundos |
| `required_secrets` | **0 de 27** | Ninguno |
| `preview` | **0 de 27** | Ninguno |

Los 14 flows restantes (01–07 y 21–27) corren con `SandboxPolicy` permisiva y el histórico
lo registra: `state['policy']['permissive'] == True`. Análisis en
[11 · Seguridad](11-security.md).

### 2.4 Campos de un paso y de una transición

| Campo del paso | Tipo | Por defecto | Notas |
|---|---|---|---|
| `id` | string | — | ✅ obligatorio, único dentro del flow |
| `action` | string | — | ✅ obligatorio, debe estar registrado |
| `params` | object | `{}` | Se pasan como argumentos por nombre a la acción |
| `save_as` | string | — | Clave del contexto donde guardar el resultado |
| `retries` | integer 0–100 | `0` | **Sin espera entre intentos** |
| `when` | condition | — | Si no se cumple: `status: skipped` |
| `transitions` | array | `[]` | Sin transiciones, el orden es el del array |

| Campo de transición | Valores | Por defecto |
|---|---|---|
| `on` | `success`, `failure`, `any` | `success` |
| `next` | id de un paso existente | — |
| `end` | boolean | `false` |
| `when` | condition | — |

> **Detalle no obvio de las transiciones de fallo.** Para que un flow se recupere de un
> error, la transición `on: "failure"` debe apuntar a un paso **distinto del siguiente por
> defecto**. Si apunta al que ya venía a continuación, el motor no lo distingue de «no hay
> rama» y marca la corrida como `failed`. Ver
> [06 §1.2](06-deep-code-explanation.md#12-run--bloque-por-bloque).

## 3. El contexto de un flow

### 3.1 Precedencia: la primera que exista gana

```python
# engine/loader.py::load_context — orden de búsqueda
[--context RUTA]  →  configs/<carpeta>.json  →  flows/<c>/context.user.json  →  flows/<c>/context.example.json
```

**No hay mezcla de claves.** La primera fuente que exista se devuelve entera y las demás
se ignoran por completo.

**La consecuencia práctica más importante:** guardar la configuración desde el panel crea
`configs/<carpeta>.json`, que a partir de ese momento **oculta el `context.example.json`**.
Si una versión posterior del flow añade una clave nueva al ejemplo, el flow configurado no
la verá y el parámetro llegará a la acción como el placeholder literal sin resolver
(`"{{ nueva_clave }}"`), que probablemente provoque un error de tipo.

**Segunda trampa, más sutil:** `Path('configs')` es **relativa al directorio de trabajo**,
no a `root_dir()` ni a `data_dir()`. Pero `set_flow_config` escribe en
`data_dir() / 'configs'`. En desarrollo coinciden; en el binario empaquetado **no**: el
panel escribiría en `%LOCALAPPDATA%\Automa\configs\` y el loader leería `./configs`
relativo al cwd. `installer/automa_entry.py` hace `os.chdir(data_dir())` precisamente para
que coincidan, pero cualquier ejecución del CLI desde otra carpeta rompe la resolución.
Registrado en [15](15-risks-and-technical-debt.md).

### 3.2 Los contextos reales del catálogo

Los 27 `context.example.json`, agrupados por lo que configuran:

| Flow | Claves | Valores por defecto |
|---|---|---|
| `01_screen_capture_analyze` | `analyzer_override` | — |
| `02_screen_capture_browser` | `target_url`, `full_page`, `viewport_width`, `viewport_height`, `wait_seconds` | `data/web/control_page.html`, `true`, `1280`, `800`, `1` |
| `03_folder_inventory` | `path_override` | — |
| `04_document_drop_pipeline` | `dropbox_path`, `notes` | — |
| `05_system_healthcheck` | *(ninguna)* | — |
| `06_process_watchdog` | *(ninguna)* | — |
| `07_browser_form_filler` | `target_url`, `seeds_path`, `used_path`, `headless`, `slow_mo_ms`, `viewport_width`, `viewport_height` | HTML local, seed de 100, `false`, `250` |
| `08` `10` `13` `14` `20` | `dry_run` + parámetro propio (`folder_path`, `note`, `command`) | `dry_run` presente en todos |
| `09_show_desktop_capture` | `dry_run` | — |
| `11_settings_open_section` | `section` | URI `ms-settings:` |
| `12` `16` `17` `19` | *(ninguna o `dry_run`)* | — |
| `15_clipboard_capture` | `max_chars` | — |
| `18_powershell_audit` | `command` | Comando de la allowlist |
| `21_web_content_extract` | `target_url`, `include_tables`, `max_links`, `wait_seconds`, `take_screenshot` | `data/web/demo_page.html`, `true`, `100`, `0.5`, `true` |
| `22_web_site_map` | `start_url`, `max_pages`, `max_depth`, `same_domain_only`, `delay_seconds`, `respect_robots`, `wait_seconds` | `data/web/site_demo/index.html`, `10`, `2`, `true`, `0.2`, `true`, `0.2` |
| `23_web_change_detector` | `target_url`, `state_path`, `wait_seconds`, `notify_backend`, `notify_target` | `data/web/demo_page.html`, `data/web_watch/demo_page.json`, `0.5`, **`file`**, `output/notifications/web_changes.log` |
| `24_web_link_audit` | `target_url`, `max_links`, `timeout`, `wait_seconds` | `data/web/site_demo/index.html`, `100`, `10`, `0.2` |
| `25_web_table_extract` | `target_url`, `wait_seconds` | `data/web/demo_page.html`, `0.5` |
| `26_web_value_monitor` | `target_url`, `selector`, `threshold`, `state_path`, `wait_seconds`, `notify_backend`, `notify_target` | `data/web/demo_page.html`, `#precio`, `1000`, `data/web_watch/precio_demo.json`, `0.5`, **`file`**, `output/notifications/value_monitor.log` |
| `27_web_page_archive` | `target_url`, `archive_slug`, `wait_seconds` | `data/web/demo_page.html`, `demo_page`, `0.5` |

**Tres propiedades del catálogo por defecto que conviene proteger:**

1. **Todos los flows web apuntan a HTML locales del repositorio.** La demo funciona sin
   internet y es determinista.
2. **Los dos flows con notificación usan `backend: "file"`.** Nada sale del equipo hasta
   que el operador lo cambie a `webhook`.
3. **Los flows que mueven teclado o ratón exponen `dry_run`.** Un operador puede probarlos
   sin que ocurra nada.

### 3.3 `dry_run`: el interruptor de seguridad

Presente en los flows 08, 09, 10, 13, 14, 17 y 20. Con `dry_run: true`, las acciones de UI
devuelven el payload que habrían producido con `sent`/`typed`/`clicked`/`launched` en
`false`, **sin tocar el sistema**.

```json
{"dry_run": true}
```

Es la forma recomendada de probar un flow de UI por primera vez. Registro: es también lo
que permite que `tests/test_actions_basic.py` ejercite esas acciones en la CI sin efectos.

## 4. Variables de entorno

| Variable | Obligatoria | Por defecto | Efecto | Leída por |
|---|:--:|---|---|---|
| `AUTOMA_PANEL_TOKEN` | ❌ | Sin definir | Si está: **toda** mutación exige `X-Automa-Token` idéntico. Si no: modo anti-CSRF por `Host`/`Origin`/`Referer` | `app/server.py::_authorize_mutation` vía `get_secret` |
| `AUTOMA_WEBHOOK_TOKEN` | ❌ | Sin definir | Habilita `POST /api/hook/<folder>`. **Sin ella, el webhook responde 401 siempre** | `app/server.py::_check_webhook_token` |
| `AUTOMA_ROOT` | ❌ | Carpeta padre de `engine/` | Sobrescribe la raíz **de solo lectura** (`flows/`, `schemas/`) | `engine/paths.py::root_dir` |
| `AUTOMA_DATA_ROOT` | ❌ | `root_dir()` en desarrollo | Sobrescribe la raíz **escribible** (`db/`, `state/`, `logs/`, `configs/`, `secrets/`) | `engine/paths.py::data_dir` |
| `OPENAI_API_KEY` | ❌ | Sin definir | Respaldo de credencial del adaptador de visión. **Ningún flow lo usa** | `VisionModelAnalyzer._analyze_openai_compatible` |
| `LOCALAPPDATA` | Windows | Del sistema | Base de `data_dir()` en modo empaquetado | `engine/paths.py::data_dir` |
| `XDG_DATA_HOME` | Linux/macOS | `~/.local/share` | Base de `data_dir()` en modo empaquetado | `engine/paths.py::data_dir` |
| `PYTHONIOENCODING` | ❌ | Del sistema | **Recomendada en `utf-8`** para usar el CLI en Windows. Ver §7 | Python |

**Ninguna es obligatoria para arrancar.** El sistema funciona sin definir ni una sola.

### Ambos tokens también pueden vivir en archivo

`_authorize_mutation` y `_check_webhook_token` usan `engine.secrets.get_secret`, que busca
primero en `os.environ` y después en `secrets/secrets.json`:

```json
{
  "AUTOMA_PANEL_TOKEN": "PON-AQUI-UN-TOKEN-LARGO-Y-ALEATORIO",
  "AUTOMA_WEBHOOK_TOKEN": "PON-AQUI-OTRO-TOKEN-DISTINTO"
}
```

**Esos valores son marcadores, no credenciales.** Genere los suyos con
`python -c "import secrets; print(secrets.token_urlsafe(32))"`.

> **Inconsistencia verificada entre los dos mecanismos.** `SandboxPolicy.check_required_secrets`
> lee **solo `os.environ`**, no `get_secret`. Un secreto declarado en `required_secrets` que
> viva únicamente en `secrets/secrets.json` **no satisface la comprobación** y el flow no
> arranca. Los tokens del panel sí funcionan desde el archivo. Registrado en
> [15](15-risks-and-technical-debt.md).

### El archivo de secretos no está cifrado

`secrets/secrets.json` se escribe en texto plano con `json.dumps`. El docstring de
`engine/secrets.py` declara la decisión sin adornos: «permisos del FS son el control de
acceso». Está en `.gitignore` (`secrets/*.json`, con excepción de `.gitkeep`).

`engine.secrets.list_secret_names()` devuelve los **nombres** conocidos —los del archivo,
más las variables de entorno que empiecen por `AUTOMA_` o terminen en `_API_KEY` o
`_TOKEN`— **sin exponer ningún valor**. Es el diseño correcto para una pantalla de
diagnóstico.

## 5. Diferencias entre entornos

| Aspecto | Desarrollo | Binario instalado | CI |
|---|---|---|---|
| `root_dir()` | Raíz del repositorio | `sys._MEIPASS` (bundle extraído) | Raíz del repositorio |
| `data_dir()` | **Igual que `root_dir()`** | `%LOCALAPPDATA%\Automa` | Raíz del repositorio |
| Directorio de trabajo | Donde se lance el comando | `data_dir()` (por `os.chdir`) | Raíz del repositorio |
| Base de datos | `db/runs.db` | `%LOCALAPPDATA%\Automa\db\runs.db` | `db/runs.db`, efímera |
| Salidas | `output/` del repo | `%LOCALAPPDATA%\Automa\output\` | `output/` del repo |
| Playwright | Instalado a mano | Chromium **no** viene en el bundle | Sin instalar |
| Tesseract | Opcional | No viene en el bundle | Sin instalar |
| Panel | `automa-panel` o `automa-desktop` | Ventana nativa | No se levanta como servicio |
| Tokens | Sin definir | Sin definir | Sin definir |

**No hay archivos de configuración por entorno.** No existe `config.dev.json` ni
`config.prod.json`. La única diferencia entre entornos la resuelve `engine/paths.py` en
función de si el proceso está congelado.

`NO IDENTIFICADO`: no existe ningún sistema de *feature flags*. El único conmutador de
disponibilidad es `preview` en el manifest y el archivo marcador `.disabled` en la carpeta
del flow —y ningún flow del catálogo usa ninguno de los dos.

### El archivo marcador `.disabled`

```bash
touch flows/07_browser_form_filler/.disabled
```

`app/server.py::_is_preview` lo comprueba antes que el campo `preview` del manifest.
Permite **desactivar un flow localmente sin tocar el manifest ni commitear**. Los endpoints
de ejecución responderán `409`. Es un detalle operativo útil y poco visible;
`NO DOCUMENTADO EN EL REPOSITORIO` fuera del propio docstring.

Con el flow desactivado, el **CLI sigue funcionando**: el comentario del schema lo declara
como intencional, para poder probar un flow antes de quitarle la marca.

## 6. Consecuencias de una configuración incorrecta

| Error de configuración | Síntoma | Gravedad |
|---|---|---|
| `"allowed_actions": []` | Se convierte en política **permisiva**, no restrictiva | **Alta**: falsa sensación de seguridad |
| `configs/<f>.json` obsoleto tras actualizar el flow | Placeholder sin resolver llega a la acción → `TypeError` o ruta literal `{{ clave }}` | Media |
| Umbral como texto (`"threshold": "1000"`) | `TypeError` al comparar en `conditions.matches` | Media |
| `cron_expression` con día de semana estilo crontab | Se ejecuta el **día equivocado**: aquí `0` es lunes, no domingo | **Alta**: silenciosa |
| `cron_expression` pensada en hora local | Se ejecuta en **UTC** | Media: silenciosa |
| `interval_seconds` y `cron_expression` a la vez | El cron gana, el intervalo queda inerte | Baja |
| `allowed_paths` con ruta relativa mal escrita | `SandboxViolation` y flow bloqueado | Baja: falla ruidosamente |
| `required_secrets` con secreto solo en `secrets.json` | El flow **no arranca**: `assert_secrets_present` solo mira el entorno | Media |
| `notify_backend: "webhook"` sin `notify_target` | `ValueError` y paso fallido | Baja |
| `AUTOMA_WEBHOOK_TOKEN` sin definir | Todo `POST /api/hook/*` responde `401` | Baja: es el diseño |
| `AUTOMA_PANEL_TOKEN` definido y el cliente no lo envía | `401` en toda mutación, incluido el propio panel web | Media |
| `target_url` apuntando a un archivo inexistente | `FileNotFoundError` en `_to_url` | Baja |
| `AUTOMA_DATA_ROOT` a una ruta sin permisos | `PermissionError` al crear el directorio | Media |
| `system.run_powershell` con `allowlist` ampliada en el manifest | La allowlist por defecto queda **anulada** | **Alta** |

### El caso del cron, con detalle

```python
# engine/cron.py
(0, 6),    # day of week (0=lunes, 6=domingo, estilo ISO)
```

En crontab(5) estándar, `0` es **domingo**. Aquí es **lunes**. Una expresión copiada de
internet como `0 9 * * 1` («lunes a las 9» en cron estándar) se dispararía aquí en
**martes**. Está documentado en un comentario del código, pero no en `docs/OPERACION.md`
ni en la ayuda del panel.

Además, cuando ni `day of month` ni `day of week` son `*`, este cron exige que **ambos**
coincidan (AND); crontab(5) usa OR. Y `next_after` trabaja siempre en **UTC**.

Tres divergencias con el estándar, todas silenciosas. Registradas en
[15](15-risks-and-technical-debt.md).

## 7. Configuración del entorno de ejecución en Windows

```powershell
# Necesario para usar el CLI: sin esto, `automa list` y `automa run` revientan
# al imprimir JSON con caracteres no representables en cp1252.
$env:PYTHONIOENCODING = "utf-8"
```

Verificado durante el análisis: sin la variable, `python -m engine.runner list` termina en
`UnicodeEncodeError: 'charmap' codec can't encode character '→'`. Con ella, devuelve
el JSON completo. **El flow sí se ejecuta**; lo que falla es la impresión posterior.

## 8. Configuración de las herramientas de desarrollo

Toda en `pyproject.toml`:

| Sección | Configuración |
|---|---|
| `[tool.pytest.ini_options]` | `-q --strict-markers --cov=engine --cov=actions --cov=app --cov=decision --cov-report=term-missing --cov-fail-under=54`; `testpaths = ["tests"]`; marcadores `integration` y `slow` |
| `[tool.ruff]` | `line-length = 120`, `target-version = "py310"` |
| `[tool.ruff.lint]` | `select = ["E","F","W","I","B","UP"]`, `ignore = ["E501"]` |
| `[tool.ruff.lint.per-file-ignores]` | `"tests/**" = ["B011"]` (permite `assert False`) |
| `[tool.hatch.build.targets.wheel]` | `packages = ["engine","actions","app","decision","plugins","scripts"]` |

**`--cov-fail-under=54`** es un gate real: la suite falla si la cobertura baja de 54 %.
Medición actual: **58,92 %**. El margen es de menos de 5 puntos.

`ignore = ["E501"]` con `line-length = 120` significa que el límite de línea se declara
pero no se aplica; `app/server.py` tiene líneas mucho más largas por el HTML embebido.

Y `.pre-commit-config.yaml` añade hooks locales: `trailing-whitespace`,
`end-of-file-fixer`, `check-yaml`, `check-json` (excluyendo los manifests, validados
aparte), `check-toml`, `check-merge-conflict`, `check-added-large-files` (500 KB),
`mixed-line-ending --fix=lf`, `ruff --fix`, `ruff-format` y `markdownlint-cli2`.

> **Nota sobre `ruff-format` en pre-commit:** el hook está declarado pero la CI **no**
> ejecuta `ruff format --check`. Un colaborador sin `pre-commit install` puede subir código
> con formato distinto sin que nada falle.

## 9. Cómo configurar sin romper nada: receta

1. **Para un cambio puntual y reversible**, use `context_overrides` en la llamada a
   `POST /api/run/<folder>`. No toca ningún archivo.
2. **Para un cambio local persistente**, cree `flows/<carpeta>/context.user.json`. No está
   versionado y no oculta futuras claves del ejemplo... salvo que exista un
   `configs/<carpeta>.json`, que tiene más prioridad.
3. **Evite guardar desde el panel** si el flow va a actualizarse: el `configs/<f>.json`
   resultante congelará el conjunto de claves.
4. **Antes de programar con cron**, recuerde: `0` es lunes y la hora es UTC. Verifique con
   `python -c "from engine.cron import next_after; from datetime import datetime,timezone;
   print(next_after('*/15 * * * *', datetime.now(timezone.utc)))"`.
5. **Antes de ejecutar un flow de UI por primera vez**, póngalo en `dry_run: true`.
6. **Nunca escriba una credencial en `params`.** Un valor en `params` acaba en claro en
   `steps.params_json`. Use `@secret:NOMBRE` en `notify.send`, o la variable de entorno.

## 10. Lo que no se puede configurar

Valores fijos en el código, sin punto de extensión:

| Constante | Valor | Dónde |
|---|---|---|
| Puerto del panel | `8787` | `app/server.py::run_server`, `app/desktop.py::DEFAULT_PORT` — configurable solo por argumento de `automa-desktop` |
| Bind del panel | `127.0.0.1` | Igual |
| Intervalo del scheduler del panel | `2.0` s | `app/server.py`, línea de módulo |
| Ventana de métricas | `200` corridas | `engine/metrics.py::overview` |
| Límite de resultados de métricas | `10` | Todas las consultas `LIMIT 10` |
| Espera del arranque de la ventana | `8.0` s | `app/desktop.py::_wait_for_server` |
| Tamaño de ventana | `1200×800` | `app/desktop.py::DEFAULT_SIZE` |
| Allowlist de PowerShell por defecto | 13 verbos | `actions/system.py::_PS_DEFAULT_ALLOWLIST` |
| Extensiones bloqueadas en `/file` | 8 | `app/server.py::do_GET` |
| Patrón de `folder` | `^[A-Za-z0-9_\-]{1,64}$` | `app/server.py::_FOLDER_RE` |
| Campos del formulario del flow 07 | 10 nombres | `actions/browser_form.py::fill_form` |
| Extensiones de `summarize_text_folder` | `.txt .md .log .csv .json` | `actions/filesystem.py` |
| Prefijo de las métricas Prometheus | `flujo_` | `engine/metrics.py` |
| Retención de datos | **No existe** | — |

---

**Documentos relacionados:**
[02 · Instalación](02-installation-and-execution.md) ·
[05 · Referencia técnica](05-technical-reference.md) ·
[08 · Flujo de datos](08-data-flow.md) ·
[11 · Seguridad](11-security.md) ·
[14 · Solución de problemas](14-troubleshooting.md)
