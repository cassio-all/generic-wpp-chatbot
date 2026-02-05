"""WhatsApp Chatbot Runner.

This script starts the WhatsApp integration, connecting the chatbot
to WhatsApp via the Node.js bridge server.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import structlog
from src.integrations.whatsapp_integration import WhatsAppClient, WhatsAppMessage
from src.agents.orchestrator import ChatbotOrchestrator

logger = structlog.get_logger(__name__)

# Global variables for cleanup
whatsapp_client = None
orchestrator = None


async def handle_whatsapp_message(message: WhatsAppMessage):
    """Handle incoming WhatsApp messages.
    
    Args:
        message: WhatsApp message object
    """
    try:
        # Use phone number as thread_id for conversation persistence
        thread_id = f"whatsapp-{message.from_number}"
        
        logger.info(
            "Processing WhatsApp message",
            from_name=message.contact_name,
            from_number=message.from_number,
            thread_id=thread_id
        )
        
        # Send typing indicator
        await whatsapp_client.send_typing(message.from_number)
        
        # Process message with orchestrator
        response = orchestrator.process_message(
            message.body,
            thread_id=thread_id
        )
        
        # Send response back via WhatsApp
        await whatsapp_client.send_message(message.from_number, response)
        
        logger.info(
            "Response sent",
            to=message.contact_name,
            response_length=len(response)
        )
        
    except Exception as e:
        logger.error("Error processing WhatsApp message", error=str(e))
        
        # Send error message to user
        try:
            error_msg = "❌ Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente."
            await whatsapp_client.send_message(message.from_number, error_msg)
        except Exception:
            pass


async def main():
    """Main function to run the WhatsApp chatbot."""
    global whatsapp_client, orchestrator
    
    print("\n" + "="*60)
    print("🤖 Generic WhatsApp Chatbot")
    print("="*60 + "\n")
    
    # Initialize orchestrator
    logger.info("Initializing chatbot orchestrator...")
    orchestrator = ChatbotOrchestrator()
    logger.info("✅ Orchestrator ready")
    
    # Initialize WhatsApp client
    logger.info("Initializing WhatsApp client...")
    whatsapp_client = WhatsAppClient(
        bridge_url="ws://localhost:8765",
        message_handler=handle_whatsapp_message
    )
    
    try:
        # Connect to bridge
        await whatsapp_client.connect()
        
        print("\n💡 Aguardando conexão com WhatsApp...")
        print("📱 Escaneie o QR code quando aparecer\n")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
            # Check connection status
            if not whatsapp_client.connected:
                logger.warning("Lost connection to bridge, reconnecting...")
                await asyncio.sleep(5)
                try:
                    await whatsapp_client.connect()
                except Exception as e:
                    logger.error("Failed to reconnect", error=str(e))
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        
    finally:
        # Cleanup
        if whatsapp_client:
            await whatsapp_client.disconnect()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n👋 Shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
