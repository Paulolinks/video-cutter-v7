@echo off
echo 🔧 Criando ambiente virtual...
python -m venv venv

echo 📦 Ativando ambiente virtual...
call venv\Scripts\activate

echo 📥 Instalando dependências...
pip install --upgrade pip
pip install -r requirements.txt

echo 📚 Baixando modelos do spaCy...
python -m spacy download en_core_web_sm
python -m spacy download pt_core_news_sm

echo ✅ Setup concluído! Agora você pode rodar: python app.py
pause
