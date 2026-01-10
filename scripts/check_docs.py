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

import argparse
import os
import re
import sys


def check_file(filepath):
    r"""
    Verifies a single file for documentation standards.

    Checks for:
    1. Apache 2.0 license header.
    2. r\"\"\" docstrings for top-level public classes and functions.

    Args:
        filepath (`str`): Path to the python file to audit.

    Returns:
        `list[str]`: A list of strings describing any compliance errors found.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    errors = []

    # 1. License Check
    if "Copyright 2026 XRTM Team" not in content or "Apache License, Version 2.0" not in content:
        errors.append("Missing Apache 2.0 License Header")

    # 2. Docstring check for top-level public classes and functions
    lines = content.splitlines()
    for i, line in enumerate(lines):
        # Match public class or function definition ONLY at column 0
        match = re.match(r"^(class|async def|def) ([a-zA-Z_][a-zA-Z0-9_]*)(?:\(.*\))?:", line)
        if match:
            kind, name = match.groups()
            if name.startswith("_") or name.startswith("test_") or name == "main":
                continue

            # Skip common test/mock patterns in non-core code
            if ("tests/" in filepath or "examples/" in filepath) and (
                name.startswith("Mock") or name.startswith("mock_") or name.startswith("pytest_")
            ):
                continue

            # Check next lines for docstring
            has_doc = False
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if not next_line:
                    continue
                if next_line.startswith('r"""') or next_line.startswith('"""'):
                    has_doc = True
                break

            if not has_doc:
                errors.append(f"Missing docstring for public item: {name}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Audit Python files for institutional standards.")
    parser.add_argument(
        "--global-audit", action="store_true", help="Audit the entire repository instead of just src/forecast"
    )
    args = parser.parse_args()

    base_dir = "." if args.global_audit else "src/forecast"
    total_errors = 0
    total_files = 0

    print(f"--- Documentation Audit: {base_dir} ---")

    ignore_dirs = {".venv", "__pycache__", ".agent", ".git", "build", "dist", ".mypy_cache", ".pytest_cache"}

    for root, dirs, files in os.walk(base_dir):
        # In-place modification to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if not file.endswith(".py") or file == "__init__.py":
                continue

            # Skip this script itself
            if file == "check_docs.py":
                continue

            path = os.path.join(root, file)
            total_files += 1
            file_errors = check_file(path)

            if file_errors:
                print(f"[FAIL] {path}")
                for err in file_errors:
                    print(f"  - {err}")
                total_errors += len(file_errors)
            # else:
            #     print(f"[PASS] {path}")

    print(f"\nAudit completed. Scanned {total_files} files.")
    if total_errors > 0:
        print(f"Failed with {total_errors} errors.")
        sys.exit(1)
    else:
        print("Audit passed! All documented items meet institutional standards.")
        sys.exit(0)


if __name__ == "__main__":
    main()
