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

r"""
Main CLI entry point for xrtm-forecast.
r"""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forecast.core.utils.bundling import ForecastBundle
from forecast.version import __version__

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    r"""Institutional-grade reasoning engine CLI."""
    pass


@cli.command()
@click.argument("bundle_path", type=click.Path(exists=True))
@click.option("--verbose", is_flag=True, help="Show detailed hash analysis.")
def verify(bundle_path: str, verbose: bool):
    r"""
    Verifies the integrity of a .forecast bundle.

    Checks the manifest, verifies SHA-256 hashes of all components (trace, evidence, environment),
    and confirms the bundle hasn't been tampered with.
    r"""
    console.print(f"[bold blue]Verifying Bundle:[/bold blue] {bundle_path}")

    bundle = ForecastBundle(bundle_path)
    results = bundle.verify()

    if results["is_valid"]:
        metadata = results["metadata"]
        console.print(
            Panel(
                f"[bold green]SUCCESS: Bundle Integrity Verified[/bold green]\n"
                f"Engine Version: {metadata.get('version')}\n"
                f"Created At: {metadata.get('created_at')}",
                title="Institutional Audit Report",
                expand=False,
            )
        )

        if verbose:
            table = Table(title="Bundle Contents (Verified)")
            table.add_column("File", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Hash (SHA-256)", style="dim")

            for filename, file_hash in metadata.get("files", {}).items():
                table.add_row(filename, "CLEAN", file_hash)

            console.print(table)
    else:
        console.print(
            Panel(
                "[bold red]FAILURE: Bundle Compromised[/bold red]\n"
                + "\n".join([f"- {err}" for err in results["errors"]]),
                title="Institutional Audit Report",
                expand=False,
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    cli()
__all__ = ["cli"]
