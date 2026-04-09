@echo off
setlocal
set PORT=%1
if "%PORT%"=="" set PORT=8505

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_local.ps1" -Port %PORT%
