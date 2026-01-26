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

from xrtm.forecast.kit.eval.intervention import InterventionEngine

from xrtm.forecast.core.schemas.forecast import CausalEdge, CausalNode, ForecastOutput


async def run_causal_demo():
    r"""Demonstrates Causal DAG representation and 'What-If' interventions."""
    print("--- [CAUSAL INTERPRETABILITY DEMO] ---")

    # 1. Define a Causal reasoning chain
    # Scenario: Impact of a new AI regulation on company growth
    nodes = [
        CausalNode(node_id="reg", event="Strict AI Regulation Passed", probability=0.7, description="Legal hurdle"),
        CausalNode(node_id="cost", event="Compliance Costs Increase", probability=0.6, description="Financial impact"),
        CausalNode(node_id="r_d", event="R&D Slowdown", probability=0.5, description="Operational impact"),
        CausalNode(node_id="growth", event="Company Growth Stagnates", probability=0.4, description="Final outcome"),
    ]

    edges = [
        CausalEdge(source="reg", target="cost", weight=0.8, description="Regulations drive costs"),
        CausalEdge(source="cost", target="r_d", weight=0.6, description="High costs drain R&D budget"),
        CausalEdge(source="r_d", target="growth", weight=0.9, description="Reduced R&D kills growth"),
    ]

    output = ForecastOutput(
        question_id="demo-causal",
        confidence=0.4,
        reasoning="Standard projection based on current regulatory trends.",
        logical_trace=nodes,
        logical_edges=edges,
    )

    print("\nInitial State:")
    print(f"  Regulation Prob: {nodes[0].probability}")
    print(f"  Final Confidence: {output.confidence}")

    # 2. Performance an Intervention (The "What-If")
    # What if the regulation DOES NOT pass? (Prob -> 0.1)
    print("\n[INTERVENTION] What if 'Strict AI Regulation' probability drops to 0.1?")

    engine = InterventionEngine()
    new_output = engine.apply_intervention(output, node_id="reg", new_probability=0.1)

    print("\nUpdated State:")
    # Find the reg node in new output
    reg_new = next(n for n in new_output.logical_trace if n.node_id == "reg")
    cost_new = next(n for n in new_output.logical_trace if n.node_id == "cost")
    print(f"  Regulation Prob: {reg_new.probability:.2f}")
    print(f"  Compliance Cost Prob: {cost_new.probability:.2f} (Cascaded)")
    print(f"  Final Confidence: {new_output.confidence:.2f}")

    print("\nAudit Trail:")
    print("  The intervention successfully propagated the lower probability ")
    print("  through the DAG, significantly improving the growth outlook.")


if __name__ == "__main__":
    asyncio.run(run_causal_demo())
