#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG COMPLETO DA DUBLAGEM
Descobre exatamente por que está apenas copiando o vídeo
"""

import sys
import os
import json
import tempfile
import shutil
from moviepy.editor import VideoFileClip, AudioFileClip

def debug_dublagem_completo():
    """Debug completo da dublagem"""
    print("🔍 INICIANDO DEBUG COMPLETO DA DUBLAGEM")
    print("=" * 60)
    
    # 1. VERIFICAR ARQUIVOS DE ENTRADA
    print("\n📁 1. VERIFICANDO ARQUIVOS DE ENTRADA")
    print("-" * 40)
    
    # Encontrar vídeo legendado
    video_entrada = None
    for arquivo in os.listdir('static/final'):
        if arquivo.endswith('_legendado.mp4'):
            video_entrada = f'static/final/{arquivo}'
            break
    
    if not video_entrada:
        print("❌ Nenhum vídeo legendado encontrado!")
        return
    
    print(f"✅ Vídeo encontrado: {video_entrada}")
    
    # Verificar se existe
    if not os.path.exists(video_entrada):
        print(f"❌ Vídeo não existe: {video_entrada}")
        return
    
    tamanho_video = os.path.getsize(video_entrada)
    print(f"📊 Tamanho do vídeo: {tamanho_video} bytes")
    
    # 2. VERIFICAR VOZ CLONADA
    print("\n🎤 2. VERIFICANDO VOZ CLONADA")
    print("-" * 40)
    
    # Carregar vozes clonadas
    try:
        with open('vozes_clonadas.json', 'r', encoding='utf-8') as f:
            vozes = json.load(f)
        print(f"✅ Arquivo vozes_clonadas.json carregado")
        print(f"📊 Número de vozes: {len(vozes.get('vozes', []))}")
        
        # Procurar sua voz
        sua_voz = None
        for voz in vozes.get('vozes', []):
            if 'Minha Voz - Paulolinks' in voz.get('nome', ''):
                sua_voz = voz
                break
        
        if sua_voz:
            print(f"✅ Sua voz encontrada: {sua_voz['nome']}")
            print(f"📁 Arquivo: {sua_voz['arquivo']}")
            
            # Verificar se arquivo existe
            if os.path.exists(sua_voz['arquivo']):
                tamanho_voz = os.path.getsize(sua_voz['arquivo'])
                print(f"📊 Tamanho da voz: {tamanho_voz} bytes")
            else:
                print(f"❌ Arquivo de voz não existe: {sua_voz['arquivo']}")
        else:
            print("❌ Sua voz não encontrada!")
            
    except Exception as e:
        print(f"❌ Erro ao carregar vozes: {e}")
    
    # 3. VERIFICAR TRANSCRIÇÃO
    print("\n📝 3. VERIFICANDO TRANSCRIÇÃO")
    print("-" * 40)
    
    # Encontrar arquivo de transcrição
    nome_base = os.path.splitext(os.path.basename(video_entrada))[0].replace('_legendado', '')
    arquivo_transcricao = f'data/transcricoes_cortes/{nome_base}.txt'
    
    print(f"🔍 Procurando transcrição: {arquivo_transcricao}")
    
    if os.path.exists(arquivo_transcricao):
        print(f"✅ Arquivo de transcrição encontrado")
        
        # Ler conteúdo
        with open(arquivo_transcricao, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        print(f"📊 Tamanho do arquivo: {len(conteudo)} caracteres")
        
        # Verificar se tem dados do Whisper
        if 'TIMESTAMPS_DETALHADOS' in conteudo:
            print("✅ TIMESTAMPS_DETALHADOS encontrado")
            
            # Extrair timestamps
            import re
            match = re.search(r'TIMESTAMPS_DETALHADOS:\s*(\[.*?\])', conteudo, re.DOTALL)
            if match:
                timestamps_json = match.group(1)
                try:
                    timestamps = json.loads(timestamps_json)
                    print(f"📊 Número de timestamps: {len(timestamps)}")
                    
                    # Mostrar alguns timestamps
                    for i, ts in enumerate(timestamps[:3]):
                        print(f"  {i+1}: {ts.get('start', 0):.2f}s - {ts.get('end', 0):.2f}s: {ts.get('text', '')[:50]}...")
                    
                except Exception as e:
                    print(f"❌ Erro ao parsear timestamps: {e}")
            else:
                print("❌ TIMESTAMPS_DETALHADOS não encontrado no conteúdo")
        else:
            print("❌ TIMESTAMPS_DETALHADOS não encontrado")
    else:
        print(f"❌ Arquivo de transcrição não encontrado: {arquivo_transcricao}")
    
    # 4. TESTAR GERAÇÃO DE ÁUDIO
    print("\n🎵 4. TESTANDO GERAÇÃO DE ÁUDIO")
    print("-" * 40)
    
    try:
        # Importar função de geração de áudio
        sys.path.append('.')
        from app import gerar_audio_tts
        
        # Texto de teste
        texto_teste = "Este é um teste de geração de áudio com clonagem de voz."
        print(f"📝 Texto de teste: {texto_teste}")
        
        # Gerar áudio
        print("🔧 Gerando áudio...")
        audio_path = gerar_audio_tts(texto_teste, 'clonada_Minha Voz - Paulolinks', 'pt')
        
        if audio_path and os.path.exists(audio_path):
            tamanho_audio = os.path.getsize(audio_path)
            print(f"✅ Áudio gerado: {audio_path}")
            print(f"📊 Tamanho: {tamanho_audio} bytes")
            
            # Verificar se é diferente da voz original
            if sua_voz and os.path.exists(sua_voz['arquivo']):
                tamanho_original = os.path.getsize(sua_voz['arquivo'])
                if tamanho_audio != tamanho_original:
                    print("✅ Áudio é diferente da voz original (clonagem funcionando)")
                else:
                    print("⚠️ Áudio é igual à voz original (apenas cópia)")
            
            # Limpar arquivo temporário
            if os.path.exists(audio_path):
                os.remove(audio_path)
        else:
            print("❌ Falha na geração de áudio")
            
    except Exception as e:
        print(f"❌ Erro na geração de áudio: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. TESTAR DUBLAGEM COMPLETA
    print("\n🎬 5. TESTANDO DUBLAGEM COMPLETA")
    print("-" * 40)
    
    try:
        from app import dublar_video
        
        # Criar diretório de saída
        os.makedirs('data/cortes_dublado', exist_ok=True)
        
        # Arquivo de saída
        video_saida = 'data/cortes_dublado/debug_dublagem_completa.mp4'
        
        # Remover arquivo anterior se existir
        if os.path.exists(video_saida):
            os.remove(video_saida)
        
        print(f"🎬 Iniciando dublagem: {video_entrada} -> {video_saida}")
        
        # Dublar
        resultado = dublar_video(
            video_entrada,
            video_saida,
            "Este é um teste de dublagem com debug completo para descobrir por que está apenas copiando o vídeo.",
            'clonada_Minha Voz - Paulolinks',
            'pt'
        )
        
        if resultado and os.path.exists(resultado):
            tamanho_resultado = os.path.getsize(resultado)
            print(f"✅ Dublagem concluída: {resultado}")
            print(f"📊 Tamanho: {tamanho_resultado} bytes")
            
            # Comparar com vídeo original
            if tamanho_resultado == tamanho_video:
                print("⚠️ ATENÇÃO: Tamanho igual ao vídeo original (possível cópia)")
            else:
                print("✅ Tamanho diferente do vídeo original (dublagem real)")
        else:
            print("❌ Falha na dublagem")
            
    except Exception as e:
        print(f"❌ Erro na dublagem: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG COMPLETO FINALIZADO")

if __name__ == "__main__":
    debug_dublagem_completo()
