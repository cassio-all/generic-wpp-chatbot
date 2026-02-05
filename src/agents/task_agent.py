"""Task management agent."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.agents.integration import AgentIntegration
from src.tools import (
    create_task,
    list_tasks,
    complete_task,
    delete_task,
    update_task,
    get_upcoming_deadlines
)
import structlog
import json
import re
from datetime import datetime, timedelta

logger = structlog.get_logger()


class TaskAgent:
    """Agent responsible for task management."""
    
    def __init__(self):
        """Initialize the task agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        self.integration = AgentIntegration()
    
    def _detect_action(self, message: str) -> str:
        """Detect what task action the user wants.
        
        Args:
            message: User message
            
        Returns:
            Action type: create, list, complete, delete, update, or deadlines
        """
        system_prompt = """Você é um assistente que detecta intenções relacionadas a tarefas (TODO list).

Analise a mensagem do usuário e retorne APENAS UMA palavra:
- "create" - usuário quer CRIAR/ADICIONAR uma nova tarefa
- "list" - usuário quer VER/LISTAR tarefas
- "complete" - usuário quer COMPLETAR/MARCAR como feita uma tarefa
- "delete" - usuário quer DELETAR/REMOVER uma tarefa
- "update" - usuário quer EDITAR/ATUALIZAR uma tarefa
- "deadlines" - usuário quer ver tarefas com PRAZO próximo

Exemplos:
- "criar tarefa comprar leite" -> create
- "adicionar no meu TODO estudar Python" -> create
- "listar minhas tarefas" -> list
- "quais são minhas pendências" -> list
- "completar tarefa de estudar" -> complete
- "marcar como feita" -> complete
- "deletar tarefa" -> delete
- "remover da lista" -> delete
- "mudar prioridade da tarefa" -> update
- "editar descrição" -> update
- "quais tarefas vencem esta semana" -> deadlines
- "ver prazos próximos" -> deadlines

Retorne apenas a palavra."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=message)
            ])
            
            action = response.content.strip().lower()
            logger.info("Detected task action", action=action)
            return action
            
        except Exception as e:
            logger.error("Error detecting action", error=str(e))
            return "list"  # Default to list
    
    def _create_task(self, state: AgentState) -> AgentState:
        """Create a new task.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        system_prompt = """Você é um assistente de gerenciamento de tarefas.

Extraia as informações da tarefa da mensagem do usuário e retorne um JSON:
{
    "title": "título da tarefa (obrigatório)",
    "description": "descrição detalhada (opcional)",
    "priority": "low|medium|high|urgent (padrão: medium)",
    "deadline": "YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS (opcional)"
}

Data/hora atual: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """

Exemplos:
- "criar tarefa comprar leite" -> {"title": "comprar leite", "priority": "medium"}
- "adicionar tarefa urgente: revisar código até amanhã" -> {"title": "revisar código", "priority": "urgent", "deadline": "2026-02-06"}
- "TODO: estudar Python, alta prioridade" -> {"title": "estudar Python", "priority": "high"}

Retorne apenas o JSON."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ])
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            task_info = json.loads(json_match.group())
            
            if not task_info.get("title"):
                response_text = "Não consegui identificar o título da tarefa. Por favor, seja mais específico."
                state["response"] = response_text
                state["messages"] = state["messages"] + [AIMessage(content=response_text)]
                return state
            
            # Use smart creation with auto-calendar integration
            result = self.integration.smart_create_task_with_calendar(
                title=task_info.get("title"),
                description=task_info.get("description"),
                priority=task_info.get("priority", "medium"),
                deadline=task_info.get("deadline")
            )
            
            if result["task"]:
                task = result["task"]
                priority_emoji = {
                    "urgent": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }
                
                response_text = f"✅ Tarefa criada com sucesso!\n\n"
                response_text += f"{priority_emoji.get(task['priority'], '📋')} **{task['title']}**\n"
                response_text += f"🆔 ID: {task['id']}\n"
                response_text += f"📊 Prioridade: {task['priority']}\n"
                
                if task.get("description"):
                    response_text += f"📝 Descrição: {task['description']}\n"
                
                if task.get("deadline"):
                    response_text += f"⏰ Prazo: {task['deadline']}\n"
                
                # Notify if calendar event was auto-created
                if result.get("auto_calendar"):
                    response_text += f"\n🔔 **Evento criado no calendário automaticamente!**\n"
                    response_text += f"Você receberá um lembrete 30 minutos antes do prazo."
            else:
                response_text = f"❌ Erro ao criar tarefa: {result.get('message')}"
            
            state["response"] = response_text
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            
            logger.info("Task created", task_id=result.get("task", {}).get("id"))
            
        except Exception as e:
            logger.error("Error creating task", error=str(e))
            state["response"] = f"Erro ao criar tarefa: {str(e)}"
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def _list_tasks(self, state: AgentState) -> AgentState:
        """List tasks.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Detect filters
        system_prompt = """Analise a mensagem e identifique filtros para listar tarefas.

Retorne JSON:
{
    "status": "pending|completed|all (padrão: pending)",
    "priority": "low|medium|high|urgent|null (padrão: null)"
}

Exemplos:
- "listar tarefas" -> {"status": "pending", "priority": null}
- "minhas tarefas concluídas" -> {"status": "completed", "priority": null}
- "tarefas urgentes" -> {"status": "pending", "priority": "urgent"}
- "todas as tarefas" -> {"status": "all", "priority": null}

Retorne apenas o JSON."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ])
            
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                filters = json.loads(json_match.group())
            else:
                filters = {"status": "pending", "priority": None}
            
            result = list_tasks(
                status=filters.get("status"),
                priority=filters.get("priority")
            )
            
            if result["status"] == "success":
                tasks = result.get("tasks", [])
                
                if not tasks:
                    filter_desc = "pendentes" if filters.get("status") == "pending" else filters.get("status", "")
                    response_text = f"📋 Você não tem tarefas {filter_desc}."
                else:
                    priority_emoji = {
                        "urgent": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢"
                    }
                    
                    status_desc = {
                        "pending": "pendentes",
                        "completed": "concluídas",
                        "all": "todas"
                    }.get(filters.get("status", "pending"), "")
                    
                    response_text = f"📋 **Suas tarefas {status_desc}:** ({len(tasks)})\n\n"
                    
                    for task in tasks:
                        status_icon = "✅" if task['status'] == "completed" else "⬜"
                        priority_icon = priority_emoji.get(task['priority'], '📋')
                        
                        response_text += f"{status_icon} {priority_icon} **{task['title']}** (ID: {task['id']})\n"
                        
                        if task.get('description'):
                            response_text += f"   📝 {task['description']}\n"
                        
                        if task.get('deadline'):
                            response_text += f"   ⏰ Prazo: {task['deadline']}\n"
                        
                        response_text += "\n"
            else:
                response_text = f"❌ Erro ao listar tarefas: {result.get('message')}"
            
            state["response"] = response_text
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            
            logger.info("Tasks listed", count=len(tasks) if result["status"] == "success" else 0)
            
        except Exception as e:
            logger.error("Error listing tasks", error=str(e))
            state["response"] = f"Erro ao listar tarefas: {str(e)}"
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def _complete_task(self, state: AgentState) -> AgentState:
        """Mark a task as completed.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # First, get pending tasks
        result = list_tasks(status="pending")
        
        if result["status"] != "success" or not result.get("tasks"):
            state["response"] = "Não encontrei tarefas pendentes para completar."
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            return state
        
        tasks = result["tasks"]
        
        # Use LLM to identify which task to complete
        system_prompt = f"""Você precisa identificar qual tarefa o usuário quer completar.

Tarefas pendentes:
"""
        for task in tasks:
            system_prompt += f"{task['id']}. {task['title']}\n"
        
        system_prompt += f"""
Analise a mensagem e retorne o ID da tarefa (número) ou 0 se não identificar.
Retorne apenas o número."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ])
            
            task_id = int(response.content.strip())
            
            if task_id == 0:
                response_text = "📋 **Tarefas pendentes:**\n\n"
                for task in tasks[:10]:  # Limit to 10
                    response_text += f"{task['id']}. {task['title']}\n"
                response_text += "\nQual tarefa você completou? Digite o ID."
                state["response"] = response_text
            else:
                # Find task title
                task_title = next((t['title'] for t in tasks if t['id'] == task_id), f"ID {task_id}")
                
                result = complete_task(task_id)
                
                if result["status"] == "success":
                    response_text = f"✅ Tarefa completada!\n\n**{task_title}** 🎉"
                else:
                    response_text = f"❌ Erro: {result.get('message')}"
                
                state["response"] = response_text
                logger.info("Task completed", task_id=task_id)
            
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            
        except Exception as e:
            logger.error("Error completing task", error=str(e))
            state["response"] = f"Erro ao completar tarefa: {str(e)}"
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def _delete_task(self, state: AgentState) -> AgentState:
        """Delete a task.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Get all tasks
        result = list_tasks(status="all")
        
        if result["status"] != "success" or not result.get("tasks"):
            state["response"] = "Não encontrei tarefas para deletar."
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            return state
        
        tasks = result["tasks"]
        
        # Use LLM to identify which task to delete
        system_prompt = f"""Você precisa identificar qual tarefa o usuário quer deletar.

Tarefas disponíveis:
"""
        for task in tasks:
            system_prompt += f"{task['id']}. {task['title']} [{task['status']}]\n"
        
        system_prompt += f"""
Analise a mensagem e retorne o ID da tarefa (número) ou 0 se não identificar.
Retorne apenas o número."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ])
            
            task_id = int(response.content.strip())
            
            if task_id == 0:
                response_text = "📋 **Tarefas disponíveis:**\n\n"
                for task in tasks[:10]:
                    status_icon = "✅" if task['status'] == "completed" else "⬜"
                    response_text += f"{task['id']}. {status_icon} {task['title']}\n"
                response_text += "\nQual tarefa você quer deletar? Digite o ID."
                state["response"] = response_text
            else:
                # Find task title
                task_title = next((t['title'] for t in tasks if t['id'] == task_id), f"ID {task_id}")
                
                result = delete_task(task_id)
                
                if result["status"] == "success":
                    response_text = f"🗑️ Tarefa deletada!\n\n**{task_title}**"
                else:
                    response_text = f"❌ Erro: {result.get('message')}"
                
                state["response"] = response_text
                logger.info("Task deleted", task_id=task_id)
            
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            
        except Exception as e:
            logger.error("Error deleting task", error=str(e))
            state["response"] = f"Erro ao deletar tarefa: {str(e)}"
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def _get_deadlines(self, state: AgentState) -> AgentState:
        """Get tasks with upcoming deadlines.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Detect time range
        system_prompt = """Analise a mensagem e determine quantos dias à frente ver prazos.

Retorne apenas um número:
- "hoje" -> 1
- "esta semana" -> 7
- "este mês" -> 30
- "próximos prazos" -> 7 (padrão)

Retorne apenas o número."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ])
            
            days = int(response.content.strip())
            
            result = get_upcoming_deadlines(days=days)
            
            if result["status"] == "success":
                tasks = result.get("tasks", [])
                
                if not tasks:
                    period_desc = "hoje" if days == 1 else f"nos próximos {days} dias"
                    response_text = f"📅 Você não tem tarefas com prazo {period_desc}."
                else:
                    period_desc = "hoje" if days == 1 else f"nos próximos {days} dias"
                    response_text = f"⏰ **Tarefas com prazo {period_desc}:** ({len(tasks)})\n\n"
                    
                    priority_emoji = {
                        "urgent": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢"
                    }
                    
                    for task in tasks:
                        priority_icon = priority_emoji.get(task['priority'], '📋')
                        deadline_str = task.get('deadline', '')
                        
                        # Format deadline
                        if 'T' in deadline_str:
                            dt = datetime.fromisoformat(deadline_str)
                            deadline_display = dt.strftime('%d/%m às %H:%M')
                        else:
                            deadline_display = deadline_str
                        
                        response_text += f"{priority_icon} **{task['title']}** (ID: {task['id']})\n"
                        response_text += f"   ⏰ {deadline_display}\n"
                        
                        if task.get('description'):
                            response_text += f"   📝 {task['description']}\n"
                        
                        response_text += "\n"
            else:
                response_text = f"❌ Erro: {result.get('message')}"
            
            state["response"] = response_text
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            
            logger.info("Deadlines retrieved", count=len(tasks) if result["status"] == "success" else 0)
            
        except Exception as e:
            logger.error("Error getting deadlines", error=str(e))
            state["response"] = f"Erro ao buscar prazos: {str(e)}"
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def process(self, state: AgentState) -> AgentState:
        """Process a task management request.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing task request", message=last_message[:50])
        
        # Detect action type
        action = self._detect_action(last_message)
        
        logger.info("Task action detected", action=action)
        
        # Route to appropriate handler
        if action == "create":
            return self._create_task(state)
        elif action == "list":
            return self._list_tasks(state)
        elif action == "complete":
            return self._complete_task(state)
        elif action == "delete":
            return self._delete_task(state)
        elif action == "update":
            state["response"] = "Função de atualização de tarefas ainda em desenvolvimento. Por favor, delete e crie novamente."
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            return state
        elif action == "deadlines":
            return self._get_deadlines(state)
        else:
            # Default to list
            return self._list_tasks(state)
