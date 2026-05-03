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

import os
from pathlib import Path

import pytest

# Automatic Environment Loading (OSS Best Practice)
# usage: pytest ... (no wrapper script needed)
env_path = Path(".env")
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def pytest_addoption(parser):
    parser.addoption("--run-live", action="store_true", default=False, help="run live tests")
    parser.addoption("--run-local-llm", action="store_true", default=False, help="run local LLM tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: mark test as part of the unit layer")
    config.addinivalue_line("markers", "integration: mark test as part of the integration layer")
    config.addinivalue_line("markers", "verification: mark test as part of the verification layer")
    config.addinivalue_line("markers", "e2e: mark test as part of the end-to-end layer")
    config.addinivalue_line("markers", "local: mark test as part of the local environment layer")
    config.addinivalue_line("markers", "live: mark test as live to run")
    config.addinivalue_line("markers", "local_llm: mark test as requiring a local LLM endpoint")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live"):
        # --run-live given in cli: do not skip live tests
        skip_live = None
    else:
        skip_live = pytest.mark.skip(reason="need --run-live option to run")
    run_local_llm = config.getoption("--run-local-llm") or os.getenv("XRTM_RUN_LOCAL_LLM") == "1"
    skip_local_llm = None if run_local_llm else pytest.mark.skip(
        reason="need --run-local-llm option or XRTM_RUN_LOCAL_LLM=1 to run"
    )
    for item in items:
        path_parts = Path(str(item.fspath)).parts
        for layer in ("unit", "integration", "verification", "e2e", "live", "local"):
            if layer in path_parts:
                item.add_marker(layer)
        if skip_live is not None and "live" in item.keywords:
            item.add_marker(skip_live)
        if skip_local_llm is not None and "local_llm" in item.keywords:
            item.add_marker(skip_local_llm)
