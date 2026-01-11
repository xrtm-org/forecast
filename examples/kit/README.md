# Researcher Kit Examples (Instruments)

The Researcher Kit provides high-level "Instruments" and "Agents" for building complex forecasting workflows. These examples demonstrate the "Practical Shell" that builds on top of the Core.

## Master List of Examples

Below is a catalog of all available examples in the Researcher Kit, ensuring comprehensive coverage of varied forecasting needs.

### 1. Fundamental Agents
| Project | Description | Use Case |
| :--- | :--- | :--- |
| [minimal_agent](file:///workspace/forecast/examples/kit/minimal_agent/run_minimal_agent.py) | The "Hello World" of agents. A single LLM call with no memory or tools. | Starting point for understanding agent instantiations. |
| [local_analyst](file:///workspace/forecast/examples/kit/local_analyst/run_local_analyst.py) | Demonstrates using small, local LLMs (e.g., via Ollama/LocalAI) instead of cloud APIs. | Cost-sensitive or privacy-first deployments. |
| [backtest_workflow](file:///workspace/forecast/examples/kit/backtest_workflow/run_backtest_workflow.py) | Runs an agent through historical data with strict temporal sandboxing. | Verifying strategy performance on past events. |

### 2. Specialized Features (Capabilities)
These examples show how to add specific "superpowers" to your agents.

| Project | Description | Use Case |
| :--- | :--- | :--- |
| [discovery](file:///workspace/forecast/examples/kit/features/discovery/run_discovery.py) | Automated information retrieval and expansive search. | When the agent needs to "learn" a topic from scratch. |
| [calibration_demo](file:///workspace/forecast/examples/kit/features/calibration_demo/run_calibration_demo.py) | Techniques for adjusting probability confidence intervals. | Fixing over-confident models. |
| [sensitivity_analysis](file:///workspace/forecast/examples/kit/features/sensitivity_analysis/run_sensitivity_analysis.py) | Testing how forecast changes with different assumptions. | Robustness checks and scenario planning. |
| [streaming_demo](file:///workspace/forecast/examples/kit/features/streaming_demo/run_streaming_demo.py) | Handling streamed token responses for UI feedback. | Building chat interfaces or real-time dashboards. |
| [structured_telemetry](file:///workspace/forecast/examples/kit/features/structured_telemetry/run_structured_telemetry.py) | Emitting JSON logs for observability tools. | Production monitoring and debugging. |
| [trace_replay](file:///workspace/forecast/examples/kit/features/trace_replay/run_trace_replay.py) | Re-running a saved execution trace for debugging. | Post-mortem analysis of why an agent failed. |

### 3. End-to-End Pipelines
Full workflows for solving complex real-world problems.

| Project | Description | Use Case |
| :--- | :--- | :--- |
| [forecasting_analyst](file:///workspace/forecast/examples/kit/pipelines/forecasting_analyst/run_forecasting_analyst.py) | Research, reasoning, and probability estimation for a market question. | The "Standard" use case: Predicting binary market outcomes. |
| [custom_sentiment_workflow](file:///workspace/forecast/examples/kit/pipelines/custom_sentiment_workflow/run_custom_sentiment_workflow.py) | Analyzing aggregate sentiment from multiple text sources. | Signal extraction from news or social media. |

### 4. Topologies (Interaction Patterns)
Different ways agents can talk to each other.

| Project | Description | Use Case |
| :--- | :--- | :--- |
| [debate_demo](file:///workspace/forecast/examples/kit/topologies/debate_demo/run_debate_demo.py) | Two agents arguing for opposing sides before a judge decides. | Reducing bias and surfacing hidden counter-arguments. |

## Categories

### [Features](file:///workspace/forecast/examples/kit/features/)
Deep dives into specific capabilities like calibration, discovery, and sensitivity analysis.

### [Pipelines](file:///workspace/forecast/examples/kit/pipelines/)
End-to-end reasoning workflows (e.g., industry analysis, geopolitical forecasting).

### [Topologies](file:///workspace/forecast/examples/kit/topologies/)
Agent interaction patterns like debate, consensus, and orchestration.
