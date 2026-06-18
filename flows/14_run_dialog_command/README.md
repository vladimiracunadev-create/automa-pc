# ⌨️ Ejecutar comando vía diálogo Ejecutar (Win+R)

## 🎯 Para qué sirve

Lanzar cualquier comando, programa, URL o ruta usando el diálogo **Ejecutar** de Windows (`Win+R`) — sin pasar por el menú Inicio ni el explorador. El comando se elige por contexto, así que el mismo flow sirve para abrir `calc.exe`, `cmd`, una URL `https://...`, o una ruta `C:\...`.

## 🧭 Flujo paso a paso

1. **open_run_dialog** → `Win+R` para abrir el diálogo Ejecutar.
2. **wait_dialog** → espera 400 ms a que la ventana renderice.
3. **type_command** → tipea el `command` configurado.
4. **submit_command** → presiona Enter para ejecutarlo.

## ⚙️ Configuración

`context.example.json`:

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `command` | string | `calc.exe` | Comando, programa, ruta o URL a lanzar. Cualquier cosa que el diálogo Ejecutar acepte. |
| `dry_run` | bool | `false` | Si `true`, no toca el sistema — solo registra la intención. |

## 📋 Requisitos

- Sesión Windows interactiva.
- `pyautogui` instalado (dependencia base del proyecto).

## ⚠️ Limitaciones honestas

- El comando se ejecuta con los permisos del usuario actual. **No usar con input no confiable.**
- Si una ventana modal absorbe el `Win+R`, el flow puede fallar silenciosamente.
- No funciona en RDP/SSH donde modificadores Windows no se propagan.

## 📤 Salidas

Solo registro en SQLite. No produce archivos.

## ⚡ Ejecución

Panel: click en la card del flow (sin atajo Alt — los 12 disponibles ya están ocupados).

CLI:

```bash
flujo run flows/14_run_dialog_command --context flows/14_run_dialog_command/context.example.json
```
