# prompt_templates.py
from string import Template
from typing import Dict, Any

class PromptTemplates:
    """Repository di prompt engineering testati"""
    
    # Estrazione dati con Chain-of-Thought
    EXTRACTION_COT = Template("""
Sei un esperto analista documentale. Il tuo compito è estrarre dati strutturati.

DOCUMENTO DA ANALIZZARE:
$document

PROCESSO DI ANALISI (segui questi step):

Step 1: IDENTIFICAZIONE
- Che tipo di documento è questo?
- Quali sono gli elementi chiave presenti?

Step 2: ESTRAZIONE
- Localizza ogni campo richiesto nello schema
- Verifica la presenza e validità dei dati

Step 3: VALIDAZIONE
- I dati estratti sono coerenti tra loro?
- Ci sono anomalie o incongruenze?

Step 4: FORMATTAZIONE
- Converti i dati nel formato JSON richiesto
- Assicurati che tutti i campi obbligatori siano presenti

SCHEMA JSON RICHIESTO:
$json_schema

OUTPUT:
Fornisci SOLO il JSON finale, senza spiegazioni o markdown.
""")
    
    # Summarization con Few-Shot Learning
    SUMMARIZATION_FEW_SHOT = Template("""
Crea un sommario esecutivo professionale del documento seguendo questi esempi:

ESEMPIO 1:
Input: [Contratto di fornitura software per €50.000, durata 12 mesi...]
Output: {
  "title": "Contratto Fornitura Software - Cliente XYZ",
  "summary": "Accordo annuale per licenze software enterprise con supporto 24/7...",
  "key_points": ["Valore contratto €50K", "Durata 12 mesi rinnovabili", ...]
}

ESEMPIO 2:
Input: [Email di escalation cliente insoddisfatto per ritardi...]
Output: {
  "title": "Escalation Cliente - Ritardi Consegna Progetto ABC",
  "summary": "Il cliente esprime insoddisfazione per ritardi di 3 settimane...",
  "key_points": ["Ritardo: 3 settimane", "Richiesta meeting urgente", ...]
}

ORA ANALIZZA QUESTO DOCUMENTO:
$document

Genera il sommario nello stesso formato degli esempi.
""")
    
    # Analisi sentiment con contesto
    SENTIMENT_ANALYSIS = Template("""
Analizza il sentiment e il tono di questo documento nel contesto $context.

DOCUMENTO:
$document

ANALISI RICHIESTA:
1. Sentiment generale (positive/neutral/negative)
2. Emotional tone (formal/casual/aggressive/etc.)
3. Urgency level (low/medium/high/critical)
4. Key concerns identificate
5. Action items implicite

Considera:
- Linguaggio usato (formale vs colloquiale)
- Presenza di termini urgenti o critici
- Richieste esplicite e implicite
- Tono complessivo della comunicazione

OUTPUT JSON:
{
  "sentiment": "...",
  "tone": "...",
  "urgency": "...",
  "concerns": [...],
  "action_items": [...],
  "confidence": 0.0-1.0
}
""")
    
    @staticmethod
    def render(template: Template, **kwargs: Any) -> str:
        """Render template con parametri"""
        return template.safe_substitute(**kwargs)
/* Template per Casi d'Uso Comuni */ 
/* Prompt Engineering Avanzato */
