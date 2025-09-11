# 🎬 Video Cutter V8 - Sistema Avançado de Edição e Dublagem

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Visão Geral

O **Video Cutter V8** é um sistema completo de edição de vídeos com inteligência artificial, focado na criação de conteúdo para redes sociais (Shorts, Reels, TikTok). O sistema oferece corte automático, legendagem, dublagem e geração de metadados usando IA.

## ✨ Funcionalidades Principais

### 🎯 **Sistema de Corte Inteligente**
- Corte automático de vídeos longos em segmentos otimizados
- Detecção de pontos de corte baseada em análise de áudio
- Geração de múltiplos cortes simultaneamente

### 🤖 **Inteligência Artificial Integrada**
- **Ollama**: Processamento local com modelos como Qwen2.5
- **OpenAI**: Integração com GPT para geração de conteúdo
- Geração automática de títulos, legendas e hashtags
- Análise contextual avançada do conteúdo

### 🎙️ **Sistema de Dublagem Avançado**
- Múltiplos motores TTS (Text-to-Speech)
- Tradução automática inglês → português
- Vozes masculinas e femininas em português
- Integração com Edge TTS para qualidade premium

### 📊 **Gerenciamento de Metadados**
- Sistema unificado de metadados em Excel
- Categorização automática (Legendado/Dublado)
- Exportação para ChatGPT e outras ferramentas
- Integração com Google Drive

### 🌐 **Interface Web Moderna**
- Interface responsiva e intuitiva
- Visualização de vídeos em grid
- Edição de metadados em tempo real
- Upload direto para Google Drive

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- FFmpeg instalado no sistema
- Ollama (opcional, para IA local)

### Instalação Rápida
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/video-cutter-v8.git
cd video-cutter-v8

# Instale as dependências
pip install -r requirements.txt

# Execute o aplicativo
python app.py
```

### Configuração da IA
1. Acesse `http://localhost:5000`
2. Clique em "🤖 Configurar IA"
3. Configure Ollama ou OpenAI conforme preferência

## 📁 Estrutura do Projeto

```
video-cutter-v8/
├── app.py                 # Aplicação principal Flask
├── main.py               # Script de processamento principal
├── requirements.txt      # Dependências Python
├── templates/
│   └── index.html        # Interface web
├── data/
│   ├── cortes/          # Vídeos cortados originais
│   ├── final/           # Vídeos legendados finais
│   ├── cortes_dublado/  # Vídeos dublados
│   ├── planilhas/       # Metadados em Excel
│   └── transcricoes/    # Transcrições dos vídeos
├── static/              # Arquivos estáticos
├── bin/                 # Binários (FFmpeg, etc.)
└── utils/               # Utilitários auxiliares
```

## 🔧 Configuração

### Variáveis de Ambiente
```bash
# Ollama (opcional)
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# OpenAI (opcional)
OPENAI_API_KEY=sua_chave_aqui
```

### Configuração do FFmpeg
O sistema detecta automaticamente o FFmpeg na pasta `bin/ffmpeg/`. Se necessário, ajuste o caminho em `app.py`.

## 📖 Como Usar

### 1. **Corte de Vídeos**
1. Faça upload do vídeo original
2. Configure os parâmetros de corte
3. Execute o processamento
4. Visualize os cortes gerados

### 2. **Geração de Metadados com IA**
1. Clique em "GERAR TEXTOS COM AI"
2. Configure o nicho do conteúdo
3. Aguarde o processamento sequencial
4. Revise e edite os metadados gerados

### 3. **Dublagem de Vídeos**
1. Acesse a seção "Vídeos Dublados"
2. Selecione a voz desejada
3. Configure o idioma de destino
4. Execute a dublagem

### 4. **Exportação e Upload**
1. Use "Fazer Manualmente" para exportar transcrições
2. Edite no ChatGPT se necessário
3. Importe as alterações
4. Faça upload para Google Drive

## 🤖 Integração com IA

### Ollama (Recomendado)
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull qwen2.5:7b-instruct
```

### OpenAI
Configure sua API key no painel de configuração da aplicação.

## 📊 Recursos Avançados

### **Análise Contextual**
- Detecção automática de tema (motivação, negócios, educação)
- Extração de palavras-chave relevantes
- Geração de hashtags contextuais

### **Sistema de Fallback**
- Múltiplos métodos TTS para máxima compatibilidade
- Análise local quando IA não disponível
- Tratamento robusto de erros

### **Integração Google Drive**
- Upload automático de vídeos
- Atualização de planilhas no Drive
- Sincronização de metadados

## 🐛 Solução de Problemas

### Erros Comuns
1. **FFmpeg não encontrado**: Verifique se está na pasta `bin/ffmpeg/`
2. **Ollama não responde**: Verifique se o serviço está rodando
3. **Erro de permissão**: Execute como administrador se necessário

### Logs
Os logs são salvos em `server.log` e `status.log` para debugging.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Changelog

### V8.0.0 (Atual)
- ✅ Sistema de dublagem avançado
- ✅ Integração com múltiplas IAs
- ✅ Interface web moderna
- ✅ Sistema de metadados unificado
- ✅ Upload para Google Drive
- ✅ Correção de bugs críticos

### V7.0.0
- Sistema básico de corte
- Legendagem simples
- Interface básica

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**Paulo** - Desenvolvedor Principal
- GitHub: [@seu-usuario](https://github.com/seu-usuario)
- Email: seu-email@exemplo.com

## 🙏 Agradecimentos

- Comunidade Python
- Projeto Ollama
- OpenAI
- Flask Framework
- MoviePy

---

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Abra uma [Issue](https://github.com/seu-usuario/video-cutter-v8/issues)
- Envie um email para: suporte@exemplo.com

**⭐ Se este projeto te ajudou, considere dar uma estrela!**
