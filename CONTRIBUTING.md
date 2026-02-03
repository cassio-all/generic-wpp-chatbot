# Contributing to Generic WhatsApp Chatbot

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/generic-wpp-chatbot.git
   cd generic-wpp-chatbot
   ```
3. Run setup:
   ```bash
   ./setup.sh
   ```
4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- OpenAI API key

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Run the chatbot in CLI mode:
   ```bash
   python -m src.main
   ```

## Project Structure

```
generic-wpp-chatbot/
├── src/
│   ├── agents/          # LangGraph agent implementations
│   ├── tools/           # External tool integrations
│   ├── services/        # Service layer (knowledge base, etc.)
│   ├── config/          # Configuration management
│   └── main.py          # Application entry point
├── kestra/
│   └── flows/           # Kestra workflow definitions
├── knowledge_base/      # Knowledge documents (.txt files)
├── tests/               # Test suite
├── docker-compose.yml   # Docker orchestration
└── requirements.txt     # Python dependencies
```

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs

### Suggesting Enhancements

1. Open an issue with:
   - Clear description of the enhancement
   - Use case and benefits
   - Possible implementation approach

### Pull Requests

1. Create a feature branch from `main`
2. Make your changes
3. Add/update tests as needed
4. Update documentation
5. Run tests and ensure they pass
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

#### PR Guidelines

- One feature/fix per PR
- Clear description of changes
- Link related issues
- Update README if needed
- Add tests for new features
- Follow existing code style

## Code Style

### Python
- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings
- Keep functions focused and small
- Use meaningful variable names

### Example

```python
"""Module description."""
from typing import List, Optional
import structlog

logger = structlog.get_logger()


def process_message(message: str, sender: str) -> str:
    """Process a message and return response.
    
    Args:
        message: The input message
        sender: The message sender
        
    Returns:
        The generated response
    """
    logger.info("Processing message", sender=sender)
    # Implementation
    return response
```

### Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example:
```
feat: add sentiment analysis to router agent

- Implement sentiment detection
- Add tests for sentiment analysis
- Update documentation
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=src tests/
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names
- Mock external dependencies
- Test edge cases

Example:
```python
def test_knowledge_search_success():
    """Test successful knowledge base search."""
    # Arrange
    query = "test query"
    expected_results = ["result 1", "result 2"]
    
    # Act
    result = search_knowledge_base(query)
    
    # Assert
    assert result["status"] == "success"
    assert len(result["results"]) == 2
```

## Documentation

### Code Documentation

- Add docstrings to all functions/classes
- Include parameter descriptions
- Document return values
- Add usage examples for complex functions

### README Updates

Update README when:
- Adding new features
- Changing setup process
- Modifying configuration
- Adding dependencies

## Adding New Features

### Adding a New Agent

1. Create agent file in `src/agents/`:
   ```python
   class MyNewAgent:
       def __init__(self):
           self.llm = ChatOpenAI(...)
       
       def process(self, state: AgentState) -> AgentState:
           # Implementation
           return state
   ```

2. Register in `orchestrator.py`:
   ```python
   self.my_new_agent = MyNewAgent()
   workflow.add_node("my_new", self.my_new_agent.process)
   ```

3. Update router logic
4. Add tests
5. Update documentation

### Adding a New Tool

1. Create tool file in `src/tools/`:
   ```python
   def my_new_tool(param: str) -> dict:
       """Tool description."""
       try:
           # Implementation
           return {"status": "success", "data": result}
       except Exception as e:
           return {"status": "error", "message": str(e)}
   ```

2. Add to `src/tools/__init__.py`
3. Use in relevant agents
4. Add tests
5. Update documentation

### Adding a Kestra Workflow

1. Create YAML file in `kestra/flows/`:
   ```yaml
   id: my-workflow
   namespace: whatsapp-chatbot
   
   tasks:
     - id: my_task
       type: io.kestra.plugin.scripts.python.Commands
       commands:
         - python -c "print('Hello')"
   ```

2. Test locally
3. Document in README
4. Add to architecture diagram

## Debugging

### Enable Debug Logging

In `.env`:
```
LOG_LEVEL=DEBUG
```

### Common Issues

**Import Errors**:
- Ensure virtual environment is activated
- Check all dependencies are installed

**API Errors**:
- Verify API keys in `.env`
- Check API rate limits
- Review API documentation

**Vector DB Issues**:
- Delete `data/vector_db/` to rebuild
- Check knowledge_base/ has documents
- Verify OpenAI embeddings API access

## Community

- Be respectful and inclusive
- Help others when possible
- Share knowledge and experiences
- Follow code of conduct

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
