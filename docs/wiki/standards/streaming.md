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

## Local Streaming (Hugging Face)
As of v0.1.5, the `HuggingFaceProvider` supports true asynchronous streaming.

*   **Technology**: Uses `TextIteratorStreamer` in a background thread to generate tokens without blocking the asyncio event loop.
*   **Performance**: Delivers "ChatGPT-like" typing effects even for local models running on CPU/MPS.

**Usage:**
```python
async for chunk in provider.stream("Explain inflation"):
    if "contentBlockDelta" in chunk:
        print(chunk["contentBlockDelta"]["delta"]["text"], end="", flush=True)
```
