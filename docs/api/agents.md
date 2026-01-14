# Agents API

The `agents` module contains the fundamental "Lego bricks" of the system.

::: forecast.kit.agents.base.Agent
    options:
      show_root_heading: true
      show_source: true

::: forecast.kit.agents.llm.LLMAgent
    options:
      show_root_heading: true

::: forecast.kit.agents.tool.ToolAgent
    options:
      show_root_heading: true

## Specialized Agents (Specialists)

::: forecast.kit.agents.forecaster.ForecastingAnalyst
    options:
      show_root_heading: true

::: forecast.kit.agents.fact_checker.FactCheckerAgent
    options:
      show_root_heading: true

::: forecast.kit.agents.adversary.AdversaryAgent
    options:
      show_root_heading: true

::: forecast.kit.agents.registry.AgentRegistry
    options:
      show_root_heading: true
