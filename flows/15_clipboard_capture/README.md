# 📋 Captura del portapapeles a JSON

## 🎯 Para qué sirve

Persistir el contenido del portapapeles del sistema a un JSON con timestamp, de un click. Útil para:

- Auditar qué se copió antes de pegarlo en X.
- Evidencia liviana ("a las 14:30 el clipboard tenía esto").
- Primitiva para flows que necesitan procesar texto que el usuario ya tiene listo (URL, JWT, snippet).

## 🧭 Flujo paso a paso

1. **read_clipboard** → `system.read_clipboard` con `max_chars` configurable.
2. **save_clipboard** → escribe payload completo (texto, longitud real, flag `truncated`) a `output/reports/clipboard_{now}.json`.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `max_chars` | int | `10000` | Tope superior; si el clipboard es más largo, el JSON guarda los primeros N chars y marca `truncated: true` con el `length` real. |

## 📋 Requisitos

- `pyperclip` (declarado como dependencia base).
- Sesión Windows interactiva (en Linux también funciona con `xclip`/`xsel`; en SSH headless devuelve `available: false` con `reason`).

## ⚠️ Limitaciones honestas

- Solo lee **texto plano**. Si el portapapeles contiene imagen, archivos, HTML formateado, pyperclip devuelve vacío.
- Lee snapshot puntual — si el usuario copia algo nuevo entre el click y la ejecución del paso, captura lo nuevo.
- Persistir clipboard en disco puede capturar contenido sensible (contraseñas pegadas, tokens). El archivo queda en `output/reports/` — gestionar retención según política.

## 📤 Salidas

- `output/reports/clipboard_<timestamp>.json` con shape:
  ```json
  { "available": true, "text": "...", "length": 1234, "truncated": false, "max_chars": 10000 }
  ```

## ⚡ Ejecución

CLI:

```bash
flujo run flows/15_clipboard_capture --context flows/15_clipboard_capture/context.example.json
```
