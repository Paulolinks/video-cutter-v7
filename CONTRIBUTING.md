# 🤝 Guia de Contribuição - Video Cutter V8

Obrigado por considerar contribuir com o Video Cutter V8! Este documento fornece diretrizes para contribuições.

## 📋 Como Contribuir

### 1. **Fork e Clone**
```bash
# Fork o repositório no GitHub
# Clone seu fork
git clone https://github.com/SEU-USUARIO/video-cutter-v8.git
cd video-cutter-v8

# Adicione o repositório original como upstream
git remote add upstream https://github.com/ORIGINAL-OWNER/video-cutter-v8.git
```

### 2. **Criar uma Branch**
```bash
# Crie uma branch para sua feature
git checkout -b feature/nome-da-feature

# Ou para correção de bugs
git checkout -b fix/descricao-do-bug
```

### 3. **Desenvolvimento**
- Siga as convenções de código existentes
- Adicione comentários explicativos
- Teste suas mudanças localmente
- Mantenha commits pequenos e descritivos

### 4. **Testes**
```bash
# Execute os testes
python -m pytest tests/

# Verifique a sintaxe
python -m py_compile app.py

# Execute o aplicativo
python app.py
```

### 5. **Commit e Push**
```bash
# Adicione suas mudanças
git add .

# Commit com mensagem descritiva
git commit -m "feat: adiciona nova funcionalidade X"

# Push para sua branch
git push origin feature/nome-da-feature
```

### 6. **Pull Request**
- Abra um Pull Request no GitHub
- Descreva claramente as mudanças
- Referencie issues relacionadas
- Aguarde revisão e feedback

## 📝 Convenções de Código

### **Python**
- Use PEP 8 como guia de estilo
- Máximo 120 caracteres por linha
- Use docstrings para funções e classes
- Nomes de variáveis em snake_case
- Nomes de classes em PascalCase

### **Commits**
Use o formato Conventional Commits:
- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` documentação
- `style:` formatação
- `refactor:` refatoração
- `test:` testes
- `chore:` tarefas de manutenção

### **Exemplos:**
```bash
feat: adiciona sistema de dublagem
fix: corrige erro de renomeação de arquivos
docs: atualiza README com novas funcionalidades
```

## 🐛 Reportando Bugs

### **Antes de Reportar**
1. Verifique se o bug já foi reportado
2. Teste com a versão mais recente
3. Verifique os logs de erro

### **Informações Necessárias**
- Versão do Python
- Sistema operacional
- Passos para reproduzir
- Comportamento esperado vs atual
- Logs de erro (se houver)
- Screenshots (se aplicável)

### **Template de Bug Report**
```markdown
**Descrição do Bug**
Descrição clara e concisa do problema.

**Passos para Reproduzir**
1. Vá para '...'
2. Clique em '...'
3. Veja o erro

**Comportamento Esperado**
O que deveria acontecer.

**Comportamento Atual**
O que está acontecendo.

**Screenshots**
Se aplicável, adicione screenshots.

**Informações do Sistema**
- OS: [ex: Windows 10]
- Python: [ex: 3.8.5]
- Versão: [ex: 8.0.0]

**Logs Adicionais**
Cole os logs de erro aqui.
```

## ✨ Sugerindo Funcionalidades

### **Antes de Sugerir**
1. Verifique se a funcionalidade já foi sugerida
2. Considere se é realmente necessária
3. Pense na implementação

### **Template de Feature Request**
```markdown
**Funcionalidade Desejada**
Descrição clara da funcionalidade.

**Problema que Resolve**
Qual problema esta funcionalidade resolve?

**Solução Proposta**
Como você imagina que deveria funcionar?

**Alternativas Consideradas**
Outras soluções que você considerou.

**Contexto Adicional**
Qualquer contexto adicional sobre a funcionalidade.
```

## 🏗️ Estrutura do Projeto

```
video-cutter-v8/
├── app.py                 # Aplicação principal
├── main.py               # Script de processamento
├── requirements.txt      # Dependências
├── templates/            # Templates HTML
├── data/                 # Dados da aplicação
├── static/              # Arquivos estáticos
├── utils/               # Utilitários
├── tests/               # Testes
└── docs/                # Documentação
```

## 🧪 Testes

### **Executando Testes**
```bash
# Todos os testes
python -m pytest

# Testes específicos
python -m pytest tests/test_app.py

# Com cobertura
python -m pytest --cov=app
```

### **Escrevendo Testes**
- Teste funções críticas
- Use mocks para dependências externas
- Mantenha testes simples e focados
- Nomeie testes de forma descritiva

## 📚 Documentação

### **Atualizando Documentação**
- README.md para visão geral
- CHANGELOG.md para mudanças
- Docstrings para código
- Comentários para lógica complexa

### **Padrões de Documentação**
- Use Markdown para arquivos .md
- Use reStructuredText para docstrings
- Inclua exemplos de uso
- Mantenha documentação atualizada

## 🔄 Processo de Review

### **Para Revisores**
1. Verifique se o código segue as convenções
2. Teste as mudanças localmente
3. Verifique se os testes passam
4. Comente sugestões construtivas
5. Aprove ou solicite mudanças

### **Para Autores**
1. Responda aos comentários
2. Faça as mudanças solicitadas
3. Mantenha o PR atualizado
4. Seja paciente com o processo

## 📞 Suporte

### **Canais de Comunicação**
- GitHub Issues para bugs e features
- GitHub Discussions para dúvidas
- Email para questões privadas

### **Resposta Esperada**
- Issues: 2-3 dias úteis
- Pull Requests: 1-2 semanas
- Discussões: 1-2 dias

## 🎯 Roadmap

### **Versão 8.1.0**
- [ ] Suporte a mais idiomas
- [ ] Melhorias na interface mobile
- [ ] Integração com mais IAs

### **Versão 8.2.0**
- [ ] Sistema de templates
- [ ] Analytics de performance
- [ ] API REST

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a Licença MIT.

---

**Obrigado por contribuir com o Video Cutter V8! 🎬✨**
