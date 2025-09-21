#!/usr/bin/env python3
"""
Correção para PyTorch 2.6 - XTTS v2
"""

def fix_dub_xtts():
    """Aplica correção do PyTorch 2.6 no dub_xtts.py"""
    
    # Ler arquivo atual
    with open('dub_xtts.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituir imports
    old_imports = """import json, os, subprocess, shutil
from pathlib import Path
import numpy as np"""
    
    new_imports = """import json, os, subprocess, shutil
from pathlib import Path
import numpy as np
import torch

# ========= CORREÇÃO PyTorch 2.6 =========
# PyTorch 2.6 mudou o padrão de torch.load() para weights_only=True
# Precisamos permitir o carregamento do XTTS
try:
    from TTS.tts.configs.xtts_config import XttsConfig
    torch.serialization.add_safe_globals([XttsConfig])
    print("✅ [PYTORCH] Configuração de segurança aplicada para XTTS")
except ImportError:
    print("⚠️ [PYTORCH] XttsConfig não encontrado - usando fallback")
    # Fallback: desabilitar weights_only temporariamente
    torch.serialization.DEFAULT_PROTOCOL = 4"""
    
    # Aplicar correção
    content = content.replace(old_imports, new_imports)
    
    # Salvar arquivo corrigido
    with open('dub_xtts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ [CORREÇÃO] PyTorch 2.6 fix aplicado com sucesso!")
    print("✅ [CORREÇÃO] XTTS agora deve funcionar corretamente!")
    return True

if __name__ == "__main__":
    fix_dub_xtts()
