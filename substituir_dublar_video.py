#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para substituir a função dublar_video problemática pela versão corrigida
"""

import re

def substituir_funcao_dublar_video():
    """Substitui a função dublar_video problemática pela versão corrigida"""
    
    print("🔧 Substituindo função dublar_video...")
    
    # Ler a função corrigida
    with open('funcao_dublar_video_corrigida.py', 'r', encoding='utf-8') as f:
        funcao_corrigida = f.read()
    
    # Ler o arquivo app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup do arquivo original
    with open('app_backup5.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Backup criado: app_backup5.py")
    
    # Encontrar o início da função dublar_video
    inicio_funcao = content.find('def dublar_video(video_entrada, video_saida, texto_traduzido, voice, lang_target):')
    if inicio_funcao == -1:
        print("❌ Função dublar_video não encontrada!")
        return False
    
    # Encontrar o final da função (próxima função ou final do arquivo)
    linhas = content.split('\n')
    inicio_linha = content[:inicio_funcao].count('\n')
    
    # Procurar pela próxima função (linha que começa com 'def ' e não está indentada)
    fim_linha = inicio_linha
    for i in range(inicio_linha + 1, len(linhas)):
        linha = linhas[i].strip()
        if linha.startswith('def ') and not linha.startswith('    def '):
            fim_linha = i
            break
    else:
        # Se não encontrou próxima função, usar o final do arquivo
        fim_linha = len(linhas)
    
    # Reconstruir o arquivo
    linhas_antes = linhas[:inicio_linha]
    linhas_depois = linhas[fim_linha:]
    
    # Adicionar a função corrigida
    linhas_corrigidas = linhas_antes + [funcao_corrigida] + linhas_depois
    
    # Salvar arquivo corrigido
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas_corrigidas))
    
    print("✅ Função dublar_video substituída com sucesso!")
    print("📁 Backup salvo em: app_backup5.py")
    print("🔄 Arquivo app.py atualizado")
    
    return True

if __name__ == "__main__":
    substituir_funcao_dublar_video()
