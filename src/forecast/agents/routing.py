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
from typing import Any, Dict, Optional, Union

from forecast.agents.base import Agent
from forecast.inference.base import InferenceProvider
from forecast.inference.factory import ModelFactory

logger = logging.getLogger(__name__)


class RoutingAgent(Agent):
    r"""
    A composite agent that routes tasks to different specialized models or agents.

    Tiered Reasoning:
    - Highly efficient for cost management and throughput optimization.
    - Uses a cheap/fast 'router' model to classify the complexity of a task.
    - Dispatches to a 'fast' tier (local or small cloud models) for simple extraction/classification.
    - Dispatches to a 'smart' tier (frontier cloud models) for complex synthesis/logic.

    Args:
        router_model (`InferenceProvider`, *optional*):
            The model used for routing decisions.
        fast_tier (`Union[Agent, InferenceProvider]`, *optional*):
            The agent or provider for low-complexity tasks.
        smart_tier (`Union[Agent, InferenceProvider]`, *optional*):
            The agent or provider for high-complexity tasks.
        routes (`Dict[str, Union[Agent, InferenceProvider]]`, *optional*):
            A custom map of route names to agents/providers.
        name (`str`, *optional*):
            Logical name of the router.
    """

    def __init__(
        self,
        router_model: Optional[InferenceProvider] = None,
        fast_tier: Optional[Union[Agent, InferenceProvider]] = None,
        smart_tier: Optional[Union[Agent, InferenceProvider]] = None,
        routes: Optional[Dict[str, Union[Agent, InferenceProvider]]] = None,
        name: str = "Router",
    ):
        super().__init__(name=name)
        self.router_model = router_model or ModelFactory.get_provider("gemini:gemini-2.0-flash")
        self.fast_tier = fast_tier
        self.smart_tier = smart_tier
        self.routes = routes or {}

        if fast_tier:
            self.routes["fast"] = fast_tier
        if smart_tier:
            self.routes["smart"] = smart_tier

    async def run(self, input_data: Any, **kwargs: Any) -> Any:
        r"""
        Decides which route to take and executes the task.

        This method first classifies the input task as 'FAST' or 'SMART' using the
        internal router model, and then dispatches it to the corresponding tier.

        Args:
            input_data (`Any`):
                The primary task input (e.g. prompt, question, or payload).
            **kwargs:
                Additional parameters passed to the target agent/tier.

        Returns:
            `Any`: The result from the routed agent or inference provider.

        Example:
            ```python
            >>> router = RoutingAgent(fast_tier=hf_provider, smart_tier=gemini_provider)
            >>> result = await router.run("Summarize this text.")
            ```
        """
        # 1. Classification Step
        complexity_prompt = f"""
        Classify the following task complexity as 'FAST' or 'SMART'.
        'FAST': Simple data extraction, formatting, or basic classification.
        'SMART': Complex reasoning, multi-step logic, or nuanced synthesis.

        Task: {str(input_data)[:800]}

        Response: [FAST/SMART]
        """

        try:
            decision_resp = await self.router_model.run(complexity_prompt)
            decision = decision_resp.text.upper().strip()
        except Exception as e:
            logger.error(f"Routing decision failed: {e}. Falling back to SMART.")
            decision = "SMART"

        target_route = "smart" if "SMART" in decision else "fast"

        # Fallback if route not defined
        if target_route not in self.routes:
            logger.warning(f"Route '{target_route}' not defined in {self.name}. Falling back to available routes.")
            if not self.routes:
                raise ValueError(f"RoutingAgent '{self.name}' has no defined routes.")
            target_route = list(self.routes.keys())[0]

        target = self.routes[target_route]
        logger.info(f"RoutingAgent '{self.name}' [Decision: {decision}] -> Routing to: {target_route}")

        if isinstance(target, Agent):
            return await target.run(input_data, **kwargs)
        elif hasattr(target, "run") and callable(getattr(target, "run")):
            # Handles InferenceProviders or other objects with a .run() method
            if hasattr(target, "generate_content_async"):
                return await target.run(str(input_data), **kwargs)
            else:
                return await target.run(input_data, **kwargs)

        raise TypeError(f"Target '{target_route}' is not a runnable Agent or Provider: {type(target)}")


__all__ = ["RoutingAgent"]
