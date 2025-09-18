# ⚡ Configuração de Velocidade e Pausas na Dublagem

## 🎯 Problema Original
Você mencionou que o vídeo tem:
- **Momentos de pico**: ator fala mais rápido
- **Pausas naturais**: momentos de silêncio
- **Variação de velocidade**: hora mais devagar, hora mais rápido

## 🛠️ Soluções Implementadas

### 1. 📝 Configuração Básica (`vozes_clonadas.json`)

```json
{
  "vozes": [
    {
      "id": "clonada_Minha_Voz_Paulolinks",
      "nome": "Minha Voz - Paulolinks",
      "configuracoes": {
        "velocidade": 0.95,     // Levemente mais lenta
        "tom": -1.0,            // Tom um pouco mais grave  
        "qualidade": "alta",
        "pausas_naturais": true,
        "adaptacao_velocidade": true
      }
    }
  ]
}
```

### 2. 🎛️ Configurações Avançadas

Para ajustar velocidade baseada no contexto do vídeo, modifique a função no `app.py`:

```python
def gerar_audio_edge_tts_personalizado(texto, arquivo_referencia):
    """Gera áudio com Edge TTS e ajustes de velocidade"""
    try:
        # Detectar se é momento de pico ou pausa
        velocidade_base = "-10%"  # Padrão mais lenta
        
        # Detectar momentos rápidos (exclamações, perguntas)
        if any(palavra in texto.lower() for palavra in ['!', '?', 'rápido', 'agora', 'vamos']):
            velocidade_base = "+5%"   # Mais rápida para momentos de energia
        
        # Detectar momentos reflexivos (pausas naturais)
        elif any(palavra in texto.lower() for palavra in ['então', 'mas', 'porém', 'assim']):
            velocidade_base = "-20%"  # Bem mais lenta para reflexão
        
        communicate = edge_tts.Communicate(
            texto,
            "pt-BR-ValerioNeural",
            rate=velocidade_base,
            pitch="-2Hz",
            # Adicionar pausas em pontuação
            prosody_rate="medium",
            prosody_pitch="medium"
        )
        # ... resto do código
```

### 3. 🎵 Ajustes por Segmento

Para vídeos com variação de ritmo, você pode criar configurações específicas:

```python
# Adicionar no app.py, na função dublar_video()

def ajustar_audio_ao_video(audio_clip, video_clip, texto):
    """Ajusta áudio para sincronizar com ritmo do vídeo"""
    
    # Detectar momentos do texto
    segmentos = dividir_texto_por_contexto(texto)
    
    audio_ajustado = audio_clip
    
    for i, segmento in enumerate(segmentos):
        inicio = i * (audio_clip.duration / len(segmentos))
        fim = (i + 1) * (audio_clip.duration / len(segmentos))
        
        # Ajustar velocidade baseado no contexto
        if segmento["tipo"] == "rapido":
            # Acelerar este trecho
            trecho = audio_clip.subclip(inicio, fim).fx(speedx, 1.15)
        elif segmento["tipo"] == "pausa":
            # Desacelerar e adicionar pausa
            trecho = audio_clip.subclip(inicio, fim).fx(speedx, 0.85)
        else:
            # Velocidade normal
            trecho = audio_clip.subclip(inicio, fim)
        
        # Reconstruir áudio
        if i == 0:
            audio_ajustado = trecho
        else:
            audio_ajustado = concatenate_audioclips([audio_ajustado, trecho])
    
    return audio_ajustado

def dividir_texto_por_contexto(texto):
    """Divide texto em segmentos com tipo de velocidade"""
    # Detectar pontuação e palavras-chave
    segmentos = []
    
    frases = texto.split('.')
    for frase in frases:
        if any(palavra in frase.lower() for palavra in ['!', '?', 'rápido', 'agora']):
            segmentos.append({"texto": frase, "tipo": "rapido"})
        elif any(palavra in frase.lower() for palavra in ['então', 'mas', 'porém']):
            segmentos.append({"texto": frase, "tipo": "pausa"})
        else:
            segmentos.append({"texto": frase, "tipo": "normal"})
    
    return segmentos
```

### 4. 🎚️ Configurações por Tipo de Conteúdo

Adicione configurações específicas em `vozes_clonadas.json`:

```json
{
  "configuracoes": {
    "velocidade": 1.0,
    "tom": 0.0,
    "perfis_velocidade": {
      "motivacional": {
        "velocidade": 1.1,
        "pausas": "curtas",
        "enfase": "alta"
      },
      "explicativo": {
        "velocidade": 0.9,
        "pausas": "longas", 
        "enfase": "media"
      },
      "narrativo": {
        "velocidade": 1.0,
        "pausas": "naturais",
        "enfase": "variavel"
      }
    }
  }
}
```

### 5. 🔧 Configuração Manual no Frontend

Adicione controles no `templates/index.html`:

```html
<!-- Controles de Velocidade -->
<div style="margin-bottom: 20px;">
  <label style="color: #fff;">Velocidade da Dublagem:</label>
  <input type="range" id="speedRange" min="0.5" max="1.5" step="0.1" value="1.0">
  <span id="speedValue" style="color: #00f7ff;">1.0x</span>
</div>

<!-- Controles de Pausas -->
<div style="margin-bottom: 20px;">
  <label style="color: #fff;">Estilo de Pausas:</label>
  <select id="pauseStyle">
    <option value="natural">Natural (recomendado)</option>
    <option value="rapido">Rápido (sem pausas longas)</option>
    <option value="lento">Lento (pausas estendidas)</option>
  </select>
</div>

<script>
// Atualizar valor da velocidade
document.getElementById('speedRange').addEventListener('input', function() {
  document.getElementById('speedValue').textContent = this.value + 'x';
});

// Modificar função iniciarDublagem() para incluir configurações
async function iniciarDublagem() {
  const velocidade = document.getElementById('speedRange').value;
  const estiloPausa = document.getElementById('pauseStyle').value;
  
  const res = await fetch('/voz/gerar_para_cortes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      lang_target: 'pt', 
      voice: selectedVoice,
      configuracoes: {
        velocidade: parseFloat(velocidade),
        estilo_pausa: estiloPausa
      }
    })
  });
}
</script>
```

## 🎯 Configurações Recomendadas para seu caso

Baseado na descrição do seu vídeo, sugiro:

### Para vídeos motivacionais/energéticos:
```json
{
  "configuracoes": {
    "velocidade": 1.05,
    "tom": -0.5,
    "perfil": "motivacional",
    "adaptacao_automatica": true
  }
}
```

### Para vídeos explicativos:
```json
{
  "configuracoes": {
    "velocidade": 0.95,
    "tom": -1.0,
    "perfil": "explicativo",
    "pausas_enfatizadas": true
  }
}
```

## 🧪 Como testar as configurações

1. **Modifique** `vozes_clonadas.json` com as configurações desejadas
2. **Execute** `python teste_dublagem_voz_clonada.py`
3. **Teste** na interface web com um vídeo curto
4. **Ajuste** os valores conforme necessário
5. **Repita** até encontrar o equilíbrio ideal

## 🔍 Monitoramento

Adicione logs para acompanhar os ajustes:

```python
# No app.py, função gerar_audio_voz_clonada()
print(f"🎛️ Configurações aplicadas:")
print(f"   Velocidade: {config.get('velocidade', 1.0)}")
print(f"   Tom: {config.get('tom', 0.0)}")
print(f"   Perfil: {config.get('perfil', 'padrão')}")
```

**Agora você tem controle total sobre velocidade e pausas da dublagem! 🎙️**