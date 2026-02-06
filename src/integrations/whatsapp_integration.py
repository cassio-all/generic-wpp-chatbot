"""WhatsApp Integration for Generic Chatbot.

This module provides a bridge between the Python chatbot and WhatsApp Web
through a Node.js server running whatsapp-web.js.
"""

import asyncio
import json
import structlog
import websockets
import base64
import tempfile
import os
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

logger = structlog.get_logger(__name__)


@dataclass
class WhatsAppMessage:
    """Represents a WhatsApp message."""
    id: str
    from_number: str
    body: str
    timestamp: int
    contact_name: str
    is_group: bool = False
    has_media: bool = False
    audio: Optional[Dict[str, Any]] = None


class WhatsAppClient:
    """Client for communicating with WhatsApp via Node.js bridge."""
    
    def __init__(
        self,
        bridge_url: str = "ws://localhost:8765",
        message_handler: Optional[Callable] = None
    ):
        """Initialize WhatsApp client.
        
        Args:
            bridge_url: WebSocket URL of the Node.js bridge server
            message_handler: Async function to handle incoming messages
        """
        self.bridge_url = bridge_url
        self.message_handler = message_handler
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.whatsapp_ready = False
        self.whatsapp_info: Dict[str, Any] = {}
        self.openai_client = OpenAI()  # For Whisper transcription
        
    async def connect(self):
        """Connect to the Node.js bridge server."""
        try:
            logger.info("Connecting to WhatsApp bridge", url=self.bridge_url)
            self.websocket = await websockets.connect(self.bridge_url)
            self.connected = True
            logger.info("✅ Connected to WhatsApp bridge")
            
            # Start listening for messages
            asyncio.create_task(self._listen())
            
        except Exception as e:
            logger.error("Failed to connect to WhatsApp bridge", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from the bridge server."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from WhatsApp bridge")
    
    async def _listen(self):
        """Listen for messages from the bridge server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_bridge_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection to bridge closed")
            self.connected = False
            self.whatsapp_ready = False
            
        except Exception as e:
            logger.error("Error in listen loop", error=str(e))
    
    async def _transcribe_audio(self, audio_data: Dict[str, Any]) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper.
        
        Args:
            audio_data: Dictionary with 'data' (base64), 'mimetype', 'filename'
            
        Returns:
            Transcribed text or None if error
        """
        temp_file = None
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data['data'])
            
            # Save to temporary file
            # Whisper expects actual audio file extensions
            extension = '.ogg' if 'ogg' in audio_data['mimetype'] else '.mp3'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
            temp_file.write(audio_bytes)
            temp_file.close()
            
            logger.info("🎤 Transcribing audio...", size=len(audio_bytes))
            
            # Transcribe with Whisper
            with open(temp_file.name, 'rb') as audio_file:
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="pt"  # Portuguese
                )
            
            text = transcription.text
            logger.info("✅ Audio transcribed", text=text[:100])
            return text
            
        except Exception as e:
            logger.error("❌ Error transcribing audio", error=str(e))
            return None
            
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning("Failed to delete temp file", error=str(e))
    
    async def _handle_bridge_message(self, data: Dict[str, Any]):
        """Handle messages from the Node.js bridge.
        
        Args:
            data: Message data from bridge
        """
        msg_type = data.get("type")
        
        if msg_type == "qr_code":
            logger.info("📱 QR Code received - scan with WhatsApp")
            print("\n" + "="*60)
            print("📱 SCAN THIS QR CODE WITH WHATSAPP:")
            print("="*60 + "\n")
            # QR code already printed by Node.js server
            
        elif msg_type == "status":
            status = data.get("status")
            logger.info("WhatsApp status update", status=status)
            
            if status == "ready":
                self.whatsapp_ready = True
                self.whatsapp_info = data.get("info", {})
                logger.info(
                    "✅ WhatsApp ready!",
                    name=self.whatsapp_info.get("pushname"),
                    number=self.whatsapp_info.get("number")
                )
                print("\n" + "="*60)
                print(f"✅ WhatsApp conectado!")
                print(f"👤 Nome: {self.whatsapp_info.get('pushname')}")
                print(f"📞 Número: {self.whatsapp_info.get('number')}")
                print("="*60 + "\n")
                
            elif status == "authenticated":
                logger.info("🔐 WhatsApp authenticated")
                
            elif status == "auth_failure":
                logger.error("❌ WhatsApp authentication failed", error=data.get("error"))
                
            elif status == "disconnected":
                self.whatsapp_ready = False
                logger.warning("❌ WhatsApp disconnected", reason=data.get("reason"))
        
        elif msg_type == "incoming_message":
            await self._handle_incoming_message(data.get("message"))
            
        elif msg_type == "message_sent":
            if data.get("success"):
                logger.info("✅ Message sent successfully", to=data.get("to"))
            else:
                logger.error("❌ Failed to send message", error=data.get("error"))
        
        elif msg_type == "error":
            logger.error("Bridge error", error=data.get("error"))
    
    async def _handle_incoming_message(self, msg_data: Dict[str, Any]):
        """Handle incoming WhatsApp message.
        
        Args:
            msg_data: Message data from WhatsApp
        """
        try:
            # Ignore status broadcasts (WhatsApp Stories)
            from_number = msg_data.get("from", "")
            if from_number == "status@broadcast" or "broadcast" in from_number:
                logger.debug("Ignoring status broadcast message")
                return
            
            # Ignore group messages
            if msg_data.get("isGroup", False) or "@g.us" in from_number:
                logger.debug("Ignoring group message", from_number=from_number)
                return
            
            # Ignore channels/newsletters
            if from_number.startswith("120363") or "@newsletter" in from_number:
                logger.debug("Ignoring channel/newsletter message", from_number=from_number)
                return
            
            # Handle audio transcription if present
            body = msg_data["body"]
            audio_data = msg_data.get("audio")
            
            if audio_data:
                logger.info("🎤 Audio message received, transcribing...")
                transcribed_text = await self._transcribe_audio(audio_data)
                
                if transcribed_text:
                    body = transcribed_text
                    logger.info("✅ Using transcribed text", text=body[:100])
                else:
                    body = "[Mensagem de áudio - erro na transcrição]"
                    logger.error("❌ Failed to transcribe audio")
            
            contact = msg_data.get("contact", {})
            message = WhatsAppMessage(
                id=msg_data["id"],
                from_number=from_number,
                body=body,
                timestamp=msg_data["timestamp"],
                contact_name=contact.get("name", "Unknown"),
                is_group=msg_data.get("isGroup", False),
                has_media=msg_data.get("hasMedia", False),
                audio=audio_data
            )
            
            logger.info(
                "📨 Incoming message",
                from_name=message.contact_name,
                from_number=message.from_number,
                body=message.body[:50] + "..." if len(message.body) > 50 else message.body
            )
            
            # Call the message handler if provided
            if self.message_handler:
                await self.message_handler(message)
            
        except Exception as e:
            logger.error("Error handling incoming message", error=str(e))
    
    async def send_message(self, to: str, text: str):
        """Send a message via WhatsApp.
        
        Args:
            to: Phone number (with country code) or chat ID
            text: Message text to send
        """
        if not self.connected:
            raise ConnectionError("Not connected to bridge")
        
        if not self.whatsapp_ready:
            raise ConnectionError("WhatsApp not ready")
        
        message = {
            "type": "send_message",
            "data": {
                "to": to,
                "text": text
            }
        }
        
        await self.websocket.send(json.dumps(message))
        logger.info("Sending message", to=to, length=len(text))
    
    async def send_typing(self, to: str):
        """Send typing indicator.
        
        Args:
            to: Phone number or chat ID
        """
        if not self.connected or not self.whatsapp_ready:
            return
        
        message = {
            "type": "send_typing",
            "data": {"to": to}
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def get_chats(self):
        """Request list of all chats."""
        if not self.connected or not self.whatsapp_ready:
            return
        
        message = {"type": "get_chats"}
        await self.websocket.send(json.dumps(message))
    
    def is_ready(self) -> bool:
        """Check if WhatsApp is ready to send/receive messages."""
        return self.connected and self.whatsapp_ready
