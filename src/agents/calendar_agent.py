"""Calendar agent for scheduling meetings."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.tools import (
    schedule_meeting,
    check_conflicts,
    find_available_slots,
    cancel_meeting,
    update_meeting
)
import structlog
import json
import re
from datetime import datetime, timedelta, timezone

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
    
    def _handle_reschedule_time(self, state: AgentState) -> AgentState:
        """Handle rescheduling of existing meeting to new time.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        pending_meeting = state.get("pending_meeting", {})
        conflicts = state.get("conflicting_events", [])
        
        if not conflicts:
            state["response"] = "Não encontrei a reunião a ser remanejada."
            state["awaiting_reschedule_time"] = False
            return state
        
        # Parse the new time using LLM
        now_local = datetime.now()
        current_date = now_local.strftime("%Y-%m-%d")
        current_time = now_local.strftime("%H:%M")
        
        system_prompt = f"""Você é um assistente de parsing de horários. HORA ATUAL: {current_time} do dia {current_date}.

Extraia o novo horário da mensagem do usuário e converta para ISO format.

REGRAS:
- HOJE = {current_date}
- AMANHÃ = {(now_local + timedelta(days=1)).strftime("%Y-%m-%d")}
- "20h" ou "20hrs" = 20:00:00
- Retorne apenas no formato: YYYY-MM-DDTHH:MM:SS

Exemplo de resposta: 2026-02-03T20:00:00"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Mensagem: {last_message}")
            ])
            
            new_time = response.content.strip()
            
            # Validate ISO format
            datetime.fromisoformat(new_time)
            
            # Get duration from conflicting event by calculating start-end difference
            conflict_event = conflicts[0]
            
            # Parse start and end times to calculate actual duration
            import re
            start_str = conflict_event['start']
            end_str = conflict_event['end']
            
            start_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', start_str)
            end_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', end_str)
            
            if start_match and end_match:
                start_dt = datetime.fromisoformat(start_match.group(1))
                end_dt = datetime.fromisoformat(end_match.group(1))
                duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            else:
                duration_minutes = 60  # Fallback to 60 minutes if parsing fails
            
            logger.info("Rescheduling event", event_summary=conflict_event['summary'], original_duration=duration_minutes)
            
            # Update the existing meeting to new time
            update_result = update_meeting(
                event_id=conflict_event['id'],
                new_start_time=new_time,
                duration_minutes=duration_minutes
            )
            
            if update_result["status"] == "success":
                # Now schedule the new meeting at the original time
                schedule_result = schedule_meeting(
                    summary=pending_meeting.get("summary"),
                    start_time=pending_meeting.get("start_time"),
                    duration_minutes=pending_meeting.get("duration_minutes", 60),
                    attendees=pending_meeting.get("attendees", [])
                )
                
                if schedule_result["status"] == "success":
                    response_text = f"✅ Reuniões remanejadas com sucesso!\n\n"
                    response_text += f"🔄 **{conflict_event['summary']}** movida para {new_time}\n"
                    response_text += f"✅ **{pending_meeting.get('summary')}** agendada para {pending_meeting.get('start_time')}\n"
                    if schedule_result.get("link"):
                        response_text += f"🔗 {schedule_result['link']}"
                else:
                    response_text = f"⚠️ Reunião antiga movida, mas erro ao agendar nova: {schedule_result.get('message')}"
            else:
                response_text = f"❌ Erro ao remanejar reunião: {update_result.get('message')}"
            
            state["response"] = response_text
            state["pending_meeting"] = None
            state["conflicting_events"] = None
            state["awaiting_reschedule_time"] = False
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            
            logger.info("Meeting rescheduled", new_time=new_time)
            
        except Exception as e:
            logger.error("Error rescheduling meeting", error=str(e))
            state["response"] = "Desculpe, não consegui interpretar o novo horário. Tente novamente com formato como 'hoje 20h' ou 'amanhã 15h'."
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def _handle_slot_selection(self, state: AgentState) -> AgentState:
        """Handle user selecting a suggested time slot.
        
        Args:
            state: Current agent state with suggested slots
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        pending_meeting = state.get("pending_meeting", {})
        suggested_slots = state.get("suggested_slots", [])
        
        if not pending_meeting or not suggested_slots:
            state["response"] = "Não encontrei horários sugeridos. Por favor, tente novamente."
            state["suggested_slots"] = None
            return state
        
        # Try to parse the selection
        try:
            # Extract number from message
            import re
            number_match = re.search(r'\b([1-3])\b', last_message)
            
            if number_match:
                selection = int(number_match.group(1)) - 1
                
                if 0 <= selection < len(suggested_slots):
                    selected_slot = suggested_slots[selection]
                    
                    # Schedule meeting at selected time
                    result = schedule_meeting(
                        summary=pending_meeting.get("summary"),
                        start_time=selected_slot['start'],
                        duration_minutes=pending_meeting.get("duration_minutes", 60),
                        attendees=pending_meeting.get("attendees", [])
                    )
                    
                    if result["status"] == "success":
                        slot_time = selected_slot['start'].split('T')[1][:5]
                        response_text = f"✅ Reunião agendada com sucesso!\n\n"
                        response_text += f"📅 {pending_meeting.get('summary')}\n"
                        response_text += f"🕐 Hoje às {slot_time}\n"
                        response_text += f"⏱️ Duração: {pending_meeting.get('duration_minutes')} minutos\n"
                        if result.get("link"):
                            response_text += f"🔗 {result['link']}"
                    else:
                        response_text = f"❌ Erro ao agendar: {result.get('message')}"
                    
                    state["response"] = response_text
                    state["pending_meeting"] = None
                    state["suggested_slots"] = None
                    state["conflicting_events"] = None
                else:
                    response_text = f"Por favor, escolha um número entre 1 e {len(suggested_slots)}."
                    state["response"] = response_text
            else:
                response_text = "Por favor, digite o número do horário desejado (1, 2 ou 3)."
                state["response"] = response_text
            
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            logger.info("Slot selection handled", selection=number_match.group(1) if number_match else None)
            
        except Exception as e:
            logger.error("Error handling slot selection", error=str(e))
            state["response"] = "Desculpe, não consegui processar sua escolha. Digite o número do horário (1, 2 ou 3)."
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def _handle_conflict_resolution(self, state: AgentState) -> AgentState:
        """Handle user's decision about conflict resolution.
        
        Args:
            state: Current agent state with pending meeting and conflicts
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        pending_meeting = state.get("pending_meeting", {})
        conflicts = state.get("conflicting_events", [])
        
        # Check if user is providing new time for rescheduling
        if state.get("awaiting_reschedule_time"):
            return self._handle_reschedule_time(state)
        
        # Check if user is selecting from suggested time slots
        if state.get("suggested_slots"):
            return self._handle_slot_selection(state)
        
        if not pending_meeting:
            state["response"] = "Não encontrei uma reunião pendente. Por favor, tente agendar novamente."
            return state
        
        # Parse user choice
        choice = last_message.strip()
        
        try:
            if "1" in choice or "sobrepor" in choice.lower() or "agendar" in choice.lower():
                # Option 1: Schedule anyway
                result = schedule_meeting(
                    summary=pending_meeting.get("summary"),
                    start_time=pending_meeting.get("start_time"),
                    duration_minutes=pending_meeting.get("duration_minutes", 60),
                    attendees=pending_meeting.get("attendees", [])
                )
                
                if result["status"] == "success":
                    response_text = f"✅ Reunião agendada (com sobreposição)!\n\n"
                    response_text += f"📅 {pending_meeting.get('summary')}\n"
                    response_text += f"🕐 {pending_meeting.get('start_time')}\n"
                    if result.get("link"):
                        response_text += f"🔗 {result['link']}"
                else:
                    response_text = f"❌ Erro ao agendar: {result.get('message')}"
                
                state["response"] = response_text
                state["pending_meeting"] = None
                state["conflicting_events"] = None
                
            elif "2" in choice or "cancelar" in choice.lower() and "existente" in choice.lower():
                # Option 2: Cancel existing and schedule new
                if conflicts:
                    cancel_result = cancel_meeting(conflicts[0]['id'])
                    
                    if cancel_result["status"] == "success":
                        result = schedule_meeting(
                            summary=pending_meeting.get("summary"),
                            start_time=pending_meeting.get("start_time"),
                            duration_minutes=pending_meeting.get("duration_minutes", 60),
                            attendees=pending_meeting.get("attendees", [])
                        )
                        
                        if result["status"] == "success":
                            response_text = f"✅ Reunião antiga cancelada e nova agendada!\n\n"
                            response_text += f"❌ Cancelado: {conflicts[0]['summary']}\n"
                            response_text += f"✅ Novo: {pending_meeting.get('summary')}\n"
                            response_text += f"🕐 {pending_meeting.get('start_time')}\n"
                            if result.get("link"):
                                response_text += f"🔗 {result['link']}"
                        else:
                            response_text = f"⚠️ Reunião antiga cancelada, mas erro ao agendar nova: {result.get('message')}"
                    else:
                        response_text = f"❌ Erro ao cancelar reunião existente: {cancel_result.get('message')}"
                    
                    state["response"] = response_text
                    state["pending_meeting"] = None
                    state["conflicting_events"] = None
                
            elif "3" in choice or "remanejar" in choice.lower():
                # Option 3: Reschedule existing meeting
                response_text = "🔄 Para remanejar a reunião existente, por favor informe:\n\n"
                response_text += f"Reunião a ser remanejada: **{conflicts[0]['summary']}**\n\n"
                response_text += "Qual o novo horário? (ex: 'amanhã 16h' ou 'hoje 20h')"
                
                state["response"] = response_text
                state["awaiting_reschedule_time"] = True
                
            elif "4" in choice or "sugerir" in choice.lower() or "alternativ" in choice.lower():
                # Option 4: Suggest alternative times
                start_time = pending_meeting.get("start_time")
                date = start_time.split('T')[0]
                duration = pending_meeting.get("duration_minutes", 60)
                
                suggestions = find_available_slots(date, duration, num_suggestions=3)
                
                if suggestions["status"] == "success" and suggestions.get("available_slots"):
                    response_text = "💡 **Horários alternativos livres:**\n\n"
                    for idx, slot in enumerate(suggestions["available_slots"], 1):
                        slot_time = slot['start'].split('T')[1][:5]
                        response_text += f"{idx}. Hoje às {slot_time}\n"
                    
                    response_text += "\nGostaria de agendar em algum desses horários? (digite o número)"
                    state["suggested_slots"] = suggestions["available_slots"]
                else:
                    response_text = "😕 Não encontrei horários livres hoje. Deseja tentar outro dia?"
                
                state["response"] = response_text
                
            elif "5" in choice or ("cancelar" in choice.lower() and "nova" in choice.lower()):
                # Option 5: Cancel new meeting
                response_text = "❌ Nova reunião cancelada. Sua agenda permanece inalterada."
                state["response"] = response_text
                state["pending_meeting"] = None
                state["conflicting_events"] = None
                
            else:
                response_text = "Não entendi sua escolha. Por favor, digite o número (1-5) da opção desejada."
                state["response"] = response_text
            
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            logger.info("Conflict resolution handled", choice=choice)
            
        except Exception as e:
            logger.error("Error handling conflict resolution", error=str(e))
            state["response"] = "Desculpe, ocorreu um erro. Por favor, tente novamente."
        
        return state
    
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
        
        # Check if user is responding to a conflict resolution
        if state.get("pending_meeting") or state.get("awaiting_reschedule_time"):
            return self._handle_conflict_resolution(state)
        
        try:
            # Use local time instead of UTC to properly handle "hoje", "amanhã"
            now_local = datetime.now()
            current_date = now_local.strftime("%Y-%m-%d")
            current_time = now_local.strftime("%H:%M")
            
            system_prompt = f"""Você é um assistente de agendamento. HORA ATUAL: {current_time} do dia {current_date}.

Extraia da mensagem do usuário:
1. Título da reunião
2. Data e hora no formato ISO: YYYY-MM-DDTHH:MM:SS
3. Duração em minutos
4. E-mails dos participantes

REGRAS IMPORTANTES:
- HOJE = {current_date} (data de hoje)
- AMANHÃ = {(now_local + timedelta(days=1)).strftime("%Y-%m-%d")}
- Se usuário diz "18h" ou "18hrs", a hora é 18:00:00
- Se usuário diz "14h", a hora é 14:00:00
- NUNCA mude o horário que o usuário especificou!
- Se a hora ainda não passou hoje (agora são {current_time}), agende para HOJE
- Se a hora já passou hoje, agende para AMANHÃ no mesmo horário

EXEMPLO: Se agora são 16:55 e o usuário pede "hoje 18h", agende para {current_date}T18:00:00 (ainda não passou!)

Responda APENAS JSON (sem markdown):
{{
  "has_all_info": true,
  "summary": "título",
  "start_time": "YYYY-MM-DDTHH:MM:SS",
  "duration_minutes": 60,
  "attendees": ["email@example.com"],
  "missing": ""
}}

OU se faltar info:
{{
  "has_all_info": false,
  "missing": "o que falta"
}}"""
            
            user_message = f"Mensagem: {last_message}"
            
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            
            # DEBUG: Log the LLM response
            logger.info("LLM response for calendar", response_content=response.content)
            
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
            
            # Check for conflicts before scheduling
            start_time = meeting_info.get("start_time")
            duration = meeting_info.get("duration_minutes", 60)
            start_dt = datetime.fromisoformat(start_time)
            end_dt = start_dt + timedelta(minutes=duration)
            
            conflict_check = check_conflicts(start_time, end_dt.isoformat())
            
            if conflict_check.get("has_conflict"):
                conflicts = conflict_check.get("conflicts", [])
                
                # Format conflict message
                response_text = "⚠️ **Conflito de horário detectado!**\n\n"
                response_text += f"Você já tem {len(conflicts)} reunião(ões) agendada(s) neste horário:\n\n"
                
                for idx, conflict in enumerate(conflicts, 1):
                    conflict_start = conflict['start'].split('T')[1][:5] if 'T' in conflict['start'] else conflict['start']
                    response_text += f"{idx}. **{conflict['summary']}** às {conflict_start}\n"
                
                response_text += "\n**O que deseja fazer?**\n"
                response_text += "1️⃣ Agendar mesmo assim (sobrepor)\n"
                response_text += "2️⃣ Cancelar a reunião existente e agendar esta\n"
                response_text += "3️⃣ Remanejar a reunião existente para outro horário\n"
                response_text += "4️⃣ Sugerir horários alternativos livres\n"
                response_text += "5️⃣ Cancelar esta nova reunião\n\n"
                response_text += "Digite o número da opção desejada."
                
                # Store meeting info in state for later use
                state["pending_meeting"] = meeting_info
                state["conflicting_events"] = conflicts
                state["response"] = response_text
                state["messages"] = state["messages"] + [AIMessage(content=response_text)]
                
                logger.info("Conflict detected", conflicts=len(conflicts))
                return state
            
            # No conflicts, proceed with scheduling
            result = schedule_meeting(
                summary=meeting_info.get("summary", "Reunião"),
                start_time=start_time,
                duration_minutes=duration,
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
