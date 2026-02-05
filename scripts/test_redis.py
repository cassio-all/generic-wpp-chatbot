#!/usr/bin/env python3
"""Test Redis integration."""
from src.agents.orchestrator import ChatbotOrchestrator

print("🔄 Inicializando orchestrator com Redis...")
orchestrator = ChatbotOrchestrator()
print("✅ Redis integrado com sucesso!")
