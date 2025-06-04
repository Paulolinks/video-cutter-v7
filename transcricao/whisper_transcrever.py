from faster_whisper import WhisperModel
import os

def transcrever_audio(audio_path):
    model = WhisperModel("base", compute_type="int8")
    generator, _ = model.transcribe(audio_path)
    segments = list(generator)

    texto = " ".join([seg.text.strip() for seg in segments])
    with open("data/transcricoes/transcricao.txt", "w", encoding="utf-8") as f:
        f.write(texto)
    return texto, segments


