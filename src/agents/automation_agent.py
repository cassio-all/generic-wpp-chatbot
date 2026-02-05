"""Automation agent for intelligent cross-agent workflows."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.agents.integration import AgentIntegration
import structlog

logger = structlog.get_logger()


class AutomationAgent:
    """Agent responsible for automated workflows and integrations."""
    
    def __init__(self):
        """Initialize the automation agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        self.integration = AgentIntegration()
    
    def process(self, state: AgentState) -> AgentState:
        """Process automation requests.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing automation request", message=last_message[:50])
        
        # Check for "lembrar de" intent
        task_intent = self.integration.detect_task_creation_intent(last_message)
        
        if task_intent:
            return self._handle_reminder(state, task_intent)
        
        # Check for daily summary request
        if any(word in last_message.lower() for word in ["resumo", "summary", "resumir", "hoje"]):
            return self._handle_daily_summary(state)
        
        # Default: explain automation capabilities
        return self._explain_capabilities(state)
    
    def _handle_reminder(self, state: AgentState, task_intent: dict) -> AgentState:
        """Handle 'lembrar de' requests by creating tasks.
        
        Args:
            state: Current agent state
            task_intent: Detected task information
            
        Returns:
            Updated state
        """
        result = self.integration.smart_create_task_with_calendar(
            title=task_intent["title"],
            priority=task_intent["priority"]
        )
        
        if result["task"]:
            task = result["task"]
            response_text = f"✅ Ok, vou lembrar!\n\n"
            response_text += f"📝 Tarefa criada: **{task['title']}**\n"
            response_text += f"🆔 ID: {task['id']}\n"
            
            if result.get("auto_calendar"):
                response_text += f"\n🔔 Também criei um lembrete no calendário!"
        else:
            response_text = "Desculpe, não consegui criar o lembrete."
        
        state["response"] = response_text
        state["messages"] = state["messages"] + [AIMessage(content=response_text)]
        
        logger.info("Reminder created via automation", title=task_intent["title"])
        
        return state
    
    def _handle_daily_summary(self, state: AgentState) -> AgentState:
        """Generate and return daily summary.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        summary = self.integration.get_daily_summary()
        
        response_text = "📊 **Resumo do Dia**\n\n"
        response_text += f"📋 Tarefas pendentes: {summary.get('pending_tasks', 0)}\n"
        response_text += f"⏰ Prazos próximos (3 dias): {summary.get('upcoming_deadlines', 0)}\n"
        response_text += f"⚠️ Tarefas atrasadas: {summary.get('overdue_tasks', 0)}\n"
        
        if summary.get('overdue_tasks', 0) > 0:
            response_text += "\n🚨 **Tarefas atrasadas:**\n"
            for task in summary.get('overdue', [])[:5]:
                response_text += f"  • {task.get('title')} (Prazo: {task.get('deadline')})\n"
        
        state["response"] = response_text
        state["messages"] = state["messages"] + [AIMessage(content=response_text)]
        
        logger.info("Daily summary generated")
        
        return state
    
    def _explain_capabilities(self, state: AgentState) -> AgentState:
        """Explain automation capabilities.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        response_text = """🤖 **Automações Inteligentes Disponíveis:**

✅ **Lembretes Rápidos**
Diga "lembrar de [algo]" e eu crio uma tarefa automaticamente!
Exemplo: "lembrar de comprar pão"

📅 **Auto-Calendário**
Tarefas urgentes com prazo próximo viram eventos no calendário automaticamente!

📊 **Resumo Diário**
Peça "resumo do dia" para ver suas tarefas, prazos e pendências.

🔔 **Alertas de Prazo**
Tarefas com deadline próximo geram notificações automáticas.

💡 **Como usar:**
- "lembrar de ligar pro João"
- "resumo do dia"
- "criar tarefa urgente revisar código até amanhã" (cria task + evento)"""

        state["response"] = response_text
        state["messages"] = state["messages"] + [AIMessage(content=response_text)]
        
        return state
