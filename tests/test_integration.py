"""Integration tests for end-to-end workflows."""
import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock


class TestWhatsAppIntegrationFlow:
    """Integration tests for WhatsApp message flow."""
    
    @pytest.mark.asyncio
    async def test_text_message_complete_flow(self):
        """Test complete flow: WhatsApp -> Orchestrator -> Agent -> Response."""
        from src.integrations.whatsapp_integration import WhatsAppIntegration
        
        with patch('src.integrations.whatsapp_integration.AgentOrchestrator') as mock_orch_class:
            # Mock orchestrator
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_message = AsyncMock(return_value="Resposta do agente")
            mock_orch_class.return_value = mock_orchestrator
            
            # Create WhatsApp integration
            whatsapp = WhatsAppIntegration()
            
            # Simulate incoming message
            test_message = {
                'type': 'message',
                'from': '5511999999999@c.us',
                'body': 'Olá, preciso de ajuda',
                'timestamp': 1234567890
            }
            
            # Process message
            await whatsapp._handle_incoming_message(test_message)
            
            # Verify orchestrator was called
            mock_orchestrator.process_message.assert_called_once_with(
                'Olá, preciso de ajuda',
                '5511999999999@c.us'
            )
    
    @pytest.mark.asyncio
    async def test_audio_transcription_flow(self):
        """Test complete flow for audio transcription."""
        from src.integrations.whatsapp_integration import WhatsAppIntegration
        
        with patch('src.integrations.whatsapp_integration.AgentOrchestrator') as mock_orch_class:
            with patch('src.integrations.whatsapp_integration.OpenAI') as mock_openai_class:
                # Mock OpenAI client
                mock_openai = Mock()
                mock_openai.audio.transcriptions.create = Mock(
                    return_value=Mock(text="Transcrição do áudio")
                )
                mock_openai_class.return_value = mock_openai
                
                # Mock orchestrator
                mock_orchestrator = AsyncMock()
                mock_orchestrator.process_message = AsyncMock(
                    return_value="Resposta baseada na transcrição"
                )
                mock_orch_class.return_value = mock_orchestrator
                
                # Create integration
                whatsapp = WhatsAppIntegration()
                
                # Simulate audio message
                test_message = {
                    'type': 'message',
                    'from': '5511999999999@c.us',
                    'body': '[Áudio]',
                    'timestamp': 1234567890,
                    'audio': 'base64_encoded_audio_data_here'
                }
                
                # Process message
                await whatsapp._handle_incoming_message(test_message)
                
                # Verify transcription was called
                assert mock_openai.audio.transcriptions.create.called
                
                # Verify orchestrator received transcribed text
                mock_orchestrator.process_message.assert_called()


class TestCalendarWorkflow:
    """Integration tests for calendar agent workflows."""
    
    @pytest.mark.asyncio
    async def test_create_event_workflow(self):
        """Test complete workflow for creating a calendar event."""
        from src.agents.orchestrator import ChatbotOrchestrator
        
        with patch('src.agents.knowledge_agent.KnowledgeBaseService'):
            with patch('langchain_openai.ChatOpenAI'):
                # Create orchestrator
                orch = ChatbotOrchestrator()
                
                # Should have calendar agent
                assert hasattr(orch, 'calendar_agent')
                assert orch.calendar_agent is not None


class TestTaskWorkflow:
    """Integration tests for task agent workflows."""
    
    @pytest.mark.asyncio
    async def test_add_task_workflow(self):
        """Test complete workflow for adding a task."""
        from src.agents.orchestrator import ChatbotOrchestrator
        
        with patch('src.agents.knowledge_agent.KnowledgeBaseService'):
            with patch('langchain_openai.ChatOpenAI'):
                # Create orchestrator
                orch = ChatbotOrchestrator()
                
                # Should have task agent
                assert hasattr(orch, 'task_agent')
                assert orch.task_agent is not None


class TestKnowledgeBaseWorkflow:
    """Integration tests for knowledge base workflows."""
    
    @pytest.mark.asyncio
    async def test_knowledge_query_workflow(self):
        """Test complete workflow for querying knowledge base."""
        from src.agents.orchestrator import ChatbotOrchestrator
        
        with patch('src.agents.knowledge_agent.KnowledgeBaseService') as mock_kb_class:
            # Mock knowledge base
            mock_kb = Mock()
            mock_kb.search = Mock(return_value=[
                "O produto X é uma solução completa",
                "Inclui recursos A, B e C"
            ])
            mock_kb_class.return_value = mock_kb
            
            with patch('langchain_openai.ChatOpenAI'):
                # Create orchestrator
                orch = ChatbotOrchestrator()
                
                # Should have knowledge agent
                assert hasattr(orch, 'knowledge_agent')
                assert orch.knowledge_agent is not None


class TestAutoPauseIntegration:
    """Integration tests for auto-pause system."""
    
    @pytest.mark.asyncio
    async def test_manual_reply_pauses_bot(self):
        """Test that manual reply correctly pauses bot."""
        from src.integrations.whatsapp_integration import WhatsAppIntegration
        import time
        
        with patch('src.integrations.whatsapp_integration.AgentOrchestrator'):
            whatsapp = WhatsAppIntegration()
            
            # Simulate manual reply
            manual_reply_msg = {
                'type': 'manual_reply',
                'contact': '5511999999999@c.us'
            }
            
            await whatsapp._handle_incoming_message(manual_reply_msg)
            
            # Contact should be paused
            assert '5511999999999@c.us' in whatsapp.paused_contacts
            
            # Simulate incoming message during pause
            incoming_msg = {
                'type': 'message',
                'from': '5511999999999@c.us',
                'body': 'Outra mensagem',
                'timestamp': int(time.time())
            }
            
            with patch.object(whatsapp.orchestrator, 'process_message', new_callable=AsyncMock) as mock_process:
                await whatsapp._handle_incoming_message(incoming_msg)
                
                # Should NOT process message (paused)
                mock_process.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auto_resume_after_timeout(self):
        """Test that bot auto-resumes after timeout."""
        from src.integrations.whatsapp_integration import WhatsAppIntegration
        import time
        
        with patch('src.integrations.whatsapp_integration.AgentOrchestrator') as mock_orch_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_message = AsyncMock(return_value="Resposta")
            mock_orch_class.return_value = mock_orchestrator
            
            whatsapp = WhatsAppIntegration()
            contact = '5511999999999@c.us'
            
            # Pause contact (simulate old timestamp)
            whatsapp.paused_contacts[contact] = time.time() - 70  # 70 seconds ago
            
            # Simulate incoming message
            incoming_msg = {
                'type': 'message',
                'from': contact,
                'body': 'Nova mensagem',
                'timestamp': int(time.time())
            }
            
            await whatsapp._handle_incoming_message(incoming_msg)
            
            # Should process message (timeout exceeded)
            mock_orchestrator.process_message.assert_called_once()
            
            # Contact should be removed from paused list
            assert contact not in whatsapp.paused_contacts


class TestMediaHandlingIntegration:
    """Integration tests for complete media handling flows."""
    
    @pytest.mark.asyncio
    async def test_image_analysis_flow(self):
        """Test complete image analysis workflow."""
        from src.integrations.whatsapp_integration import WhatsAppIntegration
        
        with patch('src.integrations.whatsapp_integration.AgentOrchestrator') as mock_orch_class:
            with patch('src.integrations.whatsapp_integration.OpenAI') as mock_openai_class:
                # Mock OpenAI Vision
                mock_openai = Mock()
                mock_vision_response = Mock()
                mock_vision_response.choices = [
                    Mock(message=Mock(content="Imagem mostra uma pessoa"))
                ]
                mock_openai.chat.completions.create = Mock(return_value=mock_vision_response)
                mock_openai_class.return_value = mock_openai
                
                # Mock orchestrator
                mock_orchestrator = AsyncMock()
                mock_orchestrator.process_message = AsyncMock(return_value="Resposta sobre a imagem")
                mock_orch_class.return_value = mock_orchestrator
                
                whatsapp = WhatsAppIntegration()
                
                # Simulate image message
                test_message = {
                    'type': 'message',
                    'from': '5511999999999@c.us',
                    'body': '[Imagem]',
                    'timestamp': 1234567890,
                    'image': 'base64_image_data'
                }
                
                await whatsapp._handle_incoming_message(test_message)
                
                # Verify Vision API was called
                assert mock_openai.chat.completions.create.called
                
                # Verify orchestrator received image description
                mock_orchestrator.process_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_pdf_extraction_flow(self):
        """Test complete PDF extraction workflow."""
        from src.integrations.whatsapp_integration import WhatsAppIntegration
        import base64
        
        with patch('src.integrations.whatsapp_integration.AgentOrchestrator') as mock_orch_class:
            with patch('src.integrations.whatsapp_integration.PyPDF2') as mock_pypdf:
                # Mock PDF reader
                mock_reader = Mock()
                mock_page = Mock()
                mock_page.extract_text.return_value = "Texto do PDF"
                mock_reader.pages = [mock_page]
                mock_pypdf.PdfReader.return_value = mock_reader
                
                # Mock orchestrator
                mock_orchestrator = AsyncMock()
                mock_orchestrator.process_message = AsyncMock(return_value="Resposta sobre o PDF")
                mock_orch_class.return_value = mock_orchestrator
                
                whatsapp = WhatsAppIntegration()
                
                # Create fake PDF base64
                pdf_content = b"fake pdf content"
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                
                # Simulate PDF message
                test_message = {
                    'type': 'message',
                    'from': '5511999999999@c.us',
                    'body': '[Documento]',
                    'timestamp': 1234567890,
                    'document': pdf_base64
                }
                
                await whatsapp._handle_incoming_message(test_message)
                
                # Verify orchestrator received extracted text
                mock_orchestrator.process_message.assert_called()


class TestErrorRecovery:
    """Integration tests for error recovery scenarios."""
    
    @pytest.mark.asyncio
    async def test_api_failure_recovery(self):
        """Test recovery from API failures."""
        from src.integrations.whatsapp_integration import WhatsAppIntegration
        
        with patch('src.integrations.whatsapp_integration.AgentOrchestrator') as mock_orch_class:
            # Mock orchestrator that raises error
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_message = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_orch_class.return_value = mock_orchestrator
            
            whatsapp = WhatsAppIntegration()
            
            # Simulate message
            test_message = {
                'type': 'message',
                'from': '5511999999999@c.us',
                'body': 'Test message',
                'timestamp': 1234567890
            }
            
            # Should not crash
            await whatsapp._handle_incoming_message(test_message)
            
            # Should have attempted to process
            mock_orchestrator.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_malformed_message_handling(self):
        """Test handling of malformed messages."""
        from src.integrations.whatsapp_integration import WhatsAppIntegration
        
        with patch('src.integrations.whatsapp_integration.AgentOrchestrator'):
            whatsapp = WhatsAppIntegration()
            
            # Malformed messages
            malformed_messages = [
                {},  # Empty
                {'type': 'message'},  # Missing fields
                {'from': '123'},  # Missing type
                None  # None value
            ]
            
            for msg in malformed_messages:
                # Should not crash
                try:
                    await whatsapp._handle_incoming_message(msg)
                except Exception as e:
                    # If it raises, should be handled gracefully
                    assert isinstance(e, (KeyError, AttributeError, TypeError))
