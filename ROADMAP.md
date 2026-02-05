# 🚀 Roadmap de Implementação - WhatsApp Chatbot

## ✅ Funcionalidades Implementadas

- [x] Sistema de agentes com LangGraph
- [x] Memória persistente com SQLite (sobrevive restarts)
- [x] Summary Agent para gerenciamento de tokens
- [x] Google Calendar Integration
  - [x] Agendamento de reuniões
  - [x] Detecção de conflitos
  - [x] 5 opções de resolução de conflitos
  - [x] Timezone correto (America/Sao_Paulo)
  - [x] Sugestão de horários alternativos
  - [x] Listar eventos (hoje/semana/mês/todos)
  - [x] Cancelar eventos por nome/identificação
  - [x] Editar horário de eventos existentes
  - [x] Detecção de ação (schedule/list/cancel/edit)
- [x] Email Integration (Gmail SMTP + IMAP)
  - [x] Envio de emails
  - [x] Validação de endereços
  - [x] Suporte HTML
  - [x] CC/BCC support
  - [x] Leitura de emails recentes
  - [x] Busca de emails por assunto/remetente
  - [x] Detecção de ação (send/read/search)
- [x] Web Search Agent (DuckDuckGo)
  - [x] Busca geral na web
  - [x] Busca de notícias
  - [x] Formatação adaptativa baseada em intenção do usuário
  - [x] Inclusão de fontes nos resultados
- [x] Base de Conhecimento (RAG)
  - [x] ChromaDB para vetores
  - [x] Embedding de documentos
  - [x] Busca semântica
- [x] Router Agent inteligente
- [x] CLI funcional para testes

---

## 📋 Backlog de Funcionalidades

### 1. 📱 Integração WhatsApp Real
**Prioridade:** Alta  
**Complexidade:** Média

- [ ] Integrar com WhatsApp Web (whatsapp-web.js)
- [ ] Gerenciar múltiplas sessões
- [ ] QR Code para autenticação
- [ ] Suporte a mensagens de voz
- [ ] Suporte a imagens/arquivos
- [ ] Status de leitura e digitação
- [ ] Grupos do WhatsApp

**Arquivos envolvidos:**
- `src/integrations/whatsapp_integration.py` (criar)
- `src/main.py` (adaptar)

---

### 2. 🧠 Melhorias nos Agentes Existentes

#### 2.1 Calendar Agent Avançado
**Prioridade:** Média  
**Complexidade:** Baixa

- [x] Cancelamento de reuniões existentes
- [x] Listar reuniões do dia/semana
- [x] Editar reuniões (mudar hora)
- [ ] Adicionar participantes/convidados a eventos existentes
- [ ] Editar descrição de eventos
- [ ] Enviar lembretes customizados
- [ ] Integrar com múltiplas agendas
- [ ] Reuniões recorrentes
- [ ] Ver detalhes completos de um evento

**Arquivos envolvidos:**
- `src/agents/calendar_agent.py` ✅ (expandido com list/cancel/edit)
- `src/tools/calendar_tool.py` ✅ (add list_upcoming_events melhorado, get_event_details, add_attendees_to_event)

#### 2.2 Email Agent Avançado
**Prioridade:** Média  
**Complexidade:** Média

- [x] Enviar emails
- [x] Múltiplos destinatários (CC, BCC)
- [x] Ler emails recebidos (últimos N)
- [x] Buscar emails por remetente/assunto
- [ ] Responder emails existentes
- [ ] Anexar arquivos
- [ ] Templates de email
- [ ] Assinaturas customizadas
- [ ] Email threading (conversas)
- [ ] Filtros avançados (por data, não lidos) ✅ parcial

**Arquivos implementados:**
- `src/agents/email_agent.py` ✅ (expandido)
- `src/tools/email_tool.py` ✅ (IMAP + SMTP)

---

### 3. 🤖 Novos Agentes Especializados

#### 3.1 Web Search Agent
**Prioridade:** Alta  
**Complexidade:** Baixa

- [x] Integração com DuckDuckGo (grátis, sem API key)
- [x] Busca geral na web
- [x] Busca de notícias
- [x] Resumo automático de resultados com LLM
- [ ] Cache de pesquisas
- [ ] Busca de imagens
- [ ] Tradução automática de queries

**Arquivos implementados:**
- `src/agents/web_search_agent.py` ✅
- `src/tools/web_search_tool.py` ✅
- Integrado ao orchestrator e router ✅

#### 3.2 Data Analysis Agent
**Prioridade:** Média  
**Complexidade:** Alta

- [ ] Ler arquivos CSV/Excel
- [ ] Análise estatística básica
- [ ] Geração de gráficos (matplotlib/plotly)
- [ ] Exportar relatórios
- [ ] Integração com Pandas

**Arquivos a criar:**
- `src/agents/data_agent.py`
- `src/tools/data_analysis_tool.py`

#### 3.3 Task Management Agent
**Prioridade:** Média  
**Complexidade:** Média

- [ ] Criar tarefas (TODO list)
- [ ] Marcar como concluído
- [ ] Prioridades
- [ ] Deadlines
- [ ] Integração com Todoist/Notion
- [ ] Lembretes automáticos

**Arquivos a criar:**
- `src/agents/task_agent.py`
- `src/tools/task_tool.py`

#### 3.4 Code Assistant Agent
**Prioridade:** Baixa  
**Complexidade:** Alta

- [ ] Explicar código
- [ ] Gerar código a partir de descrição
- [ ] Revisar código (code review)
- [ ] Detectar bugs
- [ ] Sugerir melhorias
- [ ] Executar código Python em sandbox

**Arquivos a criar:**
- `src/agents/code_agent.py`
- `src/tools/code_execution_tool.py`

#### 3.5 Document Generator Agent
**Prioridade:** Baixa  
**Complexidade:** Média

- [ ] Gerar PDFs
- [ ] Criar apresentações (PPT)
- [ ] Gerar contratos/documentos
- [ ] Templates customizáveis
- [ ] Conversão de formatos

**Arquivos a criar:**
- `src/agents/document_agent.py`
- `src/tools/document_tool.py`

---

### 4. 🌐 Interface Web (FastAPI + Frontend)
**Prioridade:** Alta  
**Complexidade:** Alta

- [ ] API REST com FastAPI
  - [ ] Endpoints para enviar mensagens
  - [ ] Websockets para chat em tempo real
  - [ ] Autenticação JWT
  - [ ] Gerenciamento de usuários
- [ ] Frontend React/Vue
  - [ ] Chat interface
  - [ ] Histórico de conversas
  - [ ] Dashboard de métricas
  - [ ] Configurações
- [ ] Deploy
  - [ ] Docker + docker-compose
  - [ ] Nginx reverse proxy
  - [ ] SSL/HTTPS

**Arquivos a criar:**
- `src/api/` (novo diretório)
- `frontend/` (novo diretório)
- `docker-compose.yml`
- `Dockerfile`

---

### 5. ⚙️ Workflows e Automações
**Prioridade:** Média  
**Complexidade:** Alta

- [ ] Workflow engine
- [ ] Triggers automáticos (cron jobs)
- [ ] Workflows multi-step
  - [ ] Ex: "Toda segunda às 9h, buscar emails, resumir e enviar relatório"
- [ ] Integração com Kestra/n8n/Zapier
- [ ] Conditional logic avançada
- [ ] Error handling e retries

**Arquivos a criar:**
- `src/workflows/` (novo diretório)
- `src/workflows/engine.py`
- `src/workflows/triggers.py`

---

### 6. 📊 Analytics e Monitoring
**Prioridade:** Baixa  
**Complexidade:** Média

- [ ] Dashboard de métricas
  - [ ] Número de conversas
  - [ ] Tempo de resposta
  - [ ] Agentes mais usados
  - [ ] Tokens consumidos
  - [ ] Custos (OpenAI API)
- [ ] Logs estruturados (já temos structlog)
- [ ] Alertas (email/slack quando algo falha)
- [ ] Integração com Grafana/Prometheus

**Arquivos a criar:**
- `src/analytics/` (novo diretório)
- `src/analytics/metrics.py`
- `src/analytics/dashboard.py`

---

### 7. 👥 Multi-usuário e Permissões
**Prioridade:** Média  
**Complexidade:** Alta

- [ ] Sistema de usuários
  - [ ] Registro/login
  - [ ] Roles (admin, user, viewer)
  - [ ] Permissões por agente
- [ ] Múltiplas conversas simultâneas
- [ ] Isolamento de dados por usuário
- [ ] Quota de uso (limite de tokens)
- [ ] Billing/subscription

**Arquivos a criar:**
- `src/auth/` (novo diretório)
- `src/models/user.py`
- `src/middleware/auth_middleware.py`

---

### 8. 🔧 Melhorias Técnicas

#### 8.1 Testes
**Prioridade:** Alta  
**Complexidade:** Média

- [ ] Unit tests (pytest)
- [ ] Integration tests
- [ ] E2E tests
- [ ] Coverage > 80%
- [ ] CI/CD (GitHub Actions)

**Arquivos a criar:**
- `tests/` (já existe, expandir)
- `.github/workflows/test.yml`

#### 8.2 Performance
**Prioridade:** Média  
**Complexidade:** Média

- [ ] Cache de respostas (Redis)
- [ ] Async/await otimizado
- [ ] Database indexing
- [ ] Rate limiting
- [ ] Load balancing

#### 8.3 Segurança
**Prioridade:** Alta  
**Complexidade:** Média

- [ ] Input validation rigorosa
- [ ] Sanitização de outputs
- [ ] Secrets management (Vault/AWS Secrets)
- [ ] Audit logs
- [ ] OWASP compliance

---

### 9. 🌍 Internacionalização
**Prioridade:** Baixa  
**Complexidade:** Baixa

- [ ] Suporte multi-idioma
- [ ] Detecção automática de idioma
- [ ] Templates de mensagens em vários idiomas
- [ ] Tradução automática

**Arquivos a criar:**
- `src/i18n/` (novo diretório)
- `src/i18n/translations/` (JSON por idioma)

---

### 10. 📦 Extensibilidade
**Prioridade:** Baixa  
**Complexidade:** Alta

- [ ] Sistema de plugins
- [ ] Marketplace de agentes customizados
- [ ] SDK para desenvolvedores
- [ ] Documentação API completa
- [ ] Webhooks para integrações externas

---

## 🎯 Próximos Passos Sugeridos

### Sprint 1 (1-2 semanas)
1. ✅ Melhorar Email Agent (ler emails, anexos)
2. ✅ Web Search Agent
3. ✅ Testes básicos

### Sprint 2 (2-3 semanas)
4. ✅ Interface Web (FastAPI + frontend básico)
5. ✅ WhatsApp Integration real
6. ✅ Multi-usuário básico

### Sprint 3 (2-3 semanas)
7. ✅ Workflows simples
8. ✅ Analytics dashboard
9. ✅ Task Management Agent

---

## 📝 Notas

- **Prioridade:** Alta = essencial, Média = importante, Baixa = nice-to-have
- **Complexidade:** Baseada em tempo de desenvolvimento estimado
- Marque `[x]` quando implementar
- Mantenha este arquivo atualizado!

---

**Última atualização:** 4 de fevereiro de 2026
**Versão atual:** 0.1.0 (MVP funcional)
