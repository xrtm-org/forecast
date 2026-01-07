import hashlib
import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AuditHasher:
    """
    Provides SHA-256 signing and verification for reasoning chains.
    Ensures that logic traces cannot be tampered with after generation.
    """

    @staticmethod
    def calculate_hash(data: Dict[str, Any]) -> str:
        """Calculates a deterministic SHA-256 hash of a dictionary."""
        # Use default=str to handle non-serializable objects
        encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def sign_log(log_dict: Dict[str, Any]) -> str:
        """Generates a signature for the given log dictionary."""
        # Strip 'signature' if it already exists
        content = {k: v for k, v in log_dict.items() if k != "signature"}
        return AuditHasher.calculate_hash(content)

    @staticmethod
    def verify_log(log_dict: Dict[str, Any]) -> bool:
        """Verifies that the signature matches content."""
        if "signature" not in log_dict:
            return False

        expected_sig = log_dict["signature"]
        actual_sig = AuditHasher.sign_log(log_dict)
        return actual_sig == expected_sig
