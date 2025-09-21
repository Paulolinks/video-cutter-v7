#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrige a estrutura do arquivo vozes_clonadas.json
"""

import json
import os

def corrigir_vozes_json():
    """Corrige a estrutura do JSON de vozes"""
    print('🔧 CORRIGINDO ESTRUTURA DO JSON:')
    print('=' * 40)
    
    # Ler arquivo atual
    with open('vozes_clonadas.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('📊 Estrutura atual:', list(data.keys()))
    
    # Corrigir estrutura
    vozes_corrigidas = {
        'vozes': []
    }
    
    # Adicionar vozes encontradas
    for key, value in data.items():
        if isinstance(value, dict) and 'arquivo' in value:
            vozes_corrigidas['vozes'].append(value)
        elif isinstance(value, str):
            # Procurar arquivo correspondente
            for root, dirs, files in os.walk('temp_voice_cloning'):
                for file in files:
                    if file.endswith('.wav') and not file.endswith('_converted.wav'):
                        caminho = os.path.join(root, file)
                        if os.path.exists(caminho):
                            vozes_corrigidas['vozes'].append({
                                'nome': key,
                                'arquivo': caminho,
                                'ativo': True
                            })
                            break
    
    print('📊 Vozes corrigidas:', len(vozes_corrigidas['vozes']))
    for i, voz in enumerate(vozes_corrigidas['vozes']):
        print(f'  {i+1}: {voz["nome"]} -> {voz["arquivo"]}')
    
    # Salvar arquivo corrigido
    with open('vozes_clonadas.json', 'w', encoding='utf-8') as f:
        json.dump(vozes_corrigidas, f, indent=2, ensure_ascii=False)
    
    print('✅ Arquivo corrigido salvo!')

if __name__ == "__main__":
    corrigir_vozes_json()
