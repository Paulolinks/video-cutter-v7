#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir problemas de indentação específicos
"""

def corrigir_indentacao():
    """Corrige problemas de indentação específicos"""
    
    print("🔧 Corrigindo problemas de indentação...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('app_backup3.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Backup criado: app_backup3.py")
    
    # Correção 1: Linhas 2137-2144 - Problema de indentação no bloco de limpeza
    content = content.replace(
        '        \n            # Limpar arquivos temporários\n        video.close()\n            novo_audio.close()\n            video_final.close()\n            if os.path.exists(audio_temporario):\n                os.remove(audio_temporario)\n        else:',
        '        \n        # Limpar arquivos temporários\n        video.close()\n        novo_audio.close()\n        video_final.close()\n        if os.path.exists(audio_temporario):\n            os.remove(audio_temporario)\n    else:'
    )
    
    # Correção 2: Linhas 2719-2728 - Problema de indentação no bloco de tradução
    content = content.replace(
        '                        if any(palavra in texto_para_dublagem.lower() for palavra in [\'the\', \'and\', \'you\', \'your\', \'this\', \'that\', \'with\', \'from\', \'they\', \'have\', \'will\', \'can\', \'are\', \'was\', \'were\']):\n                                print(f"🌍 Detectado texto em inglês, traduzindo para português...")\n                            texto_traduzido = GoogleTranslator(source=\'en\', target=\'pt\').translate(texto_para_dublagem)\n                            print(f"✅ Texto traduzido para português: {len(texto_traduzido)} chars")\n                            \n                            # Salvar tradução no arquivo individual\n                            atualizar_texto_traduzido(arquivo_nome, texto_traduzido)\n                            \n                            texto_para_dublagem = texto_traduzido\n                        else:\n                            print(f"📝 Texto já em português, usando diretamente")',
        '                        if any(palavra in texto_para_dublagem.lower() for palavra in [\'the\', \'and\', \'you\', \'your\', \'this\', \'that\', \'with\', \'from\', \'they\', \'have\', \'will\', \'can\', \'are\', \'was\', \'were\']):\n                            print(f"🌍 Detectado texto em inglês, traduzindo para português...")\n                            texto_traduzido = GoogleTranslator(source=\'en\', target=\'pt\').translate(texto_para_dublagem)\n                            print(f"✅ Texto traduzido para português: {len(texto_traduzido)} chars")\n                            \n                            # Salvar tradução no arquivo individual\n                            atualizar_texto_traduzido(arquivo_nome, texto_traduzido)\n                            \n                            texto_para_dublagem = texto_traduzido\n                        else:\n                            print(f"📝 Texto já em português, usando diretamente")'
    )
    
    # Salvar arquivo corrigido
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Problemas de indentação corrigidos!")
    print("📁 Backup salvo em: app_backup3.py")
    print("🔄 Arquivo app.py atualizado")

if __name__ == "__main__":
    corrigir_indentacao()
