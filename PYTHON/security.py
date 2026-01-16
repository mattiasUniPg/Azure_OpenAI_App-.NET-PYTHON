# security.py
import hashlib
from typing import Optional
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

class SecureConfigManager:
    """Gestione sicura configurazione e segreti"""
    
    def __init__(self, key_vault_url: str):
        self.credential = ManagedIdentityCredential()
        self.secret_client = SecretClient(
            vault_url=key_vault_url,
            credential=self.credential
        )
    
    def get_api_key(self) -> str:
        """Recupera API key da Key Vault"""
        secret = self.secret_client.get_secret("AzureOpenAIKey")
        return secret.value
    
    def rotate_key(self, new_key: str):
        """Rotazione sicura API key"""
        self.secret_client.set_secret("AzureOpenAIKey", new_key)
        logger.info("API key ruotata con successo")
    
    @staticmethod
    def sanitize_pii(text: str) -> str:
        """Rimuovi PII prima di logging"""
        import re
        
        # Email
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     '[EMAIL]', text)
        
        # Numeri telefono (italiano)
        text = re.sub(r'\b\d{10,11}\b', '[PHONE]', text)
        
        # P.IVA
        text = re.sub(r'\b\d{11}\b', '[VAT]', text)
        
        # Codice Fiscale
        text = re.sub(r'\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b', 
                     '[CF]', text)
        
        return text
/* Sicurezza e Compliance */
