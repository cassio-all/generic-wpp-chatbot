"""Test expanded calendar agent functionality."""
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import ChatbotOrchestrator
from langchain_core.messages import HumanMessage


def test_calendar_operations():
    """Test various calendar operations."""
    print("🧪 Testing Calendar Agent - Expanded Features\n")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    thread_id = "test-calendar-expanded"
    
    # Test 1: List events
    print("\n📋 Test 1: Listar eventos")
    print("-" * 60)
    result = orchestrator.process_message(
        "Liste meus próximos eventos da semana",
        thread_id=thread_id
    )
    print(f"Resposta: {result}\n")
    
    # Test 2: Schedule a meeting (to have something to work with)
    print("\n📅 Test 2: Agendar uma reunião de teste")
    print("-" * 60)
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    result = orchestrator.process_message(
        f"Agendar reunião de teste para amanhã {tomorrow} às 14h, duração 30 minutos",
        thread_id=thread_id
    )
    print(f"Resposta: {result}\n")
    
    # Test 3: List events again to see the new one
    print("\n📋 Test 3: Listar eventos novamente")
    print("-" * 60)
    result = orchestrator.process_message(
        "Mostre meus eventos de amanhã",
        thread_id=thread_id
    )
    print(f"Resposta: {result}\n")
    
    # Test 4: Try to cancel an event
    print("\n❌ Test 4: Cancelar evento")
    print("-" * 60)
    result = orchestrator.process_message(
        "Cancelar a reunião de teste",
        thread_id=thread_id
    )
    print(f"Resposta: {result}\n")
    
    # Test 5: Schedule another meeting to test edit
    print("\n📅 Test 5: Agendar outra reunião para testar edição")
    print("-" * 60)
    result = orchestrator.process_message(
        f"Agendar reunião de planejamento para amanhã {tomorrow} às 10h",
        thread_id=thread_id
    )
    print(f"Resposta: {result}\n")
    
    # Test 6: Edit meeting time
    print("\n✏️ Test 6: Editar horário da reunião")
    print("-" * 60)
    result = orchestrator.process_message(
        f"Mudar a reunião de planejamento para {tomorrow} às 11h",
        thread_id=thread_id
    )
    print(f"Resposta: {result}\n")
    
    # Test 7: List to verify changes
    print("\n📋 Test 7: Verificar mudanças")
    print("-" * 60)
    result = orchestrator.process_message(
        "Liste minhas reuniões de amanhã",
        thread_id=thread_id
    )
    print(f"Resposta: {result}\n")
    
    print("=" * 60)
    print("✅ Testes concluídos!")


if __name__ == "__main__":
    test_calendar_operations()
