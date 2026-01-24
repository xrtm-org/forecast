# Merkle Sovereignty (Truth Protocol)

The **Truth Protocol** provides cryptographic guarantees that reasoning traces have not been tampered with. This is essential for institutional trust, regulatory compliance, and scientific reproducibility.

## The Problem: The Madoff Risk

A backtest is just a text file. Anyone can edit `results.csv` and change a loss to a win.

For an AI agent to manage institutional capital, its "thought process" must be as **immutable as a blockchain transaction**.

> **Regulatory Context**: The SEC's 2025 Examination Priorities explicitly target "AI-powered investment algorithms" and demand "comprehensive, tamper-evident audit trails."

## The Solution: Merkle-ized Reasoning

`xrtm-forecast` implements a Merkle tree structure where each reasoning step is cryptographically linked to all previous steps.

### How It Works

```
Step 1: Research → Hash(State₁)
                        ↓
Step 2: Analysis → Hash(State₂ + Hash₁)
                        ↓
Step 3: Synthesis → Hash(State₃ + Hash₂)
                        ↓
Final Hash = Tamper-evident proof of entire chain
```

If anyone modifies Step 1 after the fact, the entire hash chain breaks.

### Usage

```python
from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.bundling import ManifestBundler

# Run your reasoning graph
orchestrator = Orchestrator()
# ... add nodes and edges ...
final_state = await orchestrator.run(initial_state)

# Bundle into a verifiable research proof
manifest = ManifestBundler.bundle(final_state)
ManifestBundler.write_to_file(manifest, "research_proof.xrtm")
```

### Verification

```python
from xrtm.forecast.core.verification import SovereigntyVerifier

# Anyone can verify the proof independently
is_valid = SovereigntyVerifier.verify_file("research_proof.xrtm")
# Returns True if chain is intact, False if tampered
```

## The `.xrtm` Format

The Sovereign Bundle is a portable, self-contained research proof:

```json
{
  "version": "1.0",
  "engine": "xrtm-forecast 0.4.0",
  "timestamp": "2026-01-15T14:30:00Z",
  "subject_id": "fed_rate_decision",
  "final_state_hash": "sha256:abc123...",
  "reasoning_trace": { ... },
  "execution_path": ["research", "analysis", "synthesis"],
  "telemetry": { "latencies": {...}, "usage": {...} }
}
```

## Trade-offs

| Aspect | Consideration |
| :--- | :--- |
| **Storage** | Hash chains grow with graph depth (~32 bytes per step) |
| **Performance** | SHA-256 computation adds ~1ms overhead per step |
| **Mitigation** | Configure to hash only "significant reasoning events" |

## Related Concepts

- [Orchestration](orchestration.md) — Where Merkle hashing is integrated
- [Temporal Integrity](temporal_integrity.md) — Ensuring the inputs are also valid
