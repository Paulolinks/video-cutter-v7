#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementação de clonagem de voz REAL usando Tortoise TTS
"""

import os
import sys
import subprocess
import json

def instalar_tortoise_tts():
    """Instala Tortoise TTS para clonagem real de voz"""
    print("🔧 Instalando Tortoise TTS para clonagem real...")
    
    try:
        # Instalar Tortoise TTS
        subprocess.run([sys.executable, "-m", "pip", "install", "tortoise-tts"], check=True)
        print("✅ Tortoise TTS instalado com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar Tortoise TTS: {e}")
        return False

def criar_clonagem_real():
    """Cria função de clonagem real usando Tortoise TTS"""
    
    codigo_clonagem = '''
def clonar_voz_real(texto, arquivo_voz_referencia, arquivo_saida):
    """Clona voz real usando Tortoise TTS"""
    try:
        from tortoise.api import TextToSpeech
        from tortoise.utils.audio import load_audio, load_voice
        
        print(f"🎤 Iniciando clonagem real da voz...")
        print(f"📝 Texto: {texto[:50]}...")
        print(f"🎵 Voz de referência: {arquivo_voz_referencia}")
        
        # Carregar modelo Tortoise TTS
        tts = TextToSpeech()
        
        # Carregar voz de referência
        voice_samples, conditioning_latents = load_voice(arquivo_voz_referencia)
        
        # Gerar áudio clonado
        gen = tts.tts_with_preset(
            texto,
            voice_samples=voice_samples,
            conditioning_latents=conditioning_latents,
            preset="fast"  # ou "high_quality" para melhor qualidade
        )
        
        # Salvar áudio
        import torchaudio
        torchaudio.save(arquivo_saida, gen.squeeze(0).cpu(), 24000)
        
        print(f"✅ Voz clonada com sucesso: {arquivo_saida}")
        return arquivo_saida
        
    except Exception as e:
        print(f"❌ Erro na clonagem real: {e}")
        return None
'''
    
    # Salvar função em arquivo
    with open("clonagem_real.py", "w", encoding="utf-8") as f:
        f.write(codigo_clonagem)
    
    print("✅ Função de clonagem real criada: clonagem_real.py")

def testar_clonagem_real():
    """Testa clonagem real"""
    print("🧪 TESTE: Clonagem Real da Voz")
    print("=" * 50)
    
    try:
        # Verificar se Tortoise TTS está instalado
        try:
            import tortoise
            print("✅ Tortoise TTS disponível")
        except ImportError:
            print("❌ Tortoise TTS não instalado")
            return False
        
        # Importar função de clonagem
        from clonagem_real import clonar_voz_real
        
        # Testar clonagem
        arquivo_voz = "temp_voice_cloning/user_voice_1757776341.wav"
        if not os.path.exists(arquivo_voz):
            print(f"❌ Arquivo de voz não encontrado: {arquivo_voz}")
            return False
        
        texto_teste = "Este é um teste de clonagem real da minha voz."
        arquivo_saida = "teste_clonagem_real.wav"
        
        resultado = clonar_voz_real(texto_teste, arquivo_voz, arquivo_saida)
        
        if resultado and os.path.exists(arquivo_saida):
            tamanho = os.path.getsize(arquivo_saida)
            print(f"✅ Clonagem real funcionando: {tamanho} bytes")
            
            # Limpar arquivo de teste
            try:
                os.unlink(arquivo_saida)
            except:
                pass
            
            return True
        else:
            print("❌ Clonagem real falhou")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 IMPLEMENTANDO CLONAGEM REAL DE VOZ")
    print("=" * 60)
    
    # 1. Instalar Tortoise TTS
    if not instalar_tortoise_tts():
        print("❌ Falha na instalação do Tortoise TTS")
        return False
    
    # 2. Criar função de clonagem
    criar_clonagem_real()
    
    # 3. Testar clonagem
    if testar_clonagem_real():
        print("\n🎉 CLONAGEM REAL IMPLEMENTADA COM SUCESSO!")
        print("✅ Agora sua voz será realmente clonada!")
        return True
    else:
        print("\n❌ FALHA NA IMPLEMENTAÇÃO DA CLONAGEM REAL")
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)
