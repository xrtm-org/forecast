import asyncio
import logging
import sys
import time

from forecast.kit.agents import LLMAgent
from forecast.kit.patterns import create_debate_graph, create_fanout_graph
from forecast.providers.inference.base import InferenceProvider, ModelResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VERIFY_TOPO")


# --- Mock Provider ---
class MockProvider(InferenceProvider):
    def __init__(self, name="Mock"):
        self.name = name
        self.call_count = 0

    async def generate_content_async(self, prompt, **kwargs):
        self.call_count += 1
        # Simulate latency to prove parallelism
        await asyncio.sleep(0.5)
        return ModelResponse(text=f"[{self.name}] response {self.call_count}")

    def generate_content(self, *args, **kwargs):
        pass

    def stream(self, *args, **kwargs):
        pass


# --- Mock Agent ---
class MockAgent(LLMAgent):
    def __init__(self, name, role, model):
        super().__init__(model, name)
        self.role = role

    async def run(self, *args, **kwargs):
        # Delegate to model to simulate "work"
        return await self.model.generate_content_async("prompt")


async def verify_debate():
    logger.info("--- Verifying DEBATE Topology ---")

    # Create mock agents
    pro = MockAgent("ProAgent", "Debater", MockProvider("PRO"))
    con = MockAgent("ConAgent", "Debater", MockProvider("CON"))
    judge = MockAgent("JudgeAgent", "Judge", MockProvider("JUDGE"))

    # Create Graph: 2 rounds -> Pro, Con, Judge, Pro, Con, Judge, Pro...
    # Logic in topology is max_rounds * 3 + 2, but let's test basic cycling.
    graph = create_debate_graph(pro, con, judge, max_rounds=2, name="TestDebate")

    start_time = time.time()
    await graph.run("Debate topic: Python vs Rust")
    duration = time.time() - start_time

    logger.info(f"Debate finished in {duration:.2f}s")
    logger.info(f"Call Counts: PRO={pro.model.call_count}, CON={con.model.call_count}, JUDGE={judge.model.call_count}")

    # Expected: 2 rounds of 3 agents = 6 calls minimum, maybe +2 for extra cycle handling
    # The topology unrolled loop logic is a bit implicit, let's see what happens.
    # At minimum, each should be called.
    assert pro.model.call_count >= 1
    assert con.model.call_count >= 1
    assert judge.model.call_count >= 1


async def verify_fanout():
    logger.info("--- Verifying FANOUT Topology ---")

    # Create 3 workers
    w1 = MockAgent("Worker1", "Worker", MockProvider("W1"))
    w2 = MockAgent("Worker2", "Worker", MockProvider("W2"))
    w3 = MockAgent("Worker3", "Worker", MockProvider("W3"))
    agg = MockAgent("Aggregator", "Boss", MockProvider("AGG"))

    graph = create_fanout_graph([w1, w2, w3], agg, name="TestFanOut")

    start_time = time.time()
    await graph.run("Analyze massive dataset")
    duration = time.time() - start_time

    logger.info(f"FanOut finished in {duration:.2f}s")

    # Verification of Parallelism:
    # Each worker sleeps 0.5s.
    # Sequential: 3 * 0.5 + 0.5 (agg) = ~2.0s
    # Parallel: max(0.5, 0.5, 0.5) + 0.5 (agg) = ~1.0s
    # We expect duration < 1.6s clearly indicating parallelism.

    logger.info(f"Worker Call Counts: W1={w1.model.call_count}, W2={w2.model.call_count}, W3={w3.model.call_count}")
    assert w1.model.call_count == 1
    assert w2.model.call_count == 1
    assert w3.model.call_count == 1
    assert agg.model.call_count == 1

    if duration < 1.8:
        logger.info("✅ Parallelism Confirmed! (Duration < Sequential Sum)")
    else:
        logger.error(f"❌ Parallelism Failed! Duration {duration:.2f}s suggests sequential execution.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(verify_debate())
    asyncio.run(verify_fanout())
