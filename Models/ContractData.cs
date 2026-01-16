// Models/ContractData.cs
public record ContractData
{
    public string ContractNumber { get; init; } = string.Empty;
    public DateTime? StartDate { get; init; }
    public DateTime? EndDate { get; init; }
    public decimal ContractValue { get; init; }
    public string ClientName { get; init; } = string.Empty;
    public string ClientVAT { get; init; } = string.Empty;
    public List<string> Services { get; init; } = new();
    public PaymentTerms Payment { get; init; } = new();
    public string ContractType { get; init; } = string.Empty;
}

public record PaymentTerms
{
    public int DaysNet { get; init; }
    public string Frequency { get; init; } = string.Empty;
    public string Method { get; init; } = string.Empty;
}

// ContractProcessor.cs
public class ContractProcessor
{
    private readonly AzureOpenAIService _openAIService;
    private readonly ILogger<ContractProcessor> _logger;

    public ContractProcessor(
        AzureOpenAIService openAIService,
        ILogger<ContractProcessor> logger)
    {
        _openAIService = openAIService;
        _logger = logger;
    }

    public async Task<ContractData> ExtractContractDataAsync(
        string contractText,
        CancellationToken cancellationToken = default)
    {
        var extractionInstructions = @"
Estrai le seguenti informazioni dal contratto:

Schema JSON richiesto:
{
  ""contractNumber"": ""string"",
  ""startDate"": ""YYYY-MM-DD"",
  ""endDate"": ""YYYY-MM-DD"",
  ""contractValue"": decimal,
  ""clientName"": ""string"",
  ""clientVAT"": ""string"",
  ""services"": [""string""],
  ""payment"": {
    ""daysNet"": integer,
    ""frequency"": ""string"",
    ""method"": ""string""
  },
  ""contractType"": ""string""
}

Regole di estrazione:
1. Date in formato ISO (YYYY-MM-DD)
2. Importi in formato numerico puro
3. Partita IVA italiana: 11 cifre
4. Services: array di servizi distinti
5. Payment.DaysNet: numero di giorni (es. 30, 60, 90)
";

        _logger.LogInformation("Inizio estrazione dati contratto");

        var contractData = await _openAIService.ExtractStructuredDataAsync<ContractData>(
            contractText,
            extractionInstructions,
            cancellationToken
        );

        _logger.LogInformation(
            "Dati estratti: Contratto {Number}, Cliente {Client}, Valore €{Value}",
            contractData.ContractNumber,
            contractData.ClientName,
            contractData.ContractValue
        );

        return contractData;
    }

    public async Task<string> SummarizeContractAsync(
        string contractText,
        CancellationToken cancellationToken = default)
    {
        var systemPrompt = @"
Sei un esperto legale specializzato in analisi contrattuale.
Crea un sommario esecutivo del contratto che includa:

1. OVERVIEW (2-3 righe)
   - Tipo di contratto
   - Parti coinvolte
   - Oggetto principale

2. TERMINI CHIAVE
   - Durata
   - Valore economico
   - Condizioni di pagamento

3. OBBLIGAZIONI PRINCIPALI
   - Obblighi del fornitore
   - Obblighi del cliente

4. CLAUSOLE CRITICHE
   - Penali
   - Risoluzione anticipata
   - Rinnovo automatico

5. RISK ASSESSMENT
   - Rischi identificati
   - Raccomandazioni

Usa un linguaggio professionale ma comprensibile.
Lunghezza: massimo 500 parole.
";

        return await _openAIService.CompleteChatAsync(
            systemPrompt,
            $"Contratto da analizzare:\n\n{contractText}",
            cancellationToken
        );
    }
}
/*  Estrazione Dati da Contratti */
