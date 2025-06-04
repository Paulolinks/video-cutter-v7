from difflib import SequenceMatcher





# Aqui que definimos o tempo mínimo e máximo para os cortes
def mapear_frases(frases, segments, tempo_min=15.0, tempo_max=45.0):
    transcript = [(seg.start, seg.end, seg.text.strip()) for seg in segments]
    print(f"🧠 Segments disponíveis: {len(transcript)}")
    print(f"🧠 Frases de efeito: {len(frases)}")

    resultados = []

    for frase in frases:
        texto = frase["text"].strip()
        palavras = texto.split()

        if len(palavras) < 4:
            print(f"⚠️ Pulando frase curta: {texto}")
            continue

        melhor_inicio, melhor_fim, maior_sim = None, None, 0

        for i in range(len(transcript)):
            for j in range(i + 1, len(transcript) + 1):
                trecho = " ".join(seg[2] for seg in transcript[i:j])
                sim = SequenceMatcher(None, texto.lower(), trecho.lower()).ratio()
                start = transcript[i][0]
                end = transcript[j - 1][1]
                if sim > maior_sim and tempo_min <= (end - start) <= tempo_max:
                    maior_sim = sim
                    melhor_inicio, melhor_fim = start, end

        if melhor_inicio is not None:
            print(f"✅ Match encontrado: '{texto}' ({maior_sim:.2f}) de {melhor_inicio:.2f}s a {melhor_fim:.2f}s")
            resultados.append({
                "start": round(melhor_inicio, 2),
                "end": round(melhor_fim, 2),
                "text": texto
            })
        else:
            print(f"❌ Sem correspondência para: {texto}")

    print(f"\n🔢 Total de cortes encontrados: {len(resultados)}")
    return resultados
