import os
from moviepy.editor import VideoFileClip

def extrair_audio(video_path):
    os.makedirs("data/audio", exist_ok=True)
    audio_path = os.path.join("data/audio", "audio.wav")

    print("🎬 Carregando vídeo...")
    clip = VideoFileClip(video_path)

    print("🎧 Extraindo áudio com MoviePy...")
    clip.audio.write_audiofile(audio_path)

    # Fecha os processos internos corretamente
    import sys

    print("🔃 Fechando recursos MoviePy...")
    clip.reader.close()
    if clip.audio:
        clip.audio.reader.close_proc()
    clip.close()
    print("✅ Recursos fechados.")
    sys.stdout.flush()


    print("✅ Áudio extraído com sucesso:", audio_path)
    return audio_path
