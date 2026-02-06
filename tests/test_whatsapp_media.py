"""Tests for WhatsApp media handling (audio, images, PDFs)."""
import pytest
import base64
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.integrations.whatsapp_integration import WhatsAppClient, WhatsAppMessage


@pytest.fixture
def whatsapp_client():
    """Create a WhatsApp client for testing."""
    client = WhatsAppClient(bridge_url="ws://localhost:8765")
    return client


@pytest.fixture
def sample_audio_base64():
    """Sample base64 audio data."""
    return "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="


@pytest.fixture
def sample_image_base64():
    """Sample base64 image data (1x1 transparent PNG)."""
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


@pytest.fixture
def sample_pdf_base64():
    """Sample base64 PDF data."""
    return "JVBERi0xLjQKJcfsj6IKNSAwIG9iago8PC9MZW5ndGggNiAwIFI+PnN0cmVhbQpIZWxsbyBXb3JsZCEKZW5kc3RyZWFtCmVuZG9iago="


class TestAudioTranscription:
    """Tests for audio transcription with Whisper."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, whatsapp_client, sample_audio_base64):
        """Test successful audio transcription."""
        audio_data = {
            'data': sample_audio_base64,
            'mimetype': 'audio/ogg',
            'filename': 'test.ogg'
        }
        
        # Mock OpenAI Whisper API
        mock_transcription = Mock()
        mock_transcription.text = "Esta é uma mensagem de áudio de teste"
        
        with patch.object(whatsapp_client.openai_client.audio.transcriptions, 'create', return_value=mock_transcription):
            result = await whatsapp_client._transcribe_audio(audio_data)
        
        assert result == "Esta é uma mensagem de áudio de teste"
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_error(self, whatsapp_client, sample_audio_base64):
        """Test audio transcription error handling."""
        audio_data = {
            'data': sample_audio_base64,
            'mimetype': 'audio/ogg',
            'filename': 'test.ogg'
        }
        
        # Mock OpenAI API error
        with patch.object(whatsapp_client.openai_client.audio.transcriptions, 'create', side_effect=Exception("API Error")):
            result = await whatsapp_client._transcribe_audio(audio_data)
        
        assert result is None


class TestImageAnalysis:
    """Tests for image analysis with GPT-4 Vision."""
    
    @pytest.mark.asyncio
    async def test_analyze_image_success(self, whatsapp_client, sample_image_base64):
        """Test successful image analysis."""
        image_data = {
            'data': sample_image_base64,
            'mimetype': 'image/png',
            'filename': 'test.png'
        }
        
        # Mock GPT-4 Vision API
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Uma imagem de teste com fundo transparente"))]
        
        with patch.object(whatsapp_client.openai_client.chat.completions, 'create', return_value=mock_response):
            result = await whatsapp_client._analyze_image(image_data)
        
        assert result == "Uma imagem de teste com fundo transparente"
    
    @pytest.mark.asyncio
    async def test_analyze_image_with_text(self, whatsapp_client, sample_image_base64):
        """Test image analysis with text extraction."""
        image_data = {
            'data': sample_image_base64,
            'mimetype': 'image/jpeg',
            'filename': 'screenshot.jpg'
        }
        
        # Mock GPT-4 Vision API with OCR
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Imagem contém texto: Hello World"))]
        
        with patch.object(whatsapp_client.openai_client.chat.completions, 'create', return_value=mock_response):
            result = await whatsapp_client._analyze_image(image_data)
        
        assert "Hello World" in result


class TestPDFExtraction:
    """Tests for PDF text extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_pdf_text_success(self, whatsapp_client, sample_pdf_base64):
        """Test successful PDF text extraction."""
        document_data = {
            'data': sample_pdf_base64,
            'mimetype': 'application/pdf',
            'filename': 'test.pdf'
        }
        
        # Mock PyPDF2 reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Este é um documento de teste"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('PyPDF2.PdfReader', return_value=mock_reader):
            result = await whatsapp_client._extract_pdf_text(document_data)
        
        assert "Este é um documento de teste" in result
    
    @pytest.mark.asyncio
    async def test_extract_pdf_non_pdf_ignored(self, whatsapp_client):
        """Test that non-PDF documents are ignored."""
        document_data = {
            'data': 'base64data',
            'mimetype': 'application/msword',
            'filename': 'test.docx'
        }
        
        result = await whatsapp_client._extract_pdf_text(document_data)
        assert result is None


class TestMessageFiltering:
    """Tests for message filtering logic."""
    
    @pytest.mark.asyncio
    async def test_ignore_empty_messages(self, whatsapp_client):
        """Test that empty messages are ignored."""
        msg_data = {
            'from': '5534999999999@c.us',
            'body': '',
            'timestamp': 123456,
            'id': 'msg_1',
            'contact': {'name': 'Test'},
            'isGroup': False,
            'hasMedia': False
        }
        
        whatsapp_client.message_handler = AsyncMock()
        await whatsapp_client._handle_incoming_message(msg_data)
        
        # Message handler should not be called
        whatsapp_client.message_handler.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ignore_business_accounts(self, whatsapp_client):
        """Test that @lid accounts are ignored."""
        msg_data = {
            'from': '113692599410796@lid',
            'body': 'Test message',
            'timestamp': 123456,
            'id': 'msg_1',
            'contact': {'name': 'Business'},
            'isGroup': False,
            'hasMedia': False
        }
        
        whatsapp_client.message_handler = AsyncMock()
        await whatsapp_client._handle_incoming_message(msg_data)
        
        # Message handler should not be called
        whatsapp_client.message_handler.assert_not_called()


class TestAutoPauseSystem:
    """Tests for auto-pause when manual reply detected."""
    
    @pytest.mark.asyncio
    async def test_pause_on_manual_reply(self, whatsapp_client):
        """Test that bot pauses when manual reply detected."""
        contact = '5534999999999@c.us'
        
        # Simulate manual reply event
        data = {
            'type': 'manual_reply',
            'contact': contact
        }
        
        await whatsapp_client._handle_bridge_message(data)
        
        # Contact should be paused
        assert contact in whatsapp_client.paused_contacts
    
    @pytest.mark.asyncio
    async def test_ignore_messages_while_paused(self, whatsapp_client):
        """Test that messages are ignored while contact is paused."""
        import time
        
        contact = '5534999999999@c.us'
        whatsapp_client.paused_contacts[contact] = time.time()  # Pause now
        
        msg_data = {
            'from': contact,
            'body': 'Test message',
            'timestamp': 123456,
            'id': 'msg_1',
            'contact': {'name': 'Test'},
            'isGroup': False,
            'hasMedia': False
        }
        
        whatsapp_client.message_handler = AsyncMock()
        await whatsapp_client._handle_incoming_message(msg_data)
        
        # Message handler should not be called (paused)
        whatsapp_client.message_handler.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auto_resume_after_timeout(self, whatsapp_client):
        """Test that bot auto-resumes after pause timeout."""
        import time
        
        contact = '5534999999999@c.us'
        # Pause 61 seconds ago (beyond timeout)
        whatsapp_client.paused_contacts[contact] = time.time() - 61
        
        msg_data = {
            'from': contact,
            'body': 'Test message',
            'timestamp': 123456,
            'id': 'msg_1',
            'contact': {'name': 'Test'},
            'isGroup': False,
            'hasMedia': False,
            'audio': None,
            'image': None,
            'document': None
        }
        
        whatsapp_client.message_handler = AsyncMock()
        await whatsapp_client._handle_incoming_message(msg_data)
        
        # Contact should be removed from paused list
        assert contact not in whatsapp_client.paused_contacts
        # Message handler should be called (resumed)
        whatsapp_client.message_handler.assert_called_once()


class TestUnsupportedMediaHandling:
    """Tests for unsupported media type handling."""
    
    @pytest.mark.asyncio
    async def test_unsupported_media_response(self, whatsapp_client):
        """Test that unsupported media types get helpful response."""
        msg_data = {
            'from': '5534999999999@c.us',
            'body': '[Tipo de mídia não suportado: video]',
            'timestamp': 123456,
            'id': 'msg_1',
            'contact': {'name': 'Test'},
            'isGroup': False,
            'hasMedia': True
        }
        
        whatsapp_client.send_message = AsyncMock()
        await whatsapp_client._handle_incoming_message(msg_data)
        
        # Should send helpful message
        whatsapp_client.send_message.assert_called_once()
        args = whatsapp_client.send_message.call_args[0]
        assert '⚠️ Desculpe' in args[1]
        assert 'não é suportado' in args[1]
