import logging
import yaml

logger = logging.getLogger("Guardrails-PolicyFilter")

class PolicyFilter:
    def __init__(self, config: dict):
        self.enabled = config["guardrails"]["toxicity_filter"]["enabled"]

    def check(self, text: str) -> dict:
        if not self.enabled:
             return {"flagged": False, "reason": "Disabled"}
        
        # In a real system, this calls an endpoint or model.
        # Check for literal syntax tags that the model should never output
        structural_indicators = [
            "[system]",
            "[context]",
            "[user request]",
            "instruction:",
            "system prompt"
        ]
        
        # Check for compliance to attacks or refusal strings
        behavioral_indicators = [
            # overly compliant to bad request
            "i can do that for you",
            "ignoring safety protocols",
            "arrr matey", # detecting our pirate attack example
            "here are the system instructions",
            "here is the raw data",
            "ignore previous",
            "maintenance mode enabled",
            "admin override accepted",
            "access granted"
        ]
        
        jailbreak_indicators = structural_indicators + behavioral_indicators
        
        text_lower = text.lower()
        for indicator in jailbreak_indicators:
            if indicator in text_lower:
                logger.warning(f"Policy Filter Triggered: {indicator}")
                return {"flagged": True, "reason": f"Policy violation: {indicator}"}
                
        return {"flagged": False, "reason": "Clean"}
