# 09 · APIs e integraciones

> Endpoints internos, contratos de datos, integraciones salientes, dependencias de
> plataforma y el adaptador de visión multimodal que existe pero ningún flow usa.
> Todos los ejemplos usan valores ficticios y dominios reservados.

---

## 1. La API HTTP del panel

| Aspecto | Valor |
|---|---|
| Servidor | `ThreadingHTTPServer` de la biblioteca estándar |
| Bind por defecto | `127.0.0.1:8787` (`app/server.py::run_server`) |
| Protocolo | HTTP/1.1 sin TLS |
| Formatos | `application/json; charset=utf-8`, `text/html; charset=utf-8`, `text/plain; version=0.0.4` |
| Versionado | **Ninguno.** No hay `/v1/`, ni cabecera de versión |
| CORS | **No se emite ninguna cabecera CORS.** El navegador bloquea cualquier lectura cross-origin |
| Documentación de API | `NO DOCUMENTADO EN EL REPOSITORIO`: no hay OpenAPI ni Swagger |

**Sin TLS y sin CORS**, la superficie efectiva es la máquina local. La única cabecera de
seguridad que se emite es `X-Content-Type-Options: nosniff`, y solo en `/file`.

### 1.1 Endpoints GET

| Método | Ruta | Devuelve | Auth |
|---|---|---|:--:|
| GET | `/` | HTML del panel de 3 pestañas | ❌ |
| GET | `/healthz` | `{"status": "ok"}` | ❌ |
| GET | `/metrics` | Texto Prometheus | ❌ |
| GET | `/api/metrics` | `{"overview": {…}, "by_flow": [{…}]}` | ❌ |
| GET | `/metrics/dashboard` | HTML del dashboard | ❌ |
| GET | `/api/flows` | Array de flows | ❌ |
| GET | `/api/runs?flow_id=&limit=50` | Array de corridas | ❌ |
| GET | `/api/runs/<run_id>/status` | Estado paso a paso | ❌ |
| GET | `/flow/<folder>` | HTML de la ficha | ❌ |
| GET | `/flow/<folder>/config` | HTML del editor de contexto | ❌ |
| GET | `/flow/<folder>/history` | HTML del histórico del flow | ❌ |
| GET | `/run/<flow_id>/<run_id>` | HTML del detalle | ❌ |
| GET | `/file?path=<relativa>` | Bytes del archivo | ❌ |

**Ninguna lectura exige autenticación**, ni siquiera con `AUTOMA_PANEL_TOKEN` definido:
`do_GET` no llama a `_authorize_mutation`. Ver [11 · Seguridad](11-security.md).

### 1.2 Endpoints POST

| Método | Ruta | Cuerpo | Devuelve | Auth |
|---|---|---|---|---|
| POST | `/api/run/<folder>` | `{"context_overrides": {…}}` opcional | `{ok, run_id, status, flow_id}` | `_authorize_mutation` |
| POST | `/api/hook/<folder>` | Ignorado | `{ok, run_id, status, flow_id}` | `AUTOMA_WEBHOOK_TOKEN` |
| POST | `/api/form/submit` | JSON libre | `{ok, saved_path}` | `_authorize_mutation` |
| POST | `/run?flow=<folder>` | Formulario | `303` → `/run/<flow_id>/<run_id>` | `_authorize_mutation` |
| POST | `/flow/<folder>/config` | `config_json=<JSON>` | HTML | `_authorize_mutation` |
| POST | `/flow/<folder>/schedule` | `enabled`, `interval_seconds`, `cron_expression` | `303` → `/#schedule` | `_authorize_mutation` |

### 1.3 Códigos de estado

| Código | Cuándo |
|---|---|
| `200` | Éxito |
| `303` | Redirección tras un POST de formulario |
| `400` | `folder` que no pasa `_safe_folder`, JSON malformado, cuerpo vacío en `/api/form/submit`, error al guardar config o schedule |
| `401` | No autorizado: token inválido, `Host` no loopback, `Origin`/`Referer` incoherentes, o `AUTOMA_WEBHOOK_TOKEN` sin definir |
| `404` | Flow inexistente, corrida inexistente, ruta no servida, archivo no encontrado en `/file` |
| `409` | Flow marcado `preview: true` o con archivo `.disabled` |
| `415` | `/file` con extensión de la lista bloqueada |
| `500` | `FlowExecutionError` en la ejecución síncrona (`/run`, `/api/hook`) o al instanciar el orquestador |

## 2. Ejemplos de uso

### Disparar un flow y hacer polling

```bash
# 1. Disparo asíncrono: devuelve de inmediato
curl -s -X POST http://127.0.0.1:8787/api/run/05_system_healthcheck \
     -H 'Content-Type: application/json' \
     -d '{}'
```

```json
{
  "ok": true,
  "run_id": "20260827T143052123456Z",
  "status": "running",
  "flow_id": "system_healthcheck"
}
```

```bash
# 2. Polling del estado paso a paso
curl -s http://127.0.0.1:8787/api/runs/20260827T143052123456Z/status
```

```json
{
  "ok": true,
  "run_id": "20260827T143052123456Z",
  "flow_id": "system_healthcheck",
  "flow_folder": "05_system_healthcheck",
  "flow_name": "Healthcheck del sistema",
  "status": "completed",
  "steps": [
    {"step_id": "take_snapshot", "action": "system.snapshot_system", "status": "success", "attempt": 1, "duration_seconds": 0.2143},
    {"step_id": "evaluate_snapshot",  "action": "rules.evaluate",         "status": "success", "attempt": 1, "duration_seconds": 0.0002},
    {"step_id": "write_snapshot",  "action": "filesystem.write_json",  "status": "success", "attempt": 1, "duration_seconds": 0.0011}
  ],
  "duration_seconds": 0.4312,
  "started_at": "2026-08-27T14:30:52.200000+00:00",
  "finished_at": "2026-08-27T14:30:52.631200+00:00",
  "error": null
}
```

> Las 11 claves de primer nivel son exactamente las que devuelve
> `app/server.py::_run_status_payload`, que combina la fila de `runs`, los registros de
> `steps` y la lista de pasos del manifest. Un paso sin registro aparece como `running` si
> es el primero pendiente de una corrida viva, `pending` para los siguientes de esa misma
> corrida, y `not_taken` si la corrida ya terminó —porque entonces significa «rama no
> tomada», no «pendiente».

### Disparar con override de contexto

```bash
curl -s -X POST http://127.0.0.1:8787/api/run/03_folder_inventory \
     -H 'Content-Type: application/json' \
     -d '{"context_overrides": {"path_override": "C:/Users/ejemplo/Documentos"}}'
```

El override reemplaza claves de **primer nivel**; no hay fusión profunda.

### Webhook entrante

```bash
# Requiere AUTOMA_WEBHOOK_TOKEN definido en el entorno del panel
curl -s -X POST http://127.0.0.1:8787/api/hook/05_system_healthcheck \
     -H 'X-Automa-Token: TOKEN-DE-EJEMPLO-NO-REAL'
```

**Diferencia crítica con `/api/run`:** el webhook es **síncrono**. Ejecuta el flow
completo y responde al terminar. Una petición contra un flow largo mantiene la conexión
abierta hasta el final, y un timeout del cliente no cancela la corrida.

```json
{"ok": true, "run_id": "20260827T143100987654Z", "status": "completed", "flow_id": "system_healthcheck"}
```

Sin token configurado:

```json
{"ok": false, "error": "token inválido o AUTOMA_WEBHOOK_TOKEN no configurado"}
```

### Panel con token

```bash
export AUTOMA_PANEL_TOKEN='TOKEN-DE-EJEMPLO-NO-REAL'   # en el proceso del panel
curl -s -X POST http://127.0.0.1:8787/api/run/05_system_healthcheck \
     -H 'X-Automa-Token: TOKEN-DE-EJEMPLO-NO-REAL' -d '{}'
```

La comparación se hace con `hmac.compare_digest`, en tiempo constante (cierra CWE-208).

### Programar un flow

```bash
# Cada 15 minutos, en punto (recordar: los campos van en UTC)
curl -s -X POST 'http://127.0.0.1:8787/flow/05_system_healthcheck/schedule' \
     -d 'enabled=on' --data-urlencode 'cron_expression=*/15 * * * *'

# O por intervalo simple, en segundos
curl -s -X POST 'http://127.0.0.1:8787/flow/05_system_healthcheck/schedule' \
     -d 'enabled=on' -d 'interval_seconds=900'
```

`set_schedule` prioriza `cron_expression` si viene; el panel envía `interval_seconds` solo
cuando no hay cron.

### Servir un archivo de salida

```bash
curl -s -o captura.png 'http://127.0.0.1:8787/file?path=output/screenshots/desktop_clean_20260827_143052.png'
```

`/file` acepta **solo rutas relativas** a la raíz del proyecto y rechaza `.html`, `.htm`,
`.xhtml`, `.xml`, `.svg`, `.js`, `.mjs` y `.css` con `415`. Los `.png`, `.json`, `.csv`,
`.md`, `.log` y `.jsonl` **sí se sirven**.

## 3. Contrato de datos: `/metrics` en formato Prometheus

`engine/metrics.py::prometheus_text` emite un puñado de series. Ejemplo real de la forma:

```text
# HELP flujo_runs_total Total de corridas por estado.
# TYPE flujo_runs_total counter
flujo_runs_total{status="completed"} 148
flujo_runs_total{status="failed"} 3
# HELP flujo_run_duration_seconds_avg Duración promedio histórica.
# TYPE flujo_run_duration_seconds_avg gauge
flujo_run_duration_seconds_avg 0.8123456
flujo_runs_window_completed 96
flujo_runs_window_failed 2
```

**Observaciones sobre el contrato:**

- El prefijo es `flujo_`, no `automa_`. Es un resto del nombre anterior del proyecto y
  quedaría feo cambiarlo sin romper dashboards existentes. Referencia histórica, no error.
- `flujo_runs_window_completed` y `flujo_runs_window_failed` se emiten **sin `# HELP` ni
  `# TYPE`**. Prometheus lo tolera, pero es una inconsistencia del formato.
- La ventana es de 200 corridas, fija (`overview(window_runs=200)`).
- El endpoint **no exige autenticación**. Un scraper en la red local podría leerlo si el
  panel se expusiera fuera de loopback.

`/api/metrics` devuelve el mismo material en JSON, con más detalle: `slowest_actions`,
`retries_top_actions`, `failed_top_actions` y el desglose `by_flow`.

## 4. Integraciones salientes

### 4.1 Chromium vía Playwright

| Aspecto | Detalle |
|---|---|
| Acciones | `browser.capture_page`, `browser.fill_form`, `browser.extract_content`, `browser.crawl_site` |
| Instalación | `pip install playwright && python -m playwright install chromium` |
| **No declarada** | `playwright` no está en `pyproject.toml` ni en `requirements.txt` |
| Modo | Headless salvo `browser.fill_form`, que por defecto abre ventana visible |
| User-Agent | `automa-pc` en `extract_content` y `crawl_site`; el de Chromium por defecto en los otros dos |
| Timeout | `timeout_seconds=30.0` por defecto, aplicado con `page.set_default_timeout` |
| Degradación | `RuntimeError` con el comando de instalación exacto |

`_to_url` acepta `http://`, `https://`, `file://` o una ruta local a un `.html`. Una ruta
inexistente que no sea URL levanta `FileNotFoundError`.

### 4.2 `robots.txt`

`actions/browser_extract.py::RobotsCache` consulta `<esquema>://<host>/robots.txt` una vez
por host, con `User-Agent: automa-pc` y timeout de 5 s.

| Situación | Comportamiento |
|---|---|
| `robots.txt` legible | Se aplica `RobotFileParser.can_fetch` |
| Estado ≥ 400 | Se permite; `checked=True` |
| Error de red | **Se permite**; `checked=False`, reportado en `robots_checked_hosts` |
| Esquema no http(s) (por ejemplo `file://`) | Se permite sin consultar |

El fallo es permisivo pero **declarado**: el docstring lo dice y el reporte del flow 22 lo
expone. Es la decisión honesta.

### 4.3 Verificación de enlaces

`http.check_urls` hace `HEAD` con redirects y, ante `405` o `501`, reintenta con `GET` en
modo `stream` cerrando la respuesta sin descargar el cuerpo. `file://` se verifica por
existencia en disco. `mailto:` y `tel:` se marcan `skipped`.

**Sin control de reintentos ni de concurrencia:** las peticiones son secuenciales, con
`delay_seconds` opcional entre ellas. Un `max_urls` de 100 contra un servidor lento con
timeout de 10 s puede tardar hasta 1 000 segundos. `INFERENCIA`.

### 4.4 Notificaciones salientes

`actions/notify.py::send_notification` con `backend: "webhook"`:

```json
POST <target>
Content-Type: application/json
Authorization: Bearer <token resuelto>     ← solo si se pasó token

{
  "text": "⚠️ Cambio detectado en https://ejemplo.example/pagina · hash a3f5…",
  "timestamp": "2026-08-27T14:30:52.123456+00:00"
}
```

Compatible con Slack y Discord si el endpoint acepta `{"text": "…"}`. El campo `extra` del
manifest se fusiona en el cuerpo.

**Resolución de secretos:** un `token` que empiece por `@secret:` se resuelve con
`engine.secrets.get_secret`. Ejemplo de manifest:

```json
{"action": "notify.send",
 "params": {"message": "…", "backend": "webhook",
            "target": "https://hooks.ejemplo.example/servicios/XXXX",
            "token": "@secret:NOTIFY_TOKEN"}}
```

**El token nunca se devuelve en el resultado.** `record` contiene `backend`, `message`,
`timestamp`, `sent`, `target` y `status_code` — no el token. Es correcto y deliberado,
porque ese resultado acaba en `runs.context_json`.

**Sin reintentos ni cola:** un webhook caído produce una excepción de `requests` que el
orquestador convierte en fallo del paso. La única política de reintento disponible es el
campo `retries` del paso en el manifest.

**Ningún flow usa `backend: "webhook"` por defecto.** Los flows 23 y 26 traen
`notify_backend: "file"` en su `context.example.json`.

### 4.5 Tesseract OCR

Integración con un **binario externo**, no con un servicio. `pytesseract` invoca
`tesseract` en el sistema. `OCRImageAnalyzer._tesseract_binary_available` lo busca en el
PATH y, además, en `C:/Program Files/Tesseract-OCR/tesseract.exe` y su equivalente
`(x86)`, que es donde el instalador de Windows lo deja sin añadirlo al PATH.

Si falta, devuelve un payload válido con `status: "unavailable"`, `reason`
(`pytesseract_missing` o `tesseract_binary_missing`) y una `summary` con el comando de
instalación por sistema operativo. **El flow no falla.**

## 5. Adaptador opcional de visión multimodal (no usado por ningún flow)

Este es el único punto del repositorio donde existe código capaz de llamar a un modelo de
IA. Conviene documentarlo con precisión, porque el producto se presenta —correctamente—
como determinista y sin LLM.

### 5.1 Qué existe

`plugins/analyzers/vision_model_analyzer.py::VisionModelAnalyzer.analyze` soporta tres
proveedores:

| `provider` | Endpoint | Autenticación | Red |
|---|---|---|:--:|
| `mock` **(por defecto)** | — | — | ❌ |
| `openai_compatible` | `<endpoint>/chat/completions` | `Bearer` desde `api_key`, `api_key_env` o `OPENAI_API_KEY` | ✅ |
| `ollama` | `<endpoint o http://127.0.0.1:11434>/api/chat` | Ninguna | ✅ (local por defecto) |

`mock` no llama a nada: abre la imagen con Pillow, calcula brillo medio y RGB, y devuelve
`target_found: False, confidence: 0.0`. Su propia `summary` lo declara: «Visión mock
completada sin OCR ni proveedor externo […] no identifica texto real».

Los dos proveedores reales codifican la imagen en base64 (data URL en el caso
OpenAI-compatible), piden una respuesta **solo JSON** con `summary`, `target_found`,
`confidence`, `target_bbox` y `visible_text`, y usan `_extract_json_object` para recuperar
el objeto aunque venga envuelto en texto. `temperature: 0` en el caso OpenAI-compatible.
Sin endpoint o sin modelo, levantan `RuntimeError`.

### 5.2 Por qué es inalcanzable desde el catálogo

Cadena de invocación completa, verificada con búsqueda en todo el repositorio:

```text
VisionModelAnalyzer.analyze
    ← llamado SOLO por actions/vision.py::inspect_screen_target
        ← registrado como acción 'vision.inspect_screen_target'
            ← usada por 0 de los 27 manifests
```

Comprobación reproducible:

```bash
grep -l "inspect_screen_target" flows/*/manifest.json     # sin resultados
```

**Conclusión verificable:** con el catálogo tal y como se distribuye, **ningún flow puede
provocar una llamada a un proveedor de IA**. La instancia `VISION_ANALYZER =
VisionModelAnalyzer()` se crea al importar `actions/vision.py`, pero su constructor no
hace nada y ningún método se ejecuta sin pasar por `inspect_screen_target`.

Activarlo exigiría **escribir un flow nuevo** que declarara esa acción con
`vision_provider` distinto de `mock` y un `vision_endpoint`. Es una decisión explícita del
operador, no un comportamiento por defecto.

### 5.3 Riesgos si alguien lo activara

| Riesgo | Detalle |
|---|---|
| **Exfiltración de pantalla** | La imagen enviada es una captura del escritorio, codificada íntegra en base64 |
| Clave en el manifest | `vision_api_key` es un parámetro de la acción: escribirla ahí la dejaría en `steps.params_json` en claro |
| Sin validación del endpoint | Cualquier URL es aceptada |
| Determinismo perdido | La decisión `click` / `recover` pasaría a depender de un modelo |

La forma segura sería `vision_api_key_env` con el nombre de una variable, nunca
`vision_api_key` con el valor. `NO DOCUMENTADO EN EL REPOSITORIO`: no hay guía sobre esto.

### 5.4 Los stubs de `decision/`

`decision/optional_ai.py::suggest_step_order` y `decision/rules.py::prioritize_steps`
devuelven la lista de pasos sin tocarla y **nadie los importa**. La docstring del primero
documenta la intención de diseño, que sigue siendo válida aunque el código no exista:

> «Stub para futura integración IA. La IA solo debe sugerir orden o prioridad, nunca
> reemplazar la ejecución del motor.»

Es una decisión arquitectónica registrada. El código muerto asociado está en
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md).

## 6. Interfaces de plataforma (Windows)

No son APIs de red, pero son las integraciones que definen el producto.

| Interfaz | Vía | Acciones | Qué falla sin ella |
|---|---|---|---|
| Captura de framebuffer | `mss`, respaldo `Pillow.ImageGrab` | `screen.*` | `RuntimeError` explícito |
| Teclado y ratón | `pyautogui` | `ui.hotkey`, `type_text`, `click`, `click_bbox` | `RuntimeError` con instrucción |
| Ventana en foco | `pygetwindow` | `screen.capture_active_window` | `RuntimeError` con motivo |
| Portapapeles | `pyperclip` | `system.read_clipboard` | `available: False` con razón, **sin excepción** |
| PowerShell | `subprocess` | `system.run_powershell` | Depende del SO |
| Lanzador de procesos | `subprocess.Popen` + `shlex` | `ui.launch_process` | — |
| Navegador del sistema | `webbrowser` | `ui.open_url`, `open_file_in_browser` | — |
| Ventana nativa | `pywebview` (`edgechromium` en Windows) | `automa-desktop` | Código de salida 2 |
| CPU, RAM, disco, procesos | `psutil` | `system.*` | — |

**URIs `ms-settings:`** — el flow 11 usa `ui.open_url` con URIs del tipo
`ms-settings:network`. `webbrowser.open` delega en el manejador de protocolo de Windows.
Es una integración con el shell del sistema operativo, no con la web.

## 7. Extensión por terceros: entry points

`LazyActionRegistry._maybe_load_entry_points` descubre el grupo `automa.actions`:

```toml
# pyproject.toml de un paquete de terceros
[project.entry-points."automa.actions"]
"miempresa.exportar_sap" = "mi_paquete.acciones:exportar_sap"
```

Reglas del mecanismo, verificadas en el código:

- Los entry points se cargan **una sola vez**, de forma perezosa, cuando se pide un nombre
  desconocido o se llama a `keys()`.
- Se usa `setdefault`: **una acción interna nunca puede ser sobrescrita** por un paquete
  externo. Es una decisión de seguridad relevante.
- La función debe aceptar los parámetros como argumentos por nombre y devolver un `dict`
  serializable a JSON.

Contrato completo en [`docs/EXTENSION.md`](../EXTENSION.md).

> **Discrepancia verificada:** `_BUILT_IN_ACTIONS` declara 36 acciones y
> `[project.entry-points."automa.actions"]` del `pyproject.toml` solo 31. Faltan
> `browser.capture_page`, `browser.crawl_site`, `browser.extract_content`,
> `browser.fill_form` y `http.check_urls`. No rompe el runtime —el diccionario interno se
> consulta primero— pero un paquete externo que inspeccione el grupo verá un catálogo
> incompleto. Registrado en [15](15-risks-and-technical-debt.md).

## 8. Lo que NO existe

Verificado con búsqueda en todo el repositorio:

| No existe | Comprobación |
|---|---|
| Cliente de base de datos remota | Solo `sqlite3` |
| Cola de mensajes, broker, `celery` | Sin dependencias de ese tipo |
| Autenticación OAuth / OIDC / SSO | Sin bibliotecas de auth |
| Telemetría o *analytics* del producto | Sin cliente saliente propio |
| API pública versionada | Sin `/v1/`, sin OpenAPI |
| Servidor gRPC o WebSocket | Solo HTTP/1.1 |
| Cliente de correo | Sin `smtplib` en el código de producción |
| Integración con servicios en la nube | Sin SDK de ningún proveedor |
| Actualización automática | El instalador no incluye *updater* |

```bash
# Comando que respalda la afirmación de ausencia de red no declarada
grep -rn "requests\.\|urllib.request\|http.client\|socket\." --include="*.py" \
     actions/ engine/ app/ plugins/ decision/ | grep -v "^Binary"
```

Devuelve únicamente: `actions/http_actions.py`, `actions/notify.py`,
`actions/browser_extract.py` (`RobotsCache`), `plugins/analyzers/vision_model_analyzer.py`
y `app/desktop.py` (`socket.create_connection` contra `127.0.0.1`, para esperar al
servidor local). No hay ninguna otra salida de red en el sistema.

---

**Documentos relacionados:**
[05 · Referencia técnica](05-technical-reference.md) ·
[08 · Flujo de datos](08-data-flow.md) ·
[10 · Configuración](10-configuration.md) ·
[11 · Seguridad](11-security.md) ·
[13 · Despliegue y operación](13-deployment-and-operations.md)
