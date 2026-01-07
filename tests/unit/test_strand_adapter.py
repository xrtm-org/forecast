
import pytest

from forecast.tools.base import StrandToolWrapper


class MockStrandTool:
    """Simulates a tool from the strands-agents SDK."""
    def __init__(self):
        self.name = "get_weather"
        self.description = "Returns the weather for a city."
        self.spec = {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }

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
        def fn(self): return "ok"

    adapter = StrandToolWrapper(VariantTool())
    assert adapter.parameters_schema == {"type": "object", "properties": {}}
