def dublar_video(video_entrada, video_saida, texto_traduzido, voice, lang_target):
    """Implementa dublagem real do vídeo com texto traduzido"""
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
        import subprocess
        import tempfile
        import os
        import shutil
        
        print(f"Iniciando dublagem: {video_entrada} -> {video_saida}")
        print(f"Texto traduzido: {texto_traduzido[:100]}...")
        
        # Carregar vídeo
        video = VideoFileClip(video_entrada)
        print(f"Vídeo carregado. Duração: {video.duration}s")
        
        # Gerar áudio com TTS (Text-to-Speech)
        audio_temporario = gerar_audio_tts(texto_traduzido, voice, lang_target)
        
        if audio_temporario and os.path.exists(audio_temporario):
            print(f"Áudio TTS gerado: {audio_temporario}")
            
            # Carregar novo áudio
            novo_audio = AudioFileClip(audio_temporario)
            print(f"Áudio carregado. Duração: {novo_audio.duration}s")
            
            # Ajustar duração do áudio para o vídeo
            if novo_audio.duration > video.duration:
                novo_audio = novo_audio.subclip(0, video.duration)
                print("Áudio cortado para duração do vídeo")
            elif novo_audio.duration < video.duration:
                # Estender áudio se necessário
                from moviepy.audio.fx.audio_loop import audio_loop
                novo_audio = audio_loop(novo_audio, duration=video.duration)
                print("Áudio estendido para duração do vídeo")
            
            # Substituir áudio do vídeo
            video_final = video.set_audio(novo_audio)
            print("Áudio substituído no vídeo")
            
            # Salvar vídeo dublado
            print("Salvando vídeo dublado...")
            video_final.write_videofile(
                video_saida,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                verbose=False,
                logger=None
            )
            print(f"Vídeo dublado salvo: {video_saida}")
            
            # Limpar arquivos temporários
            video.close()
            novo_audio.close()
            video_final.close()
            if os.path.exists(audio_temporario):
                os.remove(audio_temporario)
        else:
            print("Erro ao gerar áudio TTS - copiando vídeo original")
            # Fallback: copiar vídeo original
            shutil.copy2(video_entrada, video_saida)
            video.close()
        
    except Exception as e:
        print(f"Erro na dublagem: {e}")
        # Fallback: copiar arquivo original
        try:
            import shutil
            shutil.copy2(video_entrada, video_saida)
        except:
            pass
