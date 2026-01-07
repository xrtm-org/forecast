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

from forecast.memory.unified import Memory as UnifiedMemory

logger = logging.getLogger(__name__)


class EpisodicLearner:
    """
    Bridges episodic memory with live agent execution.
    Retrieves relevant lessons learned from the past to inject into LLM prompts.
    """

    def __init__(self, memory: UnifiedMemory):
        self.memory = memory

    def get_lessons_for_subject(self, subject_id: str, n_results: int = 3) -> str:
        """
        Retrieves the top N similar experiences for a subject and formats them for prompt injection.
        """
        try:
            # Query for the subject specifically or similar event types
            query = f"Past performance and lessons for {subject_id}"
            experiences = self.memory.retrieve_similar(query, n_results=n_results)

            if not experiences:
                return "No relevant past experiences found."

            formatted_lessons = "\n--- PAST LESSONS LEARNED ---\n"
            for i, doc in enumerate(experiences, 1):
                formatted_lessons += f"Experience {i}:\n{doc.strip()}\n"

            return formatted_lessons
        except Exception as e:
            logger.error(f"[LEARNER] Failed to retrieve lessons: {e}")
            return "Error retrieving past lessons."
