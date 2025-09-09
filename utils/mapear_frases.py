# mapear_frases.py
from difflib import SequenceMatcher
import os, re, subprocess, glob

def _estimar_wps(segments):
    total_w = sum(len(seg.text.split()) for seg in segments if getattr(seg, "text", "").strip())
    if not segments:
        return 2.5
    inicio  = segments[0].start
    fim     = segments[-1].end
    dur     = max(1e-6, fim - inicio)
    wps     = total_w / dur
    return max(1.5, min(4.5, wps))  # fala típica

def _ffmpeg_bin():
    # usa o que você já define no main.py
    return os.environ.get("IMAGEIO_FFMPEG_EXE") or os.path.join("bin","ffmpeg","ffmpeg.exe")

def _detectar_silencios(video_path, min_sil=0.35, thresh="-30dB"):
    """Retorna lista de (start,end) de silencios com ffmpeg silencedetect."""
    try:
        cmd = [
            _ffmpeg_bin(), "-hide_banner", "-nostats", "-i", video_path,
            "-af", f"silencedetect=noise={thresh}:d={min_sil}",
            "-f", "null", "-"
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        out = (p.stderr or "") + (p.stdout or "")
        silences, cur = [], {}
        for line in out.splitlines():
            line=line.strip()
            if "silence_start" in line:
                cur = {"start": float(line.split("silence_start:")[-1].strip())}
            elif "silence_end" in line and "silence_duration" in line:
                parts = line.split("silence_end:")[-1].split("|")[0].strip()
                cur["end"] = float(parts)
                if "start" in cur and "end" in cur:
                    silences.append((cur["start"], cur["end"]))
        return silences
    except Exception:
        return []

def _snap_to_silence(t, silences, raio=0.7):
    """Ajusta um tempo t para a borda de silêncio mais próxima dentro de ±raio."""
    melhor = (None, 1e9)
    for s,e in silences:
        for b in (s,e):
            d = abs(b - t)
            if d < melhor[1]:
                melhor = (b, d)
    return melhor[0] if melhor[1] <= raio else t

def _fresh_chunks_from_transcript(segments):
    """Transforma segments (start,end,text) em lista [(s,e,text)]."""
    return [(seg.start, seg.end, seg.text.strip()) for seg in segments if getattr(seg,"text","").strip()]

def mapear_frases(frases, segments, tempo_min=12.0, tempo_max=60.0, video_path=None, usar_silencio=True, min_clipes=10):
    """
    frases: lista de dicts com {"text": "..."} (suas 'frases de efeito')
    segments: transcrição com timestamps (ex.: Whisper segments)
    Retorna: lista de dicts {"start":..., "end":..., "text":...}
    """
    transcript = _fresh_chunks_from_transcript(segments)
    if not transcript:
        return []

    wps = _estimar_wps(segments)
    max_palavras = int(tempo_max * wps * 1.25)  # teto dinâmico de palavras

    silences = _detectar_silencios(video_path) if (usar_silencio and video_path and os.path.exists(video_path)) else []

    resultados = []
    # mapeia cada frase de efeito para o melhor trecho do transcript
    for frase in frases:
        alvo = (frase.get("text") or "").strip()
        if not alvo:
            continue
        if len(alvo.split()) < 5 or len(alvo) < 25:
            # muito curto -> geralmente vira ruído; deixa para join/fallback
            continue

        melhor = {"score": 0.0, "i": None, "j": None, "start": None, "end": None}

        for i in range(len(transcript)):
            trecho_txt = ""
            s0 = transcript[i][0]
            pals = 0
            for j in range(i, len(transcript)):
                s1, e1, t1 = transcript[j]
                dur = e1 - s0
                if dur > tempo_max:
                    break

                # agrega texto e conta palavras
                trecho_txt = (trecho_txt + " " + t1).strip() if trecho_txt else t1
                pals += len(t1.split())
                # só respeite teto de palavras depois que já chegou perto do mínimo
                if pals > max_palavras and dur >= tempo_min * 0.8:
                    break

                sim = SequenceMatcher(None, alvo.lower(), trecho_txt.lower()).ratio()
                if dur >= tempo_min * 0.55 and sim > melhor["score"]:
                    melhor.update(score=sim, i=i, j=j, start=s0, end=e1)

        if melhor["i"] is None:
            continue

        # JOIN: se ficou menor que o mínimo, estende por sentenças seguintes até atingir min, sem estourar max
        i, j, start, end = melhor["i"], melhor["j"], melhor["start"], melhor["end"]
        k = j
        while (end - start) < tempo_min and (k + 1) < len(transcript) and (transcript[k+1][1] - start) <= tempo_max:
            k += 1
            end = transcript[k][1]
            # se termina com pontuação, ótimo; senão continua até atingir ~min
            texto_join = " ".join(t[2] for t in transcript[i:k+1])
            if re.search(r"[.!?…]\s*$", texto_join) and (end - start) >= tempo_min*0.9:
                break

        # SNAP em silêncio (fica bem mais natural)
        if silences:
            start = _snap_to_silence(start, silences, 0.7)
            end   = _snap_to_silence(end,   silences, 0.7)
            if end - start < tempo_min*0.75:  # não destruir o corte
                # se “grudou demais”, volta a bordas originais
                start, end = melhor["start"], melhor["end"]

        resultados.append({"start": round(start,2), "end": round(end,2), "text": alvo})

    # Dedup + ordenar
    seen, clean = set(), []
    for r in sorted(resultados, key=lambda x: (x["start"], x["end"])):
        key = (round(r["start"],1), round(r["end"],1))
        if key in seen: 
            continue
        seen.add(key)
        # SPLIT: se ficou grande demais, quebra em 2 partes (fallback simples por tempo médio)
        dur = r["end"] - r["start"]
        if dur > tempo_max:
            mid = (r["start"] + r["end"]) / 2
            clean.append({"start": r["start"], "end": round(mid,2), "text": r["text"]})
            clean.append({"start": round(mid,2), "end": r["end"], "text": r["text"]})
        else:
            clean.append(r)

    # Fallback: se ainda gerou poucos cortes, crie janelas por tempo (garante saída)
    if len(clean) < min_clipes:
        # pega duração total do transcript
        total = transcript[-1][1] - transcript[0][0]
        win, hop = 18.0, 17.0  # janela e avanço
        t = transcript[0][0]
        while t + 3.0 < transcript[-1][1]:
            s, e = t, min(t + win, transcript[-1][1])
            # snap opcional
            if silences:
                s = _snap_to_silence(s, silences, 0.7)
                e = _snap_to_silence(e, silences, 0.7)
            if e - s >= 9.0:  # não gere cortes minúsculos
                clean.append({"start": round(s,2), "end": round(e,2), "text": "[fallback]"})
            t += hop

    return clean
