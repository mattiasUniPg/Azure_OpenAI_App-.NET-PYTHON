# models/document_models.py
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional
from enum import Enum

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    REPORT = "report"
    EMAIL = "email"

class InvoiceData(BaseModel):
    """Modello per dati fattura estratti"""
    
    invoice_number: str = Field(..., description="Numero fattura")
    invoice_date: date = Field(..., description="Data emissione")
    due_date: Optional[date] = Field(None, description="Data scadenza")
    
    supplier_name: str = Field(..., description="Nome fornitore")
    supplier_vat: str = Field(..., description="P.IVA fornitore")
    supplier_address: Optional[str] = None
    
    client_name: str = Field(..., description="Nome cliente")
    client_vat: str = Field(..., description="P.IVA cliente")
    
    subtotal: float = Field(..., gt=0, description="Imponibile")
    vat_amount: float = Field(..., ge=0, description="Importo IVA")
    total_amount: float = Field(..., gt=0, description="Totale fattura")
    
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")
    
    line_items: List[dict] = Field(default_factory=list)
    payment_terms: Optional[str] = None
    
    @field_validator('supplier_vat', 'client_vat')
    @classmethod
    def validate_italian_vat(cls, v: str) -> str:
        """Valida formato P.IVA italiana"""
        cleaned = v.replace(" ", "").replace(".", "")
        if not cleaned.isdigit() or len(cleaned) != 11:
            raise ValueError(f"P.IVA non valida: {v}")
        return cleaned

class DocumentSummary(BaseModel):
    """Sommario documento generato da AI"""
    
    document_type: DocumentType
    title: str = Field(..., max_length=200)
    summary: str = Field(..., description="Sommario esecutivo")
    key_points: List[str] = Field(..., min_items=1, max_items=10)
    entities_mentioned: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = Field(None, pattern="^(positive|neutral|negative)$")
    confidence_score: float = Field(..., ge=0, le=1)

# document_processor.py
import asyncio
from typing import List
from azure_openai_service import AzureOpenAIService
from models.document_models import InvoiceData, DocumentSummary, DocumentType

class DocumentProcessor:
    """Processore documenti con AI"""
    
    def __init__(self):
        self.openai_service = AzureOpenAIService()
    
    async def extract_invoice_data(self, document_text: str) -> InvoiceData:
        """Estrae dati strutturati da fattura"""
        
        extraction_instructions = """
Estrai tutte le informazioni dalla fattura seguendo lo schema JSON.

ATTENZIONE PARTICOLARE a:
- Date: formato YYYY-MM-DD
- Importi: numeri decimali (usa . come separatore)
- P.IVA: 11 cifre senza spazi
- Valuta: codice ISO 3 lettere (EUR, USD, etc.)

Per line_items, estrai ogni riga con:
- description: descrizione prodotto/servizio
- quantity: quantità
- unit_price: prezzo unitario
- total: totale riga
"""
        
        logger.info("Inizio estrazione dati fattura")
        
        invoice_data = await self.openai_service.extract_structured_data(
            document=document_text,
            extraction_instructions=extraction_instructions,
            response_model=InvoiceData
        )
        
        logger.info(
            f"Fattura estratta: {invoice_data.invoice_number}, "
            f"totale €{invoice_data.total_amount:.2f}"
        )
        
        return invoice_data
    
    async def summarize_document(
        self,
        document_text: str,
        document_type: DocumentType
    ) -> DocumentSummary:
        """Genera sommario intelligente del documento"""
        
        extraction_instructions = f"""
Analizza questo documento di tipo {document_type.value} e crea un sommario strutturato.

Il sommario deve includere:
1. title: titolo descrittivo (max 200 caratteri)
2. summary: sintesi esecutiva (2-4 paragrafi, max 500 parole)
3. key_points: 3-7 punti chiave più importanti
4. entities_mentioned: nomi di persone, aziende, luoghi menzionati
5. sentiment: tono generale (positive/neutral/negative)
6. confidence_score: tua confidenza nell'analisi (0.0-1.0)

Usa linguaggio professionale e chiaro.
"""
        
        result = await self.openai_service.extract_structured_data(
            document=document_text,
            extraction_instructions=extraction_instructions,
            response_model=DocumentSummary
        )
        
        return result
    
    async def batch_process_documents(
        self,
        documents: List[tuple[str, str]],  # (id, text)
        max_concurrent: int = 5
    ) -> List[tuple[str, InvoiceData]]:
        """Elaborazione batch con concorrenza controllata"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_one(doc_id: str, doc_text: str):
            async with semaphore:
                try:
                    data = await self.extract_invoice_data(doc_text)
                    return (doc_id, data)
                except Exception as e:
                    logger.error(f"Errore documento {doc_id}: {e}")
                    return (doc_id, None)
        
        tasks = [process_one(doc_id, text) for doc_id, text in documents]
        results = await asyncio.gather(*tasks)
        
        successful = [(doc_id, data) for doc_id, data in results if data is not None]
        
        logger.info(
            f"Batch completato: {len(successful)}/{len(documents)} successi"
        )
        
        return successful
 /*  Analisi Documentale Avanzata */
