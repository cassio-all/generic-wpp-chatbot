# Generic WhatsApp Chatbot

Um chatbot genérico para WhatsApp com arquitetura modular, orquestração de agentes usando LangGraph e integração com Kestra. Clone este projeto, adicione sua base de conhecimento personalizada e ferramentas para criar seu próprio assistente de atendimento.

## 🚀 Características

- **Arquitetura de Agentes LangGraph**: Sistema modular com agentes especializados para diferentes tarefas
- **Orquestração Kestra**: Workflows automatizados para processar mensagens e tarefas agendadas
- **Base de Conhecimento**: Sistema de recuperação de informações usando vector database (ChromaDB)
- **Agendamento de Reuniões**: Integração com Google Calendar
- **Envio de E-mails**: Integração com SendGrid
- **Docker Ready**: Ambiente containerizado para fácil deployment
- **Genérico e Extensível**: Fácil de forkar e adicionar conhecimento customizado

## 📋 Agentes Disponíveis

O chatbot usa LangGraph para orquestrar diferentes agentes:

1. **Router Agent**: Determina a intenção do usuário e roteia para o agente apropriado
2. **Knowledge Agent**: Responde perguntas consultando a base de conhecimento
3. **Calendar Agent**: Agenda reuniões no Google Calendar
4. **Email Agent**: Envia e-mails via SendGrid
5. **General Chat Agent**: Conversa geral e saudações

## 🛠️ Tecnologias

- **Python 3.11+**
- **LangGraph**: Orquestração de agentes
- **LangChain**: Framework de LLM
- **OpenAI GPT**: Modelos de linguagem
- **ChromaDB**: Vector database para conhecimento
- **Kestra**: Orquestração de workflows
- **SendGrid**: Envio de e-mails
- **Google Calendar API**: Agendamento
- **Docker & Docker Compose**: Containerização

## 📦 Instalação

### Pré-requisitos

- Python 3.11 ou superior
- Docker e Docker Compose (opcional, mas recomendado)
- Conta OpenAI com API key
- Conta SendGrid (opcional, para e-mails)
- Google Cloud Console (opcional, para Calendar)

### Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/cassio-all/generic-wpp-chatbot.git
cd generic-wpp-chatbot
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

5. Execute o chatbot (modo CLI para testes):
```bash
python -m src.main
```

### Instalação com Docker

1. Configure o arquivo `.env`:
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

2. Inicie os serviços:
```bash
docker-compose up -d
```

3. Acesse o Kestra UI:
```
http://localhost:8080
```

## ⚙️ Configuração

### OpenAI API Key (Obrigatório)

1. Obtenha sua API key em: https://platform.openai.com/api-keys
2. Adicione no `.env`:
```
OPENAI_API_KEY=sk-...
```

### SendGrid (Opcional - Para envio de e-mails)

1. Crie uma conta em: https://sendgrid.com
2. Gere uma API key
3. Adicione no `.env`:
```
SENDGRID_API_KEY=SG....
SENDER_EMAIL=seu-email@example.com
```

### Google Calendar (Opcional - Para agendamento)

1. Crie um projeto no Google Cloud Console
2. Ative a Google Calendar API
3. Crie credenciais OAuth 2.0
4. Baixe o arquivo JSON e salve em `credentials/google_calendar_credentials.json`
5. Na primeira execução, será necessário autorizar o acesso

## 📚 Adicionando Conhecimento

Para adicionar sua base de conhecimento:

1. Adicione arquivos `.txt` na pasta `knowledge_base/`:
```bash
mkdir -p knowledge_base
echo "Sua informação aqui" > knowledge_base/minha_info.txt
```

2. O vector database será reconstruído automaticamente na próxima execução

3. Para forçar a reconstrução:
```bash
rm -rf data/vector_db
python -m src.main
```

### Exemplo de Estrutura de Conhecimento

```
knowledge_base/
├── produtos.txt          # Informações sobre produtos
├── politicas.txt         # Políticas da empresa
├── faq.txt              # Perguntas frequentes
└── contatos.txt         # Informações de contato
```

## 🔄 Kestra Workflows

O projeto inclui workflows Kestra para automação:

### 1. whatsapp-chatbot-main.yml
Processa mensagens do WhatsApp através dos agentes

### 2. knowledge-base-update.yml
Atualiza a base de conhecimento automaticamente (diário às 2h)

### 3. scheduled-reports.yml
Envia relatórios agendados (diário às 9h)

Para ativar os workflows:
1. Acesse o Kestra UI: http://localhost:8080
2. Navegue até Flows
3. Habilite os triggers necessários

## 📱 Uso

### Modo CLI (Testes)

```bash
python -m src.main
```

Digite suas mensagens e veja as respostas do bot.

### Exemplos de Interação

**Consulta de Conhecimento:**
```
Você: Quais são os produtos disponíveis?
Bot: [Responde com base na knowledge base]
```

**Agendamento:**
```
Você: Agende uma reunião para amanhã às 14h sobre projeto X
Bot: ✅ Reunião agendada com sucesso!
```

**Envio de E-mail:**
```
Você: Envie um e-mail para cliente@example.com com o assunto "Proposta" e conteúdo "..."
Bot: ✅ E-mail enviado com sucesso!
```

## 🔧 Personalização

### Modificando Prompts

Edite os prompts dos agentes em:
- `src/agents/knowledge_agent.py`
- `src/agents/calendar_agent.py`
- `src/agents/email_agent.py`
- `src/agents/general_chat_agent.py`

### Adicionando Novos Agentes

1. Crie um novo arquivo em `src/agents/`
2. Implemente a classe do agente
3. Adicione o agente no `orchestrator.py`
4. Atualize a lógica de roteamento

### Adicionando Novas Ferramentas

1. Crie um novo arquivo em `src/tools/`
2. Implemente as funções da ferramenta
3. Importe e use nos agentes apropriados

## 🧪 Testes

Para testar o sistema:

1. **Teste CLI**: Use o modo CLI para testar interações
2. **Teste de Conhecimento**: Adicione documentos e faça perguntas
3. **Teste de Agendamento**: Configure Google Calendar e teste agendamentos
4. **Teste de E-mail**: Configure SendGrid e teste envios

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

[Adicione sua licença aqui]

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

## 🌟 Acknowledgments

Este projeto utiliza:
- LangGraph e LangChain
- OpenAI GPT models
- Kestra workflow engine
- ChromaDB vector database
- SendGrid email service
- Google Calendar API
