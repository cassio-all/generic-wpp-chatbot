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
    logger.info("Starting WhatsApp Chatbot", config=settings.dict())
    
    # Initialize orchestrator
    orchestrator = ChatbotOrchestrator()
    
    # Simple CLI interface for testing
    print("=" * 60)
    print("WhatsApp Chatbot - CLI Mode")
    print("=" * 60)
    print("Type 'quit' to exit")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            response = orchestrator.process_message(user_input)
            print(f"\nBot: {response}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error("Error in main loop", error=str(e))
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()
