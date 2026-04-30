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
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from xrtm.forecast.core.utils.bundling import ForecastBundle
from xrtm.forecast.version import __version__

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


@cli.command(name="real-e2e-local-llm")
@click.option("--limit", type=int, default=2, show_default=True, help="Number of real corpus questions to run.")
@click.option("--base-url", default=None, help="OpenAI-compatible local endpoint, e.g. http://localhost:8080/v1.")
@click.option("--model", default=None, help="Local model id served by the endpoint.")
@click.option("--api-key", default=None, help="API key for the local endpoint; defaults to test/env.")
@click.option("--max-tokens", type=int, default=768, show_default=True, help="Maximum completion tokens per question.")
@click.option("--artifact-dir", type=click.Path(file_okay=False, path_type=Path), default=None, help="Directory for JSONL runtime artifacts.")
@click.option("--no-artifacts", is_flag=True, help="Validate without writing JSONL runtime artifacts.")
def real_e2e_local_llm(
    limit: int,
    base_url: str | None,
    model: str | None,
    api_key: str | None,
    max_tokens: int,
    artifact_dir: Path | None,
    no_artifacts: bool,
):
    r"""Run deterministic real-question E2E validation against a local LLM."""
    from xrtm.forecast.e2e import run_real_question_e2e

    try:
        records = run_real_question_e2e(
            limit=limit,
            base_url=base_url,
            model=model,
            api_key=api_key,
            max_tokens=max_tokens,
            artifact_dir=artifact_dir,
            write_artifacts=not no_artifacts,
        )
    except Exception as exc:
        console.print(Panel(f"[bold red]Real-question E2E failed[/bold red]\n{exc}", title="Local LLM E2E"))
        sys.exit(1)

    table = Table(title="Real-question local LLM E2E")
    table.add_column("Question ID", style="cyan")
    table.add_column("Probability", justify="right")
    table.add_column("Trace Nodes", justify="right")
    for record in records:
        table.add_row(
            record.question_id,
            f"{record.output.probability:.3f}",
            str(len(record.output.logical_trace)),
        )
    console.print(table)
    console.print(f"[bold green]Validated {len(records)} ForecastOutput record(s).[/bold green]")


if __name__ == "__main__":
    cli()
__all__ = ["cli"]
