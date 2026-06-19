# Build local del bundle Automa con PyInstaller.
#
# Uso desde la raiz del repo:
#   pwsh installer/build_local.ps1
#
# Salida:
#   dist/Automa/Automa.exe          (launcher GUI)
#   dist/Automa/*                   (DLLs, datafiles, runtime de Python)

$ErrorActionPreference = "Stop"

Write-Host "==> Limpiando build/ y dist/..."
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

Write-Host "==> Corriendo PyInstaller..."
python -m PyInstaller installer/automa.spec --noconfirm --clean

if (Test-Path "dist/Automa/Automa.exe") {
    $size = (Get-Item "dist/Automa/Automa.exe").Length / 1MB
    Write-Host ""
    Write-Host "==> OK. Automa.exe = $([Math]::Round($size, 1)) MB"
    Write-Host "    Probar: dist/Automa/Automa.exe"
} else {
    Write-Error "Build fallo: no se encontro dist/Automa/Automa.exe"
    exit 1
}
