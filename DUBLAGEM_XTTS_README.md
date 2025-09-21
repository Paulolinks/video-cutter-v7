# Sistema de Dublagem XTTS v2

## Visão Geral

Este sistema implementa dublagem avançada usando XTTS v2 (Coqui) com clonagem de voz por sentenças, resolvendo os problemas de sincronização e qualidade da dublagem anterior.

## Características Principais

- **Dublagem por sentenças**: Cada sentença é processada individualmente
- **Time-stretch preciso**: Ajusta a duração de cada sentença para bater exatamente com os timestamps
- **Pausas reais**: Calcula e insere silêncio entre sentenças
- **Clonagem de voz**: Usa XTTS v2 para clonar sua voz de referência
- **Sincronização perfeita**: Alinha com as legendas e timestamps originais

## Arquivos do Sistema

- `dub_xtts.py` - Sistema principal de dublagem XTTS v2
- `converter_transcricoes_xtts.py` - Conversor de transcrições para formato JSON
- `teste_dublagem_xtts.py` - Script de teste do sistema
- `voice_refs/` - Pasta para arquivos de referência de voz

## Como Usar

### 1. Preparação

1. **Instalar dependências** (já está no requirements.txt):
   ```bash
   pip install TTS==0.22.0
   ```

2. **Converter transcrições** (se ainda não foi feito):
   ```bash
   python converter_transcricoes_xtts.py
   ```

3. **Adicionar arquivo de voz de referência**:
   - Coloque um arquivo WAV com sua voz em `voice_refs/minha_voz.wav`
   - Ou use o arquivo existente em `data/audio/audio.wav`

### 2. Uso via API

**Endpoint**: `POST /dublar_xtts`

**Parâmetros**:
```json
{
    "cut_id": "corte_1",
    "prefer_lang": "pt"
}
```

**Resposta de sucesso**:
```json
{
    "success": true,
    "message": "Dublagem concluída com sucesso! 13 sentenças processadas.",
    "result": {
        "audio": "outputs/dublados/corte_1/corte_1_dub.wav",
        "video": "outputs/dublados/corte_1/corte_1_dub.mp4",
        "report": "outputs/dublados/corte_1/corte_1_align_report.json",
        "sentences": 13
    }
}
```

### 3. Uso Direto (Python)

```python
from dub_xtts import dublar_corte_xtts

# Dublar um corte específico
result = dublar_corte_xtts(
    cut_id="corte_1",
    prefer_lang="pt",  # "pt" para português, "en" para inglês
    base_data_dir="data",
    outputs_dir="outputs"
)

print(f"Arquivos gerados: {result}")
```

## Estrutura de Dados

### Transcrições JSON

O sistema espera arquivos JSON na pasta `data/transcricoes_cortes/json/` com a estrutura:

```json
{
  "sentences": [
    {
      "start": 0,
      "end": 5.0,
      "text": "Texto original em inglês",
      "text_en": "Texto original em inglês",
      "text_pt": "Texto traduzido em português",
      "duration": 5.0
    }
  ]
}
```

### Arquivos de Saída

Para cada corte dublado, são gerados:

- `{cut_id}_dub.wav` - Áudio dublado
- `{cut_id}_dub.mp4` - Vídeo final com dublagem
- `{cut_id}_align_report.json` - Relatório de alinhamento

## Vantagens sobre o Sistema Anterior

1. **Sincronização perfeita**: Time-stretch por sentença, não no vídeo inteiro
2. **Pausas naturais**: Calcula silêncio real entre sentenças
3. **Qualidade superior**: XTTS v2 com clonagem de voz
4. **Sem "colagem"**: Cada sentença é sintetizada individualmente
5. **Alinhamento preciso**: Bate exatamente com os timestamps

## Resolução de Problemas

### Erro: "XTTS v2 não disponível"
- Verifique se `TTS==0.22.0` está instalado
- Execute: `pip install TTS==0.22.0`

### Erro: "Transcrição JSON não encontrada"
- Execute o conversor: `python converter_transcricoes_xtts.py`

### Erro: "Arquivo de referência de voz não encontrado"
- Coloque um arquivo WAV em `voice_refs/minha_voz.wav`
- Ou use o arquivo existente em `data/audio/audio.wav`

### Erro: "FFmpeg error"
- Verifique se FFmpeg está instalado no sistema
- Adicione FFmpeg ao PATH do Windows

## Teste do Sistema

Execute o script de teste para verificar se tudo está funcionando:

```bash
python teste_dublagem_xtts.py
```

## Integração no App.py

O sistema já está integrado no `app.py` com a rota `/dublar_xtts`. A integração inclui:

- Verificação de disponibilidade do XTTS
- Validação de arquivos necessários
- Tratamento de erros
- Resposta JSON padronizada

## Próximos Passos

1. **Teste com arquivo de voz real**: Grave um arquivo WAV com sua voz
2. **Ajuste de parâmetros**: Modifique `SR`, `LANG_DEFAULT` se necessário
3. **Interface web**: Adicione botão na interface para usar a nova dublagem
4. **Otimizações**: Ajuste time-stretch e pausas conforme necessário
