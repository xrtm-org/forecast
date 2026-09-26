# Streaming Sovereignty

For specialized financial interfaces, the "appearance of thinking" is as important as the answer. `xrtm-forecast` enforces a **Standardized Streaming Protocol** across all providers (Cloud or Local).

## The Standard
All `InferenceProvider` implementations must implement `stream()` returning an `AsyncIterable`.
The yielded chunks must adhere to the following JSON structure (inspired by the Amazon Bedrock / Anthropic schema):

```json
{
  "contentBlockDelta": {
    "delta": {
      "text": " partial_token_string"
    }
  }
}
```

This standardization ensures that your UI/Frontend code never needs to handle "OpenAI format" vs "Gemini format" vs "HuggingFace format".

## Streaming Providers

Streaming is supported by the OpenAI-compatible providers (including
`AnthropicProvider` and `MockProvider`) through `provider.stream(...)`.

> **Removed in 0.9–0.10.** The dedicated `HuggingFaceProvider` (and its local
> `TextIteratorStreamer` path) was removed. Point an OpenAI-compatible provider
> at a local server (e.g. vLLM or Ollama's OpenAI-compatible endpoint) to stream
> from local models.

**Usage:**
```python
async for chunk in provider.stream("Explain inflation"):
    if "contentBlockDelta" in chunk:
        print(chunk["contentBlockDelta"]["delta"]["text"], end="", flush=True)
```
