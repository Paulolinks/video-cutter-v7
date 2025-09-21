"""
Dublagem simplificada usando XTTS sem FFmpeg
Gera apenas o áudio dublado com clonagem de voz
"""
import json
import os
import shutil
from pathlib import Path
from TTS.api import TTS

def dublagem_simples_xtts():
    """
    Dublagem simplificada que gera apenas áudio dublado
    """
    print("🎬 DUBLAGEM SIMPLIFICADA COM XTTS")
    print("=" * 50)
    
    # Inicializar XTTS
    try:
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
        print("✅ XTTS inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar XTTS: {e}")
        return
    
    # Verificar arquivo de voz de referência
    voice_ref = Path("voice_refs/minha_voz.wav")
    if not voice_ref.exists():
        print("❌ Arquivo de voz de referência não encontrado")
        return
    
    print(f"🎤 Usando voz de referência: {voice_ref}")
    
    # Pasta de destino
    destino_dir = Path("data/cortes_dublado")
    destino_dir.mkdir(exist_ok=True)
    
    # Processar cada corte
    for i in range(1, 7):  # corte_1 até corte_6
        corte_id = f"corte_{i}"
        print(f"\n🎬 PROCESSANDO {corte_id.upper()}")
        
        # Verificar se existe transcrição JSON
        json_path = Path(f"data/transcricoes_cortes/json/{corte_id}.json")
        if not json_path.exists():
            print(f"   ❌ Transcrição não encontrada: {json_path}")
            continue
        
        # Carregar transcrição
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sentences = data['sentences']
        print(f"   📝 {len(sentences)} sentenças encontradas")
        
        # Criar pasta de trabalho
        work_dir = destino_dir / f"{corte_id}_work"
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir()
        
        # Processar cada sentença
        audio_files = []
        total_duration = 0
        
        for j, sent in enumerate(sentences):
            text = sent['text_pt'] if sent['text_pt'] else sent['text_en']
            duration = sent['duration']
            
            print(f"   🎤 Sentença {j+1}: {text[:50]}...")
            
            # Gerar áudio com XTTS
            audio_file = work_dir / f"sent_{j:03d}.wav"
            
            try:
                tts.tts_to_file(
                    text=text,
                    file_path=str(audio_file),
                    speaker_wav=str(voice_ref),
                    language="pt"
                )
                
                # Verificar se o arquivo foi criado
                if audio_file.exists():
                    audio_files.append(audio_file)
                    total_duration += duration
                    print(f"      ✅ Gerado: {duration:.1f}s")
                else:
                    print(f"      ❌ Arquivo não criado")
                    
            except Exception as e:
                print(f"      ❌ Erro: {e}")
        
        # Concatenar áudios simples (sem FFmpeg)
        if audio_files:
            print(f"   🔗 Concatenando {len(audio_files)} arquivos de áudio...")
            
            # Criar arquivo de lista para concatenação
            list_file = work_dir / "concat_list.txt"
            with open(list_file, 'w', encoding='utf-8') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file.absolute()}'\n")
            
            # Arquivo final
            final_audio = destino_dir / f"{corte_id}_dublado.wav"
            
            # Tentar usar FFmpeg se disponível, senão copiar o primeiro arquivo
            try:
                import subprocess
                cmd = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                    "-i", str(list_file), "-c", "copy", str(final_audio)
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"   ✅ Áudio concatenado: {final_audio}")
            except:
                # Se FFmpeg não estiver disponível, copiar o primeiro arquivo
                shutil.copy2(audio_files[0], final_audio)
                print(f"   ⚠️  FFmpeg não disponível, copiado primeiro arquivo: {final_audio}")
            
            # Criar relatório
            report = {
                "corte_id": corte_id,
                "sentenças_processadas": len(audio_files),
                "duração_total": total_duration,
                "arquivos_gerados": [str(f) for f in audio_files],
                "arquivo_final": str(final_audio)
            }
            
            report_file = destino_dir / f"{corte_id}_relatorio.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"   📊 Relatório salvo: {report_file}")
        else:
            print(f"   ❌ Nenhum áudio foi gerado")
    
    print(f"\n🎉 DUBLAGEM CONCLUÍDA!")
    print(f"📁 Arquivos salvos em: {destino_dir}")
    
    # Listar arquivos gerados
    arquivos_gerados = list(destino_dir.glob("*_dublado.wav"))
    if arquivos_gerados:
        print(f"\n📄 ARQUIVOS DE ÁUDIO GERADOS:")
        for arquivo in arquivos_gerados:
            print(f"   🎵 {arquivo.name}")

if __name__ == "__main__":
    dublagem_simples_xtts()
