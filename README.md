# Generic WhatsApp Chatbot

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.54-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

</div>

Um chatbot inteligente para WhatsApp com arquitetura multi-agente modular, baseado em **LangGraph** para orquestração de agentes especialistas e **Kestra** para automação de workflows. Este template foi projetado para ser facilmente personalizável, permitindo que você adicione sua própria base de conhecimento, prompts customizados e integrações específicas para criar um assistente virtual completo.

**Ideal para:** Atendimento ao cliente, suporte técnico, agendamento automático, FAQs inteligentes, assistentes virtuais corporativos.

---

## 🚀 Características Principais

### 🤖 Arquitetura Multi-Agente Inteligente
- **LangGraph State Machine**: Orquestração avançada de múltiplos agentes especialistas com contexto compartilhado
- **Roteamento Inteligente**: Sistema de routing automático baseado em análise semântica da intenção do usuário
- **Agentes Especializados**: Cada agente é otimizado para uma tarefa específica (conhecimento, agendamento, email, chat)
- **Fallback Gracioso**: Sistema de fallback para lidar com requisições fora do escopo

### 📚 Sistema de Conhecimento RAG (Retrieval-Augmented Generation)
- **Vector Database**: ChromaDB com embeddings de alta qualidade via Sentence Transformers
- **Busca Semântica**: Recuperação de informações por similaridade, não apenas keywords
- **Atualização Dinâmica**: Hot reload da base de conhecimento sem reiniciar o sistema
- **Multi-documento**: Suporte para múltiplos arquivos de conhecimento organizados por domínio

### ⚡ Automação com Kestra
- **Workflows Declarativos**: Processamento assíncrono de mensagens com retry automático
- **Scheduled Tasks**: Atualização automática de conhecimento e relatórios periódicos
- **Monitoramento Visual**: Interface web para acompanhar execuções e logs em tempo real

### 🔌 Integrações Prontas para Uso
- **Google Calendar API**: Agendamento inteligente com parsing de data/hora natural
- **SendGrid**: Envio transacional de emails com templates e tracking
- **WhatsApp Web**: Conexão via whatsapp-web.py com suporte a QR Code

### 🐳 Deploy Simplificado
- **Docker Compose**: Stack completa (app + Kestra + PostgreSQL) com um comando
- **Environment Variables**: Configuração centralizada via .env
- **Hot Reload**: Desenvolvimento com reload automático em mudanças de código

## 📋 Arquitetura de Agentes

O sistema utiliza **LangGraph** para criar um grafo de estados com múltiplos agentes especialistas que colaboram para resolver tarefas complexas:

```
┌─────────────────┐
│  User Message   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Router Agent   │ ◄─── Analisa intenção usando embeddings semânticos
└────────┬────────┘      Modelos: GPT-4o-mini
         │
         ├──────────────────┬──────────────────┬──────────────────┬─────────────────┐
         ▼                  ▼                  ▼                  ▼                 ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Knowledge   │   │   Calendar   │   │    Email     │   │ General Chat │   │   (Custom)   │
│    Agent     │   │    Agent     │   │    Agent     │   │    Agent     │   │    Agent     │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
      │                    │                    │                  │
      ▼                    ▼                    ▼                  ▼
  ChromaDB          Google Calendar       SendGrid API       OpenAI Chat
  (RAG Search)      (Events CRUD)        (Transactional)    (Conversational)
```

### Agentes Disponíveis

#### 1. **Router Agent** 🎯
- **Função**: Ponto de entrada que classifica a intenção do usuário
- **Tecnologia**: Análise semântica + classificação via LLM
- **Roteamento**: Direciona para o agente mais apropriado
- **Fallback**: Encaminha para General Chat Agent se intenção for ambígua

#### 2. **Knowledge Agent** 📖
- **Função**: Responde perguntas consultando a base de conhecimento corporativa
- **Técnica**: RAG (Retrieval-Augmented Generation) com ChromaDB
- **Features**: 
  - Top-k retrieval com reranking
  - Citação de fontes dos documentos
  - Threshold de confiança para respostas
- **Exemplo**: "Qual é a política de reembolso?" → Busca em `knowledge_base/policies.txt`

#### 3. **Calendar Agent** 📅
- **Função**: Gerencia agendamentos no Google Calendar
- **Capacidades**:
  - Criar eventos com parsing de linguagem natural ("amanhã às 14h")
  - Listar próximos compromissos
  - Verificar disponibilidade de horários
  - Enviar convites para participantes
- **Exemplo**: "Agende reunião com time de vendas na quinta-feira 10h"

#### 4. **Email Agent** 📧
- **Função**: Envia emails transacionais via SendGrid
- **Features**:
  - Validação de endereços de email
  - Suporte a templates HTML
  - Tracking de abertura/cliques
  - Attachments (futuro)
- **Exemplo**: "Envie o relatório mensal para financeiro@empresa.com"

#### 5. **General Chat Agent** 💬
- **Função**: Conversação geral, saudações e pequenas conversas
- **Personalidade**: Customizável via system prompt
- **Uso**: Fallback para interações sociais ou fora do escopo dos outros agentes
- **Exemplo**: "Bom dia!" → Resposta cordial sem acionar ferramentas

## 🛠️ Stack Tecnológico

| Categoria | Tecnologia | Versão | Propósito |
|-----------|-----------|---------|-----------|
| **Orquestração** | LangGraph | 0.2.54 | State machine para fluxo de agentes |
| **LLM Framework** | LangChain | 0.3.13 | Abstrações para trabalhar com LLMs |
| **Modelo AI** | OpenAI GPT-4o/4o-mini | Latest | Processamento de linguagem natural |
| **Vector DB** | ChromaDB | 0.5.23 | Armazenamento e busca de embeddings |
| **Embeddings** | Sentence Transformers | 3.3.1 | Geração de embeddings semânticos |
| **Workflow Engine** | Kestra | Latest | Orquestração de workflows assíncronos |
| **WhatsApp** | whatsapp-web.py | 0.2.5 | Integração com WhatsApp Web |
| **Email Service** | SendGrid | 6.11.0 | Envio transacional de emails |
| **Calendar API** | Google Calendar API | Latest | Gerenciamento de eventos |
| **Web Framework** | FastAPI | 0.115.6 | APIs REST para webhooks (futuro) |
| **Config Management** | Pydantic Settings | 2.7.0 | Validação de configurações |
| **Logging** | structlog | 24.4.0 | Logs estruturados em JSON |
| **Testing** | pytest | 8.3.4 | Framework de testes unitários |
| **Container** | Docker + Compose | Latest | Containerização e orquestração |

### Por que estas tecnologias?

- **LangGraph**: Permite criar fluxos complexos de agentes com estado compartilhado, superior ao LangChain LCEL para casos multi-agente
- **ChromaDB**: Vector database leve e eficiente, ideal para RAG em produção sem overhead de infraestrutura
- **Kestra**: Workflow engine moderno com UI visual, perfeito para orquestrar tarefas assíncronas e scheduled jobs
- **Pydantic**: Validação rigorosa de tipos e configurações, reduz bugs em runtime
- **structlog**: Logs estruturados facilitam debugging e integração com ferramentas de observabilidade

## 📦 Instalação e Setup

### 🔧 Pré-requisitos

| Requisito | Versão Mínima | Obrigatório? | Nota |
|-----------|---------------|--------------|------|
| Python | 3.11+ | ✅ Sim | Use `python3.11` ou superior |
| pip | Latest | ✅ Sim | Para instalar dependências |
| Docker | 20.x+ | ⚠️ Recomendado | Para deploy com Kestra |
| Docker Compose | 2.x+ | ⚠️ Recomendado | Para stack completa |
| OpenAI API Key | - | ✅ Sim | [Obter aqui](https://platform.openai.com/api-keys) |
| SendGrid API Key | - | ❌ Opcional | Apenas para funcionalidade de email |
| Google Cloud Project | - | ❌ Opcional | Apenas para Google Calendar |

### ⚡ Setup Rápido (5 minutos)

A maneira mais rápida de começar é usando o script de setup automatizado:

```bash
# 1. Clone o repositório
git clone https://github.com/cassio-all/generic-wpp-chatbot.git
cd generic-wpp-chatbot

# 2. Execute o setup automatizado
./setup.sh

# 3. Configure suas credenciais
nano .env  # Adicione pelo menos OPENAI_API_KEY

# 4. Ative o ambiente virtual e execute
source venv/bin/activate
python -m src.main
```

O script `setup.sh` faz automaticamente:
- ✅ Verifica versão do Python
- ✅ Cria ambiente virtual (venv)
- ✅ Instala todas as dependências do `requirements.txt`
- ✅ Cria estrutura de diretórios necessária
- ✅ Copia `.env.example` para `.env` se não existir

---

### 🐍 Instalação Manual (Passo a Passo)

Se preferir fazer manualmente ou entender cada etapa:

```bash
# 1. Clone o repositório
git clone https://github.com/cassio-all/generic-wpp-chatbot.git
cd generic-wpp-chatbot
```

# 2. Verifique a versão do Python
python3 --version  # Deve ser 3.11 ou superior

# 3. Crie e ative ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# No Windows: venv\Scripts\activate

# 4. Atualize pip
pip install --upgrade pip

# 5. Instale dependências
pip install -r requirements.txt

# 6. Configure variáveis de ambiente
cp .env.example .env
nano .env  # Ou use seu editor preferido

# 7. Crie diretórios necessários (se não existirem)
mkdir -p credentials data knowledge_base logs

# 8. Execute em modo CLI para testes
python -m src.main
```

**Troubleshooting Instalação:**
- ❌ `python: command not found` → Instale Python 3.11+
- ❌ `pip: No module named venv` → Execute `apt install python3-venv` (Ubuntu/Debian)
- ❌ Erro ao instalar requirements → Verifique se pip está atualizado: `pip install --upgrade pip`

---

### 🐳 Instalação com Docker (Recomendado para Produção)

Docker Compose orquestra toda a stack (app + Kestra + PostgreSQL):

```bash
# 1. Configure o .env primeiro
cp .env.example .env
nano .env  # Adicione pelo menos OPENAI_API_KEY

# 2. Build e start de todos os serviços
docker-compose up -d

# 3. Verifique status dos containers
docker-compose ps

# 4. Visualize logs em tempo real
docker-compose logs -f app

# 5. Acesse interfaces web
# - Kestra UI: http://localhost:8080
# - API (futuro): http://localhost:8000
```

**Serviços incluídos no docker-compose:**
- 🤖 **app**: Aplicação principal do chatbot
- 🔄 **kestra**: Workflow engine para automação
- 🗄️ **postgres**: Banco de dados do Kestra
- 📁 **volumes**: Persistência de dados (vector_db, credentials, logs)

**Comandos úteis Docker:**
```bash
# Parar todos os serviços
docker-compose down

# Rebuild após mudanças no código
docker-compose up -d --build

# Ver logs de um serviço específico
docker-compose logs -f kestra

# Entrar no container para debugging
docker-compose exec app bash

# Limpar volumes (atenção: apaga dados!)
docker-compose down -v
```

## ⚙️ Configuração Detalhada

### 🔑 OpenAI API (Obrigatório)

```bash
# .env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Como obter:**
1. Acesse [OpenAI Platform](https://platform.openai.com/api-keys)
2. Faça login ou crie uma conta
3. Vá em "API Keys" → "Create new secret key"
4. Copie a chave (ela só é mostrada uma vez!)
5. Cole no seu `.env`

**Modelos utilizados:**
- `gpt-4o`: Para tarefas complexas (Router, Knowledge Agent)
- `gpt-4o-mini`: Para tarefas simples (General Chat) - mais barato
- Embeddings: `text-embedding-3-small` (via ChromaDB)

**Custos estimados (USD):**
- 1000 mensagens/dia: ~$5-10/mês
- 10000 mensagens/dia: ~$50-100/mês

> 💡 **Dica**: Use `gpt-4o-mini` para desenvolvimento e testes - é 10x mais barato

---

### 📧 SendGrid (Opcional - Para Email Agent)

```bash
# .env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxx
SENDER_EMAIL=noreply@seudominio.com
```

**Setup completo:**

1. **Crie conta SendGrid**
   - Acesse [SendGrid](https://signup.sendgrid.com/)
   - Plano gratuito: 100 emails/dia

2. **Gere API Key**
   ```
   Dashboard → Settings → API Keys → Create API Key
   - Name: "WhatsApp Chatbot"
   - Permissions: Full Access
   ```

3. **Verifique domínio (recomendado)**
   ```
   Settings → Sender Authentication → Domain Authentication
   - Adicione registros DNS do seu domínio
   - Melhora deliverability e evita spam
   ```

4. **Teste a integração**
   ```bash
   python -c "
   from src.tools.email_tool import send_email
   send_email(
       to='seu-email@teste.com',
       subject='Teste SendGrid',
       body='Se você recebeu isso, está funcionando!'
   )
   "
   ```

**Troubleshooting:**
- ❌ Email não chega → Verifique spam, autenticação de domínio
- ❌ 401 Unauthorized → API key incorreta ou expirada
- ❌ 403 Forbidden → Conta SendGrid bloqueada (verifique email deles)

---

### 📅 Google Calendar (Opcional - Para Calendar Agent)

```bash
# .env
GOOGLE_CALENDAR_CREDENTIALS_PATH=./credentials/google_calendar_credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=./credentials/token.json
```

**Setup completo (10-15 minutos):**

#### 1. Criar Projeto no Google Cloud

```
1. Acesse: https://console.cloud.google.com/
2. Clique em "Select a project" → "New Project"
3. Nome: "WhatsApp Chatbot" → Create
4. Aguarde criação (~30s)
```

#### 2. Ativar Google Calendar API

```
1. No menu lateral: APIs & Services → Library
2. Busque: "Google Calendar API"
3. Clique em "Enable"
```

#### 3. Criar Credenciais OAuth 2.0

```
1. APIs & Services → Credentials → Create Credentials
2. Selecione: "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "WhatsApp Bot Desktop"
5. Download JSON → Salve como credentials/google_calendar_credentials.json
```

#### 4. Autorizar Acesso (primeira vez)

```bash
# Execute o bot
python -m src.main

# Uma janela do navegador abrirá automaticamente
# 1. Selecione sua conta Google
# 2. Clique em "Allow" para dar permissões
# 3. Token será salvo em credentials/token.json
```

**Estrutura esperada de arquivos:**
```
credentials/
├── google_calendar_credentials.json  # ← Download do Google Cloud
└── token.json                        # ← Gerado automaticamente na primeira auth
```

**Permissões necessárias:**
- `https://www.googleapis.com/auth/calendar` - Ler/escrever eventos
- `https://www.googleapis.com/auth/calendar.events` - Gerenciar eventos

**Troubleshooting:**
- ❌ `FileNotFoundError` → Verifique caminho em `.env` e se arquivo existe
- ❌ `RefreshError` → Delete `token.json` e autorize novamente
- ❌ `Access blocked` → Adicione email de teste em OAuth consent screen
- ❌ Eventos não aparecem → Verifique se está usando calendar correto (ID)

---

## 📚 Construindo sua Base de Conhecimento

A base de conhecimento usa **RAG (Retrieval-Augmented Generation)** com ChromaDB para busca semântica.

### 🏗️ Estrutura Recomendada

```
knowledge_base/
├── company/
│   ├── about.txt              # História, missão, valores
│   ├── products.txt           # Catálogo de produtos/serviços
│   └── team.txt               # Equipe e contatos
├── support/
│   ├── faq.txt                # Perguntas frequentes
│   ├── troubleshooting.txt    # Solução de problemas comuns
│   └── tutorials.txt          # Guias passo a passo
├── policies/
│   ├── privacy.txt            # Política de privacidade
│   ├── terms.txt              # Termos de uso
│   ├── refund.txt             # Política de reembolso
│   └── shipping.txt           # Política de envio
└── sales/
    ├── pricing.txt            # Tabela de preços
    ├── promotions.txt         # Promoções ativas
    └── catalog.txt            # Catálogo detalhado
```

### ✍️ Formatação de Documentos

**Exemplo: `knowledge_base/support/faq.txt`**

```markdown
# FAQ - Perguntas Frequentes

## Como faço para cancelar minha assinatura?
Para cancelar sua assinatura:
1. Acesse Minha Conta → Assinaturas
2. Clique em "Cancelar Assinatura"
3. Confirme o cancelamento
Não há multa para cancelamento. O acesso permanece até o fim do período pago.

## Qual é o prazo de entrega?
Nossos prazos de entrega variam por região:
- Capitais: 3-5 dias úteis
- Interior: 7-10 dias úteis
- Norte/Nordeste: 10-15 dias úteis
Frete expresso disponível para entregas em 24-48h.

## Vocês emitem nota fiscal?
Sim, emitimos nota fiscal eletrônica (NF-e) para todas as compras.
A nota é enviada automaticamente para o email cadastrado em até 48h após confirmação do pagamento.
```

**Dicas de escrita:**
- ✅ Seja específico e objetivo
- ✅ Use linguagem natural (como as pessoas perguntariam)
- ✅ Inclua números, datas, valores concretos
- ✅ Organize em seções com cabeçalhos
- ✅ Cite fontes de autoridade quando aplicável
- ❌ Evite informações genéricas ou vagas
- ❌ Não use apenas keywords (busca é semântica!)

### 🔄 Atualizando a Base de Conhecimento

#### Método 1: Hot Reload (Manual)

```bash
# 1. Adicione/edite arquivos em knowledge_base/
echo "Nova informação importante" >> knowledge_base/company/about.txt

# 2. Force rebuild do vector database
rm -rf data/vector_db

# 3. Restart o bot (recria índice automaticamente)
python -m src.main
```

#### Método 2: Kestra Workflow (Automático)

```yaml
# O workflow knowledge-base-update.yml atualiza automaticamente:
# - Execução: Diária às 2h AM
# - Monitora mudanças em knowledge_base/
# - Rebuild automático se detectar alterações
# - Notifica no log/Slack (se configurado)
```

#### Método 3: API Endpoint (Futuro)

```bash
# POST /api/knowledge/reload
curl -X POST http://localhost:8000/api/knowledge/reload \
  -H "Authorization: Bearer TOKEN"
```

### 📊 Boas Práticas

1. **Chunk Size**: Documentos são divididos em chunks (~500 tokens)
   - Muito pequeno → Perde contexto
   - Muito grande → Busca imprecisa
   - Ideal: 1-3 parágrafos por tópico

2. **Redundância Estratégica**: Repita informações críticas em múltiplos documentos
   ```
   pricing.txt: "Plano Pro custa R$ 99/mês"
   faq.txt: "O Plano Pro custa R$ 99/mês e inclui..."
   ```

3. **Versionamento**: Use Git para rastrear mudanças
   ```bash
   git add knowledge_base/
   git commit -m "feat: adiciona política de devolução atualizada"
   ```

4. **Testes**: Pergunte ao bot após adicionar conhecimento
   ```
   Você: Qual é nossa política de devolução?
   [Verifique se resposta está correta e completa]
   ```

### 🔍 Verificando Qualidade da Base

```python
# Script para testar retrieval
from src.services.knowledge_base import KnowledgeBase

kb = KnowledgeBase()
results = kb.search("política de cancelamento", top_k=3)

for doc, score in results:
    print(f"Score: {score:.2f}")
    print(f"Conteúdo: {doc.page_content[:200]}...")
    print(f"Fonte: {doc.metadata['source']}")
    print("---")
```

**Métricas de qualidade:**
- Similarity score > 0.7 → Resultado muito relevante
- Similarity score 0.5-0.7 → Resultado relevante
- Similarity score < 0.5 → Resultado questionável

---

## 🔄 Workflows Kestra

O Kestra automatiza tarefas recorrentes e processamento assíncrono de mensagens. Todos os workflows estão em `kestra/flows/`.

### 📋 Workflows Incluídos

#### 1. `whatsapp-chatbot-main.yml` - Processamento Principal
**Função**: Processa mensagens do WhatsApp através da orquestração de agentes

```yaml
triggers:
  - type: io.kestra.core.models.triggers.types.Webhook
    # Recebe webhook do WhatsApp quando nova mensagem chega
    
flow:
  1. Recebe mensagem → Valida formato
  2. Envia para Router Agent → Determina intenção
  3. Processa com agente específico → Gera resposta
  4. Envia resposta via WhatsApp API
  5. Log resultado (sucesso/erro)
```

**Features:**
- ✅ Retry automático em caso de falha (3 tentativas)
- ✅ Dead letter queue para mensagens com erro persistente
- ✅ Timeout de 30s por mensagem
- ✅ Rate limiting para evitar sobrecarga

**Métricas visualizáveis:**
- Taxa de sucesso/erro
- Tempo médio de resposta
- Distribuição de intenções (qual agente mais usado)

---

#### 2. `knowledge-base-update.yml` - Atualização de Conhecimento
**Função**: Atualiza automaticamente o vector database quando arquivos mudam

```yaml
schedule:
  - cron: "0 2 * * *"  # Diariamente às 2h AM
  
flow:
  1. Verifica checksums dos arquivos em knowledge_base/
  2. Se houver mudanças:
     a. Backup do vector_db anterior
     b. Rebuild completo do índice ChromaDB
     c. Valida integridade (testa queries)
     d. Notifica sucesso/falha
  3. Cleanup de backups antigos (mantém últimos 7 dias)
```

**Uso:**
- Permite atualizar conhecimento sem downtime
- Útil para empresas que atualizam catálogos/preços frequentemente
- Pode ser triggerado manualmente via UI

---

#### 3. `scheduled-reports.yml` - Relatórios Automáticos
**Função**: Envia relatórios diários de uso do chatbot

```yaml
schedule:
  - cron: "0 9 * * 1-5"  # Segunda a Sexta às 9h
  
flow:
  1. Coleta métricas das últimas 24h:
     - Total de mensagens processadas
     - Breakdown por tipo de agente
     - Taxa de sucesso/erro
     - Tempo médio de resposta
  2. Gera relatório em formato HTML
  3. Envia email via SendGrid para stakeholders
```

**Métricas incluídas:**
```
📊 Relatório Diário - WhatsApp Chatbot
Data: 03/02/2026

Total de mensagens: 247
├─ Knowledge Agent: 112 (45%)
├─ General Chat: 89 (36%)
├─ Calendar Agent: 31 (13%)
└─ Email Agent: 15 (6%)

Taxa de sucesso: 97.6%
Tempo médio de resposta: 1.8s
Pico de uso: 14h-16h (68 msgs)
```

---

### 🎛️ Gerenciando Workflows no Kestra UI

**Acessar UI:**
```bash
# Local
http://localhost:8080

# Docker
docker-compose logs kestra  # Verificar se subiu
```

**Interface principal:**

1. **Flows**: Visualizar todos os workflows
   - Editar YAML inline
   - Testar execução manual
   - Ver histórico de runs

2. **Executions**: Histórico de execuções
   - Status (Success/Failed/Running)
   - Logs detalhados por task
   - Output de cada step
   - Replay de execuções falhadas

3. **Triggers**: Gerenciar triggers
   - Enable/Disable workflows
   - Configurar schedules
   - Testar webhooks

4. **Logs**: Logs centralizados
   - Filtrar por flow/execution
   - Busca full-text
   - Export para análise

**Comandos úteis:**

```bash
# Trigger manual via CLI
curl -X POST http://localhost:8080/api/v1/executions/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "whatsapp-chatbot",
    "flowId": "knowledge-base-update"
  }'

# Listar execuções recentes
curl http://localhost:8080/api/v1/executions?namespace=whatsapp-chatbot

# Ver logs de uma execução específica
curl http://localhost:8080/api/v1/executions/{executionId}/logs
```

---

### ➕ Criando Novos Workflows

**Exemplo: Backup Automático**

```yaml
# kestra/flows/daily-backup.yml
id: daily-backup
namespace: whatsapp-chatbot
description: Backup diário de dados críticos

tasks:
  - id: backup-vector-db
    type: io.kestra.core.tasks.scripts.Bash
    script: |
      DATE=$(date +%Y%m%d)
      tar -czf /backups/vector_db_$DATE.tar.gz /app/data/vector_db
      
  - id: backup-logs
    type: io.kestra.core.tasks.scripts.Bash
    script: |
      DATE=$(date +%Y%m%d)
      tar -czf /backups/logs_$DATE.tar.gz /app/logs
      
  - id: cleanup-old-backups
    type: io.kestra.core.tasks.scripts.Bash
    script: |
      find /backups -name "*.tar.gz" -mtime +30 -delete

triggers:
  - id: daily-schedule
    type: io.kestra.core.models.triggers.types.Schedule
    cron: "0 3 * * *"  # 3h AM diariamente
```

**Deploy do workflow:**
1. Salve em `kestra/flows/`
2. Restart Kestra: `docker-compose restart kestra`
3. Workflow aparece automaticamente na UI

---

## 📱 Usando o Chatbot

### 🖥️ Modo CLI (Desenvolvimento e Testes)

Ideal para testar localmente sem conectar ao WhatsApp:

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute em modo CLI
python -m src.main

# Interface interativa:
# ┌─────────────────────────────────────┐
# │ WhatsApp Chatbot - CLI Mode        │
# │ Digite 'sair' para encerrar        │
# └─────────────────────────────────────┘
# 
# Você: 
```

**Comandos especiais CLI:**
- `sair` ou `exit` - Encerra o bot
- `limpar` ou `clear` - Limpa histórico da conversa
- `debug` - Ativa modo debug verbose
- `status` - Mostra status dos agentes e base de conhecimento

---

### 💬 Exemplos de Interação

#### 1. Consulta de Conhecimento (Knowledge Agent)

```
Você: Quais produtos vocês oferecem?

Bot: 🤖 Baseado em nossa base de conhecimento:

Oferecemos 3 linhas principais de produtos:

1. **Plano Básico** (R$ 49/mês)
   - Até 100 mensagens/dia
   - Base de conhecimento básica
   - Suporte por email

2. **Plano Pro** (R$ 99/mês)  
   - Mensagens ilimitadas
   - Integrações avançadas
   - Suporte prioritário 24/7

3. **Plano Enterprise** (Sob consulta)
   - Customização completa
   - SLA garantido
   - Onboarding dedicado

📄 Fonte: knowledge_base/products.txt
```

#### 2. Agendamento (Calendar Agent)

```
Você: Preciso agendar uma reunião de alinhamento com o time comercial 
      na próxima quinta-feira às 14h. Duração de 1 hora.

Bot: ✅ Reunião agendada com sucesso!

📅 **Detalhes:**
- Título: Reunião de alinhamento - Time Comercial
- Data: 06/02/2026 (quinta-feira)
- Horário: 14:00 - 15:00
- Local: Google Meet (link gerado automaticamente)

📧 Convite enviado para:
- comercial@empresa.com
- gerente@empresa.com

🔗 Link da reunião: meet.google.com/abc-defg-hij
```

#### 3. Envio de Email (Email Agent)

```
Você: Envia um email para contato@cliente.com com assunto "Proposta Comercial" 
      e texto "Conforme solicitado, segue proposta em anexo"

Bot: ✅ E-mail enviado com sucesso!

📧 **Confirmação:**
- Para: contato@cliente.com
- Assunto: Proposta Comercial
- Enviado em: 03/02/2026 15:32
- Status: Delivered
- ID Rastreamento: SG.abc123def456

💡 O destinatário será notificado quando abrir o email.
```

#### 4. Conversa Geral (General Chat Agent)

```
Você: Bom dia! Como você está?

Bot: Bom dia! 😊 Estou ótimo, obrigado por perguntar! 

Estou aqui para ajudá-lo com:
- 📚 Informações sobre produtos e serviços
- 📅 Agendamento de reuniões
- 📧 Envio de emails
- 💬 Dúvidas gerais

Como posso ajudar você hoje?
```

#### 5. Consulta Complexa (Múltiplos Agentes)

```
Você: Qual é a política de cancelamento? Se eu quiser cancelar hoje,
      quanto tempo tenho para solicitar reembolso?

Bot: 📋 Sobre cancelamentos e reembolsos:

**Política de Cancelamento:**
- Você pode cancelar a qualquer momento, sem multa
- O acesso permanece ativo até o fim do período pago
- Não há renovação automática após cancelamento

**Reembolso:**
- Solicitações dentro de 7 dias da compra: reembolso integral
- Solicitações entre 8-14 dias: reembolso parcial (50%)
- Após 15 dias: sem direito a reembolso

Para cancelar e solicitar reembolso:
1. Acesse: Minha Conta → Assinaturas
2. Clique em "Cancelar e Solicitar Reembolso"
3. Preencha o motivo (opcional)

Posso agendar uma ligação com nosso suporte para ajudar 
com o processo? 📞

📄 Fonte: knowledge_base/policies/refund.txt
```

---

### 📊 Interpretando Respostas

O bot fornece metadados úteis:

**Indicadores de fonte:**
- 📄 `Fonte: knowledge_base/...` - Resposta baseada em documentos
- 🤖 `Baseado em:` - Inferência do LLM (pode ser menos preciso)
- ✅ `Confirmação:` - Ação executada com sucesso
- ⚠️ `Atenção:` - Avisos ou limitações

**Níveis de confiança (Knowledge Agent):**
- Alta (>0.8): Resposta muito precisa
- Média (0.6-0.8): Resposta relevante, mas verifique
- Baixa (<0.6): "Não encontrei informações sobre isso..."

---

### 🔧 Troubleshooting de Interações

**Bot não responde:**
```bash
# Verifique se OpenAI API está configurada
cat .env | grep OPENAI_API_KEY

# Veja logs para erros
tail -f logs/app.log

# Teste conexão com OpenAI
python -c "
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': 'test'}]
)
print('Conexão OK!')
"
```

**Respostas genéricas demais:**
- Verifique se knowledge_base/ tem conteúdo
- Rebuild vector database: `rm -rf data/vector_db && python -m src.main`
- Ajuste similarity threshold em `src/services/knowledge_base.py`

**Agendamentos não funcionam:**
- Verifique credenciais Google Calendar em `credentials/`
- Delete `token.json` e reautorize
- Confirme que Calendar API está ativada no Google Cloud

**Emails não chegam:**
- Verifique SendGrid API key no `.env`
- Confirme que domínio está autenticado no SendGrid
- Cheque se email caiu no spam

---

## 🔧 Customização e Extensão

### 🎨 Personalizando Prompts dos Agentes

Cada agente tem um system prompt que define sua personalidade e comportamento:

#### Knowledge Agent
Arquivo: [src/agents/knowledge_agent.py](src/agents/knowledge_agent.py)

```python
# Encontre a variável SYSTEM_PROMPT e customize:

SYSTEM_PROMPT = """
Você é um assistente especializado da EMPRESA X.

Personalidade:
- Profissional mas amigável
- Focado em resolver problemas rapidamente
- Usa emojis moderadamente (máximo 2 por mensagem)

Diretrizes:
1. Sempre cite a fonte do conhecimento
2. Se não tiver 80%+ de certeza, peça esclarecimento
3. Sugira próximos passos quando apropriado
4. Nunca invente informações - use apenas a base de conhecimento

Formato de resposta:
- Use bullet points para listas
- Destaque informações importantes com **negrito**
- Inclua links quando relevante
"""
```

#### Router Agent  
Arquivo: [src/agents/router_agent.py](src/agents/router_agent.py)

```python
# Customize intenções reconhecidas:

INTENTS = {
    "knowledge": [
        "informações", "sobre", "como", "qual", "quais",
        "preço", "produto", "serviço", "política"
    ],
    "calendar": [
        "agenda", "reunião", "meeting", "marcar", "agendar",
        "disponibilidade", "horário livre"
    ],
    "email": [
        "enviar email", "mandar mensagem", "email para",
        "notificar", "avisar por email"
    ],
    # Adicione novos agentes aqui
    "custom_agent": ["keyword1", "keyword2"]
}
```

#### General Chat Agent
Arquivo: [src/agents/general_chat_agent.py](src/agents/general_chat_agent.py)

```python
# Defina a "marca" do seu bot:

SYSTEM_PROMPT = """
Você é Alex, assistente virtual da TechCorp Brasil.

Estilo de comunicação:
- Informal mas respeitoso (tutear)
- Entusiasta de tecnologia
- Paciente com iniciantes
- Usa gírias tech moderadamente

Saudações:
- Manhã: "Bom dia! ☀️"
- Tarde: "Boa tarde! 🌤️"
- Noite: "Boa noite! 🌙"

Sempre termine oferecendo ajuda adicional.
"""
```

---

### ➕ Adicionando Novos Agentes

**Passo a passo para criar um agente de Suporte Técnico:**

#### 1. Crie o arquivo do agente

```python
# src/agents/tech_support_agent.py

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from .state import AgentState

SYSTEM_PROMPT = """
Você é um especialista em suporte técnico.
Diagnostica problemas e fornece soluções passo a passo.
"""

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

def tech_support_agent(state: AgentState) -> AgentState:
    """
    Agente especializado em troubleshooting técnico.
    """
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state["user_input"])
    ]
    
    # Aqui você pode adicionar ferramentas específicas
    # Ex: consultar logs, rodar diagnósticos, etc.
    
    response = llm.invoke(messages)
    
    return {
        **state,
        "output": response.content,
        "agent_used": "tech_support"
    }
```

#### 2. Registre o agente no Orchestrator

```python
# src/agents/orchestrator.py

from .tech_support_agent import tech_support_agent

# Adicione no grafo
workflow.add_node("tech_support", tech_support_agent)

# Adicione na lógica de roteamento
def route_to_agent(state: AgentState) -> str:
    intent = state.get("intent", "")
    
    if intent == "tech_support":
        return "tech_support"
    # ... outros casos
```

#### 3. Atualize o Router

```python
# src/agents/router_agent.py

INTENTS = {
    # ... existentes
    "tech_support": [
        "erro", "bug", "problema", "não funciona",
        "travou", "lento", "crash", "como resolver"
    ]
}
```

#### 4. Teste o novo agente

```bash
python -m src.main

# Teste:
Você: Meu app está travando ao abrir, como resolver?
Bot: [Resposta do Tech Support Agent]
```

---

### 🔌 Adicionando Novas Ferramentas (Tools)

**Exemplo: Integração com API de CRM**

#### 1. Crie a ferramenta

```python
# src/tools/crm_tool.py

import httpx
from typing import Dict, Optional
import os

CRM_API_URL = os.getenv("CRM_API_URL", "https://api.crm.com/v1")
CRM_API_KEY = os.getenv("CRM_API_KEY")

async def get_customer_info(email: str) -> Optional[Dict]:
    """
    Busca informações de cliente no CRM.
    
    Args:
        email: Email do cliente
        
    Returns:
        Dict com dados do cliente ou None se não encontrado
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CRM_API_URL}/customers",
            params={"email": email},
            headers={"Authorization": f"Bearer {CRM_API_KEY}"}
        )
        
        if response.status_code == 200:
            return response.json()
        return None

async def create_ticket(
    customer_email: str,
    subject: str,
    description: str,
    priority: str = "medium"
) -> Dict:
    """
    Cria um ticket de suporte no CRM.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CRM_API_URL}/tickets",
            json={
                "customer_email": customer_email,
                "subject": subject,
                "description": description,
                "priority": priority
            },
            headers={"Authorization": f"Bearer {CRM_API_KEY}"}
        )
        
        return response.json()
```

#### 2. Integre com um agente

```python
# src/agents/support_agent.py

from ..tools.crm_tool import get_customer_info, create_ticket

async def support_agent(state: AgentState) -> AgentState:
    user_email = state.get("user_email")
    
    # Busca histórico do cliente
    customer = await get_customer_info(user_email)
    
    if customer:
        context = f"""
        Cliente: {customer['name']}
        Plano: {customer['plan']}
        Tickets anteriores: {len(customer['tickets'])}
        """
    else:
        context = "Cliente novo, sem histórico."
    
    # Processa com contexto enriquecido
    messages = [
        SystemMessage(content=f"Contexto do cliente:\n{context}"),
        HumanMessage(content=state["user_input"])
    ]
    
    response = llm.invoke(messages)
    
    # Se necessário, cria ticket
    if "criar ticket" in state["user_input"].lower():
        ticket = await create_ticket(
            customer_email=user_email,
            subject="Solicitação via WhatsApp",
            description=state["user_input"]
        )
        response.content += f"\n\n✅ Ticket #{ticket['id']} criado!"
    
    return {
        **state,
        "output": response.content,
        "agent_used": "support"
    }
```

#### 3. Configure variáveis de ambiente

```bash
# .env
CRM_API_URL=https://api.seu-crm.com/v1
CRM_API_KEY=crm_xxx_your_key_here
```

---

### 🎯 Customizações Avançadas

#### Multi-idioma

```python
# src/config/languages.py

PROMPTS = {
    "pt-BR": {
        "greeting": "Olá! Como posso ajudar?",
        "error": "Desculpe, ocorreu um erro.",
    },
    "en-US": {
        "greeting": "Hello! How can I help?",
        "error": "Sorry, an error occurred.",
    },
    "es-ES": {
        "greeting": "¡Hola! ¿Cómo puedo ayudar?",
        "error": "Lo siento, ocurrió un error.",
    }
}

def get_prompt(key: str, lang: str = "pt-BR") -> str:
    return PROMPTS.get(lang, PROMPTS["pt-BR"]).get(key)
```

#### Context Windows & Memory

```python
# src/agents/state.py

from typing import List, Dict

class ConversationMemory:
    """Gerencia histórico de conversas por usuário."""
    
    def __init__(self, max_messages: int = 10):
        self.memories: Dict[str, List] = {}
        self.max_messages = max_messages
    
    def add_message(self, user_id: str, role: str, content: str):
        if user_id not in self.memories:
            self.memories[user_id] = []
        
        self.memories[user_id].append({
            "role": role,
            "content": content
        })
        
        # Mantém apenas últimas N mensagens
        if len(self.memories[user_id]) > self.max_messages:
            self.memories[user_id] = self.memories[user_id][-self.max_messages:]
    
    def get_history(self, user_id: str) -> List[Dict]:
        return self.memories.get(user_id, [])
```

#### Rate Limiting

```python
# src/middleware/rate_limit.py

from functools import wraps
from time import time
from typing import Dict

class RateLimiter:
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window  # segundos
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, user_id: str) -> bool:
        now = time()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove requests fora da janela
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True

# Uso:
rate_limiter = RateLimiter(max_requests=20, window=60)

def handle_message(user_id: str, message: str):
    if not rate_limiter.is_allowed(user_id):
        return "⚠️ Você está enviando mensagens muito rápido. Aguarde um momento."
    
    # Processa normalmente
    return process_message(message)
```

---

## 🧪 Testes e Qualidade

### 🔬 Executando Testes

O projeto usa **pytest** para testes automatizados:

```bash
# Ativa ambiente virtual
source venv/bin/activate

# Executa todos os testes
pytest

# Executa com coverage report
pytest --cov=src --cov-report=html

# Executa testes específicos
pytest tests/test_agents.py
pytest tests/test_tools.py::test_calendar_integration

# Modo verbose para debug
pytest -v -s

# Apenas testes marcados (ex: @pytest.mark.slow)
pytest -m "not slow"
```

---

### 📊 Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py                 # Fixtures compartilhadas
├── test_agents.py             # Testes dos agentes
├── test_tools.py              # Testes de integrações
├── test_knowledge_base.py     # Testes de RAG
└── integration/
    ├── test_e2e.py            # Testes end-to-end
    └── test_workflows.py      # Testes de Kestra workflows
```

---

### ✅ Categorias de Testes

#### 1. Testes Unitários (Agentes)

```python
# tests/test_agents.py

import pytest
from src.agents.knowledge_agent import knowledge_agent
from src.agents.state import AgentState

def test_knowledge_agent_responds_correctly():
    """Testa se Knowledge Agent retorna resposta válida."""
    state = AgentState(
        user_input="Quais são os produtos disponíveis?",
        intent="knowledge"
    )
    
    result = knowledge_agent(state)
    
    assert result["output"] is not None
    assert len(result["output"]) > 0
    assert result["agent_used"] == "knowledge"

def test_router_agent_classifies_intent():
    """Testa classificação de intenção pelo Router."""
    from src.agents.router_agent import router_agent
    
    test_cases = [
        ("Quero agendar uma reunião", "calendar"),
        ("Envie um email", "email"),
        ("Olá!", "general_chat"),
        ("Quanto custa o plano Pro?", "knowledge")
    ]
    
    for input_text, expected_intent in test_cases:
        state = AgentState(user_input=input_text)
        result = router_agent(state)
        assert result["intent"] == expected_intent
```

#### 2. Testes de Integração (Ferramentas)

```python
# tests/test_tools.py

import pytest
from src.tools.email_tool import send_email
from src.tools.calendar_tool import create_event

@pytest.mark.skipif(
    not os.getenv("SENDGRID_API_KEY"),
    reason="SendGrid não configurado"
)
def test_sendgrid_integration():
    """Testa envio real de email via SendGrid."""
    result = send_email(
        to="test@example.com",
        subject="Test Email",
        body="This is a test"
    )
    
    assert result["status"] == "sent"
    assert "message_id" in result

@pytest.mark.skipif(
    not os.path.exists("credentials/google_calendar_credentials.json"),
    reason="Google Calendar não configurado"
)
def test_google_calendar_integration():
    """Testa criação de evento no Google Calendar."""
    event = create_event(
        summary="Test Meeting",
        start_time="2026-02-10T14:00:00",
        end_time="2026-02-10T15:00:00"
    )
    
    assert event["id"] is not None
    assert event["status"] == "confirmed"
```

#### 3. Testes de RAG (Base de Conhecimento)

```python
# tests/test_knowledge_base.py

import pytest
from src.services.knowledge_base import KnowledgeBase

@pytest.fixture
def knowledge_base():
    """Fixture para instanciar Knowledge Base."""
    return KnowledgeBase()

def test_knowledge_base_initialization(knowledge_base):
    """Testa se base de conhecimento inicializa corretamente."""
    assert knowledge_base.vectorstore is not None
    assert knowledge_base.retriever is not None

def test_knowledge_base_retrieval(knowledge_base):
    """Testa busca semântica na base."""
    query = "política de cancelamento"
    results = knowledge_base.search(query, top_k=3)
    
    assert len(results) > 0
    assert results[0][1] > 0.5  # Score > 0.5
    
    # Verifica metadata
    doc, score = results[0]
    assert "source" in doc.metadata

def test_knowledge_base_handles_empty_query(knowledge_base):
    """Testa comportamento com query vazia."""
    results = knowledge_base.search("", top_k=3)
    assert len(results) == 0
```

#### 4. Testes End-to-End

```python
# tests/integration/test_e2e.py

import pytest
from src.agents.orchestrator import run_chatbot

def test_full_conversation_flow():
    """Testa fluxo completo de conversa."""
    test_messages = [
        "Olá, tudo bem?",
        "Quais produtos vocês têm?",
        "Quanto custa o Plano Pro?",
        "Obrigado!"
    ]
    
    for message in test_messages:
        response = run_chatbot(message)
        
        assert response is not None
        assert len(response) > 0
        assert not response.startswith("Error")

def test_knowledge_to_action_flow():
    """Testa fluxo: pergunta → conhecimento → ação."""
    # 1. Pergunta sobre produto
    response1 = run_chatbot("Me fale sobre o Plano Pro")
    assert "Plano Pro" in response1
    
    # 2. Solicita ação baseada no conhecimento
    response2 = run_chatbot("Quero agendar uma demo desse plano")
    assert "agendar" in response2.lower() or "reunião" in response2.lower()
```

---

### 🎭 Mocking e Fixtures

```python
# tests/conftest.py

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_openai():
    """Mock da API OpenAI para testes rápidos."""
    with patch('openai.ChatCompletion.create') as mock:
        mock.return_value = {
            "choices": [{
                "message": {
                    "content": "Mocked response"
                }
            }]
        }
        yield mock

@pytest.fixture
def sample_knowledge_files(tmp_path):
    """Cria arquivos temporários de conhecimento para testes."""
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    
    (kb_dir / "products.txt").write_text("""
    Plano Básico: R$ 49/mês
    Plano Pro: R$ 99/mês
    """)
    
    (kb_dir / "faq.txt").write_text("""
    Q: Como cancelar?
    A: Acesse Minha Conta → Cancelar
    """)
    
    return kb_dir

def test_with_mock_openai(mock_openai):
    """Exemplo usando mock do OpenAI."""
    from src.agents.general_chat_agent import general_chat_agent
    from src.agents.state import AgentState
    
    state = AgentState(user_input="Olá!")
    result = general_chat_agent(state)
    
    assert mock_openai.called
    assert result["output"] == "Mocked response"
```

---

### 📈 Métricas de Qualidade

#### Coverage Report

```bash
# Gera relatório de cobertura
pytest --cov=src --cov-report=term-missing

# Output:
# Name                              Stmts   Miss  Cover   Missing
# ---------------------------------------------------------------
# src/agents/router_agent.py           45      2    96%   23-24
# src/agents/knowledge_agent.py        67      5    93%   89-93
# src/tools/calendar_tool.py           34      8    76%   45-52
# ---------------------------------------------------------------
# TOTAL                               456     23    95%
```

**Meta:** Manter cobertura > 85%

#### Linting e Formatação

```bash
# Instala ferramentas de linting
pip install black flake8 mypy isort

# Formata código automaticamente
black src/ tests/

# Organiza imports
isort src/ tests/

# Verifica estilo (PEP 8)
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/ --ignore-missing-imports
```

#### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy

# Instala hooks
pip install pre-commit
pre-commit install
```

---

### 🐛 Debugging

#### Modo Debug Verbose

```python
# src/main.py

import logging

# Ativa debug completo
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Debug apenas de componentes específicos
logging.getLogger("src.agents").setLevel(logging.DEBUG)
logging.getLogger("src.tools").setLevel(logging.INFO)
```

#### Inspecionando Estado dos Agentes

```python
# Durante desenvolvimento, adicione prints:

def knowledge_agent(state: AgentState) -> AgentState:
    print(f"[DEBUG] Knowledge Agent State: {state}")
    print(f"[DEBUG] User Input: {state['user_input']}")
    
    # ... processamento
    
    print(f"[DEBUG] Retrieved docs: {len(docs)}")
    print(f"[DEBUG] Response length: {len(response)}")
    
    return result
```

#### Testando Queries Específicas

```python
# scripts/test_query.py

from src.agents.orchestrator import run_chatbot

def test_query(query: str):
    print(f"\n{'='*50}")
    print(f"Query: {query}")
    print(f"{'='*50}\n")
    
    response = run_chatbot(query, debug=True)
    
    print(f"\nResponse:\n{response}")
    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    test_queries = [
        "Qual é o preço do Plano Pro?",
        "Agende reunião amanhã 14h",
        "Envie email para teste@example.com"
    ]
    
    for q in test_queries:
        test_query(q)
```

---

## 📊 Monitoramento

### Logs

Os logs são estruturados em formato JSON e podem ser visualizados em:
- Console (durante desenvolvimento)
- Arquivos de log (em produção)
- Kestra UI (para workflows)

### Métricas

O Kestra fornece métricas de execução dos workflows:
- Taxa de sucesso/falha
- Tempo de processamento
- Histórico de execuções

## 🤝 Contribuindo

Este é um projeto template. Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

## 📝 Licença

Copyright © 2026 Cássio de Alcantara

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes completos.

**Em resumo, você pode:**
- ✅ Usar comercialmente
- ✅ Modificar o código
- ✅ Distribuir
- ✅ Uso privado
- ✅ Forkar e criar seus próprios projetos

**Condições:**
- 📄 Manter aviso de copyright e licença
- ⚖️ Fornecido "como está", sem garantias

## 🎯 Roadmap

- [ ] Integração completa com WhatsApp Web
- [ ] Suporte para múltiplos idiomas
- [ ] Interface web para gerenciamento
- [ ] Análise de sentimentos
- [ ] Relatórios e analytics
- [ ] Suporte para arquivos e imagens
- [ ] Integração com mais APIs (CRM, etc.)

## 💡 Dicas para Forks

Para criar seu próprio chatbot baseado neste template:

1. **Fork o repositório**
2. **Adicione seu conhecimento** em `knowledge_base/`
3. **Personalize os prompts** dos agentes
4. **Configure suas credenciais** no `.env`
5. **Adicione novas ferramentas** conforme necessário
6. **Deploy** usando Docker Compose

## 🆘 Suporte

Para questões e suporte:
- Abra uma issue no GitHub
- Consulte a documentação das ferramentas utilizadas
- Verifique os logs para debugging

## 🌟 Agradecimentos e Créditos

Este projeto não seria possível sem estas incríveis ferramentas open-source e serviços:

### 🤖 AI & ML
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Framework de orquestração de agentes
- **[LangChain](https://github.com/langchain-ai/langchain)** - Abstrações para LLMs
- **[OpenAI](https://openai.com/)** - Modelos GPT-4o e embeddings
- **[Sentence Transformers](https://www.sbert.net/)** - Embeddings multilíngue

### 🗄️ Data & Storage
- **[ChromaDB](https://www.trychroma.com/)** - Vector database de código aberto
- **[PostgreSQL](https://www.postgresql.org/)** - Banco de dados relacional

### ⚙️ Orchestration & Workflow
- **[Kestra](https://kestra.io/)** - Workflow engine moderno
- **[Docker](https://www.docker.com/)** - Containerização

### 🔌 Integrations
- **[SendGrid](https://sendgrid.com/)** - Plataforma de email transacional
- **[Google Calendar API](https://developers.google.com/calendar)** - Gerenciamento de eventos
- **[WhatsApp Web.py](https://github.com/tgalal/yowsup)** - Biblioteca Python para WhatsApp

### 🛠️ Development Tools
- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno
- **[Pydantic](https://docs.pydantic.dev/)** - Validação de dados
- **[structlog](https://www.structlog.org/)** - Logging estruturado
- **[pytest](https://pytest.org/)** - Framework de testes

---

<div align="center">

**Feito com ❤️ por desenvolvedores, para desenvolvedores**

[Reporte um Bug](https://github.com/cassio-all/generic-wpp-chatbot/issues) • 
[Solicite Feature](https://github.com/cassio-all/generic-wpp-chatbot/issues) • 
[Contribua](CONTRIBUTING.md)

⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!

</div>
