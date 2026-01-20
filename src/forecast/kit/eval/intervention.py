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

r"""
Intervention Engine for performining "What-If" analysis on causal reasoning chains.
"""

import logging

import networkx as nx

from forecast.core.schemas.forecast import ForecastOutput

logger = logging.getLogger(__name__)

__all__ = ["InterventionEngine"]


class InterventionEngine:
    r"""
    A kit component for performing causal interventions (do-calculus) on forecast outputs.
    Allows users to simulate the impact of changing an assumption on the final confidence.
    """

    @staticmethod
    def apply_intervention(
        output: ForecastOutput,
        node_id: str,
        new_probability: float
    ) -> ForecastOutput:
        r"""
        Simulates the impact of an intervention on a specific reasoning node.
        Propagates the change through the causal graph using linear weighting.

        Args:
            output (`ForecastOutput`):
                The original forecast output containing the causal graph.
            node_id (`str`):
                The ID of the node to intervene on.
            new_probability (`float`):
                The new probability assigned to the node (0.0 to 1.0).

        Returns:
            `ForecastOutput`: A NEW forecast output object with updated probabilities.

        Raises:
            `ValueError`: If the node_id is not found in the output.
        """
        # 1. Clone the output (deep copy of logical trace)
        new_output = output.model_copy(deep=True)

        # 2. Build the working graph
        dg = new_output.to_networkx()

        if node_id not in dg:
            raise ValueError(f"Node ID '{node_id}' not found in the causal graph.")

        # 3. Apply the intervention (the "do" operation)
        # We manually update the node's probability
        for node in new_output.logical_trace:
            if node.node_id == node_id:
                node.probability = new_probability
                break
        else:
             raise ValueError(f"Node ID '{node_id}' not found in logical_trace.")

        # 4. Propagate the change downstream
        # We use a simple linear propagation strategy:
        # new_value = old_value + (delta * edge_weight)

        # Get nodes in topological order to ensure we propagate correctly
        nodes_ordered = list(nx.topological_sort(dg))
        start_index = nodes_ordered.index(node_id)

        # We only care about nodes downstream of the intervention
        for current_id in nodes_ordered[start_index:]:
            # Get current prob from the NEW output
            current_node = next(n for n in new_output.logical_trace if n.node_id == current_id)

            # Find all outgoing edges from this node
            for _, target_id, data in dg.out_edges(current_id, data=True):
                weight = data.get("weight", 1.0)

                # Update target node prob
                target_node = next(n for n in new_output.logical_trace if n.node_id == target_id)
                old_target_prob = target_node.probability or 0.5

                # Simple linear accumulation (clamped 0-1)
                # In a real Bayesian network, this would be more complex math
                normalized_delta = (current_node.probability - (dg.nodes[current_id].get("probability") or 0.5)) * weight
                target_node.probability = max(0.0, min(1.0, old_target_prob + normalized_delta))

        # 5. Update final confidence if the graph has a sink node that represents the outcome
        # For now, we assume the average of leaf nodes or specific logic.
        # In this prototype, we'll just update the output confidence based on the last node's change
        # if the last node is affected.

        leaf_nodes = [n for n in dg.nodes() if dg.out_degree(n) == 0]
        if leaf_nodes:
            avg_leaf_prob = sum(
                next(n.probability for n in new_output.logical_trace if n.node_id == leaf_id) or 0.0
                for leaf_id in leaf_nodes
            ) / len(leaf_nodes)
            new_output.confidence = avg_leaf_prob

        return new_output
