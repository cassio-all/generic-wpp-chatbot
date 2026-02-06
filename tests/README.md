# 🧪 Testes Automatizados

Documentação completa do sistema de testes do Generic WhatsApp Chatbot.

## 📋 Estrutura dos Testes

```
tests/
├── test_whatsapp_media.py      # Testes de mídia (áudio, imagem, PDF)
├── test_knowledge_base.py      # Testes da base de conhecimento FAISS
├── test_orchestrator.py        # Testes do orquestrador de agentes
├── test_integration.py         # Testes de integração end-to-end
├── test_agents.py              # Testes dos agentes individuais
├── test_tools.py               # Testes das ferramentas
├── test_calendar_expanded.py  # Testes expandidos do calendário
└── test_task_agent.py         # Testes do agente de tarefas
```

## 🚀 Executando os Testes

### Método Rápido
```bash
./run_tests.sh
```

### Método Manual
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências de teste
pip install -r requirements.txt

# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=src --cov-report=html --cov-report=term-missing

# Executar testes específicos
pytest tests/test_whatsapp_media.py
pytest tests/test_orchestrator.py -v
pytest tests/test_integration.py::TestCalendarWorkflow
```

## 📊 Cobertura de Código

O projeto visa **>80% de cobertura** em todas as áreas críticas.

### Visualizar Relatório HTML
```bash
pytest --cov=src --cov-report=html
python -m http.server 8000 --directory htmlcov
# Abrir: http://localhost:8000
```

### Áreas Cobertas
- ✅ **WhatsApp Integration**: Processamento de mensagens, mídia, filtros
- ✅ **Media Handling**: Áudio, imagem, PDF, mídia não suportada
- ✅ **Auto-Pause System**: Detecção de resposta manual, timeout
- ✅ **Knowledge Base**: Busca, monitoramento, reindexação
- ✅ **Orchestrator**: Roteamento, classificação de intents, contexto
- ✅ **Integration Flows**: Fluxos end-to-end completos
- ⏳ **Agents**: Calendar, Task, Email (em expansão)
- ⏳ **Security**: Validação de entrada, sanitização (pendente)

## 🎯 Tipos de Testes

### 1. Testes Unitários
Testam componentes individuais isoladamente com mocks.

**Exemplo:**
```python
def test_transcribe_audio_success(whatsapp_client, sample_audio_base64):
    with patch.object(whatsapp_client.openai_client.audio.transcriptions, 'create') as mock_create:
        mock_create.return_value = Mock(text="Texto transcrito")
        result = await whatsapp_client._transcribe_audio(sample_audio_base64)
        assert result == "Texto transcrito"
```

### 2. Testes de Integração
Testam fluxos completos entre múltiplos componentes.

**Exemplo:**
```python
async def test_audio_transcription_flow():
    # Mensagem de áudio -> Transcrição -> Orchestrator -> Resposta
    pass
```

### 3. Testes de Fixtures
Usam dados de exemplo reutilizáveis.

**Fixtures Disponíveis:**
- `whatsapp_client`: Cliente WhatsApp mockado
- `sample_audio_base64`: Áudio de exemplo em base64
- `sample_image_base64`: Imagem de exemplo em base64
- `sample_pdf_base64`: PDF de exemplo em base64
- `mock_knowledge_base`: Base de conhecimento mockada
- `orchestrator`: Orquestrador mockado

## 📝 Convenções de Nomenclatura

### Classes de Teste
```python
class TestFeatureName:
    """Tests for specific feature."""
    pass
```

### Métodos de Teste
```python
def test_feature_specific_behavior():
    """Test that feature behaves correctly in specific scenario."""
    pass
```

### Testes Assíncronos
```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

## 🔍 Mocking Guidelines

### Mock de APIs Externas
```python
with patch('module.OpenAI') as mock_openai:
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Mock(...)
    mock_openai.return_value = mock_client
```

### Mock de Métodos Assíncronos
```python
with patch.object(obj, 'method', new_callable=AsyncMock) as mock_method:
    mock_method.return_value = "result"
    await obj.method()
```

### Mock de Arquivos
```python
with patch('builtins.open', mock_open(read_data='content')):
    with open('file.txt') as f:
        data = f.read()
```

## ✅ Checklist de Cobertura

### WhatsApp Integration
- [x] Processamento de mensagens de texto
- [x] Transcrição de áudio (Whisper)
- [x] Análise de imagens (GPT-4 Vision)
- [x] Extração de texto de PDFs
- [x] Filtro de mensagens antigas (>30s)
- [x] Filtro de contas @lid (business)
- [x] Filtro de mensagens vazias
- [x] Sistema de auto-pause (manual reply)
- [x] Timeout de auto-resume (60s)
- [x] Resposta para mídia não suportada

### Knowledge Base (FAISS)
- [x] Inicialização e carregamento
- [x] Busca por similaridade
- [x] Monitoramento de arquivos (MD5)
- [x] Detecção de mudanças
- [x] Reindexação automática
- [x] Adicionar documentos
- [x] Rebuild completo

### Orchestrator
- [x] Classificação de intents
- [x] Roteamento para agentes
- [x] Gerenciamento de contexto
- [x] Tratamento de erros
- [x] Integração com knowledge base
- [ ] Rate limiting
- [ ] Session management

### Agents
- [x] Calendar agent (básico)
- [x] Task agent (básico)
- [ ] Email agent
- [ ] Knowledge agent
- [ ] Search agent
- [ ] General agent

### Security
- [ ] Validação de entrada
- [ ] Sanitização de dados
- [ ] Proteção contra injeção
- [ ] Rate limiting
- [ ] Secrets management

## 🐛 Debugging de Testes

### Executar com mais verbosidade
```bash
pytest -vv -s
```

### Ver traceback completo
```bash
pytest --tb=long
```

### Executar apenas testes que falharam
```bash
pytest --lf
```

### Modo debug com pdb
```bash
pytest --pdb
```

### Ver print statements
```bash
pytest -s
```

## 📈 Métricas Atuais

**Status:** 🟡 Em desenvolvimento

- **Testes Criados:** 50+
- **Cobertura Estimada:** ~60%
- **Meta de Cobertura:** >80%
- **Testes Passando:** Aguardando execução inicial

## 🔄 Integração Contínua (CI/CD)

### GitHub Actions (exemplo)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## 📚 Recursos Adicionais

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## 🤝 Contribuindo

Ao adicionar novos testes:

1. Siga as convenções de nomenclatura
2. Use fixtures para dados reutilizáveis
3. Mock APIs externas
4. Adicione docstrings descritivas
5. Teste casos de sucesso E erro
6. Mantenha cobertura >80%

## 🚨 Problemas Comuns

### ImportError
```bash
# Adicionar src ao PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### AsyncIO Warnings
```ini
# pytest.ini
asyncio_mode = auto
```

### Coverage não detecta arquivos
```ini
# .coveragerc
[run]
source = src
```

---

**Última atualização:** Versão 0.3.0  
**Mantido por:** Generic WhatsApp Chatbot Team
