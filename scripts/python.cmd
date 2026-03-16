@echo off
setlocal

powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0python.ps1" %*
exit /b %ERRORLEVEL%
