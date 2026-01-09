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

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def parse_json_markdown(text: str, default: Optional[Any] = None) -> Any:
    r"""
    Parser for extracting JSON data from Large Language Model (LLM) responses.

    LLMs often wrap JSON in markdown blocks (e.g., ```json ... ```) or surround it
    with conversational preamble. This utility robustly identifies and parses
    the JSON content, whether it is a dictionary or an array.

    Args:
        text (`str`):
            The raw text string from the LLM.
        default (`Any`, *optional*):
            The value to return if no valid JSON can be extracted.

    Returns:
        `Any`: The parsed dictionary or list, or the `default` value if parsing fails.

    Example:
        ```python
        >>> output = "Here is the result: ```json\n{'confidence': 0.8}\n```"
        >>> data = parse_json_markdown(output)
        >>> print(data['confidence'])
        0.8
        ```
    """
    try:
        # 1. Try to find content inside markdown fences
        pattern = r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```"
        json_match = re.search(pattern, text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 2. Fallback: Search for outermost balanced brackets/braces
        first_idx = -1
        last_idx = -1
        for i, char in enumerate(text):
            if char in "{[":
                first_idx = i
                break

        if first_idx != -1:
            opening_char = text[first_idx]
            closing_char = "}" if opening_char == "{" else "]"

            for i in range(len(text) - 1, first_idx, -1):
                if text[i] == closing_char:
                    last_idx = i + 1
                    break

        if first_idx != -1 and last_idx != -1:
            candidate = text[first_idx:last_idx]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # 3. Last resort: Try loading the raw text as a string
        return json.loads(text)
    except Exception as e:
        logger.warning(f"JSON Parsing Error: {e}")
        return default


__all__ = ["parse_json_markdown"]
