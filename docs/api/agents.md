# Agents API

The `agents` module contains the fundamental "Lego bricks" of the system.

::: xrtm.forecast.kit.agents.base.Agent
    options:
      show_root_heading: true
      show_source: true

::: xrtm.forecast.kit.agents.llm.LLMAgent
    options:
      show_root_heading: true

::: xrtm.forecast.kit.agents.tool.ToolAgent
    options:
      show_root_heading: true

::: xrtm.forecast.kit.agents.registry.AgentRegistry
    options:
      show_root_heading: true

## Specialized Agents (Specialists)

::: xrtm.forecast.kit.agents.specialists.analyst.ForecastingAnalyst
    options:
      show_root_heading: true

> **Changed in 0.9–0.10.** The `FactCheckerAgent` and `AdversaryAgent`
> specialists were removed. Verification-style work is now expressed with
> `DecisionProvider` + `EscalationRouter` (see [Decisions](decisions.md)), and
> research with skills such as `WebSearchSkill`.
