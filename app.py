# app.py (atualizado com encoding='utf-8' no subprocess.run)
from flask import Flask, render_template, request, jsonify
import subprocess
import os
import json
import sys
# fontes do computado
from matplotlib import font_manager
from flask import jsonify
app = Flask(__name__, template_folder="templates", static_folder="static")

# Verifica se o arquivo de configuração existe e carrega o ID da pasta
from utils.pasta_drive import salvar_pasta_id, carregar_pasta_id

# app.py (trecho novo, logo após as outras importações)
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Se alterar o escopo, delete o token.json para re-autenticar
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Fazer a autenticação com o Google Drive
def get_drive_service():
    creds = None

    # Verifica se já existe um token salvo
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Se não tiver credenciais ou forem inválidas, inicia o fluxo de login
    if not creds or not creds.valid or not creds.refresh_token:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES
        )
        creds = flow.run_local_server(
            port=5501,
            access_type='offline',
            prompt='consent'
        )

        # Salva o token com o refresh_token incluso
        with open('token.json', 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


# Rota para configurar a pasta do Google Drive
@app.route("/salvar_pasta_id", methods=["POST"])
def salvar_id():
    folder_id = request.json.get("folder_id")
    if not folder_id:
        return jsonify({"success": False, "message": "ID vazio"})
    salvar_pasta_id(folder_id)
    return jsonify({"success": True})



# Rota para upload de vídeos para o Google Drive
@app.route("/upload", methods=["POST"])
def upload_to_drive():
    try:
        service = get_drive_service()
        pasta_videos = Path("static/final")  # agora Path está definido
        arquivos = list(pasta_videos.glob("*.mp4"))

        if not arquivos:
            return jsonify({"success": False, "message": "Nenhum vídeo em static/final."})

        uploaded_ids = []
        target_folder_id = carregar_pasta_id()
        if not target_folder_id:
            return jsonify({"success": False, "message": "ID da pasta não configurado."})
                 # coloque seu ID de pasta aqui

        for arquivo in arquivos:
            file_metadata = {
                'name': arquivo.name,
                'parents': [target_folder_id]
            }
            media = MediaFileUpload(str(arquivo), mimetype='video/mp4')
            gfile = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            uploaded_ids.append(gfile.get('id'))

        return jsonify({"success": True, "uploaded_ids": uploaded_ids})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# Fazer upload de credenciais do Google Drive ( credentials.json )
@app.route("/upload_credencial", methods=["POST"])
def upload_credencial():
    try:
        arquivo = request.files.get("credencial")
        if not arquivo:
            return jsonify({"success": False, "message": "Nenhum arquivo foi enviado."})

        caminho = os.path.join(os.getcwd(), "credentials.json")

        if os.path.exists(caminho):
            print("⚠️ Credencial anterior será substituída.")

        arquivo.save(caminho)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    link = request.json.get("link")

    if not link:
        return jsonify({"success": False, "message": "Nenhum link fornecido."})

    # Captura config enviada pelo frontend
    config = {
        "fonte": request.json.get("fonte", "Arial-Bold"),
        "cor": request.json.get("cor", "white"),
        "tamanho": request.json.get("tamanho", 60),
        "altura": request.json.get("altura", 1280),
        "largura": request.json.get("largura", 720),
        "posicao": request.json.get("posicao", 0.2),
        "tempo_min": request.json.get("tempo_min", 15.0),
        "tempo_max": request.json.get("tempo_max", 53.0),

    }


    try:
        # Salva config
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # Apaga progresso anterior
        if os.path.exists("status.json"):
            os.remove("status.json")

        # Executa o script main.py com encoding utf-8
        result = subprocess.run(
            [sys.executable, "main.py", link],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if result.returncode != 0:
            erro = f"Erro ao processar: {result.stderr}"
            with open("status.json", "w", encoding="utf-8") as f:
                json.dump({"etapa": 0, "descricao": erro}, f, ensure_ascii=False)
            return jsonify({"success": False, "message": erro})

        return jsonify({
            "success": True,
            "message": "Finalizado com sucesso!",
            "log": result.stdout
        })

    except Exception as e:
        erro = f"Erro ao processar: {str(e)}"
        with open("status.json", "w", encoding="utf-8") as f:
            json.dump({"etapa": 0, "descricao": erro}, f, ensure_ascii=False)
        return jsonify({"success": False, "message": erro})

@app.route("/progresso", methods=["GET"])
def progresso():
    if os.path.exists("status.json"):
        try:
            with open("status.json", "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({"etapa": 0, "descricao": f"Erro ao ler progresso: {str(e)}"})
    else:
        return jsonify({"etapa": 0, "descricao": "Aguardando..."})

@app.route("/videos")
def videos():
    arquivos = os.listdir("static/final")
    mp4s = ["/static/final/" + arq for arq in arquivos if arq.endswith(".mp4")]
    return jsonify(mp4s)



# Rota para obter as fontes disponíveis - New
@app.route("/fonts", methods=["GET"])
def listar_fontes():
    fontes = []
    for font_path in font_manager.findSystemFonts(fontpaths=None, fontext='ttf'):
        try:
            nome = font_manager.FontProperties(fname=font_path).get_name()
            if nome not in fontes:
                fontes.append(nome)
        except:
            continue
    fontes.sort()
    return jsonify(fontes)


# Deletar videos antigos
from flask import send_from_directory

@app.route("/deletar_videos", methods=["POST"])
def deletar_videos():
    pastas = ["data/videos","data/final", "data/cortes", "static/final"]
    deletados = []

    for pasta in pastas:
        if os.path.exists(pasta):
            for arquivo in os.listdir(pasta):
                caminho = os.path.join(pasta, arquivo)
                if os.path.isfile(caminho) and arquivo.endswith(".mp4"):
                    os.remove(caminho)
                    deletados.append(os.path.join(pasta, arquivo))

    return jsonify({"success": True, "deletados": deletados})

# Deletar videos individuais - v8
@app.route("/deletar_video/<nome>", methods=["DELETE"])
def deletar_video_individual(nome):
    try:
        caminho = os.path.join("static/final", nome)
        if os.path.exists(caminho):
            os.remove(caminho)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Arquivo não encontrado."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


if __name__ == "__main__":
    app.run(port=5500)
