"""
Conversor para transformar transcrições do formato atual para JSON compatível com XTTS v2
"""
import json
import re
from pathlib import Path

def converter_transcricao_para_xtts(arquivo_txt: Path, arquivo_json: Path):
    """
    Converte arquivo de transcrição .txt para formato JSON compatível com XTTS
    """
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Extrair timestamps detalhados
    timestamps_match = re.search(r'TIMESTAMPS_DETALHADOS:\s*(\[.*?\])', conteudo, re.DOTALL)
    if not timestamps_match:
        raise ValueError("TIMESTAMPS_DETALHADOS não encontrado no arquivo")
    
    timestamps_str = timestamps_match.group(1)
    timestamps = json.loads(timestamps_str)
    
    # Extrair segmentos de legenda para tradução
    legendas_match = re.search(r'SEGMENTOS_LEGENDA:\s*(\[.*?\])', conteudo, re.DOTALL)
    legendas = []
    if legendas_match:
        legendas_str = legendas_match.group(1)
        legendas = json.loads(legendas_str)
    
    # Criar dicionário de traduções por índice
    traducoes = {}
    for legenda in legendas:
        indice = legenda.get('indice')
        if indice:
            traducoes[indice] = {
                'texto_original': legenda.get('texto_original', ''),
                'texto_traduzido': legenda.get('texto_traduzido', '')
            }
    
    # Converter para formato XTTS
    sentences = []
    for i, ts in enumerate(timestamps):
        indice = ts.get('indice', i + 1)
        traducao = traducoes.get(indice, {})
        
        sentence = {
            "start": ts.get('inicio', 0),
            "end": ts.get('fim', 0),
            "text": ts.get('texto', ''),  # texto original em inglês
            "text_en": ts.get('texto', ''),  # texto em inglês
            "text_pt": traducao.get('texto_traduzido', ''),  # texto em português
            "duration": ts.get('duracao', 0)
        }
        sentences.append(sentence)
    
    # Salvar no formato JSON esperado pelo XTTS
    dados_xtts = {
        "sentences": sentences,
        "metadata": {
            "source_file": str(arquivo_txt),
            "total_sentences": len(sentences),
            "converted_for": "xtts_v2"
        }
    }
    
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(dados_xtts, f, ensure_ascii=False, indent=2)
    
    print(f"Convertido: {arquivo_txt} -> {arquivo_json}")
    print(f"Total de sentenças: {len(sentences)}")
    
    return arquivo_json

def converter_todas_transcricoes(data_dir="data"):
    """
    Converte todas as transcrições da pasta data/transcricoes_cortes
    """
    data_path = Path(data_dir)
    transcricoes_dir = data_path / "transcricoes_cortes"
    
    if not transcricoes_dir.exists():
        print(f"Pasta não encontrada: {transcricoes_dir}")
        return
    
    # Criar pasta para JSONs se não existir
    json_dir = transcricoes_dir / "json"
    json_dir.mkdir(exist_ok=True)
    
    arquivos_txt = list(transcricoes_dir.glob("*.txt"))
    
    if not arquivos_txt:
        print("Nenhum arquivo .txt encontrado")
        return
    
    print(f"Encontrados {len(arquivos_txt)} arquivos para converter...")
    
    for arquivo_txt in arquivos_txt:
        try:
            # Nome do arquivo JSON baseado no TXT
            nome_json = arquivo_txt.stem + ".json"
            arquivo_json = json_dir / nome_json
            
            converter_transcricao_para_xtts(arquivo_txt, arquivo_json)
            
        except Exception as e:
            print(f"Erro ao converter {arquivo_txt}: {e}")
    
    print("Conversão concluída!")

if __name__ == "__main__":
    converter_todas_transcricoes()
