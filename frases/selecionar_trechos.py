# frases/selecionar_trechos.py
import spacy
from difflib import SequenceMatcher
import re
from collections import Counter
import math
from .config_selecao import (
    DURACAO, PESOS_SCORE, FILTROS, PALAVRAS_EXTRAS, DEBUG,
    get_config_por_rede_social
)


# --- Helpers para ler segmentos vindos como dict OU como objeto (Faster-Whisper etc.) ---

def _get(seg, key, default=None):
    # tenta atributo .key
    v = getattr(seg, key, None)
    if v is not None:
        return v
    # tenta dict-like
    if isinstance(seg, dict):
        return seg.get(key, default)
    try:
        return seg[key]  # namedtuple / mapping
    except Exception:
        return default

def seg_start(seg) -> float:
    v = _get(seg, "start", 0.0)
    try:
        return float(v)
    except Exception:
        return 0.0

def seg_end(seg) -> float:
    v = _get(seg, "end", None)
    if v is None:
        v = seg_start(seg)
    try:
        return float(v)
    except Exception:
        return seg_start(seg)

def seg_text(seg) -> str:
    v = _get(seg, "text", "")
    return str(v or "")
 

def carregar_nlp(idioma, use_lg=False):
    """Carrega modelo spaCy com fallback para modelo menor"""
    try:
        if use_lg:
            # Tentar modelo grande primeiro
            try:
                return spacy.load("en_core_web_lg" if idioma == "en" else "pt_core_news_lg")
            except OSError:
                print("⚠️ Modelo grande não encontrado, usando modelo pequeno...")
                return spacy.load("en_core_web_sm" if idioma == "en" else "pt_core_news_sm")
        else:
            return spacy.load("en_core_web_sm" if idioma == "en" else "pt_core_news_sm")
    except OSError as e:
        print(f"❌ Erro ao carregar modelo spaCy: {e}")
        print("🔄 Tentando baixar modelo automaticamente...")
        
        # Tentar baixar o modelo
        try:
            from spacy.cli import download
            modelo = "en_core_web_sm" if idioma == "en" else "pt_core_news_sm"
            download(modelo)
            return spacy.load(modelo)
        except Exception as download_error:
            print(f"❌ Erro ao baixar modelo: {download_error}")
            print("🔄 Usando modelo básico...")
            
            # Fallback para modelo básico
            try:
                return spacy.blank("en" if idioma == "en" else "pt")
            except:
                return spacy.blank("en")

# Palavras-chave de alto engajamento para redes sociais
PALAVRAS_ENGAJAMENTO = {
    'pt': {
        'positivas': ['incrível', 'fantástico', 'surpreendente', 'impressionante', 'espetacular', 
                     'maravilhoso', 'sensacional', 'extraordinário', 'excelente', 'perfeito',
                     'genial', 'brilhante', 'notável', 'excepcional', 'único', 'especial',
                     'revolucionário', 'inovador', 'criativo', 'inteligente', 'sábio'],
        'negativas': ['terrível', 'horrível', 'péssimo', 'ruim', 'desastroso', 'catastrófico',
                     'chocante', 'alarmante', 'preocupante', 'perigoso', 'arriscado'],
        'ação': ['descobrir', 'aprender', 'conhecer', 'entender', 'compreender', 'realizar',
                'conquistar', 'alcançar', 'obter', 'ganhar', 'vencer', 'superar', 'criar',
                'construir', 'desenvolver', 'inventar', 'descobrir', 'revelar', 'mostrar'],
        'intensidade': ['muito', 'extremamente', 'totalmente', 'completamente', 'absolutamente',
                       'definitivamente', 'certamente', 'realmente', 'verdadeiramente', 'sinceramente'],
        'perguntas': ['como', 'por que', 'o que', 'quando', 'onde', 'quem', 'qual', 'será que'],
        'exclamações': ['nossa', 'caramba', 'uau', 'não', 'sim', 'claro', 'óbvio', 'exato']
    },
    'en': {
        'positivas': ['amazing', 'incredible', 'fantastic', 'awesome', 'brilliant', 'outstanding',
                     'excellent', 'perfect', 'wonderful', 'spectacular', 'remarkable', 'exceptional',
                     'unique', 'special', 'revolutionary', 'innovative', 'creative', 'intelligent', 'wise'],
        'negativas': ['terrible', 'horrible', 'awful', 'bad', 'disastrous', 'catastrophic',
                     'shocking', 'alarming', 'concerning', 'dangerous', 'risky'],
        'ação': ['discover', 'learn', 'know', 'understand', 'realize', 'achieve', 'accomplish',
                'gain', 'win', 'overcome', 'create', 'build', 'develop', 'invent', 'reveal', 'show'],
        'intensidade': ['very', 'extremely', 'totally', 'completely', 'absolutely', 'definitely',
                       'certainly', 'really', 'truly', 'sincerely'],
        'perguntas': ['how', 'why', 'what', 'when', 'where', 'who', 'which', 'would'],
        'exclamações': ['wow', 'oh', 'no', 'yes', 'sure', 'obviously', 'exactly']
    }
}

def analisar_engajamento(texto: str, idioma: str = 'pt') -> float:
    """Analisa o potencial de engajamento do texto baseado em palavras-chave."""
    if not texto:
        return 0.0
    
    texto_lower = texto.lower()
    palavras = PALAVRAS_ENGAJAMENTO.get(idioma, PALAVRAS_ENGAJAMENTO['pt'])
    palavras_extras = PALAVRAS_EXTRAS.get(idioma, PALAVRAS_EXTRAS['pt'])
    
    score = 0.0
    total_palavras = len(texto.split())
    
    if total_palavras == 0:
        return 0.0
    
    # Pontuação por categoria principal
    for categoria, palavras_cat in palavras.items():
        peso = {
            'positivas': 2.0,
            'negativas': 1.5,  # Negativas também geram engajamento
            'ação': 1.8,
            'intensidade': 1.2,
            'perguntas': 1.5,
            'exclamações': 1.3
        }.get(categoria, 1.0)
        
        for palavra in palavras_cat:
            if palavra in texto_lower:
                score += peso
    
    # Pontuação por categoria extra
    for categoria, palavras_cat in palavras_extras.items():
        peso = {
            'viral': 2.5,      # Palavras virais têm peso maior
            'numeros': 1.8,    # Números chamam atenção
            'tempo': 1.4,      # Referências temporais
            'quantidade': 1.3  # Quantificadores
        }.get(categoria, 1.0)
        
        for palavra in palavras_cat:
            if palavra in texto_lower:
                score += peso
    
    # Normaliza pelo tamanho do texto
    return min(score / total_palavras * 10, 1.0)

def calcular_densidade_informacao(texto: str, nlp) -> float:
    """Calcula a densidade de informação do texto."""
    if not texto:
        return 0.0
    
    doc = nlp(texto)
    tokens = [t for t in doc if not t.is_space and not t.is_punct]
    
    if not tokens:
        return 0.0
    
    # Conta entidades nomeadas, substantivos, adjetivos e verbos
    entidades = len(doc.ents)
    substantivos = len([t for t in tokens if t.pos_ in ['NOUN', 'PROPN']])
    adjetivos = len([t for t in tokens if t.pos_ == 'ADJ'])
    verbos = len([t for t in tokens if t.pos_.startswith('V')])
    
    # Palavras não-stop (conteúdo)
    palavras_conteudo = len([t for t in tokens if not t.is_stop])
    
    # Fórmula de densidade
    densidade = (entidades * 2 + substantivos + adjetivos + verbos + palavras_conteudo) / len(tokens)
    
    return min(densidade, 1.0)

def detectar_estrutura_narrativa(texto: str, nlp) -> float:
    """Detecta se o texto tem estrutura narrativa (início, meio, fim)."""
    if not texto:
        return 0.0
    
    doc = nlp(texto)
    frases = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    
    if len(frases) < 2:
        return 0.0
    
    # Marcadores de início
    inicio_markers = ['primeiro', 'inicialmente', 'começando', 'para começar', 'primeiramente']
    meio_markers = ['depois', 'em seguida', 'então', 'além disso', 'também', 'ainda']
    fim_markers = ['finalmente', 'por último', 'conclusão', 'resumindo', 'em resumo']
    
    texto_lower = texto.lower()
    
    score = 0.0
    if any(marker in texto_lower for marker in inicio_markers):
        score += 0.3
    if any(marker in texto_lower for marker in meio_markers):
        score += 0.3
    if any(marker in texto_lower for marker in fim_markers):
        score += 0.4
    
    return score

def calcular_impacto_visual(texto: str) -> float:
    """Calcula o potencial de impacto visual para redes sociais."""
    if not texto:
        return 0.0
    
    # Pontuação por pontuação e formatação
    score = 0.0
    
    # Exclamações aumentam impacto
    score += texto.count('!') * 0.1
    
    # Interrogações indicam engajamento
    score += texto.count('?') * 0.08
    
    # Números chamam atenção
    numeros = len(re.findall(r'\d+', texto))
    score += numeros * 0.05
    
    # Palavras em maiúscula (se houver)
    maiusculas = len(re.findall(r'[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ]{2,}', texto))
    score += maiusculas * 0.1
    
    # Palavras repetidas para ênfase
    palavras = texto.lower().split()
    if len(palavras) > 0:
        contador = Counter(palavras)
        repetidas = sum(1 for count in contador.values() if count > 1)
        score += (repetidas / len(palavras)) * 0.2
    
    return min(score, 1.0)

def analisar_coerencia_temporal(segmentos, indice_inicio, indice_fim) -> float:
    """Analisa se os segmentos formam uma sequência temporal coerente."""
    if indice_fim <= indice_inicio:
        return 0.0
    
    # Verifica se há pausas muito longas entre segmentos
    pausas = []
    for i in range(indice_inicio, indice_fim - 1):
        fim_atual = seg_end(segmentos[i])
        inicio_proximo = seg_start(segmentos[i + 1])
        pausa = inicio_proximo - fim_atual
        pausas.append(pausa)
    
    if not pausas:
        return 1.0
    
    # Penaliza pausas muito longas (> 2 segundos)
    pausas_longas = sum(1 for p in pausas if p > 2.0)
    score = 1.0 - (pausas_longas / len(pausas)) * 0.5
    
    return max(score, 0.0)

def pausa_longa(prev_end, next_start, lim=0.35):
    return (next_start - prev_end) >= lim

def completude_spacy(nlp, texto: str):
    """Score melhorado do quão 'completo' o trecho soa."""
    texto = (texto or "").strip()
    if not texto:
        return 0.0
    
    doc = nlp(texto)
    
    # Análise sintática básica
    tem_verbo_raiz = any(t.dep_ == "ROOT" and t.pos_.startswith("V") for t in doc)
    tem_sujeito = any(t.dep_.startswith("nsubj") for t in doc)
    tem_noun_chunk = any(True for _ in doc.noun_chunks)
    fim_pontuado = texto[-1:] in ".?!…"
    
    # Análise de coesão
    tem_conectivos = any(t.text.lower() in ['e', 'mas', 'porém', 'então', 'assim', 'portanto', 'além disso'] for t in doc)
    tem_pronomes = any(t.pos_ == 'PRON' for t in doc)
    
    # Análise de riqueza lexical
    tokens = [t for t in doc if not t.is_space and not t.is_punct]
    non_stop = [t for t in tokens if not t.is_stop]
    
    score = 0.0
    
    # Estrutura sintática (40%)
    score += 0.25 if tem_verbo_raiz else 0.0
    score += 0.15 if (tem_sujeito or tem_noun_chunk) else 0.0
    
    # Coesão textual (25%)
    score += 0.10 if tem_conectivos else 0.0
    score += 0.08 if tem_pronomes else 0.0
    score += 0.07 if fim_pontuado else 0.0
    
    # Riqueza lexical (35%)
    if tokens:
        densidade = len(non_stop) / len(tokens)
        score += 0.20 * min(1.0, max(0.0, (densidade - 0.35) / 0.4))
        
        # Diversidade lexical
        palavras_unicas = len(set(t.lemma_.lower() for t in non_stop))
        diversidade = palavras_unicas / len(non_stop) if non_stop else 0
        score += 0.15 * min(1.0, diversidade)
    
    return min(score, 1.0)

def calcular_score_completo(texto: str, nlp, idioma: str = 'pt', tema_doc=None, 
                          segmentos=None, indice_inicio=None, indice_fim=None,
                          rede_social='instagram') -> dict:
    """Calcula um score completo considerando múltiplos fatores."""
    if not texto:
        return {'score': 0.0, 'detalhes': {}}
    
    # Scores individuais
    completude = completude_spacy(nlp, texto)
    engajamento = analisar_engajamento(texto, idioma)
    densidade = calcular_densidade_informacao(texto, nlp)
    narrativa = detectar_estrutura_narrativa(texto, nlp)
    visual = calcular_impacto_visual(texto)
    
    # Similaridade com tema (se fornecido)
    similaridade_tema = 0.0
    if tema_doc is not None:
        similaridade_tema = nlp(texto).similarity(tema_doc)
    
    # Coerência temporal (se segmentos fornecidos)
    coerencia_temporal = 1.0
    if segmentos and indice_inicio is not None and indice_fim is not None:
        coerencia_temporal = analisar_coerencia_temporal(segmentos, indice_inicio, indice_fim)
    
    # Usa configuração específica para a rede social
    _, pesos = get_config_por_rede_social(rede_social)
    
    # Ajusta pesos se não há tema
    if tema_doc is None:
        # Redistribui o peso do tema para engajamento e visual
        peso_tema = pesos.get('similaridade_tema', 0.0)
        pesos['engajamento'] += peso_tema * 0.6
        pesos['visual'] += peso_tema * 0.4
        pesos['similaridade_tema'] = 0.0
    
    # Calcula score final
    score_final = (
        completude * pesos.get('completude', 0.20) +
        engajamento * pesos.get('engajamento', 0.25) +
        densidade * pesos.get('densidade', 0.15) +
        narrativa * pesos.get('narrativa', 0.10) +
        visual * pesos.get('visual', 0.15) +
        similaridade_tema * pesos.get('similaridade_tema', 0.10) +
        coerencia_temporal * pesos.get('coerencia_temporal', 0.05)
    )
    
    return {
        'score': round(score_final, 4),
        'detalhes': {
            'completude': round(completude, 3),
            'engajamento': round(engajamento, 3),
            'densidade': round(densidade, 3),
            'narrativa': round(narrativa, 3),
            'visual': round(visual, 3),
            'similaridade_tema': round(similaridade_tema, 3),
            'coerencia_temporal': round(coerencia_temporal, 3)
        }
    }

def similaridade(a: str, b: str):
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

def similaridade_tema(nlp, texto: str, tema_doc):
    if tema_doc is None:
        return 0.0
    return nlp(texto).similarity(tema_doc)

def juntar_em_janelas(segments, tempo_min, tempo_max, pausa=0.35):
    """
    Junta segmentos contíguos de forma mais inteligente, considerando:
    - Pausas naturais na fala
    - Pontuação no texto
    - Densidade de informação
    - Estrutura narrativa
    """
    segments = list(segments)  # garante indexação
    janelas = []
    i = 0
    n = len(segments)

    while i < n:
        start = seg_start(segments[i])
        end = seg_end(segments[i])
        textos = [seg_text(segments[i])]

        j = i + 1
        while j < n:
            gap = seg_start(segments[j]) - end
            
            # Pausa muito longa - para aqui
            if gap > pausa * 2:  # Pausa muito longa
                break
            
            novo_end = seg_end(segments[j])
            duracao_atual = novo_end - start
            
            # Excede tempo máximo - para aqui
            if duracao_atual > tempo_max:
                break
            
            # Verifica se vale a pena adicionar este segmento
            texto_atual = " ".join(t for t in textos if t)
            texto_novo = seg_text(segments[j])
            texto_combinado = f"{texto_atual} {texto_novo}".strip()
            
            # Critérios para adicionar o segmento:
            # 1. Pausa não muito longa
            # 2. Texto não termina abruptamente (tem pontuação)
            # 3. Não cria frases muito longas sem pausas
            deve_adicionar = True
            
            if gap > pausa:  # Pausa moderada
                # Só adiciona se o texto atual termina com pontuação
                if not any(texto_atual.strip().endswith(p) for p in '.!?…'):
                    deve_adicionar = False
            
            # Verifica se o texto novo começa com conectivos (indica continuação)
            texto_novo_lower = texto_novo.lower().strip()
            conectivos = ['e', 'mas', 'porém', 'então', 'assim', 'portanto', 'além disso', 
                         'também', 'ainda', 'depois', 'em seguida', 'finalmente']
            
            if not any(texto_novo_lower.startswith(c) for c in conectivos) and gap > pausa * 0.8:
                # Se não há conectivo e a pausa é significativa, pode não valer a pena
                if len(texto_combinado.split()) > 30:  # Texto já muito longo
                    deve_adicionar = False
            
            if deve_adicionar:
                textos.append(texto_novo)
                end = novo_end
                j += 1
            else:
                break

        # Só adiciona se atende critérios mínimos
        texto_final = " ".join(t for t in textos if t).strip()
        duracao_final = end - start
        
        if (duracao_final >= tempo_min and 
            len(texto_final.split()) >= 5 and  # Pelo menos 5 palavras
            any(texto_final.endswith(p) for p in '.!?…') or  # Termina com pontuação
            duracao_final >= tempo_min * 1.5):  # Ou é bem longo
            
            janelas.append({
                "start": start,
                "end": end,
                "text": texto_final
            })

        i = max(j, i + 1)

    return janelas

def selecionar_trechos_significativos(
    texto_transcrito: str,
    segments,
    idioma="pt",
    tempo_min=15.0,
    tempo_max=50.0,
    tema: str | None = None,
    max_resultados=6,
    usar_modelo_lg=True,
    rede_social='instagram'
):
    """
    Retorna trechos coerentes, ranqueados por múltiplos critérios otimizados para redes sociais.
    Se 'tema' for None ou string vazia, funciona em modo automático (sem tema).
    """
    nlp = carregar_nlp(idioma, usar_modelo_lg)
    tema_doc = nlp(tema) if (tema and tema.strip()) else None

    # Usa configurações específicas para a rede social
    config, _ = get_config_por_rede_social(rede_social)
    
    # Ajusta parâmetros baseado na configuração
    tempo_min_ajustado = max(tempo_min, config['minima'])
    tempo_max_ajustado = min(tempo_max, config['maxima'])
    pausa_ajustada = config['pausa_maxima']

    # Cria janelas mais inteligentes
    janelas = juntar_em_janelas(segments, tempo_min_ajustado, tempo_max_ajustado, pausa=pausa_ajustada)
    
    if DEBUG['mostrar_detalhes']:
        print(f"🔍 Analisando {len(janelas)} janelas de texto para {rede_social}...")
        print(f"⚙️ Configuração: {tempo_min_ajustado}-{tempo_max_ajustado}s, pausa max: {pausa_ajustada}s")

    candidatos = []
    for i, jn in enumerate(janelas):
        # Encontra índices dos segmentos originais para análise temporal
        indice_inicio = None
        indice_fim = None
        
        # Busca os segmentos originais que correspondem a esta janela
        for j, seg in enumerate(segments):
            if abs(seg_start(seg) - jn["start"]) < 0.1:
                indice_inicio = j
            if abs(seg_end(seg) - jn["end"]) < 0.1:
                indice_fim = j
                break
        
        # Calcula score completo
        resultado_score = calcular_score_completo(
            jn["text"], nlp, idioma, tema_doc, 
            segments, indice_inicio, indice_fim, rede_social
        )
        
        # Aplica filtros
        duracao = jn["end"] - jn["start"]
        palavras = len(jn["text"].split())
        
        # Filtra por critérios mínimos
        if (resultado_score["score"] < FILTROS['score_minimo'] or
            palavras < FILTROS['palavras_minimas'] or
            duracao < FILTROS['duracao_minima_absoluta']):
            continue
        
        # Adiciona informações extras
        candidato = {
            **jn,
            "score": resultado_score["score"],
            "detalhes_score": resultado_score["detalhes"],
            "duracao": duracao,
            "palavras": palavras
        }
        
        candidatos.append(candidato)
        
        # Log detalhado para debug
        if DEBUG['mostrar_detalhes'] and i < DEBUG['mostrar_candidatos']:
            print(f"📊 Janela {i+1}: Score {candidato['score']:.3f} | "
                  f"Engajamento: {candidato['detalhes_score']['engajamento']:.3f} | "
                  f"Visual: {candidato['detalhes_score']['visual']:.3f} | "
                  f"Texto: '{jn['text'][:60]}...'")

    # Ordena por score
    candidatos.sort(key=lambda x: x["score"], reverse=True)
    
    if DEBUG['mostrar_detalhes']:
        scores_texto = [f'{c["score"]:.3f}' for c in candidatos[:3]]
        print(f"📈 Melhores scores: {scores_texto}")

    # Seleciona candidatos únicos (evita repetições)
    escolhidos = []
    for c in candidatos:
        # Verifica similaridade com candidatos já escolhidos
        similar = False
        for escolhido in escolhidos:
            if similaridade(c["text"], escolhido["text"]) > FILTROS['similaridade_maxima']:
                similar = True
                break
        
        if not similar:
            escolhidos.append(c)
            if DEBUG['mostrar_detalhes']:
                print(f"✅ Selecionado: Score {c['score']:.3f} | "
                      f"'{c['text'][:50]}...'")
        
        if len(escolhidos) >= max_resultados:
            break

    if DEBUG['mostrar_detalhes']:
        print(f"🎯 Total de trechos selecionados: {len(escolhidos)}")
    
    # Remove detalhes_score do resultado final para compatibilidade
    for escolhido in escolhidos:
        escolhido.pop('detalhes_score', None)
        escolhido.pop('palavras', None)
    
    return escolhidos
