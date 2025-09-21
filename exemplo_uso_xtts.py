"""
Exemplo prático de uso do sistema de dublagem XTTS v2
"""
import os
from pathlib import Path

def exemplo_dublagem_completa():
    """
    Exemplo completo de como usar o sistema de dublagem XTTS v2
    """
    print("🎬 EXEMPLO DE USO - SISTEMA XTTS v2")
    print("=" * 50)
    
    # 1. Verificar se o sistema está disponível
    try:
        from dub_xtts import dublar_corte_xtts
        print("✅ Sistema XTTS v2 disponível")
    except ImportError as e:
        print(f"❌ Sistema XTTS v2 não disponível: {e}")
        return
    
    # 2. Verificar arquivos necessários
    print("\n📁 Verificando arquivos necessários...")
    
    # Verificar se existem cortes
    cortes_dir = Path("data/cortes")
    if not cortes_dir.exists():
        print("❌ Pasta data/cortes não encontrada")
        return
    
    cortes = list(cortes_dir.glob("*.mp4"))
    print(f"✅ Encontrados {len(cortes)} cortes de vídeo")
    
    # Verificar transcrições JSON
    json_dir = Path("data/transcricoes_cortes/json")
    if not json_dir.exists():
        print("❌ Pasta de transcrições JSON não encontrada")
        print("💡 Execute: python converter_transcricoes_xtts.py")
        return
    
    json_files = list(json_dir.glob("*.json"))
    print(f"✅ Encontrados {len(json_files)} arquivos de transcrição JSON")
    
    # Verificar arquivo de voz de referência
    voice_refs = [
        Path("voice_refs/minha_voz.wav"),
        Path("data/audio/audio.wav")
    ]
    
    voice_ref = None
    for ref in voice_refs:
        if ref.exists():
            voice_ref = ref
            break
    
    if not voice_ref:
        print("❌ Nenhum arquivo de voz de referência encontrado")
        print("💡 Coloque um arquivo WAV em voice_refs/minha_voz.wav")
        return
    
    print(f"✅ Arquivo de voz de referência: {voice_ref}")
    
    # 3. Exemplo de dublagem
    print("\n🎤 Exemplo de dublagem...")
    
    # Escolher um corte para dublar
    corte_exemplo = "corte_1"
    
    if not Path(f"data/cortes/{corte_exemplo}.mp4").exists():
        print(f"❌ Corte {corte_exemplo} não encontrado")
        return
    
    if not Path(f"data/transcricoes_cortes/json/{corte_exemplo}.json").exists():
        print(f"❌ Transcrição JSON para {corte_exemplo} não encontrada")
        return
    
    print(f"🎯 Dublando corte: {corte_exemplo}")
    
    try:
        # Executar dublagem
        result = dublar_corte_xtts(
            cut_id=corte_exemplo,
            prefer_lang="pt",  # Português
            base_data_dir="data",
            outputs_dir="outputs"
        )
        
        print("✅ Dublagem concluída com sucesso!")
        print(f"📊 Resultado: {result}")
        
        # Verificar arquivos gerados
        print("\n📁 Arquivos gerados:")
        for key, path in result.items():
            if key != "sentences":
                if Path(path).exists():
                    print(f"  ✅ {key}: {path}")
                else:
                    print(f"  ❌ {key}: {path} (não encontrado)")
        
        print(f"\n📈 Total de sentenças processadas: {result['sentences']}")
        
    except Exception as e:
        print(f"❌ Erro na dublagem: {e}")
        print("💡 Verifique se FFmpeg está instalado e no PATH")

def exemplo_api_usage():
    """
    Exemplo de como usar via API HTTP
    """
    print("\n🌐 EXEMPLO DE USO VIA API")
    print("=" * 30)
    
    print("Para usar via API, faça uma requisição POST para /dublar_xtts:")
    print()
    print("URL: http://localhost:5000/dublar_xtts")
    print("Method: POST")
    print("Content-Type: application/json")
    print()
    print("Body:")
    print('{')
    print('    "cut_id": "corte_1",')
    print('    "prefer_lang": "pt"')
    print('}')
    print()
    print("Resposta esperada:")
    print('{')
    print('    "success": true,')
    print('    "message": "Dublagem concluída com sucesso! 13 sentenças processadas.",')
    print('    "result": {')
    print('        "audio": "outputs/dublados/corte_1/corte_1_dub.wav",')
    print('        "video": "outputs/dublados/corte_1/corte_1_dub.mp4",')
    print('        "report": "outputs/dublados/corte_1/corte_1_align_report.json",')
    print('        "sentences": 13')
    print('    }')
    print('}')

def main():
    """
    Função principal do exemplo
    """
    exemplo_dublagem_completa()
    exemplo_api_usage()
    
    print("\n" + "=" * 50)
    print("🎉 EXEMPLO CONCLUÍDO!")
    print("💡 Para mais informações, consulte DUBLAGEM_XTTS_README.md")

if __name__ == "__main__":
    main()
