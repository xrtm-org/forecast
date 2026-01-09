from datetime import datetime

from forecast.inference.config import OpenAIConfig
from forecast.inference.openai_provider import OpenAIProvider
from forecast.schemas.graph import BaseGraphState, TemporalContext


def test_temporal_context_validation():
    ref_time = datetime(2024, 6, 15, 12, 0)
    ctx = TemporalContext(reference_time=ref_time, is_backtest=True)
    assert ctx.reference_time == ref_time
    assert ctx.is_backtest is True
    assert ctx.strict_mode is True


def test_graph_state_temporal_integration():
    ref_time = datetime(2024, 6, 15, 12, 0)
    ctx = TemporalContext(reference_time=ref_time, is_backtest=True)
    state = BaseGraphState(subject_id="test", temporal_context=ctx)
    assert state.temporal_context.reference_time == ref_time


def test_provider_knowledge_cutoff_metadata():
    cutoff = datetime(2023, 11, 1)
    config = OpenAIConfig(model_id="gpt-4", api_key="fake", knowledge_cutoff=cutoff)
    provider = OpenAIProvider(config)
    assert provider.knowledge_cutoff == cutoff


def test_provider_default_cutoff():
    config = OpenAIConfig(model_id="gpt-4", api_key="fake")
    provider = OpenAIProvider(config)
    assert provider.knowledge_cutoff is None
