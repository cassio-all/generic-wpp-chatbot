"""Email agent for managing emails."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.tools import send_email, read_emails, search_emails
import structlog
import json
import re

logger = structlog.get_logger()


class EmailAgent:
    """Agent responsible for email operations."""
    
    def __init__(self):
        """Initialize the email agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process an email request.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing email request", message=last_message[:50])
        
        # Determine the type of email operation
        system_prompt = """Você é um assistente de email. Analise a mensagem e determine a ação:

AÇÕES DISPONÍVEIS:
1. "send" - Enviar um email
2. "read" - Ler emails recebidos
3. "search" - Buscar emails específicos

Responda APENAS com um JSON:
{
  "action": "send|read|search",
  "params": {
    // Para send:
    "to_email": "email",
    "subject": "assunto",
    "content": "conteúdo",
    "cc": ["email1", "email2"],  // opcional
    
    // Para read:
    "max_emails": número (padrão 5),
    "unread_only": true/false,
    
    // Para search:
    "query": "termo de busca",
    "max_results": número
  },
  "missing": "o que falta (se incompleto)"
}

Exemplos:
- "envie email para x@y.com sobre reunião" -> send
- "leia meus últimos emails" -> read
- "busque emails de João" -> search"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Mensagem: {last_message}")
            ])
            
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if not json_match:
                state["response"] = "Desculpe, não entendi o que você quer fazer com emails."
                return state
            
            email_request = json.loads(json_match.group())
            action = email_request.get("action")
            params = email_request.get("params", {})
            missing = email_request.get("missing")
            
            if missing:
                state["response"] = f"Para realizar esta ação, preciso de: {missing}"
                return state
            
            # Execute action
            if action == "send":
                result = self._send_email(params)
            elif action == "read":
                result = self._read_emails(params)
            elif action == "search":
                result = self._search_emails(params)
            else:
                result = {"status": "error", "message": "Ação desconhecida"}
            
            state["response"] = result.get("message", "Operação concluída")
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            
            logger.info("Email operation processed", action=action, status=result.get("status"))
            
        except Exception as e:
            logger.error("Error processing email request", error=str(e))
            state["response"] = "Desculpe, ocorreu um erro. Por favor, tente novamente."
        
        return state
    
    def _send_email(self, params: dict) -> dict:
        """Send an email."""
        result = send_email(
            to_email=params.get("to_email", ""),
            subject=params.get("subject", ""),
            content=params.get("content", ""),
            cc=params.get("cc"),
            bcc=params.get("bcc")
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"✅ Email enviado!\n\n📧 Para: {params.get('to_email')}\n📝 Assunto: {params.get('subject')}"
            }
        else:
            return {
                "status": "error",
                "message": f"❌ Erro: {result['message']}"
            }
    
    def _read_emails(self, params: dict) -> dict:
        """Read recent emails."""
        max_emails = min(params.get("max_emails", 5), 10)
        unread_only = params.get("unread_only", False)
        
        result = read_emails(max_emails=max_emails, unread_only=unread_only)
        
        if result["status"] == "error":
            return {"status": "error", "message": f"❌ {result['message']}"}
        
        emails = result.get("emails", [])
        
        if not emails:
            msg = "📬 Nenhum email " + ("não lido" if unread_only else "") + " encontrado."
            return {"status": "success", "message": msg}
        
        # Format email list
        response = f"📨 **{len(emails)} email(s)**:\n\n"
        for i, email in enumerate(emails, 1):
            response += f"**{i}. {email['subject']}**\n"
            response += f"   📤 De: {email['from']}\n"
            response += f"   📅 {email['date']}\n"
            if email.get('body'):
                preview = email['body'][:150].replace('\n', ' ')
                response += f"   💬 {preview}...\n"
            response += "\n"
        
        return {"status": "success", "message": response}
    
    def _search_emails(self, params: dict) -> dict:
        """Search for emails."""
        query = params.get("query", "")
        max_results = min(params.get("max_results", 10), 20)
        
        result = search_emails(query=query, max_emails=max_results)
        
        if result["status"] == "error":
            return {"status": "error", "message": f"❌ {result['message']}"}
        
        emails = result.get("emails", [])
        
        if not emails:
            return {"status": "success", "message": f"🔍 Nenhum email encontrado com '{query}'"}
        
        response = f"🔍 **{len(emails)} email(s) com '{query}':**\n\n"
        for i, email in enumerate(emails, 1):
            response += f"**{i}. {email['subject']}**\n"
            response += f"   📤 De: {email['from']}\n"
            response += f"   📅 {email['date']}\n\n"
        
        return {"status": "success", "message": response}
