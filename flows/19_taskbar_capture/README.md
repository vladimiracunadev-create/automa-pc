# 🪟 Captura de la barra de tareas

## 🎯 Para qué sirve

Sacar un PNG solo de la franja inferior del escritorio (barra de tareas + system tray + reloj + íconos pinneados), sin capturar la pantalla entera. Útil para:

- Auditar qué apps están pinneadas.
- Ver qué notificaciones/badges hay activos sin abrir nada.
- Comparar el estado del system tray a lo largo del día.

## 🧭 Flujo paso a paso

1. **capture_taskbar** → `screen.capture_region` con `bbox` anclado al borde inferior (`top: -48`) y `height: 48`. La altura cubre la barra estándar de Windows.

## ⚙️ Configuración

El flow tomó el `bbox` directo del manifest. Para cambiar el alto (ej. barras de 40 o 56 px en Windows 11), editá el manifest:

```json
"bbox": { "left": 0, "top": -48, "width": 99999, "height": 48 }
```

Convenciones del bbox (ver `actions/screen.py:capture_region`):

- `top` o `left` negativos → relativos al borde opuesto (estilo CSS).
- `width`/`height` se clampean al borde del monitor si exceden — usar `99999` significa "hasta el final".
- Alternativa: `{ "left": L, "top": T, "right": R, "bottom": B }`.

## 📋 Requisitos

- `mss` (dependencia base).
- Monitor principal accesible.

## ⚠️ Limitaciones honestas

- Captura solo el **monitor primario** (`monitors[1]` de mss).
- Si tu barra de tareas está en otro borde (izquierda, arriba, derecha — configuración no estándar), cambiá las coordenadas del `bbox`.
- En equipos con DPI scaling alto, una barra "de 48 px" puede medir más en píxeles físicos — ajustá.

## 📤 Salidas

- `output/screenshots/taskbar_<timestamp>.png`

## ⚡ Ejecución

CLI:

```bash
flujo run flows/19_taskbar_capture
```
