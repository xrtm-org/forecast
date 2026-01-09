# Evaluation API

Tools for benchmarking and validating agent performance.

::: forecast.core.eval.definitions.Evaluator
    options:
      show_root_heading: true

::: forecast.kit.eval.runner.BacktestRunner
    options:
      show_root_heading: true

::: forecast.kit.eval.runner.BacktestInstance
    options:
      show_root_heading: true

::: forecast.core.eval.definitions.EvaluationReport
    options:
      show_root_heading: true
      members:
        - to_json
        - to_pandas

::: forecast.core.eval.definitions.ReliabilityBin
    options:
      show_root_heading: true

::: forecast.kit.eval.metrics.BrierScoreEvaluator
    options:
      show_root_heading: true

::: forecast.kit.eval.metrics.ExpectedCalibrationErrorEvaluator
    options:
      show_root_heading: true
