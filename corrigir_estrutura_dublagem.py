#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir estrutura da função dublar_video
"""

def corrigir_estrutura_dublagem():
    """Corrige estrutura da função dublar_video"""
    
    print("🔧 Corrigindo estrutura da função dublar_video...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('app_backup4.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Backup criado: app_backup4.py")
    
    # Encontrar e corrigir a função dublar_video problemática
    # Procurar pelo padrão problemático e substituir
    content = content.replace(
        '        video_final.close()\n        if os.path.exists(audio_temporario):\n            os.remove(audio_temporario)\n    else:\n            print("Erro ao gerar áudio TTS - copiando vídeo original")\n            # Fallback: copiar vídeo original\n            shutil.copy2(video_entrada, video_saida)\n        \n    except Exception as e:\n        print(f"Erro na dublagem: {e}")\n        # Fallback: copiar arquivo original\n        import shutil\n        shutil.copy2(video_entrada, video_saida)',
        '        video_final.close()\n        if os.path.exists(audio_temporario):\n            os.remove(audio_temporario)\n    else:\n        print("Erro ao gerar áudio TTS - copiando vídeo original")\n        # Fallback: copiar vídeo original\n        shutil.copy2(video_entrada, video_saida)\n        \nexcept Exception as e:\n    print(f"Erro na dublagem: {e}")\n    # Fallback: copiar arquivo original\n    import shutil\n    shutil.copy2(video_entrada, video_saida)'
    )
    
    # Salvar arquivo corrigido
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Estrutura da função dublar_video corrigida!")
    print("📁 Backup salvo em: app_backup4.py")
    print("🔄 Arquivo app.py atualizado")

if __name__ == "__main__":
    corrigir_estrutura_dublagem()
