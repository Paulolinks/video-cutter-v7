import spacy
import torch
from difflib import SequenceMatcher
from transformers import pipeline

def carregar_modelo_spacy(idioma):
    return spacy.load("pt_core_news_sm") if idioma == "pt" else spacy.load("en_core_web_sm")

def carregar_sumarizador(idioma):
    modelo = "pierreguillou/t5-base-pt-summarization" if idioma == "pt" else "facebook/bart-large-cnn"
    usar_gpu = 0 if torch.cuda.is_available() else -1
    return pipeline("summarization", model=modelo, device=usar_gpu, truncation=True)

def extrair_frases_de_efeito(texto, idioma, segmentos, tempo_min=15.0, tempo_max=53.0, similaridade_min=0.75):
    nlp = carregar_modelo_spacy(idioma)
    doc = nlp(texto)

    frases = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
    transcript = [(seg.start, seg.end, seg.text.strip()) for seg in segmentos]

    resultados = []

    for frase in frases:
        melhor_match = None
        maior_sim = 0.0

        for i in range(len(transcript)):
            for j in range(i + 1, min(i + 6, len(transcript))):
                trecho = " ".join(seg[2] for seg in transcript[i:j])
                start = transcript[i][0]
                end = transcript[j - 1][1]
                duracao = end - start

                if duracao < tempo_min or duracao > tempo_max:
                    continue

                sim = SequenceMatcher(None, frase.lower(), trecho.lower()).ratio()
                if sim > maior_sim:
                    maior_sim = sim
                    melhor_match = {
                        "start": round(start, 2),
                        "end": round(end, 2),
                        "text": frase
                    }

        if melhor_match and maior_sim >= similaridade_min:
            print(f"✅ Match: '{frase[:60]}...' ({maior_sim:.2f})")
            resultados.append(melhor_match)
        else:
            print(f"❌ Ignorado: '{frase[:60]}...' (similaridade: {maior_sim:.2f})")

    print(f"\n🔢 Total de frases selecionadas: {len(resultados)}")
    return resultados