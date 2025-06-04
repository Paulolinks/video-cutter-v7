
import os
import uuid
from moviepy.editor import VideoFileClip

def cortar_com_base_nas_frases(video_path, partes):
    os.makedirs("data/cortes", exist_ok=True)
    print("🔍 Testando leitura do vídeo original...")
    clip_test = VideoFileClip(video_path)
    print(f"🕒 Duração do vídeo: {clip_test.duration:.2f} segundos")
    clip_test.close()

    for i, parte in enumerate(partes):
        try:
            inicio = float(parte["start"])
            fim = float(parte["end"])
            texto = parte["text"]

            print(f"✂️ Corte {i+1}: {inicio:.2f}s até {fim:.2f}s")
        #Tamanho do corte do video 
            clip = VideoFileClip(video_path, fps_source="fps").subclip(inicio, fim)
            clip = clip.resize(height=1280)
            clip = clip.crop(x_center=int(clip.w / 2), width=720)

            print(f"📏 Dimensões do corte: {clip.size[0]}x{clip.size[1]} pixels")

            filename = f"corte_{i+1}.mp4"
            out_path = os.path.abspath(os.path.join("data/cortes", filename))
           
             # Executar teste de velocidade de renderização
             #codec="libx264",
            clip.write_videofile(
                out_path,
                codec="libx264",
                audio_codec="aac",
                remove_temp=True,
                ffmpeg_params=["-preset", "ultrafast"],
                threads=os.cpu_count(),      # usa todos núcleos   threads=1,
                write_logfile=False,
                logger=None
        )


            clip.close()
            print(f"✅ Corte salvo em: {out_path}")
        except Exception as e:
            print(f"❌ Erro ao salvar corte {i+1}: {e}")
