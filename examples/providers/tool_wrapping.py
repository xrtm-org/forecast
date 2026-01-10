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

import asyncio

from forecast.core.tools.base import FunctionTool
from forecast.core.tools.registry import tool_registry


# 1. Define a standard Python function
def calculate_growth_rate(initial_value: float, final_value: float, periods: int) -> float:
    """
    Calculates the Compound Annual Growth Rate (CAGR).

    Args:
        initial_value: The starting value.
        final_value: The ending value.
        periods: Number of years/periods.
    """
    if initial_value <= 0 or periods <= 0:
        return 0.0
    return (final_value / initial_value) ** (1 / periods) - 1


async def main():
    print("--- Starting Tool Wrapping Demo ---")

    # 2. Wrap the function using FunctionTool
    # This automatically generates a JSON Schema from the docstring and signature.
    growth_tool = FunctionTool(
        fn=calculate_growth_rate,
        name="growth_calculator",  # Optional override
    )

    print(f"Tool Name: {growth_tool.name}")
    print(f"Tool Description: {growth_tool.description}")
    print(f"Tool Schema: {growth_tool.parameters_schema}")

    # 3. Register the tool in the global registry
    # This makes it discoverable by agents or other components.
    tool_registry.register(growth_tool)

    # 4. Execute the tool manually via the standard interface
    # Note that all tool runs are async.
    result = await growth_tool.run(initial_value=100.0, final_value=200.0, periods=5)

    print(f"\nExecution Result (100 -> 200 over 5 periods): {result:.2%}")

    # 5. Retrieve from registry
    retrieved_tool = tool_registry.get("growth_calculator")
    print(f"Retrieved '{retrieved_tool.name}' from registry successfully.")


if __name__ == "__main__":
    asyncio.run(main())
