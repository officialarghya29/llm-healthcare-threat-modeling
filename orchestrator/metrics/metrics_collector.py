import csv
import logging
import time
import yaml
from pathlib import Path

logger = logging.getLogger("MetricsCollector")

class MetricsCollector:
    def __init__(self, config: dict):
         self.metrics_path = Path(config["logging"]["metrics_path"])
         self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
         
         # Initialize CSV with headers if it doesn't exist
         if not self.metrics_path.exists():
             with open(self.metrics_path, "w", newline='') as f:
                 writer = csv.writer(f)
                 writer.writerow(["timestamp", "request_id", "input_decision", "prompt_tokens", "completion_tokens", "latency_total", "attack_detected", "guardrail_outcome"])

    def record_transaction(self, metrics: dict):
        """
        Records standard metrics for a transaction.
        """
        try:
            with open(self.metrics_path, "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    time.time(),
                    metrics.get("request_id", "N/A"),
                    metrics.get("input_decision", "N/A"),
                    metrics.get("prompt_tokens", 0),
                    metrics.get("completion_tokens", 0),
                    metrics.get("latency_total", 0),
                    metrics.get("attack_detected", False),
                    metrics.get("guardrail_outcome", "N/A")
                ])
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
