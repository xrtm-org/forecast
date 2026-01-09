# Evaluation API

Tools for benchmarking and validating agent performance.

::: forecast.eval.definitions.Evaluator
    options:
      show_root_heading: true

::: forecast.eval.runner.BacktestRunner
    options:
      show_root_heading: true

::: forecast.eval.runner.BacktestInstance
    options:
      show_root_heading: true

::: forecast.eval.definitions.EvaluationReport
    options:
      show_root_heading: true
      members:
        - to_json
        - to_pandas

::: forecast.eval.definitions.ReliabilityBin
    options:
      show_root_heading: true

::: forecast.eval.metrics.BrierScoreEvaluator
    options:
      show_root_heading: true

::: forecast.eval.metrics.ExpectedCalibrationErrorEvaluator
    options:
      show_root_heading: true
