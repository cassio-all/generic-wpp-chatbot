"""Test agent integrations and automation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import ChatbotOrchestrator


def test_integrations():
    """Test intelligent agent integrations."""
    print("🤖 Testing Agent Integrations\n")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    thread_id = "test-integrations"
    
    # Test 1: Quick reminder (automation)
    print("\n💡 Test 1: Lembrete rápido (automation)")
    print("-" * 60)
    result = orchestrator.process_message(
        "lembrar de comprar café",
        thread_id=thread_id
    )
    print(f"Resposta:\n{result}\n")
    
    # Test 2: Urgent task with deadline (should auto-create calendar event)
    print("\n📅 Test 2: Tarefa urgente com prazo (auto-calendário)")
    print("-" * 60)
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    result = orchestrator.process_message(
        f"criar tarefa urgente entregar relatório até {tomorrow}",
        thread_id=thread_id
    )
    print(f"Resposta:\n{result}\n")
    
    # Test 3: Daily summary
    print("\n📊 Test 3: Resumo do dia")
    print("-" * 60)
    result = orchestrator.process_message(
        "resumo do dia",
        thread_id=thread_id
    )
    print(f"Resposta:\n{result}\n")
    
    # Test 4: Another reminder
    print("\n📝 Test 4: Outro lembrete")
    print("-" * 60)
    result = orchestrator.process_message(
        "não esquecer de ligar pro João",
        thread_id=thread_id
    )
    print(f"Resposta:\n{result}\n")
    
    # Test 5: Normal task (no auto-calendar)
    print("\n📋 Test 5: Tarefa normal (sem auto-calendário)")
    print("-" * 60)
    result = orchestrator.process_message(
        "criar tarefa estudar Python, prioridade baixa",
        thread_id=thread_id
    )
    print(f"Resposta:\n{result}\n")
    
    # Test 6: List all tasks
    print("\n📝 Test 6: Listar tarefas criadas")
    print("-" * 60)
    result = orchestrator.process_message(
        "listar minhas tarefas",
        thread_id=thread_id
    )
    print(f"Resposta:\n{result}\n")
    
    print("=" * 60)
    print("✅ Testes de integração concluídos!")
    print("\n💡 Recursos demonstrados:")
    print("  • Lembretes rápidos via 'lembrar de'")
    print("  • Auto-criação de eventos no calendário")
    print("  • Resumo diário de tarefas")
    print("  • Detecção inteligente de intenções")


if __name__ == "__main__":
    test_integrations()
