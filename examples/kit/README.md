# Researcher Kit Examples

These examples show the high-level `xrtm-forecast` runtime surface you use once you are building directly in code.

**Quick chooser:** start with `xrtm` if you still need the released provider-free product workflow; start here once you are embedding forecasting behavior in Python.

## Start here

1. **No-key learning path**: [Provider-Free Analyst](../providers/provider_free_analyst/) — uses the deterministic provider from `xrtm`.
2. **Smallest code-first entry**: [Minimal Agent](./minimal_agent/) — a compact forecasting-agent script with an explicit model configuration.
3. **Typical end-to-end runtime path**: [Forecasting Analyst](./pipelines/forecasting_analyst/) — research, reasoning, and probability estimation for a market question.

## Example catalog

### Fundamental agents
| Project | Description | Use case |
| :--- | :--- | :--- |
| [Minimal Agent](./minimal_agent/) | Smallest forecasting-agent script with explicit model setup. | Learn the runtime shape before adding tools or orchestration. |
| [Local Analyst](./local_analyst/) | Demonstrates using local LLMs (for example via Ollama or LocalAI) instead of hosted APIs. | Cost-sensitive or privacy-first deployments. |
| [Fact Checker Demo](./agents/fact_checker_demo/) | An agent that verifies claims against tools. | Auditing sources and checking contentious statements. |

### Features
| Project | Description | Use case |
| :--- | :--- | :--- |
| [Discovery](./features/discovery/) | Automated information retrieval and expansive search. | When the agent needs to learn a topic from scratch. |
| [Sensitivity Analysis](./features/sensitivity_analysis/) | Tests how a forecast changes with different assumptions. | Robustness checks and scenario planning. |
| [Streaming Demo](./features/streaming_demo/) | Handles streamed token responses for UI feedback. | Building chat interfaces or real-time dashboards. |
| [Structured Telemetry](./features/structured_telemetry/) | Emits JSON logs for observability tools. | Production monitoring and debugging. |
| [Tiered Reasoning](./features/tiered_reasoning/) | Escalates reasoning depth based on the task. | Balance speed against deeper analysis. |

### Pipelines
| Project | Description | Use case |
| :--- | :--- | :--- |
| [Forecasting Analyst](./pipelines/forecasting_analyst/) | Research, reasoning, and probability estimation for a market question. | The standard forecasting runtime workflow. |
| [Custom Sentiment Workflow](./pipelines/custom_sentiment_workflow/) | Analyzes aggregate sentiment from multiple text sources. | Signal extraction from news or social media. |

### Topologies
| Project | Description | Use case |
| :--- | :--- | :--- |
| [Debate Demo](./topologies/debate_demo/) | Two agents argue for opposing sides before a judge decides. | Reduce bias and surface hidden counter-arguments. |
| [Consensus Demo](./topologies/consensus_demo/) | Multiple agents converge on a shared answer. | Compare perspectives before committing to one forecast. |

## Related indexes

- [Providers](../providers/) — provider setup, provider-free entry, and inference-layer examples
- [Features](./features/) — focused capabilities
- [Pipelines](./pipelines/) — end-to-end workflows
- [Topologies](./topologies/) — multi-agent interaction patterns
