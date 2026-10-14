@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-OpenSci.ps1" -LauncherAction Menu
set "OpenSciClaudeExit=%errorlevel%"
if not "%OpenSciClaudeExit%"=="0" pause
endlocal & exit /b %OpenSciClaudeExit%
