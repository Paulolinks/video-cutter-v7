#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMPLEMENTAÇÃO DA IDEIA SUPERIOR DO USUÁRIO
Salvar TODOS os dados do Whisper durante a legendagem para dublagem otimizada
"""

import re
import json
import os

def implementar_modificacoes():
    print("🚀 IMPLEMENTANDO SUA IDEIA SUPERIOR!")
    print("=" * 60)
    
    # 1. MODIFICAR cortes/cortar_video.py
    print("🔧 1. Modificando cortes/cortar_video.py...")
    
    with open("cortes/cortar_video.py", "r", encoding="utf-8") as f:
        conteudo_cortes = f.read()
    
    # Nova função salvar_transcricao_corte com dados completos
    nova_funcao_cortes = '''def salvar_transcricao_corte(nome_arquivo, texto, inicio, fim, segmentos_whisper=None):
    """Salva a transcrição COMPLETA com todos os dados necessários para dublagem"""
    try:
        # Criar pasta de transcrições dos cortes
        os.makedirs("data/transcricoes_cortes", exist_ok=True)
        
        # Nome do arquivo de transcrição (mesmo nome do vídeo, mas .txt)
        nome_base = os.path.splitext(nome_arquivo)[0]
        transcricao_path = os.path.join("data/transcricoes_cortes", f"{nome_base}.txt")
        
        # CORREÇÃO: Traduzir o texto automaticamente
        print(f"🌍 [TRADUÇÃO] Traduzindo texto para português...")
        try:
            from deep_translator import GoogleTranslator
            texto_traduzido = GoogleTranslator(source="auto", target="pt").translate(texto)
            print(f"✅ [TRADUÇÃO] Texto traduzido: {len(texto_traduzido)} chars")
        except Exception as e:
            print(f"⚠️ [TRADUÇÃO] Erro na tradução: {e} - usando texto original")
            texto_traduzido = texto
        
        # Se temos segmentos do Whisper, salvar dados completos
        if segmentos_whisper:
            print(f"💾 [DADOS COMPLETOS] Salvando timestamps e pausas do Whisper...")
            
            # Formatar timestamps detalhados
            timestamps_detalhados = []
            for i, seg in enumerate(segmentos_whisper):
                inicio_seg = seg.get("start", 0.0)
                fim_seg = seg.get("end", 0.0)
                texto_seg = seg.get("text", "").strip()
                
                timestamps_detalhados.append({
                    "indice": i + 1,
                    "inicio": round(inicio_seg, 2),
                    "fim": round(fim_seg, 2),
                    "duracao": round(fim_seg - inicio_seg, 2),
                    "texto": texto_seg
                })
            
            # Detectar pausas baseadas nos segmentos
            pausas_detectadas = []
            for i in range(len(segmentos_whisper) - 1):
                fim_atual = segmentos_whisper[i].get("end", 0.0)
                inicio_proximo = segmentos_whisper[i + 1].get("start", 0.0)
                duracao_pausa = inicio_proximo - fim_atual
                
                if duracao_pausa >= 0.3:  # Pausa > 0.3s
                    pausas_detectadas.append({
                        "indice": i + 1,
                        "inicio": round(fim_atual, 2),
                        "fim": round(inicio_proximo, 2),
                        "duracao": round(duracao_pausa, 2),
                        "tipo": "pausa_natural"
                    })
            
            # Formatar segmentos de legenda
            import re
            frases_traduzidas = re.split(r"[.!?]+", texto_traduzido)
            frases_traduzidas = [f.strip() for f in frases_traduzidas if f.strip()]
            
            segmentos_legenda = []
            for i, seg in enumerate(segmentos_whisper):
                inicio_seg = seg.get("start", 0.0)
                fim_seg = seg.get("end", 0.0)
                texto_original = seg.get("text", "").strip()
                texto_legenda = frases_traduzidas[i] if i < len(frases_traduzidas) else texto_original
                
                segmentos_legenda.append({
                    "indice": i + 1,
                    "inicio": round(inicio_seg, 2),
                    "fim": round(fim_seg, 2),
                    "duracao": round(fim_seg - inicio_seg, 2),
                    "texto_original": texto_original,
                    "texto_traduzido": texto_legenda
                })
            
            # Criar conteúdo COMPLETO
            conteudo = f"""TRANSCRIÇÃO DO CORTE: {nome_arquivo}
INÍCIO: {inicio:.2f}s
FIM: {fim:.2f}s
DURAÇÃO: {fim - inicio:.2f}s

TEXTO:
{texto}

TEXTO_TRADUZIDO:
{texto_traduzido}

TIMESTAMPS_DETALHADOS:
{json.dumps(timestamps_detalhados, indent=2, ensure_ascii=False)}

PAUSAS_DETECTADAS:
{json.dumps(pausas_detectadas, indent=2, ensure_ascii=False)}

SEGMENTOS_LEGENDA:
{json.dumps(segmentos_legenda, indent=2, ensure_ascii=False)}

METADADOS_DUBLAGEM:
- Timestamps extraídos do Whisper: {len(timestamps_detalhados)} segmentos
- Pausas detectadas: {len(pausas_detectadas)} pausas
- Segmentos de legenda: {len(segmentos_legenda)} segmentos
- Fonte dos dados: Whisper (mais preciso que FFmpeg)
- Status: Pronto para dublagem otimizada
"""
            print(f"📊 [DADOS COMPLETOS] Timestamps: {len(timestamps_detalhados)}, Pausas: {len(pausas_detectadas)}")
        else:
            # Fallback: salvar apenas texto básico
            conteudo = f"""TRANSCRIÇÃO DO CORTE: {nome_arquivo}
INÍCIO: {inicio:.2f}s
FIM: {fim:.2f}s
DURAÇÃO: {fim - inicio:.2f}s

TEXTO:
{texto}

TEXTO_TRADUZIDO:
{texto_traduzido}
"""
        
        # Salvar arquivo
        with open(transcricao_path, "w", encoding="utf-8") as f:
            f.write(conteudo)
        
        print(f"📝 Transcrição salva: {transcricao_path}")
        print(f"✅ Texto traduzido salvo automaticamente")
        
    except Exception as e:
        print(f"❌ Erro ao salvar transcrição do corte {nome_arquivo}: {e}")'''
    
    # Substituir a função no arquivo cortes
    conteudo_cortes_corrigido = re.sub(
        r"def salvar_transcricao_corte\(nome_arquivo, texto, inicio, fim\):.*?except Exception as e:\n        print\(f\"❌ Erro ao salvar transcrição do corte \{nome_arquivo\}: \{e\}\"\)",
        nova_funcao_cortes,
        conteudo_cortes,
        flags=re.DOTALL
    )
    
    # Salvar arquivo corrigido
    with open("cortes/cortar_video.py", "w", encoding="utf-8") as f:
        f.write(conteudo_cortes_corrigido)
    
    print("✅ 1. cortes/cortar_video.py modificado!")
    
    # 2. MODIFICAR main.py para passar segmentos do Whisper
    print("🔧 2. Modificando main.py...")
    
    with open("main.py", "r", encoding="utf-8") as f:
        conteudo_main = f.read()
    
    # Modificar a chamada da função legendar_cortes_por_segmento para passar segmentos
    conteudo_main_corrigido = conteudo_main.replace(
        "legendar_cortes_por_segmento(partes)",
        "legendar_cortes_por_segmento(partes, segmentos)"
    )
    
    # Salvar arquivo corrigido
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(conteudo_main_corrigido)
    
    print("✅ 2. main.py modificado!")
    
    # 3. MODIFICAR a função legendar_cortes_por_segmento
    print("🔧 3. Modificando função legendar_cortes_por_segmento...")
    
    # Nova função legendar_cortes_por_segmento
    nova_funcao_main = '''def legendar_cortes_por_segmento(partes, segmentos_whisper=None):
    import os
    import glob
    import re
    
    os.makedirs("data/final", exist_ok=True)
    
    # Obter os números dos cortes que foram criados
    def obter_numeros_cortes_criados():
        padrao = "data/cortes/corte_*.mp4"
        arquivos_existentes = glob.glob(padrao)
        numeros = []
        for arquivo in arquivos_existentes:
            nome = os.path.basename(arquivo)
            match = re.search(r'corte_(\d+)\.mp4', nome)
            if match:
                numeros.append(int(match.group(1)))
        return sorted(numeros)
    
    numeros_cortes = obter_numeros_cortes_criados()
    print(f"🔢 Cortes encontrados: {numeros_cortes}")
    
    if not numeros_cortes:
        print("❌ Nenhum corte encontrado para legendagem!")
        return
    
    for i, parte in enumerate(partes):
        if i >= len(numeros_cortes):
            print(f"⚠️ Não há corte correspondente para parte {i+1}")
            continue
            
        numero_corte = numeros_cortes[i]
        entrada = f"data/cortes/corte_{numero_corte}.mp4"
        
        # Obter próximo número sequencial para vídeos finais
        def obter_proximo_numero_final():
            padrao = "data/final/corte_*_legendado.mp4"
            arquivos_existentes = glob.glob(padrao)
            numeros = []
            for arquivo in arquivos_existentes:
                nome = os.path.basename(arquivo)
                match = re.search(r'corte_(\d+)_legendado\.mp4', nome)
                if match:
                    numeros.append(int(match.group(1)))
            return max(numeros) + 1 if numeros else 1
        
        proximo_final = obter_proximo_numero_final()
        saida = f"data/final/corte_{proximo_final}_legendado.mp4"
        segmentos = []
        parte_inicio = parte["start"]
        parte_fim = parte["end"]

        for seg in parte["segmentos"]:
            seg_ini = seg["start"] if isinstance(seg, dict) else seg.start
            seg_fim = seg["end"] if isinstance(seg, dict) else seg.end
            if seg_fim > parte_inicio and seg_ini < parte_fim:
                inicio_legenda = max(0, seg_ini - parte_inicio)
                fim_legenda = max(inicio_legenda + 0.5, seg_fim - parte_inicio)
                segmentos.append({
                    "start": round(inicio_legenda, 2),
                    "end": round(fim_legenda, 2),
                    "text": seg["text"] if isinstance(seg, dict) else seg.text
                })
        
        # NOVA FUNCIONALIDADE: Salvar dados completos na transcrição
        if segmentos_whisper:
            print(f"💾 [DADOS COMPLETOS] Salvando dados do Whisper para corte_{numero_corte}")
            from cortes.cortar_video import salvar_transcricao_corte
            
            # Filtrar segmentos do Whisper que estão dentro desta parte
            segmentos_parte = []
            for seg in segmentos_whisper:
                seg_ini = seg.get("start", 0.0)
                seg_fim = seg.get("end", 0.0)
                if seg_fim > parte_inicio and seg_ini < parte_fim:
                    # Ajustar timestamps para o corte
                    seg_ajustado = {
                        "start": max(0, seg_ini - parte_inicio),
                        "end": max(0, seg_fim - parte_inicio),
                        "text": seg.get("text", "")
                    }
                    segmentos_parte.append(seg_ajustado)
            
            # Salvar transcrição completa com dados do Whisper
            salvar_transcricao_corte(f"corte_{numero_corte}.mp4", parte.get("text", ""), parte_inicio, parte_fim, segmentos_parte)
        
        legendar_video_por_segmentos(entrada, segmentos, saida)'''
    
    # Substituir a função no arquivo main
    conteudo_main_corrigido = re.sub(
        r"def legendar_cortes_por_segmento\(partes\):.*?legendar_video_por_segmentos\(entrada, segmentos, saida\)",
        nova_funcao_main,
        conteudo_main_corrigido,
        flags=re.DOTALL
    )
    
    # Salvar arquivo corrigido
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(conteudo_main_corrigido)
    
    print("✅ 3. Função legendar_cortes_por_segmento modificada!")
    
    print("🎉 IMPLEMENTAÇÃO COMPLETA!")
    print("Agora o sistema salva TODOS os dados durante a legendagem:")
    print("- ✅ Timestamps detalhados do Whisper")
    print("- ✅ Pausas detectadas automaticamente")
    print("- ✅ Segmentos de legenda formatados")
    print("- ✅ Dados prontos para dublagem otimizada")
    print("")
    print("🚀 SUA IDEIA FOI IMPLEMENTADA COM SUCESSO!")

if __name__ == "__main__":
    implementar_modificacoes()
