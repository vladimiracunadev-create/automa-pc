# Documentación del sistema — Automa

> Portada e índice navegable de la documentación técnica, funcional, arquitectónica
> y operativa del repositorio `automa-pc`.

---

## 1. Identificación

| Campo | Valor |
|---|---|
| **Sistema** | Automa |
| **Nombre del paquete** | `automa-pc` (`pyproject.toml`, `[project].name`) |
| **Versión analizada** | `0.3.0` (`pyproject.toml`, `[project].version`) |
| **Commit analizado** | `ff246abb4d6f5235afb4dcc74032a50645db954c` (rama `main`) |
| **Fecha del análisis** | 2026-08-27 |
| **Lenguaje principal** | Python 3.10+ (CI corre 3.10, 3.11 y 3.12) |
| **Plataforma objetivo** | Windows 10 / 11. La CI también corre `ubuntu-latest` |
| **Licencia** | MIT (`LICENSE`) |
| **Repositorio** | <https://github.com/vladimiracunadev-create/automa-pc> |
| **Sitio del proyecto** | <https://vladimiracunadev-create.github.io/automa-pc/> |

**Tamaño medido en el commit analizado** (`git ls-files`, `wc -l`):

| Métrica | Valor |
|---|---:|
| Archivos versionados | 210 |
| Archivos `.py` de producción (sin `tests/`) | 47 |
| Archivos `.py` de pruebas | 17 |
| Líneas de Python de producción | 6 126 |
| Líneas de Python de pruebas | 1 525 |
| Flows declarativos (`flows/*/manifest.json`) | 27 |
| Acciones registradas (`engine/action_registry.py`) | 36 |
| Pruebas que pasan (`pytest`) | 150 |

## 2. Descripción breve

Automa es un **orquestador local de automatización (RPA) para el escritorio Windows**,
escrito en Python puro. Cada caso de uso se declara en un `manifest.json` con pasos,
condiciones y transiciones; un motor determinista los ejecuta, aplica una política de
sandbox por flow y deja trazabilidad completa en SQLite, JSONL y archivos de salida.

No hay ningún modelo de lenguaje en el camino de ejecución. **El "agente" es el manifest
declarativo, no un LLM.** El repositorio contiene un adaptador opcional de visión
multimodal (`plugins/analyzers/vision_model_analyzer.py`) que ningún flow del catálogo
usa; el detalle y la evidencia de esa afirmación están en
[09 · APIs e integraciones](09-apis-and-integrations.md#5-adaptador-opcional-de-visión-multimodal-no-usado-por-ningún-flow).

## 3. Propósito de esta documentación

Permitir que:

1. Un desarrollador nuevo se incorpore al proyecto sin depender de conocimiento tácito.
2. Una persona no técnica entienda qué hace el sistema y para qué sirve.
3. Un desarrollador experimentado consulte detalles de acciones, motor y persistencia.
4. Un auditor revise arquitectura, base de datos, dependencias, seguridad y deuda técnica.
5. Otro agente de IA use estos documentos como contexto verificable del repositorio.

## 4. Público destinatario por documento

| Documento | Usuario final | Dev nuevo | Dev senior | Auditor | Dirección |
|---|:--:|:--:|:--:|:--:|:--:|
| 01 · Descripción general | ✅ | ✅ | ○ | ○ | ✅ |
| 02 · Instalación y ejecución | ✅ | ✅ | ✅ | ○ | ○ |
| 03 · Arquitectura | ○ | ✅ | ✅ | ✅ | ○ |
| 04 · Mapa del código | ○ | ✅ | ✅ | ✅ | ○ |
| 05 · Referencia técnica | ○ | ○ | ✅ | ✅ | ○ |
| 06 · Explicación profunda | ○ | ✅ | ✅ | ✅ | ○ |
| 07 · Base de datos | ○ | ✅ | ✅ | ✅ | ○ |
| 08 · Flujo de datos | ○ | ✅ | ✅ | ✅ | ○ |
| 09 · APIs e integraciones | ○ | ✅ | ✅ | ✅ | ○ |
| 10 · Configuración | ✅ | ✅ | ✅ | ✅ | ○ |
| 11 · Seguridad | ○ | ○ | ✅ | ✅ | ✅ |
| 12 · Pruebas y calidad | ○ | ✅ | ✅ | ✅ | ○ |
| 13 · Despliegue y operación | ○ | ○ | ✅ | ✅ | ○ |
| 14 · Solución de problemas | ✅ | ✅ | ✅ | ○ | ○ |
| 15 · Riesgos y deuda técnica | ○ | ○ | ✅ | ✅ | ✅ |
| 16 · Glosario | ✅ | ✅ | ○ | ✅ | ✅ |
| 17 · Resumen ejecutivo | ✅ | ○ | ○ | ✅ | ✅ |
| 18 · Guía para nuevo desarrollador | ○ | ✅ | ○ | ○ | ○ |
| 19 · Matriz de trazabilidad | ○ | ✅ | ✅ | ✅ | ○ |

✅ destinatario principal · ○ lectura opcional

## 5. Tabla de contenidos

| # | Documento | Contenido | Estado |
|---|---|---|---|
| — | [README](README.md) | Portada, índice y convenciones | ✅ Completo |
| 01 | [Descripción general del sistema](01-system-overview.md) | Qué es, qué resuelve, casos de uso, explicación no técnica | ✅ Completo |
| 02 | [Instalación y ejecución](02-installation-and-execution.md) | Requisitos, instalación, ejecución, pruebas, errores frecuentes | ✅ Completo |
| 03 | [Arquitectura](03-architecture.md) | Estilo, capas, patrones, diagramas Mermaid | ✅ Completo |
| 04 | [Mapa completo del código](04-code-map.md) | Inventario jerárquico de directorios, módulos y funciones | ✅ Completo |
| 05 | [Referencia técnica](05-technical-reference.md) | Catálogo de acciones, funciones, endpoints, comandos y errores | ✅ Completo |
| 06 | [Explicación profunda del código](06-deep-code-explanation.md) | Flujo interno módulo a módulo, decisiones y casos límite | ✅ Completo |
| 07 | [Base de datos](07-database.md) | Esquema SQLite, diccionario de datos, consultas, ERD | ✅ Completo |
| 08 | [Flujo de datos](08-data-flow.md) | Origen, validación, transformación, almacenamiento, consumo | ✅ Completo |
| 09 | [APIs e integraciones](09-apis-and-integrations.md) | Endpoints HTTP, webhooks, Playwright, OCR, IA opcional | ✅ Completo |
| 10 | [Configuración](10-configuration.md) | `configs/`, `context.example.json`, variables de entorno | ✅ Completo |
| 11 | [Seguridad](11-security.md) | Sandbox, auth del panel, superficie de ataque, controles ausentes | ✅ Completo |
| 12 | [Pruebas y calidad](12-testing-and-quality.md) | 150 tests, cobertura medida, huecos priorizados | ✅ Completo |
| 13 | [Despliegue y operación](13-deployment-and-operations.md) | CI/CD, PyInstaller, Inno Setup, logs, respaldo y rollback | ✅ Completo |
| 14 | [Solución de problemas](14-troubleshooting.md) | Síntoma → causa → diagnóstico → solución → riesgo | ✅ Completo |
| 15 | [Riesgos y deuda técnica](15-risks-and-technical-debt.md) | Hallazgos clasificados por severidad e impacto | ✅ Completo |
| 16 | [Glosario](16-glossary.md) | Términos técnicos y de dominio en lenguaje claro | ✅ Completo |
| 17 | [Resumen ejecutivo](17-executive-summary.md) | Presentación del sistema para decisión | ✅ Completo |
| 18 | [Guía para un nuevo desarrollador](18-new-developer-guide.md) | Itinerario de incorporación y primeras tareas | ✅ Completo |
| 19 | [Matriz de trazabilidad](19-traceability-matrix.md) | Funcionalidad → módulo → función → persistencia → prueba | ✅ Completo |

**Recursos adicionales**

- [`assets/`](assets/) — recursos gráficos de esta documentación. Actualmente vacío:
  los diagramas se declaran como código Mermaid dentro de los propios `.md` y se
  rasterizan al generar el PDF. Las capturas del producto viven en
  [`docs/manual_screenshots/`](../manual_screenshots/) y la portada en
  [`docs/assets/`](../assets/).
- [`pdf/`](pdf/) — versión PDF de cada documento, más un consolidado, generados por script.

## 6. Cómo generar los PDF

Los Markdown de esta carpeta son la **fuente única**. Los PDF se generan a partir de ellos:

```bash
python scripts/build_docs_pdf.py            # todos los documentos + consolidado
python scripts/build_docs_pdf.py --only 03  # solo el documento 03 (iteración rápida)
python scripts/build_docs_pdf.py --check    # comprueba dependencias sin generar
```

Requisitos, opciones y limitaciones conocidas en
[13 · Despliegue y operación → Generación de la documentación en PDF](13-deployment-and-operations.md#8-generación-de-la-documentación-en-pdf).

## 7. Documentación añadida en el propio código

Este análisis revisó los 47 archivos `.py` de producción. **El repositorio ya tiene una
densidad alta de comentarios de calidad**: los módulos con decisiones no obvias
(`engine/paths.py`, `engine/sandbox.py`, `engine/secrets.py`, `engine/cron.py`,
`engine/template.py`, `engine/introspection.py`, `actions/browser_extract.py`,
`actions/notify.py`, `actions/system.py`, `app/server.py`, `installer/automa_entry.py`)
llevan docstring de módulo explicando **por qué** existe el código, no qué hace la línea
siguiente. Los bloques de seguridad de `app/server.py` documentan incluso el modelo de
amenaza que cierran.

Siguiendo el criterio de no degradar un código bien comentado con ruido, **no se
modificó ningún archivo de código fuente en este análisis**. Los archivos sin docstring
de módulo (`engine/models.py`, `engine/loader.py`, `engine/conditions.py`,
`actions/filesystem.py`, `actions/rules.py`, `actions/ui.py`, `actions/screen.py`,
`actions/http_actions.py`) son módulos cortos, con nombres explícitos y tipado completo;
su explicación se aporta en [06 · Explicación profunda](06-deep-code-explanation.md) en
lugar de duplicarse en el código. La recomendación de añadirles docstring queda
registrada como deuda de baja severidad en
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md).

El único archivo Python nuevo que introduce este trabajo es
[`scripts/build_docs_pdf.py`](../../scripts/build_docs_pdf.py), la herramienta que genera
los PDF. No participa en el runtime del producto.

## 8. Relación con la documentación previa del repositorio

Este conjunto **no reemplaza** la documentación que ya existía en `docs/`; la complementa
y la referencia. La documentación previa está orientada a producto, operación y contrato
de extensión; esta está orientada a comprensión del sistema y auditoría.

| Ya existía | Este conjunto aporta |
|---|---|
| [`docs/ARQUITECTURA.md`](../ARQUITECTURA.md) — diseño técnico resumido | Arquitectura con diagramas, capas y flujos completos (03) |
| [`docs/CREAR_FLUJOS.md`](../CREAR_FLUJOS.md) — contrato para escribir un flow | Explicación del motor que consume ese contrato, línea a línea (06) |
| [`docs/FAMILIAS_Y_CASOS.md`](../FAMILIAS_Y_CASOS.md) — catálogo | Inventario verificado de los 27 flows con su política real (04, 19) |
| [`docs/SEGURIDAD.md`](../SEGURIDAD.md) — sandbox y modelo de confianza | Controles presentes **y ausentes**, medidos flow por flow (11) |
| [`docs/VALIDACION.md`](../VALIDACION.md) — schema, pytest, CI | Cobertura medida y huecos priorizados (12) |
| [`docs/OPERACION.md`](../OPERACION.md) y [`RUNBOOK.md`](../../RUNBOOK.md) — día a día | Despliegue, CI/CD y procedimientos de recuperación (13) |
| [`docs/TROUBLESHOOTING.md`](../TROUBLESHOOTING.md) — fallas comunes | Guía síntoma → causa → diagnóstico → solución → **riesgo** (14) |
| [`docs/ROADMAP.md`](../ROADMAP.md) — hoja de ruta | Estado verificado del código en el commit analizado (01, 17) |

## 9. Convenciones utilizadas

### 9.1 Marcadores de confianza

Toda afirmación de estos documentos está anclada a evidencia del repositorio. Cuando algo
no se pudo comprobar, se marca explícitamente:

| Marcador | Significado |
|---|---|
| *(sin marcador)* | **Hecho verificado**: leído directamente en el código, la configuración o el historial del repositorio. Se cita archivo y, cuando aplica, símbolo o comando ejecutado. |
| `INFERENCIA` | Conclusión razonada a partir del código, no una afirmación literal del repositorio. |
| `REQUIERE VALIDACIÓN` | Depende de ejecución en Windows real, de servicios externos o de una decisión humana pendiente. |
| `NO DOCUMENTADO EN EL REPOSITORIO` | El repositorio no contiene la información. |
| `NO IDENTIFICADO` | Se buscó y no se encontró evidencia en ningún sentido. |

### 9.2 Referencias a código

- Los archivos se citan con ruta relativa a la raíz del repositorio: `engine/orchestrator.py`.
- Los símbolos se citan con su nombre real en el código, sin traducir: `Orchestrator.run`,
  `SandboxPolicy.assert_paths_allowed`, `_BUILT_IN_ACTIONS`.
- Los nombres de columnas SQL, claves JSON de manifest y variables de entorno se citan en
  su forma original (`flow_folder`, `allowed_paths`, `AUTOMA_PANEL_TOKEN`).
- Las líneas citadas corresponden al commit analizado y pueden desplazarse en commits
  posteriores; el nombre del símbolo es la referencia estable.

### 9.3 Idioma

Documentación en español, igual que el resto del repositorio y que los comentarios del
código. Los identificadores de código, los nombres de acción (`browser.extract_content`) y
los nombres de columnas SQL se mantienen en su forma original para garantizar
trazabilidad textual.

### 9.4 Datos sensibles

Ningún documento contiene credenciales, tokens ni claves reales. Los valores de ejemplo
son ficticios y están marcados como tales; las URL de ejemplo usan dominios reservados
(`example.com`). Los hallazgos de seguridad se describen sin publicar cadenas explotables.

## 10. Elementos pendientes de validar

Lista viva de lo que esta documentación **no** pudo verificar en este análisis. El detalle
y la recomendación de cada punto están en
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md).

| # | Pendiente | Motivo | Documento |
|---|---|---|---|
| 1 | Comportamiento real de las acciones de UI (`ui.hotkey`, `ui.type_text`, `ui.click`) y de captura (`screen.*`) | Requieren una sesión Windows interactiva con escritorio gráfico. No se ejecutó ningún flow que mueva teclado o ratón durante el análisis, por ser una acción con efecto sobre la máquina del usuario | [05](05-technical-reference.md), [06](06-deep-code-explanation.md) |
| 2 | Flows 02, 07 y 21–27 de punta a punta | Requieren `playwright` y el navegador Chromium descargado (`python -m playwright install chromium`), que no forman parte de las dependencias declaradas en `pyproject.toml` | [02](02-installation-and-execution.md), [12](12-testing-and-quality.md) |
| 3 | Flows 12 y 17 (OCR) | Requieren el binario externo `tesseract`, que el repositorio no instala. `OCRImageAnalyzer` degrada con `status: "unavailable"` en vez de fallar | [09](09-apis-and-integrations.md), [14](14-troubleshooting.md) |
| 4 | Funcionamiento del binario empaquetado (`Automa.exe`) y del instalador | Requiere PyInstaller + Inno Setup en Windows. No se compiló en este análisis. Hay un hallazgo abierto sobre `installer/automa.spec` (ver #5) | [13](13-deployment-and-operations.md), [15](15-risks-and-technical-debt.md) |
| 5 | Si los flows 21–27 funcionan dentro del binario empaquetado | `installer/automa.spec` NO lista `actions.browser_extract` en `hiddenimports`, y el registro lo carga por `import_module` dinámico. `INFERENCIA`: PyInstaller no lo detectaría y esos siete flows fallarían con `ModuleNotFoundError` en el `.exe`. Sin build no se puede confirmar | [13](13-deployment-and-operations.md), [15](15-risks-and-technical-debt.md) |
| 6 | Vulnerabilidades conocidas de las dependencias | No se ejecutó `pip-audit` ni consulta a bases de CVE en este análisis. La CI sí lo hace (`security.yml`) | [11](11-security.md) |
| 7 | Publicación efectiva del release y del sitio GitHub Pages | Depende de tags y de la configuración del repositorio en GitHub, fuera del árbol de trabajo | [13](13-deployment-and-operations.md) |

---

*Documentación generada por análisis estático y ejecución de las pruebas del repositorio
en el commit `ff246ab`. Si el código cambia, actualizar primero los Markdown de esta
carpeta y regenerar los PDF con `python scripts/build_docs_pdf.py`.*
