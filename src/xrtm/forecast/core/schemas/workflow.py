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

r"""Workflow schema types for defining forecast graphs.

These are framework-level types. Any developer building a forecasting system
can use these to define graph topologies, question sources, runtime profiles,
and workflow blueprints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

WORKFLOW_SCHEMA_VERSION = "xrtm.workflow.v1"
DEFAULT_LOCAL_WORKFLOWS_DIR = Path(".xrtm/workflows")
_WORKFLOW_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
_SUPPORTED_PROVIDERS = {"deterministic", "local-llm", "openai", "openai-compatible"}
_SUPPORTED_QUESTION_SOURCES = {"real-binary-corpus"}
_WORKFLOW_ALIASES = {"demo-deterministic": "demo-deterministic"}
ALLOWED_PRODUCT_NODE_KINDS = frozenset({"tool", "model", "scorer", "aggregator", "router", "human-gate", "agent"})
DETERMINISTIC_PROVIDER_NAME = "deterministic"
AGGREGATE_CANDIDATES_IMPLEMENTATION = "xrtm.product.workflow_nodes.aggregate_candidate_forecasts_node"


def _normalize_provider_name(name: str) -> str:
    return name.lower()
CANDIDATE_IMPLEMENTATIONS = frozenset(
    {
        "xrtm.product.workflow_nodes.candidate_forecast_node",
        "xrtm.product.workflow_nodes.deterministic_candidate_node",
        "xrtm.product.workflow_nodes.time_series_baseline_node",
    }
)


def validate_workflow_name(name: str) -> None:
    if name in {"", ".", ".."}:
        raise ValueError("workflow name may not be empty, '.', or '..'")
    if not _WORKFLOW_NAME.fullmatch(name):
        raise ValueError("workflow name may only contain letters, numbers, dots, underscores, and dashes")


def _mapping(value: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object")
    return value


def _list_of_strings(value: Any, *, context: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{context} must be a list of non-empty strings")
    return list(value)


def _string(payload: dict[str, Any], key: str, *, context: str, default: str | None = None) -> str:
    value = payload.get(key, default)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string when provided")
    return value


def _integer(payload: dict[str, Any], key: str, *, context: str, default: int) -> int:
    value = payload.get(key, default)
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{context}.{key} must be an integer >= 1")
    return value


def _boolean(payload: dict[str, Any], key: str, *, default: bool) -> bool:
    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be true or false")
    return value


@dataclass(frozen=True)
class QuestionSourceSpec:
    source: str = "real-binary-corpus"
    corpus_id: str = "xrtm-real-binary-v1"
    limit: int = 2

    def __post_init__(self) -> None:
        if self.source not in _SUPPORTED_QUESTION_SOURCES:
            raise ValueError(f"unsupported question source: {self.source}")
        if self.limit < 1:
            raise ValueError("question source limit must be at least 1")

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "QuestionSourceSpec":
        data = _mapping(payload, context="questions")
        return cls(
            source=_string(data, "source", context="questions", default="real-binary-corpus"),
            corpus_id=_string(data, "corpus_id", context="questions", default="xrtm-real-binary-v1"),
            limit=_integer(data, "limit", context="questions", default=2),
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "corpus_id": self.corpus_id,
            "limit": self.limit,
        }


@dataclass(frozen=True)
class RuntimeProfileSpec:
    provider: str = DETERMINISTIC_PROVIDER_NAME
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    max_tokens: int = 768

    def __post_init__(self) -> None:
        normalized_provider = _normalize_provider_name(self.provider)
        object.__setattr__(self, "provider", normalized_provider)
        if normalized_provider not in _SUPPORTED_PROVIDERS:
            raise ValueError(f"unsupported workflow runtime provider: {normalized_provider}")
        if self.max_tokens < 1:
            raise ValueError("runtime max_tokens must be at least 1")

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuntimeProfileSpec":
        data = _mapping(payload, context="runtime")
        return cls(
            provider=_normalize_provider_name(_string(data, "provider", context="runtime", default=DETERMINISTIC_PROVIDER_NAME)),
            base_url=_optional_string(data, "base_url"),
            model=_optional_string(data, "model"),
            api_key=_optional_string(data, "api_key"),
            max_tokens=_integer(data, "max_tokens", context="runtime", default=768),
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "api_key": self.api_key,
            "max_tokens": self.max_tokens,
        }


@dataclass(frozen=True)
class NodeSpec:
    kind: str
    implementation: str | None = None
    runtime: str | None = None
    description: str | None = None
    optional: bool = False
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "NodeSpec":
        data = _mapping(payload, context="graph.nodes")
        kind = data.get("kind", data.get("type"))
        if not isinstance(kind, str) or not kind:
            raise ValueError("graph.nodes.*.kind must be a non-empty string")
        config = data.get("config", {})
        if not isinstance(config, dict):
            raise ValueError("graph.nodes.*.config must be an object when provided")
        return cls(
            kind=kind,
            implementation=_optional_string(data, "implementation"),
            runtime=_optional_string(data, "runtime"),
            description=_optional_string(data, "description"),
            optional=_boolean(data, "optional", default=False),
            config=dict(config),
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "implementation": self.implementation,
            "runtime": self.runtime,
            "description": self.description,
            "optional": self.optional,
            "config": self.config,
        }


@dataclass(frozen=True)
class EdgeSpec:
    from_node: str
    to_node: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EdgeSpec":
        data = _mapping(payload, context="graph.edges")
        from_node = data.get("from_node", data.get("from"))
        to_node = data.get("to_node", data.get("to"))
        if not isinstance(from_node, str) or not from_node:
            raise ValueError("graph.edges.*.from_node must be a non-empty string")
        if not isinstance(to_node, str) or not to_node:
            raise ValueError("graph.edges.*.to_node must be a non-empty string")
        return cls(from_node=from_node, to_node=to_node)

    def to_json_dict(self) -> dict[str, Any]:
        return {"from_node": self.from_node, "to_node": self.to_node}


@dataclass(frozen=True)
class ParallelGroupSpec:
    nodes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.nodes:
            raise ValueError("parallel groups must include at least one node")

    @classmethod
    def from_payload(cls, payload: Any) -> "ParallelGroupSpec":
        if isinstance(payload, dict):
            nodes = payload.get("nodes")
        else:
            nodes = payload
        return cls(nodes=tuple(_list_of_strings(nodes, context="graph.parallel_groups.*.nodes")))

    def to_json_dict(self) -> dict[str, Any]:
        return {"nodes": list(self.nodes)}


@dataclass(frozen=True)
class ConditionalRouteSpec:
    route_field: str = "route"
    routes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.route_field:
            raise ValueError("conditional route field may not be empty")
        if not self.routes:
            raise ValueError("conditional routes must define at least one branch")
        for key, value in self.routes.items():
            if not key or not value:
                raise ValueError("conditional route keys and targets must be non-empty strings")

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ConditionalRouteSpec":
        data = _mapping(payload, context="graph.conditional_routes")
        routes = _mapping(data.get("routes", {}), context="graph.conditional_routes.*.routes")
        normalized_routes: dict[str, str] = {}
        for key, value in routes.items():
            if not isinstance(key, str) or not key:
                raise ValueError("graph.conditional_routes.*.routes keys must be non-empty strings")
            if not isinstance(value, str) or not value:
                raise ValueError("graph.conditional_routes.*.routes values must be non-empty strings")
            normalized_routes[key] = value
        return cls(
            route_field=_string(data, "route_field", context="graph.conditional_routes", default="route"),
            routes=normalized_routes,
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "route_field": self.route_field,
            "routes": self.routes,
        }


@dataclass(frozen=True)
class GraphSpec:
    entry: str
    nodes: dict[str, NodeSpec]
    edges: tuple[EdgeSpec, ...] = ()
    parallel_groups: dict[str, ParallelGroupSpec] = field(default_factory=dict)
    conditional_routes: dict[str, ConditionalRouteSpec] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.nodes:
            raise ValueError("graph.nodes must define at least one node")
        available_targets = set(self.nodes) | set(self.parallel_groups)
        if self.entry not in available_targets:
            raise ValueError(f"graph.entry must reference a node or parallel group, got: {self.entry}")
        for group_name, group in self.parallel_groups.items():
            missing = [node for node in group.nodes if node not in self.nodes]
            if missing:
                raise ValueError(f"graph.parallel_groups.{group_name} references unknown nodes: {', '.join(missing)}")
        for edge in self.edges:
            if edge.from_node not in available_targets:
                raise ValueError(f"graph edge references unknown source: {edge.from_node}")
            if edge.to_node not in available_targets:
                raise ValueError(f"graph edge references unknown target: {edge.to_node}")
        for source_name, route in self.conditional_routes.items():
            if source_name not in available_targets:
                raise ValueError(f"graph conditional route references unknown source: {source_name}")
            missing_targets = [target for target in route.routes.values() if target not in available_targets]
            if missing_targets:
                raise ValueError(
                    f"graph.conditional_routes.{source_name} references unknown targets: {', '.join(missing_targets)}"
                )

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "GraphSpec":
        data = _mapping(payload, context="graph")
        raw_nodes = _mapping(data.get("nodes", {}), context="graph.nodes")
        nodes = {name: NodeSpec.from_payload(node_payload) for name, node_payload in raw_nodes.items()}
        raw_parallel = _mapping(data.get("parallel_groups", {}), context="graph.parallel_groups")
        parallel_groups = {
            name: ParallelGroupSpec.from_payload(group_payload) for name, group_payload in raw_parallel.items()
        }
        raw_conditional = _mapping(data.get("conditional_routes", {}), context="graph.conditional_routes")
        conditional_routes = {
            name: ConditionalRouteSpec.from_payload(route_payload) for name, route_payload in raw_conditional.items()
        }
        raw_edges = data.get("edges", [])
        if not isinstance(raw_edges, list):
            raise ValueError("graph.edges must be a list")
        edges = tuple(EdgeSpec.from_payload(item) for item in raw_edges)
        entry = data.get("entry")
        if entry is None:
            if not nodes:
                raise ValueError("graph.nodes must define at least one node")
            entry = next(iter(nodes))
        if not isinstance(entry, str) or not entry:
            raise ValueError("graph.entry must be a non-empty string")
        return cls(
            entry=entry,
            nodes=nodes,
            edges=edges,
            parallel_groups=parallel_groups,
            conditional_routes=conditional_routes,
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "entry": self.entry,
            "nodes": {name: node.to_json_dict() for name, node in self.nodes.items()},
            "edges": [edge.to_json_dict() for edge in self.edges],
            "parallel_groups": {name: group.to_json_dict() for name, group in self.parallel_groups.items()},
            "conditional_routes": {name: route.to_json_dict() for name, route in self.conditional_routes.items()},
        }


@dataclass(frozen=True)
class ArtifactPolicy:
    write_report: bool = True
    write_blueprint_copy: bool = True
    write_graph_trace: bool = True

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "ArtifactPolicy":
        data = _mapping(payload or {}, context="artifacts")
        return cls(
            write_report=_boolean(data, "write_report", default=True),
            write_blueprint_copy=_boolean(data, "write_blueprint_copy", default=True),
            write_graph_trace=_boolean(data, "write_graph_trace", default=True),
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "write_report": self.write_report,
            "write_blueprint_copy": self.write_blueprint_copy,
            "write_graph_trace": self.write_graph_trace,
        }


@dataclass(frozen=True)
class ScoringPolicy:
    write_eval: bool = True
    write_train_backtest: bool = True

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "ScoringPolicy":
        data = _mapping(payload or {}, context="scoring")
        return cls(
            write_eval=_boolean(data, "write_eval", default=True),
            write_train_backtest=_boolean(data, "write_train_backtest", default=True),
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "write_eval": self.write_eval,
            "write_train_backtest": self.write_train_backtest,
        }


@dataclass(frozen=True)
class WorkflowBlueprint:
    name: str
    title: str
    description: str
    workflow_kind: str
    questions: QuestionSourceSpec
    runtime: RuntimeProfileSpec
    graph: GraphSpec
    artifacts: ArtifactPolicy = field(default_factory=ArtifactPolicy)
    scoring: ScoringPolicy = field(default_factory=ScoringPolicy)
    schema_version: str = WORKFLOW_SCHEMA_VERSION
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_workflow_name(self.name)
        if self.schema_version != WORKFLOW_SCHEMA_VERSION:
            raise ValueError(f"unsupported workflow schema version: {self.schema_version}")
        if not self.title:
            raise ValueError("workflow title may not be empty")
        if not self.description:
            raise ValueError("workflow description may not be empty")
        if not self.workflow_kind:
            raise ValueError("workflow_kind may not be empty")

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "WorkflowBlueprint":
        data = _mapping(payload, context="workflow")
        questions_payload = data.get("questions", data.get("question_source"))
        if questions_payload is None:
            raise ValueError("workflow.questions is required")
        return cls(
            schema_version=_string(data, "schema_version", context="workflow", default=WORKFLOW_SCHEMA_VERSION),
            name=_string(data, "name", context="workflow"),
            title=_string(data, "title", context="workflow"),
            description=_string(data, "description", context="workflow"),
            workflow_kind=_string(data, "workflow_kind", context="workflow", default="workflow"),
            questions=QuestionSourceSpec.from_payload(questions_payload),
            runtime=RuntimeProfileSpec.from_payload(data.get("runtime", {})),
            graph=GraphSpec.from_payload(data.get("graph", {})),
            artifacts=ArtifactPolicy.from_payload(data.get("artifacts")),
            scoring=ScoringPolicy.from_payload(data.get("scoring")),
            tags=tuple(_list_of_strings(data.get("tags", []), context="workflow.tags")) if "tags" in data else (),
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "workflow_kind": self.workflow_kind,
            "questions": self.questions.to_json_dict(),
            "runtime": self.runtime.to_json_dict(),
            "graph": self.graph.to_json_dict(),
            "artifacts": self.artifacts.to_json_dict(),
            "scoring": self.scoring.to_json_dict(),
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class WorkflowSummary:
    name: str
    title: str
    workflow_kind: str
    description: str
    source: str
    runtime_provider: str
    question_limit: int
    path: str


