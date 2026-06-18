# 📝 Nota rápida en Notepad

## 🎯 Para qué sirve

Abrir Notepad y dejar una nota tipeada de un click. Útil como scratchpad volátil, recordatorio visible, o anotación rápida del estado de una tarea sin desviar la atención hacia otra app.

## 🧭 Flujo paso a paso

1. **launch_notepad** → lanza `notepad.exe`.
2. **wait_notepad_ready** → espera 1 s a que la ventana renderice.
3. **type_note** → tipea el texto del campo `note` en la ventana activa.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `note` | string | (texto de ejemplo) | Contenido a tipear en Notepad. |
| `dry_run` | bool | `false` | Si `true`, no abre Notepad ni tipea. |

## 📋 Requisitos

- Windows con `notepad.exe` en `PATH` (estándar).
- `pyautogui` (dependencia base).

## ⚠️ Limitaciones honestas

- Si Notepad tarda más de 1 s en abrir (equipo lento, primer arranque tras boot), el texto puede tipearse antes de que Notepad esté listo. Ajustá `wait_notepad_ready` si pasa.
- El texto se tipea sobre la **ventana en foco** al momento del paso `type_note` — si otra app robó el foco, la nota termina ahí.
- Notepad no se guarda automáticamente — la nota es volátil.

## 📤 Salidas

Solo registro en SQLite. La nota queda visible en Notepad hasta que el usuario la guarde o cierre.

## ⚡ Ejecución

CLI:

```bash
flujo run flows/13_notepad_quick_note --context flows/13_notepad_quick_note/context.example.json
```
