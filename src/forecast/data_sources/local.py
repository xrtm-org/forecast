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

import json
import logging
from typing import List, Optional

from forecast.data_sources.base import DataSource
from forecast.schemas.forecast import ForecastQuestion

logger = logging.getLogger(__name__)


class LocalDataSource(DataSource):
    """
    DataSource implementation that reads from a local JSON file.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    async def fetch_questions(self, query: Optional[str] = None, limit: int = 5) -> List[ForecastQuestion]:
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)

            questions = []
            for item in data:
                # Basic title-based search
                if not query or query.lower() in item.get("title", "").lower():
                    questions.append(ForecastQuestion(**item))

                if len(questions) >= limit:
                    break
            return questions
        except Exception as e:
            logger.error(f"Failed to read local questions from {self.file_path}: {e}")
            return []

    async def get_question_by_id(self, question_id: str) -> Optional[ForecastQuestion]:
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)

            for item in data:
                if item.get("id") == question_id:
                    return ForecastQuestion(**item)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve question {question_id} from {self.file_path}: {e}")
            return None
