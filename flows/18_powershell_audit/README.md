# 🛡️ Auditoría rápida con PowerShell

## 🎯 Para qué sirve

Correr un comando PowerShell **read-only** de una allowlist estricta y guardar `stdout`/`stderr`/`exit_code` a JSON con timestamp. Pensado para snapshots de auditoría puntuales sin abrir una consola — qué hora es según el equipo, qué procesos corren, qué servicios están en marcha, info del sistema.

**No** está pensado para automatización con efectos secundarios.

## 🧭 Flujo paso a paso

1. **run_audit_command** → `system.run_powershell` con el `command` configurado y un `timeout_seconds` de 30.
2. **save_audit_report** → JSON con `{command, exit_code, stdout, stderr, allowlist_used}` a `output/reports/powershell_audit_{now}.json`.

## ⚙️ Configuración

| Campo | Tipo | Por defecto | Significado |
| --- | --- | --- | --- |
| `command` | string | `Get-Date` | Comando PowerShell. Debe empezar EXACTAMENTE con uno de los verbos del allowlist. |

## 🛡️ Allowlist de seguridad

La acción `system.run_powershell` aplica una allowlist por defecto **read-only**:

```
Get-Date, Get-Process, Get-Service, Get-ComputerInfo, Get-CimInstance,
Get-WmiObject, Get-Disk, Get-Volume, Get-NetAdapter, Get-NetIPAddress,
Get-EventLog, Get-Host, Get-Location
```

Rechazos previos a invocar PowerShell:

- Cualquier token de **chain o redirección** (`;`, `|`, `&`, `` ` ``, `>`, `<`, `$(`, `$_`) — evita inyección.
- Cualquier verbo fuera del allowlist.

Para extender el allowlist en un flow específico, pasarlo como param `allowlist` al step (no en `context` — el allowlist viaja en el manifest, no en el input del usuario).

## 📋 Requisitos

- Windows con `powershell` en `PATH` (estándar).

## ⚠️ Limitaciones honestas

- La allowlist es por **verbo inicial** — un usuario malicioso con control del param `command` no puede ejecutar `rm -rf` pero tampoco puede correr nada con side-effects útiles, eso es intencional.
- `stdout` se trunca a 50 000 chars, `stderr` a 5 000 — comandos con output enorme quedan parciales pero el JSON marca `*_truncated: true`.
- Timeout default de 30 s — comandos largos (`Get-Process` con cientos de procesos suele tardar <1 s, pero `Get-EventLog` puede ser lento).

## 📤 Salidas

- `output/reports/powershell_audit_<timestamp>.json` con el shape:
  ```json
  {
    "command": "Get-Date",
    "exit_code": 0,
    "stdout": "...",
    "stderr": "",
    "stdout_truncated": false,
    "stderr_truncated": false,
    "allowlist_used": ["Get-Date", "Get-Process", "..."]
  }
  ```

## ⚡ Ejecución

CLI:

```bash
flujo run flows/18_powershell_audit --context flows/18_powershell_audit/context.example.json
```
