# main.py (usa seleção por coerência + tema opcional)
import sys
import psutil
import os
import io
import json
import shutil
import time

# Corrige problema de codificação ao imprimir no terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Caminhos de binários (ajuste se necessário)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["IMAGEMAGICK_BINARY"] = os.path.join(APP_DIR, "bin", "imagemagick", "magick.exe")
os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.join(APP_DIR, "bin", "ffmpeg", "ffmpeg.exe")

# === IMPORTS DO PIPELINE ===
# Ajuste para os seus módulos reais (mantive nomes genéricos)
from baixar.baixar_video import baixar_video
from audio.extrair_audio import extrair_audio
from transcricao.whisper_transcrever import transcrever_audio
from frases.selecionar_trechos import selecionar_trechos_significativos
from cortes.cortar_video import cortar_com_base_nas_frases

from langdetect import detect
from deep_translator import GoogleTranslator
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# Configurar ImageMagick e FFmpeg locais (como no V7)
import os
os.environ['IMAGEMAGICK_BINARY'] = os.path.abspath("bin/imagemagick/magick.exe")
os.environ['IMAGEIO_FFMPEG_EXE'] = os.path.abspath("bin/ffmpeg/ffmpeg.exe.exe")

# Carrega configurações visuais e lógicas
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

fonte = config.get("fonte")
cor = config.get("cor")
tamanho = config.get("tamanho")
altura = config.get("altura")
largura = config.get("largura")
posicao = float(config.get("posicao", 0.2))
tempo_min = config.get("tempo_min", 10.0)
tempo_max = config.get("tempo_max", 60.0)

# NOVO: modo, tema e rede social
automatico = bool(config.get("automatico", True))
tema_cfg = (config.get("tema") or "").strip()
rede_social = config.get("rede_social", "instagram")
modo_video = config.get("modo_video", "crop")
qualidade_video = config.get("qualidade_video", "alta")

# DEBUG: Mostrar configurações carregadas
print(f"🔧 Configurações carregadas:")
print(f"   Fonte: {fonte}")
print(f"   Cor: {cor}")
print(f"   Tamanho: {tamanho}")
print(f"   Posição: {posicao}")
print(f"   Altura: {altura}")
print(f"   Largura: {largura}")

def quebrar_em_linhas(texto, max_palavras=8):
    palavras = texto.split()
    linhas = []
    # CORREÇÃO: Remover limite de 16 palavras para não cortar legendas
    for i in range(0, len(palavras), max_palavras):
        linhas.append(" ".join(palavras[i:i+max_palavras]))
    return "\n".join(linhas)

# Sistema de fontes simplificado como no V7
def obter_fonte_para_moviepy(fonte_config):
    """Obtém o nome da fonte para o MoviePy (como no V7)"""
    if not fonte_config:
        return "Arial"
    
    # Se é um caminho, extrair apenas o nome
    if os.path.exists(fonte_config):
        nome_arquivo = os.path.basename(fonte_config)
        nome_sem_ext = os.path.splitext(nome_arquivo)[0]
        return nome_sem_ext
    
    # Se já é um nome, usar diretamente
    return fonte_config

def legendar_video_por_segmentos(video_path, segmentos, saida_path):
    clip = VideoFileClip(video_path)
    legendas = []
    
    print(f" Aplicando fonte: {fonte}")
    print(f"🎨 Cor: {cor}")
    print(f"🎨 Tamanho: {tamanho}")
    
    # Obter nome da fonte para MoviePy (como no V7)
    fonte_final = obter_fonte_para_moviepy(fonte)
    
    print(f" Usando fonte final: {fonte_final}")
    
    for seg in segmentos:
        inicio = max(0, float(seg["start"]))
        fim_original = float(seg["end"])
        duracao = fim_original - inicio
        fim = inicio + max(duracao, 0.8)
        texto = quebrar_em_linhas(traduzir(seg["text"]))
        
        # Criar legenda como no V7 (usando nome da fonte)
        try:
            print(f"🎬 Criando legenda com fonte: {fonte_final}")
            
            legenda = TextClip(
                texto,
                fontsize=tamanho,
                font=fonte_final,  # V7 usa nome da fonte diretamente
                color=cor,
                stroke_color="black",
                stroke_width=2,  # V7 usa stroke_width=2
                method="caption",
                size=(clip.w * 0.9, None)
            ).set_position(("center", int(clip.h * posicao))).set_start(inicio).set_end(fim)
            
            print(f"✅ Legenda criada com sucesso usando: {fonte_final}")
            
        except Exception as font_error:
            print(f"⚠️ Erro com fonte {fonte_final}: {font_error}")
            print(" Usando Arial como fallback...")
            
            legenda = TextClip(
                texto,
                fontsize=tamanho,
                font='Arial',  # V7 usa Arial como fallback
                color=cor,
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(clip.w * 0.9, None)
            ).set_position(("center", int(clip.h * posicao))).set_start(inicio).set_end(fim)
        
        legendas.append(legenda)

    # CORREÇÃO: Verificar e limpar arquivo de saída antes de escrever
    if os.path.exists(saida_path):
        try:
            os.remove(saida_path)
            print(f"️ Arquivo existente removido: {saida_path}")
        except Exception as e:
            print(f"⚠️ Não foi possível remover arquivo existente: {e}")
    
    # CORREÇÃO: Garantir que o diretório existe
    os.makedirs(os.path.dirname(saida_path), exist_ok=True)
    
    # CORREÇÃO: Usar caminho absoluto e verificar permissões
    saida_absoluta = os.path.abspath(saida_path)
    print(f"💾 Salvando em: {saida_absoluta}")
    
    try:
        final = CompositeVideoClip([clip, *legendas])
        final.write_videofile(
            saida_absoluta,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2,
            verbose=False,
            logger=None
        )
        
        # Verificar se o arquivo foi criado
        if os.path.exists(saida_absoluta):
            print(f"✅ Arquivo salvo com sucesso: {saida_absoluta}")
            
            # Copiar para static/final
            os.makedirs("static/final", exist_ok=True)
            shutil.copy(saida_absoluta, os.path.join("static/final", os.path.basename(saida_absoluta)))
            print(f"✅ Arquivo copiado para static/final")
        else:
            print(f"❌ Arquivo não foi criado: {saida_absoluta}")
            
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        print(f" Tentando com nome alternativo...")
        
        # Tentar com nome alternativo
        nome_alt = f"corte_alt_{int(time.time())}.mp4"
        saida_alt = os.path.join(os.path.dirname(saida_path), nome_alt)
        
        try:
            final = CompositeVideoClip([clip, *legendas])
            final.write_videofile(
                saida_alt,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                threads=2,
                verbose=False,
                logger=None
            )
            print(f"✅ Arquivo salvo com nome alternativo: {saida_alt}")
        except Exception as e2:
            print(f"❌ Erro mesmo com nome alternativo: {e2}")
            raise e2

def medir_etapa(nome):
    print(f"\n⏳ Iniciando: {nome}")
    return time.time(), nome

def fim_etapa(inicio, nome):
    duracao = time.time() - inicio
    print(f"⏱️ {nome}: {duracao:.1f}s")
    return duracao

def legendar_cortes_por_segmento(partes, segmentos_whisper=None):
    import os
    import glob
    import re
    
    os.makedirs("data/final", exist_ok=True)
    
    # Obter os números dos cortes que foram criados
    def obter_numeros_cortes_criados():
        padrao = "data/cortes/corte_*.mp4"
        arquivos_existentes = glob.glob(padrao)
        numeros = []
        for arquivo in arquivos_existentes:
            nome = os.path.basename(arquivo)
            match = re.search(r'corte_(\d+)\.mp4', nome)
            if match:
                numeros.append(int(match.group(1)))
        return sorted(numeros)
    
    numeros_cortes = obter_numeros_cortes_criados()
    print(f"🔢 Cortes encontrados: {numeros_cortes}")
    
    if not numeros_cortes:
        print("❌ Nenhum corte encontrado para legendagem!")
        return
    
    for i, parte in enumerate(partes):
        if i >= len(numeros_cortes):
            print(f"⚠️ Não há corte correspondente para parte {i+1}")
            continue
            
        numero_corte = numeros_cortes[i]
        entrada = f"data/cortes/corte_{numero_corte}.mp4"
        
        # Obter próximo número sequencial para vídeos finais
        def obter_proximo_numero_final():
            padrao = "data/final/corte_*_legendado.mp4"
            arquivos_existentes = glob.glob(padrao)
            numeros = []
            for arquivo in arquivos_existentes:
                nome = os.path.basename(arquivo)
                match = re.search(r'corte_(\d+)_legendado\.mp4', nome)
                if match:
                    numeros.append(int(match.group(1)))
            return max(numeros) + 1 if numeros else 1
        
        proximo_final = obter_proximo_numero_final()
        saida = f"data/final/corte_{proximo_final}_legendado.mp4"
        segmentos = []
        parte_inicio = parte["start"]
        parte_fim = parte["end"]

        # CORREÇÃO: Usar dados salvos para criar legendas corretas
        if segmentos_whisper:
            print(f"📖 [LEGENDA] Usando dados salvos do Whisper para corte_{numero_corte}")
            
            # Carregar dados salvos da transcrição
            transcricao_path = f"data/transcricoes_cortes/corte_{numero_corte}.txt"
            if os.path.exists(transcricao_path):
                with open(transcricao_path, 'r', encoding='utf-8') as f:
                    conteudo_transcricao = f.read()
                
                # Extrair segmentos de legenda salvos
                pattern = r"SEGMENTOS_LEGENDA:\s*\n(\[.*?\])"
                match = re.search(pattern, conteudo_transcricao, flags=re.DOTALL)
                if match:
                    try:
                        segmentos_salvos = json.loads(match.group(1))
                        print(f"✅ [LEGENDA] Carregados {len(segmentos_salvos)} segmentos salvos")
                        
                        # Usar segmentos salvos para criar legendas
                        segmentos = []
                        for seg in segmentos_salvos:
                            segmentos.append({
                                "start": seg["inicio"],
                                "end": seg["fim"],
                                "text": seg["texto_traduzido"] if seg["texto_traduzido"] else seg["texto_original"]
                            })
                        
                        print(f"✅ [LEGENDA] Legendas criadas com dados corretos do Whisper")
                    except Exception as e:
                        print(f"⚠️ [LEGENDA] Erro ao carregar segmentos salvos: {e}")
                        print(f"🔄 [LEGENDA] Usando fallback com segmentos originais")
                else:
                    print(f"⚠️ [LEGENDA] Segmentos salvos não encontrados - usando fallback")
            else:
                print(f"⚠️ [LEGENDA] Arquivo de transcrição não encontrado - usando fallback")
        
        # Fallback: usar lógica original se não conseguir carregar dados salvos
        if not segmentos:
            print(f"🔄 [LEGENDA] Usando fallback - criando segmentos originais")
            for seg in parte["segmentos"]:
                seg_ini = seg["start"] if isinstance(seg, dict) else seg.start
                seg_fim = seg["end"] if isinstance(seg, dict) else seg.end
                if seg_fim > parte_inicio and seg_ini < parte_fim:
                    inicio_legenda = max(0, seg_ini - parte_inicio)
                    fim_legenda = max(inicio_legenda + 0.5, seg_fim - parte_inicio)
                    segmentos.append({
                        "start": round(inicio_legenda, 2),
                        "end": round(fim_legenda, 2),
                        "text": seg["text"] if isinstance(seg, dict) else seg.text
                    })
        
        # NOVA FUNCIONALIDADE: Salvar dados completos na transcrição
        if segmentos_whisper:
            print(f"💾 [DADOS COMPLETOS] Salvando dados do Whisper para corte_{numero_corte}")
            from cortes.cortar_video import salvar_transcricao_corte
            
            # Filtrar segmentos do Whisper que estão dentro desta parte
            segmentos_parte = []
            for seg in segmentos_whisper:
                # Verificar se é objeto Segment ou dicionário
                if hasattr(seg, 'start'):
                    seg_ini = seg.start
                    seg_fim = seg.end
                    seg_texto = seg.text
                else:
                    seg_ini = seg.get("start", 0.0)
                    seg_fim = seg.get("end", 0.0)
                    seg_texto = seg.get("text", "")
                
                if seg_fim > parte_inicio and seg_ini < parte_fim:
                    # Ajustar timestamps para o corte
                    seg_ajustado = {
                        "start": max(0, seg_ini - parte_inicio),
                        "end": max(0, seg_fim - parte_inicio),
                        "text": seg_texto
                    }
                    segmentos_parte.append(seg_ajustado)
            
            # Salvar transcrição completa com dados do Whisper
            salvar_transcricao_corte(f"corte_{numero_corte}.mp4", parte.get("text", ""), parte_inicio, parte_fim, segmentos_parte)
        
        legendar_video_por_segmentos(entrada, segmentos, saida)

def log(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("utf-8", "replace").decode())
    with open("status.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def traduzir(texto):
    try:
        return GoogleTranslator(source="auto", target="pt").translate(texto)
    except:
        return texto



def verificar_fontes_disponiveis():
    """Verifica quais fontes estão disponíveis no sistema"""
    try:
        from moviepy.editor import TextClip
        import os
        
        # Listar fontes do Windows
        fontes_dir = "C:/Windows/Fonts/"
        if os.path.exists(fontes_dir):
            fontes = [f for f in os.listdir(fontes_dir) if f.lower().endswith(('.ttf', '.otf'))]
            print(" Fontes disponíveis no sistema:")
            for f in sorted(fontes)[:20]:  # Mostrar apenas as primeiras 20
                print(f"   - {f}")
            
            # Verificar especificamente Impact
            impact_files = [f for f in fontes if 'impact' in f.lower()]
            if impact_files:
                print(f"✅ Arquivos Impact encontrados: {impact_files}")
            else:
                print("❌ Nenhum arquivo Impact encontrado")
        
        # Testar algumas fontes comuns
        fontes_teste = ["Arial", "Arial-Bold", "Times", "Courier"]
        for f in fontes_teste:
            try:
                test = TextClip("Test", font=f, fontsize=20)
                test.close()
                print(f"✅ Fonte {f} funciona")
            except Exception as e:
                print(f"❌ Fonte {f} não funciona: {e}")
                
    except Exception as e:
        print(f"❌ Erro ao verificar fontes: {e}")

def limpar_arquivos_temporarios():
    """Limpa arquivos temporários que podem estar causando conflito"""
    try:
        import glob
        
        # Limpar arquivos temporários do MoviePy
        temp_files = glob.glob("data/final/*.mp4")
        for f in temp_files:
            try:
                os.remove(f)
                print(f"🗑️ Arquivo temporário removido: {f}")
            except:
                pass
                
        # Limpar arquivos de cache
        cache_files = glob.glob("data/final/*.tmp")
        for f in cache_files:
            try:
                os.remove(f)
                print(f"🗑️ Arquivo de cache removido: {f}")
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ Erro ao limpar arquivos temporários: {e}")

def listar_fontes_disponiveis():
    """Lista todas as fontes disponíveis na pasta legenda/fonts"""
    fonts_dir = "legenda/fonts"
    fontes = {}
    
    if os.path.exists(fonts_dir):
        for arquivo in os.listdir(fonts_dir):
            if arquivo.lower().endswith(('.ttf', '.otf')):
                nome_fonte = arquivo.replace('.ttf', '').replace('.otf', '')
                fontes[nome_fonte.lower()] = arquivo
                print(f"📝 Fonte disponível: {nome_fonte} -> {arquivo}")
    
    return fontes

def obter_proximo_numero_corte():
    """Obtém o próximo número sequencial para cortes"""
    import glob
    import re
    
    # Buscar todos os arquivos de corte existentes
    padrao = "data/cortes/corte_*.mp4"
    arquivos_existentes = glob.glob(padrao)
    
    numeros = []
    for arquivo in arquivos_existentes:
        nome = os.path.basename(arquivo)
        match = re.search(r'corte_(\d+)\.mp4', nome)
        if match:
            numeros.append(int(match.group(1)))
    
    # Retornar o próximo número
    if numeros:
        return max(numeros) + 1
    else:
        return 1

def obter_proximo_numero_final():
    """Obtém o próximo número sequencial para vídeos finais"""
    import glob
    import re
    
    # Buscar todos os arquivos finais existentes
    padrao = "data/final/corte_*_legendado.mp4"
    arquivos_existentes = glob.glob(padrao)
    
    numeros = []
    for arquivo in arquivos_existentes:
        nome = os.path.basename(arquivo)
        match = re.search(r'corte_(\d+)_legendado\.mp4', nome)
        if match:
            numeros.append(int(match.group(1)))
    
    # Retornar o próximo número
    if numeros:
        return max(numeros) + 1
    else:
        return 1

def limpar_videos_anteriores():
    """Limpa vídeos antigos de todas as pastas exceto final"""
    pastas_limpar = ["data/videos", "data/cortes", "data/audio", "data/transcricoes"]
    
    for pasta in pastas_limpar:
        if os.path.exists(pasta):
            print(f"🗑️ Limpando pasta: {pasta}")
            for arquivo in os.listdir(pasta):
                if arquivo.endswith(('.mp4', '.webm', '.wav', '.txt')):
                    try:
                        os.remove(os.path.join(pasta, arquivo))
                        print(f"   ✅ Removido: {arquivo}")
                    except Exception as e:
                        print(f"   ⚠️ Erro ao remover {arquivo}: {e}")

def main():
    inicio = time.time()
    
    # DEBUG: Verificar configurações carregadas
    print(f"🔧 CONFIGURAÇÕES CARREGADAS:")
    print(f"   Fonte do config: '{fonte}'")
    print(f"   Tipo da fonte: {type(fonte)}")
    print(f"   Fonte é None? {fonte is None}")
    print(f"   Fonte é string vazia? {fonte == ''}")
    
    if len(sys.argv) > 1:
        link = sys.argv[1]
    else:
        link = input("Cole o link do vídeo: ")

    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 1, "descricao": "Iniciando..."}, f, ensure_ascii=False)

    # Etapa 1 – Baixar vídeo
    t, n = medir_etapa("Etapa 1 – Baixar vídeo")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 10, "descricao": "Baixando vídeo..."}, f, ensure_ascii=False)
    video_path = baixar_video(link)
    fim_etapa(t, n)

    # Etapa 2 – Extrair áudio
    t, n = medir_etapa("Etapa 2 – Extrair áudio")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 20, "descricao": "Extraindo áudio..."}, f, ensure_ascii=False)
    audio_path = extrair_audio(video_path)
    print("🎯 Audio salvo em:", audio_path)
    print("🧠 Subprocessos ativos:")
    for p in psutil.Process().children(recursive=True):
        print(f" - PID: {p.pid}, name: {p.name()}")
    fim_etapa(t, n)

    # Etapa 3 – Transcrever (Whisper)
    t, n = medir_etapa("Etapa 3 – Transcrição (Whisper)")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 30, "descricao": "Transcrevendo áudio..."}, f, ensure_ascii=False)
    print("🎙️ Iniciando transcrição com Whisper...")
    texto, segmentos = transcrever_audio(audio_path)
    print("✅ Transcrição concluída")
    idioma = detect(texto or "pt")
    fim_etapa(t, n)

    # Etapa 4 – Selecionar trechos (Automático sem tema OU com tema)
    t, n = medir_etapa("Etapa 4 – Selecionar trechos significativos")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 40, "descricao": "Selecionando trechos..."}, f, ensure_ascii=False)

    tema_efetivo = None if automatico or not tema_cfg else tema_cfg
    partes = selecionar_trechos_significativos(
        texto_transcrito=texto,
        segments=segmentos,
        idioma=idioma,
        tempo_min=tempo_min,
        tempo_max=tempo_max,
        tema=tema_efetivo,
        max_resultados=6,
        usar_modelo_lg=False,
        rede_social=rede_social
    )

    # compat: anexar segmentos para legendar depois
    for parte in partes:
        parte["segmentos"] = segmentos
    fim_etapa(t, n)

    # Etapa 5 – Cortar vídeo
    t, n = medir_etapa("Etapa 5 – Cortar vídeo")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 70, "descricao": "Cortando vídeo..."}, f, ensure_ascii=False)

    print(f"🔍 Debug: Total de partes para cortar: {len(partes)}")
    for i, parte in enumerate(partes):
        print(f"🔍 Debug: Parte {i+1}: {parte['start']:.2f}s - {parte['end']:.2f}s")

    cortar_com_base_nas_frases(video_path, partes, modo_video, qualidade_video)

    # Verificar se os arquivos foram criados
    import os
    cortes_dir = "data/cortes"
    if os.path.exists(cortes_dir):
        arquivos = os.listdir(cortes_dir)
        print(f" Debug: Arquivos em {cortes_dir}: {arquivos}")
    else:
        print(f"❌ Debug: Diretório {cortes_dir} não existe!")

    fim_etapa(t, n)

    # Etapa 6 – Legendar cortes
    t, n = medir_etapa("Etapa 6 – Adicionar legendas")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 90, "descricao": "Adicionando legendas..."}, f, ensure_ascii=False)
    legendar_cortes_por_segmento(partes, segmentos)
    fim_etapa(t, n)

    # Etapa 7 – Copiar para pasta pública
    t, n = medir_etapa("Etapa 7 – Copiar para pasta pública")
    os.makedirs("static/final", exist_ok=True)
    for arq in os.listdir("data/final"):
        if arq.endswith(".mp4"):
            shutil.copy(f"data/final/{arq}", f"static/final/{arq}")
    fim_etapa(t, n)

    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 100, "descricao": "Finalizado com sucesso!"}, f, ensure_ascii=False)

    fim = time.time()
    print(f"\n✅ Tempo total de execução: {fim - inicio:.2f} segundos")

if __name__ == "__main__":
    main()
