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

import abc
from typing import List, Optional

from forecast.schemas.forecast import ForecastQuestion


class DataSource(abc.ABC):
    r"""
    Abstract interface for gathering or streaming forecasting workloads.

    `DataSource` implementations are responsible for retrieving `ForecastQuestion`
    objects from external environments (e.g., Prediction Markets, Local Databases,
    or APIs).
    """

    @abc.abstractmethod
    async def fetch_questions(self, query: Optional[str] = None, limit: int = 5) -> List[ForecastQuestion]:
        r"""
        Retrieves a collection of forecast questions.

        Args:
            query (`str`, *optional*):
                A search string or filter for specialized discovery.
            limit (`int`, *optional*, defaults to `5`):
                The maximum number of questions to retrieve.

        Returns:
            `List[ForecastQuestion]`: A list of questions ready for processing.
        """
        pass

    @abc.abstractmethod
    async def get_question_by_id(self, question_id: str) -> Optional[ForecastQuestion]:
        r"""
        Retrieves a specific forecast question by its unique identifier.

        Args:
            question_id (`str`):
                The unique ID of the question.

        Returns:
            `Optional[ForecastQuestion]`: The question object if found, else `None`.
        """
        pass


__all__ = ["DataSource"]
