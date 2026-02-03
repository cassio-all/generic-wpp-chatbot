"""Calendar agent for scheduling meetings."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.tools import schedule_meeting
import structlog
import json
import re
from datetime import datetime, timedelta

logger = structlog.get_logger()


class CalendarAgent:
    """Agent responsible for scheduling meetings."""
    
    def __init__(self):
        """Initialize the calendar agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process a meeting scheduling request.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing meeting scheduling request", message=last_message[:50])
        
        system_prompt = """Você é um assistente de agendamento. Analise a mensagem do usuário e extraia:
1. Título/assunto da reunião
2. Data e hora (formato ISO: YYYY-MM-DDTHH:MM:SS)
3. Duração em minutos
4. E-mails dos participantes (se mencionados)

Se alguma informação estiver faltando, pergunte ao usuário.

Responda APENAS com um JSON no formato:
{
  "has_all_info": true/false,
  "summary": "título da reunião",
  "start_time": "2024-03-20T10:00:00",
  "duration_minutes": 60,
  "attendees": ["email1@example.com"],
  "missing": "lista do que está faltando"
}"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Mensagem do usuário: {last_message}\nData/hora atual: {datetime.now().isoformat()}")
            ])
            
            # Extract JSON from response
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if not json_match:
                state["response"] = "Desculpe, não consegui processar sua solicitação de agendamento. Pode fornecer mais detalhes sobre a reunião?"
                return state
            
            meeting_info = json.loads(json_match.group())
            
            if not meeting_info.get("has_all_info", False):
                missing = meeting_info.get("missing", "algumas informações")
                state["response"] = f"Para agendar a reunião, preciso de: {missing}"
                return state
            
            # Schedule the meeting
            result = schedule_meeting(
                summary=meeting_info.get("summary", "Reunião"),
                start_time=meeting_info.get("start_time"),
                duration_minutes=meeting_info.get("duration_minutes", 60),
                attendees=meeting_info.get("attendees", [])
            )
            
            if result["status"] == "success":
                response_text = f"✅ Reunião agendada com sucesso!\n\n"
                response_text += f"📅 {meeting_info.get('summary')}\n"
                response_text += f"🕐 {meeting_info.get('start_time')}\n"
                response_text += f"⏱️ Duração: {meeting_info.get('duration_minutes')} minutos\n"
                if result.get("link"):
                    response_text += f"🔗 Link: {result['link']}"
            else:
                response_text = f"❌ Não foi possível agendar a reunião: {result.get('message')}"
            
            state["response"] = response_text
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            
            logger.info("Meeting scheduling processed", status=result["status"])
            
        except Exception as e:
            logger.error("Error processing meeting scheduling", error=str(e))
            state["response"] = "Desculpe, ocorreu um erro ao agendar a reunião. Por favor, tente novamente."
        
        return state
