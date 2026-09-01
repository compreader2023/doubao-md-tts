@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 goto :no_python
  set "PYTHON=python"
)

%PYTHON% -c "import sys; raise SystemExit(sys.version_info < (3,10))"
if errorlevel 1 (
  echo 错误：需要 Python 3.10 或更高版本。
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo 正在创建虚拟环境……
  %PYTHON% -m venv .venv
  if errorlevel 1 exit /b 1
)

if not exist "TTSAPIKEY" (
  copy /y "TTSAPIKEY.example" "TTSAPIKEY" >nul
  echo 已创建 TTSAPIKEY。下一步请填写 API Key 和 VOICE_TYPE。
)

echo 安装完成。运行示例：
echo   tts.bat 文章.md --emotion "温暖、沉稳地朗读"
exit /b 0

:no_python
echo 错误：没有找到 Python 3。请按 README 的 Windows 安装章节操作。
exit /b 1
