
def clonar_voz_real(texto, arquivo_voz_referencia, arquivo_saida):
    """Clona voz real usando Tortoise TTS"""
    try:
        from tortoise.api import TextToSpeech
        from tortoise.utils.audio import load_audio, load_voice
        
        print(f"🎤 Iniciando clonagem real da voz...")
        print(f"📝 Texto: {texto[:50]}...")
        print(f"🎵 Voz de referência: {arquivo_voz_referencia}")
        
        # Carregar modelo Tortoise TTS
        tts = TextToSpeech()
        
        # Carregar voz de referência
        voice_samples, conditioning_latents = load_voice(arquivo_voz_referencia)
        
        # Gerar áudio clonado
        gen = tts.tts_with_preset(
            texto,
            voice_samples=voice_samples,
            conditioning_latents=conditioning_latents,
            preset="fast"  # ou "high_quality" para melhor qualidade
        )
        
        # Salvar áudio
        import torchaudio
        torchaudio.save(arquivo_saida, gen.squeeze(0).cpu(), 24000)
        
        print(f"✅ Voz clonada com sucesso: {arquivo_saida}")
        return arquivo_saida
        
    except Exception as e:
        print(f"❌ Erro na clonagem real: {e}")
        return None
