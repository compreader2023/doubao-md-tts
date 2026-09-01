@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  call setup.bat
  if errorlevel 1 exit /b 1
)
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
".venv\Scripts\python.exe" -m doubao_md_tts %*
exit /b %errorlevel%
