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

r"""Internal policy helpers for inference provider resolution."""

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Optional

from pydantic import SecretStr

from xrtm.forecast.core.config.inference import (
    OpenAIConfig,
    ProviderConfig,
)
from xrtm.forecast.core.exceptions import ConfigurationError


@dataclass(frozen=True)
class ProviderSpec:
    r"""Describe one supported inference-provider family and its resolution defaults."""

    aliases: tuple[str, ...]
    config_type: type[ProviderConfig]
    default_model_id: str
    provider_module: str
    provider_name: str
    settings_api_key_field: Optional[str] = None
    accepts_provider_kwargs: bool = False


_PROVIDER_SPECS: dict[str, ProviderSpec] = {
    "OPENAI": ProviderSpec(
        aliases=("OPENAI", "OPENAI-COMPATIBLE"),
        config_type=OpenAIConfig,
        default_model_id="gpt-4o",
        provider_module="xrtm.forecast.providers.inference.openai_provider",
        provider_name="OpenAIProvider",
        settings_api_key_field="openai_api_key",
        accepts_provider_kwargs=True,
    ),
}

_PROVIDER_ALIASES = {
    alias: provider_type for provider_type, spec in _PROVIDER_SPECS.items() for alias in spec.aliases
}


def coerce_provider_request(
    config: Optional[Any],
    provider_type: Optional[str],
    model_id: Optional[str],
) -> tuple[Optional[Any], Optional[str], Optional[str]]:
    if isinstance(config, str) and isinstance(provider_type, ProviderConfig):
        return provider_type, config, model_id

    if isinstance(config, str):
        if ":" in config:
            provider_type, model_id = config.split(":", 1)
        else:
            provider_type = config
        config = None

    return config, provider_type, model_id


def normalize_provider_type(provider_type: Optional[str]) -> str:
    if not provider_type:
        raise ConfigurationError(
            "Explicitly provide either a `config` object or `provider_type` (or a shortcut string)."
        )

    canonical = _PROVIDER_ALIASES.get(provider_type.upper())
    if canonical is None:
        raise ConfigurationError(f"Unsupported provider type: {provider_type}")

    return canonical


def split_config_kwargs(
    config_type: type[ProviderConfig],
    kwargs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    config_fields = set(config_type.model_fields)
    config_kwargs = {key: value for key, value in kwargs.items() if key in config_fields}
    provider_kwargs = {key: value for key, value in kwargs.items() if key not in config_fields}
    return config_kwargs, provider_kwargs


def build_config(
    provider_type: str,
    model_id: Optional[str],
    api_key: Optional[SecretStr],
    kwargs: dict[str, Any],
) -> tuple[ProviderConfig, dict[str, Any]]:
    spec = _PROVIDER_SPECS[normalize_provider_type(provider_type)]
    config_kwargs, provider_kwargs = split_config_kwargs(spec.config_type, kwargs)
    config_kwargs.setdefault("model_id", model_id or spec.default_model_id)
    if api_key is not None:
        config_kwargs["api_key"] = api_key
    return spec.config_type(**config_kwargs), provider_kwargs


def update_config(
    config: ProviderConfig,
    model_id: Optional[str],
    api_key: Optional[SecretStr],
    kwargs: dict[str, Any],
) -> tuple[ProviderConfig, dict[str, Any]]:
    config_kwargs, provider_kwargs = split_config_kwargs(type(config), kwargs)
    if model_id is not None:
        config_kwargs["model_id"] = model_id
    if api_key is not None:
        config_kwargs["api_key"] = api_key
    if config_kwargs:
        config = config.model_copy(update=config_kwargs)
    return config, provider_kwargs


def apply_environment_profile(config: ProviderConfig, env_profile: Optional[str]) -> ProviderConfig:
    if env_profile == "production" and isinstance(config, OpenAIConfig):
        return config.model_copy(update={"model_id": "gpt-4o"})

    if env_profile == "dev":
        if isinstance(config, OpenAIConfig):
            return config.model_copy(update={"model_id": "gpt-4o-mini"})

    return config


def inject_api_key_from_settings(config: ProviderConfig, settings: Any) -> ProviderConfig:
    spec = get_provider_spec_for_config(config)
    if spec is None or spec.settings_api_key_field is None or config.api_key:
        return config

    api_key = getattr(settings, spec.settings_api_key_field, None)
    if api_key:
        return config.model_copy(update={"api_key": api_key})

    return config


def get_provider_spec_for_config(config: ProviderConfig) -> Optional[ProviderSpec]:
    for spec in _PROVIDER_SPECS.values():
        if isinstance(config, spec.config_type):
            return spec
    return None


def instantiate_provider(config: ProviderConfig, provider_kwargs: dict[str, Any]) -> Any:
    spec = get_provider_spec_for_config(config)
    if spec is None:
        raise ConfigurationError(f"Unsupported configuration type: {type(config)}")

    provider_cls = getattr(import_module(spec.provider_module), spec.provider_name)

    if spec.accepts_provider_kwargs:
        return provider_cls(config=config, **provider_kwargs)
    return provider_cls(config=config)


__all__ = [
    "apply_environment_profile",
    "build_config",
    "coerce_provider_request",
    "inject_api_key_from_settings",
    "instantiate_provider",
    "update_config",
]
