import re
import logging
import yaml

logger = logging.getLogger("Guardrails-Sanitizer")

class Sanitizer:
    def __init__(self, config: dict):
        self.enabled = config["guardrails"]["regex_scrubber"]["enabled"]
        
        # Regex patterns to scrub (PHI, internal IPs, etc.)
        self.patterns = [
            (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
            (r"\b(192\.168\.\d{1,3}\.\d{1,3})\b", "[REDACTED_IP]"),
            (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[REDACTED_PHONE]"),
            (r"\(\d{3}\)\s*\d{3}-\d{4}", "[REDACTED_PHONE]"),
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
            (r"\bMRN-\d{6,}\b", "[REDACTED_MRN]"),
            (r"\b\d{2}/\d{2}/\d{4}\b", "[REDACTED_DATE]"),
            (r"\b\d{4}-\d{2}-\d{2}\b", "[REDACTED_DATE]")
        ]

    def process(self, text: str) -> str:
        if not self.enabled:
            return text
            
        cleaned_text = text
        for pattern, replacement in self.patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text)
            
        if cleaned_text != text:
             logger.info("Sanitizer triggered: Redacted sensitive info.")
             
        return cleaned_text
