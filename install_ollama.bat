@echo off
echo Instalando Ollama no Windows...

REM Baixar o instalador do Ollama
echo Baixando instalador do Ollama...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.exe' -OutFile 'ollama-installer.exe'"

REM Instalar Ollama
echo Instalando Ollama...
ollama-installer.exe

REM Aguardar instalação
timeout /t 5 /nobreak

REM Iniciar o serviço Ollama
echo Iniciando serviço Ollama...
ollama serve

REM Aguardar o serviço iniciar
timeout /t 10 /nobreak

REM Baixar modelo llama3.2
echo Baixando modelo llama3.2...
ollama pull llama3.2

echo Instalação concluída!
pause
