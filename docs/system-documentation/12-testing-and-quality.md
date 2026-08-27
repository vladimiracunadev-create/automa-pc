# 12 · Pruebas y calidad

> Qué se prueba, qué no, con qué cobertura medida, qué herramientas de calidad hay y qué
> pruebas faltan, priorizadas. Todas las cifras de este documento se obtuvieron ejecutando
> los comandos del propio repositorio en el commit analizado.

---

## 1. Resultado medido

| Comando | Resultado real | Duración |
|---|---|---|
| `python -m pytest` | **150 passed, 0 failed** | 16,62 s |
| `python -m ruff check .` | **All checks passed!** | < 1 s |
| `python scripts/validate_project.py` | `{"ok": true, "flows_checked": 27, "registered_actions": 36, "errors": []}` | < 1 s |
| `python scripts/smoke_test.py` | `{"ok": true, "runs": 20, "db_path": "…/db/runs.db"}` | ~2 s |

Los cuatro gates del repositorio están **en verde** en el commit `ff246ab`.

## 2. Tipos de prueba

`pytest` con 17 archivos y **150 pruebas**. Dos marcadores declarados en
`pyproject.toml` —`integration` y `slow`— con `--strict-markers` activo.

| Tipo | Dónde | Qué ejercita |
|---|---|---|
| **Unitarias puras** | `test_template`, `test_conditions`, `test_cron`, `test_browser_extract` (mayoría) | Funciones sin efectos: placeholders, operadores, cron, hash, links, BFS |
| **Unitarias con filesystem** | `test_loader`, `test_actions_basic`, `test_secrets_and_notify` | Escriben en `tmp_path` |
| **Integración con SQLite** | `test_orchestrator`, `test_run_locks`, `test_metrics`, `test_panel_endpoints` | Base de datos real, redirigida por fixture |
| **Contrato** | `test_manifest_schema`, `test_action_registry` | JSON Schema y registro de acciones |
| **Seguridad** | `test_security_hardening` | `_safe_folder`, path traversal, allowlist de PowerShell, `shell=True` |
| **Humo de extremo a extremo** | `scripts/smoke_test.py` (fuera de pytest) | Tres flows completos + scheduler + base |

### El patrón que hace posible probar la familia web sin navegador

`actions/browser_extract.py` separa deliberadamente lo puro de lo impuro. Su docstring lo
declara: la interacción con Playwright vive en tres funciones de pegamento y **toda la
lógica** —hash, normalización, links, tracking, markdown, CSV, BFS— son funciones puras.

`tests/test_browser_extract.py` (358 líneas, el archivo de pruebas más grande) explota eso
con una `FakePage` que imita la interfaz de Playwright y un `fetch_page` falso para el
crawl. Resultado medible: **`actions/browser_extract.py` alcanza 91 % de cobertura sin
lanzar un solo Chromium**, mientras que `browser_capture.py` y `browser_form.py` —que no
tienen esa separación— se quedan en 18 % y 0 %.

Es la propiedad de diseño más valiosa del repositorio en materia de pruebas, y la que hay
que exigir a cualquier acción nueva.

## 3. Cobertura medida

Gate configurado: `--cov-fail-under=54` en `pyproject.toml`. Ámbitos:
`--cov=engine --cov=actions --cov=app --cov=decision`.

**Medición del análisis: 2 527 sentencias, cobertura total entre 58,9 % y 60,0 %.**

> **La cobertura no es reproducible entre ejecuciones.** Dos corridas consecutivas de
> `pytest` en el mismo commit dieron 58,92 % y 60,0 %. La causa `INFERENCIA`: importar
> `app.server` arranca un hilo de scheduler (`SCHEDULER.start_in_background()` a nivel de
> módulo), y cuántas líneas de `engine/scheduler.py` se ejecutan depende del temporizado
> del hilo. En la primera corrida `scheduler.py` marcó 51 %, en la segunda 76 %. El margen
> sobre el gate de 54 % es de apenas 5 puntos, así que una corrida desafortunada podría
> hacer fallar la CI sin ningún cambio de código. Registrado en
> [15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md).

### Cobertura por módulo

| Módulo | Sentencias | Cobertura | Lectura |
|---|---:|---:|---|
| `engine/loader.py` | 27 | **100 %** | Contrato del manifest, completo |
| `engine/logger.py` | 17 | **100 %** | |
| `engine/metrics.py` | 36 | **100 %** | |
| `engine/models.py` | 31 | **100 %** | Dataclasses |
| `engine/template.py` | 40 | **100 %** | Los placeholders, completos |
| `engine/sandbox.py` | 57 | **95 %** | La política, casi completa |
| `engine/conditions.py` | 52 | **90 %** | |
| `engine/introspection.py` | 41 | **90 %** | |
| `actions/browser_extract.py` | 245 | **91 %** | La lógica pura de la familia web |
| `engine/orchestrator.py` | 175 | **87 %** | El bucle central |
| `engine/cron.py` | 70 | **87 %** | |
| `engine/paths.py` | 29 | **86 %** | |
| `engine/action_registry.py` | 44 | **84 %** | |
| `engine/scheduler.py` | 55 | 51–76 % | **Variable entre corridas** |
| `engine/database.py` | 129 | 73 % | |
| `engine/secrets.py` | 33 | 73 % | |
| `engine/catalog.py` | 43 | 72 % | |
| `engine/state_store.py` | 16 | 75 % | |
| `actions/rules.py` | 36 | 75 % | |
| `actions/system.py` | 71 | 65 % | |
| `actions/filesystem.py` | 71 | 59 % | |
| `actions/notify.py` | 45 | 58 % | |
| `actions/ui.py` | 64 | 56 % | Solo la rama `dry_run` |
| `engine/manifest_schema.py` | 45 | 53 % | El respaldo sin `jsonschema` no se ejercita |
| `actions/http_actions.py` | 45 | 53 % | |
| `app/desktop.py` | 60 | 48 % | |
| **`app/server.py`** | **593** | **38 %** | El archivo más grande, el menos cubierto |
| `actions/screen.py` | 86 | **30 %** | Requiere escritorio gráfico |
| `actions/browser_capture.py` | 34 | **18 %** | Requiere Chromium |
| **`actions/browser_form.py`** | **90** | **0 %** | El flow más complejo, sin ninguna prueba |
| **`actions/vision.py`** | **104** | **0 %** | Ninguna prueba |
| **`engine/runner.py`** | **37** | **0 %** | El CLI, sin ninguna prueba |
| `decision/optional_ai.py` | 3 | **0 %** | Código muerto |
| `decision/rules.py` | 3 | **0 %** | Código muerto |

`plugins/analyzers/` **no está en el ámbito de cobertura**: `--cov` cubre `engine`,
`actions`, `app` y `decision`, pero no `plugins`. Sus 379 líneas —incluido
`VisionModelAnalyzer` con 222— no se miden. Como `actions/vision.py` está al 0 %,
`INFERENCIA`: los cuatro analizadores solo se ejecutan de forma indirecta, si acaso, y su
comportamiento de degradación no está verificado por ninguna prueba.

### Los cinco módulos al 0 %

| Módulo | Líneas | Por qué no se prueba | ¿Es aceptable? |
|---|---:|---|---|
| `actions/vision.py` | 104 | Depende de Pillow y del binario `tesseract` | **No.** `find_text_in_image` e `inspect_screen_target` son lógica pura sobre el resultado del OCR: se pueden probar con un `matches` falso |
| `actions/browser_form.py` | 90 | Depende de Chromium | **Parcialmente.** `_pick_record`, `_load_used_ids` y `_save_used_ids` son puras y críticas |
| `engine/runner.py` | 37 | El CLI | **No.** `build_parser` es trivial de probar, y ahí vive un defecto real (§7) |
| `decision/rules.py` | 3 | Código muerto | Irrelevante |
| `decision/optional_ai.py` | 3 | Código muerto | Irrelevante |

## 4. Fixtures y datos de prueba

`tests/conftest.py`, 28 líneas y solo dos fixtures:

| Fixture | Qué hace |
|---|---|
| `tmp_runtime` | Crea `db/`, `logs/`, `state/`, `output/`, `configs/` y `flows/` dentro de un `tmp_path` y hace `monkeypatch.chdir(tmp_path)` |
| `project_root` | Devuelve la raíz del repositorio |

El aislamiento se consigue **cambiando el directorio de trabajo**, no parcheando módulos.
Su propio docstring explica el porqué: «El motor escribe rutas relativas a la cwd. Para
tests deterministas cambiamos cwd al tmp y dejamos que cree sus propias carpetas». Es
simple y funciona, y de paso documenta una propiedad real del sistema: en modo desarrollo,
**todo se resuelve contra el cwd**.

`tests/test_actions_basic.py` sí ejercita la otra vía —`monkeypatch.setenv("AUTOMA_DATA_ROOT", …)`—
en las tres pruebas que cubren `engine/paths.py::data_dir`, añadidas en la v0.2.1 según el
`CHANGELOG.md`. Eso explica el 86 % de `paths.py`.

| Recurso | Ubicación | Uso |
|---|---|---|
| `tests/assets/sample_ui.png` | Versionado | Imagen para las pruebas de análisis |
| `data/seeds/form_seeds.json` | Versionado, 100 registros | Dataset del flow 07 |
| `data/web/*.html` | Versionado, 7 archivos | Páginas de demo para los flows web |
| `data/inbox/example.txt`, `data/dropbox/inbox/*` | Versionado | Entrada de los flows 03 y 04 |
| `tmp_path` de pytest | Efímero | Escrituras de las pruebas de filesystem |

**No hay factories ni datos generados.** Los fixtures son archivos reales versionados, lo
que hace las pruebas deterministas y legibles a costa de flexibilidad.

## 5. Herramientas de calidad

### Análisis estático y formato

| Herramienta | Configuración | Dónde corre |
|---|---|---|
| `ruff check` | `select = ["E","F","W","I","B","UP"]`, `ignore = ["E501"]`, `line-length = 120` | CI + pre-commit |
| `ruff format` | Por defecto | **Solo pre-commit** |
| CodeQL | `security-extended,security-and-quality` sobre Python | `security.yml` |
| `actionlint` | Con verificación de checksum del binario | `workflow-security.yml` |
| `zizmor` | `==1.5.2`, pinneado | `workflow-security.yml` |
| `detect-secrets` | `==1.5.0`, filesystem + 50 commits | `security.yml` |
| `pip-audit` | Soft en PR, hard en `main` | `security.yml` |
| `markdownlint-cli2` | `v0.15.0` | **Solo pre-commit** |
| Verificador de enlaces Markdown | Script Python propio | `markdown-docs.yml` |

> **Dos huecos entre pre-commit y CI.** `ruff format --check` y `markdownlint-cli2` están
> declarados en `.pre-commit-config.yaml` pero **no se ejecutan en ningún workflow**.
> Verificado: `grep -rn "ruff format" .github/workflows/` no devuelve nada. Un colaborador
> que no ejecute `pre-commit install` puede subir código con formato distinto y Markdown
> con problemas de lint sin que ningún gate lo detecte.

### Gates de la CI

| Workflow | Qué falla la construcción |
|---|---|
| `ci.yml` · job `test` | `ruff check`, `validate_project.py` o `pytest` (incluido el umbral de cobertura), en 6 combinaciones: 2 SO × 3 versiones de Python |
| `ci.yml` · job `smoke` | `smoke_test.py` en Ubuntu con Python 3.12 |
| `security.yml` | `detect-secrets` con hallazgo, `pip-audit` en `main`, Trojan Source, ofuscación |
| `workflow-security.yml` | `actionlint`, `zizmor`, `pin-check` |
| `markdown-docs.yml` | Cualquier enlace relativo roto en **cualquier** `.md` del repositorio |

`dependency-hygiene.yml` es informativo: usa `continue-on-error: true`.

**Nota sobre `markdown-docs.yml`:** solo se dispara en `pull_request` con `paths:
'**/*.md'`. Un push directo a `main` con un enlace roto **no lo detecta**.

## 6. El validador de manifests

`scripts/validate_project.py` es el gate específico del dominio. Cinco comprobaciones por
manifest:

1. JSON Schema completo (o respaldo estructural si falta `jsonschema`).
2. IDs de paso no duplicados.
3. Toda `action` está registrada en `ACTION_REGISTRY`.
4. Toda `action` está dentro del `allowed_actions` del propio manifest, si lo declara.
5. `transitions.next` y `start_step` apuntan a pasos existentes.

La comprobación 4 es especialmente valiosa: impide publicar un flow cuya política se
contradiga con sus propios pasos.

**Lo que no comprueba, y son huecos reales:**

| Hueco | Consecuencia |
|---|---|
| Que los `params` coincidan con la firma de la acción | Un paso sin un parámetro obligatorio pasa la CI y falla con `TypeError` en ejecución |
| Que el flow declare `allowed_actions` | 14 de 27 flows no lo hacen y nadie avisa |
| Que una transición tenga `next` o `end` | Una transición inerte pasa desapercibida |
| Que `allowed_actions: []` no sea una lista vacía | Se convierte silenciosamente en política permisiva |
| Que los `params` de `system.run_powershell` no amplíen la allowlist | Ver [11 · Seguridad](11-security.md) |

## 7. Módulos y comportamientos sin cobertura

### 7.1 El defecto del CLI que ninguna prueba habría detectado

`engine/runner.py` tiene **0 % de cobertura** y contiene un defecto reproducible:

```text
$ python -m engine.runner list
UnicodeEncodeError: 'charmap' codec can't encode character '→' in position 6042
```

`print(json.dumps(..., ensure_ascii=False))` sobre una consola Windows `cp1252`. Afecta a
`list` y a `run`. **Una sola prueba que capturase `stdout` con codificación forzada lo
habría detectado.** Es el ejemplo más claro del costo de dejar un módulo sin pruebas.

### 7.2 Comportamientos críticos sin prueba

| Comportamiento | Módulo | Riesgo de no probarlo |
|---|---|---|
| `_pick_record` sin repetir y con reinicio de ciclo | `browser_form.py` | El flow 07 podría repetir registros sin que nadie lo note |
| `is_success` por comparación de texto | `browser_form.py` | Un cambio de copy en la página lo rompe en silencio |
| `find_text_in_image` sobre `matches` del OCR | `vision.py` | Lógica pura, trivialmente testeable |
| `inspect_screen_target` en sus tres modos | `vision.py` | 100 líneas de lógica de decisión sin cubrir |
| Degradación de `OCRImageAnalyzer` sin `tesseract` | `plugins/` | **Fuera del ámbito de `--cov`** |
| `_smart_summary` para los 6 flows que cubre | `app/server.py` | Sin prueba de renderizado |
| `_is_preview` con `.disabled` y con `preview: true` | `app/server.py` | Mecanismo de desactivación sin cubrir |
| `render_*` del panel (≈660 líneas) | `app/server.py` | Escapado HTML sin verificar |
| `allowed_actions: []` → política permisiva | `engine/loader.py` | Caso límite con impacto de seguridad |
| `data_dir()` en modo congelado | `engine/paths.py` | Cubierto en parte (`CHANGELOG` v0.2.1 menciona 3 casos) |
| Recuperación por transición `on: failure` | `engine/orchestrator.py` | Cubierto en `test_orchestrator.py` |

### 7.3 Lo que no se puede probar en CI y hay que asumir

| Área | Motivo |
|---|---|
| `screen.capture_*` real | Requiere escritorio gráfico |
| `ui.hotkey`, `type_text`, `click` reales | Moverían teclado y ratón de la máquina de CI |
| `system.read_clipboard` con contenido | Requiere backend de portapapeles |
| `system.run_powershell` real | Requiere Windows con PowerShell |
| `capture_active_window` | Requiere una ventana en foco |
| Los flows 02, 07, 21–27 completos | Requieren Chromium instalado |
| Los flows 12 y 17 completos | Requieren el binario `tesseract` |
| El binario empaquetado | Requiere PyInstaller + Inno Setup |

Para las acciones de UI, el repositorio resolvió bien el problema: **`dry_run` permite
ejercitar la firma y el payload sin efectos**, y `tests/test_actions_basic.py` lo usa. Es
la mitigación correcta dentro de lo posible.

## 8. Criterios de aceptación observados

Deducidos de los gates, no declarados en un documento:

| Criterio | Umbral | Dónde se aplica |
|---|---|---|
| Todas las pruebas pasan | 150/150 | `ci.yml`, 6 combinaciones |
| Cobertura mínima | 54 % | `pyproject.toml` |
| Lint sin hallazgos | 0 | `ci.yml` |
| Manifests válidos | 0 errores | `ci.yml` |
| Smoke test completo | `ok: true` | `ci.yml`, job `smoke` |
| Sin secretos en el árbol ni en 50 commits | 0 hallazgos | `security.yml` |
| Toda acción de terceros con SHA pin | 100 % | `workflow-security.yml` |
| Enlaces Markdown válidos | 0 rotos | `markdown-docs.yml` (solo en PR) |

`docs/VALIDACION.md` del repositorio documenta esta batería desde la perspectiva del
autor de flows.

## 9. Casos límite relevantes: cubiertos y no cubiertos

### Cubiertos

| Caso | Prueba |
|---|---|
| Placeholder exacto que resuelve a `None` | `test_template.py` |
| Llaves que no son placeholders (JSON en un comando) | `test_template.py` |
| Los 13 operadores de condición | `test_conditions.py` |
| Cron con listas, rangos y pasos | `test_cron.py` |
| Lock ya tomado por otra corrida | `test_run_locks.py` |
| Liberación forzada de lock | `test_run_locks.py` |
| Path traversal por `..` y por prefijo hermano | `test_security_hardening.py` |
| `shell=True` rechazado | `test_security_hardening.py` |
| PowerShell fuera de la allowlist | `test_security_hardening.py` |
| Reintentos y recuperación por transición | `test_orchestrator.py` |
| Precedencia del contexto | `test_loader.py` |
| `parse_number` con formatos mixtos | `test_browser_extract.py` |
| BFS con cotas, errores y robots | `test_browser_extract.py` |
| Primera corrida del tracking (`first_run`) | `test_browser_extract.py` |
| Validación con y sin `jsonschema` | `test_manifest_schema.py` |

### No cubiertos

| Caso | Impacto |
|---|---|
| `allowed_actions: []` → permisivo | **Seguridad** |
| Salida del CLI en consola no-UTF-8 | **Defecto real y reproducible** |
| Archivo de tracking corrupto → línea base reiniciada en silencio | Datos |
| `max_runtime_seconds` con un paso que se cuelga | Nunca interrumpe |
| Dos corridas del mismo flow en paralelo desde el panel | Escritura concurrente del tracking |
| Corrida huérfana en `running` tras matar el proceso | Nunca se limpia |
| `set_flow_config` con fallo entre archivo y tabla | Desincronización |
| Día de la semana del cron (0 = lunes, no domingo) | Silencioso |
| `configs/` relativo al cwd frente a `data_dir()` | Empaquetado |

## 10. Propuesta priorizada de pruebas faltantes

Ninguna se implementó: este documento es informativo.

### Prioridad alta

| # | Prueba | Esfuerzo | Por qué |
|---|---|---|---|
| 1 | Salida del CLI con codificación forzada no-UTF-8 | Bajo | Detecta un defecto **real y actual** |
| 2 | `allowed_actions: []` produce política permisiva | Bajo | Documenta un caso límite de seguridad |
| 3 | `_pick_record`: no repite, reinicia al agotar, marca antes de llenar | Bajo | 90 líneas al 0 % en el flow más complejo |
| 4 | `find_text_in_image` con `matches` falso | Bajo | Lógica pura sin cubrir |
| 5 | `inspect_screen_target` en `ocr`, `vision` e `hybrid` con analizadores falsos | Medio | 100 líneas de decisión sin cubrir |
| 6 | Regla en `validate_project.py`: todo flow debe declarar `allowed_actions` | Bajo | Cierra el hueco de los 14 flows |

### Prioridad media

| # | Prueba | Esfuerzo |
|---|---|---|
| 7 | Añadir `plugins` al ámbito de `--cov` y cubrir la degradación de `OCRImageAnalyzer` | Bajo |
| 8 | `_is_preview` con `.disabled` y con `preview: true` | Bajo |
| 9 | `_smart_summary` para los 6 flows que cubre | Medio |
| 10 | Escapado HTML en las rutas de renderizado con contenido controlado | Medio |
| 11 | `apply_tracking` con archivo corrupto | Bajo |
| 12 | Semántica del día de la semana del cron, con caso explícito | Bajo |
| 13 | Estabilizar la cobertura: no arrancar el scheduler al importar en modo test | Medio |

### Prioridad baja

| # | Prueba | Esfuerzo |
|---|---|---|
| 14 | `engine/runner.py::build_parser` con los tres subcomandos | Bajo |
| 15 | `app/desktop.py::_wait_for_server` con timeout | Bajo |
| 16 | `metrics.prometheus_text` con base vacía | Bajo |
| 17 | `data_dir()` en las tres ramas de resolución | Bajo |

## 11. Lo que está bien y conviene proteger

- **Los cuatro gates están en verde y son rápidos** (≈17 s la suite completa). Un ciclo
  corto es lo que hace que la gente los ejecute.
- **La separación puro/impuro de `browser_extract.py`** permite probar la familia web sin
  navegador. Debería ser el patrón obligatorio de toda acción nueva.
- **`dry_run` en las acciones de UI** hace testeable lo que por naturaleza no lo es.
- **Los fixtures aíslan cambiando el directorio de trabajo**, no parcheando módulos. Las
  pruebas ejercitan el mismo camino de resolución de rutas que producción, y las tres de
  `data_dir()` usan la variable de entorno real `AUTOMA_DATA_ROOT`.
- **El validador de manifests comprueba la coherencia interna de la política**, no solo la
  sintaxis.
- **La matriz de CI cubre 6 combinaciones** de sistema operativo y versión de Python.
- **`--strict-markers`** impide que un marcador mal escrito pase inadvertido.

## 12. Lo que no se pudo verificar

| Aspecto | Motivo |
|---|---|
| Ejecución real de los 27 flows | Requiere escritorio Windows interactivo, Chromium y `tesseract` |
| Resultado de CodeQL, `zizmor`, `detect-secrets` y `pip-audit` en este commit | Requiere ver las ejecuciones en GitHub Actions |
| `markdownlint-cli2` sobre los `.md` | No se ejecutó: no forma parte de ningún gate de CI |
| Cobertura de `plugins/` | Fuera del ámbito de `--cov` |
| Comportamiento del binario empaquetado | No se compiló |
| Estabilidad de la suite bajo carga o en paralelo | Sin pruebas de estrés |

---

**Documentos relacionados:**
[04 · Mapa del código](04-code-map.md) ·
[06 · Explicación profunda](06-deep-code-explanation.md) ·
[13 · Despliegue y operación](13-deployment-and-operations.md) ·
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md) ·
[19 · Matriz de trazabilidad](19-traceability-matrix.md)
