# FUNCIONALIDADES AVANÇADAS DO TTS
import os
import time
import librosa
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, AudioClip

def analisar_emocao_audio_original(video_path, timestamps):
    try:
        print(" Analisando emoção do áudio original...")
        
        video = VideoFileClip(video_path)
        audio_original = video.audio
        
        import tempfile
        temp_audio_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        audio_original.write_audiofile(temp_audio_path, logger=None, verbose=False)
        
        y, sr = librosa.load(temp_audio_path, sr=22050)
        os.remove(temp_audio_path)
        
        emocoes_por_segmento = []
        
        for i, ts in enumerate(timestamps):
            inicio = ts['start']
            fim = ts['end']
            
            start_sample = int(inicio * sr)
            end_sample = int(fim * sr)
            segment_audio = y[start_sample:end_sample]
            
            if len(segment_audio) == 0:
                emocoes_por_segmento.append({
                    'segmento': i,
                    'tipo': 'neutro',
                    'intensidade': 0.5,
                    'energia': 0.0,
                    'ritmo': 0.0,
                    'tom': 0.0
                })
                continue
            
            emocao = detectar_emocao_segmento_avancada(segment_audio, sr)
            emocao['segmento'] = i
            emocoes_por_segmento.append(emocao)
            
            print(f"    Emoção: {emocao['tipo']} (intensidade: {emocao['intensidade']:.2f})")
        
        video.close()
        audio_original.close()
        
        return emocoes_por_segmento
        
    except Exception as e:
        print(f" Erro na análise de emoção: {e}")
        return []

def detectar_emocao_segmento_avancada(audio_segmento, sr):
    try:
        mfccs = librosa.feature.mfcc(y=audio_segmento, sr=sr, n_mfcc=13)
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_segmento, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_segmento)
        rms = librosa.feature.rms(y=audio_segmento)
        tempo, beats = librosa.beat.beat_track(y=audio_segmento, sr=sr)
        
        mfcc_mean = np.mean(mfccs)
        spectral_mean = np.mean(spectral_centroids)
        zcr_mean = np.mean(zero_crossing_rate)
        rms_mean = np.mean(rms)
        
        energia = rms_mean
        ritmo = tempo / 120.0
        tom = spectral_mean / 4000.0
        instabilidade = zcr_mean
        
        if energia > 0.15 and ritmo > 0.8 and tom > 0.6:
            tipo_emocao = "excitado"
            intensidade = min(energia * 6 + ritmo * 0.3 + tom * 0.2, 1.0)
        elif energia < 0.05 and ritmo < 0.4 and tom < 0.4:
            tipo_emocao = "calmo"
            intensidade = 0.3 + (1.0 - energia) * 0.2
        elif instabilidade > 0.15 and energia > 0.1:
            tipo_emocao = "nervoso"
            intensidade = min(instabilidade * 4 + energia * 2, 1.0)
        elif ritmo > 0.6 and energia > 0.1:
            tipo_emocao = "energético"
            intensidade = min(ritmo * 0.8 + energia * 3, 1.0)
        else:
            tipo_emocao = "neutro"
            intensidade = 0.5
        
        return {
            'tipo': tipo_emocao,
            'intensidade': float(intensidade),
            'energia': float(energia),
            'ritmo': float(ritmo),
            'tom': float(tom),
            'instabilidade': float(instabilidade)
        }
        
    except Exception as e:
        print(f" Erro na detecção de emoção: {e}")
        return {
            'tipo': 'neutro',
            'intensidade': 0.5,
            'energia': 0.0,
            'ritmo': 0.0,
            'tom': 0.0,
            'instabilidade': 0.0
        }

def calcular_fator_emocao(emocao):
    try:
        tipo = emocao['tipo']
        intensidade = emocao['intensidade']
        energia = emocao['energia']
        ritmo = emocao['ritmo']
        
        if tipo == "excitado":
            fator_base = 1.0 + intensidade * 0.4
        elif tipo == "calmo":
            fator_base = 1.0 - intensidade * 0.3
        elif tipo == "nervoso":
            fator_base = 1.0 + intensidade * 0.5
        elif tipo == "energético":
            fator_base = 1.0 + ritmo * 0.3
        else:
            fator_base = 1.0
        
        if energia > 0.1:
            fator_energia = 1.0 + (energia - 0.1) * 0.5
        else:
            fator_energia = 0.8 + energia * 2.0
        
        fator_final = fator_base * fator_energia
        fator_final = max(0.5, min(2.0, fator_final))
        
        return fator_final
        
    except Exception as e:
        print(f" Erro ao calcular fator de emoção: {e}")
        return 1.0

def gerar_audio_tts_com_emocao(texto, voice, lang_target, emocao):
    try:
        print(f" Gerando áudio com emoção: {emocao['tipo']} (intensidade: {emocao['intensidade']:.2f})")
        
        from app import usar_voz_clonada_real, gerar_audio_tts
        
        if voice.startswith("clonada_") or "clonada" in voice.lower():
            audio_path = usar_voz_clonada_real(texto, lang_target)
        else:
            audio_path = gerar_audio_tts(texto, voice, lang_target)
        
        if not audio_path:
            return None
        
        audio_ajustado = aplicar_ajustes_emocionais_avancados(audio_path, emocao)
        return audio_ajustado
        
    except Exception as e:
        print(f" Erro ao gerar áudio com emoção: {e}")
        return None

def aplicar_ajustes_emocionais_avancados(audio_path, emocao):
    try:
        audio, sr = librosa.load(audio_path, sr=22050)
        
        tipo = emocao['tipo']
        intensidade = emocao['intensidade']
        energia = emocao['energia']
        ritmo = emocao['ritmo']
        tom = emocao['tom']
        instabilidade = emocao.get('instabilidade', 0.0)
        
        pitch_shift = 0
        if tipo == "excitado":
            pitch_shift = int(tom * 4)
        elif tipo == "calmo":
            pitch_shift = -int(tom * 2)
        elif tipo == "nervoso":
            pitch_shift = int(instabilidade * 2)
        
        velocidade = 1.0
        if tipo == "excitado":
            velocidade = 1.0 + ritmo * 0.3
        elif tipo == "calmo":
            velocidade = 1.0 - ritmo * 0.2
        elif tipo == "nervoso":
            velocidade = 1.0 + intensidade * 0.4
        
        if pitch_shift != 0:
            audio = librosa.effects.pitch_shift(audio, sr=sr, n_steps=pitch_shift)
        
        if abs(velocidade - 1.0) > 0.05:
            audio = librosa.effects.time_stretch(audio, rate=velocidade)
        
        output_path = f"temp_audio_emocao_{int(time.time() * 1000)}.wav"
        librosa.output.write_wav(output_path, audio, sr)
        
        print(f" Ajustes emocionais aplicados: pitch={pitch_shift}, velocidade={velocidade:.2f}x")
        
        return output_path
        
    except Exception as e:
        print(f" Erro ao aplicar ajustes emocionais: {e}")
        return audio_path
