from pydantic import SecretStr

import xrtm.forecast.providers.inference.openai_provider as openai_provider_module
from xrtm.forecast.core.config.inference import OpenAIConfig


def test_openai_provider_uses_config_timeout(monkeypatch) -> None:
    calls: list[dict] = []

    class FakeClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(openai_provider_module, "AsyncOpenAI", FakeClient)
    monkeypatch.setattr(openai_provider_module, "OpenAI", FakeClient)

    openai_provider_module.OpenAIProvider(
        OpenAIConfig(
            model_id="demo-model",
            api_key=SecretStr("test-key"),
            base_url="http://localhost:8080/v1",
            timeout=123,
        )
    )

    assert calls == [
        {"api_key": "test-key", "base_url": "http://localhost:8080/v1", "timeout": 123},
        {"api_key": "test-key", "base_url": "http://localhost:8080/v1", "timeout": 123},
    ]
