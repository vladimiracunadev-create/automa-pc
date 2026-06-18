# 🔇 Mutear/desmutear audio del sistema

## 🎯 Para qué sirve

Togglear el mute del audio maestro de Windows con un click. Equivale a apretar la tecla de mute del teclado: si hay sonido, lo silencia; si está silenciado, lo reactiva.

## 🧭 Flujo paso a paso

1. **send_mute_key** → envía la tecla multimedia `volumemute` vía `ui.hotkey`. Windows togglea el mute maestro instantáneamente.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `dry_run` | bool | `false` | Si `true`, no toca el sistema — solo registra la intención. |

## 📋 Requisitos

- Sesión Windows interactiva.
- `pyautogui` instalado (dependencia base).

## ⚠️ Limitaciones honestas

- Es un **toggle**, no un set absoluto: el estado final depende del estado previo. Para "siempre mutear" o "siempre desmutear" hace falta leer primero el estado del mixer (no incluido en este flow).
- Afecta el dispositivo de audio por defecto. Si tenés varios outputs y querés mutear uno específico, este flow no alcanza.
- No funciona en RDP/SSH donde teclas multimedia no se propagan.

## 📤 Salidas

Solo registro en SQLite. No produce archivos.

## ⚡ Ejecución

CLI:

```bash
flujo run flows/20_volume_mute_toggle
```
