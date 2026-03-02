import json
import logging
import time
import hashlib
import yaml
from pathlib import Path

logger = logging.getLogger("AuditLogger")

class AuditLogger:
    def __init__(self, config: dict):
        self.log_path = Path(config["logging"]["audit_log_path"])
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Audit Logger initialized. Writing to {self.log_path}")

    def log_event(self, event_type: str, details: dict):
        """
        Logs a structured event with a timestamp and hash of the content for integrity.
        """
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "details": details
        }
        
        # Calculate integrity hash of details
        details_str = json.dumps(details, sort_keys=True)
        entry["hash"] = hashlib.sha256(details_str.encode()).hexdigest()
        
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
