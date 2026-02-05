"""Test Task Management Agent functionality."""
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import ChatbotOrchestrator


def test_task_operations():
    """Test various task management operations."""
    print("🧪 Testing Task Management Agent\n")
    print("=" * 60)
    
    orchestrator = ChatbotOrchestrator()
    thread_id = "test-tasks"
    
    # Test 1: Create tasks
    print("\n📝 Test 1: Criar tarefas")
    print("-" * 60)
    
    tasks_to_create = [
        "criar tarefa comprar leite",
        "adicionar tarefa urgente: revisar código",
        "criar tarefa estudar Python, prioridade alta, prazo amanhã",
        "TODO: preparar apresentação"
    ]
    
    for task_msg in tasks_to_create:
        result = orchestrator.process_message(task_msg, thread_id=thread_id)
        print(f"📌 {task_msg}")
        print(f"   {result[:100]}...\n" if len(result) > 100 else f"   {result}\n")
    
    # Test 2: List all tasks
    print("\n📋 Test 2: Listar todas as tarefas")
    print("-" * 60)
    result = orchestrator.process_message("listar minhas tarefas", thread_id=thread_id)
    print(f"Resposta:\n{result}\n")
    
    # Test 3: List by priority
    print("\n🔴 Test 3: Listar tarefas urgentes")
    print("-" * 60)
    result = orchestrator.process_message("mostrar tarefas urgentes", thread_id=thread_id)
    print(f"Resposta:\n{result}\n")
    
    # Test 4: Get upcoming deadlines
    print("\n⏰ Test 4: Ver tarefas com prazo próximo")
    print("-" * 60)
    result = orchestrator.process_message("quais tarefas vencem esta semana?", thread_id=thread_id)
    print(f"Resposta:\n{result}\n")
    
    # Test 5: Complete a task
    print("\n✅ Test 5: Completar tarefa")
    print("-" * 60)
    result = orchestrator.process_message("completar tarefa de comprar leite", thread_id=thread_id)
    print(f"Resposta:\n{result}\n")
    
    # Test 6: List pending tasks
    print("\n⬜ Test 6: Ver tarefas pendentes")
    print("-" * 60)
    result = orchestrator.process_message("minhas tarefas pendentes", thread_id=thread_id)
    print(f"Resposta:\n{result}\n")
    
    # Test 7: List completed tasks
    print("\n✅ Test 7: Ver tarefas completadas")
    print("-" * 60)
    result = orchestrator.process_message("tarefas concluídas", thread_id=thread_id)
    print(f"Resposta:\n{result}\n")
    
    # Test 8: Delete a task
    print("\n🗑️ Test 8: Deletar tarefa")
    print("-" * 60)
    result = orchestrator.process_message("deletar a tarefa de preparar apresentação", thread_id=thread_id)
    print(f"Resposta:\n{result}\n")
    
    # Test 9: Final list
    print("\n📋 Test 9: Lista final de tarefas")
    print("-" * 60)
    result = orchestrator.process_message("listar todas as tarefas", thread_id=thread_id)
    print(f"Resposta:\n{result}\n")
    
    print("=" * 60)
    print("✅ Testes concluídos!")


if __name__ == "__main__":
    test_task_operations()
