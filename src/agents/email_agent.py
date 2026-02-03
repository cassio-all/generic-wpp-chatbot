"""Email agent for sending emails."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.tools import send_email
import structlog
import json
import re

logger = structlog.get_logger()


class EmailAgent:
    """Agent responsible for sending emails."""
    
    def __init__(self):
        """Initialize the email agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process an email sending request.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing email sending request", message=last_message[:50])
        
        system_prompt = """Você é um assistente de e-mail. Analise a mensagem do usuário e extraia:
1. E-mail do destinatário
2. Assunto do e-mail
3. Conteúdo do e-mail

Se alguma informação estiver faltando, pergunte ao usuário.

Responda APENAS com um JSON no formato:
{
  "has_all_info": true/false,
  "to_email": "destinatario@example.com",
  "subject": "Assunto do e-mail",
  "content": "Conteúdo do e-mail",
  "missing": "lista do que está faltando"
}"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Mensagem do usuário: {last_message}")
            ])
            
            # Extract JSON from response
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if not json_match:
                state["response"] = "Desculpe, não consegui processar sua solicitação de e-mail. Pode fornecer mais detalhes?"
                return state
            
            email_info = json.loads(json_match.group())
            
            if not email_info.get("has_all_info", False):
                missing = email_info.get("missing", "algumas informações")
                state["response"] = f"Para enviar o e-mail, preciso de: {missing}"
                return state
            
            # Send the email
            result = send_email(
                to_email=email_info.get("to_email"),
                subject=email_info.get("subject"),
                content=email_info.get("content")
            )
            
            if result["status"] == "success":
                response_text = f"✅ E-mail enviado com sucesso!\n\n"
                response_text += f"📧 Para: {email_info.get('to_email')}\n"
                response_text += f"📝 Assunto: {email_info.get('subject')}"
            else:
                response_text = f"❌ Não foi possível enviar o e-mail: {result.get('message')}"
            
            state["response"] = response_text
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            
            logger.info("Email sending processed", status=result["status"])
            
        except Exception as e:
            logger.error("Error processing email sending", error=str(e))
            state["response"] = "Desculpe, ocorreu um erro ao enviar o e-mail. Por favor, tente novamente."
        
        return state
