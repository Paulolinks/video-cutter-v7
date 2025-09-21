#!/usr/bin/env python3
"""
Correções avançadas para qualidade da voz
"""

def fix_advanced_voice_quality():
    """Aplica correções avançadas no dub_xtts.py"""
    
    # Ler o arquivo atual
    with open('dub_xtts.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # CORREÇÃO 4: Adicionar função para normalizar áudio de referência
    old_imports = '''import json, os, subprocess, shutil
from pathlib import Path'''
    
    new_imports = '''import json, os, subprocess, shutil
from pathlib import Path
import numpy as np'''
    
    content = content.replace(old_imports, new_imports)
    
    # CORREÇÃO 5: Adicionar função para preparar voz de referência
    old_configs = '''# ========= Configs globais =========
SR = 24000  # sample rate único do pipeline (mono, s16)
LANG_DEFAULT = "pt"  # idioma padrão para o XTTS (ajuste conforme seu projeto)'''
    
    new_configs = '''# ========= Configs globais =========
SR = 24000  # sample rate único do pipeline (mono, s16)
LANG_DEFAULT = "pt"  # idioma padrão para o XTTS (ajuste conforme seu projeto)

def _prepare_voice_reference(voice_ref_wav: Path) -> Path:
    """Prepara a voz de referência para melhor clonagem"""
    if not voice_ref_wav.exists():
        raise FileNotFoundError(f"Voz de referência não encontrada: {voice_ref_wav}")
    
    # Criar versão otimizada da voz de referência
    optimized_ref = voice_ref_wav.parent / f"{voice_ref_wav.stem}_optimized.wav"
    
    # Normalizar e otimizar a voz de referência
    cmd = [
        "ffmpeg", "-y", "-i", str(voice_ref_wav),
        "-af", "highpass=f=80,lowpass=f=8000,volume=0.8",  # Filtros para melhor clonagem
        "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16",
        str(optimized_ref)
    ]
    
    try:
        from dub_xtts import _ffmpeg
        _ffmpeg(cmd)
        print(f"✅ Voz de referência otimizada: {optimized_ref}")
        return optimized_ref
    except:
        print("⚠️ Usando voz de referência original")
        return voice_ref_wav'''
    
    content = content.replace(old_configs, new_configs)
    
    # CORREÇÃO 6: Usar voz otimizada na síntese
    old_synth_call = '''        xtts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker_wav=str(voice_ref_wav),
            language=language,
            # Parâmetros adicionais para melhor qualidade
            split_sentences=False,  # Não quebrar sentenças para manter naturalidade
            use_speaker_embedding=True  # Usar embedding do speaker para melhor clonagem
        )'''
    
    new_synth_call = '''        # Preparar voz de referência otimizada
        optimized_voice = _prepare_voice_reference(voice_ref_wav)
        
        xtts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker_wav=str(optimized_voice),
            language=language,
            # Parâmetros adicionais para melhor qualidade
            split_sentences=False,  # Não quebrar sentenças para manter naturalidade
            use_speaker_embedding=True  # Usar embedding do speaker para melhor clonagem
        )'''
    
    content = content.replace(old_synth_call, new_synth_call)
    
    # CORREÇÃO 7: Adicionar pós-processamento para melhorar qualidade
    old_normalize = '''        # Normaliza (PCM s16, mono, SR)
        tmp = out_wav.with_suffix(".tmp.wav")
        _ensure_wav_pcm(out_wav, tmp, sr=SR)
        out_wav.unlink(missing_ok=True)
        tmp.rename(out_wav)
        
        print(f"✅ Áudio normalizado: {out_wav}")
        return out_wav'''
    
    new_normalize = '''        # Normaliza e aplica pós-processamento para melhor qualidade
        tmp = out_wav.with_suffix(".tmp.wav")
        _ensure_wav_pcm(out_wav, tmp, sr=SR)
        
        # Aplicar pós-processamento para melhorar qualidade da voz
        final_tmp = out_wav.with_suffix(".final.wav")
        cmd = [
            "ffmpeg", "-y", "-i", str(tmp),
            "-af", "highpass=f=100,lowpass=f=7000,volume=1.1,compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-30/-20|0/-20:.2:0:-90:.1",  # Compressão suave
            "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16",
            str(final_tmp)
        ]
        
        try:
            _ffmpeg(cmd)
            out_wav.unlink(missing_ok=True)
            final_tmp.rename(out_wav)
            print(f"✅ Áudio processado e normalizado: {out_wav}")
        except:
            # Fallback para normalização simples
            out_wav.unlink(missing_ok=True)
            tmp.rename(out_wav)
            print(f"✅ Áudio normalizado: {out_wav}")
        
        return out_wav'''
    
    content = content.replace(old_normalize, new_normalize)
    
    # Salvar arquivo corrigido
    with open('dub_xtts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Correções avançadas aplicadas:")
    print("   - Preparação otimizada da voz de referência")
    print("   - Filtros de áudio para melhor clonagem")
    print("   - Pós-processamento com compressão suave")
    print("   - Fallback para normalização simples")

if __name__ == "__main__":
    fix_advanced_voice_quality()
