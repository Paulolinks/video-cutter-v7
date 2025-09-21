#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir problemas na função gerar_audio_tts
"""

import re

def corrigir_gerar_audio_tts():
    """Corrige todos os problemas na função gerar_audio_tts"""
    
    print("🔧 Iniciando correção da função gerar_audio_tts...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup do arquivo original
    with open('app_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Backup criado: app_backup.py")
    
    # Correção 1: Fixar indentação da linha 2165
    print("🔧 Correção 1: Fixando indentação...")
    content = re.sub(
        r'        # Criar arquivo temporário para áudio\n            with tempfile\.NamedTemporaryFile\(suffix="\.wav", delete=False\) as temp_file:\n            audio_path = temp_file\.name',
        '        # Criar arquivo temporário para áudio\n        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:\n            audio_path = temp_file.name',
        content
    )
    
    # Correção 2: Fixar break fora do loop na linha 2195
    print("🔧 Correção 2: Fixando break fora do loop...")
    content = re.sub(
        r'                    for voice in voices:\n                        if any\(\'pt\' in lang\.lower\(\) or \'portuguese\' in lang\.lower\(\) for lang in voice\.languages\):\n                            voz_selecionada = voice\n                            print\(f"✅ Voz em português encontrada: \{voice\.name\}"\)\n                    break',
        '                    for voice in voices:\n                        if any(\'pt\' in lang.lower() or \'portuguese\' in lang.lower() for lang in voice.languages):\n                            voz_selecionada = voice\n                            print(f"✅ Voz em português encontrada: {voice.name}")\n                            break',
        content
    )
    
    # Correção 3: Fixar except fora do bloco try na linha 2219
    print("🔧 Correção 3: Fixando estrutura except...")
    content = re.sub(
        r'                    else:\n                        print\("❌ pyttsx3 falhou, tentando Edge TTS\.\.\."\)\n        \n    except Exception as e:\n                    print\(f"Erro com pyttsx3: \{e\}, tentando PowerShell\.\.\."\)',
        '                    else:\n                        print("❌ pyttsx3 falhou, tentando Edge TTS...")\n        \n                except Exception as e:\n                    print(f"Erro com pyttsx3: {e}, tentando PowerShell...")',
        content
    )
    
    # Correção 4: Fixar return fora do bloco if na linha 2338
    print("🔧 Correção 4: Fixando return mal posicionado...")
    content = re.sub(
        r'            if os\.path\.exists\(audio_path\) and os\.path\.getsize\(audio_path\) > 0:\n                print\(f"✅ Áudio pyttsx3 gerado: \{audio_path\}"\)\n            return audio_path',
        '            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:\n                print(f"✅ Áudio pyttsx3 gerado: {audio_path}")\n                return audio_path',
        content
    )
    
    # Correção 5: Remover return duplicado nas linhas 2363 e 2367
    print("🔧 Correção 5: Removendo return duplicado...")
    content = re.sub(
        r'                wav_file\.writeframes\(silence\.tobytes\(\)\)\n                return audio_path\n            print\(f"✅ Áudio silencioso criado: \{audio_path\}"\)\n\n            \n            return audio_path',
        '                wav_file.writeframes(silence.tobytes())\n            print(f"✅ Áudio silencioso criado: {audio_path}")\n            return audio_path',
        content
    )
    
    # Salvar arquivo corrigido
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Função gerar_audio_tts corrigida com sucesso!")
    print("📁 Backup salvo em: app_backup.py")
    print("🔄 Arquivo app.py atualizado")

if __name__ == "__main__":
    corrigir_gerar_audio_tts()
