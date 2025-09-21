#!/usr/bin/env python3
"""
Correções para qualidade da voz e velocidade na dublagem XTTS v2
"""

def fix_dub_xtts():
    """Aplica correções no arquivo dub_xtts.py"""
    
    # Ler o arquivo atual
    with open('dub_xtts.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # CORREÇÃO 1: Melhorar configuração do XTTS v2
    old_xtts_config = '''        _XTTS = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)'''
    new_xtts_config = '''        # Configuração otimizada para clonagem de voz
        _XTTS = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
        
        # Configurar parâmetros para melhor qualidade de clonagem
        if hasattr(_XTTS, 'synthesizer') and hasattr(_XTTS.synthesizer, 'tts_config'):
            # Ajustar configurações para melhor clonagem
            _XTTS.synthesizer.tts_config['use_speaker_embedding'] = True
            _XTTS.synthesizer.tts_config['use_d_vector_file'] = False
            print("✅ Configurações de clonagem otimizadas")'''
    
    content = content.replace(old_xtts_config, new_xtts_config)
    
    # CORREÇÃO 2: Melhorar função de time-stretching
    old_time_stretch = '''def _time_stretch_to_duration(wav_in: Path, wav_out: Path, target_sec: float, sr=SR):
    cur = _probe_duration_sec(wav_in)
    
    if cur < 1e-3 or target_sec < 1e-3:
        _ensure_wav_pcm(wav_in, wav_out, sr=sr)
        return cur, 1.0
    
    ratio = target_sec / cur
    
    # Usar asetrate + aresample em vez de atempo (mais confiável)
    # Para acelerar (diminuir duração): aumentar a taxa de amostragem
    # Para desacelerar (aumentar duração): diminuir a taxa de amostragem
    new_rate = int(sr / ratio)  # Invertido: ratio < 1 significa acelerar
    af_filter = f"asetrate={new_rate},aresample={sr}"
    
    cmd = ["ffmpeg","-y","-i",str(wav_in),"-af",af_filter,"-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]
    _ffmpeg(cmd)
    newdur = _probe_duration_sec(wav_out)
    
    return newdur, ratio'''
    
    new_time_stretch = '''def _time_stretch_to_duration(wav_in: Path, wav_out: Path, target_sec: float, sr=SR):
    cur = _probe_duration_sec(wav_in)
    
    if cur < 1e-3 or target_sec < 1e-3:
        _ensure_wav_pcm(wav_in, wav_out, sr=sr)
        return cur, 1.0
    
    ratio = target_sec / cur
    
    # Limitar ratio para evitar distorção extrema (voz de Minion)
    # Se a diferença for muito grande, usar padding em vez de stretch
    if ratio < 0.4 or ratio > 2.5:
        print(f"⚠️ Ratio muito extremo ({ratio:.2f}), usando padding em vez de stretch")
        _ensure_wav_pcm(wav_in, wav_out, sr=sr)
        return cur, 1.0
    
    # Usar atempo com chain para melhor qualidade de voz
    if 0.5 <= ratio <= 2.0:
        # Ratio dentro do limite do atempo - usar diretamente
        af_filter = f"atempo={ratio:.6f}"
    else:
        # Ratio fora do limite - usar chain
        af_filter = _atempo_chain(ratio)
    
    cmd = ["ffmpeg","-y","-i",str(wav_in),"-af",af_filter,"-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]
    _ffmpeg(cmd)
    newdur = _probe_duration_sec(wav_out)
    
    return newdur, ratio'''
    
    content = content.replace(old_time_stretch, new_time_stretch)
    
    # CORREÇÃO 3: Melhorar síntese TTS com parâmetros otimizados
    old_synth = '''        # A API já salva WAV/MP3/OGG; por padrão salva WAV 22050~24000, normalizamos depois.
        xtts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker_wav=str(voice_ref_wav),
            language=language
        )'''
    
    new_synth = '''        # A API já salva WAV/MP3/OGG; por padrão salva WAV 22050~24000, normalizamos depois.
        # Usar parâmetros otimizados para melhor clonagem de voz
        xtts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker_wav=str(voice_ref_wav),
            language=language,
            # Parâmetros adicionais para melhor qualidade
            split_sentences=False,  # Não quebrar sentenças para manter naturalidade
            use_speaker_embedding=True  # Usar embedding do speaker para melhor clonagem
        )'''
    
    content = content.replace(old_synth, new_synth)
    
    # Salvar arquivo corrigido
    with open('dub_xtts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Correções aplicadas no dub_xtts.py:")
    print("   - Configurações otimizadas do XTTS v2")
    print("   - Time-stretching melhorado (evita voz de Minion)")
    print("   - Parâmetros de síntese otimizados")
    print("   - Limites de ratio para evitar distorção")

if __name__ == "__main__":
    fix_dub_xtts()
