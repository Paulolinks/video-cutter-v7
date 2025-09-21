#!/usr/bin/env python3
"""
Correção para PyTorch 2.6 - XTTS v2 (Versão 2)
"""

def fix_dub_xtts_v2():
    """Aplica correção do PyTorch 2.6 no dub_xtts.py (versão corrigida)"""
    
    # Ler arquivo atual
    with open('dub_xtts.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituir a seção problemática
    old_section = """# ========= CORREÇÃO PyTorch 2.6 =========
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
    
    new_section = """# ========= CORREÇÃO PyTorch 2.6 =========
# PyTorch 2.6 mudou o padrão de torch.load() para weights_only=True
# Solução: monkey patch do torch.load para desabilitar weights_only temporariamente
import functools

# Salvar o torch.load original
_original_torch_load = torch.load

@functools.wraps(_original_torch_load)
def _patched_torch_load(*args, **kwargs):
    # Forçar weights_only=False para XTTS
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

# Aplicar o patch
torch.load = _patched_torch_load
print("✅ [PYTORCH] Patch aplicado - weights_only=False para XTTS")"""
    
    # Aplicar correção
    content = content.replace(old_section, new_section)
    
    # Salvar arquivo corrigido
    with open('dub_xtts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ [CORREÇÃO] PyTorch 2.6 fix v2 aplicado com sucesso!")
    print("✅ [CORREÇÃO] XTTS agora deve funcionar corretamente!")
    return True

if __name__ == "__main__":
    fix_dub_xtts_v2()
