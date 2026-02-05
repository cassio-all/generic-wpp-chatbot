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
    update_meeting,
    list_upcoming_events,
    get_event_details,
    add_attendees_to_event
)
import structlog
import json
import re
from datetime import datetime, timedelta, timezone

logger = structlog.get_logger()


class CalendarAgent:
    """Agent responsible for managing calendar events."""
    
    def __init__(self):
        """Initialize the calendar agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
    
    def _detect_action(self, message: str) -> str:
        """Detect what calendar action the user wants.
        
        Args:
            message: User message
            
        Returns:
            Action type: schedule, list, cancel, edit, or details
        """
        system_prompt = """Você é um assistente que detecta intenções relacionadas ao calendário.

Analise a mensagem do usuário e retorne APENAS UMA palavra:
- "schedule" - usuário quer AGENDAR/CRIAR uma nova reunião
- "list" - usuário quer VER/LISTAR reuniões futuras
- "cancel" - usuário quer CANCELAR uma reunião
- "edit" - usuário quer EDITAR/MUDAR horário de uma reunião
- "details" - usuário quer ver DETALHES de uma reunião específica
- "add_attendees" - usuário quer ADICIONAR participantes a uma reunião

Exemplos:
- "agendar reunião amanhã" -> schedule
- "listar minhas reuniões" -> list
- "quais são meus compromissos" -> list
- "cancelar a reunião de amanhã" -> cancel
- "mudar reunião para 16h" -> edit
- "adicionar joão na reunião" -> add_attendees
- "ver detalhes da reunião" -> details

Retorne apenas a palavra."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=message)
            ])
            
            action = response.content.strip().lower()
            logger.info("Detected calendar action", action=action)
            return action
            
        except Exception as e:
            logger.error("Error detecting action", error=str(e))
            return "schedule"  # Default to schedule
    
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
        """Process a calendar request.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing calendar request", message=last_message[:50])
        
        # Check if user is responding to a conflict resolution or pending action
        if state.get("pending_meeting") or state.get("awaiting_reschedule_time"):
            return self._handle_conflict_resolution(state)
        
        # Detect action type
        action = self._detect_action(last_message)
        
        logger.info("Calendar action detected", action=action)
        
        # Route to appropriate handler
        if action == "list":
            return self._list_events(state)
        elif action == "cancel":
            return self._cancel_event(state)
        elif action == "edit":
            return self._edit_event(state)
        elif action == "schedule":
            return self._schedule_meeting(state)
        elif action == "details":
            # For now, redirect to list
            return self._list_events(state)
        elif action == "add_attendees":
            state["response"] = "Função de adicionar participantes ainda em desenvolvimento."
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            return state
        else:
            # Default to scheduling
            return self._schedule_meeting(state)
    
    def _schedule_meeting(self, state: AgentState) -> AgentState:
        """Handle scheduling a new meeting.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
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
    def _list_events(self, state: AgentState) -> AgentState:
        """List upcoming calendar events.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Detect time range (today, week, month, all)
        system_prompt = """Analise a mensagem e determine quantos dias à frente o usuário quer ver eventos.

Retorne apenas um número (dias) ou "all":
- "hoje" -> 1
- "esta semana" ou "semana" -> 7
- "este mês" ou "mês" -> 30
- "próximos eventos" ou nada específico -> all

Exemplos:
- "minhas reuniões de hoje" -> 1
- "o que tenho esta semana" -> 7
- "listar todos eventos" -> all"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ])
            
            days_str = response.content.strip().lower()
            days_ahead = None if days_str == "all" else int(days_str)
            
            result = list_upcoming_events(max_results=20, days_ahead=days_ahead)
            
            if result["status"] == "success":
                events = result.get("events", [])
                
                if not events:
                    response_text = "📅 Você não tem eventos agendados no período solicitado."
                else:
                    period = "hoje" if days_ahead == 1 else f"nos próximos {days_ahead} dias" if days_ahead else "futuros"
                    response_text = f"📅 **Seus eventos {period}:**\n\n"
                    
                    for idx, event in enumerate(events, 1):
                        summary = event.get('summary', 'Sem título')
                        start = event.get('start', '')
                        
                        # Format date/time
                        if 'T' in start:
                            dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                            date_str = dt.strftime('%d/%m')
                            time_str = dt.strftime('%H:%M')
                            response_text += f"{idx}. **{summary}**\n   📆 {date_str} às {time_str}\n"
                        else:
                            response_text += f"{idx}. **{summary}**\n   📆 {start}\n"
                        
                        # Add attendees if present
                        attendees = event.get('attendees', [])
                        if attendees:
                            attendee_emails = [a.get('email') for a in attendees if a.get('email')]
                            if attendee_emails:
                                response_text += f"   👥 {', '.join(attendee_emails[:3])}"
                                if len(attendee_emails) > 3:
                                    response_text += f" +{len(attendee_emails)-3} mais"
                                response_text += "\n"
                        
                        response_text += "\n"
            else:
                response_text = f"❌ Erro ao listar eventos: {result.get('message')}"
            
            state["response"] = response_text
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            
            logger.info("Events listed", count=len(events) if result["status"] == "success" else 0)
            
        except Exception as e:
            logger.error("Error listing events", error=str(e))
            state["response"] = f"Erro ao listar eventos: {str(e)}"
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def _cancel_event(self, state: AgentState) -> AgentState:
        """Cancel a calendar event.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # First, list recent events to find which one to cancel
        result = list_upcoming_events(max_results=10, days_ahead=7)
        
        if result["status"] != "success" or not result.get("events"):
            state["response"] = "Não encontrei eventos para cancelar."
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            return state
        
        events = result["events"]
        
        # Use LLM to identify which event to cancel
        system_prompt = f"""Você precisa identificar qual evento o usuário quer cancelar.

Eventos disponíveis:
"""
        for idx, event in enumerate(events, 1):
            summary = event.get('summary', 'Sem título')
            start = event.get('start', '')
            system_prompt += f"{idx}. {summary} - {start}\n"
        
        system_prompt += """
Analise a mensagem do usuário e retorne o número do evento que ele quer cancelar (1 a """ + str(len(events)) + """).
Se não conseguir identificar, retorne "0".

Retorne apenas o número."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ])
            
            event_number = int(response.content.strip())
            
            if event_number < 1 or event_number > len(events):
                response_text = "📅 **Eventos disponíveis para cancelar:**\n\n"
                for idx, event in enumerate(events, 1):
                    summary = event.get('summary', 'Sem título')
                    start = event.get('start', '')
                    if 'T' in start:
                        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        date_str = dt.strftime('%d/%m às %H:%M')
                    else:
                        date_str = start
                    response_text += f"{idx}. **{summary}** - {date_str}\n"
                
                response_text += "\nQual evento você deseja cancelar? Digite o número."
                state["response"] = response_text
            else:
                event_to_cancel = events[event_number - 1]
                event_id = event_to_cancel.get('id')
                
                cancel_result = cancel_meeting(event_id)
                
                if cancel_result["status"] == "success":
                    response_text = f"✅ Evento cancelado com sucesso!\n\n"
                    response_text += f"❌ **{event_to_cancel.get('summary')}**"
                else:
                    response_text = f"❌ Erro ao cancelar: {cancel_result.get('message')}"
                
                state["response"] = response_text
                logger.info("Event cancelled", event_id=event_id)
            
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            
        except Exception as e:
            logger.error("Error cancelling event", error=str(e))
            state["response"] = f"Erro ao cancelar evento: {str(e)}"
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state
    
    def _edit_event(self, state: AgentState) -> AgentState:
        """Edit an existing calendar event.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # List recent events
        result = list_upcoming_events(max_results=10, days_ahead=7)
        
        if result["status"] != "success" or not result.get("events"):
            state["response"] = "Não encontrei eventos para editar."
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            return state
        
        events = result["events"]
        
        # Identify event and new time
        system_prompt = f"""Você precisa identificar qual evento editar e o novo horário.

Eventos disponíveis:
"""
        for idx, event in enumerate(events, 1):
            summary = event.get('summary', 'Sem título')
            start = event.get('start', '')
            system_prompt += f"{idx}. {summary} - {start}\n"
        
        system_prompt += """
Analise a mensagem e retorne JSON:
{
    "event_number": <número do evento 1 a """ + str(len(events)) + """, ou 0 se não identificar>,
    "new_time": "<novo horário em formato ISO YYYY-MM-DDTHH:MM:SS ou vazio se não especificado>"
}

Data/hora atual: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """

Exemplos:
- "mudar reunião 1 para amanhã 15h" -> {"event_number": 1, "new_time": "2026-...-15:00:00"}
- "editar a reunião de projeto" -> {"event_number": <número correspondente>, "new_time": ""}"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ])
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            edit_info = json.loads(json_match.group())
            event_number = edit_info.get("event_number", 0)
            new_time = edit_info.get("new_time", "")
            
            if event_number < 1 or event_number > len(events):
                response_text = "📅 **Eventos disponíveis para editar:**\n\n"
                for idx, event in enumerate(events, 1):
                    summary = event.get('summary', 'Sem título')
                    start = event.get('start', '')
                    if 'T' in start:
                        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        date_str = dt.strftime('%d/%m às %H:%M')
                    else:
                        date_str = start
                    response_text += f"{idx}. **{summary}** - {date_str}\n"
                
                response_text += "\nQual evento você deseja editar e para qual horário?"
                state["response"] = response_text
            elif not new_time:
                event_to_edit = events[event_number - 1]
                response_text = f"📅 Evento selecionado: **{event_to_edit.get('summary')}**\n\n"
                response_text += "Para qual horário você quer mudar? (ex: amanhã 15h, hoje 18h)"
                state["response"] = response_text
            else:
                event_to_edit = events[event_number - 1]
                event_id = event_to_edit.get('id')
                
                # Calculate duration from original event
                start_str = event_to_edit.get('start', '')
                end_str = event_to_edit.get('end', '')
                
                duration_minutes = 60  # Default
                if 'T' in start_str and 'T' in end_str:
                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                
                edit_result = update_meeting(
                    event_id=event_id,
                    new_start_time=new_time,
                    duration_minutes=duration_minutes
                )
                
                if edit_result["status"] == "success":
                    response_text = f"✅ Evento atualizado com sucesso!\n\n"
                    response_text += f"📅 **{event_to_edit.get('summary')}**\n"
                    response_text += f"🕐 Novo horário: {new_time}"
                else:
                    response_text = f"❌ Erro ao editar: {edit_result.get('message')}"
                
                state["response"] = response_text
                logger.info("Event edited", event_id=event_id, new_time=new_time)
            
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
            
        except Exception as e:
            logger.error("Error editing event", error=str(e))
            state["response"] = f"Erro ao editar evento: {str(e)}"
            state["messages"] = state["messages"] + [AIMessage(content=state["response"])]
        
        return state