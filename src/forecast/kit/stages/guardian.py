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

import logging
import re
from typing import Callable, List, Optional

from forecast.core.schemas.graph import BaseGraphState
from forecast.providers.inference.base import InferenceProvider

logger = logging.getLogger(__name__)


class LeakageGuardian:
    r"""
    A specialized Stage for detecting and redacting future-information leakage.

    The Guardian scans tool outputs (stored in `node_reports`) for dates and facts
    that post-date the `reference_time`. It uses a fast LLM for semantic verification
    and redaction.
    """

    def __init__(
        self,
        provider: InferenceProvider,
        target_nodes: Optional[List[str]] = None,
        redaction_template: str = "[REDACTED_FUTURE_LEAK]",
    ):
        self.provider = provider
        self.target_nodes = target_nodes  # Nodes to scan. If None, scans all.
        self.redaction_template = redaction_template

    async def __call__(self, state: BaseGraphState, report_progress: Callable) -> Optional[str]:
        r"""
        Executes the redaction logic on the current state.
        """
        if not state.temporal_context or not state.temporal_context.is_backtest:
            return None

        ref_time = state.temporal_context.reference_time
        ref_date_str = ref_time.strftime("%Y-%m-%d")

        await report_progress(0.7, "Guardian", "SCANNING", f"Checking for leaks post-{ref_date_str}")

        # Collect content to scan
        nodes_to_scan = self.target_nodes or list(state.node_reports.keys())
        leakage_found = False

        for node_name in nodes_to_scan:
            content = state.node_reports.get(node_name)
            if not content:
                continue

            # Convert to string for scanning if it's a dict/list
            text_to_scan = str(content)

            # 1. Fast Regex Check (Pre-filter)
            # Look for any year >= ref_year + 1 or dates in general
            if self._regex_pre_filter(text_to_scan, ref_time.year):
                # 2. Semantic LLM Check
                redacted_content = await self._semantic_redaction(text_to_scan, ref_date_str)
                if redacted_content != text_to_scan:
                    state.node_reports[node_name] = redacted_content
                    leakage_found = True
                    logger.warning(f"[GUARDIAN] Redacted future leakage in node: {node_name}")

        if leakage_found:
            await report_progress(0.75, "Guardian", "REDACTED", "Potential future leakage was found and suppressed.")
        else:
            await report_progress(0.75, "Guardian", "CLEAN", "No significant temporal leakage detected.")

        return None

    def _regex_pre_filter(self, text: str, ref_year: int) -> bool:
        r"""Quick check to avoid LLM calls for obviously clean text."""
        # Check for any year > ref_year (simplistic)
        # In a real tool, we'd look for more patterns.
        years = re.findall(r"\b20\d{2}\b", text)
        for year_str in years:
            if int(year_str) > ref_year:
                return True
        return False

    async def _semantic_redaction(self, text: str, ref_date: str) -> str:
        r"""Uses the provider to redact sentences referring to events after ref_date."""
        prompt = f"""
SYSTEM: You are the Leakage Guardian. Your job is to prevent "Look-Ahead Bias" in historical backtests.
TASK: Redact any information in the following text that mentions events, data, or results occurring AFTER {ref_date}.
RULE: Replace leaking sentences with "{self.redaction_template}". If the whole text is a leak, return just the template.
RULE: Keep all information occurring on or before {ref_date} untouched.
TEXT:
{text}
REDACTED TEXT:
"""
        response = await self.provider.generate_content_async(prompt)
        return response.text.strip()
