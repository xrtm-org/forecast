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


import pytest

from forecast.tools.base import StrandToolWrapper


class MockStrandTool:
    """Simulates a tool from the strands-agents SDK."""

    def __init__(self):
        self.name = "get_weather"
        self.description = "Returns the weather for a city."
        self.spec = {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}

    async def fn(self, city: str) -> str:
        return f"The weather in {city} is sunny."


@pytest.mark.asyncio
async def test_strand_tool_wrapper_execution():
    """
    Verifies that StrandToolWrapper correctly maps the Strand SDK protocol
    to our internal tool protocol.
    """
    # 1. Create a tool using the 'external' protocol
    external_tool = MockStrandTool()

    # 2. Wrap it with our adapter
    adapter = StrandToolWrapper(external_tool)

    # 3. Verify metadata mapping
    assert adapter.name == "get_weather"
    assert adapter.description == "Returns the weather for a city."
    assert adapter.parameters_schema == external_tool.spec

    # 4. Verify execution mapping
    result = await adapter.run(city="London")
    assert result == "The weather in London is sunny."


def test_strand_tool_metadata_variants():
    """Checks that the wrapper handles different Strand spec formats."""

    class VariantTool:
        def __init__(self):
            self.name = "test"
            self.parameters = {"type": "object", "properties": {}}

        def fn(self):
            return "ok"

    adapter = StrandToolWrapper(VariantTool())
    assert adapter.parameters_schema == {"type": "object", "properties": {}}
