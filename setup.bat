@echo off
title Video Cutter - Setup
color 0B
echo.
echo ==============================
echo 🔧 Criando ambiente virtual...
echo ==============================
python -m venv venv

echo.
echo ==============================
echo 📦 Ativando ambiente virtual...
echo ==============================
call venv\Scripts\activate

echo.
echo ==============================
echo 📥 Instalando dependências...
echo ==============================
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ==============================
echo 📚 Baixando modelos do spaCy...
echo ==============================
python -m spacy download en_core_web_sm
python -m spacy download pt_core_news_sm

echo.
echo ==============================
echo ✅ SETUP CONCLUÍDO!
echo Rode o app com:
echo.
echo     venv\Scripts\activate && python app.py
echo.
pause
