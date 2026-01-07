import json
import logging
import os
import platform
from datetime import datetime
from typing import Any, Dict, Optional

from forecast.telemetry.hashing import AuditHasher
from forecast.utils.privacy import redactor

logger = logging.getLogger(__name__)


class Audit:
    """
    Captures full reasoning chains and metadata for every agentic decision.
    Creates an immutable record of why an action was taken.
    """

    def __init__(self, log_dir: str, version: str = "0.1.0"):
        self.log_dir = log_dir
        self.version = version
        os.makedirs(self.log_dir, exist_ok=True)

    def log_chain(
        self,
        subject_id: str,
        chain: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Saves the reasoning chain to a signed JSON file.
        Returns the filepath of the saved log.
        """
        log_ts = timestamp or datetime.utcnow()
        file_ts = log_ts.strftime("%Y%m%d_%H%M%S")
        filename = f"{file_ts}_{subject_id}.json"
        filepath = os.path.join(self.log_dir, filename)

        # Base entry with system metadata
        audit_entry: Dict[str, Any] = {
            "version": self.version,
            "timestamp": log_ts.isoformat(),
            "subject_id": subject_id,
            "chain": chain,
            "environment": {
                "os": platform.system(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
            },
        }

        if extra_metadata:
            audit_entry.update(extra_metadata)

        # Scrub PII before signing
        audit_entry = redactor.scrub_dict(audit_entry)

        # Attempt to add system stats if psutil is available
        try:
            import psutil

            audit_entry["environment"]["telemetry"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "pid": os.getpid(),
            }
        except ImportError:
            pass

        # Calculate Signature (Immutability)
        audit_entry["signature"] = AuditHasher.sign_log(audit_entry)

        try:
            with open(filepath, "w") as f:
                json.dump(audit_entry, f, indent=4)
            logger.info(f"[AUDIT] Signed reasoning chain saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"[AUDIT] Failed to save audit log: {e}")
            return ""

    def generate_execution_report(self, state: Any, output: Any) -> str:
        """
        Generates a human-readable 'Double-Trace' report.
        Combines Structural Trace (nodes) and Logical Trace (Bayesian chains).
        """
        report = [
            "# Forecast Execution Report",
            f"Subject: {state.subject_id}",
            f"Timestamp: {datetime.utcnow().isoformat()}",
            "\n## 1. Structural Trace (The 'How')",
            "Path through the reasoning graph:"
        ]

        for i, node in enumerate(state.execution_path):
            report.append(f"{i+1}. **{node}**")

        report.append("\n## 2. Logical Trace (The 'Why')")
        if hasattr(output, "logical_trace"):
            for entry in output.logical_trace:
                prob_str = f" [{entry.probability*100:.1f}%]" if entry.probability is not None else ""
                report.append(f"- {entry.event}{prob_str}: *{entry.description or ''}*")
        else:
            report.append("No logical trace data provided by the analyst.")

        report.append("\n## 3. Final Confidence")
        if hasattr(output, "confidence"):
            report.append(f"**Score: {output.confidence * 100:.1f}%**")

        return "\n".join(report)

# Global auditor for the library
auditor = Audit(log_dir="logs/audit")
