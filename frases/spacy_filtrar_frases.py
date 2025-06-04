import spacy
from transformers import pipeline
from difflib import SequenceMatcher
from transformers import pipeline
import torch



def carregar_modelo_spacy(idioma):
    return spacy.load("pt_core_news_sm") if idioma == "pt" else spacy.load("en_core_web_sm")

def carregar_sumarizador(idioma):
    modelo = "pierreguillou/t5-base-pt-summarization" if idioma == "pt" else "facebook/bart-large-cnn"
    usar_gpu = 0 if torch.cuda.is_available() else -1
    return pipeline("summarization", model=modelo, device=usar_gpu, truncation=True)

def extrair_frases_de_efeito(texto, idioma, segmentos):
    nlp = carregar_modelo_spacy(idioma)
    doc = nlp(texto)

    frases = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 1]
    resultados = []

    i = 0
    while i < len(segmentos):
        grupo_texto = ""
        grupo_inicio = segmentos[i].start
        grupo_fim = segmentos[i].end

        grupo_texto += segmentos[i].text.strip()
        i += 1

        while i < len(segmentos):
            duracao = grupo_fim - grupo_inicio

            if duracao >= 15 and duracao <= 35:
                resultados.append({
                    "start": round(grupo_inicio, 2),
                    "end": round(grupo_fim, 2),
                    "text": grupo_texto.strip()
                })
                break

            if duracao > 35:
                break

            grupo_texto += " " + segmentos[i].text.strip()
            grupo_fim = segmentos[i].end
            i += 1

    print(f"\n🔢 Total de cortes encontrados: {len(resultados)}")
    for r in resultados:
        print(f"[{r['start']}s - {r['end']}s] {r['text'][:80]}...")

    return resultados
