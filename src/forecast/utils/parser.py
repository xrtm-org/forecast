import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def parse_json_markdown(text: str, default: Optional[Any] = None) -> Any:
    """
    Robustly parses JSON from LLM output, handling markdown blocks and preambles.
    Supports both JSON Objects {} and JSON Arrays [].
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
