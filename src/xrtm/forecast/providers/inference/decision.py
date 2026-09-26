# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""Typed decision providers.

Two provider flavors share the :class:`DecisionProvider` contract:

- :class:`LLMDecisionProvider` asks any text-generation model for a JSON
  decision and normalizes it into a :class:`DecisionResult`.
- :class:`JevProvider` targets TypeSafe Jev (a System-One decision model)
  through an OpenAI-compatible gateway and unwraps its ``answers`` payload.

Example:
    >>> from xrtm.forecast.providers.inference.decision import LLMDecisionProvider
    >>> from xrtm.forecast.core.schemas.decision import DecisionOption
    >>> provider = LLMDecisionProvider(model=my_openai_provider)  # doctest: +SKIP
    >>> result = await provider.decide(  # doctest: +SKIP
    ...     "Should we trade this market?",
    ...     [DecisionOption(name="trade"), DecisionOption(name="skip")],
    ... )
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence

from pydantic import SecretStr

from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.core.exceptions import ConfigurationError, ProviderError
from xrtm.forecast.core.interfaces import DecisionProvider, InferenceProvider
from xrtm.forecast.core.schemas.decision import DecisionOption, DecisionResult
from xrtm.forecast.core.utils.parser import parse_json_markdown
from xrtm.forecast.core.utils.schemas import json_object_response_format
from xrtm.forecast.providers.inference.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

__all__ = ["LLMDecisionProvider", "JevProvider"]

_DECISION_SYSTEM_PROMPT = (
    "You are a decision engine. Choose exactly one option and reply with JSON only, matching: "
    '{"decision": "<option name>", "confidence": <0-1>, "probabilities": {"<option>": <0-1>}, '
    '"escalate": <true|false>, "rationale": "<short reason>"}'
)


class LLMDecisionProvider(DecisionProvider):
    r"""Decision provider backed by any text-generation :class:`InferenceProvider`.

    Args:
        model: The inference provider used to produce the decision.
        temperature: Sampling temperature (default 0.0 for deterministic decisions).
        max_tokens: Output budget for the decision response.
        system_prompt: Optional custom system prompt.
        structured_output: Request provider-enforced JSON output when supported.
    """

    def __init__(
        self,
        model: InferenceProvider,
        temperature: float = 0.0,
        max_tokens: int = 512,
        system_prompt: Optional[str] = None,
        structured_output: bool = True,
    ):
        if not isinstance(model, InferenceProvider):
            raise ConfigurationError("LLMDecisionProvider requires an InferenceProvider instance")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or _DECISION_SYSTEM_PROMPT
        self.structured_output = structured_output

    async def decide(
        self,
        state: str,
        options: Sequence[DecisionOption],
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> DecisionResult:
        r"""Return a :class:`DecisionResult` for *state* over *options*."""
        if not options:
            raise ConfigurationError("decide() requires at least one DecisionOption")

        option_lines = [f"- {option.name}: {option.description}" for option in options]
        context_block = ""
        if context:
            context_block = "\n\nContext:\n" + json.dumps(context, default=str, sort_keys=True)

        prompt = (
            f"{self.system_prompt}\n\n"
            f"State:\n{state}\n\n"
            f"Options:\n" + "\n".join(option_lines) + context_block
        )

        gen_kwargs: Dict[str, Any] = {"temperature": self.temperature, "max_tokens": self.max_tokens}
        if self.structured_output:
            gen_kwargs["response_format"] = json_object_response_format()

        response = await self.model.generate_content_async(prompt, **gen_kwargs)
        text = getattr(response, "text", "") or ""
        payload = parse_json_markdown(text)
        if not isinstance(payload, dict):
            raise ProviderError(f"Decision provider returned non-JSON output: {text[:200]!r}")

        payload = self._unwrap_payload(payload)
        usage = getattr(response, "usage", None) or {}
        return self._normalize(payload, [option.name for option in options], usage=usage)

    def _unwrap_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        r"""Hook for provider-specific payload shapes (overridden by :class:`JevProvider`)."""
        return payload

    @staticmethod
    def _normalize(payload: Dict[str, Any], names: List[str], usage: Optional[Dict[str, Any]] = None) -> DecisionResult:
        r"""Coerce a decision payload into a :class:`DecisionResult`."""
        raw_probs = payload.get("probabilities")
        probabilities: Dict[str, float] = {}
        if isinstance(raw_probs, dict):
            for name in names:
                try:
                    probabilities[name] = max(0.0, float(raw_probs.get(name, 0.0) or 0.0))
                except (TypeError, ValueError):
                    probabilities[name] = 0.0

        decision = str(payload.get("decision", "") or "").strip()
        if decision not in names:
            best = max(probabilities, key=lambda key: probabilities[key]) if probabilities else ""
            decision = best if best and probabilities.get(best, 0.0) > 0 else names[0]

        try:
            confidence = float(payload.get("confidence"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            confidence = probabilities.get(decision, 0.5)
        confidence = min(max(confidence, 0.0), 1.0)

        total = sum(probabilities.values())
        if total > 0:
            probabilities = {name: value / total for name, value in probabilities.items()}

        clean_usage: Dict[str, int] = {}
        for key, value in (usage or {}).items():
            if isinstance(value, (int, float)):
                clean_usage[str(key)] = int(value)

        return DecisionResult(
            decision=decision,
            confidence=confidence,
            probabilities=probabilities,
            escalate=bool(payload.get("escalate", False)),
            rationale=str(payload.get("rationale", "") or ""),
            usage=clean_usage,
        )


class JevProvider(LLMDecisionProvider):
    r"""Decision provider for TypeSafe Jev via an OpenAI-compatible gateway.

    Jev returns typed answers, e.g. ``{"answers": {"intent": {"type": "choice",
    "choice": "trade", "confidence": 1.0, "probabilities": {...}}}}``. This
    provider unwraps the first (or named) answer into the shared decision shape.

    Args:
        model_id: Gateway model identifier (default ``"jev"``).
        base_url: Gateway base URL (defaults to ``JEV_BASE_URL``).
        api_key: Gateway API key (defaults to ``JEV_API_KEY``).
        answer_key: Which entry of ``answers`` to use when there are several.
        provider: Pre-built inference provider (for tests/DI); bypasses gateway config.
    """

    def __init__(
        self,
        model_id: str = "jev",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        answer_key: Optional[str] = None,
        provider: Optional[InferenceProvider] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ):
        resolved_base = base_url or os.environ.get("JEV_BASE_URL", "")
        resolved_key = api_key or os.environ.get("JEV_API_KEY", "")
        if provider is None:
            if not resolved_base or not resolved_key:
                raise ConfigurationError(
                    "JevProvider requires base_url/api_key (or JEV_BASE_URL/JEV_API_KEY environment variables)"
                )
            config = OpenAIConfig(
                model_id=model_id,
                base_url=resolved_base,
                api_key=SecretStr(resolved_key),
                thinking="disabled",
                timeout=60,
            )
            provider = OpenAIProvider(config)
        self.answer_key = answer_key
        super().__init__(provider, temperature=temperature, max_tokens=max_tokens)

    def _unwrap_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        r"""Unwrap the Jev ``answers`` envelope into a flat decision payload."""
        answers = payload.get("answers")
        if not isinstance(answers, dict) or not answers:
            return payload

        key = self.answer_key
        if key is None:
            key = "decision" if "decision" in answers else next(iter(answers))
        entry = answers.get(key)
        if not isinstance(entry, dict):
            return payload

        flat = dict(payload)
        choice = entry.get("choice") or entry.get("decision")
        if choice is not None:
            flat.setdefault("decision", choice)
        if "confidence" in entry:
            flat.setdefault("confidence", entry["confidence"])
        if "probabilities" in entry:
            flat.setdefault("probabilities", entry["probabilities"])
        return flat
