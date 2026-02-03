"""Configuration management for the WhatsApp chatbot."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI Configuration
    openai_api_key: str
    
    # WhatsApp Configuration
    whatsapp_session_name: str = "generic-wpp-chatbot"
    whatsapp_headless: bool = True
    
    # Email Configuration
    sendgrid_api_key: Optional[str] = None
    sender_email: Optional[str] = None
    
    # Google Calendar Configuration
    google_calendar_credentials_path: str = "./credentials/google_calendar_credentials.json"
    google_calendar_token_path: str = "./credentials/token.json"
    
    # Knowledge Base Configuration
    knowledge_base_path: str = "./knowledge_base"
    vector_db_path: str = "./data/vector_db"
    
    # Kestra Configuration
    kestra_api_url: str = "http://localhost:8080"
    kestra_namespace: str = "whatsapp-chatbot"
    
    # Application Configuration
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # Conversation Memory Configuration
    max_history_tokens: int = 2000  # Token limit before triggering summary
    keep_recent_messages: int = 4  # Recent messages to keep uncompressed
    enable_conversation_summary: bool = True  # Enable/disable auto-summarization
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
