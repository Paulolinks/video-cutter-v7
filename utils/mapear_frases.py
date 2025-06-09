from difflib import SequenceMatcher

# Define tempo mínimo e máximo, e comprimento máximo permitido por corte
def mapear_frases(frases, segments, tempo_min=15.0, tempo_max=53.0, max_palavras=30):
    transcript = [(seg.start, seg.end, seg.text.strip()) for seg in segments]
    print(f"🧠 Segments disponíveis: {len(transcript)}")
    print(f"🧠 Frases de efeito: {len(frases)}")

    resultados = []

    for frase in frases:
        texto = frase["text"].strip()
        if len(texto.split()) < 6 or len(texto) < 25:
            print(f"⚠️ Pulando frase irrelevante: {texto}")
            continue

        melhor_inicio, melhor_fim, maior_sim = None, None, 0

        for i in range(len(transcript)):
            duracao_acumulada = 0
            trecho = ""
            palavras_acumuladas = 0

            for j in range(i, len(transcript)):
                trecho += (" " + transcript[j][2]) if trecho else transcript[j][2]
                duracao_acumulada = transcript[j][1] - transcript[i][0]
                palavras_acumuladas = len(trecho.split())

                if duracao_acumulada > tempo_max or palavras_acumuladas > max_palavras:
                    break

                if duracao_acumulada >= tempo_min:
                    sim = SequenceMatcher(None, texto.lower(), trecho.lower()).ratio()
                    if sim > maior_sim:
                        maior_sim = sim
                        melhor_inicio = transcript[i][0]
                        melhor_fim = transcript[j][1]

        if melhor_inicio is not None:
            print(f"✅ Match: '{texto[:60]}...' ({maior_sim:.2f})")
            resultados.append({
                "start": round(melhor_inicio, 2),
                "end": round(melhor_fim, 2),
                "text": texto
            })
        else:
            print(f"❌ Sem correspondência para: '{texto[:60]}...'")

    print(f"\n🔢 Total de cortes encontrados: {len(resultados)}")
    return resultados
