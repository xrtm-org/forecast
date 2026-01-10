import os

HEADER = """# coding=utf-8
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

"""

FILES = [
    "tests/experimental/verify_guardian_logic.py",
    "tests/experimental/verify_pit_search.py",
    "tests/experimental/verify_temporal_logic.py",
    "tests/unit/__init__.py",
    "tests/conftest.py",
    "tests/integration/__init__.py",
    "tests/integration/test_pit_search.py",
    "tests/integration/test_scenarios.py",
    "tests/verification/test_calibration_metrics.py",
    "tests/live/test_leakage_protection_live.py",
    "tests/live/__init__.py",
    "examples/core/__init__.py",
    "examples/providers/__init__.py",
    "examples/providers/data/__init__.py",
    "examples/kit/features/__init__.py",
    "examples/kit/features/trace_replay.py",
    "examples/kit/minimal_agent.py",
    "examples/kit/__init__.py",
    "examples/kit/pipelines/__init__.py",
    "examples/kit/topologies/__init__.py",
    "examples/__init__.py",
]

for fpath in FILES:
    full_path = os.path.join("/workspace/forecast", fpath)
    if not os.path.exists(full_path):
        print(f"Skipping {fpath} (not found)")
        continue

    with open(full_path, "r") as f:
        content = f.read()

    if "Copyright 2026 XRTM Team" in content:
        print(f"Skipping {fpath} (already has header)")
        continue

    with open(full_path, "w") as f:
        f.write(HEADER + content)
    print(f"Applied header to {fpath}")
