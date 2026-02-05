"""Knowledge base service using FAISS vector database."""
import os
from pathlib import Path
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config import settings
import structlog

logger = structlog.get_logger()


class KnowledgeBaseService:
    """Service for managing and querying the knowledge base using FAISS."""
    
    def __init__(self):
        """Initialize the knowledge base service."""
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.vector_store: Optional[FAISS] = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize or load the FAISS vector store."""
        try:
            faiss_path = os.path.join(settings.vector_db_path, "faiss_index")
            
            if os.path.exists(faiss_path):
                logger.info("Loading existing FAISS vector store", path=faiss_path)
                self.vector_store = FAISS.load_local(
                    faiss_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("✅ FAISS vector store loaded successfully")
            else:
                logger.info("Creating new FAISS vector store", path=faiss_path)
                self._build_knowledge_base()
        except Exception as e:
            logger.error("Error initializing FAISS vector store", error=str(e))
            self.vector_store = None
    
    def _build_knowledge_base(self):
        """Build the knowledge base from documents in the knowledge_base directory."""
        try:
            if not os.path.exists(settings.knowledge_base_path):
                logger.warning("Knowledge base path does not exist", path=settings.knowledge_base_path)
                os.makedirs(settings.knowledge_base_path, exist_ok=True)
                
                # Create a sample knowledge file
                sample_path = os.path.join(settings.knowledge_base_path, "sample.txt")
                with open(sample_path, "w", encoding="utf-8") as f:
                    f.write("Este é um chatbot genérico para WhatsApp.\n\n"
                           "Você pode adicionar seus próprios arquivos de conhecimento na pasta knowledge_base/.\n\n"
                           "Arquivos suportados: .txt\n\n"
                           "O sistema usa FAISS para busca vetorial eficiente.")
        
            # Load documents
            loader = DirectoryLoader(
                settings.knowledge_base_path,
                glob="**/*.txt",
                loader_cls=TextLoader,
                show_progress=False,
                silent_errors=True,
                loader_kwargs={"encoding": "utf-8"}
            )
            documents = loader.load()
            
            if not documents:
                logger.warning("No documents found in knowledge base")
                # Create minimal FAISS store with dummy document
                from langchain.docstore.document import Document
                dummy_doc = Document(
                    page_content="Sistema de base de conhecimento inicializado.",
                    metadata={"source": "system"}
                )
                self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)
            else:
                # Split documents
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                splits = text_splitter.split_documents(documents)
                
                logger.info("Building FAISS vector store", num_documents=len(documents), num_chunks=len(splits))
                
                # Create FAISS vector store
                self.vector_store = FAISS.from_documents(splits, self.embeddings)
                
                # Save to disk
                os.makedirs(os.path.dirname(os.path.join(settings.vector_db_path, "faiss_index")), exist_ok=True)
                self.vector_store.save_local(os.path.join(settings.vector_db_path, "faiss_index"))
                
                logger.info("✅ FAISS knowledge base built successfully", num_chunks=len(splits))
                
        except Exception as e:
            logger.error("Error building knowledge base", error=str(e))
            self.vector_store = None
    
    def search(self, query: str, k: int = 3) -> List[str]:
        """Search the knowledge base for relevant information.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of relevant document chunks
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized")
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            logger.error("Error searching knowledge base", error=str(e), query=query)
            return []
    
    def add_documents(self, documents: List[str], metadatas: List[dict] = None):
        """Add new documents to the knowledge base.
        
        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dicts
        """
        try:
            if not self.vector_store:
                # Create new vector store if not exists
                from langchain.docstore.document import Document
                docs = [Document(page_content=text, metadata=meta or {}) 
                       for text, meta in zip(documents, metadatas or [{}] * len(documents))]
                self.vector_store = FAISS.from_documents(docs, self.embeddings)
            else:
                # Add to existing
                from langchain.docstore.document import Document
                docs = [Document(page_content=text, metadata=meta or {}) 
                       for text, meta in zip(documents, metadatas or [{}] * len(documents))]
                self.vector_store.add_documents(docs)
            
            # Save updated store
            faiss_path = os.path.join(settings.vector_db_path, "faiss_index")
            os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
            self.vector_store.save_local(faiss_path)
            
            logger.info("Documents added to knowledge base", count=len(documents))
        except Exception as e:
            logger.error("Error adding documents", error=str(e))
    
    def rebuild(self):
        """Rebuild the entire knowledge base from source files."""
        logger.info("Rebuilding knowledge base")
        self._build_knowledge_base()
