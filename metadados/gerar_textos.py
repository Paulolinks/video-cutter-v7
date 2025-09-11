
from __future__ import annotations
import re
import yake
import spacy
from unidecode import unidecode

# Carrega spaCy PT; se não houver o modelo, cai para um pipeline vazio.
try:
    NLP = spacy.load("pt_core_news_sm")
except OSError:
    NLP = spacy.blank("pt")

def _sentencas(texto: str) -> list[str]:
    """Quebra o texto em sentenças de forma robusta."""
    doc = NLP(texto)
    sents = [s.text.strip() for s in doc.sents if s.text.strip()]
    if not sents:
        sents = re.split(r"[.!?]\s+", texto)
        sents = [s.strip() for s in sents if s.strip()]
    return sents

def extrair_palavras_chave(texto: str, topk: int = 12) -> list[str]:
    """Extrai palavras-chave com YAKE (rápido e local)."""
    kw_extractor = yake.KeywordExtractor(lan="pt", n=1, top=topk)
    kws = [k for k,_ in kw_extractor.extract_keywords(texto)]
    # Normaliza
    kws = [unidecode(k.lower()) for k in kws if 2 <= len(k) <= 20]
    # Remove duplicatas mantendo ordem
    kws = list(dict.fromkeys(kws))
    return kws[:topk]

def gerar_titulo(texto: str, max_chars: int = 60) -> str:
    """Escolhe uma sentença curta como título."""
    sents = _sentencas(texto)
    if not sents:
        return "Vídeo curto"
    candidatos = sorted(sents, key=len)
    for s in candidatos:
        t = s.strip(" .!?:;“”\"'").capitalize()
        if 12 <= len(t) <= max_chars:
            return t
    return candidatos[0][:max_chars].strip()

def gerar_hashtags(texto: str, n=8) -> list[str]:
    kws = extrair_palavras_chave(texto, topk=20)
    tags = []
    for k in kws:
        k = re.sub(r"[^a-z0-9]+", "", unidecode(k.lower()))
        if k and k not in {"que","para","com","uma","como","mais"}:
            tags.append("#" + k)
        if len(tags) >= n:
            break
    base = ["#shorts", "#motivacao", "#video"]
    for b in base:
        if b not in tags:
            tags.append(b)
    return tags[:n]

def gerar_legenda(texto: str, titulo: str, link_bio: str | None = None, tom: str = "direto") -> str:
    sents = _sentencas(texto) or [texto.strip()]
    blocos = sents[:2] if len(sents) < 4 else sents[:3]
    corpo = " ".join(blocos).strip()
    cta = f"\n\nQuer mais? Acesse: {link_bio}" if link_bio else ""
    if tom == "inspirador":
        return f"{titulo}\n\n{corpo}\n\nVocê consegue!{cta}"
    return f"{titulo}\n\n{corpo}{cta}"
