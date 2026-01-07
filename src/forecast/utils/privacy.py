from typing import Any, Dict


class Anonymizer:
    def scrub_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Basic pass-through for now
        return data

redactor = Anonymizer()
