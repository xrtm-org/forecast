import asyncio
import os
from typing import Any, Dict
from pydantic import SecretStr

# Import core library components
from forecast import (
    LLMAgent, 
    ModelFactory, 
    tool_registry, 
    BaseGraphState
)
from forecast.inference.config import GeminiConfig

# --- SIMULATION OF EXTERNAL SDK ---
# This part simulates how a third-party library like 'strand-agents' defines tools.
class ExternalStrandTool:
    """A simulated tool following the @strands.tool protocol."""
    def __init__(self):
        self.name = "get_market_sentiment"
        self.description = "Calculates current market sentiment for a ticker based on simulation."
        self.spec = {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock or crypto ticker."}
            },
            "required": ["ticker"]
        }
    
    async def fn(self, ticker: str) -> str:
        # Business logic from the external library
        return f"Sentiment for {ticker} is moderately bullish (+0.65)."

# --- INTEGRATION EXAMPLE ---

async def main():
    # 1. Initialize an external tool (e.g., from strand-agents)
    strand_tool = ExternalStrandTool()
    print(f"[App] Ingesting external tool: {strand_tool.name}")

    # 2. Register it with xrtm-forecast using the protocol adapter
    # In a real app, you'd just do: tool_registry.register_strand_tool(strand_tool)
    tool_registry.register_strand_tool(strand_tool)

    # 3. Setup our Agent to use this tool
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Abort] GEMINI_API_KEY not found. Please set it to run the real LLM handshake.")
        return

    config = GeminiConfig(
        model_id="gemini-2.0-flash-lite", 
        api_key=SecretStr(api_key)
    )
    model = ModelFactory.get_provider(config)

    # We create a generic analyst that knows it can use registry tools
    class ResearchAgent(LLMAgent):
        async def run(self, ticker: str):
            # Fetch tools by name from the registry
            tools = self.get_tools(["get_market_sentiment"])
            
            prompt = f"Using the available tools, analyze {ticker} and provide a summary."
            
            print(f"[Agent] Running research mission for {ticker}...")
            # The model will automatically detect the tool schema and call it
            response = await self.model.generate_content_async(prompt, tools=tools)
            return response.text

    # 4. Execute the reasoning mission
    agent = ResearchAgent(model=model, name="Researcher")
    result = await agent.run(ticker="ETH")
    
    print("\n" + "="*50)
    print("FINAL AGENT REPORT (Using External Strand Tool):")
    print(result)
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
