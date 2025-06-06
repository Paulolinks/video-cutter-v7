import sys
# main.py (trecho completo com cópia no final da função main)
import psutil
import os
import io
import json
import shutil
import time
# Corrige problema de codificação ao imprimir no terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define o caminho do ImageMagick (necessário para renderizar texto com moviepy)
os.environ["IMAGEMAGICK_BINARY"] = r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"

# Imports das funções de cada etapa do processo
from baixar.baixar_video import baixar_video
from audio.extrair_audio import extrair_audio
from transcricao.whisper_transcrever import transcrever_audio
from frases.spacy_filtrar_frases import extrair_frases_de_efeito
from utils.mapear_frases import mapear_frases
from cortes.cortar_video import cortar_com_base_nas_frases
from langdetect import detect
from deep_translator import GoogleTranslator
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# Carrega configurações visuais (fonte, cor, tamanho da fonte, altura/largura do vídeo)
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

fonte = config.get("fonte")
cor = config.get("cor")
tamanho = config.get("tamanho")
altura = config.get("altura")
largura = config.get("largura")
posicao = float(config.get("posicao", 0.2))  # valor de 0.2 até 0.8
tempo_min = config.get("tempo_min", 15.0)
tempo_max = config.get("tempo_max", 53.0)



# Adiciona legendas no vídeo com base nos segmentos (tempo + texto)
def legendar_video_por_segmentos(video_path, segmentos, saida_path):
    clip = VideoFileClip(video_path)
    legendas = []
    for seg in segmentos:
        inicio = max(0, float(seg["start"]))
        fim = max(inicio + 0.5, float(seg["end"]))
        texto = traduzir(seg["text"])
        legenda = TextClip(
            texto,
            fontsize=tamanho,
            font=fonte,
            color=cor,
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(clip.w * 0.9, None)
        ).set_position(("center", int(clip.h * posicao))) \
         .set_start(inicio) \
         .set_end(fim)
        legendas.append(legenda)
    final = CompositeVideoClip([clip, *legendas])
    
    # Executar teste de velocidade de renderização
    
    final.write_videofile(
        saida_path,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2       # usa todos núcleos threads=2  threads=os.cpu_count()
    )
        
    #Carregar videos cortados
    os.makedirs("static/final", exist_ok=True)

    #Carregar videos cortados
    shutil.copy(saida_path, os.path.join("static/final", os.path.basename(saida_path)))

# Testar Velocidade de Renderização
def medir_etapa(nome):
    print(f"\n⏳ Iniciando: {nome}")
    return time.time(), nome

def fim_etapa(inicio, nome):
    duracao = time.time() - inicio
    print(f"⏱️ {nome}: {duracao:.1f}s")
    return duracao

# Aplica legenda nos cortes com base nos segmentos dentro de cada parte
def legendar_cortes_por_segmento(partes):
    os.makedirs("data/final", exist_ok=True)
    for i, parte in enumerate(partes):
        entrada = f"data/cortes/corte_{i+1}.mp4"
        saida = f"data/final/corte_{i+1}_legendado.mp4"
        segmentos = []
        for seg in parte["segmentos"]:
            seg_ini = seg.start
            seg_fim = seg.end
            if seg_ini >= parte["start"] and seg_fim <= parte["end"]:
                segmentos.append({
                    "start": seg_ini - parte["start"],
                    "end": seg_fim - parte["start"],
                    "text": seg.text
                })
        legendar_video_por_segmentos(entrada, segmentos, saida)

# Salva mensagens de log
def log(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("utf-8", "replace").decode())
    with open("status.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Traduz texto para português (caso esteja em outro idioma)
def traduzir(texto):
    try:
        return GoogleTranslator(source="auto", target="pt").translate(texto)
    except:
        return texto

# Função principal do sistema
def main():
    inicio = time.time()  # ⏱️ Início

    # Captura o link do YouTube via argumento ou input
    if len(sys.argv) > 1:
        link = sys.argv[1]
    else:
        link = input("Cole o link do vídeo: ")

    # Salva status inicial
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 1, "descricao": "Iniciando..."}, f, ensure_ascii=False)

      # Etapa 1: baixar vídeo
    t, n = medir_etapa("Etapa 1 – Baixar vídeo")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 10, "descricao": "Baixando vídeo..."}, f, ensure_ascii=False)
    video_path = baixar_video(link)
    fim_etapa(t, n)

     # Etapa 2: extrair áudio
    t, n = medir_etapa("Etapa 2 – Extrair áudio")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 20, "descricao": "Extraindo áudio..."}, f, ensure_ascii=False)
    #audio_path = extrair_audio(video_path)
    #fim_etapa(t, n)
############### DEBUGANDO ####################
    # Verifica se o áudio foi extraído corretamente
    audio_path = extrair_audio(video_path)
    print("🎯 Audio salvo em:", audio_path)
    sys.stdout.flush()

    print("🧠 Subprocessos ativos:")
    for p in psutil.Process().children(recursive=True):
        print(f" - PID: {p.pid}, name: {p.name()}")
################ DEBUGANDO #####################33



      # Etapa 3: transcrever áudio
    t, n = medir_etapa("Etapa 3 – Transcrição (Whisper)")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 30, "descricao": "Transcrevendo áudio..."}, f, ensure_ascii=False)
    #texto, segmentos = transcrever_audio(audio_path)

################################################
    print("🎙️ Iniciando transcrição com Whisper...")
    sys.stdout.flush()

    texto, segmentos = transcrever_audio(audio_path)

    print("✅ Transcrição concluída")
    sys.stdout.flush()
  
##########################################
    idioma = detect(texto)
    fim_etapa(t, n)

    # Etapa 4: extrair frases de impacto
    t, n = medir_etapa("Etapa 4 – Frases de efeito")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 40, "descricao": "Filtrando frases de efeito..."}, f, ensure_ascii=False)
    frases = extrair_frases_de_efeito(texto, idioma, segmentos)
    fim_etapa(t, n)

        # Etapa 5: (removida) – já mapeado na etapa 4
    partes = frases
    for parte in partes:
        parte["segmentos"] = segmentos


     # Etapa 6: traduzir frases, se idioma for inglês
    t, n = medir_etapa("Etapa 6 – Traduzir frases")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 60, "descricao": "Traduzindo frases..."}, f, ensure_ascii=False)
    for parte in partes:
        parte["traducao"] = traduzir(parte["text"]) if idioma == "en" else parte["text"]
    fim_etapa(t, n)

    # Etapa 7: cortar vídeo com base nas frases
    t, n = medir_etapa("Etapa 7 – Cortar vídeo")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 70, "descricao": "Cortando vídeo..."}, f, ensure_ascii=False)
    cortar_com_base_nas_frases(video_path, partes)
    fim_etapa(t, n)

    # Etapa 8: adicionar legendas aos cortes
    t, n = medir_etapa("Etapa 8 – Adicionar legendas")
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 90, "descricao": "Adicionando legendas..."}, f, ensure_ascii=False)
    legendar_cortes_por_segmento(partes)
    fim_etapa(t, n)

    # Etapa 9: copiar vídeos para pasta pública
    t, n = medir_etapa("Etapa 9 – Copiar para pasta pública")
    os.makedirs("static/final", exist_ok=True)
    for arq in os.listdir("data/final"):
        if arq.endswith(".mp4"):
            shutil.copy(f"data/final/{arq}", f"static/final/{arq}")
    fim_etapa(t, n)

    # Etapa final: salvar status concluído
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump({"etapa": 100, "descricao": "Finalizado com sucesso!"}, f, ensure_ascii=False)

    fim = time.time()
    print(f"\n✅ Tempo total de execução: {fim - inicio:.2f} segundos")    

if __name__ == "__main__":
    main()
