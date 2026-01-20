# Optimization API

The Optimization module provides tools for automatic probability calibration and "DSPy-style" prompt engineering to minimize Brier Score.

## Core: Calibration Engines

### PlattScaler
The original Platt Scaling implementation using Logistic Regression.

::: forecast.core.eval.calibration.PlattScaler
    options:
      show_root_heading: true
      show_source: true

### BetaScaler
An advanced calibrator superior for handling asymmetric overconfidence ("S-curves").

::: forecast.core.eval.calibration.BetaScaler
    options:
      show_root_heading: true
      show_source: true

---

## Kit: Prompt Optimization

### PromptTemplate
A versioned, structured prompt object that enables iterative optimization.

::: forecast.kit.agents.prompting.PromptTemplate
    options:
      show_root_heading: true
      show_source: true

### CompiledAgent
An LLM agent that uses a `PromptTemplate`, allowing for external compilation.

::: forecast.kit.agents.prompting.CompiledAgent
    options:
      show_root_heading: true
      show_source: true

### BrierOptimizer
The "Teleprompter" that tunes instructions to reduce forecasting errors.

::: forecast.kit.optimization.compiler.BrierOptimizer
    options:
      show_root_heading: true
      show_source: true
