
import os
import uuid
from moviepy.editor import VideoFileClip

def cortar_com_base_nas_frases(video_path, partes, modo_video="crop", qualidade_video="alta"):
    import json
    import glob
    import re
    
    os.makedirs("data/cortes", exist_ok=True)
    print("🔍 Testando leitura do vídeo original...")
    clip_test = VideoFileClip(video_path)
    print(f"🕒 Duração do vídeo: {clip_test.duration:.2f} segundos")
    clip_test.close()

    # Obter próximo número sequencial
    def obter_proximo_numero():
        padrao = "data/cortes/corte_*.mp4"
        arquivos_existentes = glob.glob(padrao)
        numeros = []
        for arquivo in arquivos_existentes:
            nome = os.path.basename(arquivo)
            match = re.search(r'corte_(\d+)\.mp4', nome)
            if match:
                numeros.append(int(match.group(1)))
        return max(numeros) + 1 if numeros else 1

    proximo_numero = obter_proximo_numero()
    print(f"🔢 Próximo número de corte: {proximo_numero}")

    for i, parte in enumerate(partes):
        try:
            inicio = float(parte["start"])
            fim = float(parte["end"])
            texto = parte["text"]

            print(f"✂️ Corte {proximo_numero + i}: {inicio:.2f}s até {fim:.2f}s")
            
            #Tamanho do corte do video 
            clip = VideoFileClip(video_path, fps_source="fps").subclip(inicio, fim)
            
            print(f"📏 Dimensões originais: {clip.size[0]}x{clip.size[1]} pixels")
            
            if modo_video == "crop":
                print("📐 Modo: Crop centralizado (sem bordas pretas)")
            else:
                print("📐 Modo: Letterbox (com bordas pretas)")

            filename = f"corte_{proximo_numero + i}.mp4"
            out_path = os.path.abspath(os.path.join("data/cortes", filename))
           
            # Configurações de qualidade baseadas na seleção
            if qualidade_video == "alta":
                crf = "15"  # Qualidade muito alta
                preset = "slow"  # Melhor qualidade
            elif qualidade_video == "media":
                crf = "18"  # Qualidade alta
                preset = "medium"
            else:  # rapida
                crf = "23"  # Qualidade média
                preset = "fast"
            
            # Configurar FFmpeg baseado no modo
            if modo_video == "letterbox":
                # Para letterbox: redimensionar mantendo proporção e adicionar padding preto
                ffmpeg_params = [
                    "-preset", preset,
                    "-crf", crf,
                    "-pix_fmt", "yuv420p",
                    "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:black",
                    "-profile:v", "high",
                    "-level", "4.1",
                    "-movflags", "+faststart"
                ]
            else:
                # Para crop: redimensionar altura para 1280 e cortar largura para 720 no centro
                ffmpeg_params = [
                    "-preset", preset,
                    "-crf", crf,
                    "-pix_fmt", "yuv420p",
                    "-vf", "scale=-1:1280,crop=720:1280:(iw-720)/2:0",
                    "-profile:v", "high",
                    "-level", "4.1",
                    "-movflags", "+faststart"
                ]
            
            print(f"🎬 Qualidade: {qualidade_video} (CRF {crf}, preset {preset})")
            
            clip.write_videofile(
                out_path,
                codec="libx264",
                audio_codec="aac",
                remove_temp=True,
                ffmpeg_params=ffmpeg_params,
                threads=2,
                write_logfile=False,
                logger=None
            )


            clip.close()
            print(f"✅ Corte salvo em: {out_path}")
            
            # Salvar transcrição específica do corte
            salvar_transcricao_corte(filename, texto, inicio, fim)
            
        except Exception as e:
            print(f"❌ Erro ao salvar corte {i+1}: {e}")

def salvar_transcricao_corte(nome_arquivo, texto, inicio, fim):
    """Salva a transcrição específica de cada corte"""
    try:
        # Criar pasta de transcrições dos cortes
        os.makedirs("data/transcricoes_cortes", exist_ok=True)
        
        # Nome do arquivo de transcrição (mesmo nome do vídeo, mas .txt)
        nome_base = os.path.splitext(nome_arquivo)[0]
        transcricao_path = os.path.join("data/transcricoes_cortes", f"{nome_base}.txt")
        
        # Criar conteúdo da transcrição com metadados
        conteudo = f"""TRANSCRIÇÃO DO CORTE: {nome_arquivo}
INÍCIO: {inicio:.2f}s
FIM: {fim:.2f}s
DURAÇÃO: {fim - inicio:.2f}s

TEXTO:
{texto}

TEXTO_TRADUZIDO:
[Tradução será adicionada automaticamente]
"""
        
        # Salvar arquivo
        with open(transcricao_path, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print(f"📝 Transcrição salva: {transcricao_path}")
        
    except Exception as e:
        print(f"❌ Erro ao salvar transcrição do corte {nome_arquivo}: {e}")

def atualizar_texto_traduzido(nome_arquivo, texto_traduzido):
    """Atualiza o campo TEXTO_TRADUZIDO em um arquivo de transcrição existente"""
    try:
        nome_base = os.path.splitext(nome_arquivo)[0]
        transcricao_path = os.path.join("data/transcricoes_cortes", f"{nome_base}.txt")
        
        if not os.path.exists(transcricao_path):
            print(f"⚠️ Arquivo de transcrição não encontrado: {transcricao_path}")
            return False
        
        # Ler arquivo existente
        with open(transcricao_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Atualizar campo TEXTO_TRADUZIDO
        if "TEXTO_TRADUZIDO:" in conteudo:
            # Substituir conteúdo existente
            import re
            pattern = r"TEXTO_TRADUZIDO:\s*\n.*?(?=\n\n|\Z)"
            novo_campo = f"TEXTO_TRADUZIDO:\n{texto_traduzido}\n"
            conteudo_atualizado = re.sub(pattern, novo_campo, conteudo, flags=re.DOTALL)
        else:
            # Adicionar campo se não existir
            conteudo_atualizado = conteudo + f"\n\nTEXTO_TRADUZIDO:\n{texto_traduzido}\n"
        
        # Salvar arquivo atualizado
        with open(transcricao_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_atualizado)
        
        print(f"✅ Texto traduzido atualizado: {transcricao_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar texto traduzido: {e}")
        return False

def buscar_texto_traduzido(nome_arquivo):
    """Busca o texto traduzido de um arquivo de transcrição"""
    try:
        nome_base = os.path.splitext(nome_arquivo)[0]
        transcricao_path = os.path.join("data/transcricoes_cortes", f"{nome_base}.txt")
        
        if not os.path.exists(transcricao_path):
            return None
        
        with open(transcricao_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Extrair texto traduzido
        if "TEXTO_TRADUZIDO:" in conteudo:
            import re
            pattern = r"TEXTO_TRADUZIDO:\s*\n(.*?)(?=\n\n|\Z)"
            match = re.search(pattern, conteudo, flags=re.DOTALL)
            if match:
                texto_traduzido = match.group(1).strip()
                if texto_traduzido and texto_traduzido != "[Tradução será adicionada automaticamente]":
                    return texto_traduzido
        
        return None
        
    except Exception as e:
        print(f"❌ Erro ao buscar texto traduzido: {e}")
        return None

def renomear_transcricao_individual(nome_antigo, nome_novo):
    """Renomeia arquivo de transcrição individual quando vídeo é renomeado"""
    try:
        # Extrair nomes base
        nome_base_antigo = os.path.splitext(nome_antigo)[0]
        nome_base_novo = os.path.splitext(nome_novo)[0]
        
        # Remover sufixos comuns
        nome_limpo_antigo = nome_base_antigo.replace('_legendado', '').replace('_dublado', '')
        nome_limpo_novo = nome_base_novo.replace('_legendado', '').replace('_dublado', '')
        
        print(f"🔄 Renomeando transcrição: {nome_antigo} -> {nome_novo}")
        print(f"📁 Nome limpo antigo: {nome_limpo_antigo}")
        print(f"📁 Nome limpo novo: {nome_limpo_novo}")
        
        # Mapear nome antigo para arquivo de transcrição correto
        mapeamento_cortes = {
            'corte_1': 'corte_1.txt',
            'corte_2': 'corte_2.txt', 
            'corte_3': 'corte_3.txt',
            'corte_4': 'corte_4.txt',
            'corte_5': 'corte_5.txt',
            'corte_6': 'corte_6.txt'
        }
        
        # Encontrar arquivo de transcrição correspondente
        arquivo_transcricao_antigo = None
        for corte, arquivo in mapeamento_cortes.items():
            if corte in nome_limpo_antigo:
                arquivo_transcricao_antigo = arquivo
                break
        
        if not arquivo_transcricao_antigo:
            print(f"⚠️ Não foi possível mapear {nome_limpo_antigo} para arquivo de transcrição")
            return False
        
        # Caminhos dos arquivos
        transcricao_antiga = f"data/transcricoes_cortes/{arquivo_transcricao_antigo}"
        transcricao_nova = f"data/transcricoes_cortes/{nome_limpo_novo}.txt"
        
        print(f"🔍 Procurando: {transcricao_antiga}")
        print(f"📝 Renomeando para: {transcricao_nova}")
        
        # Verificar se arquivo antigo existe
        if os.path.exists(transcricao_antiga):
            # Renomear arquivo
            os.rename(transcricao_antiga, transcricao_nova)
            print(f"✅ Transcrição renomeada: {transcricao_nova}")
            
            # Atualizar conteúdo do arquivo com novo nome
            with open(transcricao_nova, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Atualizar nome do arquivo no conteúdo
            conteudo_atualizado = conteudo.replace(f"TRANSCRIÇÃO DO CORTE: {nome_antigo}", f"TRANSCRIÇÃO DO CORTE: {nome_novo}")
            
            with open(transcricao_nova, 'w', encoding='utf-8') as f:
                f.write(conteudo_atualizado)
            
            print(f"✅ Conteúdo da transcrição atualizado")
            return True
        else:
            print(f"⚠️ Arquivo de transcrição não encontrado: {transcricao_antiga}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao renomear transcrição: {e}")
        return False

def adicionar_campo_traduzido_existentes():
    """Adiciona campo TEXTO_TRADUZIDO em arquivos de transcrição existentes"""
    try:
        pasta_transcricoes = "data/transcricoes_cortes"
        if not os.path.exists(pasta_transcricoes):
            print(f"⚠️ Pasta não encontrada: {pasta_transcricoes}")
            return
        
        arquivos = [f for f in os.listdir(pasta_transcricoes) if f.endswith('.txt')]
        print(f"🔍 Encontrados {len(arquivos)} arquivos de transcrição")
        
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(pasta_transcricoes, arquivo)
            
            # Ler arquivo
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Verificar se já tem campo TEXTO_TRADUZIDO
            if "TEXTO_TRADUZIDO:" not in conteudo:
                # Adicionar campo
                conteudo_atualizado = conteudo + "\n\nTEXTO_TRADUZIDO:\n[Tradução será adicionada automaticamente]\n"
                
                # Salvar arquivo atualizado
                with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                    f.write(conteudo_atualizado)
                
                print(f"✅ Campo TEXTO_TRADUZIDO adicionado: {arquivo}")
            else:
                print(f"⏭️ Campo já existe: {arquivo}")
        
        print(f"✅ Processamento concluído: {len(arquivos)} arquivos verificados")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar campo traduzido: {e}")

def renomear_todas_transcricoes():
    """Renomeia todas as transcrições para corresponder aos vídeos renomeados"""
    try:
        # Mapeamento dos vídeos renomeados para arquivos de transcrição
        mapeamento_videos = {
            'desenvolvimento-pessoal-apos-o-covid-19': 'corte_1.txt',
            'comece-onde-voce-esta': 'corte_2.txt',
            'voce-realmente-tem-controle': 'corte_3.txt', 
            'habilidade-de-identificar-padroes-e-crucial': 'corte_4.txt',
            'a-importancia-de-acordar-cedo': 'corte_5.txt',
            'por-que-voce-esta-na-escuridao': 'corte_6.txt',
            'como-manter-a-motivacao-diariamente': 'corte_7.txt',
            'progresso-e-a-chave-para-a-felicidade': 'corte_8.txt',
            'ser-excepcional-e-estar-sozinho': 'corte_9.txt',
            'ser-um-homem-na-vida-adulta': 'corte_10.txt',
            'voce-realmente-acredita': 'corte_11.txt',
            'batman-e-a-memoria-do-heroi': 'corte_12.txt'
        }
        
        pasta_transcricoes = "data/transcricoes_cortes"
        if not os.path.exists(pasta_transcricoes):
            print(f"⚠️ Pasta não encontrada: {pasta_transcricoes}")
            return
        
        print(f"🔄 Iniciando renomeação de todas as transcrições...")
        
        for nome_video, arquivo_antigo in mapeamento_videos.items():
            arquivo_antigo_path = os.path.join(pasta_transcricoes, arquivo_antigo)
            arquivo_novo_path = os.path.join(pasta_transcricoes, f"{nome_video}.txt")
            
            if os.path.exists(arquivo_antigo_path):
                # Renomear arquivo
                os.rename(arquivo_antigo_path, arquivo_novo_path)
                print(f"✅ Renomeado: {arquivo_antigo} -> {nome_video}.txt")
                
                # Atualizar conteúdo
                with open(arquivo_novo_path, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                
                # Atualizar nome do arquivo no conteúdo
                conteudo_atualizado = conteudo.replace(f"TRANSCRIÇÃO DO CORTE: {arquivo_antigo.replace('.txt', '.mp4')}", f"TRANSCRIÇÃO DO CORTE: {nome_video}.mp4")
                
                with open(arquivo_novo_path, 'w', encoding='utf-8') as f:
                    f.write(conteudo_atualizado)
                
                print(f"✅ Conteúdo atualizado: {nome_video}.txt")
            else:
                print(f"⚠️ Arquivo não encontrado: {arquivo_antigo}")
        
        print(f"✅ Renomeação concluída!")
        
    except Exception as e:
        print(f"❌ Erro ao renomear transcrições: {e}")




 #Tamanho do corte do video
# usa todos núcleos   threads=1, ou  threads=os.cpu_count(), 