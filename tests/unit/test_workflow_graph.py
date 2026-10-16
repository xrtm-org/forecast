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

r"""Tests for the workflow-blueprint compiler (compile, execute, hardening)."""

import asyncio

import pytest

from xrtm.forecast.core.schemas.workflow import (
    GraphSpec,
    NodeSpec,
    QuestionSourceSpec,
    RuntimeProfileSpec,
    WorkflowBlueprint,
)
from xrtm.forecast.graph.workflow_graph import (
    WorkflowGraphState,
    _runtime_provider,
    compile_workflow_blueprint,
)


def _blueprint(node: NodeSpec) -> WorkflowBlueprint:
    return WorkflowBlueprint(
        name="test-workflow",
        title="Test workflow",
        description="Compiler test blueprint.",
        workflow_kind="demo",
        questions=QuestionSourceSpec(),
        runtime=RuntimeProfileSpec(),
        graph=GraphSpec(entry="n1", nodes={"n1": node}),
    )


def test_compile_and_run_single_node():
    async def node(state):
        return {"ok": True}

    compiled = compile_workflow_blueprint(_blueprint(NodeSpec(kind="tool")), node_callables={"n1": node})
    state = WorkflowGraphState(subject_id="s1")

    asyncio.run(compiled.orchestrator.run(state))

    assert state.node_reports["n1"] == {"ok": True}


def test_node_row_tolerates_mapping_options():
    async def node(state):
        return {"ok": True}

    compiled = compile_workflow_blueprint(_blueprint(NodeSpec(kind="tool")), node_callables={"n1": node})
    state = WorkflowGraphState(subject_id="s1")
    state.context["options"] = {"provider": "openai"}  # plain dict used to raise AttributeError

    asyncio.run(compiled.orchestrator.run(state))

    rows = state.context.get("graph_trace_rows", [])
    assert rows and rows[0]["runtime"] == "openai"


def test_disallowed_dotted_implementation_is_rejected():
    blueprint = _blueprint(NodeSpec(kind="tool", implementation="os.system"))
    with pytest.raises(ValueError, match="not allowed"):
        compile_workflow_blueprint(blueprint, node_callables={})


def test_api_key_is_redacted_in_exports():
    spec = RuntimeProfileSpec(api_key="sk-secret-value")
    assert spec.to_json_dict()["api_key"] == "***"
    assert RuntimeProfileSpec().to_json_dict()["api_key"] is None


def test_runtime_provider_accepts_mappings_and_objects():
    assert _runtime_provider({"provider": "openai"}) == "openai"
    assert _runtime_provider(None) is None

    class _Options:
        provider = "deterministic"

    assert _runtime_provider(_Options()) == "deterministic"
