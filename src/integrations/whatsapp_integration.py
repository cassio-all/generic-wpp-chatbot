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
import time
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
    image: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None


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
        
        # Auto-pause when manual reply detected
        self.paused_contacts: Dict[str, float] = {}  # {number: timestamp}
        self.pause_duration = 60  # seconds
        
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
    
    async def _analyze_image(self, image_data: Dict[str, Any]) -> Optional[str]:
        """Analyze image using GPT-4 Vision.
        
        Args:
            image_data: Dictionary with 'data' (base64), 'mimetype', 'filename'
            
        Returns:
            Image description or None if error
        """
        try:
            logger.info("🖼️  Analyzing image...", mimetype=image_data['mimetype'])
            
            # Prepare image for GPT-4 Vision
            base64_image = image_data['data']
            
            # Call GPT-4 Vision
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # gpt-4o-mini supports vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Descreva esta imagem em português de forma detalhada. Se houver texto na imagem, transcreva-o."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_data['mimetype']};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            description = response.choices[0].message.content
            logger.info("✅ Image analyzed", description=description[:100])
            return description
            
        except Exception as e:
            logger.error("❌ Error analyzing image", error=str(e))
            return None
    
    async def _extract_pdf_text(self, document_data: Dict[str, Any]) -> Optional[str]:
        """Extract text from PDF document.
        
        Args:
            document_data: Dictionary with 'data' (base64), 'mimetype', 'filename'
            
        Returns:
            Extracted text or None if error
        """
        temp_file = None
        try:
            # Only process PDFs for now
            if 'pdf' not in document_data['mimetype'].lower():
                logger.info("⚠️  Non-PDF document, skipping text extraction", mimetype=document_data['mimetype'])
                return None
            
            # Decode base64 document
            doc_bytes = base64.b64decode(document_data['data'])
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(doc_bytes)
            temp_file.close()
            
            logger.info("📄 Extracting text from PDF...", filename=document_data['filename'])
            
            # Extract text with PyPDF2
            try:
                from PyPDF2 import PdfReader
                
                reader = PdfReader(temp_file.name)
                text_parts = []
                
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(f"--- Página {page_num} ---\n{text}")
                
                full_text = "\n\n".join(text_parts)
                
                if full_text.strip():
                    logger.info("✅ Text extracted from PDF", pages=len(reader.pages), chars=len(full_text))
                    return full_text
                else:
                    logger.warning("⚠️  PDF has no extractable text (might be scanned)")
                    return None
                    
            except ImportError:
                logger.error("❌ PyPDF2 not installed - run: pip install PyPDF2")
                return None
            
        except Exception as e:
            logger.error("❌ Error extracting PDF text", error=str(e))
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
        
        elif msg_type == "manual_reply":
            # User replied manually, pause bot for this contact
            contact = data.get("contact")
            if contact:
                self.paused_contacts[contact] = time.time()
                logger.info("⏸️  Bot paused for contact (manual reply detected)", 
                           contact=contact, 
                           duration_seconds=self.pause_duration)
            
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
            
            # Ignore WhatsApp Business accounts and channels (@lid)
            if "@lid" in from_number:
                logger.debug("Ignoring WhatsApp Business/Channel", from_number=from_number)
                return
            
            # Ignore empty messages
            body = msg_data.get("body", "")
            if not body and not msg_data.get("audio") and not msg_data.get("image") and not msg_data.get("document"):
                logger.debug("Ignoring empty message", from_number=from_number)
                return
            
            # Check if bot is paused for this contact (manual reply detected)
            if from_number in self.paused_contacts:
                pause_time = self.paused_contacts[from_number]
                elapsed = time.time() - pause_time
                
                if elapsed < self.pause_duration:
                    remaining = int(self.pause_duration - elapsed)
                    logger.info("⏸️  Bot paused for this contact", 
                               contact=from_number, 
                               remaining_seconds=remaining)
                    return  # Ignore message while paused
                else:
                    # Pause expired, remove from paused list
                    del self.paused_contacts[from_number]
                    logger.info("▶️  Bot resumed for contact (pause expired)", contact=from_number)
            
            # Handle audio transcription if present
            body = msg_data["body"]
            audio_data = msg_data.get("audio")
            image_data = msg_data.get("image")
            document_data = msg_data.get("document")
            
            # Check for unsupported media type
            if body.startswith("[Tipo de mídia não suportado:"):
                logger.warning("⚠️  Unsupported media type received", body=body)
                # Send helpful response
                await self.send_message(
                    from_number,
                    "⚠️ Desculpe, este tipo de arquivo ainda não é suportado.\n\n"
                    "📱 Tipos suportados:\n"
                    "• 🎤 Áudios (transcrição automática)\n"
                    "• 🖼️ Imagens (análise visual)\n"
                    "• 📄 Documentos PDF (extração de texto)\n\n"
                    "Por favor, envie mensagens de texto ou um dos formatos acima."
                )
                return  # Don't process further
            
            if audio_data:
                logger.info("🎤 Audio message received, transcribing...")
                transcribed_text = await self._transcribe_audio(audio_data)
                
                if transcribed_text:
                    body = transcribed_text
                    logger.info("✅ Using transcribed text", text=body[:100])
                else:
                    body = "[Mensagem de áudio - erro na transcrição]"
                    logger.error("❌ Failed to transcribe audio")
            
            elif image_data:
                logger.info("🖼️  Image message received, analyzing...")
                image_description = await self._analyze_image(image_data)
                
                if image_description:
                    # Combine caption (if any) with image description
                    if body:
                        body = f"[Imagem com legenda: {body}]\n\nDescrição da imagem: {image_description}"
                    else:
                        body = f"[Imagem enviada]\n\nDescrição: {image_description}"
                    logger.info("✅ Using image description", text=body[:100])
                else:
                    body = "[Imagem enviada - erro na análise]"
                    logger.error("❌ Failed to analyze image")
            
            elif document_data:
                logger.info("📄 Document message received, extracting text...")
                extracted_text = await self._extract_pdf_text(document_data)
                
                if extracted_text:
                    # Truncate if too long (keep first 5000 chars)
                    if len(extracted_text) > 5000:
                        extracted_text = extracted_text[:5000] + "\n\n[... texto truncado ...]"
                    
                    filename = document_data.get('filename', 'documento')
                    body = f"[Documento PDF: {filename}]\n\nConteúdo extraído:\n\n{extracted_text}"
                    logger.info("✅ Using extracted PDF text", chars=len(extracted_text))
                else:
                    filename = document_data.get('filename', 'documento')
                    body = f"[Documento enviado: {filename}]\n\n(Não foi possível extrair texto)"
                    logger.warning("⚠️  Could not extract text from document")
            
            contact = msg_data.get("contact", {})
            message = WhatsAppMessage(
                id=msg_data["id"],
                from_number=from_number,
                body=body,
                timestamp=msg_data["timestamp"],
                contact_name=contact.get("name", "Unknown"),
                is_group=msg_data.get("isGroup", False),
                has_media=msg_data.get("hasMedia", False),
                audio=audio_data,
                image=image_data,
                document=document_data
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
