#!/usr/bin/env python3
"""
Teste específico para verificar a qualidade da clonagem de voz
"""
import os
import torch
from pathlib import Path

def verificar_cuda():
    print("🔍 VERIFICAÇÃO DE CUDA")
    print("=" * 30)
    print(f"CUDA disponível: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Dispositivo: {torch.cuda.get_device_name(0)}")
        print(f"Memória: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    return torch.cuda.is_available()

def testar_xtts_import():
    print("\n🔍 TESTE DE IMPORTAÇÃO XTTS")
    print("=" * 30)
    try:
        from TTS.api import TTS
        print("✅ TTS importado com sucesso")
        
        if torch.cuda.is_available():
            print("🚀 Inicializando XTTS com GPU...")
            tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
            print("✅ XTTS inicializado com GPU")
        else:
            print("⚠️ Inicializando XTTS com CPU...")
            tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
            print("✅ XTTS inicializado com CPU")
        
        return tts
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        return None

def testar_clonagem_simples(tts):
    print("\n🔍 TESTE DE CLONAGEM SIMPLES")
    print("=" * 30)
    
    # Verificar arquivos de voz
    voice_files = [
        Path("voice_refs/minha_voz.wav"),
        Path("voice_refs/paulo_links_fixed.wav"),
        Path("voice_refs/paulo_links.wav")
    ]
    
    for voice_file in voice_files:
        if voice_file.exists():
            size = voice_file.stat().st_size
            print(f"📄 {voice_file.name}: {size} bytes")
        else:
            print(f"❌ {voice_file.name}: não encontrado")
    
    # Testar clonagem com cada arquivo
    test_text = "Olá, este é um teste de clonagem de voz do Paulo Links"
    
    for voice_file in voice_files:
        if voice_file.exists():
            print(f"\n🎤 Testando com: {voice_file.name}")
            try:
                output_file = f"teste_clone_{voice_file.stem}.wav"
                tts.tts_to_file(
                    text=test_text,
                    file_path=output_file,
                    speaker_wav=str(voice_file),
                    language="pt"
                )
                print(f"✅ Clonagem concluída: {output_file}")
                
                # Verificar tamanho do arquivo gerado
                if os.path.exists(output_file):
                    size = os.path.getsize(output_file)
                    print(f"📊 Tamanho do áudio gerado: {size} bytes")
                
            except Exception as e:
                print(f"❌ Erro na clonagem: {e}")

def main():
    print("🎯 TESTE DE CLONAGEM DE VOZ")
    print("=" * 50)
    
    # Verificar CUDA
    cuda_ok = verificar_cuda()
    
    # Testar importação XTTS
    tts = testar_xtts_import()
    
    if tts is not None:
        # Testar clonagem
        testar_clonagem_simples(tts)
    else:
        print("❌ Não foi possível inicializar XTTS")

if __name__ == "__main__":
    main()
