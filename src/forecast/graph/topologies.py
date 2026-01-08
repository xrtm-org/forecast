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
from typing import Optional

from forecast.agents import Agent, GraphAgent, LLMAgent
from forecast.graph.orchestrator import Orchestrator
from forecast.schemas.graph import BaseGraphState

logger = logging.getLogger(__name__)


def _agent_node_wrapper(agent: Agent):
    r"""Adapter to turn an Agent into a Graph Node callable."""

    async def node_func(state: BaseGraphState, report_progress=None) -> Optional[str]:
        # Extract input from context or previous steps
        # For simplicity, we pass the raw context "input" or the full history.
        # In a real debate, we'd pass the conversation history.

        user_input = state.context.get("input", "")
        # Call the agent
        # We might want to pass different args based on the topology
        result = await agent.run(user_input)

        # Store result in state
        # 1. Deterministic output key for parallel aggregation
        state.context[f"result_{agent.name}"] = str(result)

        # 2. Append to shared history (Thread-safe due to GIL for list.append,
        # but order is non-deterministic in parallel groups)
        history = state.context.setdefault("history", [])
        history.append({"agent": agent.name, "content": str(result)})

        # Determine next step?
        # For declarative topologies, we return None to let the Orchestrator decide based on edges.
        return None

    return node_func


def create_debate_graph(
    pro_agent: LLMAgent, con_agent: LLMAgent, judge_agent: LLMAgent, max_rounds: int = 3, name: str = "DebateGraph"
) -> GraphAgent:
    r"""
    Creates a pre-wired `GraphAgent` that executes a debate between two agents.
    ...
    """

    # 1. Define the Graph State (Atomic)
    # We use the standard BaseGraphState.

    # 2. Instantiate Orchestrator
    orchestrator = Orchestrator.create_standard(max_cycles=max_rounds * 3 + 2)

    # 3. Add Nodes (Wrapped)
    orchestrator.add_node(pro_agent.name, _agent_node_wrapper(pro_agent))
    orchestrator.add_node(con_agent.name, _agent_node_wrapper(con_agent))
    orchestrator.add_node(judge_agent.name, _agent_node_wrapper(judge_agent))

    # 4. Define Logic
    # Since we lack conditional edges (Phase 2 Roadmap), we unroll the debate rounds into a linear chain.
    # Pattern: Pro -> Con -> Judge -> Pro -> Con -> Judge ...

    # We cheat slightly by using the orchestrator's implicit state machine property.
    # The nodes are stateless in registration; we can register them, but wiring a loop
    # strictly via "name->name" edges implies an infinite loop unless the node breaks it.

    # Strategy: A "Round Robin" wiring.
    orchestrator.set_entry_point(pro_agent.name)
    orchestrator.add_edge(pro_agent.name, con_agent.name)
    orchestrator.add_edge(con_agent.name, judge_agent.name)
    orchestrator.add_edge(judge_agent.name, pro_agent.name)  # Loop back

    # Logic: The Orchestrator's `max_cycles` will naturally terminate this infinite loop.
    # This is a valid "Practical Shell" way to implement a fixed-duration debate.

    return GraphAgent(name=name, orchestrator=orchestrator)


def create_fanout_graph(workers: list[Agent], aggregator: Agent, name: str = "FanOutGraph") -> GraphAgent:
    r"""
    Creates a `GraphAgent` that parallels tasks across workers and aggregates results.

    **Topology**:
    Start -> [Worker1, Worker2, ...] --(Wait All)--> Aggregator -> End

    Args:
        workers (`list[Agent]`): List of worker agents to run in parallel.
        aggregator (`Agent`): Agent to synthesize worker outputs.
        name (`str`): Name of the graph.

    Returns:
        `GraphAgent`: Configured graph.
    """
    orchestrator = Orchestrator()

    # 1. Add ALL nodes (Workers + Aggregator)
    worker_names = []
    for w in workers:
        orchestrator.add_node(w.name, _agent_node_wrapper(w))
        worker_names.append(w.name)

    orchestrator.add_node(aggregator.name, _agent_node_wrapper(aggregator))

    # 2. Logic: Fan-Out via Parallel Group
    # Step 1: Execute all workers in parallel
    group_name = "parallel_workers"
    orchestrator.add_parallel_group(group_name, worker_names)

    # Wiring: Start -> Parallel Group -> Aggregator -> End
    orchestrator.set_entry_point(group_name)
    orchestrator.add_edge(group_name, aggregator.name)

    # Aggregator ends the flow (implicitly returns None or no edge out)

    return GraphAgent(name=name, orchestrator=orchestrator)
