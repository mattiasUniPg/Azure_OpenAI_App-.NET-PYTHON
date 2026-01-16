# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_key: str | None = None
    azure_openai_deployment: str
    azure_openai_api_version: str = "2024-02-15-preview"
    
    # Key Vault (per produzione)
    azure_key_vault_url: str | None = None
    
    # Configurazione modello
    max_tokens: int = 4000
    temperature: float = 0.3
    top_p: float = 0.95
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_tokens_per_minute: int = 90000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
  /*  Installazione e Configurazione */ 
