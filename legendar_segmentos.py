# nao esta utilizando mais



import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from deep_translator import GoogleTranslator

def traduzir(texto):
    try:
        return GoogleTranslator(source="auto", target="pt").translate(texto)
    except:
        return texto

def legendar_segmentos(video_path, segmentos, saida_path):
    clip = VideoFileClip(video_path)
    legendas = []

    for seg in segmentos:
        inicio = float(seg["start"])
        fim = float(seg["end"])
        texto = traduzir(seg["text"])
# Posicao da legenda
        legenda = TextClip(
            texto,
            fontsize=50,
            font="Arial-Bold",
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(clip.w * 0.9, None)
        ).set_position(("center", int(clip.h * 0.4)))          .set_start(inicio)          .set_end(fim)

        legendas.append(legenda)
    #ultimo teste
    final = CompositeVideoClip([clip, *legendas])
    final.write_videofile(
        saida_path,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2,
        threads=os.cpu_count()      # usa todos núcleos
    )

# Exemplo de uso
if __name__ == "__main__":
    from transcricao.whisper_transcrever import transcrever_audio

    caminho_video = "data/videos/video.mp4"
    caminho_audio = "data/audio/audio.wav"
    caminho_saida = "data/final/legendado_segmentos.mp4"

    texto, segmentos = transcrever_audio(caminho_audio)
    legendar_segmentos(caminho_video, segmentos, caminho_saida)
