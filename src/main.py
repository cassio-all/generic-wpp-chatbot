"""Main application entry point."""
import asyncio
import structlog
from src.config import settings
from src.agents import ChatbotOrchestrator

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def main():
    """Main application entry point."""
    logger.info("Starting WhatsApp Chatbot", config=settings.model_dump())
    
    # Initialize orchestrator
    orchestrator = ChatbotOrchestrator()
    
    # Thread ID for this CLI session (in production, would be user's phone number)
    thread_id = "cli_session"
    
    # Simple CLI interface for testing
    print("=" * 60)
    print("WhatsApp Chatbot - CLI Mode")
    print("=" * 60)
    print("Type 'quit' to exit")
    print("Type 'clear' to clear conversation history")
    print("Type 'history' to see message count")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if user_input.lower() == 'clear':
                orchestrator.clear_conversation(thread_id)
                print("🗑️  Conversation history cleared!")
                continue
            
            if user_input.lower() == 'history':
                history = orchestrator.get_conversation_history(thread_id)
                print(f"📊 Total messages in history: {len(history)}")
                continue
            
            if not user_input:
                continue
            
            response = orchestrator.process_message(user_input, thread_id=thread_id)
            print(f"\nBot: {response}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error("Error in main loop", error=str(e))
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()
