#!/usr/bin/env python3
"""
Teste da voz corrigida
"""
import os
from pathlib import Path

def testar_dublagem_corrigida():
    """Testa a dublagem com as correções aplicadas"""
    
    print("🎤 Testando dublagem com correções de qualidade...")
    
    try:
        from dub_xtts import dublar_corte_xtts
        
        # Testar com um corte existente
        result = dublar_corte_xtts(
            cut_id="corte_1_legendado",
            prefer_lang="pt",
            base_data_dir="data",
            outputs_dir="outputs"
        )
        
        if result and "video" in result:
            print(f"✅ Dublagem concluída: {result['video']}")
            print("🎬 Teste a qualidade da voz no vídeo gerado!")
            return True
        else:
            print("❌ Dublagem falhou")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    testar_dublagem_corrigida()
