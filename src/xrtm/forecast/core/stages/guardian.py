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
from datetime import datetime, timezone
from typing import Callable, List, Optional

from xrtm.forecast.core.interfaces import InferenceProvider
from xrtm.forecast.core.schemas.graph import BaseGraphState

__all__ = ["LeakageGuardian"]


logger = logging.getLogger(__name__)


class LeakageGuardian:
    r"""
    A specialized Stage for detecting and redacting future-information leakage.

    The Guardian scans tool outputs (stored in `node_reports`) for dates and facts
    that post-date the `reference_time`. It uses a fast LLM for semantic verification
    and redaction.
    r"""

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

        Args:
            state (`BaseGraphState`): The state containing node reports to scan.
            report_progress (`Callable`): A callback for telemetry updates.

        Returns:
            `Optional[str]`: Always returns `None`, as it modifies the state in-place.

        Example:
            ```python
            guardian = LeakageGuardian(provider)
            await guardian(state, report_progress)
            ```
        r"""
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
            if self._regex_pre_filter(text_to_scan, ref_time):
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

    def _regex_pre_filter(self, text: str, reference_time: datetime) -> bool:
        r"""
        Quick check to avoid LLM calls for obviously clean text.

        Args:
            text (`str`): The content to scan for date patterns.
            reference_time (`datetime`): Anything after this moment is a potential leak.

        Returns:
            `bool`: `True` if high-risk temporal patterns are found.
        """
        # Exact ISO dates catch same-year future dates ("2026-12-31" seen from
        # March), which the year-only heuristic below would miss. A naive
        # reference_time (accepted by TemporalContext) is treated as UTC.
        reference = reference_time if reference_time.tzinfo is not None else reference_time.replace(tzinfo=timezone.utc)
        for match in re.finditer(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text):
            try:
                moment = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), tzinfo=timezone.utc)
            except ValueError:
                continue
            if moment > reference:
                return True
        for year_str in re.findall(r"\b20\d{2}\b", text):
            if int(year_str) > reference.year:
                return True
        return False

    async def _semantic_redaction(self, text: str, ref_date: str) -> str:
        r"""
        Uses the provider to redact sentences referring to events after ref_date.

        Args:
            text (`str`): The leaking content.
            ref_date (`str`): The ISO format reference date string.

        Returns:
            `str`: The redacted (safe) text.
        """
        prompt = f"""
SYSTEM: You are the Leakage Guardian. Your job is to prevent "Look-Ahead Bias" in historical backtests.
TASK: Redact any information in the following text that mentions events, data, or results occurring AFTER {ref_date}.
RULE: Replace leaking sentences with "{self.redaction_template}". If the whole text is a leak, return just the template.
RULE: Keep all information occurring on or before {ref_date} untouched.
TEXT:
{text}
REDACTED TEXT:
r"""
        response = await self.provider.generate_content_async(prompt)
        return response.text.strip()
