"""Summary Agent for condensing conversation history."""
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from src.config import settings
import tiktoken
import structlog

logger = structlog.get_logger()


class SummaryAgent:
    """Agent responsible for summarizing conversation history to save tokens."""
    
    def __init__(self):
        """Initialize the summary agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Cheaper model for summaries
            temperature=0.3,
            api_key=settings.openai_api_key
        )
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    
    def count_tokens(self, messages: List[BaseMessage]) -> int:
        """Count total tokens in message list.
        
        Args:
            messages: List of messages to count
            
        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            # Approximate token count (content + role overhead)
            total += len(self.encoding.encode(msg.content))
            total += 4  # Overhead per message
        return total
    
    def summarize_messages(
        self, 
        messages: List[BaseMessage],
        existing_summary: str = ""
    ) -> str:
        """Summarize a list of messages into a concise summary.
        
        Args:
            messages: Messages to summarize
            existing_summary: Previous summary to continue from
            
        Returns:
            Condensed summary of the conversation
        """
        logger.info("Summarizing conversation history", 
                   message_count=len(messages),
                   has_existing_summary=bool(existing_summary))
        
        # Build conversation text
        conversation_text = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                conversation_text.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                conversation_text.append(f"Assistant: {msg.content}")
        
        conversation = "\n".join(conversation_text)
        
        # Create summary prompt
        system_prompt = """Você é um assistente especializado em resumir conversas.

Sua tarefa é criar um resumo conciso que preserve:
1. O contexto principal da conversa
2. Informações importantes mencionadas
3. Decisões ou acordos feitos
4. Estado atual da conversa

Seja breve mas completo. Use bullets para organizar informações chave.
Máximo de 200 palavras."""

        if existing_summary:
            user_prompt = f"""Resumo anterior da conversa:
{existing_summary}

Novas mensagens:
{conversation}

Atualize o resumo incorporando as novas informações. Mantenha apenas o essencial."""
        else:
            user_prompt = f"""Resuma a seguinte conversa:

{conversation}

Crie um resumo conciso que capture o essencial."""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            summary = response.content.strip()
            
            logger.info("Summary created successfully", 
                       summary_length=len(summary),
                       original_tokens=self.count_tokens(messages),
                       summary_tokens=len(self.encoding.encode(summary)))
            
            return summary
            
        except Exception as e:
            logger.error("Error creating summary", error=str(e))
            return existing_summary or "Erro ao criar resumo da conversa."
    
    def should_summarize(
        self,
        messages: List[BaseMessage],
        max_tokens: int = 2000
    ) -> bool:
        """Check if conversation should be summarized.
        
        Args:
            messages: Current message history
            max_tokens: Maximum tokens before summarizing
            
        Returns:
            True if should summarize
        """
        token_count = self.count_tokens(messages)
        should = token_count > max_tokens
        
        if should:
            logger.info("Token threshold exceeded, summarization needed",
                       current_tokens=token_count,
                       max_tokens=max_tokens)
        
        return should
    
    def compress_history(
        self,
        messages: List[BaseMessage],
        existing_summary: str = "",
        keep_recent: int = 4
    ) -> tuple[List[BaseMessage], str]:
        """Compress message history by summarizing older messages.
        
        Args:
            messages: Full message history
            existing_summary: Previous summary if any
            keep_recent: Number of recent messages to keep as-is
            
        Returns:
            Tuple of (compressed_messages, updated_summary)
        """
        if len(messages) <= keep_recent:
            return messages, existing_summary
        
        # Split into old and recent
        old_messages = messages[:-keep_recent]
        recent_messages = messages[-keep_recent:]
        
        # Summarize old messages
        new_summary = self.summarize_messages(old_messages, existing_summary)
        
        # Create summary message
        summary_message = SystemMessage(
            content=f"📋 Resumo da conversa anterior:\n{new_summary}"
        )
        
        # Return summary + recent messages
        compressed = [summary_message] + recent_messages
        
        logger.info("History compressed",
                   original_count=len(messages),
                   compressed_count=len(compressed),
                   kept_recent=keep_recent)
        
        return compressed, new_summary
