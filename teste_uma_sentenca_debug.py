#!/usr/bin/env python3
"""
Teste de debug para uma única sentença com debug de voz
"""
import os
import json
from pathlib import Path
from dub_xtts import dublar_corte_xtts

def testar_uma_sentenca_com_debug():
    print("🔍 TESTE DE DEBUG - UMA SENTENÇA COM VOZ")
    print("=" * 50)
    
    try:
        # Testar dublagem de uma sentença
        result = dublar_corte_xtts(
            cut_id="corte_1",
            prefer_lang="pt",
            base_data_dir="data",
            outputs_dir="outputs"
        )
        
        print(f"\n✅ Resultado: {result}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_uma_sentenca_com_debug()
