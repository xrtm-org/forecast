from click.testing import CliRunner

from xrtm.forecast.cli.main import cli


def test_real_e2e_artifact_dir_help_is_actionable() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["real-e2e-local-llm", "--help"])

    assert result.exit_code == 0
    assert "Directory for JSONL runtime artifacts" in result.output
    assert "Ignored runtime artifact directory" not in result.output
