::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFAtVWQiNAE+/Fb4I5/jH+eODp0JQV/crbIrJmvnONrcv7ETyfJUi2DRTm8Rs
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCyDJGyX8VAjFAtVWQiNAE+/Fb4I5/jH+eODp0JQV/crbIrJmvnONrcvzEzqdJpg4HNencRBLw5Mahe5Ixll52xDoiqAL8L8
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
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
