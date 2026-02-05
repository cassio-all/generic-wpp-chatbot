#!/bin/bash

# Test script for SQLite persistence across restarts
SESSION_ID="test-$(date +%s)"

echo "=== TESTE 1: Primeira execução - Salvando informação ==="
echo "Meu nome é Cássio e sou desenvolvedor Python
quit" | ./venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from src.agents.orchestrator import ChatbotOrchestrator

orchestrator = ChatbotOrchestrator()
thread_id = '$SESSION_ID'

# First message
response = orchestrator.process_message('Meu nome é Cássio e sou desenvolvedor Python', thread_id)
print(f'Bot: {response}')
"

echo ""
echo "=== AGUARDANDO 2 SEGUNDOS ==="
sleep 2

echo ""
echo "=== TESTE 2: Segunda execução - Tentando recuperar memória ==="
./venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from src.agents.orchestrator import ChatbotOrchestrator

orchestrator = ChatbotOrchestrator()
thread_id = '$SESSION_ID'

# Ask for memory
response = orchestrator.process_message('Como eu me chamo?', thread_id)
print(f'Bot: {response}')

# Ask about profession
response = orchestrator.process_message('Qual é minha profissão?', thread_id)
print(f'Bot: {response}')
"

echo ""
echo "=== TESTE CONCLUÍDO ==="
echo "Se o bot lembrou do nome 'Cássio' e da profissão, a persistência funciona!"
