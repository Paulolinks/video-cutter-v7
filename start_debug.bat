@echo on
setlocal EnableExtensions
set "BASE=%~dp0"
cd /d "%BASE%" || (echo [ERRO] cd falhou & pause & exit /b)

set "PORT=5500"

rem -- mata algo preso na porta
for /f "tokens=5" %%p in ('netstat -aon ^| findstr :%PORT% ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1

rem -- detecta o venv (.venv primeiro, depois venv)
if exist ".venv\Scripts\python.exe" (
  set "PY=%BASE%.venv\Scripts\python.exe"
  set "ACT=%BASE%.venv\Scripts\activate.bat"
) else if exist "venv\Scripts\python.exe" (
  set "PY=%BASE%venv\Scripts\python.exe"
  set "ACT=%BASE%venv\Scripts\activate.bat"
) else (
  echo [ERRO] Nao achei .venv\Scripts\python.exe nem venv\Scripts\python.exe
  pause
  exit /b 1
)

call "%ACT%"

rem -- binarios locais (se usar)
set "IMAGEIO_FFMPEG_EXE=%BASE%bin\ffmpeg\ffmpeg.exe"
set "IMAGEMAGICK_BINARY=%BASE%bin\imagemagick\magick.exe"

echo ==== PYTHON ====
"%PY%" -V

echo ==== INICIANDO APP ====
"%PY%" "%BASE%app.py"

echo ==== SAIDA: %errorlevel% ====
pause
