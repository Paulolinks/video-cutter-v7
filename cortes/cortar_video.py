
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
        except Exception as e:
            print(f"❌ Erro ao salvar corte {i+1}: {e}")






 #Tamanho do corte do video
# usa todos núcleos   threads=1, ou  threads=os.cpu_count(), 