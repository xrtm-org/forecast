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

from xrtm.forecast import AsyncRuntime

# Configure logging to see uvloop activation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("runtime_demo")


async def worker(name: str, delay: float):
    r"""
    A demo worker that simulates an institutional task.

    Args:
        name (`str`): The name assigned to the worker.
        delay (`float`): The duration (in seconds) the worker should sleep.

    Returns:
        `str`: A formatted result string.
    """
    logger.info(f"Worker {name} starting (Task: {AsyncRuntime.current_task_name()})")
    await AsyncRuntime.sleep(delay)
    logger.info(f"Worker {name} finished after {delay}s")
    return f"Result from {name}"


async def main():
    logger.info("=== Starting AsyncRuntime Patterns Demo ===")

    # 1. Structured Concurrency with TaskGroups
    logger.info("--- Phase 1: TaskGroups ---")
    async with AsyncRuntime.task_group() as tg:
        t1 = tg.create_task(worker("A", 0.1))
        t2 = tg.create_task(worker("B", 0.2))

    logger.info(f"Batch results: {t1.result()}, {t2.result()}")

    # 2. Institutional Spawn with Mandatory Naming
    logger.info("\n--- Phase 2: Mandatory Naming ---")
    task = AsyncRuntime.spawn(worker("C", 0.1), name="custom_worker_c")
    result = await task
    logger.info(f"Spawned result: {result}")


if __name__ == "__main__":
    # AsyncRuntime.run_main handles uvloop installation automatically
    AsyncRuntime.run_main(main())
