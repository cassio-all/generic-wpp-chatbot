# 📱 WhatsApp Integration Setup

Este guia explica como conectar o chatbot ao WhatsApp usando **whatsapp-web.js**.

---

## 🎯 O Que Você Ganha

Com a integração do WhatsApp, você pode:

✅ Conversar com todos os **8 agentes especializados** direto pelo WhatsApp
✅ **Criar tarefas**, agendar reuniões, enviar emails - tudo pelo celular  
✅ **Memória persistente** - o chatbot lembra de conversas anteriores por número
✅ **Múltiplas conversas** simultâneas com diferentes contatos
✅ **Status de digitação** - você vê quando o bot está respondendo
✅ **Lembretes automáticos** - "lembrar de comprar café" cria tarefa instantaneamente
✅ **Integração cross-agent** - tarefas urgentes viram eventos no calendário

---

## 📋 Pré-requisitos

### 1. Node.js 18+

Verifique se você tem Node.js instalado:

```bash
node -v
```

Se não tiver, instale:

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS:**
```bash
brew install node
```

**Windows:**
Baixe de [nodejs.org](https://nodejs.org/)

### 2. Python Environment

Certifique-se de que seu ambiente Python está ativo:

```bash
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Dependência Python

Instale o websockets:

```bash
pip install websockets
```

---

## 🚀 Instalação

### 1. Instalar Dependências Node.js

As dependências são instaladas automaticamente ao rodar o script, mas você pode instalar manualmente:

```bash
cd src/integrations/whatsapp
npm install
cd ../../..
```

**Pacotes instalados:**
- `whatsapp-web.js` - Cliente WhatsApp Web
- `qrcode-terminal` - Gerar QR code no terminal
- `ws` - WebSocket para comunicação Python ↔ Node.js
- `express` - Health check HTTP

### 2. Tornar Script Executável

```bash
chmod +x start_whatsapp.sh
```

---

## 📱 Como Usar

### Método 1: Script Automático (Recomendado)

Execute o script que inicia tudo:

```bash
./start_whatsapp.sh
```

O script irá:
1. ✅ Verificar Node.js instalado
2. 📦 Instalar dependências (se necessário)
3. 🌉 Iniciar servidor Node.js (porta 8765)
4. 🐍 Iniciar chatbot Python
5. 📱 Exibir QR code para escanear

### Método 2: Manual (Avançado)

**Terminal 1 - Node.js Bridge:**
```bash
cd src/integrations/whatsapp
node server.js
```

**Terminal 2 - Python Chatbot:**
```bash
source venv/bin/activate
python run_whatsapp.py
```

---

## 📱 Conectando ao WhatsApp

### 1. Escanear QR Code

Quando você iniciar, verá um QR code no terminal:

```
📱 QR Code received! Scan with WhatsApp:
┌─────────────────────────┐
│ ██ ▄▄▄▄▄ █▀▀▄▀██ ▄▄▄▄▄ ██│
│ ██ █   █ █▀▄ ▀▀█ █   █ ██│
│ ██ █▄▄▄█ █ ▀█▀ █ █▄▄▄█ ██│
│ ██▄▄▄▄▄▄▄█ ▀▄█ █▄▄▄▄▄▄▄██│
│ ...                      │
└─────────────────────────┘
```

### 2. Abrir WhatsApp no Celular

1. Abra **WhatsApp** no seu celular
2. Toque em **⋮** (Android) ou **Configurações** (iPhone)
3. Toque em **Dispositivos conectados**
4. Toque em **Conectar um dispositivo**
5. **Escaneie o QR code** que apareceu no terminal

### 3. Autenticação

Após escanear, você verá:

```
✅ WhatsApp conectado!
👤 Nome: Seu Nome
📞 Número: +55...
```

**🎉 Pronto!** O chatbot está conectado ao seu WhatsApp.

---

## 💬 Como Conversar

Abra o WhatsApp e envie mensagens para o número conectado. O chatbot responderá automaticamente!

### Exemplos de Uso

**1. Criar tarefas:**
```
Você: lembrar de comprar café
Bot: ✅ Ok, vou lembrar!
     📝 Tarefa criada: comprar café
```

**2. Agendar reuniões:**
```
Você: agendar reunião com João amanhã às 15h
Bot: ✅ Reunião agendada!
     📅 João - 06/02/2026 15:00
```

**3. Enviar emails:**
```
Você: enviar email para joao@example.com assunto "Relatório" corpo "Segue o relatório em anexo"
Bot: ✅ Email enviado com sucesso!
```

**4. Buscar na web:**
```
Você: buscar notícias sobre Python
Bot: 🔍 Aqui estão as últimas notícias sobre Python:
     1. [título] - [fonte]
     ...
```

**5. Resumo do dia:**
```
Você: resumo do dia
Bot: 📊 Resumo do Dia
     📋 Tarefas pendentes: 3
     ⏰ Prazos próximos: 1
```

---

## 🔧 Arquitetura

```
WhatsApp ←→ Node.js Bridge ←→ Python Chatbot ←→ 8 Agentes
              (WebSocket)         (Orchestrator)
```

**Fluxo de Mensagem:**

1. **Você** envia mensagem no WhatsApp
2. **whatsapp-web.js** recebe via Puppeteer
3. **Node.js server** envia via WebSocket (porta 8765)
4. **Python client** recebe e processa com orchestrator
5. **Agentes** processam (Calendar, Email, Task, etc.)
6. **Resposta** volta pelo mesmo caminho
7. **Você** recebe no WhatsApp

---

## 🔍 Verificação de Status

### Health Check

Verifique se o bridge está rodando:

```bash
curl http://localhost:3000/health
```

Resposta:
```json
{
  "whatsapp": "connected",
  "python": "connected",
  "uptime": 125.4
}
```

### Logs

O sistema usa **structlog** para logs detalhados:

```
2026-02-05 01:00:00 [info] 📨 Incoming message from_name=João body=Oi
2026-02-05 01:00:01 [info] Processing WhatsApp message thread_id=whatsapp-5511999999999
2026-02-05 01:00:02 [info] Intent determined intent=general_conversation
2026-02-05 01:00:03 [info] ✅ Message sent successfully
```

---

## 🛑 Como Parar

Pressione **Ctrl+C** no terminal. O script irá:

1. Fechar conexão Python
2. Parar servidor Node.js
3. Limpar recursos

```
👋 Shutting down gracefully...
🛑 Stopping services...
✅ All services stopped
```

---

## 📂 Arquivos Criados

Após a primeira execução:

```
src/integrations/whatsapp/
├── .wwebjs_auth/          # Sessão persistente do WhatsApp
│   └── session-default/   # Não precisa escanear QR toda vez
├── .wwebjs_cache/         # Cache do navegador
├── node_modules/          # Dependências Node.js
├── package.json           # Configuração Node.js
├── package-lock.json      # Lock de versões
└── server.js              # Servidor bridge
```

**⚠️ IMPORTANTE:** A pasta `.wwebjs_auth/` contém sua sessão. Não delete ou você precisará escanear o QR code novamente.

---

## 🔐 Segurança

### Dados Armazenados

- **Sessão WhatsApp**: `.wwebjs_auth/` (local)
- **Conversas**: `data/checkpoints.db` (SQLite local)
- **Tarefas**: `data/tasks.db` (SQLite local)

### Boas Práticas

✅ **Nunca compartilhe** a pasta `.wwebjs_auth/`  
✅ Adicione ao `.gitignore` (já configurado)  
✅ Use apenas em ambiente confiável  
✅ Desconecte dispositivos não utilizados no WhatsApp

---

## 🐛 Troubleshooting

### Erro: "Node.js not found"

**Solução:** Instale Node.js 18+ (veja [Pré-requisitos](#📋-pré-requisitos))

### Erro: "Failed to connect to bridge"

**Solução:**
1. Verifique se o servidor Node.js está rodando
2. Verifique porta 8765 livre: `lsof -i :8765`
3. Reinicie o bridge

### Erro: "Authentication failure"

**Solução:**
1. Delete `.wwebjs_auth/`
2. Escaneie QR code novamente

### QR Code não aparece

**Solução:**
1. Verifique logs do Node.js
2. Certifique-se que o Puppeteer foi instalado corretamente
3. Em servidores sem GUI, instale dependências extras:

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    gconf-service libasound2 libatk1.0-0 libc6 libcairo2 \
    libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 \
    libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 \
    libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 \
    libxrender1 libxss1 libxtst6 ca-certificates \
    fonts-liberation libappindicator1 libnss3 lsb-release \
    xdg-utils wget
```

### "Connection closed"

**Solução:**
1. Verifique conexão com internet
2. WhatsApp Web pode ter desconectado - escaneie QR novamente
3. Reinicie ambos os servidores

---

## 🎓 Recursos Adicionais

- [whatsapp-web.js Docs](https://wwebjs.dev/)
- [Node.js WebSocket](https://github.com/websockets/ws)
- [Python websockets](https://websockets.readthedocs.io/)

---

## 🚀 Próximos Passos

Após conectar ao WhatsApp, você pode:

1. **Testar todos os agentes** - envie mensagens variadas
2. **Adicionar contatos** - compartilhe o número com amigos/equipe
3. **Personalizar respostas** - edite os agentes em `src/agents/`
4. **Adicionar grupos** - o bot funciona em grupos também!
5. **Deploy em servidor** - use VPS para rodar 24/7

---

**🎉 Aproveite seu chatbot no WhatsApp!**

Se tiver dúvidas, consulte os logs ou abra uma issue no projeto.
