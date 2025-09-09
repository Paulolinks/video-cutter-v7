# app.py (atualizado: suporta 'automatico' e 'tema' no /process)
from flask import Flask, render_template, request, jsonify
import subprocess
import os, glob
import json
import sys
import time
# from matplotlib import font_manager
from pathlib import Path
from utils_fontes import listar_fontes_windows, listar_fontes_legiveis
from utils_fontes import listar_fontes_legiveis_filtradas


# Google Drive (sem mudanças funcionais)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__, template_folder="templates", static_folder="static")

# Se alterar o escopo, delete o token.json para re-autenticar
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ==== Utils para salvar/ler pasta no Drive (ajuste se não usar) ====
def salvar_pasta_id(folder_id: str):
    with open("drive_folder_id.txt", "w", encoding="utf-8") as f:
        f.write(folder_id.strip())

def carregar_pasta_id():
    try:
        with open("drive_folder_id.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return None
# ===================================================================
# utils_fontes.py (crie este arquivo na raiz do projeto)

def listar_fontes_windows():
    fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    padroes = ["*.ttf", "*.otf", "*.ttc"]
    fontes = []
    for pad in padroes:
        fontes.extend(glob.glob(os.path.join(fonts_dir, pad)))
    # remove duplicados preservando ordem
    seen, out = set(), []
    for f in fontes:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out




#+++++++++++++

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid or not creds.refresh_token:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=5501, access_type='offline', prompt='consent')
        with open('token.json', 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


@app.route("/salvar_pasta_id", methods=["POST"])
def salvar_id():
    folder_id = request.json.get("folder_id")
    if not folder_id:
        return jsonify({"success": False, "message": "ID vazio"})
    salvar_pasta_id(folder_id)
    return jsonify({"success": True})

@app.route("/upload", methods=["POST"])
def upload_to_drive():
    try:
        service = get_drive_service()
        pasta_videos = Path("static/final")
        arquivos = list(pasta_videos.glob("*.mp4"))
        if not arquivos:
            return jsonify({"success": False, "message": "Nenhum vídeo em static/final."})
        uploaded_ids = []
        target_folder_id = carregar_pasta_id()
        if not target_folder_id:
            return jsonify({"success": False, "message": "ID da pasta não configurado."})
        for arquivo in arquivos:
            file_metadata = {'name': arquivo.name, 'parents': [target_folder_id]}
            media = MediaFileUpload(str(arquivo), mimetype='video/mp4')
            gfile = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            uploaded_ids.append(gfile.get('id'))
        return jsonify({"success": True, "uploaded_ids": uploaded_ids})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/upload_credencial", methods=["POST"])
def upload_credencial():
    try:
        arquivo = request.files.get("file")  # Corrigido: era "credencial", agora é "file"
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
    return render_template("index.html", build=str(int(time.time())))

@app.route("/process", methods=["POST"])
def process():
    link = request.json.get("link")
    if not link:
        return jsonify({"success": False, "message": "Nenhum link fornecido."})

    # NOVO: captura modo automático, tema e rede social
    automatico = bool(request.json.get("automatico", True))
    tema = (request.json.get("tema") or "").strip()
    rede_social = request.json.get("rede_social", "instagram")
    modo_video = request.json.get("modo_video", "crop")
    qualidade_video = request.json.get("qualidade_video", "alta")

    # Config visual e lógica
    config = {
        "fonte": request.json.get("fonte", "Arial-Bold"),
        "cor": request.json.get("cor", "white"),
        "tamanho": request.json.get("tamanho", 60),
        "altura": request.json.get("altura", 1280),
        "largura": request.json.get("largura", 720),
        "posicao": request.json.get("posicao", 0.2),
        "tempo_min": request.json.get("tempo_min", 15.0),
        "tempo_max": request.json.get("tempo_max", 53.0),

        # >>> NOVO <<<
        "automatico": automatico,
        "tema": tema if not automatico else "",
        "rede_social": rede_social,
        "modo_video": modo_video,
        "qualidade_video": qualidade_video
    }

    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        if os.path.exists("status.json"):
            os.remove("status.json")

        result = subprocess.run(
            [sys.executable, "main.py", link],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            erro = f"Erro ao processar: {result.stderr}"
            with open("status.json", "w", encoding="utf-8") as f:
                json.dump({"etapa": 0, "descricao": erro}, f, ensure_ascii=False)
            return jsonify({"success": False, "message": erro})

        return jsonify({"success": True, "message": "Finalizado com sucesso!", "log": result.stdout})
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
    try:
        if not os.path.exists("static/final"):
            return jsonify({"success": True, "videos": []})
        
        arquivos = os.listdir("static/final")
        mp4s = ["/static/final/" + arq for arq in arquivos if arq.endswith(".mp4")]
        return jsonify({"success": True, "videos": mp4s})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})



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


@app.get("/fontes")
def fontes():
    """Retorna lista de fontes básicas do Windows"""
    # Fontes básicas do Windows (sem matplotlib)
    fontes_basicas = [
        {'nome': 'Arial', 'arquivo': 'arial.ttf', 'caminho': 'Arial'},
        {'nome': 'Arial Black', 'arquivo': 'arial-black.ttf', 'caminho': 'Arial Black'},
        {'nome': 'Impact', 'arquivo': 'impact.ttf', 'caminho': 'Impact'},
        {'nome': 'Times New Roman', 'arquivo': 'times.ttf', 'caminho': 'Times New Roman'},
        {'nome': 'Verdana', 'arquivo': 'verdana.ttf', 'caminho': 'Verdana'},
        {'nome': 'Comic Sans MS', 'arquivo': 'comic.ttf', 'caminho': 'Comic Sans MS'},
        {'nome': 'Courier New', 'arquivo': 'cour.ttf', 'caminho': 'Courier New'},
        {'nome': 'Georgia', 'arquivo': 'georgia.ttf', 'caminho': 'Georgia'},
        {'nome': 'Tahoma', 'arquivo': 'tahoma.ttf', 'caminho': 'Tahoma'},
        {'nome': 'Trebuchet MS', 'arquivo': 'trebuc.ttf', 'caminho': 'Trebuchet MS'},
        {'nome': 'Calibri', 'arquivo': 'calibri.ttf', 'caminho': 'Calibri'},
        {'nome': 'Segoe UI', 'arquivo': 'segoeui.ttf', 'caminho': 'Segoe UI'}
    ]
    return jsonify({"success": True, "fontes": fontes_basicas})

@app.route("/obter_pasta_id", methods=["GET"])
def obter_pasta_id():
    """Retorna o ID da pasta do Google Drive salvo"""
    try:
        pasta_id = carregar_pasta_id()
        if pasta_id:
            return jsonify({"success": True, "pasta_id": pasta_id})
        else:
            return jsonify({"success": False, "message": "Nenhuma pasta configurada"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/testar_drive", methods=["POST"])
def testar_drive():
    """Testa a conexão com o Google Drive"""
    try:
        service = get_drive_service()
        # Testar listando arquivos
        results = service.files().list(pageSize=1).execute()
        return jsonify({"success": True, "message": "Conexão com Google Drive OK"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro na conexão: {str(e)}"})

@app.route("/limpar_videos_antigos", methods=["POST"])
def limpar_videos_antigos():
    """Limpa vídeos antigos de todas as pastas exceto final"""
    try:
        pastas_limpar = ["data/videos", "data/cortes", "data/audio", "data/transcricoes"]
        deletados = []
        
        for pasta in pastas_limpar:
            if os.path.exists(pasta):
                for arquivo in os.listdir(pasta):
                    if arquivo.endswith(('.mp4', '.webm', '.wav', '.txt')):
                        try:
                            caminho = os.path.join(pasta, arquivo)
                            os.remove(caminho)
                            deletados.append(caminho)
                        except Exception as e:
                            print(f"Erro ao remover {arquivo}: {e}")
        
        return jsonify({"success": True, "deletados": deletados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/deletar_video_final/<nome>", methods=["DELETE"])
def deletar_video_final(nome):
    """Deleta um vídeo específico da pasta final"""
    try:
        # Deletar de ambas as pastas
        caminho_static = os.path.join("static/final", nome)
        caminho_data = os.path.join("data/final", nome)
        
        deletados = []
        
        if os.path.exists(caminho_static):
            os.remove(caminho_static)
            deletados.append("static/final")
            
        if os.path.exists(caminho_data):
            os.remove(caminho_data)
            deletados.append("data/final")
            
        if deletados:
            return jsonify({"success": True, "message": f"Vídeo {nome} deletado de: {', '.join(deletados)}"})
        else:
            return jsonify({"success": False, "message": "Arquivo não encontrado"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/deletar_todos_final", methods=["POST"])
def deletar_todos_final():
    """Deleta todos os vídeos da pasta final"""
    try:
        pastas = ["static/final", "data/final"]
        deletados = []
        
        for pasta in pastas:
            if os.path.exists(pasta):
                for arquivo in os.listdir(pasta):
                    if arquivo.endswith('.mp4'):
                        try:
                            caminho = os.path.join(pasta, arquivo)
                            os.remove(caminho)
                            deletados.append(f"{pasta}/{arquivo}")
                        except Exception as e:
                            print(f"Erro ao remover {arquivo}: {e}")
        
        return jsonify({"success": True, "deletados": deletados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})



if __name__ == "__main__":
    app.run(port=5500)
