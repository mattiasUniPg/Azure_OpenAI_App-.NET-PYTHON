# azure_openai_service.py
import asyncio
import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timedelta
from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from pydantic import BaseModel
import json

from config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class RateLimiter:
    """Rate limiter per rispettare i limiti Azure OpenAI"""
    
    def __init__(self, max_requests: int, max_tokens: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.max_tokens = max_tokens
        self.window_seconds = window_seconds
        self.requests: List[datetime] = []
        self.tokens_used: List[tuple[datetime, int]] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self, estimated_tokens: int = 1000):
        """Attendi se necessario per rispettare i rate limits"""
        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.window_seconds)
            
            # Pulisci vecchie richieste
            self.requests = [r for r in self.requests if r > cutoff]
            self.tokens_used = [(t, tokens) for t, tokens in self.tokens_used if t > cutoff]
            
            # Calcola utilizzo corrente
            current_requests = len(self.requests)
            current_tokens = sum(tokens for _, tokens in self.tokens_used)
            
            # Attendi se necessario
            if current_requests >= self.max_requests or \
               current_tokens + estimated_tokens > self.max_tokens:
                wait_time = (self.requests[0] - cutoff).total_seconds() if self.requests else 1
                logger.warning(f"Rate limit raggiunto, attesa di {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                return await self.acquire(estimated_tokens)
            
            # Registra utilizzo
            self.requests.append(now)
            self.tokens_used.append((now, estimated_tokens))

class AzureOpenAIService:
    """Service per interazioni con Azure OpenAI"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = self._initialize_client()
        self.rate_limiter = RateLimiter(
            max_requests=self.settings.max_requests_per_minute,
            max_tokens=self.settings.max_tokens_per_minute
        )
    
    def _initialize_client(self) -> AsyncAzureOpenAI:
        """Inizializza client con autenticazione sicura"""
        
        # Produzione: usa Key Vault + Managed Identity
        if self.settings.azure_key_vault_url:
            credential = DefaultAzureCredential()
            secret_client = SecretClient(
                vault_url=self.settings.azure_key_vault_url,
                credential=credential
            )
            api_key = secret_client.get_secret("AzureOpenAIKey").value
        else:
            # Development: usa chiave da environment
            api_key = self.settings.azure_openai_key
        
        return AsyncAzureOpenAI(
            api_key=api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint
        )
    
    @retry(
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry {retry_state.attempt_number} dopo errore: {retry_state.outcome.exception()}"
        )
    )
    async def complete_chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Completamento chat con retry automatico"""
        
        # Stima token per rate limiting
        estimated_tokens = len(system_prompt.split()) + len(user_message.split()) * 1.3
        await self.rate_limiter.acquire(int(estimated_tokens))
        
        start_time = datetime.now()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature or self.settings.temperature,
                max_tokens=max_tokens or self.settings.max_tokens,
                top_p=self.settings.top_p
            )
            
            completion_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Completamento: {response.usage.total_tokens} tokens, "
                f"{completion_time:.2f}s, modello: {response.model}"
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Errore chiamata Azure OpenAI: {e}")
            raise
    
    async def extract_structured_data(
        self,
        document: str,
        extraction_instructions: str,
        response_model: type[T]
    ) -> T:
        """Estrazione dati strutturati con validazione Pydantic"""
        
        system_prompt = f"""
Sei un assistente specializzato nell'estrazione di dati strutturati.

ISTRUZIONI:
{extraction_instructions}

REGOLE CRITICHE:
1. Rispondi SOLO con JSON valido
2. NO testo prima o dopo il JSON
3. NO markdown code blocks
4. Usa null per valori mancanti
5. Rispetta esattamente lo schema richiesto

Schema JSON atteso:
{response_model.model_json_schema()}
"""
        
        user_message = f"Documento da analizzare:\n\n{document}"
        
        json_response = await self.complete_chat(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.1  # Bassa temperatura per output strutturato
        )
        
        # Pulizia risposta
        clean_json = json_response.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("```")[1]
            if clean_json.startswith("json"):
                clean_json = clean_json[4:]
        clean_json = clean_json.strip()
        
        try:
            data = json.loads(clean_json)
            return response_model.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Errore parsing JSON: {e}\nRisposta: {clean_json}")
            raise ValueError(f"Impossibile parsare risposta come JSON: {e}")
          /* Client Service con Retry Logic */
