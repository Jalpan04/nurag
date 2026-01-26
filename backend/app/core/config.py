from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Nurag"
    API_V1_STR: str = "/api"
    
    # Models
    CHAT_MODEL: str = "gemma3:latest"
    GRADER_MODEL: str = "gemma3:1b"
    ROUTER_MODEL: str = "qwen2.5-coder:7b"
    EMBEDDING_MODEL: str = "nomic-embed-text:latest"
    
    # Storage
    CHROMA_DB_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "neural_rag_knowledge"
    
    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
