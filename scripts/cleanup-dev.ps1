Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "[cleanup] removing Python cache..."
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Remove-Item ".pytest_cache" -Recurse -Force
Remove-Item "pytest-cache-files-*" -Recurse -Force

Write-Host "[cleanup] pruning Docker builder cache..."
docker builder prune -f | Out-Host

Write-Host "[cleanup] done. SQLite data and Ollama model volumes were preserved."
