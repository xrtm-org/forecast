# Resilience & Retries

> **Moved in 0.9–0.10.** The dedicated `ResilientProvider` / `RetryConfig`
> modules were removed; resilience is configured directly on the inference provider.

Retry, backoff, rate limiting, and timeouts live on `OpenAIConfig`:

| Setting | Purpose |
|---|---|
| `max_retries` | Retry attempts for transient API errors (default 2) |
| `backoff_base` | Exponential backoff base in seconds (jittered 50–100%) |
| `retry_on_empty_content` | Retry once with a larger `max_tokens` when a reasoning model returns no content |
| `empty_content_multiplier` | `max_tokens` multiplier applied to that retry |
| `rate_limit_timeout_seconds` | How long a call waits for a rate-limit token |
| `redis_url` | Optional Redis for cross-process rate limiting |
| `timeout` | Request timeout in seconds (default 120; reasoning models need it) |

See [Inference](inference.md) for the full configuration surface and
[Cache](cache.md) for TTL/eviction behaviour.
