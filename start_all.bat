@echo off
chcp 65001 >nul
echo =====================================
echo   社交匹配系统 — 一键启动
echo =====================================
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0start_all.ps1"
pause
