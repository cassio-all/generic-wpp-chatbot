# Quick Start Guide

## 🚀 5-Minute Setup

### Prerequisites
- Python 3.11+
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone and Setup**
   ```bash
   git clone https://github.com/cassio-all/generic-wpp-chatbot.git
   cd generic-wpp-chatbot
   ./setup.sh
   ```

2. **Configure API Key**
   ```bash
   # Edit .env file
   nano .env
   
   # Add your OpenAI API key:
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Run the Chatbot**
   ```bash
   source venv/bin/activate
   python -m src.main
   ```

## 💬 Try It Out

Once running, you can test these interactions:

### General Chat
```
You: Olá, como você está?
Bot: Olá! Estou bem, obrigado por perguntar. Como posso ajudá-lo hoje?
```

### Knowledge Query
```
You: Quais funcionalidades você tem?
Bot: [Responde baseado no arquivo knowledge_base/welcome.txt]
```

### Schedule Meeting (requires Google Calendar setup)
```
You: Agende uma reunião amanhã às 14h sobre projeto X
Bot: ✅ Reunião agendada com sucesso!
```

### Send Email (requires SendGrid setup)
```
You: Envie um email para teste@example.com com assunto "Teste"
Bot: ✅ E-mail enviado com sucesso!
```

## 🐳 Docker Quick Start

```bash
# 1. Configure .env
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY

# 2. Start all services
docker-compose up -d

# 3. Access Kestra UI
open http://localhost:8080
```

## 📚 Add Your Knowledge

```bash
# Add text files to knowledge_base/
echo "Your company information here" > knowledge_base/company_info.txt

# Restart to rebuild the knowledge base
python -m src.main
```

## 🔧 Optional Integrations

### SendGrid (for emails)
1. Get API key from [SendGrid](https://sendgrid.com)
2. Add to `.env`:
   ```
   SENDGRID_API_KEY=SG.xxx
   SENDER_EMAIL=your-email@domain.com
   ```

### Google Calendar (for scheduling)
1. Create project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Download JSON and save as `credentials/google_calendar_credentials.json`

## 🧪 Run Tests

```bash
source venv/bin/activate
pytest
```

## 📖 Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## 🆘 Common Issues

### "ModuleNotFoundError"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "OpenAI API Error"
- Check your API key in `.env`
- Ensure you have credits in your OpenAI account

### "No knowledge found"
- Add `.txt` files to `knowledge_base/`
- Delete `data/vector_db/` to force rebuild

## 💡 Tips

- Start with CLI mode for testing
- Add knowledge incrementally
- Monitor logs in console
- Use Kestra UI for workflow monitoring

## 🌟 Key Features

✅ **Modular Architecture** - Easy to extend and customize  
✅ **LangGraph Agents** - Intelligent routing and processing  
✅ **Kestra Orchestration** - Automated workflows  
✅ **Vector Database** - Smart knowledge retrieval  
✅ **Docker Ready** - One-command deployment  
✅ **Generic & Forkable** - Perfect for customization  

---

**Need Help?** Open an issue on GitHub or check the documentation!
