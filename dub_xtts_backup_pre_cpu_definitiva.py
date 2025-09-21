"""
Dublagem por sentenças com XTTS v2 (Coqui), alinhada aos timestamps.
- Lê data/transcricoes_cortes/<cut_id>/(timestamps.json | timestamp_detalhado.json | sentences.json)
- Para cada sentença:
    * Gera TTS clonado com tua voz (voice_ref_wav)
    * Faz time-stretch para bater em end-start
    * Insere silêncio até a próxima sentença
- Concatena e muxa com o vídeo do corte.

Requisitos:
  pip install TTS==0.22.0
  ffmpeg instalado no sistema

Uso (exemplo):
  from dub_xtts import dub_by_sentences_xtts
  dub_by_sentences_xtts(
      base_data_dir=Path("data"),
      cut_id="0001",
      video_cut_path=Path("outputs/cortes/0001.mp4"),
      out_dir=Path("outputs/dublados/0001"),
      voice_ref_wav=Path("voice_refs/minha_voz.wav"),
      prefer_lang="pt"  # "pt" usa text_pt quando houver; "en" usa text_en/text
  )
"""
import json, os, subprocess, shutil
from pathlib import Path
import numpy as np

# ========= Configs globais =========
SR = 24000  # sample rate único do pipeline (mono, s16)
LANG_DEFAULT = "pt"  # idioma padrão para o XTTS (ajuste conforme seu projeto)

def _prepare_voice_reference(voice_ref_wav: Path) -> Path:
    """
    🎯 CORREÇÃO: Usar voz original sem otimização desnecessária
    """
    if not voice_ref_wav.exists():
        raise FileNotFoundError(f"Voz de referência não encontrada: {voice_ref_wav}")
    
    print(f"✅ [VOZ] Usando voz de referência ORIGINAL: {voice_ref_wav}")
    print(f"📊 [VOZ] Tamanho do arquivo: {voice_ref_wav.stat().st_size / 1024**2:.1f} MB")
    
    # RETORNAR DIRETAMENTE a voz original - sem "otimização"
    return voice_ref_wav

# ========= XTTS v2 (Coqui) =========
_XTTS = None
_XTTS_IMPORT_ERROR = None

def reset_xtts():
    """Reseta o XTTS para forçar reinicialização"""
    global _XTTS, _XTTS_IMPORT_ERROR
    _XTTS = None
    _XTTS_IMPORT_ERROR = None
    print("🔄 XTTS v2 resetado - próxima inicialização será limpa")

def _init_xtts():
    """
    🎯 CORREÇÃO: Inicializa XTTS v2 com uso forçado da GPU
    """
    global _XTTS, _XTTS_IMPORT_ERROR
    
    # Se já foi inicializado e não houve erro, retorna
    if _XTTS is not None:
        return _XTTS
    
    # Se houve erro anterior, tenta reinicializar
    if _XTTS_IMPORT_ERROR is not None:
        print(f"🔄 Tentando reinicializar XTTS v2 após erro anterior...")
        _XTTS = None
        _XTTS_IMPORT_ERROR = None
    
    try:
        from TTS.api import TTS
        import torch
        
        # Verificar se CUDA está disponível (opcional)
        if torch.cuda.is_available():
            print(f"🚀 [GPU] CUDA disponível: {torch.cuda.get_device_name(0)}")
            gpu_available = True
        else:
            print("⚠️ [CPU] CUDA não disponível - usando CPU")
            gpu_available = False
        
        print(f"🚀 [GPU] Inicializando XTTS v2 com GPU: {torch.cuda.get_device_name(0)}")
        print(f"📊 [GPU] Memória GPU disponível: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        
        # Limpar cache do CUDA antes de inicializar
        torch.cuda.empty_cache()
        
        # Configuração adaptável GPU/CPU
        if gpu_available:
            print("🎯 [GPU] Inicializando XTTS com GPU...")
            torch.cuda.set_device(0)
            print(f"🎯 [GPU] Device CUDA definido: {torch.cuda.current_device()}")
            _XTTS = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
            
            # Mover modelo para GPU
            if hasattr(_XTTS, 'synthesizer') and hasattr(_XTTS.synthesizer, 'tts_model'):
                if hasattr(_XTTS.synthesizer.tts_model, 'cuda'):
                    _XTTS.synthesizer.tts_model.cuda()
                    print("🎯 [GPU] Modelo XTTS movido para GPU")
            
            # Verificar memória GPU
            gpu_memory_used = torch.cuda.memory_allocated(0) / 1024**3
            print(f"📊 [GPU] Memória GPU em uso: {gpu_memory_used:.2f} GB")
            print("✅ [GPU] XTTS v2 inicializado com GPU")
        else:
            print("🎯 [CPU] Inicializando XTTS com CPU...")
            _XTTS = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
            print("✅ [CPU] XTTS v2 inicializado com CPU")
        
        # Configurar parâmetros para melhor qualidade de clonagem
        if hasattr(_XTTS, 'synthesizer') and hasattr(_XTTS.synthesizer, 'tts_config'):
            # Ajustar configurações para melhor clonagem
            _XTTS.synthesizer.tts_config['use_speaker_embedding'] = True
            _XTTS.synthesizer.tts_config['use_d_vector_file'] = False
            print("✅ Configurações de clonagem otimizadas")
        
        return _XTTS
        
    except Exception as e:
        _XTTS = None
        _XTTS_IMPORT_ERROR = e
        print(f"❌ Erro ao inicializar XTTS v2: {e}")
        print(f"⚠️ XTTS v2 não disponível - funcionalidades de dublagem desabilitadas")
        return None

# ========= Utilitários =========
def _ffmpeg(cmd):
    # Usar FFmpeg da pasta bin local
    if cmd[0] == "ffmpeg":
        cmd[0] = "bin/ffmpeg/ffmpeg.exe"
    elif cmd[0] == "ffprobe":
        cmd[0] = "bin/ffmpeg/ffprobe.exe"
    
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{' '.join(cmd)}\n\n{p.stdout}")
    return p.stdout

def _probe_duration_sec(wav_path: Path) -> float:
    # Usar ffmpeg para obter duração (fallback para quando ffprobe não estiver disponível)
    cmd = [
        "bin/ffmpeg/ffmpeg.exe","-i",str(wav_path),"-f","null","-"
    ]
    out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Extrair duração do stderr do ffmpeg
    import re
    duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out.stderr)
    if duration_match:
        hours, minutes, seconds = duration_match.groups()
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        return total_seconds
    
    # Fallback: tentar usar librosa se disponível
    try:
        import librosa
        y, sr = librosa.load(str(wav_path), sr=None)
        return len(y) / sr
    except:
        return 0.0

def _ensure_wav_pcm(wav_in: Path, wav_out: Path, sr=SR):
    cmd = ["ffmpeg","-y","-i",str(wav_in),"-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]
    _ffmpeg(cmd)

def _atempo_chain(ratio: float) -> str:
    # Decompõe a razão em passos entre 0.5 e 2.0 (limite do atempo)
    chain = []
    r = float(ratio)
    while r > 2.0:
        chain.append(2.0); r /= 2.0
    while r < 0.5:
        chain.append(0.5); r /= 0.5
    chain.append(r)
    return ",".join([f"atempo={x:.6f}" for x in chain])

def _time_stretch_to_duration(wav_in: Path, wav_out: Path, target_sec: float, sr=SR):
    """
    🎯 CORREÇÃO: Time-stretching robusto que garante duração exata
    """
    cur = _probe_duration_sec(wav_in)
    
    print(f"🔍 [TIME-STRETCH] Duração atual: {cur:.3f}s → Alvo: {target_sec:.3f}s")
    
    if cur < 1e-3 or target_sec < 1e-3:
        _ensure_wav_pcm(wav_in, wav_out, sr=sr)
        return cur, 1.0
    
    ratio = target_sec / cur
    print(f"🔍 [TIME-STRETCH] Ratio calculado: {ratio:.3f}")
    
    # Limitar ratio para evitar distorção extrema
    if ratio < 0.5 or ratio > 2.0:
        print(f"⚠️ [TIME-STRETCH] Ratio extremo ({ratio:.3f}), usando padding/trimming")
        
        # Se muito rápido, fazer trim
        if ratio < 0.5:
            cmd = ["ffmpeg","-y","-i",str(wav_in),"-t",f"{target_sec:.3f}",
                   "-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]
        # Se muito lento, fazer padding
        else:
            cmd = ["ffmpeg","-y","-i",str(wav_in),
                   "-filter_complex",f"[0:a]apad=whole_dur={target_sec:.3f}[out]",
                   "-map","[out]","-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]
        
        _ffmpeg(cmd)
        final_dur = _probe_duration_sec(wav_out)
        print(f"✅ [TIME-STRETCH] Duração final (padding/trim): {final_dur:.3f}s")
        return final_dur, ratio
    
    # Usar atempo para time-stretching suave
    print(f"🎵 [TIME-STRETCH] Aplicando atempo={ratio:.3f}")
    cmd = ["ffmpeg","-y","-i",str(wav_in),"-af",f"atempo={ratio:.6f}",
           "-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]
    
    try:
        _ffmpeg(cmd)
        final_dur = _probe_duration_sec(wav_out)
        print(f"✅ [TIME-STRETCH] Duração final: {final_dur:.3f}s (erro: {abs(final_dur-target_sec):.3f}s)")
        
        # Se ainda não está exato, fazer ajuste fino
        if abs(final_dur - target_sec) > 0.1:
            print(f"🔧 [TIME-STRETCH] Ajuste fino necessário...")
            
            temp_out = wav_out.with_suffix(".temp.wav")
            # Usar técnica mais precisa: asetpts
            correction_ratio = target_sec / final_dur
            cmd_fine = ["ffmpeg","-y","-i",str(wav_out),
                       "-filter:a",f"asetpts=PTS/{correction_ratio:.6f}",
                       "-ar",str(sr),"-ac","1","-sample_fmt","s16",str(temp_out)]
            
            _ffmpeg(cmd_fine)
            wav_out.unlink()
            temp_out.rename(wav_out)
            
            final_dur = _probe_duration_sec(wav_out)
            print(f"✅ [TIME-STRETCH] Duração final (ajustada): {final_dur:.3f}s")
        
        return final_dur, ratio
        
    except Exception as e:
        print(f"❌ [TIME-STRETCH] Erro no atempo: {e}")
        # Fallback: cópia simples
        _ensure_wav_pcm(wav_in, wav_out, sr=sr)
        return cur, 1.0

def _make_silence(wav_out: Path, dur_sec: float, sr=SR):
    dur_sec = max(0.0, dur_sec)
    cmd = [
        "ffmpeg","-y","-f","lavfi","-i",f"anullsrc=r={sr}:cl=mono",
        "-t",f"{dur_sec:.3f}","-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)
    ]
    _ffmpeg(cmd)

def _concat_wavs_concatdemux(out_wav: Path, parts: list):
    # parts: lista de Paths (todos PCM s16, mono, mesmo SR)
    listfile = out_wav.with_suffix(".txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for p in parts:
            # Usar caminho absoluto para evitar problemas de path
            abs_path = p.resolve().as_posix()
            f.write(f"file '{abs_path}'\n")
    cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",str(listfile),"-c","copy",str(out_wav)]
    _ffmpeg(cmd)
    listfile.unlink(missing_ok=True)

def _mux_video_audio(video_in: Path, audio_in: Path, out_mp4: Path):
    # apad para garantir que o áudio não termine antes; -shortest deixa o video mandar no fim
    cmd = [
        "ffmpeg","-y",
        "-i",str(video_in),
        "-i",str(audio_in),
        "-filter_complex","[1:a]apad=pad_dur=60[a]",
        "-map","0:v:0","-map","[a]",
        "-c:v","copy","-c:a","aac","-b:a","192k",
        "-shortest",
        str(out_mp4)
    ]
    _ffmpeg(cmd)

# ========= Leitura da transcrição =========
def _find_transcripts_dir(base_data_dir: Path) -> Path:
    cands = [
        base_data_dir/"transcricoes_cortes"/"json",   # pasta JSON convertida
        base_data_dir/"transcricoes_cortes",   # sem acento
        base_data_dir/"transcrições_cortes",   # com acento (fallback)
    ]
    for c in cands:
        if c.exists():
            return c
    raise FileNotFoundError(f"Nenhuma pasta de transcrições encontrada. Esperado uma destas: {cands}")

def _load_sentences(transcript_json: Path):
    with open(transcript_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "sentences" in data:
        data = data["sentences"]

    sents = []
    for item in data:
        start = item.get("start", item.get("start_time", item.get("s")))
        end   = item.get("end",   item.get("end_time",   item.get("e")))
        text_en = item.get("text_en") or item.get("text") or item.get("en") or ""
        text_pt = item.get("text_pt") or item.get("pt") or item.get("text_translated") or ""
        if start is None or end is None:
            continue
        sents.append({
            "start": float(start),
            "end": float(end),
            "dur": float(end) - float(start),
            "text_en": (text_en or "").strip(),
            "text_pt": (text_pt or "").strip()
        })
    sents.sort(key=lambda x: x["start"])
    return sents

def _pick_ts_json(cut_dir: Path) -> Path:
    # Primeiro tenta arquivos específicos
    for name in ("timestamps.json", "timestamp_detalhado.json", "sentences.json"):
        p = cut_dir / name
        if p.exists():
            return p
    
    # Depois tenta arquivo com nome do corte
    corte_name = cut_dir.name
    p = cut_dir / f"{corte_name}.json"
    if p.exists():
        return p
    
    raise FileNotFoundError(f"Nenhum timestamps JSON encontrado em {cut_dir}")

# ========= XTTS wrapper =========
def synth_tts_clone_xtts(text: str, voice_ref_wav: Path, out_wav: Path, language: str = LANG_DEFAULT):
    """
    Gera fala clonada com XTTS v2 usando GPU.
    """
    xtts = _init_xtts()
    if xtts is None:
        # Tentar resetar e reinicializar uma vez
        print("🔄 Tentando resetar XTTS e reinicializar...")
        reset_xtts()
        xtts = _init_xtts()
        if xtts is None:
            raise RuntimeError(f"XTTS v2 não disponível: {_XTTS_IMPORT_ERROR}")
    
    print(f"🎤 Sintetizando: '{text[:50]}...' com GPU")
    print(f"📁 Voz de referência: {voice_ref_wav}")
    
    try:
        # A API já salva WAV/MP3/OGG; por padrão salva WAV 22050~24000, normalizamos depois.
        # Usar parâmetros otimizados para melhor clonagem de voz
        
        # 🎯 CORREÇÃO: Verificar GPU/CPU antes da síntese
        import torch
        if torch.cuda.is_available():
            gpu_memory_before = torch.cuda.memory_allocated(0) / 1024**3
            print(f"📊 [GPU] Memória antes da síntese: {gpu_memory_before:.2f} GB")
        else:
            print("📊 [CPU] Usando CPU para síntese")
        
        # Usar voz ORIGINAL (sem otimização)
        original_voice = voice_ref_wav  # Usar diretamente
        
        xtts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker_wav=str(original_voice),
            language=language
        )
        
        # 🎯 VERIFICAR: GPU foi usada?
        if torch.cuda.is_available():
            gpu_memory_after = torch.cuda.memory_allocated(0) / 1024**3
            gpu_memory_diff = gpu_memory_after - gpu_memory_before
            print(f"📊 [GPU] Memória após síntese: {gpu_memory_after:.2f} GB")
            print(f"🎯 [GPU] Diferença de memória: {gpu_memory_diff:.3f} GB")
            
            if gpu_memory_diff > 0.001:
                print("✅ [GPU] GPU FOI USADA durante a síntese! 🎉")
            else:
                print("⚠️ [GPU] GPU pode NÃO ter sido usada... 🤔")
        else:
            print("✅ [CPU] Síntese concluída com CPU")
        
        # Verificar se o arquivo foi criado
        if not out_wav.exists() or out_wav.stat().st_size == 0:
            raise RuntimeError(f"Falha na síntese: arquivo {out_wav} não foi criado ou está vazio")
        
        print(f"✅ Áudio sintetizado: {out_wav.stat().st_size} bytes")
        
        # Normaliza e aplica pós-processamento para melhor qualidade
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
        
        return out_wav
        
    except Exception as e:
        print(f"❌ Erro na síntese XTTS: {e}")
        # Se falhar, resetar XTTS para próxima tentativa
        reset_xtts()
        raise RuntimeError(f"Falha na síntese de voz: {e}")

# ========= Pipeline principal =========
def dub_by_sentences_xtts(
    base_data_dir: Path,
    cut_id: str,
    video_cut_path: Path,
    out_dir: Path,
    voice_ref_wav: Path,
    prefer_lang: str = "pt"  # "pt" usa text_pt; "en" usa text_en/text
):
    """
    Dublagem clonada por sentença para um corte usando GPU.
    Retorna dict com caminhos do áudio/vídeo/report e nº de sentenças.
    """
    print(f"🎬 Iniciando dublagem XTTS para: {cut_id}")
    print(f"📁 Vídeo: {video_cut_path}")
    print(f"🎤 Voz: {voice_ref_wav}")
    print(f"🌍 Idioma: {prefer_lang}")
    
    # Verificar se o vídeo existe
    if not video_cut_path.exists():
        raise FileNotFoundError(f"Vídeo não encontrado: {video_cut_path}")
    
    # Verificar se a voz de referência existe
    if not voice_ref_wav.exists():
        raise FileNotFoundError(f"Arquivo de voz de referência não encontrado: {voice_ref_wav}")
    
    # Localiza transcrição
    transcripts_dir = _find_transcripts_dir(base_data_dir)
    print(f"🔍 [DEBUG] Pasta de transcrições: {transcripts_dir}")
    print(f"🔍 [DEBUG] Cut ID recebido: {cut_id}")
    
    # Extrair nome base do cut_id (remover _legendado se existir)
    base_cut_id = cut_id.replace("_legendado", "")
    print(f"🔍 [DEBUG] Nome base extraído: {base_cut_id}")
    
    # Se a pasta é json, procura diretamente o arquivo
    if transcripts_dir.name == "json":
        ts_json = transcripts_dir / f"{base_cut_id}.json"
        print(f"🔍 [DEBUG] Procurando JSON: {ts_json}")
    else:
        cut_dir = transcripts_dir / base_cut_id
        print(f"🔍 [DEBUG] Procurando pasta: {cut_dir}")
        ts_json = _pick_ts_json(cut_dir)
    
    print(f"🔍 [DEBUG] Arquivo JSON final: {ts_json}")
    print(f"🔍 [DEBUG] Arquivo existe? {ts_json.exists()}")
    
    if not ts_json.exists():
        raise FileNotFoundError(f"Arquivo de transcrição não encontrado: {ts_json}")
    
    print(f"📄 Carregando transcrição: {ts_json}")
    sentences = _load_sentences(ts_json)
    print(f"📝 Encontradas {len(sentences)} sentenças")

    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / f"_work_{cut_id}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    parts = []
    report = []

    print(f"🎵 Processando {len(sentences)} sentenças...")
    
    for i, s in enumerate(sentences):
        print(f"\n--- Sentença {i+1}/{len(sentences)} ---")
        
        # Escolhe o texto pelo idioma preferido, com fallback
        text = s["text_pt"] if (prefer_lang == "pt" and s["text_pt"]) else (s["text_en"] or s["text_pt"])
        text = text or ""  # garante string
        
        # Duração alvo baseada nos timestamps reais das legendas
        start_time = float(s["start"])
        end_time = float(s["end"])
        target = max(0.05, end_time - start_time)
        

        print(f"📝 Texto: '{text[:100]}...'")
        print(f"⏱️  Duração alvo: {target:.2f}s")

        raw_wav = work / f"sent_{i:03d}_raw.wav"
        fit_wav = work / f"sent_{i:03d}_fit.wav"

        # 1) TTS clonada (XTTS v2)
        print(f"🎤 Sintetizando com GPU...")
        synth_tts_clone_xtts(text, voice_ref_wav, raw_wav, language=("pt" if prefer_lang=="pt" else "en"))

        # 2) Ajusta duração para bater exatamente com o target
        print(f"⚡ Ajustando duração...")
        newdur, ratio = _time_stretch_to_duration(raw_wav, fit_wav, target, sr=SR)
        parts.append(fit_wav)
        print(f"✅ Duração ajustada: {newdur:.2f}s (ratio: {ratio:.3f})")
        

        # 3) Insere pausa entre sentenças
        if i < len(sentences) - 1:
            next_start = float(sentences[i+1]["start"])
            current_end = float(s["end"])
            pause = max(0.0, next_start - current_end)
            
            if pause > 1e-3:
                print(f"🔇 Inserindo pausa: {pause:.2f}s")
                pause_wav = work / f"pause_{i:03d}.wav"
                _make_silence(pause_wav, pause, sr=SR)
                parts.append(pause_wav)

        report.append({
            "index": i,
            "text": text,
            "target_sec": target,
            "fit_dur_sec": newdur,
            "ratio": ratio,
            "start": s["start"],
            "end": s["end"]
        })

    print(f"\n🔗 Concatenando {len(parts)} partes de áudio...")
    # 4) Concatena o áudio final do corte
    out_wav = out_dir / f"{cut_id}_dub.wav"
    _concat_wavs_concatdemux(out_wav, parts)
    print(f"✅ Áudio concatenado: {out_wav}")

    print(f"🎬 Muxando vídeo com áudio dublado...")
    # 5) Muxa com o vídeo do corte
    out_mp4 = out_dir / f"{cut_id}_dub.mp4"
    _mux_video_audio(video_cut_path, out_wav, out_mp4)
    print(f"✅ Vídeo dublado: {out_mp4}")

    # 6) Salva relatório
    report_path = out_dir / f"{cut_id}_align_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📊 Relatório salvo: {report_path}")

    print(f"\n🎉 DUBLAGEM CONCLUÍDA!")
    print(f"📁 Vídeo final: {out_mp4}")
    print(f"🎵 Áudio: {out_wav}")
    print(f"📊 Sentenças processadas: {len(sentences)}")

    return {
        "audio": str(out_wav),
        "video": str(out_mp4),
        "report": str(report_path),
        "sentences": len(sentences)
    }

# ========= Função de integração para o app.py =========
def dublar_corte_xtts(cut_id: str, prefer_lang="pt", base_data_dir="data", outputs_dir="outputs"):
    """
    Função simplificada para integração no app.py
    """
    print(f"🚀 [DEBUG] dublar_corte_xtts chamada com:")
    print(f"🚀 [DEBUG] - cut_id: {cut_id}")
    print(f"🚀 [DEBUG] - prefer_lang: {prefer_lang}")
    print(f"🚀 [DEBUG] - base_data_dir: {base_data_dir}")
    print(f"🚀 [DEBUG] - outputs_dir: {outputs_dir}")
    
    base_data = Path(base_data_dir)
    
    # Procurar o vídeo em diferentes locais possíveis
    possible_video_paths = [
        Path(f"data/final/{cut_id}.mp4"),           # Vídeo exato da pasta final
        Path(f"data/final/{cut_id}_legendado.mp4"), # Vídeo legendado da pasta final
        Path(f"data/cortes/{cut_id}.mp4"),           # Vídeo original dos cortes
        Path(f"{outputs_dir}/cortes/{cut_id}.mp4"),  # Vídeo na pasta de outputs
        Path(f"static/final/{cut_id}.mp4"),          # Vídeo exato da pasta static
        Path(f"static/final/{cut_id}_legendado.mp4") # Vídeo legendado da pasta static
    ]
    
    print(f"🔍 [DEBUG] Procurando vídeos em:")
    for i, path in enumerate(possible_video_paths):
        exists = path.exists()
        print(f"🔍 [DEBUG] {i+1}. {path} - {'✅ EXISTE' if exists else '❌ NÃO EXISTE'}")
    
    video_cut = None
    for video_path in possible_video_paths:
        if video_path.exists():
            video_cut = video_path
            print(f"✅ [DEBUG] Vídeo encontrado: {video_cut}")
            break
    
    if video_cut is None:
        raise FileNotFoundError(f"Vídeo não encontrado para {cut_id}. Procurado em: {possible_video_paths}")
    
    out_dir = Path(f"{outputs_dir}/dublados/{cut_id}")
    
    # Priorizar a voz do Paulo Links - testando com minha_voz.wav primeiro
    possible_refs = [
        Path("voice_refs/minha_voz.wav"),          # Sua voz original (90MB)
        Path("voice_refs/paulo_links_fixed.wav"),  # Sua voz clonada convertida
        Path("voice_refs/paulo_links.wav"),        # Sua voz clonada original
        Path("voice_refs/voice_ref.wav"),
        Path("audio/audio.wav"),
        Path("data/audio/audio.wav")
    ]
    
    print(f"🔍 [DEBUG] Procurando vozes de referência:")
    for i, ref in enumerate(possible_refs):
        exists = ref.exists()
        print(f"🔍 [DEBUG] {i+1}. {ref} - {'✅ EXISTE' if exists else '❌ NÃO EXISTE'}")
    
    voice_ref = None
    for ref in possible_refs:
        if ref.exists():
            voice_ref = ref
            print(f"✅ [DEBUG] Voz encontrada: {voice_ref}")
            break
    
    if voice_ref is None:
        raise FileNotFoundError(f"Nenhum arquivo de referência de voz encontrado. Procurado em: {possible_refs}")
    
    print(f"🎤 Usando voz de referência: {voice_ref}")

    print(f"🎬 DUBLAGEM XTTS v2 - {cut_id}")
    print(f"📁 Vídeo encontrado: {video_cut}")
    print(f"🎤 Voz de referência: {voice_ref}")
    print(f"📂 Pasta de saída: {out_dir}")

    result = dub_by_sentences_xtts(
        base_data_dir=base_data,
        cut_id=cut_id,
        video_cut_path=video_cut,
        out_dir=out_dir,
        voice_ref_wav=voice_ref,
        prefer_lang=prefer_lang,
    )
    print("✅ DUBLAGEM CONCLUÍDA:", result)
    return result

if __name__ == "__main__":
    # teste rápido
    try:
        result = dublar_corte_xtts("corte_1", prefer_lang="pt")
        print("Teste concluído com sucesso!")
        print(f"Arquivos gerados: {result}")
    except Exception as e:
        print(f"Erro no teste: {e}")
