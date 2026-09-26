# Calibration & Prompt Optimization

> **Relocated in 0.9–0.10.** The in-engine Platt/Beta scalers and the DSPy-style
> prompt compiler were removed. Scoring and calibration now live in `xrtm-eval`,
> and prompts are configured through `PromptTemplate`.

## Scoring (xrtm-eval)

Brier score, expected calibration error, and reliability decomposition ship in
`xrtm-eval`:

::: xrtm.eval.kit.eval.metrics.BrierScoreEvaluator
    options:
      show_root_heading: true

::: xrtm.eval.kit.eval.metrics.ExpectedCalibrationErrorEvaluator
    options:
      show_root_heading: true

## Prompt configuration

::: xrtm.forecast.core.schemas.prompt.PromptTemplate
    options:
      show_root_heading: true
      show_source: true

Pass a template to the analyst: `ForecastingAnalyst(model=..., prompt_template=template)`.
The template id is recorded in `ForecastOutput.provenance.prompt_id`.
