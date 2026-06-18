# 🖼️ Screenshot de la ventana activa

## 🎯 Para qué sirve

Capturar **solo** la ventana actualmente en foco — sin barra de tareas, sin escritorio, sin otras apps detrás. Útil para:

- Documentar un paso puntual de un proceso (capturar la ventana del IDE, del navegador, de un instalador).
- Dejar evidencia de un mensaje de error específico sin filtrar info de otras apps.
- Comparar el estado de una única app a lo largo del tiempo.

## 🧭 Flujo paso a paso

1. **shot_active** → `screen.capture_active_window` resuelve el rectángulo de la ventana en foco con `pygetwindow` y delega el recorte a `screen.capture_region`. Devuelve `image_path`, `bbox`, `window_title`.

## ⚙️ Configuración

Sin parámetros — la ventana activa se autodetecta al momento del paso.

## 📋 Requisitos

- `PyGetWindow` (declarado como dependencia base).
- Backend de captura (`mss` o `PIL.ImageGrab`).
- Sesión Windows interactiva — `getActiveWindow()` devuelve `None` en sesiones sin foco visible.

## ⚠️ Limitaciones honestas

- Como el flow se dispara desde el panel (web), al hacer click la ventana activa **es el navegador del panel** — el screenshot capturará el navegador, no lo que mirabas antes. Para capturar otra app, dispará el flow desde CLI o con un cron programado.
- Si la ventana tiene parte fuera del monitor (negative `left`/`top`), se clampea al borde del monitor.
- En equipos con varios monitores, el bbox se interpreta sobre el monitor principal — ventanas en el secundario quedan recortadas.
- No funciona en RDP/SSH headless.

## 📤 Salidas

- `output/screenshots/active_window_<timestamp>.png`
- En el JSON de run queda registrado `window_title` para auditoría.

## ⚡ Ejecución

CLI:

```bash
flujo run flows/16_active_window_screenshot
```
