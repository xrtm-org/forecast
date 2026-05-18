# Merkle Sovereignty (Truth Protocol)

The Truth Protocol provides cryptographic guarantees that reasoning traces and execution traces have not been tampered with.

## The problem: the Madoff risk

A backtest is just a text file. Anyone can edit `results.csv` and change a loss to a win.

For an AI agent to manage institutional capital, its recorded decision process must be tamper evident.

> **Regulatory Context**: The SEC's 2025 Examination Priorities explicitly target AI-powered investment algorithms and demand comprehensive, tamper-evident audit trails.

## The solution: Merkle-linked run state

`xrtm-forecast` links each execution-graph state to the prior state with a Merkle-style hash chain.

### How it works

```
Step 1: Research  → Hash(State₁)
                        ↓
Step 2: Analysis  → Hash(State₂ + Hash₁)
                        ↓
Step 3: Synthesis → Hash(State₃ + Hash₂)
                        ↓
Final Hash = tamper-evident proof of the whole run
```

If anyone modifies an earlier step after the fact, the final hash no longer verifies.

### Usage

```python
from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.bundling import ManifestBundler

# Run your execution graph.
orchestrator = Orchestrator()
# ... add nodes and edges ...
final_state = await orchestrator.run(initial_state)

manifest = ManifestBundler.bundle(final_state)
ManifestBundler.write_to_file(manifest, "research_proof.xrtm")
```

### Verification

```python
from xrtm.forecast.core.verification import SovereigntyVerifier

is_valid = SovereigntyVerifier.verify_file("research_proof.xrtm")
```

## The `.xrtm` format

The sovereign bundle is a portable, self-contained research proof:

```json
{
  "version": "1.0",
  "engine": "xrtm-forecast 0.4.0",
  "timestamp": "2026-01-15T14:30:00Z",
  "subject_id": "fed_rate_decision",
  "final_state_hash": "sha256:abc123...",
  "reasoning_trace": { ... },
  "execution_trace": ["research", "analysis", "synthesis"],
  "execution_path": ["research", "analysis", "synthesis"],
  "telemetry": {"latencies": {...}, "usage": {...}}
}
```

`execution_trace` is the preferred user-facing field. `execution_path` remains as a compatibility alias for older consumers.

## Trade-offs

| Aspect | Consideration |
| :--- | :--- |
| **Storage** | Hash chains grow with execution-graph depth (~32 bytes per step) |
| **Performance** | SHA-256 computation adds ~1ms overhead per step |
| **Mitigation** | Configure hashing around significant reasoning events |
