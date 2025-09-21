"""
Demonstração do sistema de dublagem sem XTTS (para mostrar a estrutura)
"""
import json
import subprocess
import shutil
from pathlib import Path

def demo_dublagem_simples(cut_id="corte_1"):
    """
    Demonstra a estrutura de dublagem sem usar XTTS
    """
    print(f"🎬 DEMONSTRAÇÃO DE DUBLAGEM - {cut_id}")
    print("=" * 50)
    
    # 1. Carregar transcrição JSON
    json_path = Path(f"data/transcricoes_cortes/json/{cut_id}.json")
    if not json_path.exists():
        print(f"❌ Arquivo de transcrição não encontrado: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sentences = data['sentences']
    print(f"✅ Carregadas {len(sentences)} sentenças")
    
    # 2. Mostrar estrutura das sentenças
    print("\n📝 ESTRUTURA DAS SENTENÇAS:")
    for i, sent in enumerate(sentences[:3]):  # Mostrar apenas as 3 primeiras
        print(f"\nSentença {i+1}:")
        print(f"  ⏱️  Tempo: {sent['start']:.1f}s - {sent['end']:.1f}s (duração: {sent['duration']:.1f}s)")
        print(f"  🇺🇸 Inglês: {sent['text_en']}")
        print(f"  🇧🇷 Português: {sent['text_pt']}")
    
    # 3. Simular processamento de dublagem
    print(f"\n🎤 SIMULANDO PROCESSAMENTO DE DUBLAGEM:")
    
    out_dir = Path(f"outputs/dublados/{cut_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Criar pasta de trabalho
    work_dir = out_dir / f"_work_{cut_id}"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()
    
    print(f"📁 Pasta de trabalho criada: {work_dir}")
    
    # Simular geração de áudio para cada sentença
    total_duration = 0
    for i, sent in enumerate(sentences):
        # Simular arquivo de áudio gerado
        raw_wav = work_dir / f"sent_{i:03d}_raw.wav"
        fit_wav = work_dir / f"sent_{i:03d}_fit.wav"
        
        # Criar arquivo vazio para demonstração
        raw_wav.touch()
        fit_wav.touch()
        
        # Calcular duração ajustada
        target_duration = sent['duration']
        total_duration += target_duration
        
        print(f"  ✅ Sentença {i+1:2d}: {target_duration:.1f}s - '{sent['text_pt'][:50]}...'")
        
        # Simular pausa entre sentenças
        if i < len(sentences) - 1:
            next_start = sentences[i+1]['start']
            current_end = sent['end']
            pause_duration = max(0, next_start - current_end)
            
            if pause_duration > 0.1:  # Só criar pausa se for significativa
                pause_wav = work_dir / f"pause_{i:03d}.wav"
                pause_wav.touch()
                print(f"    ⏸️  Pausa: {pause_duration:.1f}s")
                total_duration += pause_duration
    
    # 4. Simular concatenação final
    print(f"\n🔗 CONCATENANDO ÁUDIO FINAL:")
    
    # Lista de arquivos para concatenar
    audio_files = []
    for i in range(len(sentences)):
        audio_files.append(work_dir / f"sent_{i:03d}_fit.wav")
        
        # Adicionar pausa se existir
        pause_file = work_dir / f"pause_{i:03d}.wav"
        if pause_file.exists():
            audio_files.append(pause_file)
    
    print(f"  📄 {len(audio_files)} arquivos de áudio para concatenar")
    
    # 5. Simular mux com vídeo
    video_path = Path(f"data/cortes/{cut_id}.mp4")
    if video_path.exists():
        print(f"\n🎥 MUXANDO COM VÍDEO:")
        print(f"  📹 Vídeo: {video_path}")
        print(f"  🎵 Áudio: {len(audio_files)} segmentos")
        print(f"  ⏱️  Duração total: {total_duration:.1f}s")
        
        # Simular arquivos de saída
        out_audio = out_dir / f"{cut_id}_dub.wav"
        out_video = out_dir / f"{cut_id}_dub.mp4"
        out_report = out_dir / f"{cut_id}_align_report.json"
        
        out_audio.touch()
        out_video.touch()
        
        # Criar relatório de alinhamento
        report = []
        for i, sent in enumerate(sentences):
            report.append({
                "index": i,
                "text": sent['text_pt'],
                "target_sec": sent['duration'],
                "fit_dur_sec": sent['duration'],
                "ratio": 1.0,
                "start": sent['start'],
                "end": sent['end']
            })
        
        with open(out_report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ ARQUIVOS GERADOS:")
        print(f"  🎵 Áudio: {out_audio}")
        print(f"  🎬 Vídeo: {out_video}")
        print(f"  📊 Relatório: {out_report}")
        
        return {
            "audio": str(out_audio),
            "video": str(out_video),
            "report": str(out_report),
            "sentences": len(sentences),
            "total_duration": total_duration
        }
    else:
        print(f"❌ Vídeo não encontrado: {video_path}")
        return None

def main():
    """
    Executa a demonstração
    """
    print("🚀 DEMONSTRAÇÃO DO SISTEMA DE DUBLAGEM XTTS v2")
    print("=" * 60)
    print("📋 Esta demonstração mostra a estrutura completa do sistema")
    print("   sem executar o XTTS (devido a problemas de compatibilidade)")
    print("=" * 60)
    
    result = demo_dublagem_simples("corte_1")
    
    if result:
        print(f"\n🎉 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 Resultado: {result}")
        print(f"\n💡 Para usar com XTTS real, resolva o problema de compatibilidade do PyTorch")
    else:
        print(f"\n❌ Demonstração falhou")

if __name__ == "__main__":
    main()
