"""Knowledge base service for retrieving information."""
import os
from typing import List, Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from src.config import settings
import structlog

logger = structlog.get_logger()


class KnowledgeBaseService:
    """Service for managing and querying the knowledge base."""
    
    def __init__(self):
        """Initialize the knowledge base service."""
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.vector_store: Optional[Chroma] = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize or load the vector store."""
        if os.path.exists(settings.vector_db_path):
            logger.info("Loading existing vector store", path=settings.vector_db_path)
            self.vector_store = Chroma(
                persist_directory=settings.vector_db_path,
                embedding_function=self.embeddings
            )
        else:
            logger.info("Creating new vector store", path=settings.vector_db_path)
            self._build_knowledge_base()
    
    def _build_knowledge_base(self):
        """Build the knowledge base from documents in the knowledge_base directory."""
        if not os.path.exists(settings.knowledge_base_path):
            logger.warning("Knowledge base path does not exist", path=settings.knowledge_base_path)
            os.makedirs(settings.knowledge_base_path, exist_ok=True)
            
            # Create a sample knowledge file
            sample_path = os.path.join(settings.knowledge_base_path, "sample.txt")
            with open(sample_path, "w") as f:
                f.write("This is a generic WhatsApp chatbot. You can add your knowledge base files in the knowledge_base directory.")
        
        # Load documents
        loader = DirectoryLoader(
            settings.knowledge_base_path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True
        )
        documents = loader.load()
        
        if not documents:
            logger.warning("No documents found in knowledge base")
            # Create empty vector store
            self.vector_store = Chroma(
                persist_directory=settings.vector_db_path,
                embedding_function=self.embeddings
            )
            return
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        logger.info("Building vector store", num_documents=len(documents), num_splits=len(splits))
        
        # Create vector store
        self.vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=settings.vector_db_path
        )
        
        logger.info("Vector store created successfully")
    
    def search(self, query: str, k: int = 3) -> List[str]:
        """Search the knowledge base for relevant information.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of relevant document contents
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized")
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            logger.error("Error searching knowledge base", error=str(e))
            return []
    
    def add_documents(self, texts: List[str]):
        """Add new documents to the knowledge base.
        
        Args:
            texts: List of text contents to add
        """
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return
        
        try:
            self.vector_store.add_texts(texts)
            logger.info("Documents added to knowledge base", num_documents=len(texts))
        except Exception as e:
            logger.error("Error adding documents to knowledge base", error=str(e))
