# 11 · Seguridad

> Superficie de ataque, controles **presentes** y controles **ausentes**, medidos sobre el
> código del commit analizado. No se ejecutó ninguna prueba destructiva ni ningún ataque
> contra sistemas externos: todo lo que sigue es análisis estático más ejecución de la
> suite de pruebas del propio repositorio. Los hallazgos se describen **sin publicar
> cadenas explotables**.

---

## 1. Modelo de amenaza declarado por el proyecto

El repositorio no esconde su situación. `.github/workflows/security.yml` abre con un
comentario que es, de hecho, el modelo de amenaza:

> «este repo ejecuta acciones de teclado/mouse/captura de pantalla en el equipo del
> operador. Un commit malicioso fusionado a main se traduce directamente en RCE local
> cuando el operador hace pull.»

Esa frase ordena bien las prioridades: **la cadena de suministro es el vector principal**,
porque el producto, por diseño, ya tiene permiso para hacer casi cualquier cosa en la
máquina. Y el repositorio invierte en consecuencia (§2).

### Activos a proteger

| Activo | Dónde vive | Por qué importa |
|---|---|---|
| La sesión de Windows del operador | El equipo | El sistema puede teclear, hacer clic y lanzar procesos en ella |
| Capturas del escritorio | `output/screenshots/*.png` | Pueden contener cualquier cosa visible en pantalla |
| Contenido del portapapeles | `output/reports/clipboard_*.json`, SQLite | Puede contener credenciales recién copiadas |
| Histórico completo | `db/runs.db`, `state/`, `logs/` | Contiene todo lo anterior, sin cifrar |
| Tokens del panel | `secrets/secrets.json` o entorno | Sin cifrar |
| El propio catálogo de flows | `flows/*/manifest.json` | Un manifest es código ejecutable en la práctica |

## 2. Lo que está bien y hay que proteger

Un informe que solo enumerase problemas daría una imagen falsa. Estos controles están
implementados, verificados y algunos son mejores que la media del sector.

### 2.1 Hardening de la cadena de suministro — 12 capas

`SECURITY.md` documenta la política completa. Verificado en los workflows:

| # | Capa | Evidencia en el repositorio |
|---|---|---|
| 1 | SHA pin en toda acción de terceros | `actions/checkout@9c091bb…`, `astral-sh/setup-uv@fac544c…`, `github/codeql-action/*@8aad20d…` |
| 2 | `pin-check` con parser YAML real | `.github/workflows/workflow-security.yml`, job `pin-check` |
| 3 | Allowlist de excepciones vacía | Sin excepciones silenciosas |
| 4 | `persist-credentials: false` | En **todos** los `checkout` |
| 5 | Permisos mínimos por job | `permissions: contents: read`; `release.yml` arranca con `permissions: {}` |
| 6 | `concurrency: cancel-in-progress` | En `ci`, `security`, `workflow-security`, `markdown-docs`, `dependency-hygiene` |
| 7 | Sin `pull_request_target` | Verificado: no se usa como disparador en ningún workflow. La única aparición es un comentario de `workflow-security.yml` que lo lista como patrón prohibido |
| 8 | CodeQL `security-extended` | `security.yml`, con `security-and-quality` añadido |
| 9 | `actionlint` (con verificación de checksum) + `zizmor` | `workflow-security.yml` |
| 10 | `detect-secrets` sobre filesystem **y 50 commits de historial** | `security.yml`, con `fetch-depth: 0` |
| 11 | Detección de Trojan Source, ofuscación y URLs de exfiltración | `security.yml` |
| 12 | `pip-audit` | `security.yml` |

La capa 10 es la más infrecuente: escanear el árbol completo en cada uno de los últimos 50
commits detecta un secreto **aunque se haya borrado después**.

La capa 9 verifica el **checksum del propio `actionlint`** antes de ejecutarlo, cerrando el
caso de una herramienta de seguridad comprometida.

### 2.2 Sanitización de entrada en el panel

| Control | Implementación | Cierra |
|---|---|---|
| Slug de `folder` | `_FOLDER_RE = ^[A-Za-z0-9_\-]{1,64}$` aplicado en **las 7 rutas** que reciben un folder | Path traversal, NUL, no-ASCII |
| Path traversal en `/file` | Cuatro controles en cascada; ver §2.3 | CWE-22 |
| XSS reflejado desde `/file` | Allowlist negativa de 8 extensiones + `X-Content-Type-Options: nosniff` | CWE-79 |
| Escapado del HTML del panel | `html.escape` en las rutas de renderizado | CWE-79 |
| Comparación de tokens | `hmac.compare_digest` | CWE-208 (fuga por temporización) |
| Anti-CSRF sin token | `Host` loopback + `Origin`/`Referer` coherentes | CSRF, DNS rebinding |
| Command injection | `shell=True` **prohibido** en `ui.launch_process`; `shlex.split` + `shell=False` | CWE-78 |
| Inyección en PowerShell | Tokens prohibidos + allowlist de verbos | CWE-78 |
| Inyección SQL | **Todas** las consultas son parametrizadas con `?` | CWE-89 |
| Sanitización del tag en release | Regex `^v\d+\.\d+\.\d+([-.][\w]+)?$`, con `throw` si no coincide | Inyección en el pipeline |

Los comentarios del código citan explícitamente los CWE que cierran. Es una práctica poco
habitual y muy útil para auditar.

### 2.3 Los cuatro controles de `/file`, en orden

```text
1. Rechaza \x00 y cualquier carácter de control (ord(c) < 32)
2. Rechaza rutas absolutas
3. normpath(join(base, rel)) debe empezar por base + os.sep
4. Extensión no puede estar en {.html .htm .xhtml .xml .svg .js .mjs .css} → 415
```

El `+ os.sep` del punto 3 es el detalle fino: sin él, un directorio hermano llamado
`repo-evil` pasaría el `startswith` de `repo`. El comentario del código lo señala.

Cubierto por `tests/test_security_hardening.py`.

### 2.4 Higiene de secretos en el resultado

`notify.send` con `backend: "webhook"` resuelve el token y lo usa en la cabecera
`Authorization`, pero **el `record` que devuelve no lo incluye**. Es correcto y
deliberado: ese resultado va al contexto y de ahí a `runs.context_json`.

`engine.secrets.list_secret_names()` devuelve **nombres, nunca valores**.

### 2.5 Salidas de red opt-in

Con la configuración por defecto, **el sistema no genera tráfico de red**. Verificado
leyendo los 27 `context.example.json`: los nueve flows de navegador apuntan a HTML locales
del repositorio, y los dos con notificación usan `backend: "file"`.

## 3. Autenticación y autorización

### 3.1 No hay usuarios

**No existe autenticación de usuario, ni sesión, ni roles, ni permisos.** El README del
repositorio lo declara: «Multiusuario / RBAC — 🔴 No — un operador local».

El modelo de confianza es: *quien tiene la sesión de Windows tiene el sistema*. Es
coherente con un producto de escritorio, pero conviene enunciarlo porque cambia la lectura
de todo lo demás.

### 3.2 Protección de las mutaciones: dos modos

```python
# app/server.py::_authorize_mutation
panel_token = get_secret('AUTOMA_PANEL_TOKEN')
if panel_token:
    return (True, '') if self._check_token('AUTOMA_PANEL_TOKEN') else (False, 'token inválido …')

host_only = (self.headers.get('Host') or '').split(':', 1)[0].lower()
if host_only not in {'127.0.0.1', 'localhost', '[::1]', '::1'}:
    return False, 'Host no loopback: cliente remoto debe usar AUTOMA_PANEL_TOKEN'
origin = self.headers.get('Origin')
if origin and origin != expected_origin:  return False, ...
referer = self.headers.get('Referer')
if referer and not referer.startswith(expected_origin + '/') and referer != expected_origin:
    return False, ...
return True, ''
```

**Modo 1 · con token.** Toda mutación exige `X-Automa-Token` idéntico, comparado en tiempo
constante. Robusto.

**Modo 2 · sin token.** Tres comprobaciones que cierran el ataque real: una web maliciosa
que el operador visita y que intenta `fetch('http://127.0.0.1:8787/api/run/…')`. El
navegador **siempre** envía `Origin` en un `fetch` cross-site, así que se bloquea.

**Lo que el modo 2 no cubre, y hay que decirlo:** las comprobaciones de `Origin` y
`Referer` son condicionales (`if origin and …`). Un cliente que **no envíe** esas
cabeceras —`curl`, un script Python, cualquier proceso local— pasa el control con solo
poner `Host: 127.0.0.1`. Es una decisión calibrada contra el navegador, no contra un
proceso local hostil. El comentario del código es honesto sobre cuál es el caso que
cubre.

### 3.3 Las lecturas no están protegidas

**`do_GET` no llama a `_authorize_mutation` en ningún caso.** Verificado leyendo el
método completo. Consecuencia: incluso con `AUTOMA_PANEL_TOKEN` definido, siguen abiertos:

| Ruta | Qué expone |
|---|---|
| `GET /api/runs` | **`context_json` completo de cada corrida**: portapapeles, texto OCR, contenido web, inventarios |
| `GET /api/flows` | Catálogo con todos los pasos y parámetros |
| `GET /api/metrics`, `/metrics` | Volumen, duraciones, tasas de fallo |
| `GET /file?path=…` | Cualquier archivo bajo la raíz salvo 8 extensiones. **Los `.png` de las capturas SÍ se sirven** |
| `GET /run/<flow_id>/<run_id>` | Detalle completo en HTML |

**Este es el hallazgo de mayor impacto del documento.** Con el panel escuchando en
loopback y un solo usuario, el riesgo real es bajo. Deja de serlo si alguien cambia el
bind, monta un reverse proxy, o si hay más de una cuenta en el equipo.

### 3.4 El webhook

`POST /api/hook/<folder>` exige `AUTOMA_WEBHOOK_TOKEN` **siempre**, independientemente del
modo. Sin la variable definida responde `401`: está **deshabilitado por defecto**. Es la
decisión correcta para la única superficie pensada para llamadas no locales.

`REQUIERE VALIDACIÓN`: el webhook es **síncrono**. Una petición contra un flow largo
mantiene la conexión abierta y no hay límite de peticiones concurrentes. `INFERENCIA`: un
atacante con el token podría agotar recursos disparando el mismo flow muchas veces —el
`run_locks` no se aplica en esta ruta.

## 4. El sandbox: qué protege de verdad

### 4.1 Es declarativo, no de sistema operativo

`docs/SEGURIDAD.md` lo declara y el README lo marca como «🟡 Sandbox declarativo, no
proceso». El motor comprueba nombres de acción y prefijos de ruta **antes** de llamar a la
función. Una vez dentro, la acción corre con **todos los permisos del usuario**: no hay
contenedor, ni jaula, ni token restringido, ni AppContainer.

### 4.2 La mayoría del catálogo no lo usa

Conteo verificado leyendo los 27 manifests:

| Control | Flows que lo declaran | Flows sin él |
|---|---:|---:|
| `allowed_actions` | 13 (08–20) | **14** (01–07, 21–27) |
| `allowed_paths` | 7 (09, 12, 15–19) | **20** |
| `max_runtime_seconds` | 13 (08–20) | **14** |
| `required_secrets` | 0 | **27** |

Entre los 14 sin política están:

- **`07_browser_form_filler`** — lanza un navegador visible y escribe archivos.
- **Los siete flows web (21–27)** — salen a internet si se cambia la URL.
- **`01`, `03`, `04`, `05`, `06`** — leen el sistema de archivos y el estado del equipo.

`INFERENCIA`: el bloque 08–20 se añadió en la v0.2.0 con la política ya en mente, y la
familia web de la v0.3.0 no la incorporó. No hay ninguna regla en la CI que exija declarar
`allowed_actions`, así que el hueco puede crecer con cada caso nuevo.

### 4.3 La detección de rutas es por nombre de clave

```python
if any(token in key.lower() for token in ('path', 'destination', 'source', 'output', 'file')):
```

`assert_paths_allowed` considera candidata a ruta **cualquier cadena cuya clave contenga**
uno de esos cinco fragmentos. Consecuencias verificadas:

| Parámetro | ¿Se comprueba? |
|---|:--:|
| `output_path`, `save_data_path`, `seeds_path`, `state_path`, `track_state_path` | ✅ |
| `target` de `browser.extract_content` / `capture_page` | ❌ (puede ser una ruta local) |
| `command` de `ui.launch_process` | ❌ (contiene una ruta) |
| `path` de `filesystem.*` | ✅ |

En el catálogo actual no abre un agujero, porque ninguno de los siete flows con
`allowed_paths` usa esas acciones. Pero un autor de flows que confíe en `allowed_paths`
para acotar un flow de navegador tendría una protección que no protege.

### 4.4 `max_runtime_seconds` no es un timeout

Se comprueba **entre pasos**. Una acción que se cuelga dentro no se interrumpe. Un
`browser.crawl_site` contra un servidor lento, o un `http.check_urls` de 100 URLs con
timeout de 10 s, pueden superar largamente el límite sin que nada los corte. Es un control
de *arranque de paso*.

### 4.5 `required_secrets` mira solo el entorno

`SandboxPolicy.check_required_secrets` usa `os.environ.get`, no
`engine.secrets.get_secret`. Un secreto que viva solo en `secrets/secrets.json` **no
satisface** el requisito y el flow no arranca. Incoherencia entre dos mecanismos
presentados como equivalentes.

## 5. La superficie de mayor riesgo: `system.run_powershell`

Dos controles bien construidos y una puerta abierta por diseño.

**Los controles:**

```python
forbidden_chars = (";", "|", "&", "`", ">", "<", "$(", "$_")
for token in forbidden_chars:
    if token in trimmed:
        raise ValueError(...)
verbs = tuple(allowlist) if allowlist else _PS_DEFAULT_ALLOWLIST
head = trimmed.split()[0]
if head not in verbs:
    raise ValueError(...)
```

Se ejecuta con `shell=False` y argumentos como lista, `-NoProfile -NonInteractive`. Los 13
verbos por defecto son todos `Get-*` de solo lectura.

**La puerta abierta:** el parámetro `allowlist` es **sobrescribible desde el manifest**.
Un flow que declare `"allowlist": ["Remove-Item"]` obtiene exactamente eso, y los tokens
prohibidos no impiden un comando destructivo de una sola palabra con argumentos.

**Lectura correcta:** no es una vulnerabilidad explotable desde fuera —requiere escribir
un manifest, es decir, tener ya acceso de escritura al repositorio o al directorio de
flows—. Pero significa que **la seguridad de esta acción depende de la revisión de código
de los manifests, no de un control del motor**. Es exactamente el modelo de amenaza que
`security.yml` describe, y por eso el hardening del CI es la defensa correcta.

`NO IDENTIFICADO`: ninguna regla de `scripts/validate_project.py` comprueba los `params`
de un paso. Un manifest con una allowlist ampliada pasa la validación sin comentarios.

## 6. Almacenamiento de datos sensibles

| Dato | Almacén | Cifrado | Control de acceso |
|---|---|:--:|---|
| Tokens del panel | `secrets/secrets.json` | ❌ Texto plano | Permisos del sistema de archivos |
| Histórico completo | `db/runs.db` | ❌ | Permisos del sistema de archivos |
| Portapapeles capturado | SQLite + `output/reports/*.json` | ❌ | Igual |
| Capturas de escritorio | `output/screenshots/*.png` | ❌ | Igual, **más `GET /file` sin auth** |
| Texto OCR de ventanas | SQLite + reportes | ❌ | Igual |
| Salida de PowerShell | SQLite + reportes | ❌ | Igual |

**No hay cifrado en reposo en ningún punto.** El docstring de `engine/secrets.py` lo
declara sin adornos: «permisos del FS son el control de acceso». Para un producto local de
un solo usuario es defendible; en un equipo compartido o con respaldo automático a la nube,
no.

**No hay retención ni purga.** Verificado buscando `VACUUM`, `DELETE FROM runs`,
`retention` y `backup` en todo el código: no existe ninguna rutina. Un flow programado cada
15 minutos genera 96 corridas diarias, cada una con su fila en SQLite, su `.jsonl` y su
`.json` de estado, indefinidamente.

## 7. Dependencias

### Política declarada

`pyproject.toml` fija un piso explícito por paquete, con el motivo escrito:

> «Cotas de seguridad: piso explícito = primera versión sin CVE conocida al corte de la
> auditoría 2026-06-01 (ver SECURITY.md §"Auditoría 2026-06").»

Es una política razonada, no un rango arbitrario. Todas las dependencias llevan además
cota superior de *major* (`<13`, `<8`, `<3`…), lo que evita saltos de versión mayor
inesperados.

### Lo que no está pinneado

**No hay lockfile versionado.** El comentario de `requirements.txt` lo reconoce: «Para
reproducibilidad estricta usar `uv export` (lockfile en CI) — este archivo solo fija un
piso seguro». Verificado: no existe `uv.lock` ni `requirements.lock` en `git ls-files`.

`INFERENCIA`: dos instalaciones en fechas distintas pueden resolver versiones distintas
dentro del mismo rango. Un escáner de vulnerabilidades sobre las declaraciones no puede
pronunciarse con precisión sobre versiones no fijadas.

### `requirements.txt` incompleto

Declara seis paquetes y le faltan `pyperclip`, `PyGetWindow` y `pywebview`, que sí están en
`pyproject.toml`. `make install` usa ese archivo. No es un riesgo de seguridad, pero deja
el entorno incompleto.

### Análisis de vulnerabilidades

`pip-audit` corre en `security.yml` (soft en PR, hard en `main`). **No se ejecutó en este
análisis**: `REQUIERE VALIDACIÓN`. La CI del repositorio es la fuente para ese dato.

### Dependencias con superficie especial

| Paquete | Superficie |
|---|---|
| `pyautogui` | Control de teclado y ratón: si se compromete, controla la sesión |
| `playwright` (no declarado) | Descarga y ejecuta un Chromium completo |
| `pywebview` | Motor de navegador embebido (`edgechromium` en Windows) |
| `pytesseract` | Invoca un binario externo del sistema |

## 8. Riesgos de inyección: revisión punto por punto

| Vector | Estado | Evidencia |
|---|---|---|
| **SQL injection** | ✅ Cerrado | Todas las consultas usan `?`. Sin concatenación de strings en SQL |
| **Command injection (shell)** | ✅ Cerrado | `shell=True` prohibido con `ValueError`; `shlex.split` + `shell=False` |
| **PowerShell injection** | ⚠️ Mitigado | Tokens prohibidos + allowlist; pero la allowlist es sobrescribible desde el manifest |
| **Path traversal** | ✅ Cerrado en el panel | `_safe_folder` + los 4 controles de `/file` |
| **Path traversal en acciones** | ⚠️ Parcial | `allowed_paths` es opcional y solo lo declaran 7 flows |
| **XSS reflejado** | ✅ Mitigado | Allowlist de extensiones en `/file` + `nosniff` + `html.escape` |
| **XSS almacenado** | ⚠️ `REQUIERE VALIDACIÓN` | El panel renderiza contenido de las corridas; el escapado se aplica en las rutas revisadas, pero el HTML se construye por concatenación de f-strings en ~660 líneas. Una ruta sin `html.escape` sería difícil de detectar por lectura |
| **CSRF** | ✅ Mitigado | Modo 2 de `_authorize_mutation` |
| **DNS rebinding** | ✅ Mitigado | Comprobación de `Host` loopback |
| **SSRF** | ⚠️ Abierto por diseño | `http.fetch_url`, `check_urls` y `browser.*` aceptan cualquier URL, incluidas IPs internas. Es la funcionalidad del producto |
| **Deserialización insegura** | ✅ Sin riesgo | Solo `json.loads`. Sin `pickle`, `yaml.load` ni `eval` |
| **Carga de archivos** | ✅ Sin superficie | No hay endpoint de subida. `POST /api/form/submit` escribe JSON con nombre generado por el servidor |

Verificación de la penúltima fila:

```bash
grep -rn "pickle\|eval(\|exec(\|yaml.load\|os.system" --include="*.py" \
     engine/ actions/ app/ plugins/ decision/
```

Sin resultados en el código de producción.

## 9. Controles ausentes

Lista honesta de lo que **no** existe, verificado por búsqueda:

| Control ausente | Impacto | Prioridad sugerida |
|---|---|---|
| Autenticación en los GET | Todo el histórico es legible sin token | **Alta** |
| Cifrado en reposo de `secrets.json` | Tokens en texto plano | Media |
| Cifrado del histórico | Capturas, OCR y portapapeles sin cifrar | Media |
| Retención y purga de datos | Crecimiento sin límite | Media |
| `allowed_actions` obligatorio en la CI | 14 flows sin política | **Alta** |
| Validación de `params` contra la firma de la acción | Un manifest puede ampliar la allowlist de PowerShell sin aviso | **Alta** |
| Timeout real por acción | `max_runtime_seconds` no interrumpe | Media |
| Lock en las rutas del panel | El mismo flow puede correr dos veces en paralelo | Media |
| Lockfile de dependencias | Superficie no auditable con precisión | Media |
| Cabeceras de seguridad (`CSP`, `X-Frame-Options`, `Referrer-Policy`) | Solo se emite `nosniff`, y solo en `/file` | Baja |
| Límite de tasa en el webhook | Agotamiento de recursos con token válido | Baja |
| Registro de auditoría de accesos al panel | `log_message` está **silenciado** a propósito | Baja |
| `ruff format --check` en la CI | El hook existe en pre-commit pero la CI no lo aplica | Baja |
| Firma de código del `.exe` | `codesign_identity=None` en `automa.spec`; SmartScreen avisará | Baja |
| Rotación de tokens | Sin mecanismo | Baja |

### Sobre el registro silenciado

```python
def log_message(self, format: str, *args: Any) -> None:  # silencia logs ruidosos
    return
```

`AppHandler.log_message` está sobrescrito para no imprimir nada. Es razonable para no
llenar la consola de la ventana nativa, pero significa que **no queda ningún registro de
qué peticiones recibió el panel**. Las corridas sí quedan en SQLite; los accesos de
lectura, no.

## 10. Comprobación de secretos en el repositorio

Realizada durante este análisis sobre el árbol versionado:

```bash
grep -rnEi "(sk-|ghp_|gho_|AKIA|BEGIN [A-Z ]*PRIVATE KEY|password\s*=\s*[\"'][^\"']{6,}|api[_-]?key\s*[:=])" \
     $(git ls-files '*.py' '*.json' '*.toml' '*.md' '*.yml' '*.ps1' '*.iss')
```

**Sin coincidencias de credenciales reales.** Las seis coincidencias del patrón son
todas benignas y se listan aquí para que la comprobación sea reproducible:

| Archivo | Qué es |
|---|---|
| `actions/vision.py` (×2) | Nombres de parámetro: `vision_api_key`, `api_key=` |
| `plugins/analyzers/vision_model_analyzer.py` (×3) | Nombres de parámetro: `api_key` |
| `docs/OPERACION.md` línea 130 | Ejemplo de documentación: `set_secret("MY_API_KEY", "sk-...")`. El valor es literalmente `sk-...`, un marcador, no una clave |

`secrets/` contiene únicamente `.gitkeep`. `.gitignore` excluye `secrets/*.json`,
`db/*.db`, `logs/*.jsonl`, `state/*.json` y las salidas de `output/`.

La CI hace lo mismo con `detect-secrets==1.5.0` y además escanea los últimos 50 commits.

## 11. Protección de datos personales

`NO IDENTIFICADO`: no existe ninguna funcionalidad de privacidad. Sin anonimización, sin
redacción de campos, sin consentimiento, sin política de retención, sin exportación ni
borrado a petición.

Los datos que el sistema captura pueden ser personales o sensibles según lo que haya en
pantalla o en el portapapeles del operador. Como todo permanece en el equipo y no sale a
la red, la responsabilidad recae íntegramente en quien lo opera.

**Recomendaciones para el operador**, `INFERENCIA` a partir de la arquitectura:

1. No ejecute `15_clipboard_capture` con credenciales en el portapapeles.
2. Revise `output/screenshots/` antes de compartir el equipo o hacer respaldo.
3. Si el equipo tiene sincronización a la nube, excluya `output/`, `db/`, `logs/` y
   `state/`.
4. Defina `AUTOMA_PANEL_TOKEN` si hay más de una cuenta en el equipo — aunque recuerde que
   **no protege las lecturas**.
5. Purgue periódicamente a mano: no hay retención automática.

## 12. Recomendaciones priorizadas

Ninguna se aplicó: este documento es informativo, igual que
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md).

| # | Recomendación | Esfuerzo | Impacto |
|---|---|---|---|
| 1 | Exigir token también en `GET /api/runs`, `/api/flows`, `/api/metrics` y `/file` cuando `AUTOMA_PANEL_TOKEN` esté definido | Bajo (una llamada en `do_GET`) | **Alto** |
| 2 | Añadir a `validate_project.py` una regla que exija `allowed_actions` en todo flow nuevo | Bajo | **Alto** |
| 3 | Validar los `params` de cada paso contra la firma de la acción (`inspect.signature`) | Medio | **Alto** |
| 4 | Bloquear el override de `allowlist` en `system.run_powershell`, o exigir una lista blanca de allowlists | Bajo | Alto |
| 5 | Comprobar también `value` (no solo la clave) en `assert_paths_allowed` para detectar rutas en `target` y `command` | Medio | Medio |
| 6 | Generar y versionar un lockfile (`uv export`) | Bajo | Medio |
| 7 | Timeout real por acción con `concurrent.futures` o señal | Medio | Medio |
| 8 | Rutina de retención configurable | Medio | Medio |
| 9 | Aplicar `run_locks` también en las rutas del panel y del webhook | Bajo | Medio |
| 10 | Cifrar `secrets.json` con DPAPI en Windows | Medio | Medio |
| 11 | Auditar el escapado HTML de las ~660 líneas de renderizado del panel | Medio | Medio |
| 12 | Añadir `ruff format --check` a la CI | Bajo | Bajo |

## 13. Lo que este análisis NO comprobó

| Aspecto | Motivo |
|---|---|
| Vulnerabilidades conocidas de las dependencias | No se ejecutó `pip-audit` ni consulta a bases de CVE. La CI sí lo hace |
| Pruebas de penetración del panel | Fuera del alcance: sin pruebas destructivas |
| XSS almacenado real | Requeriría inyectar contenido en una corrida y observar el render |
| Comportamiento del binario empaquetado | No se compiló |
| Efectividad de `zizmor`, `actionlint` y CodeQL en este commit | Requiere ver las ejecuciones en GitHub Actions |
| Permisos efectivos de los archivos en Windows | No se auditaron las ACL |
| Resistencia a carga o denegación de servicio | Sin pruebas de estrés |

---

**Documentos relacionados:**
[03 · Arquitectura](03-architecture.md) ·
[07 · Base de datos](07-database.md) ·
[08 · Flujo de datos](08-data-flow.md) ·
[10 · Configuración](10-configuration.md) ·
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md)
