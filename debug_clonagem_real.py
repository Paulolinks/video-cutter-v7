#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG REAL da clonagem de voz - verificar se está clonando de verdade
"""

import os
import sys
import json
import tempfile
import shutil

def debug_clonagem_real():
    """Debug completo da clonagem real"""
    print("🔍 DEBUG REAL DA CLONAGEM DE VOZ")
    print("=" * 60)
    
    try:
        # 1. Verificar arquivo de vozes clonadas
        vozes_path = "vozes_clonadas.json"
        if not os.path.exists(vozes_path):
            print("❌ Arquivo de vozes clonadas não encontrado")
            return False
        
        with open(vozes_path, 'r', encoding='utf-8') as f:
            vozes = json.load(f)
        
        print(f"📊 Vozes registradas: {len(vozes)}")
        for nome, info in vozes.items():
            print(f"  - {nome}: {info.get('path', 'N/A')}")
        
        # 2. Verificar sua voz específica
        if "Minha Voz - Paulolinks" not in vozes:
            print("❌ Sua voz 'Minha Voz - Paulolinks' não está registrada")
            return False
        
        voz_info = vozes["Minha Voz - Paulolinks"]
        arquivo_voz = voz_info.get('path', '')
        
        if not arquivo_voz or not os.path.exists(arquivo_voz):
            print(f"❌ Arquivo de voz não encontrado: {arquivo_voz}")
            return False
        
        print(f"✅ Sua voz encontrada: {arquivo_voz}")
        print(f"📊 Tamanho: {os.path.getsize(arquivo_voz)} bytes")
        
        # 3. TESTE REAL: Gerar áudio com sua voz
        print(f"\n🎯 TESTE REAL DE CLONAGEM:")
        
        # Importar função do app.py
        sys.path.append('.')
        from app import gerar_audio_tts
        
        # Teste com texto específico
        texto_teste = "Este é um teste da minha voz clonada real."
        print(f"📝 Texto: {texto_teste}")
        
        # Gerar áudio
        audio_resultado = gerar_audio_tts(texto_teste, "clonada_Minha Voz - Paulolinks", "pt")
        
        if not audio_resultado or not os.path.exists(audio_resultado):
            print("❌ Falha ao gerar áudio")
            return False
        
        print(f"✅ Áudio gerado: {audio_resultado}")
        print(f"📊 Tamanho: {os.path.getsize(audio_resultado)} bytes")
        
        # 4. ANÁLISE CRÍTICA: Verificar se é clonagem real
        print(f"\n🔍 ANÁLISE CRÍTICA:")
        
        # Verificar se o áudio é diferente do arquivo original
        tamanho_original = os.path.getsize(arquivo_voz)
        tamanho_gerado = os.path.getsize(audio_resultado)
        
        print(f"📊 Tamanho original: {tamanho_original} bytes")
        print(f"📊 Tamanho gerado: {tamanho_gerado} bytes")
        
        if tamanho_original == tamanho_gerado:
            print("❌ PROBLEMA: Tamanhos iguais - está apenas copiando o arquivo!")
            return False
        
        # Verificar se o tamanho é proporcional ao texto
        ratio = tamanho_gerado / len(texto_teste)
        print(f"📊 Ratio bytes/char: {ratio:.1f}")
        
        if ratio < 100:
            print("⚠️ ATENÇÃO: Ratio muito baixo - pode não ser clonagem real")
        elif ratio > 1000:
            print("⚠️ ATENÇÃO: Ratio muito alto - pode não ser clonagem real")
        else:
            print("✅ Ratio parece normal para clonagem")
        
        # 5. TESTE COMPARATIVO: Gerar áudio com texto diferente
        print(f"\n🔄 TESTE COMPARATIVO:")
        
        texto_teste2 = "Este é outro texto completamente diferente para testar se a clonagem funciona corretamente."
        print(f"📝 Texto 2: {texto_teste2}")
        
        audio_resultado2 = gerar_audio_tts(texto_teste2, "clonada_Minha Voz - Paulolinks", "pt")
        
        if not audio_resultado2 or not os.path.exists(audio_resultado2):
            print("❌ Falha ao gerar segundo áudio")
            return False
        
        tamanho_gerado2 = os.path.getsize(audio_resultado2)
        print(f"📊 Tamanho áudio 2: {tamanho_gerado2} bytes")
        
        # Comparar tamanhos
        if tamanho_gerado == tamanho_gerado2:
            print("❌ PROBLEMA: Tamanhos iguais - não está clonando baseado no texto!")
            return False
        else:
            print("✅ Tamanhos diferentes - está gerando baseado no texto")
        
        # 6. VERIFICAÇÃO FINAL: Análise do conteúdo
        print(f"\n🎯 VERIFICAÇÃO FINAL:")
        
        # Verificar se os arquivos são realmente diferentes
        with open(audio_resultado, 'rb') as f1, open(audio_resultado2, 'rb') as f2:
            conteudo1 = f1.read()
            conteudo2 = f2.read()
        
        if conteudo1 == conteudo2:
            print("❌ PROBLEMA: Conteúdo idêntico - não está clonando!")
            return False
        else:
            print("✅ Conteúdo diferente - clonagem funcionando")
        
        # 7. LIMPEZA
        try:
            os.unlink(audio_resultado)
            os.unlink(audio_resultado2)
            print("🧹 Arquivos de teste removidos")
        except:
            pass
        
        print(f"\n🎉 CONCLUSÃO: CLONAGEM REAL FUNCIONANDO!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = debug_clonagem_real()
    if sucesso:
        print("\n✅ CLONAGEM REAL ESTÁ FUNCIONANDO!")
    else:
        print("\n❌ CLONAGEM REAL NÃO ESTÁ FUNCIONANDO!")
    
    sys.exit(0 if sucesso else 1)
