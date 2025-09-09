# frases/config_selecao.py
# Configurações para o sistema de seleção de trechos otimizado para redes sociais

# Configurações de duração (em segundos)
DURACAO = {
    'minima': 15.0,      # Duração mínima de um corte
    'maxima': 60.0,      # Duração máxima de um corte
    'ideal_min': 20.0,   # Duração ideal mínima
    'ideal_max': 45.0,   # Duração ideal máxima
    'pausa_maxima': 0.7, # Pausa máxima entre segmentos para juntar
}

# Pesos para cálculo de score (soma deve ser 1.0)
PESOS_SCORE = {
    'completude': 0.20,        # Estrutura sintática e coesão
    'engajamento': 0.25,       # Palavras-chave de alto engajamento
    'densidade': 0.15,         # Densidade de informação
    'narrativa': 0.10,         # Estrutura narrativa
    'visual': 0.15,            # Impacto visual para redes sociais
    'similaridade_tema': 0.10, # Similaridade com tema (quando especificado)
    'coerencia_temporal': 0.05 # Coerência temporal entre segmentos
}

# Configurações de filtros
FILTROS = {
    'palavras_minimas': 5,           # Mínimo de palavras por trecho
    'similaridade_maxima': 0.85,     # Similaridade máxima entre trechos selecionados
    'score_minimo': 0.3,            # Score mínimo para considerar um trecho
    'duracao_minima_absoluta': 10.0, # Duração mínima absoluta (mesmo com score alto)
}

# Configurações para redes sociais
REDES_SOCIAIS = {
    'instagram': {
        'duracao_ideal': (15, 30),
        'peso_visual': 0.25,
        'peso_engajamento': 0.30,
        'preferir_curtos': True
    },
    'tiktok': {
        'duracao_ideal': (15, 60),
        'peso_visual': 0.20,
        'peso_engajamento': 0.35,
        'preferir_curtos': True
    },
    'youtube': {
        'duracao_ideal': (30, 60),
        'peso_visual': 0.10,
        'peso_engajamento': 0.20,
        'preferir_curtos': False
    },
    'facebook': {
        'duracao_ideal': (20, 45),
        'peso_visual': 0.15,
        'peso_engajamento': 0.25,
        'preferir_curtos': False
    }
}

# Palavras-chave adicionais por categoria (podem ser expandidas)
PALAVRAS_EXTRAS = {
    'pt': {
        'viral': ['viral', 'trending', 'bombou', 'explodiu', 'surgiu', 'apareceu'],
        'numeros': ['primeiro', 'segundo', 'terceiro', 'último', 'melhor', 'pior'],
        'tempo': ['agora', 'hoje', 'ontem', 'amanhã', 'sempre', 'nunca', 'jamais'],
        'quantidade': ['todos', 'ninguém', 'alguns', 'muitos', 'poucos', 'vários']
    },
    'en': {
        'viral': ['viral', 'trending', 'exploded', 'blew up', 'surged', 'appeared'],
        'numeros': ['first', 'second', 'third', 'last', 'best', 'worst'],
        'tempo': ['now', 'today', 'yesterday', 'tomorrow', 'always', 'never'],
        'quantidade': ['all', 'none', 'some', 'many', 'few', 'several']
    }
}

# Configurações de debug
DEBUG = {
    'mostrar_detalhes': True,        # Mostra detalhes dos scores
    'mostrar_candidatos': 5,         # Quantos candidatos mostrar no debug
    'salvar_analise': False,         # Salva análise detalhada em arquivo
    'arquivo_analise': 'analise_trechos.json'
}

def get_config_por_rede_social(rede_social='instagram'):
    """Retorna configuração otimizada para uma rede social específica."""
    config = DURACAO.copy()
    pesos = PESOS_SCORE.copy()
    
    if rede_social in REDES_SOCIAIS:
        rede_config = REDES_SOCIAIS[rede_social]
        config['ideal_min'] = rede_config['duracao_ideal'][0]
        config['ideal_max'] = rede_config['duracao_ideal'][1]
        
        # Ajusta pesos
        pesos['visual'] = rede_config['peso_visual']
        pesos['engajamento'] = rede_config['peso_engajamento']
        
        # Redistribui pesos restantes
        peso_restante = 1.0 - pesos['visual'] - pesos['engajamento']
        outros_pesos = sum(p for k, p in pesos.items() if k not in ['visual', 'engajamento'])
        fator = peso_restante / outros_pesos if outros_pesos > 0 else 1.0
        
        for k in pesos:
            if k not in ['visual', 'engajamento']:
                pesos[k] *= fator
    
    return config, pesos
