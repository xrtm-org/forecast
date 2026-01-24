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

r"""Unit tests for forecast.core.tools.base."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from xrtm.forecast.core.schemas.graph import TemporalContext
from xrtm.forecast.core.tools.base import FunctionTool, StrandToolWrapper, Tool


class TestFunctionTool:
    r"""Tests for the FunctionTool class."""

    @pytest.mark.asyncio
    async def test_sync_function(self):
        r"""Should wrap and execute sync function."""

        def add(a, b):
            return int(a) + int(b)

        tool = FunctionTool(add)
        result = await tool.run(a="1", b="2")
        assert result == 3

    @pytest.mark.asyncio
    async def test_async_function(self):
        r"""Should wrap and execute async function."""

        async def async_add(a, b):
            return int(a) + int(b)

        tool = FunctionTool(async_add)
        result = await tool.run(a="3", b="4")
        assert result == 7

    def test_name_from_function(self):
        r"""Should use function name as tool name."""

        def my_tool_func():
            pass

        tool = FunctionTool(my_tool_func)
        assert tool.name == "my_tool_func"

    def test_name_override(self):
        r"""Should allow name override."""

        def my_func():
            pass

        tool = FunctionTool(my_func, name="custom_name")
        assert tool.name == "custom_name"

    def test_description_from_docstring(self):
        r"""Should use docstring as description."""

        def documented_func():
            r"""This is the docstring."""
            pass

        tool = FunctionTool(documented_func)
        assert "docstring" in tool.description

    def test_description_override(self):
        r"""Should allow description override."""

        def my_func():
            r"""Original docstring."""
            pass

        tool = FunctionTool(my_func, description="Custom description")
        assert tool.description == "Custom description"

    def test_description_default(self):
        r"""Should provide default when no docstring."""

        def no_doc():
            pass

        no_doc.__doc__ = None
        tool = FunctionTool(no_doc)
        assert tool.description == "No description provided."

    def test_parameters_schema_generation(self):
        r"""Should generate schema from function signature."""

        def func_with_params(required_param, optional_param="default"):
            pass

        tool = FunctionTool(func_with_params)
        schema = tool.parameters_schema

        assert schema["type"] == "object"
        assert "required_param" in schema["properties"]
        assert "optional_param" in schema["properties"]
        assert "required_param" in schema["required"]
        assert "optional_param" not in schema["required"]


class TestStrandToolWrapper:
    r"""Tests for the StrandToolWrapper class."""

    def test_name_from_strand_tool(self):
        r"""Should extract name from strand tool."""
        mock_tool = MagicMock()
        mock_tool.name = "strand_search"
        wrapper = StrandToolWrapper(mock_tool)
        assert wrapper.name == "strand_search"

    def test_name_default(self):
        r"""Should provide default name when not set."""
        mock_tool = MagicMock(spec=[])  # No attributes
        wrapper = StrandToolWrapper(mock_tool)
        assert wrapper.name == "unnamed_strand_tool"

    def test_description_from_strand_tool(self):
        r"""Should extract description from strand tool."""
        mock_tool = MagicMock()
        mock_tool.description = "Searches the web"
        wrapper = StrandToolWrapper(mock_tool)
        assert wrapper.description == "Searches the web"

    def test_description_default(self):
        r"""Should provide default description when not set."""
        mock_tool = MagicMock(spec=[])
        wrapper = StrandToolWrapper(mock_tool)
        assert wrapper.description == "No description provided."

    def test_parameters_schema_from_parameters(self):
        r"""Should extract schema from parameters attribute."""
        mock_tool = MagicMock()
        mock_tool.parameters = {"type": "object", "properties": {}}
        wrapper = StrandToolWrapper(mock_tool)
        assert wrapper.parameters_schema == {"type": "object", "properties": {}}

    def test_parameters_schema_from_spec(self):
        r"""Should extract schema from spec attribute as fallback."""
        mock_tool = MagicMock(spec=["spec"])
        mock_tool.spec = {"type": "object"}
        del mock_tool.parameters
        wrapper = StrandToolWrapper(mock_tool)
        assert wrapper.parameters_schema == {"type": "object"}

    def test_parameters_schema_default(self):
        r"""Should return empty schema when neither parameters nor spec."""
        mock_tool = MagicMock(spec=[])
        wrapper = StrandToolWrapper(mock_tool)
        assert wrapper.parameters_schema == {}

    @pytest.mark.asyncio
    async def test_run_sync_function(self):
        r"""Should execute sync strand function."""
        mock_tool = MagicMock()
        mock_tool.fn = lambda x: x * 2
        wrapper = StrandToolWrapper(mock_tool)
        result = await wrapper.run(x=5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_run_async_function(self):
        r"""Should execute async strand function."""

        async def async_fn(x):
            return x * 3

        mock_tool = MagicMock()
        mock_tool.fn = async_fn
        wrapper = StrandToolWrapper(mock_tool)
        result = await wrapper.run(x=4)
        assert result == 12

    @pytest.mark.asyncio
    async def test_run_handles_exception(self):
        r"""Should handle exceptions and return error string."""

        def failing_fn():
            raise ValueError("Test error")

        mock_tool = MagicMock()
        mock_tool.fn = failing_fn
        mock_tool.name = "failing_tool"
        wrapper = StrandToolWrapper(mock_tool)
        result = await wrapper.run()
        assert "Error:" in result


class TestToolBase:
    r"""Tests for Tool base class methods."""

    def test_pit_supported_default(self):
        r"""Should return False by default for pit_supported."""

        class ConcreteTool(Tool):
            @property
            def name(self):
                return "test"

            @property
            def description(self):
                return "test"

            @property
            def parameters_schema(self):
                return {}

            async def run(self, **kwargs):
                return None

        tool = ConcreteTool()
        assert tool.pit_supported is False

    def test_apply_temporal_filters_no_context(self):
        r"""Should return query unchanged when no temporal context."""

        class ConcreteTool(Tool):
            @property
            def name(self):
                return "test"

            @property
            def description(self):
                return "test"

            @property
            def parameters_schema(self):
                return {}

            async def run(self, **kwargs):
                return None

        tool = ConcreteTool()
        result = tool._apply_temporal_filters("my query", None)
        assert result == "my query"

    def test_apply_temporal_filters_not_backtest(self):
        r"""Should return query unchanged when not backtest mode."""

        class ConcreteTool(Tool):
            @property
            def name(self):
                return "test"

            @property
            def description(self):
                return "test"

            @property
            def parameters_schema(self):
                return {}

            async def run(self, **kwargs):
                return None

        tool = ConcreteTool()
        ctx = TemporalContext(reference_time=datetime.now(), is_backtest=False)
        result = tool._apply_temporal_filters("my query", ctx)
        assert result == "my query"

    def test_apply_temporal_filters_backtest(self):
        r"""Should append date filter in backtest mode."""

        class ConcreteTool(Tool):
            @property
            def name(self):
                return "test"

            @property
            def description(self):
                return "test"

            @property
            def parameters_schema(self):
                return {}

            async def run(self, **kwargs):
                return None

        tool = ConcreteTool()
        ctx = TemporalContext(reference_time=datetime(2025, 6, 15), is_backtest=True)
        result = tool._apply_temporal_filters("my query", ctx)
        assert "before:2025-06-15" in result

    def test_apply_temporal_filters_no_duplicate(self):
        r"""Should not duplicate existing date filter."""

        class ConcreteTool(Tool):
            @property
            def name(self):
                return "test"

            @property
            def description(self):
                return "test"

            @property
            def parameters_schema(self):
                return {}

            async def run(self, **kwargs):
                return None

        tool = ConcreteTool()
        ctx = TemporalContext(reference_time=datetime(2025, 6, 15), is_backtest=True)
        result = tool._apply_temporal_filters("my query before:2025-06-15", ctx)
        assert result.count("before:2025-06-15") == 1
