@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
set EXIT_CODE=%ERRORLEVEL%
echo %CMDCMDLINE% | find /i "%~0" >nul
if %ERRORLEVEL%==0 pause
exit /b %EXIT_CODE%
