# prompt_optimizer.py
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class PromptOptimizer:
    """Ottimizzatore prompt basato su feedback e metriche"""
    
    def __init__(self):
        self.success_metrics: Dict[str, List[float]] = {}
    
    def optimize_extraction_prompt(
        self,
        base_prompt: str,
        field_name: str,
        success_rate: float
    ) -> str:
        """Ottimizza prompt in base a success rate"""
        
        # Traccia performance
        if field_name not in self.success_metrics:
            self.success_metrics[field_name] = []
        self.success_metrics[field_name].append(success_rate)
        
        # Se success rate < 80%, aggiungi specifiche
        if success_rate < 0.8:
            enhancements = self._get_field_enhancements(field_name)
            enhanced_prompt = f"{base_prompt}\n\nATTENZIONE SPECIALE al campo '{field_name}':\n{enhancements}"
            
            logger.info(
                f"Prompt ottimizzato per {field_name} "
                f"(success rate: {success_rate:.1%})"
            )
            
            return enhanced_prompt
        
        return base_prompt
    
    def _get_field_enhancements(self, field_name: str) -> str:
        """Suggerimenti specifici per campo problematico"""
        
        enhancements = {
            "invoice_number": """
- Cerca pattern: 'Fattura N.', 'Invoice #', 'FT', numeri prominenti
- Può essere in header o footer
- Spesso vicino alla data
- Formato tipico: numeri con separatori (/, -, etc.)
            """,
            "date": """
- Formati comuni: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
- Cerca label: 'Data', 'Date', 'Del'
- Può essere vicino al numero fattura
- Valida che sia una data plausibile
            """,
            "vat_number": """
- Italia: 11 cifre
- Cerca label: 'P.IVA', 'Partita IVA', 'VAT', 'P. IVA'
- Pulisci spazi e punteggiatura
- Verifica lunghezza corretta
            """,
            "total_amount": """
- Cerca 'Totale', 'Total', 'TOTALE FATTURA'
- Formato: numero con decimali (. o ,)
- Può avere simbolo valuta (€, EUR)
- È l'importo più grande nel documento
- Verifica coerenza con subtotal + IVA
            """
        }
        
        return enhancements.get(field_name, "Verifica attentamente questo campo.")
    
    def generate_validation_prompt(
        self,
        extracted_data: Dict[str, Any],
        original_document: str
    ) -> str:
        """Genera prompt per auto-validazione"""
        
        return f"""
Sei un validatore esperto. Verifica la correttezza dei dati estratti.

DATI ESTRATTI:
{json.dumps(extracted_data, indent=2, ensure_ascii=False)}

DOCUMENTO ORIGINALE:
{original_document}

VERIFICA:
1. Ogni dato estratto è presente nel documento?
2. I formati sono corretti?
3. I numeri hanno senso (es. subtotal + IVA = total)?
4. Le date sono plausibili?

OUTPUT JSON:
{{
  "is_valid": true/false,
  "errors": [...],  // lista errori trovati
  "confidence": 0.0-1.0,
  "suggestions": [...]  // suggerimenti correzione
}}
"""
/* Ottimizzazione Prompt per Accuratezza */
