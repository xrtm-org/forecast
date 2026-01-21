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

import re
from typing import Any, Dict, List, Pattern, Tuple

__all__ = ["Anonymizer", "redactor"]


class Anonymizer:
    r"""
    A utility for scrubbing sensitive information from datasets and traces.

    Ensures that PII (Personally Identifiable Information) and other sensitive
    data are redacted before logging or auditing.

    Supported patterns:
        - Email addresses
        - Phone numbers (US format)
        - API keys (OpenAI, AWS patterns)
        - Credit card numbers
        - Social Security Numbers

    Example:
        ```python
        >>> from forecast.core.utils.privacy import redactor
        >>> data = {"user": "john@example.com", "notes": "Call 555-123-4567"}
        >>> clean = redactor.scrub_dict(data)
        >>> print(clean)
        {'user': '[EMAIL_REDACTED]', 'notes': 'Call [PHONE_REDACTED]'}
        ```
    """

    # PII patterns with their replacement tokens
    PII_PATTERNS: List[Tuple[Pattern[str], str]] = [
        # Email addresses
        (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[EMAIL_REDACTED]"),
        # US Phone numbers (various formats)
        (re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE_REDACTED]"),
        # API keys (OpenAI sk-xxx, AWS AKIA-xxx)
        (re.compile(r"\b(sk-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16})\b"), "[API_KEY_REDACTED]"),
        # Credit card numbers (with optional separators)
        (re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"), "[CARD_REDACTED]"),
        # Social Security Numbers
        (re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"), "[SSN_REDACTED]"),
    ]

    def scrub_string(self, text: str) -> str:
        r"""
        Scrubs PII patterns from a string.

        Args:
            text (`str`): The input text to scrub.

        Returns:
            `str`: The text with PII replaced by redaction tokens.
        """
        result = text
        for pattern, replacement in self.PII_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def scrub_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        r"""
        Recursively scrubs PII from a dictionary.

        Args:
            data (`Dict[str, Any]`): The input dictionary to scrub.

        Returns:
            `Dict[str, Any]`: A new dictionary with PII redacted.
        """
        return self._scrub_value(data)  # type: ignore[return-value]

    def _scrub_value(self, value: Any) -> Any:
        r"""Recursively processes values of any type."""
        if isinstance(value, str):
            return self.scrub_string(value)
        elif isinstance(value, dict):
            return {k: self._scrub_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._scrub_value(item) for item in value]
        elif isinstance(value, tuple):
            return tuple(self._scrub_value(item) for item in value)
        else:
            # For non-string primitives (int, float, bool, None), return as-is
            return value


redactor = Anonymizer()
