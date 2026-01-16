# tests/test_document_processor.py
import pytest
from document_processor import DocumentProcessor
from models.document_models import InvoiceData

@pytest.mark.asyncio
async def test_invoice_extraction_accuracy():
    """Test accuratezza estrazione fattura"""
    processor = DocumentProcessor()
    
    # Sample fattura con dati noti
    sample_invoice = """
    FATTURA N. 2024/001
    Data: 15/01/2024
    
    Fornitore: Acme Corp SRL
    P.IVA: 12345678901
    
    Cliente: Beta Industries SPA
    P.IVA: 98765432109
    
    Imponibile: €1,000.00
    IVA 22%: €220.00
    TOTALE: €1,220.00
    """
    
    result = await processor.extract_invoice_data(sample_invoice)
    
    # Validazione risultati
    assert result.invoice_number == "2024/001"
    assert result.supplier_vat == "12345678901"
    assert result.client_vat == "98765432109"
    assert result.subtotal == 1000.00
    assert result.vat_amount == 220.00
    assert result.total_amount == 1220.00
    
    # Verifica coerenza matematica
    assert abs(result.subtotal + result.vat_amount - result.total_amount) < 0.01

@pytest.mark.asyncio
async def test_batch_processing_performance():
    """Test performance elaborazione batch"""
    processor = DocumentProcessor()
    
    # Genera 50 documenti test
    documents = [(f"doc_{i}", f"Sample document {i}") for i in range(50)]
    
    import time
    start = time.time()
    
    results = await processor.batch_process_documents(
        documents,
        max_concurrent=10
    )
    
    elapsed = time.time() - start
    
    # Verifica performance
    assert len(results) == 50
    assert elapsed < 60  # Deve completare in meno di 1 minuto
    
    throughput = len(results) / elapsed
    print(f"Throughput: {throughput:.2f} docs/sec")
  # Testing e Validazione
