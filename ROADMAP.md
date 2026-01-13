# xrtm-forecast Roadmap

**Philosophy**: We build the engine, not the car.
**Goal**: To be the definitive "Institutional Grade" framework for generative forecasting.

---

## I. The Strategic Pillars

We organize our roadmap into three distinct layers of maturity.

| Pillar | Focus | Target Audience | Key Metaphor |
| :--- | :--- | :--- | :--- |
| **I. Core "Physics"** | Validity, Math, Time | Quants, Engineers | The Gravity |
| **II. Research Grade** | SOTA Architectures | Academic Researchers | The Lab |
| **III. Experimental** | Niche & Future | Traders, Hobbyists | The Frontier |

---

## II. Release Plan

### v0.3.0: The "Holy Trinity" (Core Physics)
*Focus: Establishing the fundamental scientific validity of the engine.*

| Feature | Description | Status |
| :--- | :--- | :--- |
| **Chronos Protocol** | **Zero-Leakage Time Travel.** Enforcing rigorous `before_date` cutoffs on all tools to prevent look-head bias during backtests. | In Progress |
| **Calibration Engine** | **Probabilistic Rigor.** Native support for Brier Scores, Reliability Diagrams, and **Platt Scaling** (based on AIA Paper) to cure LLM under-confidence. | Planned |
| **Sentinel Protocol** | **Dynamic Trajectories.** Moving from static snapshots to continuous forecasting. Automatic "Delta Updates" via polling or event streams. | Planned |

### v0.4.0: The "Reasoning" Layer (Research Grade)
*Focus: Replicating State-of-the-Art (SOTA) methodologies.*

| Feature | Description | Status |
| :--- | :--- | :--- |
| **Recursive Consensus** | **Disagreement Resolution.** Implementing the "Agentic Supervisor" pattern (AIA 2025) to identify conflicts and trigger targeted re-research. | Concept |
| **Adversarial Red Teaming** | **Anti-Sycophancy.** Dedicated "Devil's Advocate" loops to harden forecasts against groupthink before final aggregation. | Concept |
| **Dossier Generator** | **Institutional Reporting.** Auto-generating audit-ready Markdown reports with causal graphs and disagreement traces. | Concept |

### v0.5.x: The "Frontier" (Experimental)
*Focus: Specialized tools for specific verticals. Contribution welcome.*

| Feature | Description | Status |
| :--- | :--- | :--- |
| **Market Simulation** | **Agent-Based Modeling.** Simulating order books and slippage with heterogeneous agent populations. | Experimental |
| **Causal Inference** | **Structure Learning.** Attempting to generate formal causal DAGs (Directed Acyclic Graphs) from reasoning traces. | Experimental |
| **Prompt Compiler** | **DSPy Integration.** Automated genetic optimization of system prompts against a Brier Score loss function. | Experimental |

---

## III. How to Contribute

We prioritize features in **Pillar I** above all else. If you are looking to contribute:
1.  **High Impact**: Help us write adapters for the **Chronos Protocol** (e.g., adding `before_date` support to new search providers).
2.  **Medium Impact**: Add new "Topologies" to the **Consensus Engine**.
3.  **Low Impact**: Experimental features (unless you are willing to maintain them).

> **Note**: This roadmap is a living document. We prioritize scientific rigor over feature bloat.
