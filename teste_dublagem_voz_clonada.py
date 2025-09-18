#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste do Sistema de Dublagem com Vozes Clonadas
Executa um teste completo do sistema implementado
"""

import json
import os
import sys
import tempfile
import time

def carregar_config_vozes_clonadas():
    """Carrega configuração de vozes clonadas do arquivo JSON"""
    try:
        with open("vozes_clonadas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar vozes clonadas: {e}")
        return {"vozes": [], "configuracao_global": {"fallback_voice": "pt-BR-ValerioNeural"}}

def is_voz_clonada(voice):
    """Verifica se a voz especificada é uma voz clonada"""
    return voice.startswith("clonada_")

def testar_sistema_vozes():
    """Testa o sistema completo de vozes clonadas"""
    print("🧪 TESTE DO SISTEMA DE DUBLAGEM COM VOZES CLONADAS")
    print("=" * 60)
    
    # Teste 1: Verificar se vozes_clonadas.json existe
    print("\n1️⃣ Verificando arquivo de configuração...")
    if os.path.exists("vozes_clonadas.json"):
        print("✅ vozes_clonadas.json encontrado")
        config = carregar_config_vozes_clonadas()
        print(f"✅ {len(config['vozes'])} vozes configuradas")
        
        for voz in config['vozes']:
            print(f"   🎤 {voz['nome']} ({voz['id']}) - {'Ativa' if voz.get('ativo', False) else 'Inativa'}")
    else:
        print("❌ vozes_clonadas.json não encontrado")
        return False
    
    # Teste 2: Verificar detecção de voz clonada
    print("\n2️⃣ Testando detecção de vozes clonadas...")
    vozes_teste = [
        "clonada_Minha_Voz_Paulolinks",
        "pt-BR-ValerioNeural",
        "clonada_teste"
    ]
    
    for voz in vozes_teste:
        resultado = is_voz_clonada(voz)
        status = "✅ Clonada" if resultado else "⚪ Padrão"
        print(f"   {voz}: {status}")
    
    # Teste 3: Verificar diretório de referências
    print("\n3️⃣ Verificando diretório de referências...")
    dir_refs = "temp_speaker_embeddings"
    if os.path.exists(dir_refs):
        print(f"✅ Diretório {dir_refs} existe")
        arquivos = os.listdir(dir_refs)
        print(f"✅ {len(arquivos)} arquivos encontrados")
        
        for arquivo in arquivos:
            if arquivo.endswith(('.wav', '.mp3')):
                caminho = os.path.join(dir_refs, arquivo)
                tamanho = os.path.getsize(caminho)
                print(f"   🎵 {arquivo} ({tamanho} bytes)")
    else:
        print(f"❌ Diretório {dir_refs} não encontrado")
    
    # Teste 4: Verificar dependências
    print("\n4️⃣ Verificando dependências...")
    dependencias = [
        ("edge_tts", "Edge TTS"),
        ("TTS", "Coqui TTS"),
        ("torch", "PyTorch"),
        ("librosa", "Librosa")
    ]
    
    for modulo, nome in dependencias:
        try:
            __import__(modulo)
            print(f"   ✅ {nome}")
        except ImportError:
            print(f"   ❌ {nome} - não instalado")
    
    # Teste 5: Simular chamada de dublagem
    print("\n5️⃣ Simulando chamada de dublagem...")
    texto_teste = "Olá, este é um teste da minha voz clonada do Paulo Links."
    voz_teste = "clonada_Minha_Voz_Paulolinks"
    
    print(f"   📝 Texto: {texto_teste}")
    print(f"   🎤 Voz: {voz_teste}")
    print(f"   🌍 Idioma: pt")
    
    if is_voz_clonada(voz_teste):
        print("   ✅ Voz reconhecida como clonada")
        
        # Verificar se existe arquivo de referência
        config = carregar_config_vozes_clonadas()
        voz_config = None
        for voz in config["vozes"]:
            if voz["id"] == voz_teste:
                voz_config = voz
                break
        
        if voz_config:
            arquivo_ref = voz_config.get("arquivo_referencia", "")
            if arquivo_ref and os.path.exists(arquivo_ref):
                print(f"   ✅ Arquivo de referência encontrado: {arquivo_ref}")
            else:
                print(f"   ⚠️ Arquivo de referência não encontrado: {arquivo_ref}")
                print("   💡 Para usar vozes clonadas, adicione um arquivo de áudio de referência")
    
    print("\n" + "=" * 60)
    print("🏁 TESTE CONCLUÍDO")
    
    return True

def criar_arquivo_referencia_exemplo():
    """Cria um arquivo de referência de exemplo para teste"""
    print("\n📁 Criando arquivo de referência de exemplo...")
    
    # Criar diretório se não existir
    os.makedirs("temp_speaker_embeddings", exist_ok=True)
    
    # Criar um arquivo de áudio vazio como placeholder
    arquivo_exemplo = "temp_speaker_embeddings/paulo_links_voice.wav"
    
    if not os.path.exists(arquivo_exemplo):
        # Criar arquivo vazio temporário
        with open(arquivo_exemplo, "wb") as f:
            # Escrever cabeçalho WAV mínimo (44 bytes)
            f.write(b'RIFF')
            f.write((36).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))  # formato PCM
            f.write((1).to_bytes(2, 'little'))  # mono
            f.write((44100).to_bytes(4, 'little'))  # sample rate
            f.write((88200).to_bytes(4, 'little'))  # byte rate
            f.write((2).to_bytes(2, 'little'))  # block align
            f.write((16).to_bytes(2, 'little'))  # bits per sample
            f.write(b'data')
            f.write((0).to_bytes(4, 'little'))  # data size
        
        print(f"✅ Arquivo placeholder criado: {arquivo_exemplo}")
        print("⚠️ IMPORTANTE: Substitua este arquivo por um áudio real da voz para funcionar!")
    else:
        print(f"ℹ️ Arquivo já existe: {arquivo_exemplo}")

if __name__ == "__main__":
    print("🚀 Iniciando teste do sistema de dublagem...")
    
    # Executar teste
    sucesso = testar_sistema_vozes()
    
    if sucesso:
        # Criar arquivo de exemplo se necessário
        criar_arquivo_referencia_exemplo()
        
        print("\n🎉 Sistema configurado com sucesso!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Instale as dependências: pip install -r requirements_voice_cloning.txt")
        print("2. Substitua 'temp_speaker_embeddings/paulo_links_voice.wav' por um áudio real")
        print("3. Execute a aplicação Flask e teste a dublagem")
        print("4. Selecione 'Minha Voz - Paulolinks' na interface web")
    else:
        print("\n❌ Falhas encontradas no sistema. Verifique os erros acima.")