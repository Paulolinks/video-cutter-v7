# 📝 Changelog - Video Cutter V8

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [8.0.0] - 2024-01-10

### 🎉 Lançamento da Versão 8.0

#### ✨ Novas Funcionalidades
- **Sistema de Dublagem Avançado**
  - Múltiplos motores TTS (PowerShell, pyttsx3, gTTS, edge_tts)
  - Tradução automática inglês → português
  - Vozes masculinas e femininas em português
  - Interface dedicada para vídeos dublados

- **Inteligência Artificial Integrada**
  - Suporte a Ollama com modelos Qwen2.5
  - Integração com OpenAI GPT
  - Geração automática de títulos, legendas e hashtags
  - Análise contextual avançada do conteúdo

- **Sistema de Metadados Unificado**
  - Planilha única para todos os metadados (`data/planilhas/publicar.xlsx`)
  - Coluna "tipo" para categorizar Legendado/Dublado
  - Coluna "postado" para controle de publicação
  - Exportação inteligente para ChatGPT

- **Interface Web Moderna**
  - Seção separada para vídeos dublados
  - Grid responsivo para visualização
  - Edição de metadados em tempo real
  - Botões de geração individual e em lote

- **Integração Google Drive**
  - Upload automático de vídeos
  - Atualização de planilhas no Drive
  - Sincronização de metadados

#### 🔧 Melhorias
- **Sistema de Corte Inteligente**
  - Detecção automática de pontos de corte
  - Processamento em lote otimizado
  - Renomeação automática baseada em IA

- **Sistema de Exportação**
  - Exporta apenas vídeos que existem fisicamente
  - Usa nomes corretos dos arquivos renomeados
  - Inclui transcrições específicas de cada corte

- **Tratamento de Erros**
  - Sistema robusto de fallback para TTS
  - Análise local quando IA não disponível
  - Logs detalhados para debugging

#### 🐛 Correções de Bugs
- **Erros Críticos de Sintaxe**
  - Corrigidos 6 erros de indentação em `app.py`
  - Corrigidos problemas de `break` fora de loops
  - Corrigidos blocos `try/except` malformados

- **Problemas de Renomeação**
  - Arquivos legendados agora são renomeados corretamente
  - Interface mostra nomes atualizados
  - Exportação usa nomes corretos

- **Problemas de Roteamento**
  - Adicionada rota para servir arquivos de `data/final`
  - Interface carrega vídeos corretamente
  - Metadados persistem após refresh

- **Problemas de Metadados**
  - Metadados de vídeos dublados agora persistem
  - Planilha de exportação inclui todos os dados
  - Sistema de idempotência funcionando

#### 🏗️ Arquitetura
- **Estrutura de Pastas Reorganizada**
  - `data/cortes/` - Vídeos cortados originais
  - `data/final/` - Vídeos legendados finais
  - `data/cortes_dublado/` - Vídeos dublados
  - `data/planilhas/` - Metadados em Excel

- **Sistema de Configuração**
  - Arquivo `ai_config.json` para configurações de IA
  - Suporte a variáveis de ambiente
  - Configuração via interface web

#### 📊 Estatísticas da Versão
- **Linhas de Código**: ~3,500
- **Arquivos Modificados**: 15+
- **Bugs Corrigidos**: 10+
- **Funcionalidades Adicionadas**: 8
- **Tempo de Desenvolvimento**: ~40 horas

#### 🔄 Migração da V7
- **Breaking Changes**: Nenhuma
- **Compatibilidade**: Total com projetos V7
- **Dados**: Migração automática de metadados

#### 📋 Próximas Versões
- **V8.1.0** (Planejada)
  - Suporte a mais idiomas de dublagem
  - Integração com mais serviços de IA
  - Melhorias na interface mobile

- **V8.2.0** (Futura)
  - Sistema de templates de metadados
  - Integração com mais plataformas
  - Analytics de performance

---

## [7.0.0] - 2023-12-15

### 🎉 Lançamento da Versão 7.0

#### ✨ Funcionalidades Iniciais
- Sistema básico de corte de vídeos
- Legendagem simples
- Interface web básica
- Upload para Google Drive

#### 🔧 Melhorias
- Processamento otimizado
- Interface responsiva
- Sistema de logs

---

## 📝 Formato do Changelog

Este projeto segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

### Tipos de Mudanças
- **✨ Adicionado** para novas funcionalidades
- **🔧 Alterado** para mudanças em funcionalidades existentes
- **🐛 Corrigido** para correções de bugs
- **🗑️ Removido** para funcionalidades removidas
- **🔒 Segurança** para correções de segurança

---

*Última atualização: 2024-01-10*
*Versão atual: 8.0.0*
