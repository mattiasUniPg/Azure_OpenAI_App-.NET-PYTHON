// CachedOpenAIService.cs
using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using System.Security.Cryptography;
using System.Text;

public class CachedOpenAIService
{
    private readonly AzureOpenAIService _openAIService;
    private readonly IDistributedCache _cache;
    private readonly ILogger<CachedOpenAIService> _logger;
    private readonly TimeSpan _cacheExpiration = TimeSpan.FromHours(24);

    public CachedOpenAIService(
        AzureOpenAIService openAIService,
        IDistributedCache cache,
        ILogger<CachedOpenAIService> logger)
    {
        _openAIService = openAIService;
        _cache = cache;
        _logger = logger;
    }

    public async Task<string> CompleteChatWithCacheAsync(
        string systemPrompt,
        string userMessage,
        CancellationToken cancellationToken = default)
    {
        // Genera cache key da hash dei prompt
        var cacheKey = GenerateCacheKey(systemPrompt, userMessage);

        // Verifica cache
        var cachedResult = await _cache.GetStringAsync(cacheKey, cancellationToken);
        if (!string.IsNullOrEmpty(cachedResult))
        {
            _logger.LogInformation("Cache hit per richiesta");
            return cachedResult;
        }

        // Cache miss: chiama API
        _logger.LogInformation("Cache miss: chiamata Azure OpenAI");
        var result = await _openAIService.CompleteChatAsync(
            systemPrompt,
            userMessage,
            cancellationToken
        );

        // Salva in cache
        var cacheOptions = new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = _cacheExpiration
        };
        await _cache.SetStringAsync(cacheKey, result, cacheOptions, cancellationToken);

        return result;
    }

    private static string GenerateCacheKey(string systemPrompt, string userMessage)
    {
        var combined = $"{systemPrompt}|{userMessage}";
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(combined));
        return $"aoai:{Convert.ToHexString(hash)}";
    }
}
/* Connection Pooling e Caching */
/*  Scaling e Performance */
