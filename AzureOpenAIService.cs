// AzureOpenAIService.cs
using Azure;
using Azure.AI.OpenAI;
using Azure.Identity;
using Azure.Security.KeyVault.Secrets;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Polly;
using Polly.Retry;
using System.Text.Json;

namespace AzureOpenAIIntegration.Services;

public class AzureOpenAIService
{
    private readonly OpenAIClient _client;
    private readonly string _deploymentName;
    private readonly ILogger<AzureOpenAIService> _logger;
    private readonly AsyncRetryPolicy _retryPolicy;
    private readonly int _maxTokens;
    private readonly float _temperature;

    public AzureOpenAIService(
        IConfiguration configuration,
        ILogger<AzureOpenAIService> logger)
    {
        _logger = logger;
        
        var endpoint = configuration["AzureOpenAI:Endpoint"] 
            ?? throw new ArgumentNullException("AzureOpenAI:Endpoint");
        _deploymentName = configuration["AzureOpenAI:DeploymentName"] 
            ?? throw new ArgumentNullException("AzureOpenAI:DeploymentName");
        _maxTokens = int.Parse(configuration["AzureOpenAI:MaxTokens"] ?? "4000");
        _temperature = float.Parse(configuration["AzureOpenAI:Temperature"] ?? "0.3");

        // Usa Managed Identity per produzione, API Key per dev
        var credential = new DefaultAzureCredential();
        
        // Recupero sicuro API Key da Key Vault
        var keyVaultUri = configuration["AzureOpenAI:KeyVaultUri"];
        if (!string.IsNullOrEmpty(keyVaultUri))
        {
            var secretClient = new SecretClient(
                new Uri(keyVaultUri), 
                credential
            );
            var secret = secretClient.GetSecret("AzureOpenAIKey").Value;
            _client = new OpenAIClient(new Uri(endpoint), new AzureKeyCredential(secret.Value));
        }
        else
        {
            _client = new OpenAIClient(new Uri(endpoint), credential);
        }

        // Polly retry policy per resilienza
        _retryPolicy = Policy
            .Handle<RequestFailedException>(ex => 
                ex.Status == 429 || // Rate limit
                ex.Status == 503    // Service unavailable
            )
            .WaitAndRetryAsync(
                retryCount: 3,
                sleepDurationProvider: attempt => TimeSpan.FromSeconds(Math.Pow(2, attempt)),
                onRetry: (exception, timeSpan, retryCount, context) =>
                {
                    _logger.LogWarning(
                        "Retry {RetryCount} dopo {Delay}s. Errore: {Error}",
                        retryCount, timeSpan.TotalSeconds, exception.Message
                    );
                }
            );
    }

    public async Task<string> CompleteChatAsync(
        string systemPrompt,
        string userMessage,
        CancellationToken cancellationToken = default)
    {
        return await _retryPolicy.ExecuteAsync(async () =>
        {
            var startTime = DateTime.UtcNow;
            
            var chatCompletionsOptions = new ChatCompletionsOptions
            {
                DeploymentName = _deploymentName,
                Messages =
                {
                    new ChatRequestSystemMessage(systemPrompt),
                    new ChatRequestUserMessage(userMessage)
                },
                MaxTokens = _maxTokens,
                Temperature = _temperature,
                FrequencyPenalty = 0,
                PresencePenalty = 0,
                NucleusSamplingFactor = 0.95f
            };

            try
            {
                Response<ChatCompletions> response = await _client.GetChatCompletionsAsync(
                    chatCompletionsOptions,
                    cancellationToken
                );

                var completionTime = DateTime.UtcNow - startTime;
                
                _logger.LogInformation(
                    "Completamento Azure OpenAI: {Tokens} tokens, {Time}ms, Modello: {Model}",
                    response.Value.Usage.TotalTokens,
                    completionTime.TotalMilliseconds,
                    response.Value.Model
                );

                return response.Value.Choices[0].Message.Content;
            }
            catch (RequestFailedException ex)
            {
                _logger.LogError(ex, "Errore chiamata Azure OpenAI: {StatusCode}", ex.Status);
                throw;
            }
        });
    }

    public async Task<T> ExtractStructuredDataAsync<T>(
        string document,
        string extractionInstructions,
        CancellationToken cancellationToken = default)
    {
        var systemPrompt = $@"
Sei un assistente specializzato nell'estrazione di dati strutturati da documenti.
Estrai i dati seguendo queste istruzioni:

{extractionInstructions}

IMPORTANTE:
- Rispondi SOLO con JSON valido
- Non aggiungere testo prima o dopo il JSON
- Usa null per valori mancanti
- Mantieni la struttura esatta richiesta
";

        var userMessage = $"Documento da analizzare:\n\n{document}";

        var jsonResponse = await CompleteChatAsync(
            systemPrompt,
            userMessage,
            cancellationToken
        );

        // Pulizia risposta (rimozione eventuali markdown)
        var cleanJson = jsonResponse
            .Replace("```json", "")
            .Replace("```", "")
            .Trim();

        try
        {
            return JsonSerializer.Deserialize<T>(cleanJson)
                ?? throw new InvalidOperationException("Deserializzazione ha prodotto null");
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Errore parsing JSON. Risposta: {Response}", cleanJson);
            throw new InvalidOperationException(
                "Impossibile deserializzare la risposta in formato JSON", ex
            );
        }
    }
}
/* Client Service con Best Practices */
