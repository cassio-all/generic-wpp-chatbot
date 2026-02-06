"""Tests for FAISS Knowledge Base with auto-monitoring."""
import pytest
import tempfile
import os
import time
from unittest.mock import Mock, patch, MagicMock
from src.services.knowledge_base_faiss import KnowledgeBaseService


@pytest.fixture
def temp_knowledge_dir():
    """Create temporary knowledge base directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_vector_db_dir():
    """Create temporary vector database directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_settings(temp_knowledge_dir, temp_vector_db_dir):
    """Mock settings for testing."""
    mock = Mock()
    mock.knowledge_base_path = temp_knowledge_dir
    mock.vector_db_path = temp_vector_db_dir
    mock.openai_api_key = "test_key"
    return mock


class TestKnowledgeBaseInitialization:
    """Tests for knowledge base initialization."""
    
    def test_create_new_knowledge_base(self, mock_settings):
        """Test creating new knowledge base from scratch."""
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                
                # Should create sample file if directory is empty
                sample_path = os.path.join(mock_settings.knowledge_base_path, "sample.txt")
                assert os.path.exists(sample_path) or kb.vector_store is not None
    
    def test_load_existing_knowledge_base(self, mock_settings, temp_vector_db_dir):
        """Test loading existing FAISS index."""
        # Create fake FAISS index directory
        faiss_path = os.path.join(temp_vector_db_dir, "faiss_index")
        os.makedirs(faiss_path, exist_ok=True)
        
        # Create dummy index files
        open(os.path.join(faiss_path, "index.faiss"), 'w').close()
        open(os.path.join(faiss_path, "index.pkl"), 'w').close()
        
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                with patch('src.services.knowledge_base_faiss.FAISS.load_local') as mock_load:
                    mock_load.return_value = Mock()
                    kb = KnowledgeBaseService()
                    
                    # Should load existing index
                    mock_load.assert_called_once()


class TestKnowledgeSearch:
    """Tests for knowledge base search functionality."""
    
    def test_search_with_results(self, mock_settings):
        """Test search returning results."""
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                
                # Mock vector store
                mock_doc1 = Mock(page_content="Informação sobre o produto X")
                mock_doc2 = Mock(page_content="Detalhes do serviço Y")
                kb.vector_store = Mock()
                kb.vector_store.similarity_search.return_value = [mock_doc1, mock_doc2]
                
                results = kb.search("produto X", k=2)
                
                assert len(results) == 2
                assert "produto X" in results[0]
    
    def test_search_no_results(self, mock_settings):
        """Test search with no results."""
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                
                # Mock empty results
                kb.vector_store = Mock()
                kb.vector_store.similarity_search.return_value = []
                
                results = kb.search("query inexistente", k=3)
                
                assert results == []
    
    def test_search_without_vector_store(self, mock_settings):
        """Test search when vector store is not initialized."""
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                kb.vector_store = None
                
                results = kb.search("test query")
                
                assert results == []


class TestAutoMonitoring:
    """Tests for automatic file monitoring and reindexing."""
    
    def test_get_files_hash(self, mock_settings, temp_knowledge_dir):
        """Test file hash calculation."""
        # Create test files
        test_file = os.path.join(temp_knowledge_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                
                files_hash = kb._get_files_hash()
                
                assert test_file in files_hash
                assert len(files_hash[test_file]) == 32  # MD5 hash length
    
    def test_check_for_changes_new_file(self, mock_settings, temp_knowledge_dir):
        """Test change detection when new file is added."""
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                
                # Initial state
                kb.files_hash = {}
                
                # Add new file
                test_file = os.path.join(temp_knowledge_dir, "new.txt")
                with open(test_file, 'w') as f:
                    f.write("New content")
                
                # Check for changes
                has_changes = kb._check_for_changes()
                
                assert has_changes is True
    
    def test_check_for_changes_modified_file(self, mock_settings, temp_knowledge_dir):
        """Test change detection when file is modified."""
        # Create initial file
        test_file = os.path.join(temp_knowledge_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Original content")
        
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                
                # Store initial hash
                kb.files_hash = kb._get_files_hash()
                
                # Modify file
                time.sleep(0.1)  # Ensure different timestamp
                with open(test_file, 'w') as f:
                    f.write("Modified content")
                
                # Check for changes
                has_changes = kb._check_for_changes()
                
                assert has_changes is True
    
    def test_check_for_changes_no_changes(self, mock_settings, temp_knowledge_dir):
        """Test that no changes are detected when files unchanged."""
        # Create file
        test_file = os.path.join(temp_knowledge_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Content")
        
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                
                # Store hash
                kb.files_hash = kb._get_files_hash()
                
                # Check for changes (no modifications)
                has_changes = kb._check_for_changes()
                
                assert has_changes is False


class TestKnowledgeBaseAddDocuments:
    """Tests for adding documents to knowledge base."""
    
    def test_add_documents_to_existing_store(self, mock_settings):
        """Test adding documents to existing vector store."""
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                kb = KnowledgeBaseService()
                
                # Mock existing vector store
                kb.vector_store = Mock()
                kb.vector_store.add_documents = Mock()
                kb.vector_store.save_local = Mock()
                
                docs = ["Documento 1", "Documento 2"]
                metadatas = [{"source": "test1"}, {"source": "test2"}]
                
                kb.add_documents(docs, metadatas)
                
                kb.vector_store.add_documents.assert_called_once()
                kb.vector_store.save_local.assert_called_once()
    
    def test_add_documents_creates_new_store(self, mock_settings):
        """Test adding documents when no vector store exists."""
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                with patch('src.services.knowledge_base_faiss.FAISS.from_documents') as mock_from_docs:
                    mock_from_docs.return_value = Mock()
                    mock_from_docs.return_value.save_local = Mock()
                    
                    kb = KnowledgeBaseService()
                    kb.vector_store = None
                    
                    docs = ["Documento novo"]
                    kb.add_documents(docs)
                    
                    mock_from_docs.assert_called_once()


class TestKnowledgeBaseRebuild:
    """Tests for rebuilding knowledge base."""
    
    def test_rebuild_knowledge_base(self, mock_settings, temp_knowledge_dir):
        """Test full rebuild of knowledge base."""
        # Create test file
        test_file = os.path.join(temp_knowledge_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content for rebuild")
        
        with patch('src.services.knowledge_base_faiss.settings', mock_settings):
            with patch('src.services.knowledge_base_faiss.OpenAIEmbeddings'):
                with patch('src.services.knowledge_base_faiss.DirectoryLoader') as mock_loader:
                    with patch('src.services.knowledge_base_faiss.FAISS.from_documents') as mock_from_docs:
                        # Mock document loading
                        mock_doc = Mock(page_content="Test content")
                        mock_loader.return_value.load.return_value = [mock_doc]
                        
                        # Mock FAISS creation
                        mock_store = Mock()
                        mock_store.save_local = Mock()
                        mock_from_docs.return_value = mock_store
                        
                        kb = KnowledgeBaseService()
                        kb.rebuild()
                        
                        # Should have called from_documents
                        mock_from_docs.assert_called()
