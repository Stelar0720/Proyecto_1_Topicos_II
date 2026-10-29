param(
    [switch]$Reset
)

$ErrorActionPreference = "Stop"
$scriptRoot = $PSScriptRoot
Set-Location $scriptRoot
$env:CITAFACIL_ENV_FILE = ".env.demo"
$python = Join-Path $scriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

if (-not (Test-Path ".env.demo")) {
    Copy-Item ".env.demo.example" ".env.demo"
    Write-Host "Se creó .env.demo. Revisa el token antes de compartir pantalla."
}

if ($Reset) {
    & $python reset_demo.py
} else {
    & $python seed.py
    & $python seed_forecast_demo.py
}

Write-Host ""
Write-Host "DEMO LISTA"
Write-Host "Público: http://127.0.0.1:8000/demo/"
Write-Host "Admin:   http://127.0.0.1:8000/demo/admin.html"
Write-Host "Token:   citafacil-demo-2026"
Write-Host ""
& $python -m uvicorn app.main:app --reload
