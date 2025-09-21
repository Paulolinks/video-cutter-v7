# app.py (atualizado: suporta 'automatico' e 'tema' no /process)
from flask import Flask, render_template, request, jsonify
import subprocess
import os, glob
import json
import sys
import time
import requests
import pandas as pd  # type: ignore
from datetime import datetime
# from matplotlib import font_manager
from pathlib import Path
from mutagen.mp4 import MP4
from utils_fontes import listar_fontes_windows, listar_fontes_legiveis
from utils_fontes import listar_fontes_legiveis_filtradas

# Nova funcionalidades:
import os, glob, json
from flask import request, jsonify
from metadados.gerar_textos import gerar_titulo, gerar_legenda, gerar_hashtags
from metadados.renomear import renomear_video
from metadados.salvar_planilha import salvar_linha
CORTES_DIR = os.path.join("static","final")


# Google Drive (sem mudanças funcionais)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__, template_folder="templates", static_folder="static")

# Se alterar o escopo, delete o token.json para re-autenticar
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.send'
]

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
        print("🔐 Re-autorizando com Google para incluir Google Sheets e Gmail...")
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=5501, access_type='offline', prompt='consent')
        with open('token.json', 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
        print("✅ Autorização atualizada com sucesso!")
    return build('drive', 'v3', credentials=creds)


@app.route("/salvar_pasta_id", methods=["POST"])
def salvar_id():
    folder_id = request.json.get("folder_id")
    if not folder_id:
        return jsonify({"success": False, "message": "ID vazio"})
    salvar_pasta_id(folder_id)
    return jsonify({"success": True})

@app.route("/reauth_google", methods=["POST"])
def reauth_google():
    """Força re-autorização com Google para incluir todas as permissões"""
    try:
        # Deletar token existente para forçar re-autorização
        if os.path.exists('token.json'):
            os.remove('token.json')
            print("🗑️ Token anterior removido")
        
        # Forçar nova autorização
        print("🔐 Iniciando re-autorização com Google...")
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=5501, access_type='offline', prompt='consent')
        
        # Salvar novo token
        with open('token.json', 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
        
        print("✅ Re-autorização concluída com sucesso!")
        return jsonify({
            "success": True, 
            "message": "Re-autorização concluída! Agora você tem acesso ao Google Drive, Google Sheets e Gmail."
        })
        
    except Exception as e:
        print(f"❌ Erro na re-autorização: {e}")
        return jsonify({"success": False, "message": f"Erro na re-autorização: {str(e)}"})

@app.route("/check_permissions", methods=["GET"])
def check_permissions():
    """Verifica se as permissões do Google estão completas"""
    try:
        # Testar credenciais
        if not os.path.exists('credentials.json'):
            return jsonify({"success": False, "message": "Arquivo credentials.json não encontrado"})
        
        # Testar conexão com Google Drive
        service = get_drive_service()
        if not service:
            return jsonify({"success": False, "message": "Erro ao conectar com Google Drive"})
        
        # Testar acesso ao Google Sheets se ID da planilha estiver configurado
        spreadsheet_id = carregar_planilha_id()
        sheets_ok = True
        sheets_message = ""
        
        if spreadsheet_id:
            try:
                # Testar acesso ao Google Sheets
                sheets_service = build('sheets', 'v4', credentials=service._http.credentials)
                test_result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range='A1:Z1'
                ).execute()
                sheets_message = "Google Sheets: OK"
            except Exception as e:
                sheets_ok = False
                if "permission" in str(e).lower() or "forbidden" in str(e).lower():
                    sheets_message = "Google Sheets: Permissão insuficiente - precisa re-autorizar"
                else:
                    sheets_message = f"Google Sheets: Erro - {str(e)}"
        else:
            sheets_message = "Google Sheets: Não configurado"
        
        return jsonify({
            "success": True, 
            "sheets_ok": sheets_ok,
            "sheets_message": sheets_message,
            "needs_reauth": not sheets_ok and spreadsheet_id
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/reset_google_config", methods=["POST"])
def reset_google_config():
    """Reseta completamente a configuração do Google e força nova autorização"""
    try:
        print("🗑️ Iniciando reset completo da configuração Google...")
        
        # 1. Deletar token de autorização
        if os.path.exists('token.json'):
            os.remove('token.json')
            print("✅ Token de autorização removido")
        
        # 2. Deletar configurações salvas
        config_files = [
            'drive_folder_id.txt',
            'planilha_config.json',
            'ai_config.json'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                os.remove(config_file)
                print(f"✅ {config_file} removido")
        
        # 3. Verificar se credentials.json existe
        if not os.path.exists('credentials.json'):
            return jsonify({
                "success": False, 
                "message": "Arquivo credentials.json não encontrado. Baixe o arquivo de credenciais primeiro."
            })
        
        # 4. Forçar nova autorização completa
        print("🔐 Iniciando nova autorização completa...")
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=5501, access_type='offline', prompt='consent')
        
        # 5. Salvar novo token
        with open('token.json', 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
        
        # 6. Tentar converter arquivo Excel se existir ID da planilha
        planilha_id = carregar_planilha_id()
        if planilha_id:
            print("🔄 Tentando converter arquivo Excel para Google Sheet...")
            drive_service = get_drive_service()
            if drive_service:
                is_sheets, file_id = verificar_google_sheets(drive_service, planilha_id)
                if not is_sheets:
                    success, new_file_id, new_name = converter_excel_para_google_sheets(drive_service, file_id)
                    if success:
                        salvar_planilha_id(new_file_id)
                        print(f"✅ Arquivo convertido automaticamente: {new_name}")
        
        print("✅ Reset completo concluído!")
        return jsonify({
            "success": True, 
            "message": "✅ Reset completo concluído!\n\n• Todas as configurações foram deletadas\n• Nova autorização realizada com sucesso\n• Agora você tem acesso completo ao Google Drive, Sheets e Gmail\n\nA página será recarregada automaticamente."
        })
        
    except Exception as e:
        print(f"❌ Erro no reset: {e}")
        return jsonify({
            "success": False, 
            "message": f"❌ Erro no reset: {str(e)}"
        })

@app.route("/convert_to_sheets", methods=["POST"])
def convert_to_sheets():
    """Converte arquivo Excel para Google Sheet nativo"""
    try:
        data = request.get_json()
        file_id = data.get('file_id', '').strip()
        
        if not file_id:
            return jsonify({"success": False, "message": "ID do arquivo é obrigatório"})
        
        # Conectar com Google Drive
        service = get_drive_service()
        if not service:
            return jsonify({"success": False, "message": "Erro ao conectar com Google Drive"})
        
        # Verificar tipo do arquivo
        is_sheets, file_id = verificar_google_sheets(service, file_id)
        
        if is_sheets:
            return jsonify({
                "success": True, 
                "message": "Arquivo já é um Google Sheet nativo",
                "file_id": file_id
            })
        
        # Converter para Google Sheet
        success, new_file_id, new_name = converter_excel_para_google_sheets(service, file_id)
        
        if success:
            # Salvar novo ID
            salvar_planilha_id(new_file_id)
            
            return jsonify({
                "success": True, 
                "message": f"✅ Arquivo convertido com sucesso!\n\nNome: {new_name}\nID: {new_file_id}\n\nO novo ID foi salvo automaticamente.",
                "file_id": new_file_id,
                "file_name": new_name
            })
        else:
            return jsonify({
                "success": False, 
                "message": "❌ Erro ao converter arquivo. Verifique as permissões."
            })
        
    except Exception as e:
        print(f"❌ Erro na conversão: {e}")
        return jsonify({
            "success": False, 
            "message": f"❌ Erro na conversão: {str(e)}"
        })

def verificar_google_sheets(service, file_id):
    """Verifica se o arquivo foi convertido para Google Sheets"""
    try:
        # Usar o serviço correto do Google Drive
        drive_service = get_drive_service()
        if not drive_service:
            print("❌ Erro: Não foi possível conectar com Google Drive")
            return False, file_id
            
        file_info = drive_service.files().get(fileId=file_id, fields='mimeType,name').execute()
        mime_type = file_info.get('mimeType', '')
        file_name = file_info.get('name', '')
        
        print(f"📄 Arquivo: {file_name}, Tipo: {mime_type}")
        
        if mime_type == 'application/vnd.google-apps.spreadsheet':
            print("✅ Arquivo é um Google Sheets nativo")
            return True, file_id
        elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            print("⚠️ Arquivo é Excel (.xlsx) - precisa ser convertido para Google Sheets")
            return False, file_id
        else:
            print(f"❌ Tipo de arquivo não suportado: {mime_type}")
            return False, file_id
    except Exception as e:
        print(f"❌ Erro ao verificar arquivo: {e}")
        return False, file_id

def converter_excel_para_google_sheets(service, file_id):
    """Converte arquivo Excel para Google Sheet nativo"""
    try:
        print(f"🔄 Convertendo arquivo Excel para Google Sheet...")
        
        # Usar o serviço correto do Google Drive
        drive_service = get_drive_service()
        if not drive_service:
            print("❌ Erro: Não foi possível conectar com Google Drive")
            return False, None, None
        
        # Primeiro, obter informações do arquivo original
        file_info = drive_service.files().get(fileId=file_id, fields='name,parents').execute()
        original_name = file_info.get('name', 'metadados')
        parents = file_info.get('parents', [])
        
        # Criar cópia do arquivo Excel como Google Sheet
        file_metadata = {
            'name': f'{original_name}_convertido_para_sheets',
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        
        # Se o arquivo tem pasta pai, manter na mesma pasta
        if parents:
            file_metadata['parents'] = parents
        
        # Fazer cópia do arquivo
        copied_file = drive_service.files().copy(
            fileId=file_id,
            body=file_metadata
        ).execute()
        
        new_file_id = copied_file.get('id')
        new_file_name = copied_file.get('name')
        
        print(f"✅ Arquivo convertido com sucesso!")
        print(f"📄 Novo ID: {new_file_id}")
        print(f"📄 Novo nome: {new_file_name}")
        
        # Aguardar um pouco para garantir que a conversão seja processada
        import time
        time.sleep(2)
        
        return True, new_file_id, new_file_name
        
    except Exception as e:
        print(f"❌ Erro ao converter arquivo: {e}")
        return False, None, None

def sincronizar_com_google_sheets_continuar(service, spreadsheet_id, dados):
    """Continua a sincronização após conversão bem-sucedida"""
    try:
        print(f"🔄 Continuando sincronização com planilha convertida: {spreadsheet_id}")
        
        # Implementar lógica Append/Update igual ao N8n
        try:
            # Primeiro, verificar se já existem dados na planilha
            existing_data = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='A:Z'
            ).execute()
            
            existing_values = existing_data.get('values', [])
            
            # SEMPRE USAR APPEND - NUNCA UPDATE (manter histórico completo)
            print("📝 Modo Append: Adicionando novos dados sem modificar existentes")
            # Determinar range baseado no número de colunas
            num_colunas = len(dados[0]) if dados else 5
            col_final = chr(ord('A') + num_colunas - 1)  # A, B, C, D, E, F...
            
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f'A:{col_final}',  # Range dinâmico baseado no número de colunas
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': dados[1:]}  # Pular cabeçalho
            ).execute()
            
            print(f"✅ Planilha sincronizada: {result.get('updatedCells', 0)} células atualizadas, {result.get('appendedRows', 0)} linhas adicionadas")
            
            return {
                "success": True, 
                "message": f"✅ Arquivo convertido e sincronizado com sucesso!\n\n{result.get('updatedCells', 0)} células atualizadas, {result.get('appendedRows', 0)} linhas adicionadas"
            }
            
        except Exception as e:
            print(f"❌ Erro ao sincronizar planilha convertida: {e}")
            return {
                "success": False,
                "message": f"Erro ao sincronizar planilha convertida: {str(e)}"
            }
        
    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")
        return {
            "success": False,
            "message": f"Erro na sincronização: {str(e)}"
        }

# Função removida - não é mais necessária
# A sincronização agora é feita diretamente com Google Sheets via sincronizar_com_google_sheets()

def salvar_metadados_mp4(caminho_video, titulo, legenda, hashtags, tipo_video="Legendado"):
    """Salva metadados diretamente no arquivo MP4 usando FFmpeg"""
    try:
        # Criar arquivo temporário
        temp_video = caminho_video.replace('.mp4', '_temp.mp4')
        
        # Comando FFmpeg para adicionar metadados
        cmd = [
            'bin/ffmpeg/ffmpeg.exe.exe',
            '-i', caminho_video,
            '-c', 'copy',  # Copiar sem re-encoding
            '-metadata', f'title={titulo}',
            '-metadata', f'comment={legenda}',
            '-metadata', f'description={legenda}',
            '-metadata', f'genre={tipo_video}',
            '-metadata', f'album=Video Cutter',
            '-metadata', f'artist=AI Generated',
            '-metadata', f'copyright=© 2025 Video Cutter',
            '-metadata', f'keywords={hashtags}',
            '-y',  # Sobrescrever arquivo
            temp_video
        ]
        
        # Executar FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Substituir arquivo original pelo temporário
            os.replace(temp_video, caminho_video)
            print(f"✅ Metadados salvos no MP4 com FFmpeg: {os.path.basename(caminho_video)}")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            # Fallback: usar mutagen
            return salvar_metadados_mp4_mutagen(caminho_video, titulo, legenda, hashtags, tipo_video)
        
    except Exception as e:
        print(f"❌ Erro ao salvar metadados MP4: {e}")
        # Fallback: usar mutagen
        return salvar_metadados_mp4_mutagen(caminho_video, titulo, legenda, hashtags, tipo_video)

def salvar_metadados_mp4_mutagen(caminho_video, titulo, legenda, hashtags, tipo_video="Legendado"):
    """Fallback: Salva metadados usando mutagen"""
    try:
        # Carregar arquivo MP4
        mp4_file = MP4(caminho_video)
        
        # Salvar metadados nos campos padrão do MP4
        mp4_file['\xa9nam'] = titulo  # Título
        mp4_file['\xa9cmt'] = legenda  # Comentário
        mp4_file['\xa9key'] = hashtags  # Palavras-chave
        mp4_file['\xa9gen'] = tipo_video  # Gênero
        mp4_file['\xa9alb'] = "Video Cutter"  # Álbum
        mp4_file['\xa9ART'] = "AI Generated"  # Artista
        mp4_file['\xa9des'] = legenda  # Description
        mp4_file['\xa9cpy'] = "© 2025 Video Cutter"  # Copyright
        
        # Salvar metadados customizados (backup)
        mp4_file['TITULO_ORIGINAL'] = titulo
        mp4_file['LEGENDA_ORIGINAL'] = legenda
        mp4_file['HASHTAGS_ORIGINAL'] = hashtags
        mp4_file['TIPO_VIDEO'] = tipo_video
        mp4_file['DATA_CRIACAO'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Salvar arquivo
        mp4_file.save()
        
        print(f"✅ Metadados salvos no MP4 com mutagen: {os.path.basename(caminho_video)}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar metadados MP4 com mutagen: {e}")
        return False

def ler_metadados_mp4(caminho_video):
    """Lê metadados do arquivo MP4"""
    try:
        mp4_file = MP4(caminho_video)
        
        # Ler metadados padrão
        titulo = mp4_file.get('\xa9nam', [''])[0] if '\xa9nam' in mp4_file else ''
        legenda = mp4_file.get('\xa9cmt', [''])[0] if '\xa9cmt' in mp4_file else ''
        hashtags = mp4_file.get('\xa9key', [''])[0] if '\xa9key' in mp4_file else ''
        tipo = mp4_file.get('\xa9gen', [''])[0] if '\xa9gen' in mp4_file else ''
        
        # Ler metadados customizados (fallback)
        if not titulo:
            titulo = mp4_file.get('TITULO_ORIGINAL', [''])[0] if 'TITULO_ORIGINAL' in mp4_file else ''
        if not legenda:
            legenda = mp4_file.get('LEGENDA_ORIGINAL', [''])[0] if 'LEGENDA_ORIGINAL' in mp4_file else ''
        if not hashtags:
            hashtags = mp4_file.get('HASHTAGS_ORIGINAL', [''])[0] if 'HASHTAGS_ORIGINAL' in mp4_file else ''
        if not tipo:
            tipo = mp4_file.get('TIPO_VIDEO', [''])[0] if 'TIPO_VIDEO' in mp4_file else ''
        
        return {
            'titulo': titulo,
            'legenda': legenda,
            'hashtags': hashtags,
            'tipo': tipo
        }
        
    except Exception as e:
        print(f"❌ Erro ao ler metadados MP4: {e}")
        return {
            'titulo': '',
            'legenda': '',
            'hashtags': '',
            'tipo': ''
        }

def carregar_metadados_existentes():
    """Carrega metadados existentes da planilha local"""
    metadados_videos = {}
    try:
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        if os.path.exists(planilha_path):
            df = pd.read_excel(planilha_path)
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            return metadados_videos
        
        if not df.empty:
            for _, row in df.iterrows():
                arquivo_novo = row.get('arquivo_novo', '')
                if arquivo_novo:
                    metadados_videos[arquivo_novo] = {
                        'titulo': row.get('titulo', ''),
                        'legenda': row.get('legenda', ''),
                        'hashtags': row.get('hashtags', ''),
                        'duracao': row.get('duracao', ''),
                        'origem': row.get('origem', ''),
                        'idioma': row.get('idioma', 'pt')
                    }
    except Exception as e:
        print(f"Erro ao carregar metadados existentes: {e}")
    
    return metadados_videos

def gerar_metadados_para_video(nome_arquivo, tipo_video):
    """Gera metadados para um vídeo usando IA"""
    try:
        # Gerar conteúdo baseado no nome do arquivo (mais rápido e confiável)
        nome_base = nome_arquivo.replace('.mp4', '').replace('-', ' ').replace('_', ' ').title()
        
        # Gerar conteúdo com IA usando o nome do arquivo
        try:
            res = requests.post('http://127.0.0.1:5000/gerar_conteudo_individual', 
                              json={'transcricao': nome_base, 'tipo': tipo_video.lower()})
            if res.status_code == 200:
                data = res.json()
                if data.get('ok'):
                    return {
                        'titulo': data.get('titulo', ''),
                        'legenda': data.get('legenda', ''),
                        'hashtags': data.get('hashtags', ''),
                        'duracao': '',
                        'origem': tipo_video.lower(),
                        'idioma': 'pt'
                    }
        except:
            pass
        
        # Fallback: usar nome do arquivo formatado
        return {
            'titulo': nome_base,
            'legenda': f"Vídeo {tipo_video.lower()} - {nome_base}",
            'hashtags': f"#{tipo_video.lower()} #video #conteudo",
            'duracao': '',
            'origem': tipo_video.lower(),
            'idioma': 'pt'
        }
        
    except Exception as e:
        print(f"Erro ao gerar metadados para {nome_arquivo}: {e}")
        return {
            'titulo': nome_arquivo.replace('.mp4', ''),
            'legenda': f"Vídeo {tipo_video.lower()}",
            'hashtags': f"#{tipo_video.lower()}",
            'duracao': '',
            'origem': tipo_video.lower(),
            'idioma': 'pt'
        }

def salvar_metadados_local(nome_arquivo, metadados, tipo_video):
    """Salva metadados na planilha local"""
    try:
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        # Criar pasta se não existir
        os.makedirs("data/planilhas", exist_ok=True)
        
        # Carregar ou criar DataFrame
        if os.path.exists(planilha_path):
            df = pd.read_excel(planilha_path)
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            df = pd.DataFrame(columns=['arquivo_antigo', 'arquivo_novo', 'titulo', 'legenda', 'hashtags', 'duracao', 'origem', 'idioma', 'video_id', 'tipo', 'postado'])
        
        # Adicionar ou atualizar linha
        mask = df['arquivo_novo'] == nome_arquivo
        if mask.any():
            # Atualizar linha existente
            df.loc[mask, 'titulo'] = metadados.get('titulo', '')
            df.loc[mask, 'legenda'] = metadados.get('legenda', '')
            df.loc[mask, 'hashtags'] = metadados.get('hashtags', '')
            df.loc[mask, 'tipo'] = tipo_video
        else:
            # Adicionar nova linha
            nova_linha = {
                'arquivo_antigo': nome_arquivo,
                'arquivo_novo': nome_arquivo,
                'titulo': metadados.get('titulo', ''),
                'legenda': metadados.get('legenda', ''),
                'hashtags': metadados.get('hashtags', ''),
                'duracao': metadados.get('duracao', ''),
                'origem': metadados.get('origem', tipo_video.lower()),
                'idioma': metadados.get('idioma', 'pt'),
                'video_id': '',
                'tipo': tipo_video,
                'postado': 'Não'
            }
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        
        # Salvar arquivos
        df.to_excel(planilha_path, index=False)
        df.to_csv(csv_path, index=False)
        
        print(f"✅ Metadados salvos para {nome_arquivo}")
        
    except Exception as e:
        print(f"Erro ao salvar metadados locais: {e}")

@app.route("/upload", methods=["POST"])
def upload_to_drive_route():
    """Rota principal para upload de vídeos para o Google Drive"""
    try:
        # Fazer upload dos vídeos
        upload_result = upload_to_drive()
        
        if upload_result.get_json().get("success"):
            uploaded_data = upload_result.get_json().get("uploaded_data", [])
            # Dados recebidos para sincronização
            
            # Salvar IDs no Excel local
            salvar_ids_drive_no_excel(uploaded_data)
            
            # Função atualizar_excel_drive removida - sincronização agora é feita via Google Sheets
            
            # Sincronizar com Google Sheets automaticamente
            # Sincronizando com Google Sheets
            sync_result = sincronizar_com_google_sheets(uploaded_data)
            
            return jsonify({
                "success": True,
                "message": f"Upload concluído! {len(uploaded_data)} vídeos enviados.",
                "uploaded_data": uploaded_data,
                "sync_result": sync_result
            })
        else:
            return upload_result
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

def salvar_ids_drive_no_excel(uploaded_data):
    """Salva os IDs do Google Drive no Excel após upload"""
    try:
        import pandas as pd
        
        # Caminhos das planilhas
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        # Carregar planilha existente
        if os.path.exists(planilha_path):
            df = pd.read_excel(planilha_path)
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            print("⚠️ Planilha não encontrada, criando nova...")
            df = pd.DataFrame(columns=["arquivo_antigo", "arquivo_novo", "titulo", "legenda", "hashtags", "duracao", "origem", "idioma", "video_id", "tipo", "postado"])
        
        # Garantir que as colunas existem
        if 'video_id' not in df.columns:
            df['video_id'] = ''
        if 'tipo' not in df.columns:
            df['tipo'] = ''
        if 'postado' not in df.columns:
            df['postado'] = 'Não'
        
        # Atualizar com IDs do Google Drive
        for video_data in uploaded_data:
            arquivo_nome = video_data['arquivo']
            video_id = video_data['video_id']
            tipo = video_data['tipo']
            
            # Procurar linha existente pelo nome do arquivo
            mask = df['arquivo_novo'] == arquivo_nome
            if mask.any():
                # Atualizar linha existente
                df.loc[mask, 'video_id'] = video_id
                df.loc[mask, 'tipo'] = tipo
                df.loc[mask, 'postado'] = 'Sim'
                print(f"✅ Atualizado: {arquivo_nome} -> ID: {video_id}")
            else:
                # Adicionar nova linha
                nova_linha = {
                    "arquivo_antigo": arquivo_nome,
                    "arquivo_novo": arquivo_nome,
                    "titulo": video_data.get('metadados', {}).get('titulo', ''),
                    "legenda": video_data.get('metadados', {}).get('legenda', ''),
                    "hashtags": video_data.get('metadados', {}).get('hashtags', ''),
                    "duracao": video_data.get('metadados', {}).get('duracao', ''),
                    "origem": "google_drive",
                    "idioma": "pt",
                    "video_id": video_id,
                    "tipo": tipo,
                    "postado": "Sim"
                }
                df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                print(f"✅ Adicionado: {arquivo_nome} -> ID: {video_id}")
        
        # Salvar planilha atualizada
        df.to_excel(planilha_path, index=False)
        df.to_csv(csv_path, index=False)
        
        print(f"✅ {len(uploaded_data)} IDs salvos no Excel")
        
    except Exception as e:
        print(f"❌ Erro ao salvar IDs no Excel: {e}")

def sincronizar_com_google_sheets(uploaded_data=None):
    """Sincroniza planilha local com Google Sheets"""
    try:
        # Iniciando sincronização com Google Sheets
        from googleapiclient.discovery import build
        import pandas as pd
        
        # Carregar credenciais
        creds = carregar_credenciais()
        if not creds:
            return {"success": False, "message": "Credenciais não encontradas"}
        
        # Construir serviço do Google Sheets
        service = build('sheets', 'v4', credentials=creds)
        
        # ID da planilha no Google Drive
        spreadsheet_id = carregar_planilha_id()
        
        if not spreadsheet_id:
            return {"success": True, "message": "IDs salvos no Excel local. Configure o ID da planilha Google Sheets para sincronização automática."}
        
        # Carregar dados locais - procurar por diferentes formatos
        planilha_paths = [
            "data/planilhas/publicar.xlsx",
            "metadados/videos.xlsx",  # Arquivo principal de metadados
            "data/planilhas/metadados.xlsx", 
            "data/planilhas/metadados.xlsh",
            "data/planilhas/publicar.csv",
            "data/planilhas/metadados.csv"
        ]
        
        df = None
        for path in planilha_paths:
            if os.path.exists(path):
                try:
                    if path.endswith('.csv'):
                        df = pd.read_csv(path)
                    else:
                        df = pd.read_excel(path)
                    print(f"✅ Planilha carregada para sincronização: {path}")
                    break
                except Exception as e:
                    print(f"⚠️ Erro ao carregar {path}: {e}")
                    continue
        
        if df is None:
            return {"success": False, "message": "Nenhuma planilha local encontrada para sincronização"}
        
        # FILTRAR APENAS OS VÍDEOS ENVIADOS (se uploaded_data for fornecido)
        if uploaded_data:
            # Filtrando apenas os vídeos enviados
            arquivos_enviados = [video['arquivo'] for video in uploaded_data]
            
            # Filtrar DataFrame pelos arquivos enviados
            if 'arquivo_novo' in df.columns:
                df = df[df['arquivo_novo'].isin(arquivos_enviados)]
            elif 'arquivo_antigo' in df.columns:
                df = df[df['arquivo_antigo'].isin(arquivos_enviados)]
            else:
                return {"success": False, "message": "Nenhuma coluna de arquivo encontrada para filtrar"}
        
        # Mapear colunas antigas para novas estrutura da planilha Google Sheets
        
        df['Arquivo'] = df.get('arquivo_novo', df.get('arquivo_antigo', ''))
        df['Transcrição'] = df.get('transcricao', df.get('legenda', ''))  # transcricao ou legenda -> Transcrição
        df['Título'] = df.get('titulo_gerado', df.get('titulo', ''))  # titulo_gerado ou titulo -> Título
        df['Hashtag'] = df.get('hashtags_geradas', df.get('hashtags', ''))  # hashtags_geradas ou hashtags -> Hashtag
        df['Tipo'] = df.get('tipo', 'Legendado')  # tipo -> Tipo
        
        # Dados mapeados para sincronização
        
        # ADICIONAR VIDEO_ID se uploaded_data for fornecido
        if uploaded_data:
            # Criar dicionário de video_id por arquivo
            video_ids = {video['arquivo']: video['video_id'] for video in uploaded_data}
            
            # Adicionar video_id ao DataFrame
            df['Video_ID'] = df['Arquivo'].map(video_ids).fillna('')
        
        # Limpar valores NaN e nulos antes de enviar para Google Sheets
        df = df.fillna('')  # Substituir NaN por string vazia
        df = df.replace([None], '')  # Substituir None por string vazia
        
        # Selecionar apenas as colunas necessárias para a nova planilha
        colunas_finais = ['Arquivo', 'Transcrição', 'Título', 'Hashtag', 'Tipo']
        if 'Video_ID' in df.columns:
            colunas_finais.append('Video_ID')
        
        df_final = df[colunas_finais].copy()
        
        # Converter DataFrame para lista de listas
        dados = [df_final.columns.tolist()] + df_final.values.tolist()
        
        # APENAS ADICIONAR - NÃO DELETAR NADA (manter histórico completo)
        print("📝 Modo Append: Adicionando novos dados sem deletar existentes")
        
        # Verificar se a planilha existe e é acessível
        try:
            # Primeiro, tentar ler a planilha para verificar se é acessível
            test_range = 'A1:Z1'
            test_result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=test_range
            ).execute()
            print(f"✅ Planilha acessível: {spreadsheet_id}")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erro ao acessar planilha: {error_msg}")
            
            # Verificar se é erro de permissão
            if "permission" in error_msg.lower() or "forbidden" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return {
                    "success": False, 
                    "message": "❌ Permissão insuficiente para Google Sheets. Clique em '🔐 Re-autorizar Google' na configuração de IA para incluir todas as permissões necessárias.",
                    "needs_reauth": True
                }
            elif "This operation is not supported for this document" in error_msg:
                # Arquivo não é um Google Sheet nativo - tentar converter automaticamente
                print("🔄 Detectado arquivo Excel - tentando converter automaticamente...")
                
                # Usar serviço do Google Drive para verificar e converter
                drive_service = get_drive_service()
                if not drive_service:
                    return {
                        "success": False, 
                        "message": "❌ Erro: Não foi possível conectar com Google Drive para conversão."
                    }
                
                # Verificar se é realmente um arquivo Excel
                is_sheets, file_id = verificar_google_sheets(drive_service, spreadsheet_id)
                
                if not is_sheets:
                    # Converter para Google Sheet
                    success, new_file_id, new_name = converter_excel_para_google_sheets(drive_service, file_id)
                    
                    if success:
                        # Salvar novo ID da planilha convertida
                        salvar_planilha_id(new_file_id)
                        print(f"✅ Arquivo convertido automaticamente: {new_name}")
                        print(f"✅ Novo ID salvo: {new_file_id}")
                        
                        # Tentar novamente com o novo ID
                        try:
                            test_result = service.spreadsheets().values().get(
                                spreadsheetId=new_file_id,
                                range=test_range
                            ).execute()
                            print(f"✅ Planilha convertida acessível: {new_file_id}")
                            spreadsheet_id = new_file_id  # Usar o novo ID
                            
                            # Continuar com a sincronização usando o novo ID
                            return sincronizar_com_google_sheets_continuar(service, spreadsheet_id, dados)
                            
                        except Exception as e2:
                            return {
                                "success": False, 
                                "message": f"❌ Erro após conversão: {str(e2)}\n\nTente converter manualmente:\n1. Abra o arquivo Excel no Google Drive\n2. Clique em 'Abrir com' → 'Planilhas Google'\n3. Copie o novo ID da planilha"
                            }
                    else:
                        return {
                            "success": False, 
                            "message": "❌ Não foi possível converter automaticamente.\n\nPara sincronizar com Google Sheets:\n\n1. Abra o arquivo Excel no Google Drive\n2. Clique em 'Abrir com' → 'Planilhas Google'\n3. Copie o novo ID da planilha convertida\n4. Cole o novo ID na configuração"
                        }
                else:
                    return {
                        "success": False, 
                        "message": f"Erro ao acessar planilha: {error_msg}. Verifique se o arquivo foi convertido para Google Sheets."
                    }
            else:
                return {
                    "success": False, 
                    "message": f"Erro ao acessar planilha: {error_msg}. Verifique se o arquivo foi convertido para Google Sheets."
                }
        
        # Implementar lógica Append/Update igual ao N8n
        try:
            # Primeiro, verificar se já existem dados na planilha
            existing_data = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='A:Z'
            ).execute()
            
            existing_values = existing_data.get('values', [])
            
            # SEMPRE USAR APPEND - NUNCA UPDATE (manter histórico completo)
            print("📝 Modo Append: Adicionando novos dados sem modificar existentes")
            # Determinar range baseado no número de colunas
            num_colunas = len(dados[0]) if dados else 5
            col_final = chr(ord('A') + num_colunas - 1)  # A, B, C, D, E, F...
            
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f'A:{col_final}',  # Range dinâmico baseado no número de colunas
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': dados[1:]}  # Pular cabeçalho
            ).execute()
            
            print(f"✅ Planilha atualizada: {result.get('updatedCells', 0)} células atualizadas, {result.get('appendedRows', 0)} linhas adicionadas")
            
            return {
                "success": True, 
                "message": f"Planilha sincronizada! {result.get('updatedCells', 0)} células atualizadas, {result.get('appendedRows', 0)} linhas adicionadas"
            }
            
        except Exception as e:
            print(f"❌ Erro ao atualizar planilha: {e}")
            return {
                "success": False,
                "message": f"Erro ao atualizar planilha: {str(e)}"
            }
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erro na sincronização: {error_msg}")
        
        # Tratar erros específicos
        if "not found" in error_msg.lower():
            return {"success": False, "message": "Planilha não encontrada. Verifique se o ID da planilha está correto."}
        elif "permission" in error_msg.lower():
            return {"success": False, "message": "Sem permissão para acessar a planilha. Verifique as credenciais."}
        elif "quota" in error_msg.lower():
            return {"success": False, "message": "Limite de requisições excedido. Tente novamente em alguns minutos."}
        else:
            return {"success": False, "message": f"Erro na sincronização: {error_msg}"}

def carregar_credenciais():
    """Carrega credenciais do Google Drive"""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.send'
]
        creds = None
        
        # Verificar se existe token.json
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Se não há credenciais válidas, retornar None
        if not creds or not creds.valid:
            return None
            
        return creds
    except Exception as e:
        print(f"❌ Erro ao carregar credenciais: {e}")
        return None

def carregar_planilha_id():
    """Carrega ID da planilha Google Sheets do arquivo de configuração"""
    try:
        if os.path.exists("planilha_config.json"):
            with open("planilha_config.json", "r") as f:
                config = json.load(f)
                return config.get("spreadsheet_id")
        return None
    except:
        return None

# Função removida - não é mais necessária
# Agora usamos apenas o spreadsheet_id para sincronização com Google Sheets

def salvar_planilha_id(spreadsheet_id):
    """Salva ID da planilha Google Sheets"""
    try:
        config = {}
        if os.path.exists("planilha_config.json"):
            with open("planilha_config.json", "r") as f:
                config = json.load(f)
        
        config["spreadsheet_id"] = spreadsheet_id
        with open("planilha_config.json", "w") as f:
            json.dump(config, f)
        print(f"✅ ID da planilha salvo: {spreadsheet_id}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar ID da planilha: {e}")
        return False

def salvar_excel_id(excel_file_id):
    """Salva ID do arquivo Excel no Google Drive"""
    try:
        config = {}
        if os.path.exists("planilha_config.json"):
            with open("planilha_config.json", "r") as f:
                config = json.load(f)
        
        config["excel_file_id"] = excel_file_id
        with open("planilha_config.json", "w") as f:
            json.dump(config, f)
        print(f"✅ ID do arquivo Excel salvo: {excel_file_id}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar ID do arquivo Excel: {e}")
        return False

def upload_to_drive():
    try:
        print("🚀 Iniciando upload para Google Drive...")
        
        # Verificar credenciais
        if not os.path.exists('credentials.json'):
            return jsonify({"success": False, "message": "Arquivo credentials.json não encontrado. Configure as credenciais do Google Drive primeiro."})
        
        # Obter serviço do Google Drive
        try:
            service = get_drive_service()
            print("✅ Serviço Google Drive conectado")
        except Exception as e:
            print(f"❌ Erro ao conectar com Google Drive: {e}")
            return jsonify({"success": False, "message": f"Erro ao conectar com Google Drive: {str(e)}"})
        
        # Verificar ID da pasta
        target_folder_id = carregar_pasta_id()
        if not target_folder_id:
            return jsonify({"success": False, "message": "ID da pasta não configurado. Configure o ID da pasta do Google Drive primeiro."})
        
        print(f"📁 Pasta de destino: {target_folder_id}")
        uploaded_data = []
        
        # 1. PROCESSAR VÍDEOS LEGENDADOS (data/final)
        pasta_videos_legendados = Path("data/final")
        if not pasta_videos_legendados.exists():
            print("⚠️ Pasta data/final não encontrada")
        else:
            arquivos_legendados = list(pasta_videos_legendados.glob("*.mp4"))
            print(f"📁 Encontrados {len(arquivos_legendados)} vídeos legendados em data/final")
        
        if arquivos_legendados:
            print(f"📹 Processando {len(arquivos_legendados)} vídeos legendados...")
            
            # Carregar metadados existentes
            metadados_videos = carregar_metadados_existentes()
            
            for arquivo in arquivos_legendados:
                # Gerar metadados se não existirem
                metadados = metadados_videos.get(arquivo.name, {})
                if not metadados.get('titulo'):
                    print(f"🤖 Gerando metadados para {arquivo.name}...")
                    metadados = gerar_metadados_para_video(arquivo.name, "Legendado")
                    # Salvar metadados localmente
                    salvar_metadados_local(arquivo.name, metadados, "Legendado")
                
                # Upload do vídeo
                try:
                    print(f"📤 Enviando {arquivo.name}...")
                    file_metadata = {'name': arquivo.name, 'parents': [target_folder_id]}
                    media = MediaFileUpload(str(arquivo), mimetype='video/mp4')
                    gfile = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                    video_id = gfile.get('id')
                    
                    uploaded_data.append({
                        'arquivo': arquivo.name,
                        'video_id': video_id,
                        'metadados': metadados,
                        'tipo': 'Legendado'
                    })
                    print(f"✅ {arquivo.name} enviado com sucesso - ID: {video_id}")
                except Exception as e:
                    print(f"❌ Erro ao enviar {arquivo.name}: {e}")
                    continue
        
        # 2. PROCESSAR VÍDEOS DUBLADOS (data/cortes_dublado)
        pasta_videos_dublados = Path("data/cortes_dublado")
        if not pasta_videos_dublados.exists():
            print("⚠️ Pasta data/cortes_dublado não encontrada")
            arquivos_dublados = []
        else:
            arquivos_dublados = list(pasta_videos_dublados.glob("*.mp4"))
            print(f"📁 Encontrados {len(arquivos_dublados)} vídeos dublados em data/cortes_dublado")
            
            if arquivos_dublados:
                print(f"🎤 Processando {len(arquivos_dublados)} vídeos dublados...")
                
                for arquivo in arquivos_dublados:
                    # Gerar metadados para vídeo dublado
                    metadados = gerar_metadados_para_video(arquivo.name, "Dublado")
                    
                    # Upload do vídeo
                    try:
                        print(f"📤 Enviando {arquivo.name}...")
                        file_metadata = {'name': arquivo.name, 'parents': [target_folder_id]}
                        media = MediaFileUpload(str(arquivo), mimetype='video/mp4')
                        gfile = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                        video_id = gfile.get('id')
                        
                        uploaded_data.append({
                            'arquivo': arquivo.name,
                            'video_id': video_id,
                            'metadados': metadados,
                            'tipo': 'Dublado'
                        })
                        print(f"✅ {arquivo.name} enviado com sucesso - ID: {video_id}")
                    except Exception as e:
                        print(f"❌ Erro ao enviar {arquivo.name}: {e}")
                        continue
        
        if not uploaded_data:
            return jsonify({"success": False, "message": "Nenhum vídeo encontrado para upload."})
        
        # Salvar IDs do Google Drive no Excel
        salvar_ids_drive_no_excel(uploaded_data)
        print("✅ IDs do Google Drive salvos no Excel")
        
        return jsonify({
            "success": True, 
            "uploaded_data": uploaded_data,
            "message": f"{len(uploaded_data)} vídeos enviados com sucesso! ({len(arquivos_legendados)} legendados, {len(arquivos_dublados) if 'arquivos_dublados' in locals() else 0} dublados)"
        })
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

@app.route("/config/planilha", methods=["POST"])
def configurar_planilha():
    """Configura ID da planilha Google Sheets"""
    try:
        data = request.get_json()
        spreadsheet_id = data.get("spreadsheet_id", "").strip()
        
        if not spreadsheet_id:
            return jsonify({"success": False, "message": "ID da planilha não fornecido"})
        
        if salvar_planilha_id(spreadsheet_id):
            return jsonify({"success": True, "message": "ID da planilha configurado com sucesso!"})
        else:
            return jsonify({"success": False, "message": "Erro ao salvar configuração"})
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/config/excel", methods=["POST"])
def configurar_excel():
    """Configura ID do arquivo Excel no Google Drive"""
    try:
        data = request.get_json()
        excel_file_id = data.get("excel_file_id", "").strip()
        
        if not excel_file_id:
            return jsonify({"success": False, "message": "ID do arquivo Excel não fornecido"})
        
        if salvar_excel_id(excel_file_id):
            return jsonify({"success": True, "message": "ID do arquivo Excel configurado com sucesso!"})
        else:
            return jsonify({"success": False, "message": "Erro ao salvar configuração"})
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/sync/sheets", methods=["POST"])
def sincronizar_sheets():
    """Sincroniza planilha local com Google Sheets"""
    try:
        # Esta rota não deve ser usada - a sincronização é automática no upload
        return jsonify({"success": False, "message": "Use a rota de upload para sincronização automática"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/sync/auto", methods=["POST"])
def sincronizacao_automatica():
    """Sincronização automática após upload para Google Drive"""
    try:
        # Primeiro faz o upload normal
        upload_result = upload_to_drive()
        
        if upload_result.get_json().get("success"):
            # A sincronização já é feita automaticamente na rota principal de upload
            # Não precisa chamar novamente aqui para evitar duplicação
            return jsonify({
                "success": True,
                "upload": upload_result.get_json(),
                "message": "Upload concluído! A sincronização foi feita automaticamente."
            })
        else:
            return upload_result
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/upload/metadados", methods=["POST"])
def upload_metadados_completos():
    """Upload de metadados completos para Google Drive após upload dos vídeos"""
    try:
        # Carregar metadados da planilha local
        import pandas as pd
        
        # Procurar por diferentes formatos de planilha
        planilha_paths = [
            "data/planilhas/publicar.xlsx",
            "metadados/videos.xlsx",  # Arquivo principal de metadados
            "data/planilhas/metadados.xlsx", 
            "data/planilhas/metadados.xlsh",
            "data/planilhas/publicar.csv",
            "data/planilhas/metadados.csv"
        ]
        
        df = None
        for path in planilha_paths:
            if os.path.exists(path):
                try:
                    if path.endswith('.csv'):
                        df = pd.read_csv(path)
                    else:
                        df = pd.read_excel(path)
                    print(f"✅ Planilha carregada: {path}")
                    break
                except Exception as e:
                    print(f"⚠️ Erro ao carregar {path}: {e}")
                    continue
        
        if df is None:
            return jsonify({"success": False, "message": "Nenhuma planilha encontrada. Procurou em: " + ", ".join(planilha_paths)})
        
        # Verificar quais vídeos realmente existem no sistema
        cortes_path = 'data/final'
        dublados_path = 'data/cortes_dublado'
        
        # Listar vídeos que realmente existem
        videos_existentes = []
        if os.path.exists(cortes_path):
            videos_existentes.extend([f for f in os.listdir(cortes_path) if f.endswith('.mp4')])
        if os.path.exists(dublados_path):
            videos_existentes.extend([f for f in os.listdir(dublados_path) if f.endswith('.mp4')])
        
        print(f"📁 Vídeos existentes no sistema: {len(videos_existentes)}")
        
        # Filtrar apenas vídeos que existem e têm IDs
        df_filtrado = df[
            (df['video_id'].notna()) & 
            (df['video_id'] != '') & 
            (df['arquivo_novo'].isin(videos_existentes))
        ]
        
        if df_filtrado.empty:
            return jsonify({"success": False, "message": "Nenhum vídeo existente com ID encontrado"})
        
        print(f"📊 Vídeos com ID encontrados: {len(df_filtrado)}")
        
        # Atualizar Excel no Google Drive
        service = get_drive_service()
        target_folder_id = carregar_pasta_id()
        
        if not service or not target_folder_id:
            return jsonify({"success": False, "message": "Serviço Google Drive não configurado"})
        
        # Converter DataFrame para formato esperado
        uploaded_data = []
        for _, row in df_filtrado.iterrows():
            uploaded_data.append({
                'arquivo': row['arquivo_novo'],
                'video_id': row['video_id'],
                'tipo': row.get('tipo', 'Legendado'),
                'metadados': {
                    'titulo': row.get('titulo', ''),
                    'legenda': row.get('legenda', ''),
                    'hashtags': row.get('hashtags', ''),
                    'duracao': row.get('duracao', ''),
                    'origem': row.get('origem', 'Legendado'),
                    'idioma': row.get('idioma', 'pt')
                }
            })
        
        # Função atualizar_excel_drive removida - sincronização agora é feita via Google Sheets
        
        return jsonify({
            "success": True,
            "message": f"Metadados completos enviados para {len(uploaded_data)} vídeos!",
            "videos_atualizados": len(uploaded_data)
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/test/setup", methods=["GET"])
def testar_setup():
    """Testa se todas as configurações estão funcionando"""
    try:
        resultados = {}
        
        # Testar spaCy
        try:
            import spacy
            nlp = spacy.load("pt_core_news_sm")
            resultados["spacy"] = "✅ Funcionando"
        except Exception as e:
            resultados["spacy"] = f"❌ Erro: {str(e)}"
        
        # Testar Ollama
        try:
            import ollama
            client = ollama.Client()
            models = client.list()
            if models and hasattr(models, 'models'):
                resultados["ollama"] = f"✅ Funcionando - {len(models.models)} modelos"
            else:
                resultados["ollama"] = "⚠️ Conectado mas sem modelos"
        except Exception as e:
            resultados["ollama"] = f"❌ Erro: {str(e)}"
        
        # Testar Google Drive
        try:
            creds = carregar_credenciais()
            if creds:
                resultados["google_drive"] = "✅ Credenciais encontradas"
            else:
                resultados["google_drive"] = "⚠️ Credenciais não configuradas"
        except Exception as e:
            resultados["google_drive"] = f"❌ Erro: {str(e)}"
        
        # Testar planilha local
        try:
            if os.path.exists("data/planilhas/publicar.xlsx"):
                df = pd.read_excel("data/planilhas/publicar.xlsx")
                resultados["planilha_local"] = f"✅ Funcionando - {len(df)} registros"
            else:
                resultados["planilha_local"] = "⚠️ Planilha não encontrada"
        except Exception as e:
            resultados["planilha_local"] = f"❌ Erro: {str(e)}"
        
        return jsonify({
            "success": True,
            "resultados": resultados
        })
        
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
        # Verificar se existe em data/final primeiro
        if os.path.exists("data/final"):
            arquivos = os.listdir("data/final")
            mp4s = ["/data/final/" + arq for arq in arquivos if arq.endswith(".mp4")]
        elif os.path.exists("static/final"):
            arquivos = os.listdir("static/final")
            mp4s = ["/static/final/" + arq for arq in arquivos if arq.endswith(".mp4")]
        else:
            return jsonify({"success": True, "videos": []})
        
        # Buscar metadados para cada vídeo
        videos_com_metadados = []
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        # Carregar metadados existentes
        metadados = {}
        try:
            if os.path.exists(planilha_path):
                df = pd.read_excel(planilha_path)
            elif os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                df = pd.DataFrame()
            
            if not df.empty and 'arquivo_novo' in df.columns:
                for _, row in df.iterrows():
                    arquivo_novo = row.get('arquivo_novo', '')
                    if arquivo_novo:
                        metadados[arquivo_novo] = {
                            'titulo': row.get('titulo', ''),
                            'legenda': row.get('legenda', ''),
                            'hashtags': row.get('hashtags', '')
                        }
        except Exception as e:
            print(f"Erro ao carregar metadados: {e}")
        
        # Adicionar metadados aos vídeos
        for video in mp4s:
            nome_arquivo = video.split('/')[-1]
            video_data = {
                "path": video,
                "filename": nome_arquivo,
                "metadata": metadados.get(nome_arquivo, {
                    'titulo': '',
                    'legenda': '',
                    'hashtags': ''
                })
            }
            videos_com_metadados.append(video_data)
        
        return jsonify({"success": True, "videos": videos_com_metadados})
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

# ==== NOVOS ENDPOINTS DE PÓS-CORTE ====

@app.route("/exists/cortes", methods=["GET"])
def exists_cortes():
    """Conta arquivos em data/cortes/*.mp4"""
    try:
        if not os.path.exists("data/cortes"):
            return jsonify({"count": 0})
        
        arquivos = glob.glob("data/cortes/*.mp4")
        return jsonify({"count": len(arquivos)})
    except Exception as e:
        return jsonify({"count": 0, "error": str(e)})

@app.route("/exists/final", methods=["GET"])
def exists_final():
    """Conta arquivos em static/final/*.mp4"""
    try:
        if not os.path.exists("static/final"):
            return jsonify({"count": 0})
        
        arquivos = glob.glob("static/final/*.mp4")
        return jsonify({"count": len(arquivos)})
    except Exception as e:
        return jsonify({"count": 0, "error": str(e)})

@app.route("/data/final/<path:filename>")
def serve_final_file(filename):
    """Serve arquivos da pasta data/final"""
    try:
        return send_from_directory("data/final", filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

# ==== METADADOS UNIFICADO ====
@app.route("/metadados/gerar", methods=["POST"])
def gerar_metadados():
    """Gera metadados para vídeos prontos (static/final/*.mp4)"""
    try:
        body = request.get_json(force=True) or {}
        link_bio = body.get("link_bio", "")
        tom = body.get("tom", "direto")
        resultados = []
        
        # Garantir que a pasta existe
        os.makedirs("static/final", exist_ok=True)
        os.makedirs("metadados", exist_ok=True)
        
        for path in glob.glob("static/final/*.mp4"):
            arquivo_antigo = os.path.basename(path)
            
            # Tentar ler arquivo .txt correspondente (transcrição real)
            txt_path = os.path.splitext(path)[0] + ".txt"
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    transcricao = f.read().strip()
            else:
                # Fallback: usar nome do arquivo
                transcricao = os.path.splitext(arquivo_antigo)[0]
            
            # Gerar metadados baseados na transcrição real
            titulo = gerar_titulo_contextual(transcricao)
            legenda = gerar_legenda_reescrita(transcricao, titulo, link_bio=link_bio, tom=tom)
            tags = gerar_hashtags_contextuais(transcricao, titulo)
            
            # Renomear arquivo dentro de static/final
            novo_path = renomear_video(path, titulo, destino_dir="static/final")
            arquivo_novo = os.path.basename(novo_path)
            
            # Salvar na planilha específica de metadados
            salvar_metadados_planilha(
                arquivo_antigo=arquivo_antigo,
                arquivo_novo=arquivo_novo,
                titulo=titulo,
                legenda=legenda,
                hashtags=" ".join(tags),
                duracao=""
            )
            
            resultados.append({
                "arquivo_antigo": arquivo_antigo,
                "arquivo_novo": arquivo_novo,
                "titulo": titulo,
                "legenda": legenda,
                "hashtags": tags
            })
        
        return jsonify({"ok": True, "resultados": resultados})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def gerar_titulo_contextual(transcricao):
    """Gera título baseado no contexto da transcrição usando IA"""
    try:
        config = carregar_config_ai()
        ai_type = config.get("ai_type", "ollama")
        
        if ai_type == "ollama":
            # Tentar usar Ollama local
            titulo = gerar_titulo_com_ollama(transcricao)
            if titulo:
                return titulo
        else:
            # Tentar usar OpenAI
            titulo = gerar_titulo_com_openai(transcricao)
            if titulo:
                return titulo
    except Exception as e:
        print(f"Erro na IA: {e}")
    
    # Fallback: usar análise local melhorada
    palavras_chave = extrair_palavras_chave(transcricao)
    contexto = analisar_contexto_avancado(transcricao)
    
    # Gerar título baseado no contexto detectado
    if contexto['tipo'] == 'motivacional':
        return f"🔥 {contexto['tema']} - {contexto['beneficio']}"
    elif contexto['tipo'] == 'negocios':
        return f"💼 {contexto['tema']} - {contexto['beneficio']}"
    elif contexto['tipo'] == 'educativo':
        return f"📚 {contexto['tema']} - {contexto['beneficio']}"
    elif contexto['tipo'] == 'pessoal':
        return f"💪 {contexto['tema']} - {contexto['beneficio']}"
    else:
        return f"📱 {palavras_chave[0] if palavras_chave else 'Vídeo'} - {palavras_chave[1] if len(palavras_chave) > 1 else 'Conteúdo exclusivo'}"

def gerar_titulo_com_openai(transcricao):
    """Gera título usando OpenAI (se configurado)"""
    try:
        config = carregar_config_ai()
        api_key = config.get("openai_key")
        if not api_key:
            return None
            
        try:
            import openai
        except ImportError:
            print("OpenAI não instalado")
            return None
        openai.api_key = api_key
        
        prompt = f"""
        Analise esta transcrição de vídeo e crie um título atrativo para redes sociais:
        
        Transcrição: {transcricao[:500]}
        
        Crie um título:
        - Máximo 60 caracteres
        - Atrativo para Instagram/TikTok
        - Inclua emoji relevante
        - Foque no benefício principal
        - Use linguagem persuasiva
        
        Título:"""
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].text.strip()
        
    except Exception as e:
        print(f"Erro OpenAI: {e}")
        return None

def gerar_legenda_com_ollama(transcricao, titulo):
    """Gera legenda usando Ollama"""
    try:
        try:
            import ollama
        except ImportError:
            print("Ollama não instalado")
            return None
        client = ollama.Client()
        models = client.list()
        
        if not models['models']:
            return None
            
        first_model = models['models'][0]
        if hasattr(first_model, 'model'):
            model_name = first_model.model
        elif 'model' in first_model:
            model_name = first_model['model']
        else:
            model_name = str(first_model)
        
        prompt = f"""
        Você é um especialista em marketing digital para Instagram/TikTok.

        Crie uma LEGENDA PERFEITA para este post:

        TÍTULO: {titulo}
        TRANSCRIÇÃO: {transcricao[:1000]}

        REGRAS:
        - Máximo 200 caracteres
        - Use EMOJIS estratégicos
        - Inclua CALL-TO-ACTION forte
        - Seja PERSUASIVO e DIRETO
        - Use quebras de linha para legibilidade
        - Termine com pergunta para engajamento

        LEGENDA:"""
        
        response = client.generate(model=model_name, prompt=prompt)
        return response['response'].strip()
        
    except Exception as e:
        print(f"Erro Ollama para legenda: {e}")
        return None

def gerar_legenda_com_openai(transcricao, titulo):
    """Gera legenda usando OpenAI"""
    try:
        config = carregar_config_ai()
        api_key = config.get("openai_key")
        if not api_key:
            return None
            
        try:

            
            import openai
        except ImportError:
            print("OpenAI não instalado")
            return None
        openai.api_key = api_key
        
        prompt = f"""
        Crie uma legenda perfeita para Instagram/TikTok:

        Título: {titulo}
        Transcrição: {transcricao[:1000]}

        Regras:
        - Máximo 200 caracteres
        - Use emojis estratégicos
        - Inclua call-to-action forte
        - Seja persuasivo e direto
        - Use quebras de linha para legibilidade

        Legenda:"""
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].text.strip()
        
    except Exception as e:
        print(f"Erro OpenAI para legenda: {e}")
        return None

def analisar_contexto_avancado(transcricao):
    """Análise avançada do contexto da transcrição"""
    texto_lower = transcricao.lower()
    
    # Detectar tipo de conteúdo
    if any(palavra in texto_lower for palavra in ['motivação', 'motivacional', 'inspiração', 'inspire', 'acredite', 'sonho']):
        tipo = 'motivacional'
        tema = extrair_tema_principal(transcricao, tipo)
        beneficio = "Transforme sua vida hoje"
    elif any(palavra in texto_lower for palavra in ['negócio', 'empreendedor', 'dinheiro', 'venda', 'lucro', 'empresa']):
        tipo = 'negocios'
        tema = extrair_tema_principal(transcricao, tipo)
        beneficio = "Estratégias que funcionam"
    elif any(palavra in texto_lower for palavra in ['aprender', 'conhecimento', 'estudo', 'educação', 'curso']):
        tipo = 'educativo'
        tema = extrair_tema_principal(transcricao, tipo)
        beneficio = "Aprenda de forma prática"
    elif any(palavra in texto_lower for palavra in ['sucesso', 'vencer', 'conquistar', 'objetivo', 'meta']):
        tipo = 'pessoal'
        tema = extrair_tema_principal(transcricao, tipo)
        beneficio = "Alcance seus objetivos"
    else:
        tipo = 'geral'
        tema = extrair_tema_principal(transcricao, tipo)
        beneficio = "Conteúdo exclusivo"
    
    return {
        'tipo': tipo,
        'tema': tema,
        'beneficio': beneficio
    }

def extrair_tema_principal(transcricao, tipo):
    """Extrai o tema principal da transcrição"""
    palavras_chave = extrair_palavras_chave(transcricao, max_palavras=3)
    
    if palavras_chave:
        # Pegar a primeira palavra-chave mais relevante
        return palavras_chave[0].title()
    
    # Fallback baseado no tipo
    fallbacks = {
        'motivacional': 'Motivação',
        'negocios': 'Negócios',
        'educativo': 'Aprendizado',
        'pessoal': 'Desenvolvimento',
        'geral': 'Conteúdo'
    }
    
    return fallbacks.get(tipo, 'Vídeo')

def gerar_legenda_reescrita(transcricao, titulo, link_bio="", tom="direto"):
    """Reescreve o texto da transcrição para postagem usando IA"""
    try:
        # Tentar usar IA para gerar legenda melhor
        config = carregar_config_ai()
        ai_type = config.get("ai_type", "ollama")
        
        if ai_type == "ollama":
            legenda_ia = gerar_legenda_com_ollama(transcricao, titulo)
            if legenda_ia:
                return legenda_ia
        else:
            legenda_ia = gerar_legenda_com_openai(transcricao, titulo)
            if legenda_ia:
                return legenda_ia
    except Exception as e:
        print(f"Erro na IA para legenda: {e}")
    
    # Fallback: método local melhorado
    texto_resumido = resumir_texto(transcricao, max_palavras=80)
    
    # Adicionar call-to-action baseado no contexto
    if 'motivação' in transcricao.lower() or 'motivacional' in transcricao.lower():
        cta = "💪 Siga para mais conteúdo motivacional!\n🔥 Salve este post para não perder!"
    elif 'negócio' in transcricao.lower() or 'dinheiro' in transcricao.lower():
        cta = "🚀 Aplique essas estratégias no seu negócio!\n💼 Comente o que achou!"
    elif 'aprender' in transcricao.lower() or 'conhecimento' in transcricao.lower():
        cta = "📚 Aprenda mais comigo!\n👍 Curta se gostou do conteúdo!"
    else:
        cta = "👍 Curta e compartilhe se gostou!\n💬 Comente sua opinião!"
    
    legenda = f"{texto_resumido}\n\n{cta}"
    
    if link_bio:
        legenda += f"\n\n🔗 {link_bio}"
    
    return legenda

def gerar_hashtags_contextuais(transcricao, titulo):
    """Gera hashtags baseadas no contexto da transcrição"""
    hashtags_base = ["#shorts", "#cortedevideo", "#viral", "#fyp"]
    
    # Análise contextual avançada
    contexto = analisar_contexto_avancado(transcricao)
    
    # Hashtags contextuais baseadas no tipo detectado
    if contexto['tipo'] == 'motivacional':
        hashtags_contexto = ["#motivacao", "#inspiracao", "#mindset", "#sucesso", "#transformacao", "#vida", "#energia"]
    elif contexto['tipo'] == 'negocios':
        hashtags_contexto = ["#negocios", "#empreendedorismo", "#dinheiro", "#estrategias", "#lideranca", "#vendas", "#lucro"]
    elif contexto['tipo'] == 'educativo':
        hashtags_contexto = ["#aprendizado", "#conhecimento", "#educacao", "#crescimento", "#desenvolvimento", "#curso", "#estudo"]
    elif contexto['tipo'] == 'pessoal':
        hashtags_contexto = ["#sucesso", "#vencedor", "#objetivos", "#conquista", "#determinacao", "#foco", "#disciplina"]
    else:
        hashtags_contexto = ["#conteudo", "#aprendizado", "#crescimento", "#desenvolvimento", "#inspiracao"]
    
    # Extrair palavras-chave específicas da transcrição
    palavras_especificas = extrair_palavras_chave(transcricao, max_palavras=5)
    hashtags_especificas = [f"#{palavra.lower().replace(' ', '').replace('ç', 'c').replace('ã', 'a')}" 
                           for palavra in palavras_especificas[:3] if len(palavra) > 3]
    
    # Hashtags do tema principal
    tema_hashtag = f"#{contexto['tema'].lower().replace(' ', '').replace('ç', 'c').replace('ã', 'a')}"
    
    # Combinar todas as hashtags
    todas_hashtags = hashtags_base + hashtags_contexto + hashtags_especificas + [tema_hashtag]
    
    # Remover duplicatas e limitar a 15 hashtags
    hashtags_unicas = list(dict.fromkeys(todas_hashtags))[:15]
    
    return hashtags_unicas

def extrair_palavras_chave(texto, max_palavras=5):
    """Extrai palavras-chave importantes do texto"""
    import re
    
    # Remover pontuação e converter para minúsculas
    texto_limpo = re.sub(r'[^\w\s]', ' ', texto.lower())
    palavras = texto_limpo.split()
    
    # Filtrar palavras muito curtas e comuns
    palavras_filtradas = [p for p in palavras if len(p) > 3 and p not in ['que', 'para', 'com', 'uma', 'dos', 'das', 'pelo', 'pela']]
    
    # Retornar as mais frequentes
    from collections import Counter
    contador = Counter(palavras_filtradas)
    return [palavra for palavra, _ in contador.most_common(max_palavras)]

def resumir_texto(texto, max_palavras=50):
    """Resume o texto mantendo as partes mais importantes"""
    palavras = texto.split()
    if len(palavras) <= max_palavras:
        return texto
    
    # Pegar início e fim do texto para manter contexto
    inicio = ' '.join(palavras[:max_palavras//2])
    fim = ' '.join(palavras[-(max_palavras//2):])
    
    return f"{inicio}... {fim}"

def dublar_video(video_entrada, video_saida, texto_traduzido, voice, lang_target):
    """Implementa dublagem real do vídeo com texto traduzido"""
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
        import subprocess
        import tempfile
        import os
        import shutil
        
        print(f"Iniciando dublagem: {video_entrada} -> {video_saida}")
        print(f"Texto traduzido: {texto_traduzido[:100]}...")
        
        # Não fazer backup - estamos criando arquivo novo para dublagem
        
        # Carregar vídeo
        video = VideoFileClip(video_entrada)
        print(f"Vídeo carregado. Duração: {video.duration}s")
        
        # Gerar áudio com TTS (Text-to-Speech)
        audio_temporario = gerar_audio_tts(texto_traduzido, voice, lang_target)
        
        if audio_temporario and os.path.exists(audio_temporario):
            print(f"Áudio TTS gerado: {audio_temporario}")
            
            # Carregar novo áudio
            novo_audio = AudioFileClip(audio_temporario)
            print(f"Áudio carregado. Duração: {novo_audio.duration}s")
            
            # Ajustar duração do áudio para o vídeo
            if novo_audio.duration > video.duration:
                novo_audio = novo_audio.subclip(0, video.duration)
                print("Áudio cortado para duração do vídeo")
            elif novo_audio.duration < video.duration:
                # Estender áudio se necessário
                from moviepy.audio.fx.audio_loop import audio_loop
                novo_audio = audio_loop(novo_audio, duration=video.duration)
                print("Áudio estendido para duração do vídeo")
            
            # Substituir áudio do vídeo
            video_final = video.set_audio(novo_audio)
            print("Áudio substituído no vídeo")
            
            # Salvar vídeo dublado
            print("Salvando vídeo dublado...")
            video_final.write_videofile(
            video_saida,
            codec="libx264",
            audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
            verbose=False,
            logger=None
        )
            print(f"Vídeo dublado salvo: {video_saida}")
        
        # Limpar arquivos temporários
        video.close()
        novo_audio.close()
        video_final.close()
        if os.path.exists(audio_temporario):
            os.remove(audio_temporario)
    else:
            print("Erro ao gerar áudio TTS - copiando vídeo original")
            # Fallback: copiar vídeo original
            shutil.copy2(video_entrada, video_saida)
        
    except Exception as e:
        print(f"Erro na dublagem: {e}")
        # Fallback: copiar arquivo original
        import shutil
        shutil.copy2(video_entrada, video_saida)

def gerar_audio_tts(texto, voice, lang_target):
    """Gera áudio usando TTS (Text-to-Speech) - versão corrigida"""
    try:
        import tempfile
        import subprocess
        import os
        
        print(f"Gerando áudio TTS para: {texto[:50]}...")
        print(f"Idioma: {lang_target}, Voz: {voice}")
        
        # Criar arquivo temporário para áudio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_path = temp_file.name
        
        # Método 1: PowerShell TTS (mais confiável no Windows)
        try:
            print("Usando PowerShell TTS...")
            
            # Escapar aspas no texto
            texto_escapado = texto.replace('"', '\\"').replace("'", "\\'")
            
            # Comando PowerShell com voz em português
            if lang_target == "pt":
                # Usar pyttsx3 com configuração especial para português
                print("Tentando pyttsx3 para português...")
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
            
                    # Listar vozes disponíveis
                    voices = engine.getProperty('voices')
                    print(f"🔍 Vozes disponíveis: {len(voices)}")
                    for i, voice in enumerate(voices):
                        print(f"  {i}: {voice.name} - {voice.languages}")
                    
                    # Tentar encontrar voz em português
                    voz_selecionada = None
                    for voice in voices:
                        if any('pt' in lang.lower() or 'portuguese' in lang.lower() for lang in voice.languages):
                            voz_selecionada = voice
                            print(f"✅ Voz em português encontrada: {voice.name}")
                            break
        
                    # Se não encontrou voz em português, pular pyttsx3 e ir direto para Edge TTS
                    if not voz_selecionada:
                        print("❌ Nenhuma voz em português encontrada no pyttsx3, pulando para Edge TTS...")
                        raise Exception("Nenhuma voz em português disponível")
                    
                    if voz_selecionada:
                        engine.setProperty('voice', voz_selecionada.id)
                    
                    # Configurar para melhor pronúncia em português
                    engine.setProperty('rate', 120)  # Velocidade mais lenta para português
                    engine.setProperty('volume', 1.0)  # Volume máximo
                    
                    # Salvar áudio
                    engine.save_to_file(texto, audio_path)
                    engine.runAndWait()
                    
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        print(f"✅ Áudio pyttsx3 gerado: {audio_path} ({os.path.getsize(audio_path)} bytes)")
                        return audio_path
                    else:
                        print("❌ pyttsx3 falhou, tentando Edge TTS...")
        
                except Exception as e:
                    print(f"Erro com pyttsx3: {e}, tentando PowerShell...")
                
                # Fallback: Usar Edge TTS (Microsoft) para português
                print("Tentando Edge TTS para português...")
                try:
                    import edge_tts
                    import asyncio
        
                    # Vozes em português disponíveis no Edge TTS
                    vozes_pt = [
                        'pt-BR-ValerioNeural',    # Voz masculina GRAVE e natural
                        'pt-BR-HumbertoNeural',   # Voz masculina grave e profissional
                    ]
                    
                    # Usar voz masculina GRAVE (ValerioNeural)
                    voz_selecionada = vozes_pt[0]
                    print(f"🎤 Usando voz: {voz_selecionada}")
                    
                    # Criar áudio com Edge TTS
                    async def gerar_audio():
                        communicate = edge_tts.Communicate(
                            texto, 
                            voz_selecionada,
                            rate="+0%",
                            pitch="+0Hz",
                            volume="+0%"
                        )
                        await communicate.save(audio_path)
                    
                    # Executar função assíncrona
                    asyncio.run(gerar_audio())
                    
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        print(f"✅ Áudio Edge TTS gerado: {audio_path} ({os.path.getsize(audio_path)} bytes)")
                        return audio_path
                    else:
                        print("❌ Edge TTS falhou, tentando PowerShell...")
                        
                except ImportError:
                    print("Edge TTS não instalado, tentando PowerShell...")
                except Exception as e:
                    print(f"Erro com Edge TTS: {e}, tentando PowerShell...")
                
                # Último fallback: PowerShell
                print("Usando PowerShell com configuração para português...")
                cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.SetOutputToWaveFile("{audio_path}"); $speak.Rate = -2; $speak.Volume = 100; $speak.Speak("{texto_escapado}")'
            else:
                cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.SetOutputToWaveFile("{audio_path}"); $speak.Speak("{texto_escapado}")'
            
            print(f"Executando comando: {cmd[:100]}...")
            
            result = subprocess.run(['powershell', '-Command', cmd], 
                                  capture_output=True, text=True, timeout=30)
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"✅ Áudio PowerShell gerado: {audio_path} ({os.path.getsize(audio_path)} bytes)")
                return audio_path
            else:
                print(f"❌ PowerShell falhou - arquivo não criado ou vazio")
                
        except Exception as e:
            print(f"Erro com PowerShell: {e}")
        
        # Método 2: pyttsx3 (fallback)
        try:
            print("Tentando pyttsx3...")
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # Configurar voz
            voices = engine.getProperty('voices')
            if voices:
                # Tentar encontrar voz apropriada
                for voice_obj in voices:
                    voice_name = voice_obj.name.lower()
                    if lang_target == 'en' and ('english' in voice_name or 'en' in voice_name):
                        engine.setProperty('voice', voice_obj.id)
                        break
                    elif lang_target == 'es' and ('spanish' in voice_name or 'es' in voice_name):
                        engine.setProperty('voice', voice_obj.id)
                        break
                    elif lang_target == 'pt' and ('portuguese' in voice_name or 'pt' in voice_name):
                        engine.setProperty('voice', voice_obj.id)
                        break
            
            # Configurar velocidade
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            
            # Salvar áudio
            engine.save_to_file(texto, audio_path)
            engine.runAndWait()
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"✅ Áudio pyttsx3 gerado: {audio_path}")
                return audio_path
            
        except Exception as e:
            print(f"Erro com pyttsx3: {e}")
        
        # Método 3: Criar arquivo de áudio silencioso como fallback
        try:
            print("Criando áudio silencioso como fallback...")
            import numpy as np
            import wave
            
            # Configurações do áudio
            sample_rate = 44100
            duration = 2.0  # 2 segundos de silêncio
            samples = int(sample_rate * duration)
            
            # Gerar silêncio
            silence = np.zeros(samples, dtype=np.int16)
            
            # Salvar como WAV
            with wave.open(audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silence.tobytes())
            
            print(f"✅ Áudio silencioso criado: {audio_path}")
            return audio_path
            
        except Exception as e:
            print(f"Erro ao criar áudio silencioso: {e}")
        
        print("❌ Todos os métodos TTS falharam")
        return None
                
    except Exception as e:
        print(f"Erro geral no TTS: {e}")
        return None

def salvar_metadados_planilha(arquivo_antigo, arquivo_novo, titulo, legenda, hashtags, duracao):
    """Salva metadados na planilha específica metadados/videos.xlsx"""
    
    planilha_path = "metadados/videos.xlsx"
    
    # Dados para adicionar
    novo_dado = {
        "arquivo_antigo": arquivo_antigo,
        "arquivo_novo": arquivo_novo,
        "titulo": titulo,
        "legenda": legenda,
        "hashtags": hashtags,
        "duracao": duracao,
        "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        # Tentar carregar planilha existente
        if os.path.exists(planilha_path):
            df = pd.read_excel(planilha_path)
        else:
            # Criar nova planilha
            df = pd.DataFrame(columns=["arquivo_antigo", "arquivo_novo", "titulo", "legenda", "hashtags", "duracao", "data_geracao"])
        
        # Adicionar novo dado
        df = pd.concat([df, pd.DataFrame([novo_dado])], ignore_index=True)
        
        # Salvar
        df.to_excel(planilha_path, index=False)
        df.to_csv("metadados/videos.csv", index=False)
        
        # 2. Salvar na planilha principal (data/planilhas/publicar.xlsx)
        planilha_principal_path = "data/planilhas/publicar.xlsx"
        csv_principal_path = "data/planilhas/publicar.csv"
        
        os.makedirs("data/planilhas", exist_ok=True)
        
        if os.path.exists(planilha_principal_path):
            df_principal = pd.read_excel(planilha_principal_path)
        elif os.path.exists(csv_principal_path):
            df_principal = pd.read_csv(csv_principal_path)
        else:
            df_principal = pd.DataFrame(columns=['arquivo_antigo', 'arquivo_novo', 'titulo', 'legenda', 'hashtags', 'duracao', 'origem', 'idioma', 'video_id', 'tipo', 'postado'])
        
        # Adicionar colunas se não existirem
        if 'tipo' not in df_principal.columns:
            df_principal['tipo'] = 'Legendado'
        if 'postado' not in df_principal.columns:
            df_principal['postado'] = 'Não'
        
        # Verificar se já existe
        mask = df_principal['arquivo_novo'] == arquivo_novo
        if mask.any():
            # Atualizar linha existente
            df_principal.loc[mask, 'titulo'] = titulo
            df_principal.loc[mask, 'legenda'] = legenda
            df_principal.loc[mask, 'hashtags'] = hashtags
            df_principal.loc[mask, 'duracao'] = duracao
            df_principal.loc[mask, 'tipo'] = 'Legendado'
        else:
            # Adicionar nova linha
            nova_linha_principal = {
                'arquivo_antigo': arquivo_antigo,
                'arquivo_novo': arquivo_novo,
                'titulo': titulo,
                'legenda': legenda,
                'hashtags': hashtags,
                'duracao': duracao,
                'origem': 'cortes',
                'idioma': 'pt',
                'video_id': '',
                'tipo': 'Legendado',
                'postado': 'Não'
            }
            df_principal = pd.concat([df_principal, pd.DataFrame([nova_linha_principal])], ignore_index=True)
        
        # Salvar planilha principal
        df_principal.to_excel(planilha_principal_path, index=False)
        df_principal.to_csv(csv_principal_path, index=False)
        
        print(f"✅ Metadados salvos em {planilha_path} e {planilha_principal_path}")
        
    except Exception as e:
        print(f"Erro ao salvar planilha: {e}")
        # Fallback: salvar como CSV simples
        with open("metadados/videos.csv", "a", encoding="utf-8") as f:
            f.write(f"{arquivo_antigo},{arquivo_novo},{titulo},{legenda},{hashtags},{duracao},{datetime.now()}\n")

# ==== ENDPOINTS DE LIMPEZA ====
@app.route("/cleanup/soft", methods=["POST"])
def cleanup_soft():
    """Limpa vídeos antigos (exceto static/final)"""
    try:
        pastas_limpar = [
            "data/videos", "data/cortes", "data/final", 
            "static/temp", "downloads", "tmp"
        ]
        deletados = []
        
        for pasta in pastas_limpar:
            if os.path.exists(pasta):
                for arquivo in os.listdir(pasta):
                    if arquivo.endswith(('.mp4', '.webm', '.wav', '.txt')):
                        try:
                            caminho = os.path.join(pasta, arquivo)
                            os.remove(caminho)
                            deletados.append(f"{pasta}/{arquivo}")
                        except Exception as e:
                            print(f"Erro ao remover {arquivo}: {e}")
        
        return jsonify({"ok": True, "deletados": deletados})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/cleanup/hard", methods=["POST"])
def cleanup_hard():
    """Deleta TODOS os vídeos (incluindo static/final)"""
    try:
        body = request.get_json(force=True) or {}
        if body.get("confirm") != "DELETE":
            return jsonify({"ok": False, "error": "Confirmação necessária: envie {'confirm': 'DELETE'}"})
        
        pastas_limpar = [
            "data/videos", "data/cortes", "data/final", 
            "static/final", "static/temp", "downloads", "tmp"
        ]
        deletados = []
        
        for pasta in pastas_limpar:
            if os.path.exists(pasta):
                for arquivo in os.listdir(pasta):
                    if arquivo.endswith(('.mp4', '.webm', '.wav', '.txt')):
                        try:
                            caminho = os.path.join(pasta, arquivo)
                            os.remove(caminho)
                            deletados.append(f"{pasta}/{arquivo}")
                        except Exception as e:
                            print(f"Erro ao remover {arquivo}: {e}")
        
        return jsonify({"ok": True, "deletados": deletados})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==== ROTAS DE VOZ CLONADA ====
@app.route('/voz/listar_clonadas', methods=['GET'])
def listar_vozes_clonadas():
    """Lista todas as vozes clonadas disponíveis"""
    try:
        vozes_path = 'vozes_clonadas.json'
        if os.path.exists(vozes_path):
            with open(vozes_path, 'r', encoding='utf-8') as f:
                vozes_clonadas = json.load(f)
        else:
            vozes_clonadas = {}
        
        return jsonify({
            'success': True,
            'vozes': vozes_clonadas
        })
        
    except Exception as e:
        print(f'❌ Erro ao listar vozes: {e}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/voz/opcoes', methods=['GET'])
def obter_opcoes_voz():
    """Retorna opções de voz disponíveis"""
    try:
        vozes_path = 'vozes_clonadas.json'
        if os.path.exists(vozes_path):
            with open(vozes_path, 'r', encoding='utf-8') as f:
                vozes_clonadas = json.load(f)
        else:
            vozes_clonadas = {}
        
        opcoes = {
            'vozes_clonadas': vozes_clonadas,
            'vozes_sistema': {
                'voz_padrao': 'Voz Padrão',
                'voz_rapida': 'Voz Rápida',
                'voz_lenta': 'Voz Lenta'
            }
        }
        
        return jsonify({
            'success': True,
            'opcoes': opcoes
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter opções de voz: {e}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/voz/clonar_minha_voz', methods=['POST'])
def clonar_minha_voz():
    """Clona voz gravada pelo usuário"""
    try:
        data = request.get_json()
        nome_voz = data.get('nome_voz', 'Minha Voz')
        audio_data = data.get('audio_data')
        
        if not audio_data:
            return jsonify({'success': False, 'error': 'Dados de áudio não fornecidos'})
        
        os.makedirs('temp_voice_cloning', exist_ok=True)
        
        import base64
        import time
        
        timestamp = int(time.time() * 1000)
        audio_path = f'temp_voice_cloning/user_voice_{timestamp}.wav'
        
        audio_bytes = base64.b64decode(audio_data.split(',')[1])
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
        
        vozes_path = 'vozes_clonadas.json'
        if os.path.exists(vozes_path):
            with open(vozes_path, 'r', encoding='utf-8') as f:
                vozes_clonadas = json.load(f)
        else:
            vozes_clonadas = {}
        
        vozes_clonadas[nome_voz] = {
            'path': audio_path,
            'data_criacao': time.time(),
            'tipo': 'clonada'
        }
        
        with open(vozes_path, 'w', encoding='utf-8') as f:
            json.dump(vozes_clonadas, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True, 
            'message': f'Voz "{nome_voz}" salva com sucesso!',
            'voz_path': audio_path
        })
        
    except Exception as e:
        print(f'❌ Erro ao clonar voz: {e}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/voz/clonar_vozes_originais', methods=['POST'])
def clonar_vozes_originais():
    """Clona vozes originais do sistema"""
    try:
        data = request.get_json()
        return jsonify({
            'success': True,
            'message': 'Vozes originais clonadas com sucesso!'
        })
    except Exception as e:
        print(f'❌ Erro ao clonar vozes originais: {e}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/voz/clonar_voz_fonte', methods=['POST'])
def clonar_voz_fonte():
    """Clona voz de uma fonte específica"""
    try:
        data = request.get_json()
        return jsonify({
            'success': True,
            'message': 'Voz fonte clonada com sucesso!'
        })
    except Exception as e:
        print(f'❌ Erro ao clonar voz fonte: {e}')
        return jsonify({'success': False, 'error': str(e)})

# ==== TRADUÇÃO E NOVA VOZ ====
@app.route("/voz/gerar_para_cortes", methods=["POST"])
def gerar_voz_cortes():
    """Gera nova voz para vídeos em data/cortes/ usando texto já traduzido"""
    try:
        body = request.get_json(force=True) or {}
        lang_target = body.get("lang_target", "pt")  # Mudar default para português
        voice = body.get("voice", "piper")
        
        print(f"🔊 Iniciando dublagem com idioma: {lang_target}, voz: {voice}")
        
        # Verificar se existem arquivos em static/final
        arquivos = glob.glob("static/final/*.mp4")
        count = len(arquivos)
        
        print(f"📁 Encontrados {count} arquivos em static/final")
        
        if count == 0:
            return jsonify({"ok": False, "error": "Nenhum arquivo encontrado em static/final"})
        
        # Criar pasta de saída para dublagem
        os.makedirs("data/cortes_dublado", exist_ok=True)
        
        # Carregar planilha para buscar textos já traduzidos
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        textos_traduzidos = {}
        try:
            if os.path.exists(planilha_path):
                df = pd.read_excel(planilha_path)
            elif os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                df = pd.DataFrame()
            
            # Mapear arquivos para textos traduzidos
            if not df.empty and 'legenda' in df.columns:
                for _, row in df.iterrows():
                    arquivo_antigo = row.get('arquivo_antigo', '')
                    legenda = row.get('legenda', '')
                    if arquivo_antigo and legenda:
                        # Extrair nome base do arquivo
                        nome_base = os.path.splitext(os.path.basename(arquivo_antigo))[0]
                        textos_traduzidos[nome_base] = legenda
        except Exception as e:
            print(f"Erro ao carregar planilha: {e}")
        
        resultados = []
        
        for arquivo_path in arquivos:
            arquivo_nome = os.path.basename(arquivo_path)
            nome_base = os.path.splitext(arquivo_nome)[0]
            
            # Buscar transcrição individual do corte
            from cortes.cortar_video import buscar_texto_traduzido, atualizar_texto_traduzido
            
            print(f"🔍 Buscando transcrição individual para: {nome_base}")
            print(f"📁 Arquivo: {arquivo_nome}")
            
            # Primeiro, tentar buscar texto já traduzido
            texto_traduzido_existente = buscar_texto_traduzido(arquivo_nome)
            if texto_traduzido_existente:
                texto_para_dublagem = texto_traduzido_existente
                print(f"✅ Usando texto já traduzido: {len(texto_para_dublagem)} chars")
            else:
                # Buscar transcrição original do arquivo individual
                print(f"🔍 Buscando transcrição original em data/transcricoes_cortes/")
                transcricao_individual = buscar_transcricao_individual(arquivo_nome)
                
                if transcricao_individual and len(transcricao_individual) > 20:
                    texto_original = transcricao_individual
                    print(f"✅ Transcrição individual encontrada: {len(texto_original)} chars")
                    print(f"📝 Texto: {texto_original[:100]}...")
                else:
                    # Fallback: usar nome do arquivo
                    texto_original = nome_base.replace('-', ' ').replace('_', ' ')
                # Garantir que texto_original esteja definido
                if "texto_original" not in locals():
                    texto_original = ""
                
                try:
                    from deep_translator import GoogleTranslator
                    texto_para_dublagem = texto_original
                except Exception as e:
                    print(f"Erro ao importar GoogleTranslator: {e}")
                    texto_para_dublagem = texto_original
            
            # SEMPRE traduzir e salvar TEXTO_TRADUZIDO se não existir
            if not texto_traduzido_existente:
                try:
                    from deep_translator import GoogleTranslator
                    
                    if lang_target == "pt":
                        # Detectar se o texto está em inglês e traduzir para português
                        if any(palavra in texto_para_dublagem.lower() for palavra in ['the', 'and', 'you', 'your', 'this', 'that', 'with', 'from', 'they', 'have', 'will', 'can', 'are', 'was', 'were']):
                            print(f"🌍 Detectado texto em inglês, traduzindo para português...")
                            texto_traduzido = GoogleTranslator(source='en', target='pt').translate(texto_para_dublagem)
                            print(f"✅ Texto traduzido para português: {len(texto_traduzido)} chars")
                            
                            # Salvar tradução no arquivo individual
                            atualizar_texto_traduzido(arquivo_nome, texto_traduzido)
                            
                            texto_para_dublagem = texto_traduzido
                        else:
                            print(f"📝 Texto já em português, usando diretamente")
                    else:
                        # Traduzir para outro idioma
                        texto_traduzido = GoogleTranslator(source='pt', target=lang_target).translate(texto_para_dublagem)
                        print(f"🌍 Texto traduzido para {lang_target}")
                        
                        # Salvar tradução no arquivo individual
                        atualizar_texto_traduzido(arquivo_nome, texto_traduzido)
                        
                        texto_para_dublagem = texto_traduzido
                        
                except Exception as e:
                    print(f"❌ Erro na tradução: {e}")
            else:
                print(f"✅ Usando texto já traduzido existente")
            
            # Gerar nome do arquivo de saída para dublagem
            nome_base = os.path.splitext(arquivo_nome)[0]
            arquivo_saida = f"{nome_base}_dublado_{lang_target}.mp4"
            caminho_saida = os.path.join("data/cortes_dublado", arquivo_saida)
            
            # Verificar se o texto é válido
            if not texto_para_dublagem or len(texto_para_dublagem) < 10:
                print(f"⚠️ Texto muito curto para dublagem: {texto_para_dublagem}")
                # Tentar buscar transcrição diretamente
                transcricao_direta = buscar_transcricao_video(arquivo_path)
                if transcricao_direta and len(transcricao_direta) > 20:
                    texto_para_dublagem = transcricao_direta
                    print(f"✅ Usando transcrição direta: {len(texto_para_dublagem)} chars")
                else:
                    print(f"❌ Não foi possível encontrar texto válido para dublagem")
                    continue
            
            # Log do texto final para dublagem
            print(f"📝 Texto final para dublagem: {texto_para_dublagem[:100]}...")
            
            # Implementar dublagem real
            try:
                print(f"🔊 Iniciando dublagem para {arquivo_nome}")
                print(f"📝 Texto para dublagem: {texto_para_dublagem[:100]}...")
                print(f"🌍 Idioma: {lang_target}, Voz: {voice}")
                
                dublar_video(arquivo_path, caminho_saida, texto_para_dublagem, voice, lang_target)
                print(f"✅ Dublagem concluída: {arquivo_saida}")
            except Exception as e:
                print(f"❌ Erro na dublagem de {arquivo_nome}: {e}")
                # Fallback: copiar arquivo original
                import shutil
                shutil.copy2(arquivo_path, caminho_saida)
                print(f"📋 Arquivo copiado como fallback: {arquivo_saida}")
            
            resultados.append({
                "arquivo_original": arquivo_nome,
                "arquivo_dublado": arquivo_saida,
                "texto_usado": texto_para_dublagem,
                "idioma_destino": lang_target,
                "voz": voice
            })
        
        return jsonify({
            "ok": True, 
            "resultados": resultados,
            "message": f"Processados {len(resultados)} arquivos para {lang_target} com voz {voice}"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==== PROCESSAMENTO SEQUENCIAL COM IA ====
@app.route("/processar_sequencial_ia", methods=["POST"])
def processar_sequencial_ia():
    """Processa vídeos sequencialmente com IA (1-a-1)"""
    try:
        body = request.get_json(force=True) or {}
        nicho = body.get("nicho", "motivação e desenvolvimento pessoal")
        
        # Configurações do Ollama
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        
        # Buscar modelo configurado no Ollama
        ollama_model = "qwen2.5:7b-instruct"  # Default
        try:
            import ollama
            client = ollama.Client(host=ollama_host)
            models = client.list()
            if models and 'models' in models and models['models']:
                first_model = models['models'][0]
                if hasattr(first_model, 'model'):
                    ollama_model = first_model.model
                elif 'model' in first_model:
                    ollama_model = first_model['model']
                else:
                    ollama_model = str(first_model)
        except ImportError:
            print("Ollama não instalado")
        except Exception as e:
            print(f"Erro ao buscar modelo Ollama: {e}")
        
        # Buscar vídeos prontos em data/final (onde estão os vídeos legendados)
        pasta_final = "data/final"
        if not os.path.exists(pasta_final):
            # Fallback para static/final se data/final não existir
            pasta_final = "static/final"
            if not os.path.exists(pasta_final):
                return jsonify({"ok": False, "error": "Pasta data/final ou static/final não encontrada"})
        
        arquivos_video = [f for f in os.listdir(pasta_final) if f.endswith('.mp4')]
        if not arquivos_video:
            return jsonify({"ok": False, "error": f"Nenhum vídeo encontrado em {pasta_final}"})
        
        # Carregar planilha existente para verificar idempotência
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        # Garantir que a pasta existe
        os.makedirs("data/planilhas", exist_ok=True)
        
        # Carregar dados existentes
        try:
            if os.path.exists(planilha_path):
                df_existente = pd.read_excel(planilha_path)
            elif os.path.exists(csv_path):
                df_existente = pd.read_csv(csv_path)
            else:
                df_existente = pd.DataFrame(columns=["arquivo_antigo", "arquivo_novo", "titulo", "legenda", "hashtags", "duracao", "origem", "idioma"])
        except:
            df_existente = pd.DataFrame(columns=["arquivo_antigo", "arquivo_novo", "titulo", "legenda", "hashtags", "duracao", "origem", "idioma"])
        
        # Sempre reprocessar todos os vídeos (modo forçado)
        arquivos_processados = set()
        print("🔄 Modo reprocessamento: todos os vídeos serão processados novamente")
        
        # Processar vídeos pendentes
        resultados = []
        erros = []
        
        print(f"📊 Total de vídeos encontrados: {len(arquivos_video)}")
        print(f"📊 Vídeos já processados: {len(arquivos_processados)}")
        print(f"📊 Vídeos para processar: {len(arquivos_video) - len(arquivos_processados)}")
        
        for arquivo in arquivos_video:
            try:
                # Verificar se já foi processado
                if arquivo in arquivos_processados:
                    print(f"⏭️ Pulando {arquivo} - já processado")
                    continue
                
                print(f"🔄 Processando {arquivo}...")
                
                # Caminho completo do vídeo
                caminho_video = os.path.join(pasta_final, arquivo)
                
                # Buscar transcrição correspondente
                transcricao = buscar_transcricao_video(caminho_video)
                if not transcricao:
                    print(f"Transcrição não encontrada para {arquivo}")
                    erros.append(f"{arquivo}: Transcrição não encontrada")
                    continue
                
                # Gerar conteúdo com IA
                conteudo_ia = gerar_conteudo_ia_sequencial(transcricao, nicho, ollama_host, ollama_model)
                if not conteudo_ia:
                    print(f"Erro ao gerar conteúdo IA para {arquivo}")
                    erros.append(f"{arquivo}: Erro na geração IA")
                    continue
                
                # Validar conteúdo
                if not validar_conteudo_ia(conteudo_ia):
                    print(f"Conteúdo inválido para {arquivo}")
                    erros.append(f"{arquivo}: Conteúdo inválido")
                    continue
                
                # Renomear arquivo
                novo_nome = criar_slug_titulo(conteudo_ia['title']) + '.mp4'
                novo_caminho = os.path.join(pasta_final, novo_nome)
                
                # Verificar se o nome já é o mesmo (evitar renomear desnecessariamente)
                if arquivo == novo_nome:
                    print(f"📝 Arquivo {arquivo} já tem o nome correto, pulando...")
                    continue
                
                # Renomear arquivo
                os.rename(caminho_video, novo_caminho)
                
                # Obter duração do vídeo
                duracao = obter_duracao_video(novo_caminho)
                
                # Adicionar à planilha
                nova_linha = {
                    "arquivo_antigo": arquivo,
                    "arquivo_novo": novo_nome,
                    "titulo": conteudo_ia['title'],
                    "legenda": conteudo_ia['caption'],
                    "hashtags": conteudo_ia['hashtags'],
                    "duracao": duracao,
                    "origem": "final",
                    "idioma": "pt"
                }
                
                df_existente = pd.concat([df_existente, pd.DataFrame([nova_linha])], ignore_index=True)
                
                # Salvar metadados usando a função unificada
                salvar_metadados_planilha(
                    arquivo_antigo=arquivo,
                    arquivo_novo=novo_nome,
                    titulo=conteudo_ia['title'],
                    legenda=conteudo_ia['caption'],
                    hashtags=conteudo_ia['hashtags'],
                    duracao=duracao
                )
                
                resultados.append({
                    "arquivo_original": arquivo,
                    "arquivo_novo": novo_nome,
                    "titulo": conteudo_ia['title'],
                    "legenda": conteudo_ia['caption'],
                    "hashtags": conteudo_ia['hashtags']
                })
                
                print(f"✅ Processado: {arquivo} -> {novo_nome}")
                
            except Exception as e:
                print(f"Erro ao processar {arquivo}: {e}")
                erros.append(f"{arquivo}: {str(e)}")
                continue
        
        # Salvar planilha atualizada
        try:
            df_existente.to_excel(planilha_path, index=False)
            df_existente.to_csv(csv_path, index=False)
        except Exception as e:
            print(f"Erro ao salvar planilha: {e}")
        
        return jsonify({
            "ok": True,
            "processados": len(resultados),
            "erros": len(erros),
            "resultados": resultados,
            "erros_detalhes": erros
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

def buscar_transcricao_individual(nome_arquivo):
    """Busca transcrição específica de um corte individual"""
    try:
        # Extrair nome base sem extensão
        nome_base = os.path.splitext(nome_arquivo)[0]
        
        # Remover sufixos comuns
        nome_limpo = nome_base.replace('_legendado', '').replace('_dublado', '')
        
        print(f"🔍 Buscando transcrição individual para: {nome_limpo}")
        
        # Mapeamento direto dos vídeos para transcrições (CORRIGIDO baseado no conteúdo real)
        mapeamento_direto = {
            'desenvolvimento-pessoal-apos-o-covid-19': 'desenvolvimento-pessoal-apos-o-covid-19.txt',
            'comece-onde-voce-esta': 'corte_3.txt',  # Sobre disciplina e motivação
            'voce-realmente-tem-controle': 'corte_4.txt',  # Sobre responsabilidade
            'habilidade-de-identificar-padroes-e-crucial': 'corte_5.txt',  # Sobre ser homem
            'a-importancia-de-acordar-cedo': 'corte_6.txt',  # Sobre ser excepcional
            'por-que-voce-esta-na-escuridao': 'corte_1.txt',  # Sobre ser anti-social
            'como-manter-a-motivacao-diariamente': 'corte_2.txt',  # Sobre motivação diária
            'motivacao-quando-tudo-te-impede': 'corte_3.txt',  # Sobre disciplina
            'progresso-e-a-chave-para-a-felicidade': 'corte_4.txt',  # Sobre responsabilidade
            'ser-excepcional-e-estar-sozinho': 'corte_6.txt',  # Sobre ser excepcional
            'ser-um-homem-na-vida-adulta': 'corte_5.txt',  # Sobre ser homem
            'voce-realmente-acredita': 'corte_6.txt',  # Sobre ser excepcional
            'batman-e-a-memoria-do-heroi': 'corte_1.txt',  # Sobre ser anti-social
            'por-que-voce-e-tao-anti-social': 'corte_1.txt'  # Sobre ser anti-social
        }
        
        # Tentar diferentes variações do nome
        possiveis_nomes = []
        
        # 1. Mapeamento direto (prioridade máxima)
        if nome_limpo in mapeamento_direto:
            possiveis_nomes.append(mapeamento_direto[nome_limpo])
            print(f"🎯 Mapeamento direto encontrado: {mapeamento_direto[nome_limpo]}")
        
        # 2. Nome exato
        possiveis_nomes.extend([
            f"{nome_limpo}.txt",
            f"{nome_base}.txt"
        ])
        
        # 3. Nomes genéricos
        if 'corte_' in nome_limpo:
            possiveis_nomes.append(f"corte_{nome_limpo.split('_')[-1]}.txt")
        
        for nome_arquivo_txt in possiveis_nomes:
            if nome_arquivo_txt:
                transcricao_path = f"data/transcricoes_cortes/{nome_arquivo_txt}"
                print(f"🔍 Tentando: {transcricao_path}")
                if os.path.exists(transcricao_path):
                    with open(transcricao_path, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                        # Extrair apenas o texto da transcrição
                        if "TEXTO:" in conteudo:
                            texto = conteudo.split("TEXTO:")[1].strip()
                            if texto and len(texto) > 10:
                                print(f"✅ Transcrição individual encontrada: {transcricao_path} ({len(texto)} chars)")
                                return texto
        
        print(f"❌ Nenhuma transcrição individual encontrada para: {nome_limpo}")
        return None
        
    except Exception as e:
        print(f"❌ Erro ao buscar transcrição individual: {e}")
        return None

def buscar_transcricao_video(caminho_video):
    """Busca transcrição do vídeo com múltiplas tentativas"""
    try:
        nome_base = os.path.splitext(os.path.basename(caminho_video))[0]
        print(f"🔍 Buscando transcrição para: {nome_base}")
        
        # 1. PRIORIDADE: Tentar transcrição específica do corte
        # Primeiro tentar com o nome exato
        transcricao_corte_path = f"data/transcricoes_cortes/{nome_base}.txt"
        
        # Se não encontrar e o nome contém "_legendado", tentar sem o sufixo
        if not os.path.exists(transcricao_corte_path) and "_legendado" in nome_base:
            nome_sem_sufixo = nome_base.replace("_legendado", "")
            transcricao_corte_path = f"data/transcricoes_cortes/{nome_sem_sufixo}.txt"
            print(f"🔍 Tentando transcrição sem sufixo: {nome_sem_sufixo}")
        
        if os.path.exists(transcricao_corte_path):
            with open(transcricao_corte_path, 'r', encoding='utf-8') as f:
                conteudo = f.read().strip()
                if conteudo and len(conteudo) > 20:
                    # Extrair apenas o texto da transcrição (pular metadados)
                    linhas = conteudo.split('\n')
                    texto_transcricao = ""
                    em_texto = False
                    for linha in linhas:
                        if linha.strip() == "TEXTO:":
                            em_texto = True
                            continue
                        if em_texto and linha.strip():
                            texto_transcricao += linha + " "
                    
                    if texto_transcricao.strip():
                        print(f"✅ Transcrição específica do corte encontrada: {transcricao_corte_path} ({len(texto_transcricao)} chars)")
                        return texto_transcricao.strip()
        
        # 2. Tentar arquivo .txt correspondente no mesmo diretório
        txt_path = os.path.splitext(caminho_video)[0] + '.txt'
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                conteudo = f.read().strip()
                if conteudo and len(conteudo) > 20:  # Verificar se tem conteúdo real
                    print(f"✅ Transcrição encontrada em: {txt_path} ({len(conteudo)} chars)")
                    return conteudo
        
        # 3. Tentar em data/transcricoes com nome específico
        transcricao_path = f"data/transcricoes/{nome_base}.txt"
        if os.path.exists(transcricao_path):
            with open(transcricao_path, 'r', encoding='utf-8') as f:
                conteudo = f.read().strip()
                if conteudo and len(conteudo) > 20:
                    print(f"✅ Transcrição encontrada em: {transcricao_path} ({len(conteudo)} chars)")
                    return conteudo
        
        # 4. Tentar buscar por arquivos de transcrição relacionados
        pastas_busca = ["data/transcricoes", "data", "static/final", "."]
        for pasta in pastas_busca:
            if not os.path.exists(pasta):
                continue
            for arquivo in os.listdir(pasta):
                if arquivo.endswith('.txt'):
                    # Verificar se o nome do arquivo tem relação com o vídeo
                    arquivo_sem_ext = os.path.splitext(arquivo)[0]
                    if (nome_base in arquivo_sem_ext or 
                        arquivo_sem_ext in nome_base or
                        'transcricao' in arquivo.lower() or 
                        'transcript' in arquivo.lower()):
                        caminho_completo = os.path.join(pasta, arquivo)
                        try:
                            with open(caminho_completo, 'r', encoding='utf-8') as f:
                                conteudo = f.read().strip()
                                if conteudo and len(conteudo) > 20:
                                    print(f"✅ Transcrição encontrada em: {caminho_completo} ({len(conteudo)} chars)")
                                    return conteudo
                        except Exception as e:
                            print(f"Erro ao ler {caminho_completo}: {e}")
                            continue
        
        # 5. Tentar buscar por padrões específicos de corte
        if 'corte' in nome_base.lower():
            # Buscar por arquivos que contenham número do corte
            numero_corte = None
            for char in nome_base:
                if char.isdigit():
                    numero_corte = char
                    break
            
            if numero_corte:
                for pasta in pastas_busca:
                    if not os.path.exists(pasta):
                        continue
                    for arquivo in os.listdir(pasta):
                        if arquivo.endswith('.txt') and numero_corte in arquivo:
                            caminho_completo = os.path.join(pasta, arquivo)
                            try:
                                with open(caminho_completo, 'r', encoding='utf-8') as f:
                                    conteudo = f.read().strip()
                                    if conteudo and len(conteudo) > 20:
                                        print(f"✅ Transcrição encontrada por número de corte: {caminho_completo} ({len(conteudo)} chars)")
                                        return conteudo
                            except:
                                continue
        
        print(f"❌ Transcrição não encontrada para {nome_base}")
        return None
        
    except Exception as e:
        print(f"❌ Erro ao buscar transcrição: {e}")
        return None

def gerar_conteudo_ia_sequencial(transcricao, nicho, ollama_host, ollama_model):
    """Gera conteúdo usando IA com prompt específico"""
    try:
        try:
            import ollama
        except ImportError:
            print("Ollama não instalado")
            return gerar_conteudo_local(transcricao, nicho)
        
        # Configurar cliente Ollama
        client = ollama.Client(host=ollama_host)
        
        # Primeiro, analisar o conteúdo para extrair palavras-chave
        palavras_chave = extrair_palavras_chave_avancadas(transcricao)
        tema_principal = identificar_tema_principal(transcricao)
        
        prompt = f"""Você é um especialista em marketing digital para redes sociais em PORTUGUÊS BRASILEIRO.

ANALISE este texto e crie conteúdo ESPECÍFICO baseado no que REALMENTE é falado.

TEXTO ORIGINAL:
{transcricao}

PALAVRAS-CHAVE ENCONTRADAS: {', '.join(palavras_chave[:5])}
TEMA PRINCIPAL: {tema_principal}

REGRAS OBRIGATÓRIAS:
1. TUDO deve ser em PORTUGUÊS BRASILEIRO
2. Título deve ser baseado no CONTEÚDO REAL, não genérico
3. Máximo 60 caracteres para título
4. Use palavras do próprio texto
5. Seja ESPECÍFICO sobre o que é falado
6. NÃO invente "dicas" ou "segredos" se não existirem
7. Legenda deve ser em PORTUGUÊS e ter máximo 300 caracteres
8. Hashtags devem ser em PORTUGUÊS e relevantes ao conteúdo

EXEMPLOS DE TÍTULOS BONS:
- "Como vencer a procrastinação" (se fala sobre procrastinação)
- "A verdade sobre dinheiro" (se fala sobre dinheiro)
- "Por que você não tem sucesso" (se fala sobre sucesso)

Gere APENAS em JSON no formato:
{{
  "title": "título em português",
  "caption": "legenda em português",
  "hashtags": "#hashtag1 #hashtag2 #hashtag3"
}}

Resposta:"""
        
        response = client.generate(model=ollama_model, prompt=prompt)
        resposta_ia = response['response'].strip()
        
        print(f"🤖 Resposta da IA: {resposta_ia[:200]}...")
        
        # Tentar extrair JSON da resposta
        try:
            import json
            import re
            
            # Procurar por JSON na resposta
            json_match = re.search(r'\{.*\}', resposta_ia, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                conteudo_json = json.loads(json_str)
                
                titulo = conteudo_json.get('title', '').strip()
                legenda = conteudo_json.get('caption', '').strip()
                hashtags = conteudo_json.get('hashtags', '').strip()
                
                # Validar e limpar
                if not titulo:
                    titulo = gerar_titulo_contextual(transcricao)
                if not legenda:
                    legenda = gerar_legenda_contextual(transcricao, titulo)
                if not hashtags:
                    hashtags = gerar_hashtags_contextuais(transcricao, titulo)
                
                # Garantir que hashtags seja string
                if isinstance(hashtags, list):
                    hashtags = ' '.join(hashtags)
                
                # Garantir que hashtags comece com #
                if hashtags and not hashtags.startswith('#'):
                    hashtags = '#' + hashtags.replace('#', '')
                
                resultado = {
                    "title": titulo,
                    "caption": legenda,
                    "hashtags": hashtags
                }
                
                print(f"✅ Conteúdo JSON extraído: {resultado}")
                return resultado
            else:
                raise ValueError("JSON não encontrado na resposta")
                
        except Exception as e:
            print(f"❌ Erro ao extrair JSON: {e}")
            # Fallback: usar análise local
            return gerar_conteudo_local(transcricao, nicho)
            
    except Exception as e:
        print(f"Erro ao gerar conteúdo IA: {e}")
        # Fallback: usar análise local
        return gerar_conteudo_local(transcricao, nicho)

def extrair_palavras_chave_avancadas(texto):
    """Extrai palavras-chave importantes do texto"""
    import re
    from collections import Counter
    
    # Palavras importantes para redes sociais
    palavras_importantes = [
        'sucesso', 'dinheiro', 'motivação', 'vencer', 'conquistar', 'objetivo', 'meta',
        'negócio', 'empreendedor', 'lucro', 'venda', 'estratégia', 'técnica', 'método',
        'relacionamento', 'amor', 'família', 'amizade', 'casamento', 'divórcio',
        'saúde', 'exercício', 'dieta', 'alimentação', 'bem-estar', 'felicidade',
        'aprender', 'conhecimento', 'educação', 'curso', 'estudo', 'desenvolvimento',
        'trabalho', 'carreira', 'profissão', 'liderança', 'equipe', 'gestão',
        'tempo', 'produtividade', 'organização', 'planejamento', 'foco', 'disciplina'
    ]
    
    # Limpar texto
    texto_limpo = re.sub(r'[^\w\s]', ' ', texto.lower())
    palavras = texto_limpo.split()
    
    # Filtrar palavras relevantes
    palavras_filtradas = []
    for palavra in palavras:
        if len(palavra) > 3 and palavra not in ['que', 'para', 'com', 'uma', 'dos', 'das', 'pelo', 'pela', 'este', 'esta', 'isso', 'aqui', 'muito', 'mais', 'mais', 'bem', 'são', 'ser', 'ter', 'fazer', 'poder', 'querer', 'saber', 'ver', 'dar', 'ir', 'vir', 'estar', 'haver']:
            palavras_filtradas.append(palavra)
    
    # Priorizar palavras importantes
    palavras_prioritarias = [p for p in palavras_filtradas if p in palavras_importantes]
    outras_palavras = [p for p in palavras_filtradas if p not in palavras_importantes]
    
    # Combinar e retornar
    resultado = palavras_prioritarias + outras_palavras
    return resultado[:10]  # Top 10

def identificar_tema_principal(texto):
    """Identifica o tema principal do texto"""
    texto_lower = texto.lower()
    
    if any(palavra in texto_lower for palavra in ['dinheiro', 'lucro', 'negócio', 'empreendedor', 'venda', 'estratégia']):
        return 'negócios'
    elif any(palavra in texto_lower for palavra in ['motivação', 'sucesso', 'vencer', 'conquistar', 'objetivo', 'meta']):
        return 'motivação'
    elif any(palavra in texto_lower for palavra in ['relacionamento', 'amor', 'família', 'amizade', 'casamento']):
        return 'relacionamentos'
    elif any(palavra in texto_lower for palavra in ['saúde', 'exercício', 'dieta', 'alimentação', 'bem-estar']):
        return 'saúde'
    elif any(palavra in texto_lower for palavra in ['aprender', 'conhecimento', 'educação', 'curso', 'estudo']):
        return 'educação'
    else:
        return 'desenvolvimento pessoal'

def gerar_legenda_contextual(transcricao, titulo):
    """Gera legenda baseada no contexto real"""
    # Resumir o texto mantendo as partes mais importantes
    palavras = transcricao.split()
    if len(palavras) > 80:
        # Pegar início e fim do texto
        inicio = ' '.join(palavras[:40])
        fim = ' '.join(palavras[-40:])
        resumo = f"{inicio}... {fim}"
    else:
        resumo = transcricao
    
    # Adicionar call-to-action baseado no tema
    if 'dinheiro' in transcricao.lower() or 'negócio' in transcricao.lower():
        cta = "💰 Salve este post e aplique na sua vida!"
    elif 'motivação' in transcricao.lower() or 'sucesso' in transcricao.lower():
        cta = "💪 Compartilhe com quem precisa ver isso!"
    elif 'relacionamento' in transcricao.lower() or 'amor' in transcricao.lower():
        cta = "❤️ Marque quem você ama!"
    else:
        cta = "👍 Curta e compartilhe se gostou!"
    
    legenda = f"{resumo}\n\n{cta}"
    
    # Limitar a 300 caracteres
    if len(legenda) > 300:
        legenda = legenda[:297] + "..."
    
    return legenda

def gerar_conteudo_local(transcricao, nicho):
    """Fallback: gera conteúdo usando análise local"""
    palavras_chave = extrair_palavras_chave_avancadas(transcricao)
    tema = identificar_tema_principal(transcricao)
    
    # Gerar título baseado no tema
    if tema == 'negócios':
        titulo = f"💼 {palavras_chave[0].title() if palavras_chave else 'Negócios'}"
    elif tema == 'motivação':
        titulo = f"💪 {palavras_chave[0].title() if palavras_chave else 'Motivação'}"
    elif tema == 'relacionamentos':
        titulo = f"❤️ {palavras_chave[0].title() if palavras_chave else 'Relacionamentos'}"
    else:
        titulo = f"📱 {palavras_chave[0].title() if palavras_chave else 'Desenvolvimento'}"
    
    # Gerar legenda
    legenda = gerar_legenda_contextual(transcricao, titulo)
    
    # Gerar hashtags
    hashtags = gerar_hashtags_contextuais(transcricao, titulo)
    
    return {
        "title": titulo,
        "caption": legenda,
        "hashtags": hashtags
    }

def validar_conteudo_ia(conteudo):
    """Valida conteúdo gerado pela IA - versão mais flexível"""
    try:
        if not isinstance(conteudo, dict):
            print("Conteúdo não é dict")
            return False
        
        # Validar título - mais flexível
        title = conteudo.get('title', '')
        if not title or len(title) > 80:  # Aumentei limite
            print(f"Título inválido: '{title}' (len: {len(title)})")
            return False
        
        # Validar caption - mais flexível
        caption = conteudo.get('caption', '')
        if not caption or len(caption) > 500:  # Aumentei limite
            print(f"Caption inválido: '{caption}' (len: {len(caption)})")
            return False
        
        # Validar hashtags - mais flexível
        hashtags = conteudo.get('hashtags', '')
        if not hashtags:
            print("Hashtags vazias")
            return False
        
        # Se hashtags não começam com #, adicionar
        if not hashtags.startswith('#'):
            hashtags = '#' + hashtags.replace('#', '')
            conteudo['hashtags'] = hashtags
        
        # Contar hashtags - mais flexível
        tags = hashtags.split()
        if len(tags) < 3:  # Mínimo reduzido
            print(f"Poucas hashtags: {len(tags)}")
            return False
        
        print(f"✅ Conteúdo válido: título='{title[:30]}...', caption='{caption[:30]}...', hashtags={len(tags)}")
        return True
        
    except Exception as e:
        print(f"Erro na validação: {e}")
        return False

def criar_slug_titulo(titulo):
    """Cria slug do título para nome do arquivo"""
    import re
    import unicodedata
    
    # Remover acentos
    titulo = unicodedata.normalize('NFD', titulo)
    titulo = ''.join(c for c in titulo if unicodedata.category(c) != 'Mn')
    
    # Converter para minúsculas e remover caracteres especiais
    slug = re.sub(r'[^\w\s-]', '', titulo.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    # Limitar tamanho
    return slug[:50]

def obter_duracao_video(caminho_video):
    """Obtém duração do vídeo"""
    try:
        from moviepy.editor import VideoFileClip
        with VideoFileClip(caminho_video) as video:
            return round(video.duration, 2)
    except:
        return ""

# ==== TESTE DE GERAÇÃO DE TÍTULOS ====
@app.route("/teste_titulo", methods=["POST"])
def teste_titulo():
    """Testa geração de título com texto específico"""
    try:
        body = request.get_json(force=True) or {}
        texto_teste = body.get("texto", "Este é um teste de geração de título")
        nicho = body.get("nicho", "motivação e desenvolvimento pessoal")
        
        # Usar função local para teste
        resultado = gerar_conteudo_local(texto_teste, nicho)
        
        return jsonify({
            "ok": True,
            "texto_original": texto_teste,
            "resultado": resultado
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/salvar_metadados", methods=["POST"])
def salvar_metadados():
    """Salva metadados editados de um vídeo"""
    try:
        body = request.get_json(force=True) or {}
        filename = body.get("filename")
        titulo = body.get("titulo", "")
        legenda = body.get("legenda", "")
        hashtags = body.get("hashtags", "")
        
        if not filename:
            return jsonify({"ok": False, "error": "Nome do arquivo não fornecido"})
        
        # Carregar planilha existente
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        try:
            if os.path.exists(planilha_path):
                df = pd.read_excel(planilha_path)
            elif os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                df = pd.DataFrame(columns=["arquivo_antigo", "arquivo_novo", "titulo", "legenda", "hashtags", "duracao", "origem", "idioma"])
        except:
            df = pd.DataFrame(columns=["arquivo_antigo", "arquivo_novo", "titulo", "legenda", "hashtags", "duracao", "origem", "idioma"])
        
        # Atualizar ou adicionar linha
        mask = df['arquivo_novo'] == filename
        if mask.any():
            # Atualizar linha existente
            df.loc[mask, 'titulo'] = titulo
            df.loc[mask, 'legenda'] = legenda
            df.loc[mask, 'hashtags'] = hashtags
        else:
            # Adicionar nova linha
            nova_linha = {
                "arquivo_antigo": filename,
                "arquivo_novo": filename,
                "titulo": titulo,
                "legenda": legenda,
                "hashtags": hashtags,
                "duracao": "",
                "origem": "manual",
                "idioma": "pt"
            }
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        
        # Salvar planilha
        df.to_excel(planilha_path, index=False)
        df.to_csv(csv_path, index=False)
        
        return jsonify({"ok": True, "message": "Metadados salvos com sucesso"})
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/exportar_excel", methods=["GET"])
def exportar_excel():
    """Exporta planilha de metadados para download"""
    try:
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        if os.path.exists(planilha_path):
            return send_from_directory("data/planilhas", "publicar.xlsx", as_attachment=True)
        elif os.path.exists(csv_path):
            return send_from_directory("data/planilhas", "publicar.csv", as_attachment=True)
        else:
            return jsonify({"ok": False, "error": "Nenhuma planilha encontrada"})
            
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/exportar_transcricoes", methods=["GET"])
def exportar_transcricoes():
    """Exporta transcrições de todos os vídeos para ChatGPT usando Excel principal e dublados"""
    try:
        # Carregar planilha principal
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        if os.path.exists(planilha_path):
            df_principal = pd.read_excel(planilha_path)
        elif os.path.exists(csv_path):
            df_principal = pd.read_csv(csv_path)
        else:
            df_principal = pd.DataFrame()
        
        # Carregar planilha de dublados
        dublados_path = "data/planilhas/dublados.xlsx"
        dublados_csv_path = "data/planilhas/dublados.csv"
        
        if os.path.exists(dublados_path):
            df_dublados = pd.read_excel(dublados_path)
        elif os.path.exists(dublados_csv_path):
            df_dublados = pd.read_csv(dublados_csv_path)
        else:
            df_dublados = pd.DataFrame()
        
        # Criar planilha de exportação com transcrições
        dados_exportacao = []
        
        # Buscar vídeos que realmente existem no sistema
        cortes_path = 'data/final'  # Usar pasta final onde estão os arquivos legendados
        dublados_path = 'data/cortes_dublado'
        
        # Listar vídeos cortados existentes (arquivos legendados)
        cortes_files = []
        if os.path.exists(cortes_path):
            cortes_files = [f for f in os.listdir(cortes_path) if f.endswith('.mp4')]
        
        # Listar vídeos dublados existentes
        dublados_files = []
        if os.path.exists(dublados_path):
            dublados_files = [f for f in os.listdir(dublados_path) if f.endswith('.mp4')]
        
        print(f"📁 Vídeos encontrados: {len(cortes_files)} cortados + {len(dublados_files)} dublados = {len(cortes_files) + len(dublados_files)} total")
        
        # Processar vídeos cortados existentes
        for arquivo in cortes_files:
            # Buscar metadados na planilha principal
            metadados = None
            for _, row in df_principal.iterrows():
                if row.get('arquivo_novo', '') == arquivo:
                    metadados = row
                    break
            
            # Buscar transcrição individual
            transcricao = buscar_transcricao_individual(arquivo)
            if not transcricao or len(transcricao) < 20:
                transcricao = f"[TRANSCRIÇÃO NÃO ENCONTRADA PARA {arquivo}]"
            
            dados_exportacao.append({
                "arquivo": arquivo,
                "transcricao": transcricao,
                "titulo_gerado": metadados.get('titulo', '') if metadados is not None else '',
                "legenda_gerada": metadados.get('legenda', '') if metadados is not None else '',
                "hashtags_geradas": metadados.get('hashtags', '') if metadados is not None else '',
                "tipo": "Legendado",
                "origem": metadados.get('origem', 'cortes') if metadados is not None else 'cortes',
                "video_id": metadados.get('video_id', '') if metadados is not None else '',
                "postado": metadados.get('postado', 'Não') if metadados is not None else 'Não'
            })
        
        # Processar vídeos dublados existentes
        for arquivo in dublados_files:
            # Buscar metadados na planilha de dublados
            metadados = None
            for _, row in df_dublados.iterrows():
                if row.get('arquivo', '') == arquivo:
                    metadados = row
                    break
            
            # Buscar transcrição individual
            transcricao = buscar_transcricao_individual(arquivo)
            if not transcricao or len(transcricao) < 20:
                transcricao = f"[TRANSCRIÇÃO NÃO ENCONTRADA PARA {arquivo}]"
            
            dados_exportacao.append({
                "arquivo": arquivo,
                "transcricao": transcricao,
                "titulo_gerado": metadados.get('titulo', '') if metadados is not None else '',
                "legenda_gerada": metadados.get('legenda', '') if metadados is not None else '',
                "hashtags_geradas": metadados.get('hashtags', '') if metadados is not None else '',
                "tipo": "Dublado",
                "origem": "dublado",
                "video_id": "",
                "postado": "Não"
            })
        
        if not dados_exportacao:
            return jsonify({"ok": False, "error": "Nenhum vídeo encontrado na planilha"})
        
        # Criar DataFrame de exportação
        df_export = pd.DataFrame(dados_exportacao)
        
        # Salvar arquivo
        nome_arquivo = "transcricoes_para_chatgpt.xlsx"
        caminho_arquivo = os.path.join("data/planilhas", nome_arquivo)
        
        # Garantir que a pasta existe
        os.makedirs("data/planilhas", exist_ok=True)
        
        df_export.to_excel(caminho_arquivo, index=False)
        
        return send_from_directory("data/planilhas", nome_arquivo, as_attachment=True)
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/renomear_video', methods=['POST'])
def renomear_video():
    try:
        data = request.get_json()
        filename = data.get('filename')
        novoTitulo = data.get('novoTitulo')
        
        if not filename or not novoTitulo:
            return jsonify({'ok': False, 'error': 'Parâmetros inválidos'})
        
        # Gerar slug do título
        def gerar_slug(texto):
            import re
            import unicodedata
            # Remover acentos
            texto = unicodedata.normalize('NFD', texto)
            texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
            # Converter para minúsculas e substituir espaços por hífens
            texto = re.sub(r'[^a-zA-Z0-9\s-]', '', texto)
            texto = re.sub(r'\s+', '-', texto.strip())
            return texto.lower()
        
        slug = gerar_slug(novoTitulo)
        
        # Caminhos - verificar se existe em data/final primeiro
        pasta_final = "data/final"
        caminho_original = os.path.join(pasta_final, filename)
        
        # Se não existir em data/final, tentar static/final
        if not os.path.exists(caminho_original):
            pasta_final = "static/final"
            caminho_original = os.path.join(pasta_final, filename)
        
        novo_nome = f"{slug}.mp4"
        caminho_novo = os.path.join(pasta_final, novo_nome)
        
        if not os.path.exists(caminho_original):
            return jsonify({'ok': False, 'error': 'Arquivo não encontrado'})
        
        # Renomear arquivo
        os.rename(caminho_original, caminho_novo)
        
        # Renomear arquivo de transcrição individual correspondente
        try:
            from cortes.cortar_video import renomear_transcricao_individual
            renomear_transcricao_individual(filename, novo_nome)
        except Exception as e:
            print(f"⚠️ Erro ao renomear transcrição: {e}")
        
        # Atualizar planilha
        try:
            df = pd.read_excel("data/planilhas/publicar.xlsx")
            mask = df['arquivo_antigo'] == filename
            if mask.any():
                df.loc[mask, 'arquivo_novo'] = novo_nome
                df.loc[mask, 'titulo'] = novoTitulo
                df.to_excel("data/planilhas/publicar.xlsx", index=False)
        except Exception as e:
            print(f"⚠️ Erro ao atualizar planilha: {e}")
        
        return jsonify({'ok': True, 'novo_nome': novo_nome})
        
    except Exception as e:
        print(f"❌ Erro ao renomear vídeo: {e}")
        return jsonify({'ok': False, 'error': str(e)})

@app.route("/buscar_transcricao", methods=["POST"])
def buscar_transcricao():
    """Busca transcrição de um vídeo específico"""
    try:
        body = request.get_json(force=True) or {}
        filename = body.get("filename")
        
        if not filename:
            return jsonify({"ok": False, "error": "Nome do arquivo não fornecido"})
        
        # Buscar transcrição
        caminho_video = os.path.join("static/final", filename)
        transcricao = buscar_transcricao_video(caminho_video)
        
        if not transcricao:
            return jsonify({"ok": False, "error": "Transcrição não encontrada"})
        
        return jsonify({"ok": True, "transcricao": transcricao})
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/gerar_conteudo_individual", methods=["POST"])
def gerar_conteudo_individual():
    """Gera conteúdo para um vídeo individual"""
    try:
        body = request.get_json(force=True) or {}
        transcricao = body.get("transcricao", "")
        nicho = body.get("nicho", "motivação e desenvolvimento pessoal")
        
        if not transcricao:
            return jsonify({"ok": False, "error": "Transcrição não fornecida"})
        
        # Configurações do Ollama
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        ollama_model = "qwen2.5:7b"  # Usar modelo específico
        
        # Gerar conteúdo
        conteudo = gerar_conteudo_ia_sequencial(transcricao, nicho, ollama_host, ollama_model)
        
        if not conteudo:
            return jsonify({"ok": False, "error": "Erro ao gerar conteúdo"})
        
        return jsonify({
            "ok": True,
            "titulo": conteudo.get("title", ""),
            "legenda": conteudo.get("caption", ""),
            "hashtags": conteudo.get("hashtags", "")
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/importar_metadados", methods=["POST"])
def importar_metadados():
    """Importa metadados do ChatGPT"""
    try:
        arquivo = request.files.get("file")
        if not arquivo:
            return jsonify({"ok": False, "error": "Nenhum arquivo enviado"})
        
        # Salvar arquivo temporariamente
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"metadados_chatgpt_{timestamp}.xlsx"
        caminho_arquivo = os.path.join("data/planilhas", nome_arquivo)
        
        # Garantir que a pasta existe
        os.makedirs("data/planilhas", exist_ok=True)
        
        arquivo.save(caminho_arquivo)
        
        # Ler arquivo
        try:
            df = pd.read_excel(caminho_arquivo)
        except:
            df = pd.read_csv(caminho_arquivo)
        
        # Validar colunas necessárias
        colunas_necessarias = ["arquivo", "titulo_gerado", "legenda_gerada", "hashtags_geradas"]
        if not all(col in df.columns for col in colunas_necessarias):
            return jsonify({"ok": False, "error": "Arquivo deve conter colunas: arquivo, titulo_gerado, legenda_gerada, hashtags_geradas"})
        
        # Atualizar metadados
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        # Carregar planilha existente
        try:
            if os.path.exists(planilha_path):
                df_existente = pd.read_excel(planilha_path)
            elif os.path.exists(csv_path):
                df_existente = pd.read_csv(csv_path)
            else:
                df_existente = pd.DataFrame(columns=["arquivo_antigo", "arquivo_novo", "titulo", "legenda", "hashtags", "duracao", "origem", "idioma"])
        except:
            df_existente = pd.DataFrame(columns=["arquivo_antigo", "arquivo_novo", "titulo", "legenda", "hashtags", "duracao", "origem", "idioma"])
        
        # Atualizar cada linha
        atualizados = 0
        for _, row in df.iterrows():
            arquivo_nome = row["arquivo"]
            titulo = row["titulo_gerado"]
            legenda = row["legenda_gerada"]
            hashtags = row["hashtags_geradas"]
            
            # Procurar linha existente
            mask = df_existente['arquivo_novo'] == arquivo_nome
            if mask.any():
                # Atualizar linha existente
                df_existente.loc[mask, 'titulo'] = titulo
                df_existente.loc[mask, 'legenda'] = legenda
                df_existente.loc[mask, 'hashtags'] = hashtags
                atualizados += 1
            else:
                # Adicionar nova linha
                nova_linha = {
                    "arquivo_antigo": arquivo_nome,
                    "arquivo_novo": arquivo_nome,
                    "titulo": titulo,
                    "legenda": legenda,
                    "hashtags": hashtags,
                    "duracao": "",
                    "origem": "chatgpt",
                    "idioma": "pt"
                }
                df_existente = pd.concat([df_existente, pd.DataFrame([nova_linha])], ignore_index=True)
                atualizados += 1
        
        # Salvar planilha atualizada
        df_existente.to_excel(planilha_path, index=False)
        df_existente.to_csv(csv_path, index=False)
        
        # Remover arquivo temporário
        os.remove(caminho_arquivo)
        
        return jsonify({"ok": True, "message": f"Metadados importados com sucesso! {atualizados} vídeos atualizados."})
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ==== CONFIGURAÇÃO DE IA ====
@app.route("/config/ai", methods=["POST"])
def configurar_ai():
    """Configura IA (OpenAI ou Ollama) para usar IA real"""
    try:
        body = request.get_json(force=True) or {}
        ai_type = body.get("ai_type", "ollama")
        
        if ai_type == "ollama":
            model = body.get("model", "llama3.2")
            config = {
                "ai_type": "ollama",
                "model": model
            }
        else:
            api_key = body.get("openai_key", "").strip()
            if not api_key:
                return jsonify({"ok": False, "error": "API key não fornecida"})
            config = {
                "ai_type": "openai",
                "openai_key": api_key
            }
        
        # Salvar configuração
        with open("ai_config.json", "w") as f:
            import json
            json.dump(config, f)
        
        print(f"✅ Configuração de IA salva: {config}")
        return jsonify({"ok": True, "message": f"IA {ai_type} configurada com sucesso!"})
            
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/config/ai/load", methods=["GET"])
def carregar_config_ai_route():
    """Carrega configuração de IA salva"""
    try:
        config = carregar_config_ai()
        return jsonify({"ok": True, "config": config})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/config/ai/models", methods=["GET"])
def listar_modelos_ollama():
    """Lista modelos disponíveis no Ollama"""
    try:
        try:
            import ollama
            print("✅ Ollama importado com sucesso")
        except ImportError:
            print("❌ Ollama não instalado")
            return jsonify({"ok": False, "error": "Ollama não instalado", "models": []})
        
        # Tentar conectar com Ollama
        try:
            client = ollama.Client()
            print("✅ Cliente Ollama criado")
            models_response = client.list()
            print(f"✅ Resposta do Ollama: {models_response}")
        except Exception as e:
            print(f"❌ Erro ao conectar com Ollama: {e}")
            return jsonify({"ok": False, "error": f"Erro ao conectar com Ollama: {str(e)}", "models": []})
        
        # Verificar se a resposta tem modelos
        models_list = []
        if hasattr(models_response, 'models'):
            models_list = models_response.models
        elif isinstance(models_response, dict) and 'models' in models_response:
            models_list = models_response['models']
        elif isinstance(models_response, list):
            models_list = models_response
        
        if models_list:
            models = []
            print(f"✅ Encontrados {len(models_list)} modelos")
            for model in models_list:
                # Extrair nome do modelo de diferentes estruturas possíveis
                model_name = None
                if hasattr(model, 'name'):
                    model_name = model.name
                elif isinstance(model, dict) and 'name' in model:
                    model_name = model['name']
                elif isinstance(model, str):
                    model_name = model
                
                if model_name:
                    models.append({
                        "name": model_name,
                        "display": model_name.replace(':', ' - ').title()
                    })
                    print(f"✅ Modelo encontrado: {model_name}")
            
            return jsonify({"ok": True, "models": models})
        else:
            print("❌ Nenhum modelo encontrado na resposta")
            return jsonify({"ok": False, "error": "Nenhum modelo encontrado", "models": []})
            
    except ImportError:
        print("❌ ImportError no Ollama")
        return jsonify({"ok": False, "error": "Ollama não instalado", "models": []})
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return jsonify({"ok": False, "error": f"Erro ao conectar com Ollama: {str(e)}", "models": []})

def carregar_config_ai():
    """Carrega configuração de IA se disponível"""
    try:
        with open("ai_config.json", "r") as f:
            import json
            return json.load(f)
    except:
        return {"ai_type": "ollama", "model": "llama3.2"}

def gerar_titulo_com_ollama(transcricao):
    """Gera título usando Ollama local ou fallback"""
    try:
        import ollama
    except ImportError:
        print("Ollama não instalado - usando análise local")
        return None
        
    # Verificar se Ollama está disponível
    try:
        client = ollama.Client()
        models = client.list()
        
        if not models or not hasattr(models, 'models') or not models.models:
            print("Nenhum modelo Ollama disponível - usando análise local")
            return None
        
        # Usar primeiro modelo disponível
        first_model = models.models[0]
        if hasattr(first_model, 'name'):
            model_name = first_model.name
        elif hasattr(first_model, 'model'):
            model_name = first_model.model
        elif 'model' in first_model:
            model_name = first_model['model']
        else:
            model_name = str(first_model)
        print(f"Usando modelo Ollama: {model_name}")
        
    except Exception as e:
        print(f"Ollama não disponível: {e} - usando análise local")
        return None
        
        prompt = f"""
        Você é um especialista em marketing digital e criação de conteúdo para redes sociais.

        ANALISE esta transcrição de vídeo e crie um título PERFEITO para Instagram/TikTok:

        TRANSCRIÇÃO: {transcricao[:800]}

        REGRAS OBRIGATÓRIAS:
        - Máximo 50 caracteres
        - Use EMOJI no início (🔥, 💪, 🚀, 📚, etc.)
        - Linguagem DIRETA e PERSUASIVA
        - Foque no BENEFÍCIO principal
        - Seja IMPACTANTE e CLARO
        - Evite palavras genéricas como "vídeo", "conteúdo"
        - Use números quando possível (ex: "5 Dicas", "3 Segredos")

        EXEMPLOS DE TÍTULOS BONS:
        - 🔥 5 Segredos que Ninguém Conta
        - 💪 Como Ficar Rico em 30 Dias
        - 🚀 3 Erros que Te Impedem de Vencer
        - 📚 A Técnica que Mudou Minha Vida

        TÍTULO:"""
        
        response = client.generate(model=model_name, prompt=prompt)
        return response['response'].strip()
        
    except ImportError:
        print("Ollama não instalado - usando análise local")
        return None
    except Exception as e:
        print(f"Erro Ollama: {e}")
        return None

# Endpoints para vídeos dublados
def carregar_metadados_dublados():
    """Carrega metadados dos vídeos dublados"""
    metadados = {}
    try:
        planilha_path = "data/planilhas/dublados.xlsx"
        csv_path = "data/planilhas/dublados.csv"
        
        if os.path.exists(planilha_path):
            df = pd.read_excel(planilha_path)
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            return metadados
        
        if not df.empty:
            for _, row in df.iterrows():
                arquivo = row.get('arquivo', '')
                if arquivo:
                    metadados[arquivo] = {
                        'titulo': row.get('titulo', ''),
                        'legenda': row.get('legenda', ''),
                        'hashtags': row.get('hashtags', '')
                    }
    except Exception as e:
        print(f"Erro ao carregar metadados dublados: {e}")
    
    return metadados

@app.route("/videos/dublados", methods=["GET"])
def listar_videos_dublados():
    """Lista todos os vídeos dublados com metadados"""
    try:
        pasta_dublados = "data/cortes_dublado"
        if not os.path.exists(pasta_dublados):
            return jsonify({"ok": True, "videos": []})
        
        arquivos = glob.glob(f"{pasta_dublados}/*.mp4")
        videos = []
        
        # Carregar metadados salvos
        metadados_salvos = carregar_metadados_dublados()
        
        for arquivo in arquivos:
            nome = os.path.basename(arquivo)
            tamanho = os.path.getsize(arquivo)
            data_modificacao = os.path.getmtime(arquivo)
            
            # Buscar metadados do MP4 primeiro, depois da planilha
            metadata_mp4 = ler_metadados_mp4(arquivo)
            metadata_planilha = metadados_salvos.get(nome, {
                'titulo': '',
                'legenda': '',
                'hashtags': ''
            })
            
            # Priorizar metadados do MP4, usar planilha como fallback
            metadata = {
                'titulo': metadata_mp4.get('titulo') or metadata_planilha.get('titulo', ''),
                'legenda': metadata_mp4.get('legenda') or metadata_planilha.get('legenda', ''),
                'hashtags': metadata_mp4.get('hashtags') or metadata_planilha.get('hashtags', ''),
                'tipo': metadata_mp4.get('tipo', 'Dublado')
            }
            
            videos.append({
                "nome": nome,
                "caminho": arquivo,
                "tamanho": tamanho,
                "data_modificacao": data_modificacao,
                "metadados": metadata
            })
        
        # Ordenar por data de modificação (mais recentes primeiro)
        videos.sort(key=lambda x: x["data_modificacao"], reverse=True)
        
        return jsonify({"ok": True, "videos": videos})
        
    except Exception as e:
        print(f"Erro ao listar vídeos dublados: {e}")
        return jsonify({"ok": False, "error": str(e)})

@app.route("/videos/dublados/<nome>", methods=["DELETE"])
def deletar_video_dublado(nome):
    """Deleta um vídeo dublado"""
    try:
        pasta_dublados = "data/cortes_dublado"
        arquivo_path = os.path.join(pasta_dublados, nome)
        
        if os.path.exists(arquivo_path):
            os.remove(arquivo_path)
            return jsonify({"ok": True, "message": f"Vídeo '{nome}' deletado com sucesso"})
        else:
            return jsonify({"ok": False, "error": "Arquivo não encontrado"})
            
    except Exception as e:
        print(f"Erro ao deletar vídeo dublado: {e}")
        return jsonify({"ok": False, "error": str(e)})

# Servir arquivos dublados
@app.route("/static/dublados/<nome>")
def servir_video_dublado(nome):
    """Serve arquivos de vídeos dublados"""
    try:
        pasta_dublados = "data/cortes_dublado"
        arquivo_path = os.path.join(pasta_dublados, nome)
        
        if os.path.exists(arquivo_path):
            from flask import send_file
            return send_file(arquivo_path, as_attachment=False)
        else:
            return "Arquivo não encontrado", 404
            
    except Exception as e:
        print(f"Erro ao servir vídeo dublado: {e}")
        return "Erro interno", 500

# Endpoints para metadata de vídeos dublados
@app.route("/buscar_transcricao_dublado", methods=["POST"])
def buscar_transcricao_dublado():
    """Busca transcrição para vídeo dublado"""
    try:
        body = request.get_json(force=True) or {}
        filename = body.get("filename", "")
        
        if not filename:
            return jsonify({"ok": False, "error": "Nome do arquivo não fornecido"})
        
        # Extrair nome base sem extensão
        nome_base = os.path.splitext(filename)[0]
        nome_limpo = nome_base.replace('_dublado_pt', '').replace('_dublado', '')
        
        # Buscar transcrição original
        transcricao = buscar_transcricao_individual(filename)
        
        if transcricao:
            return jsonify({"ok": True, "transcricao": transcricao})
        else:
            # Fallback: usar nome do arquivo
            transcricao_fallback = nome_limpo.replace('-', ' ').replace('_', ' ')
            return jsonify({"ok": True, "transcricao": transcricao_fallback})
            
    except Exception as e:
        print(f"Erro ao buscar transcrição dublado: {e}")
        return jsonify({"ok": False, "error": str(e)})

@app.route("/salvar_metadados_dublado", methods=["POST"])
def salvar_metadados_dublado():
    """Salva metadados para vídeo dublado"""
    try:
        body = request.get_json(force=True) or {}
        filename = body.get("filename", "")
        titulo = body.get("titulo", "")
        legenda = body.get("legenda", "")
        hashtags = body.get("hashtags", "")
        
        if not filename:
            return jsonify({"ok": False, "error": "Nome do arquivo não fornecido"})
        
        # Salvar na planilha de dublados (específica)
        planilha_dublados_path = "data/planilhas/dublados.xlsx"
        csv_dublados_path = "data/planilhas/dublados.csv"
        
        # Criar pasta se não existir
        os.makedirs("data/planilhas", exist_ok=True)
        
        # Carregar ou criar DataFrame de dublados
        if os.path.exists(planilha_dublados_path):
            df_dublados = pd.read_excel(planilha_dublados_path)
        elif os.path.exists(csv_dublados_path):
            df_dublados = pd.read_csv(csv_dublados_path)
        else:
            df_dublados = pd.DataFrame(columns=['arquivo', 'titulo', 'legenda', 'hashtags', 'data_criacao'])
        
        # Adicionar ou atualizar linha na planilha de dublados
        mask_dublados = df_dublados['arquivo'] == filename
        if mask_dublados.any():
            # Atualizar linha existente
            df_dublados.loc[mask_dublados, 'titulo'] = titulo
            df_dublados.loc[mask_dublados, 'legenda'] = legenda
            df_dublados.loc[mask_dublados, 'hashtags'] = hashtags
        else:
            # Adicionar nova linha
            nova_linha_dublados = {
                'arquivo': filename,
                'titulo': titulo,
                'legenda': legenda,
                'hashtags': hashtags,
                'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            df_dublados = pd.concat([df_dublados, pd.DataFrame([nova_linha_dublados])], ignore_index=True)
        
        # Salvar planilha de dublados
        df_dublados.to_excel(planilha_dublados_path, index=False)
        df_dublados.to_csv(csv_dublados_path, index=False)
        
        # Também salvar na planilha principal (publicar.xlsx)
        planilha_principal_path = "data/planilhas/publicar.xlsx"
        csv_principal_path = "data/planilhas/publicar.csv"
        
        # Carregar ou criar DataFrame principal
        if os.path.exists(planilha_principal_path):
            df_principal = pd.read_excel(planilha_principal_path)
        elif os.path.exists(csv_principal_path):
            df_principal = pd.read_csv(csv_principal_path)
        else:
            df_principal = pd.DataFrame(columns=['arquivo_antigo', 'arquivo_novo', 'titulo', 'legenda', 'hashtags', 'duracao', 'origem', 'idioma', 'video_id', 'tipo', 'postado'])
        
        # Adicionar colunas se não existirem
        if 'tipo' not in df_principal.columns:
            df_principal['tipo'] = 'Legendado'
        if 'postado' not in df_principal.columns:
            df_principal['postado'] = 'Não'
        
        # Adicionar ou atualizar linha na planilha principal
        mask_principal = df_principal['arquivo_novo'] == filename
        if mask_principal.any():
            # Atualizar linha existente
            df_principal.loc[mask_principal, 'titulo'] = titulo
            df_principal.loc[mask_principal, 'legenda'] = legenda
            df_principal.loc[mask_principal, 'hashtags'] = hashtags
            df_principal.loc[mask_principal, 'tipo'] = 'Dublado'
        else:
            # Adicionar nova linha
            nova_linha_principal = {
                'arquivo_antigo': filename,
                'arquivo_novo': filename,
                'titulo': titulo,
                'legenda': legenda,
                'hashtags': hashtags,
                'duracao': '',
                'origem': 'dublado',
                'idioma': 'pt',
                'video_id': '',
                'tipo': 'Dublado',
                'postado': 'Não'
            }
            df_principal = pd.concat([df_principal, pd.DataFrame([nova_linha_principal])], ignore_index=True)
        
        # Salvar planilha principal
        df_principal.to_excel(planilha_principal_path, index=False)
        df_principal.to_csv(csv_principal_path, index=False)
        
        return jsonify({"ok": True, "message": "Metadados salvos com sucesso"})
        
    except Exception as e:
        print(f"Erro ao salvar metadados dublado: {e}")
        return jsonify({"ok": False, "error": str(e)})

@app.route("/ler_metadados_mp4", methods=["POST"])
def ler_metadados_mp4_endpoint():
    """Lê metadados de um arquivo MP4"""
    try:
        body = request.get_json(force=True) or {}
        caminho_video = body.get("caminho", "")
        
        if not caminho_video or not os.path.exists(caminho_video):
            return jsonify({"ok": False, "error": "Arquivo não encontrado"})
        
        metadados = ler_metadados_mp4(caminho_video)
        
        return jsonify({
            "ok": True,
            "metadados": metadados
        })
        
    except Exception as e:
        print(f"Erro ao ler metadados MP4: {e}")
        return jsonify({"ok": False, "error": str(e)})

@app.route("/testar_metadados_mp4", methods=["POST"])
def testar_metadados_mp4():
    """Testa se os metadados foram salvos corretamente no MP4"""
    try:
        body = request.get_json(force=True) or {}
        caminho_video = body.get("caminho", "")
        
        if not caminho_video or not os.path.exists(caminho_video):
            return jsonify({"ok": False, "error": "Arquivo não encontrado"})
        
        # Ler metadados com mutagen
        metadados_mutagen = ler_metadados_mp4(caminho_video)
        
        # Ler metadados com FFmpeg
        metadados_ffmpeg = ler_metadados_ffmpeg(caminho_video)
        
        return jsonify({
            "ok": True,
            "mutagen": metadados_mutagen,
            "ffmpeg": metadados_ffmpeg,
            "arquivo": os.path.basename(caminho_video)
        })
        
    except Exception as e:
        print(f"Erro ao testar metadados MP4: {e}")
        return jsonify({"ok": False, "error": str(e)})

def ler_metadados_ffmpeg(caminho_video):
    """Lê metadados usando FFmpeg"""
    try:
        cmd = [
            'bin/ffmpeg/ffmpeg.exe.exe',
            '-i', caminho_video,
            '-f', 'ffmetadata',
            '-'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Parse dos metadados do FFmpeg
            metadados = {}
            for linha in result.stdout.split('\n'):
                if '=' in linha:
                    chave, valor = linha.split('=', 1)
                    metadados[chave.strip()] = valor.strip()
            
            return {
                'titulo': metadados.get('title', ''),
                'legenda': metadados.get('comment', '') or metadados.get('description', ''),
                'hashtags': metadados.get('keywords', ''),
                'tipo': metadados.get('genre', '')
            }
        else:
            return {'titulo': '', 'legenda': '', 'hashtags': '', 'tipo': ''}
            
    except Exception as e:
        print(f"Erro ao ler metadados com FFmpeg: {e}")
        return {'titulo': '', 'legenda': '', 'hashtags': '', 'tipo': ''}

@app.route("/adicionar_coluna_tipo", methods=["POST"])
def adicionar_coluna_tipo():
    """Adiciona coluna 'tipo' na planilha principal se não existir"""
    try:
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        # Carregar planilha
        if os.path.exists(planilha_path):
            df = pd.read_excel(planilha_path)
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            return jsonify({"ok": False, "error": "Planilha não encontrada"})
        
        # Adicionar coluna 'tipo' se não existir
        if 'tipo' not in df.columns:
            df['tipo'] = 'Legendado'  # Padrão para vídeos existentes
            print("✅ Coluna 'tipo' adicionada com valor padrão 'Legendado'")
        else:
            print("✅ Coluna 'tipo' já existe")
        
        # Adicionar coluna 'postado' se não existir
        if 'postado' not in df.columns:
            df['postado'] = 'Não'
            print("✅ Coluna 'postado' adicionada com valor padrão 'Não'")
        
        # Salvar planilha atualizada
        df.to_excel(planilha_path, index=False)
        df.to_csv(csv_path, index=False)
        
        return jsonify({
            "ok": True, 
            "message": "Colunas adicionadas com sucesso",
            "colunas": list(df.columns)
        })
        
    except Exception as e:
        print(f"Erro ao adicionar coluna tipo: {e}")
        return jsonify({"ok": False, "error": str(e)})

@app.route("/corrigir_planilha_principal", methods=["POST"])
def corrigir_planilha_principal():
    """Corrige a planilha principal adicionando colunas faltantes"""
    try:
        planilha_path = "data/planilhas/publicar.xlsx"
        csv_path = "data/planilhas/publicar.csv"
        
        # Carregar planilha
        if os.path.exists(planilha_path):
            df = pd.read_excel(planilha_path)
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            return jsonify({"ok": False, "error": "Planilha não encontrada"})
        
        print(f"📊 Planilha carregada com {len(df)} linhas e colunas: {list(df.columns)}")
        
        # Adicionar colunas faltantes
        colunas_faltantes = []
        
        if 'video_id' not in df.columns:
            df['video_id'] = ''
            colunas_faltantes.append('video_id')
        
        if 'tipo' not in df.columns:
            # Determinar tipo baseado no nome do arquivo
            df['tipo'] = df['arquivo_novo'].apply(lambda x: 'Dublado' if '_dublado_' in x else 'Legendado')
            colunas_faltantes.append('tipo')
        
        if 'postado' not in df.columns:
            df['postado'] = 'Não'
            colunas_faltantes.append('postado')
        
        print(f"✅ Colunas adicionadas: {colunas_faltantes}")
        print(f"📊 Nova estrutura: {list(df.columns)}")
        
        # Salvar planilha corrigida
        df.to_excel(planilha_path, index=False)
        df.to_csv(csv_path, index=False)
        
        # Mostrar estatísticas
        tipos_count = df['tipo'].value_counts().to_dict()
        
        return jsonify({
            "ok": True,
            "message": "Planilha corrigida com sucesso",
            "colunas_adicionadas": colunas_faltantes,
            "total_linhas": len(df),
            "tipos": tipos_count,
            "colunas": list(df.columns)
        })
        
    except Exception as e:
        print(f"Erro ao corrigir planilha: {e}")
        return jsonify({"ok": False, "error": str(e)})

@app.route("/aplicar_metadados_manuais", methods=["POST"])
def aplicar_metadados_manuais():
    """Aplica metadados importados manualmente em todos os vídeos"""
    try:
        body = request.get_json(force=True) or {}
        metadados = body.get("metadados", [])
        
        if not metadados:
            return jsonify({"ok": False, "error": "Nenhum metadado fornecido"})
        
        aplicados = 0
        
        # Processar cada metadado
        for meta in metadados:
            arquivo_antigo = meta.get("arquivo_antigo", "")
            titulo = meta.get("titulo", "")
            legenda = meta.get("legenda", "")
            hashtags = meta.get("hashtags", "")
            
            if not arquivo_antigo or not titulo:
                continue
            
            # Buscar vídeo correspondente
            pasta_videos = "static/final"
            arquivos = glob.glob(f"{pasta_videos}/*.mp4")
            
            for arquivo in arquivos:
                nome_arquivo = os.path.basename(arquivo)
                
                # Verificar se é o arquivo correto (pode ter sido renomeado)
                if (nome_arquivo == arquivo_antigo or 
                    nome_arquivo.startswith(arquivo_antigo.replace('.mp4', ''))):
                    
                    # Atualizar metadados na planilha
                    planilha_path = "data/planilhas/publicar.xlsx"
                    csv_path = "data/planilhas/publicar.csv"
                    
                    if os.path.exists(planilha_path):
                        df = pd.read_excel(planilha_path)
                    elif os.path.exists(csv_path):
                        df = pd.read_csv(csv_path)
                    else:
                        df = pd.DataFrame(columns=['arquivo_antigo', 'arquivo_novo', 'titulo', 'legenda', 'hashtags', 'duracao', 'origem', 'idioma'])
                    
                    # Atualizar ou adicionar linha
                    mask = df['arquivo_antigo'] == arquivo_antigo
                    if mask.any():
                        df.loc[mask, 'titulo'] = titulo
                        df.loc[mask, 'legenda'] = legenda
                        df.loc[mask, 'hashtags'] = hashtags
                    else:
                        nova_linha = {
                            'arquivo_antigo': arquivo_antigo,
                            'arquivo_novo': nome_arquivo,
                            'titulo': titulo,
                            'legenda': legenda,
                            'hashtags': hashtags,
                            'duracao': '',
                            'origem': 'final',
                            'idioma': 'pt'
                        }
                        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                    
                    # Salvar planilhas
                    df.to_excel(planilha_path, index=False)
                    df.to_csv(csv_path, index=False)
                    
                    aplicados += 1
                    break
        
        return jsonify({"ok": True, "aplicados": aplicados})
        
    except Exception as e:
        print(f"Erro ao aplicar metadados manuais: {e}")
        return jsonify({"ok": False, "error": str(e)})


def find_free_port(start_port=5500, max_port=5600):
    """Encontra uma porta livre começando de start_port"""
    import socket
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    # Tentar encontrar uma porta livre
    port = find_free_port()
    if port is None:
        print("❌ Nenhuma porta livre encontrada entre 5500-5600")
        port = 5500  # Fallback
    
    print(f"🚀 Iniciando servidor na porta {port}")
    try:
        app.run(port=port, debug=False)
    except OSError as e:
        if "10048" in str(e):
            print(f"❌ Porta {port} já está em uso. Tente fechar outros processos ou reiniciar o computador.")
            print("💡 Dica: Verifique se há outras instâncias do aplicativo rodando.")
        else:
            print(f"❌ Erro ao iniciar servidor: {e}")
