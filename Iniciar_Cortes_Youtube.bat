@echo off
setlocal EnableExtensions
set "BASE=%~dp0"
cd /d "%BASE%" || exit /b

set "PORT=5500"

rem --- libera a porta 5500 se alguem estiver escutando
for /f "tokens=5" %%p in ('netstat -aon ^| findstr /R /C:":%PORT% .*LISTENING"') do taskkill /PID %%p /F >nul 2>&1

rem --- escolhe o pythonw do venv (.venv > venv > sistema)
set "PYW="
if exist ".venv\Scripts\pythonw.exe" set "PYW=%BASE%.venv\Scripts\pythonw.exe"
if not defined PYW if exist "venv\Scripts\pythonw.exe" set "PYW=%BASE%venv\Scripts\pythonw.exe"
if not defined PYW set "PYW=pythonw.exe"

rem --- binarios locais (se voce usa)
set "IMAGEIO_FFMPEG_EXE=%BASE%bin\ffmpeg\ffmpeg.exe"
set "IMAGEMAGICK_BINARY=%BASE%bin\imagemagick\magick.exe"

rem --- inicia o app silencioso (sem console)
start "" "%PYW%" "%BASE%app.py"

rem --- espera a porta abrir (ate ~10s), entao abre o navegador
for /l %%i in (1,1,20) do (
  powershell -NoProfile -Command "try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',%PORT%);$c.Close();exit 0}catch{exit 1}" >nul 2>&1 && goto OPEN
  timeout /t 0 >nul
)
rem fallback: se nao detectou, ainda assim tenta abrir depois de 2s
timeout /t 2 >nul

:OPEN
start "" "http://127.0.0.1:%PORT%"
exit /b
