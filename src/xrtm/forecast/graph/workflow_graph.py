"""Compile workflow blueprints into forecast orchestrator graphs."""

from __future__ import annotations

import inspect
import time
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable

from xrtm.forecast.core.config.graph import GraphConfig
from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.core.schemas.workflow import ConditionalRouteSpec, GraphSpec, NodeSpec, WorkflowBlueprint
from xrtm.forecast.kit.agents.base import Agent


class WorkflowGraphState(BaseGraphState):
    """Graph state used by XRTM product workflow execution."""


@dataclass(frozen=True)
class CompiledGraph:
    blueprint: WorkflowBlueprint
    orchestrator: Orchestrator[WorkflowGraphState]
    node_adapters: dict[str, "NodeAdapter"]

    @property
    def entry_node(self) -> str:
        return self.blueprint.graph.entry


class NodeAdapter:
    """Bridge one blueprint node into an executable runtime object."""

    def __init__(
        self,
        *,
        node_name: str,
        spec: NodeSpec,
        parent_nodes: tuple[str, ...],
        target: Any = None,
    ) -> None:
        self.node_name = node_name
        self.spec = spec
        self.parent_nodes = parent_nodes
        self.target = target

    async def run(self, state: WorkflowGraphState) -> Any:
        raise NotImplementedError

    def upstream_reports(self, state: WorkflowGraphState) -> dict[str, Any]:
        return {name: state.node_reports.get(name) for name in self.parent_nodes if name in state.node_reports}


class CallableNodeAdapter(NodeAdapter):
    async def run(self, state: WorkflowGraphState) -> Any:
        if self.target is None:
            raise ValueError(f"node {self.node_name} has no implementation")
        upstream = self.upstream_reports(state)
        input_data: Any
        if len(upstream) == 1:
            input_data = next(iter(upstream.values()))
        else:
            input_data = upstream
        kwargs = {
            "state": state,
            "config": self.spec.config,
            "node_name": self.node_name,
            "input_data": input_data,
            "upstream": upstream,
            "context": state.context,
        }
        return await _invoke_target(self.target, kwargs)


class AgentNodeAdapter(NodeAdapter):
    async def run(self, state: WorkflowGraphState) -> Any:
        agent = _resolve_agent(self.target, self.node_name)
        upstream = self.upstream_reports(state)
        input_data: Any
        if len(upstream) == 1:
            input_data = next(iter(upstream.values()))
        else:
            input_data = upstream
        kwargs = {
            "state": state,
            "config": self.spec.config,
            "node_name": self.node_name,
            "context": state.context,
            "upstream": upstream,
        }
        return await agent.run(input_data, **kwargs)


class HumanGateNodeAdapter(NodeAdapter):
    async def run(self, state: WorkflowGraphState) -> Any:
        prompt = str(self.spec.config.get("prompt", f"Approval required for {self.node_name}"))
        provider = state.context.get("human_provider")
        if provider is None:
            return {"prompt": prompt, "response": None, "status": "skipped"}
        response = provider.get_human_input(prompt)
        if inspect.isawaitable(response):
            response = await response
        return {"prompt": prompt, "response": response, "status": "completed"}


def compile_workflow_blueprint(
    blueprint: WorkflowBlueprint,
    *,
    node_callables: dict[str, Any] | None = None,
) -> CompiledGraph:
    orchestrator: Orchestrator[WorkflowGraphState] = Orchestrator(
        GraphConfig(
            max_cycles=max(len(blueprint.graph.nodes) + len(blueprint.graph.parallel_groups) + 2, 3),
            entry_node=blueprint.graph.entry,
        )
    )
    parents_by_node = _parents_by_node(blueprint.graph)
    node_adapters: dict[str, NodeAdapter] = {}

    for node_name, spec in blueprint.graph.nodes.items():
        adapter = _build_node_adapter(
            node_name=node_name,
            spec=spec,
            parent_nodes=parents_by_node.get(node_name, ()),
            node_callables=node_callables or {},
        )
        node_adapters[node_name] = adapter
        orchestrator.add_node(node_name, _orchestrator_node(adapter))

    for edge in blueprint.graph.edges:
        orchestrator.add_edge(edge.from_node, edge.to_node)
    for group_name, group in blueprint.graph.parallel_groups.items():
        orchestrator.add_parallel_group(group_name, list(group.nodes))
    for node_name, route_spec in blueprint.graph.conditional_routes.items():
        orchestrator.add_conditional_edge(node_name, _condition_resolver(node_name, route_spec), route_spec.routes)
    orchestrator.set_entry_point(blueprint.graph.entry)

    return CompiledGraph(blueprint=blueprint, orchestrator=orchestrator, node_adapters=node_adapters)


def graph_trace_rows(compiled: CompiledGraph, state: WorkflowGraphState) -> list[dict[str, Any]]:
    raw_rows = list(state.context.get("graph_trace_rows", []))
    sequence = 1
    rows: list[dict[str, Any]] = []
    seen_parallel_groups = set()
    for item in raw_rows:
        row = {
            "sequence": sequence,
            "workflow": compiled.blueprint.name,
            "subject_id": state.subject_id,
            **item,
        }
        rows.append(row)
        sequence += 1
    for step in state.execution_path:
        if not step.startswith("parallel:"):
            continue
        group_name = step.split("parallel:", 1)[1]
        if group_name in seen_parallel_groups:
            continue
        seen_parallel_groups.add(group_name)
        group = compiled.blueprint.graph.parallel_groups.get(group_name)
        rows.append(
            {
                "sequence": sequence,
                "workflow": compiled.blueprint.name,
                "subject_id": state.subject_id,
                "node": group_name,
                "kind": "parallel-group",
                "implementation": None,
                "runtime": compiled.blueprint.runtime.provider,
                "optional": False,
                "status": "completed",
                "members": list(group.nodes) if group else [],
                "latency_seconds": state.latencies.get(group_name),
            }
        )
        sequence += 1
    return rows


def _build_node_adapter(
    *,
    node_name: str,
    spec: NodeSpec,
    parent_nodes: tuple[str, ...],
    node_callables: dict[str, Any],
) -> NodeAdapter:
    target = _resolve_target(node_name=node_name, spec=spec, node_callables=node_callables)
    if spec.kind == "agent":
        return AgentNodeAdapter(node_name=node_name, spec=spec, parent_nodes=parent_nodes, target=target)
    if spec.kind == "human-gate":
        return HumanGateNodeAdapter(node_name=node_name, spec=spec, parent_nodes=parent_nodes, target=target)
    return CallableNodeAdapter(node_name=node_name, spec=spec, parent_nodes=parent_nodes, target=target)


def _parents_by_node(graph: GraphSpec) -> dict[str, tuple[str, ...]]:
    parents: dict[str, list[str]] = {name: [] for name in graph.nodes}
    for edge in graph.edges:
        if edge.to_node not in graph.nodes:
            continue
        sources = list(graph.parallel_groups.get(edge.from_node, None).nodes) if edge.from_node in graph.parallel_groups else [edge.from_node]
        parents.setdefault(edge.to_node, []).extend(source for source in sources if source in graph.nodes)
    return {name: tuple(values) for name, values in parents.items()}


def _condition_resolver(node_name: str, spec: ConditionalRouteSpec) -> Callable[[WorkflowGraphState], str]:
    def resolve(state: WorkflowGraphState) -> str:
        report = state.node_reports.get(node_name)
        if isinstance(report, str):
            return report
        if isinstance(report, dict):
            value = report.get(spec.route_field)
            if isinstance(value, str) and value:
                return value
        context_value = state.context.get(spec.route_field)
        if isinstance(context_value, str) and context_value:
            return context_value
        raise ValueError(f"node {node_name} did not produce route field {spec.route_field!r}")

    return resolve


def _orchestrator_node(adapter: NodeAdapter) -> Callable[[WorkflowGraphState, Any], Any]:
    async def runner(state: WorkflowGraphState, report_progress: Any) -> Any:
        start = time.perf_counter()
        await report_progress(float(state.cycle_count + 1), adapter.node_name, "RUN", f"Running {adapter.spec.kind} node")
        trace_rows = state.context.setdefault("graph_trace_rows", [])
        row: dict[str, Any] = {
            "node": adapter.node_name,
            "kind": adapter.spec.kind,
            "implementation": adapter.spec.implementation,
            "runtime": adapter.spec.runtime or state.context.get("options").provider if state.context.get("options") else None,
            "optional": adapter.spec.optional,
        }
        try:
            result = await adapter.run(state)
            state.node_reports[adapter.node_name] = result
            row["status"] = "completed"
            if isinstance(result, dict) and "route" in result:
                row["route"] = result["route"]
            state.latencies[adapter.node_name] = time.perf_counter() - start
            row["latency_seconds"] = state.latencies[adapter.node_name]
            trace_rows.append(row)
            return result
        except Exception as exc:
            state.latencies[adapter.node_name] = time.perf_counter() - start
            row["status"] = "failed"
            row["error"] = str(exc)
            row["latency_seconds"] = state.latencies[adapter.node_name]
            trace_rows.append(row)
            raise

    return runner


def _resolve_target(*, node_name: str, spec: NodeSpec, node_callables: dict[str, Any]) -> Any:
    if node_name in node_callables:
        return node_callables[node_name]
    if spec.implementation and spec.implementation in node_callables:
        return node_callables[spec.implementation]
    if spec.kind == "human-gate":
        return None
    if spec.implementation is None:
        raise ValueError(f"node {node_name} is missing an implementation")
    module_name, attr_name = spec.implementation.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, attr_name)


def _resolve_agent(target: Any, node_name: str) -> Agent:
    if isinstance(target, Agent):
        return target
    if inspect.isclass(target) and issubclass(target, Agent):
        try:
            return target(name=node_name)
        except TypeError:
            return target()
    if callable(target):
        candidate = target()
        if isinstance(candidate, Agent):
            return candidate
    raise TypeError(f"node {node_name} does not resolve to an Agent")


async def _invoke_target(target: Any, kwargs: dict[str, Any]) -> Any:
    signature = inspect.signature(target)
    accepts_var_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values())
    supported_kwargs = {
        name: value for name, value in kwargs.items() if accepts_var_kwargs or name in signature.parameters
    }
    result = target(**supported_kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


__all__ = [
    "CompiledGraph",
    "NodeAdapter",
    "WorkflowGraphState",
    "compile_workflow_blueprint",
    "graph_trace_rows",
]
