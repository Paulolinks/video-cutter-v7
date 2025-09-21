# 🎭 Funcionalidades de Clonagem de Voz - Video Cutter v8

## 📋 Visão Geral

O Video Cutter v8 agora inclui **3 novas funcionalidades de clonagem de voz** que permitem dublar vídeos usando diferentes fontes de voz:

1. **🎤 Dublar com Minha Voz** - Upload de arquivo de áudio de referência
2. **🎬 Usar Voz Original de Cada Vídeo** - Extração automática da voz original
3. **🎯 Dublar com Voz de Um Vídeo Específico** - Usar voz de um vídeo como fonte

## 🚀 Como Usar

### 1. 🎤 Dublar com Minha Voz

**Passos:**
1. Na seção "🎭 Opções de Clonagem de Voz", clique em "📁 Escolher Arquivo de Áudio"
2. Selecione um arquivo de áudio (WAV, MP3, M4A, AAC) com sua voz
3. Faça preview do áudio se necessário
4. Clique em "🎤 Dublar com Minha Voz"

**Requisitos do arquivo de áudio:**
- Formatos suportados: WAV, MP3, M4A, AAC
- Qualidade: Áudio claro, sem ruído de fundo
- Duração: Recomendado 10-30 segundos de fala
- Idioma: Português brasileiro (para melhores resultados)

### 2. 🎬 Usar Voz Original de Cada Vídeo

**Passos:**
1. Na seção "🎭 Opções de Clonagem de Voz"
2. Marque a opção "Extrair e usar a voz original de cada vídeo individualmente"
3. Clique em "🎤 Dublar com Vozes Originais"

**Como funciona:**
- O sistema extrai automaticamente o áudio de cada vídeo
- Usa a voz extraída para gerar nova dublagem com o texto traduzido
- Cada vídeo mantém características da voz original

### 3. 🎯 Dublar com Voz de Um Vídeo Específico

**Passos:**
1. Na seção "🎭 Opções de Clonagem de Voz"
2. No dropdown "Selecionar vídeo fonte...", escolha um vídeo
3. Clique em "🎤 Dublar com Voz Selecionada"

**Como funciona:**
- Extrai a voz do vídeo selecionado como fonte
- Usa essa voz para dublar todos os outros vídeos
- Útil para manter consistência de voz em uma série de vídeos

## 🔧 Implementação Técnica

### Estrutura das APIs

```python
# Upload de voz do usuário
POST /voz/clonar_minha_voz
Content-Type: multipart/form-data
Body: audio_file (arquivo de áudio)

# Clonagem com vozes originais
POST /voz/clonar_vozes_originais
Content-Type: application/json

# Clonagem com voz de fonte específica
POST /voz/clonar_voz_fonte
Content-Type: application/json
Body: {"video_fonte": "nome_do_video.mp4"}
```

### Funções Principais

- `carregar_textos_traduzidos()` - Carrega textos da planilha para dublagem
- `extrair_audio_video()` - Extrai áudio de vídeos
- `simular_clonagem_voz()` - Simula clonagem de voz (TTS atual)
- `criar_video_dublado()` - Cria vídeo final com áudio dublado

## 📁 Estrutura de Arquivos

```
data/
├── cortes_dublado/          # Vídeos dublados com clonagem
├── planilhas/
│   ├── publicar.xlsx        # Textos traduzidos para dublagem
│   └── publicar.csv
temp_voice_cloning/          # Arquivos temporários de clonagem
static/final/                # Vídeos originais para dublagem
```

## ⚠️ Limitações Atuais

### Simulação vs. Clonagem Real

**Atualmente implementado:**
- ✅ Interface completa de clonagem de voz
- ✅ Upload e validação de arquivos de áudio
- ✅ Extração de áudio de vídeos
- ✅ Integração com sistema de dublagem existente
- ✅ Criação de vídeos dublados

**Em desenvolvimento (simulação atual):**
- 🔄 Clonagem real de voz (usa TTS padrão como placeholder)
- 🔄 Treinamento de modelo com voz do usuário
- 🔄 Clonagem avançada com bibliotecas especializadas

### Próximos Passos para Clonagem Real

Para implementar clonagem real de voz, adicionar:

```python
# requirements.txt adicionais
speechbrain>=0.5.14
resemblyzer>=0.1.1
librosa>=0.10.0
soundfile>=0.12.1
```

```python
# Exemplo de implementação real
def clonagem_real_voz(audio_referencia, texto):
    # 1. Extrair características da voz de referência
    # 2. Treinar modelo de clonagem
    # 3. Gerar áudio com texto desejado
    # 4. Retornar arquivo de áudio clonado
    pass
```

## 🎯 Casos de Uso

### Para Criadores de Conteúdo
- **Consistência de marca:** Usar sua própria voz em todos os vídeos
- **Eficiência:** Não precisar gravar áudio para cada vídeo
- **Qualidade:** Manter qualidade de voz profissional

### Para Agências
- **Clientes diversos:** Usar voz do cliente específico
- **Produção em massa:** Dublar múltiplos vídeos com mesma voz
- **Personalização:** Adaptar voz para diferentes contextos

### Para Influenciadores
- **Autenticidade:** Manter voz original em diferentes idiomas
- **Expansão:** Criar conteúdo em outros idiomas mantendo identidade
- **Produtividade:** Automatizar processo de dublagem

## 🔍 Troubleshooting

### Problemas Comuns

**Erro: "Formato de arquivo não suportado"**
- Solução: Use apenas WAV, MP3, M4A ou AAC

**Erro: "Nenhum vídeo encontrado para dublar"**
- Solução: Certifique-se que há vídeos em `static/final/`

**Erro: "Falha ao extrair voz do vídeo fonte"**
- Solução: Verifique se o vídeo tem áudio válido

**Vídeos dublados não aparecem**
- Solução: Verifique a pasta `data/cortes_dublado/`

### Logs e Debug

```bash
# Verificar logs do sistema
tail -f server.log

# Verificar arquivos temporários
ls -la temp_voice_cloning/

# Verificar vídeos dublados
ls -la data/cortes_dublado/
```

## 🚀 Roadmap

### Versão 8.1 (Próxima)
- [ ] Implementar clonagem real de voz com SpeechBrain
- [ ] Adicionar pré-visualização de áudio clonado
- [ ] Melhorar qualidade de sincronização
- [ ] Adicionar mais formatos de áudio suportados

### Versão 8.2 (Futura)
- [ ] Interface para treinamento de modelo personalizado
- [ ] Suporte a múltiplos idiomas
- [ ] Clonagem de voz em tempo real
- [ ] Integração com APIs de IA avançadas

---

**✨ As funcionalidades de clonagem de voz estão prontas para uso! A interface está completa e integrada ao sistema existente. Para clonagem real de voz, será necessário implementar as bibliotecas especializadas mencionadas no roadmap.**
