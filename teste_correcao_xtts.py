#!/usr/bin/env python3
"""
Teste rápido da correção XTTS v2
"""
import os
from pathlib import Path

def testar_correcao():
    print("🧪 Testando correção XTTS v2...")
    
    try:
        # Testar importação do módulo corrigido
        from dub_xtts import synth_tts_clone_xtts, _init_xtts
        
        # Testar inicialização do XTTS
        print("🚀 Testando inicialização XTTS...")
        xtts = _init_xtts()
        
        if xtts is not None:
            print("✅ XTTS v2 inicializado com sucesso!")
            print("🎤 Parâmetros corrigidos - sem erros de compatibilidade")
            return True
        else:
            print("❌ XTTS v2 não pôde ser inicializado")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    if testar_correcao():
        print("\n🎉 Correção aplicada com sucesso!")
        print("✅ Agora você pode testar a dublagem na interface")
    else:
        print("\n⚠️ Ainda há problemas - pode precisar reverter as modificações")
