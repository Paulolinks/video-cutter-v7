def dublar_video_avancado(video_entrada, video_saida, texto_traduzido, voice, lang_target):
    """
    Dublagem avançada com funcionalidades do TTS:
    - Controle de emoção
    - Velocidade dinâmica
    - Batch processing
    - Sincronização perfeita
    - Clonagem de voz natural
    """
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, AudioClip
        import tempfile
        import subprocess
        
        # Importar funcionalidades avançadas
        from tts_avancado import (
            analisar_emocao_audio_original,
            calcular_fator_emocao,
            gerar_audio_tts_com_emocao
        )
        
        print(" Iniciando dublagem avançada com TTS...")
        
        # 1. CARREGAR VÍDEO E ÁUDIO ORIGINAL
        video = VideoFileClip(video_entrada)
        audio_original = video.audio
        
        print(f" Vídeo carregado: {video.duration:.2f}s")
        print(f" Áudio original: {audio_original.duration:.2f}s")
        
        # 2. EXTRAIR TIMESTAMPS PRECISOS
        timestamps = extrair_timestamps_whisper_preciso(video_entrada)
        if not timestamps:
            print(" Não foi possível extrair timestamps, usando dublagem simples")
            return dublar_video_simples(video_entrada, video_saida, texto_traduzido, voice, lang_target)
        
        print(f" {len(timestamps)} timestamps extraídos")
        
        # 3. ANÁLISE AVANÇADA DE EMOÇÃO E DENSIDADE
        print(" Analisando emoção do áudio original...")
        emocoes_por_segmento = analisar_emocao_audio_original(video_entrada, timestamps)
        
        print(" Analisando densidade de palavras...")
        densidades = analisar_densidade_palavras_por_segmento(video_entrada, timestamps)
        
        if not densidades:
            print(" Erro na análise de densidade, usando dublagem simples")
            return dublar_video_simples(video_entrada, video_saida, texto_traduzido, voice, lang_target)
        
        print(f" Densidades analisadas: {len(densidades)} segmentos")
        print(f" Emoções detectadas: {len(emocoes_por_segmento)} segmentos")
        
        # 4. DIVIDIR TEXTO EM SEGMENTOS
        palavras = texto_traduzido.split()
        total_palavras = len(palavras)
        segmentos_texto = []
        
        palavra_atual = 0
        for i, densidade in enumerate(densidades):
            proporcao = densidade['duracao'] / sum(d['duracao'] for d in densidades)
            palavras_segmento = max(1, int(total_palavras * proporcao))
            palavras_segmento = min(palavras_segmento, total_palavras - palavra_atual)
            
            segmento = ' '.join(palavras[palavra_atual:palavra_atual + palavras_segmento])
            segmentos_texto.append(segmento)
            palavra_atual += palavras_segmento
        
        print(f" Texto dividido em {len(segmentos_texto)} segmentos")
        
        # 5. BATCH PROCESSING - Gerar todos os áudios com emoção
        print(" Iniciando batch processing com controle de emoção...")
        audio_segmentos_finais = []
        
        for i, (ts, densidade, texto_segmento, emocao) in enumerate(zip(timestamps, densidades, segmentos_texto, emocoes_por_segmento)):
            print(f" Processando segmento {i+1}/{len(timestamps)}: {ts['start']:.2f}s - {ts['end']:.2f}s")
            print(f" Emoção: {emocao['tipo']} (intensidade: {emocao['intensidade']:.2f})")
            
            # Gerar áudio TTS com controle de emoção
            audio_temporario = gerar_audio_tts_com_emocao(texto_segmento, voice, lang_target, emocao)
            if not audio_temporario:
                print(f" Erro ao gerar áudio para segmento {i+1}")
                continue
            
            audio_tts_clip = AudioFileClip(audio_temporario)
            duracao_original_segmento = ts['duration']
            duracao_tts_segmento = audio_tts_clip.duration
            
            # SINCRONIZAÇÃO AVANÇADA
            fator_sincronizacao = duracao_original_segmento / duracao_tts_segmento if duracao_tts_segmento > 0 else 1.0
            
            # Aplicar velocidade baseada na densidade E emoção
            fator_densidade = densidade['fator_velocidade']
            fator_emocao = calcular_fator_emocao(emocao)
            fator_velocidade_final = fator_sincronizacao * fator_densidade * fator_emocao
            
            # Limitar velocidade para evitar áudio muito lento/rápido
            fator_velocidade_final = max(0.8, min(2.0, fator_velocidade_final))
            
            print(f" Fator velocidade final: {fator_velocidade_final:.2f}x (sincronização: {fator_sincronizacao:.2f}x, densidade: {fator_densidade:.2f}x, emoção: {fator_emocao:.2f}x)")
            
            # Aplicar velocidade se necessário
            if abs(fator_velocidade_final - 1.0) > 0.05:
                print(f" Aplicando velocidade: {fator_velocidade_final:.2f}x")
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_audio = temp_file.name
                audio_tts_clip.write_audiofile(temp_audio, verbose=False, logger=None)
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    audio_ajustado = temp_file.name
                
                cmd = [
                    config.FFMPEG_EXECUTABLE,
                    "-i", temp_audio,
                    "-filter:a", f"atempo={fator_velocidade_final:.2f}",
                    "-y", audio_ajustado
                ]
                
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    audio_segmento_final = AudioFileClip(audio_ajustado)
                    os.remove(temp_audio)
                    print(f" Velocidade aplicada: {audio_segmento_final.duration:.2f}s")
                except subprocess.CalledProcessError as e:
                    print(f" Erro FFmpeg, usando áudio original: {e}")
                    audio_segmento_final = audio_tts_clip
                except Exception as e:
                    print(f" Erro geral, usando áudio original: {e}")
                    audio_segmento_final = audio_tts_clip
            else:
                audio_segmento_final = audio_tts_clip
            
            # ADICIONAR À LISTA DE SEGMENTOS
            audio_segmentos_finais.append(audio_segmento_final)
            
            # Limpar arquivo temporário
            try:
                remover_arquivo_seguro(audio_temporario)
            except:
                pass
        
        # 6. CONCATENAR SEGMENTOS EM SEQUÊNCIA
        if audio_segmentos_finais:
            print(f" Concatenando {len(audio_segmentos_finais)} segmentos...")
            audio_final = concatenate_audioclips(audio_segmentos_finais)
            
            # 7. AJUSTAR DURAÇÃO FINAL
            if audio_final.duration > video.duration:
                audio_final = audio_final.subclip(0, video.duration)
                print(" Áudio cortado para duração do vídeo")
            elif audio_final.duration < video.duration:
                silencio = AudioClip(lambda t: 0, duration=video.duration - audio_final.duration)
                audio_final = concatenate_audioclips([audio_final, silencio])
                print(" Áudio estendido com silêncio")
            
            print(f" Áudio final: {audio_final.duration:.2f}s")
        else:
            print(" Nenhum segmento de áudio gerado")
            return False
        
        # 8. SUBSTITUIR ÁUDIO NO VÍDEO
        video_dublado = video.set_audio(audio_final)
        
        # 9. SALVAR VÍDEO
        video_dublado.write_videofile(
            video_saida,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2,
            verbose=False,
            logger=None
        )
        
        print(f" Vídeo dublado avançado salvo: {video_saida}")
        
        # Limpar recursos
        video.close()
        audio_original.close()
        for seg in audio_segmentos_finais:
            seg.close()
        audio_final.close()
        video_dublado.close()
        
        return True
        
    except Exception as e:
        print(f" Erro na dublagem avançada: {e}")
        import traceback
        traceback.print_exc()
        return False
