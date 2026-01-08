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
from typing import Any, Dict

from forecast.tools.base import Tool

logger = logging.getLogger(__name__)


class SQLSkill(Tool):
    r"""
    A tool for executing read-only SQL queries against a database.

    By default, it uses a local SQLite connection but can be configured for other backends.
    This tool is essential for institutional analysts who need to query structured
    relational data.
    """

    def __init__(self, db_url: str = ":memory:", name: str = "sql_query"):
        self._db_url = db_url
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "Executes a read-only SQL query and returns the results as a list of dictionaries."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The SQL SELECT query to execute."}},
            "required": ["query"],
        }

    async def run(self, **kwargs: Any) -> Any:
        r"""
        Executes a read-only SQL query and returns the results.

        Args:
            **kwargs:
                Must include 'query' (str): The SQL SELECT query to execute.

        Returns:
            `Any`: A list of dictionaries representing the rows, or an error message.
        """
        query = kwargs.get("query")
        if not query or not isinstance(query, str):
            return "Error: 'query' argument is required and must be a string."
        import re
        import sqlite3

        # Institutional Guardrail: Robust read-only check
        forbidden_keywords = r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|GRANT|REVOKE)\b"

        # Strip comments for validation purposes
        clean_query = re.sub(r"--.*?\n", "\n", query)  # Strip -- comments
        clean_query = re.sub(r"/\*.*?\*/", "", clean_query, flags=re.DOTALL)  # Strip /* */ comments

        if re.search(forbidden_keywords, clean_query, re.IGNORECASE):
            return "Error: For security reasons, only read-only (SELECT) operations are allowed."

        if not re.search(r"\bSELECT\b", clean_query, re.IGNORECASE):
            return "Error: The query must contain a SELECT statement."

        # Ensure it starts with SELECT after stripping whitespace/comments
        if not re.search(r"^\s*SELECT\b", clean_query.strip(), re.IGNORECASE):
            return "Error: The first statement in the query must be a SELECT."

        try:
            # We use local threading fallback since sqlite3 is blocking
            import asyncio

            def _query():
                conn = sqlite3.connect(self._db_url)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                results = [dict(r) for r in rows]
                conn.close()
                return results

            return await asyncio.to_thread(_query)
        except Exception as e:
            logger.error(f"SQLSkill execution failed: {e}")
            return f"Error executing SQL: {str(e)}"


class PandasSkill(Tool):
    r"""
    A tool for processing and analyzing data using the Pandas library.

    Useful for complex aggregations, transformations, and statistical analysis
    that raw SQL alone cannot handle easily.
    """

    def __init__(self, name: str = "pandas_analyze"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return (
            "Analyzes tabular data using pandas. Common operations include 'describe', 'mean', 'sum', and 'group_by'."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {"type": "array", "description": "List of dictionaries representing the dataset."},
                "operation": {
                    "type": "string",
                    "enum": ["describe", "mean", "sum", "count"],
                    "description": "The operation to perform.",
                },
                "column": {"type": "string", "description": "The specific column to operate on (if applicable)."},
            },
            "required": ["data", "operation"],
        }

    async def run(self, **kwargs: Any) -> Any:
        r"""
        Analyzes tabular data using pandas.

        Args:
            **kwargs:
                Must include:
                - 'data' (List[Dict[str, Any]]): The dataset.
                - 'operation' (str): The operation (e.g., 'describe', 'mean').
                Optional:
                - 'column' (str): The column to operate on.

        Returns:
            `Any`: The result of the pandas analysis or an error message.
        """
        data = kwargs.get("data")
        operation = kwargs.get("operation")
        column = kwargs.get("column")
        try:
            import pandas as pd
        except ImportError:
            return "Error: pandas is not installed. Install with `pip install xrtm-forecast[data]`"

        if not data:
            return "Error: Data list is empty."

        try:
            df = pd.DataFrame(data)

            if operation == "describe":
                return df.describe(include="all").to_dict()

            if not column:
                return "Error: 'column' argument is required for this operation."

            if column not in df.columns:
                return f"Error: Column '{column}' not found in dataset. Available columns: {list(df.columns)}"

            if operation == "mean":
                return float(df[column].mean())
            if operation == "sum":
                return float(df[column].sum())
            if operation == "count":
                return int(df[column].count())

            return f"Error: Unsupported operation '{operation}'"
        except Exception as e:
            logger.error(f"PandasSkill execution failed: {e}")
            return f"Error in data analysis: {str(e)}"


__all__ = ["SQLSkill", "PandasSkill"]
