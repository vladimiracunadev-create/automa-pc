# ✅ Validación

> Tres niveles de validación: schema, pytest e integración real.

![Validación](assets/cover-automa-pc.svg)

El repositorio tiene tres niveles de validación, ordenados de barato a caro: schema + estructura, suite pytest e integración real.

## Validación De Manifests

```bash
python scripts/validate_project.py
# o, tras instalar el paquete:
automa-validate
```

Comprueba:

- conformidad con `schemas/manifest.schema.json` (vía `jsonschema` si está disponible; fallback estructural si no).
- que cada `action` esté registrada en `ACTION_REGISTRY` (incluye built-ins y entry-points externos).
- que no existan pasos duplicados.
- que cada transición `next` apunte a un paso existente.
- que `start_step`, si existe, sea válido.
- que toda acción usada esté dentro de `allowed_actions` (cuando el manifest la declara).

No ejecuta acciones ni escribe en SQLite.

## JSON Schema

`schemas/manifest.schema.json` es el contrato canónico. Si tu editor entiende JSON Schema (VS Code, JetBrains), apunta tus `manifest.json` a ese schema y obtendrás autocompletado:

```json
{
  "$schema": "../../schemas/manifest.schema.json",
  "id": "...",
  ...
}
```

## Suite Pytest

```bash
pytest                                # toda la suite (150 tests al cierre de 0.3.0)
pytest -m "not integration"           # sólo unitarios, rápido
pytest -k template                    # tests de un area especifica
pytest --cov=engine --cov=actions     # con cobertura
```

Áreas cubiertas:

- templates y resolución de placeholders;
- evaluación de condiciones;
- carga de manifests;
- registro perezoso de acciones;
- orquestador: éxito, retries, branching on failure, `when`, `max_steps`;
- sandbox: allowlist, secrets, allowed_paths;
- cron parser y `next_after`;
- locks de concurrencia en SQLite;
- métricas y export Prometheus;
- secrets y notificaciones (log/file backends);
- schema vs todos los manifests reales del repo.

## Listado De Flows

```bash
flujo list
# o
python -m engine.runner list
```

Debe funcionar incluso sin dependencias opcionales instaladas, porque el registry carga acciones bajo demanda.

## Smoke Test

```bash
python scripts/smoke_test.py
```

Comprueba:

- inicialización de SQLite;
- sincronización de flows;
- configuración guardada;
- ejecución de flows representativos (incluido el branching documental y el visual tri-modo en `mock`);
- scheduler básico;
- consulta posterior de runs.

## CI

`.github/workflows/ci.yml` ejecuta automáticamente en push y PRs sobre `main`:

- matriz Linux/Windows × Python 3.10/3.11/3.12;
- `uv sync --extra dev --extra schema`;
- `ruff check .`;
- `python scripts/validate_project.py`;
- `pytest --cov`;
- job adicional de smoke en Linux + 3.12.

## Criterios De Aceptación

Antes de subir cambios:

1. `python scripts/validate_project.py` debe terminar con `"ok": true`.
2. `pytest` debe pasar entero (o al menos los tests no marcados `integration` si tu entorno no tiene SQLite escribible).
3. `ruff check .` sin errores.
4. Si se tocaron acciones, motor o manifests, correr `python scripts/smoke_test.py`.
5. Si se tocó documentación, verificar que no queden referencias heredadas a versiones internas.

## Limitaciones De Validación

- El validador no evalúa semántica completa de parámetros (más allá del schema).
- El smoke test requiere permisos de escritura en `db/`, `state/`, `logs/` y `output/`.
- Los flows con captura real requieren escritorio gráfico.
- OCR requiere Tesseract instalado fuera de Python.
- Proveedores de visión externos requieren endpoint/modelo/API key válidos.

## Señales De Calidad

Un cambio está bien encaminado cuando:

- mejora trazabilidad sin ocultar errores;
- conserva compatibilidad con manifests existentes (mira los tests de `test_manifest_schema.py`);
- evita importar dependencias opcionales para operaciones simples;
- documenta riesgos de acciones con efectos reales;
- declara política de sandbox en manifests nuevos cuando aplica;
- deja ejemplos reproducibles.
