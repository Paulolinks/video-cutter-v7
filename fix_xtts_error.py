#!/usr/bin/env python3
"""
Correção do erro XTTS v2 - remove parâmetros não suportados
"""

def fix_xtts_error():
    # Ler arquivo
    with open('dub_xtts.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituir a função problemática
    old_code = '''        xtts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker_wav=str(optimized_voice),
            language=language,
            # Parâmetros adicionais para melhor qualidade
            split_sentences=False,  # Não quebrar sentenças para manter naturalidade
            use_speaker_embedding=True  # Usar embedding do speaker para melhor clonagem
        )'''
    
    new_code = '''        xtts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker_wav=str(optimized_voice),
            language=language
        )'''
    
    # Fazer a substituição
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Parâmetros não suportados removidos")
    else:
        print("⚠️ Código não encontrado - pode já estar corrigido")
    
    # Salvar arquivo
    with open('dub_xtts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Correção aplicada no dub_xtts.py")
    print("🎤 Agora teste a dublagem novamente!")

if __name__ == "__main__":
    fix_xtts_error()
