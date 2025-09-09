from faster_whisper import WhisperModel
from langdetect import detect
import os

# ✅ Carrega o modelo uma única vez ao iniciar
print("🎯 Carregando modelo Whisper...")
model = WhisperModel("base.en", device="cpu", compute_type="int8")
print("✅ Modelo carregado com sucesso!")

def transcrever_audio(audio_path):
    try:
        print(f"🎧 Transcrevendo áudio: {audio_path}")
        generator, _ = model.transcribe(audio_path)

        segments = []
        for seg in generator:
            print(f"📝 {seg.start:.2f}s → {seg.end:.2f}s: {seg.text.strip()}")
            segments.append(seg)

        texto = " ".join([seg.text.strip() for seg in segments])

        os.makedirs("data/transcricoes", exist_ok=True)
        with open("data/transcricoes/transcricao.txt", "w", encoding="utf-8") as f:
            f.write(texto)

        print("📄 Transcrição salva em data/transcricoes/transcricao.txt")
        return texto, segments

    except Exception as e:
        print(f"❌ Erro ao transcrever áudio: {e}")
        return "", []

def detectar_idioma(texto):
    try:
        idioma = detect(texto)
        print(f"🌐 Idioma detectado: {idioma}")
        return idioma
    except Exception as e:
        print(f"⚠️ Erro ao detectar idioma: {e}")
        return "und"
