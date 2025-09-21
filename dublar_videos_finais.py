"""
Script para dublar vídeos da pasta data/final com clonagem de voz
e salvar em data/cortes_dublado
"""
import os
import shutil
from pathlib import Path
from dub_xtts import dublar_corte_xtts

def dublar_videos_finais():
    """
    Dubla todos os vídeos da pasta data/final e salva em data/cortes_dublado
    """
    print("🎬 INICIANDO DUBLAGEM DOS VÍDEOS FINAIS")
    print("=" * 50)
    
    # Verificar se a pasta de destino existe
    destino_dir = Path("data/cortes_dublado")
    destino_dir.mkdir(exist_ok=True)
    
    # Listar vídeos na pasta final
    final_dir = Path("data/final")
    if not final_dir.exists():
        print("❌ Pasta data/final não encontrada")
        return
    
    videos = list(final_dir.glob("*.mp4"))
    if not videos:
        print("❌ Nenhum vídeo encontrado em data/final")
        return
    
    print(f"📁 Encontrados {len(videos)} vídeos para dublar")
    
    # Verificar se existe arquivo de voz de referência
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
    
    print(f"🎤 Usando voz de referência: {voice_ref}")
    
    # Processar cada vídeo
    resultados = []
    
    for i, video_path in enumerate(videos, 1):
        print(f"\n🎬 PROCESSANDO VÍDEO {i}/{len(videos)}: {video_path.name}")
        
        # Extrair nome do corte (ex: corte_1_legendado.mp4 -> corte_1)
        nome_base = video_path.stem.replace("_legendado", "")
        print(f"   📝 Nome do corte: {nome_base}")
        
        # Verificar se existe transcrição JSON
        json_path = Path(f"data/transcricoes_cortes/json/{nome_base}.json")
        if not json_path.exists():
            print(f"   ❌ Transcrição JSON não encontrada: {json_path}")
            continue
        
        # Verificar se existe corte original
        corte_original = Path(f"data/cortes/{nome_base}.mp4")
        if not corte_original.exists():
            print(f"   ❌ Corte original não encontrado: {corte_original}")
            continue
        
        print(f"   ✅ Arquivos encontrados, iniciando dublagem...")
        
        try:
            # Executar dublagem
            result = dublar_corte_xtts(
                cut_id=nome_base,
                prefer_lang="pt",
                base_data_dir="data",
                outputs_dir="outputs"
            )
            
            print(f"   ✅ Dublagem concluída: {result['sentences']} sentenças")
            
            # Copiar vídeo dublado para pasta de destino
            video_dublado = Path(result['video'])
            if video_dublado.exists():
                destino_video = destino_dir / f"{nome_base}_dublado.mp4"
                shutil.copy2(video_dublado, destino_video)
                print(f"   📁 Salvo em: {destino_video}")
                
                resultados.append({
                    "video_original": str(video_path),
                    "video_dublado": str(destino_video),
                    "sentenças": result['sentences'],
                    "status": "sucesso"
                })
            else:
                print(f"   ❌ Vídeo dublado não foi gerado")
                resultados.append({
                    "video_original": str(video_path),
                    "status": "erro - vídeo não gerado"
                })
                
        except Exception as e:
            print(f"   ❌ Erro na dublagem: {e}")
            resultados.append({
                "video_original": str(video_path),
                "status": f"erro - {str(e)}"
            })
    
    # Resumo final
    print(f"\n" + "=" * 50)
    print(f"📊 RESUMO DA DUBLAGEM")
    print(f"=" * 50)
    
    sucessos = [r for r in resultados if r['status'] == 'sucesso']
    erros = [r for r in resultados if r['status'] != 'sucesso']
    
    print(f"✅ Sucessos: {len(sucessos)}")
    print(f"❌ Erros: {len(erros)}")
    
    if sucessos:
        print(f"\n🎉 VÍDEOS DUBLADOS COM SUCESSO:")
        for resultado in sucessos:
            print(f"   📹 {Path(resultado['video_dublado']).name} ({resultado['sentenças']} sentenças)")
    
    if erros:
        print(f"\n⚠️  VÍDEOS COM ERRO:")
        for resultado in erros:
            print(f"   ❌ {Path(resultado['video_original']).name}: {resultado['status']}")
    
    print(f"\n📁 Vídeos dublados salvos em: {destino_dir}")
    
    return resultados

if __name__ == "__main__":
    dublar_videos_finais()

