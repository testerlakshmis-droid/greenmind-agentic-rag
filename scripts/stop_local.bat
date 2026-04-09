@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_local.ps1"
