import os
from moviepy.editor import VideoFileClip

def extrair_audio(video_path):
    os.makedirs("data/audio", exist_ok=True)
    audio_path = os.path.join("data/audio", "audio.wav")

    print("🎬 Carregando vídeo...")
    clip = VideoFileClip(video_path)

    # Verifica se o vídeo tem áudio
    if not clip.audio:
        print("❌ ERRO: O vídeo não possui faixa de áudio.")
        raise ValueError("Vídeo sem faixa de áudio. Tente outro link.")

    print("🎧 Extraindo áudio com MoviePy...")
    clip.audio.write_audiofile(audio_path)

    # Fecha recursos corretamente
    print("🔃 Fechando recursos MoviePy...")
    clip.reader.close()
    clip.audio.reader.close_proc()
    clip.close()

    print("✅ Recursos fechados.")
    print("✅ Áudio extraído com sucesso:", audio_path)
    return audio_path
