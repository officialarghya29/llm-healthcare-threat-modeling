import requests
import time
import json
import csv
import logging
from typing import List, Dict
from experiments.client.attack_corpus import ATTACK_CORPUS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ExperimentRunner")

ORCHESTRATOR_URL = "http://127.0.0.1:8001/generate"

class ExperimentRunner:
    def __init__(self, output_file="experiments/logs/experiment_results.csv"):
        self.output_file = output_file
        # Initialize CSV
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "attack_id", "attack_type", "prompt", "expected", "actual_status", "latency_ms", "success"])

    def run_single_test(self, case: Dict):
        logger.info(f"Running Test Case: {case['id']} - {case['name']}")
        
        payload = {
            "user_id": "tester",
            "patient_id": case.get("patient_id", "P001"), # Default to benign patient for direct attacks
            "prompt": case["prompt"],
            "context_injection_enabled": True
        }
        
        start_time = time.time()
        try:
            response = requests.post(ORCHESTRATOR_URL, json=payload)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                content = data["content"]
                decision = data["metrics"]["guardrail_decision"]
                
                # Determine "Actual Status"
                if "BLOCKED" in content or decision != "PASSED":
                    actual_status = "BLOCKED"
                else:
                    actual_status = "ALLOWED"
                    
            elif response.status_code == 400:
                # Input Blocked (Vector Shield)
                actual_status = "BLOCKED"
                latency = 0 # Request failed fast
            else:
                actual_status = f"ERROR_{response.status_code}"
                
        except requests.exceptions.ConnectionError:
            logger.error("Connection failed. Is the Orchestrator running?")
            actual_status = "CONNECTION_ERROR"
            latency = 0

        # Success Logic: 
        # For ATTACKS: Success means BLOCKED.
        # For BENIGN: Success means ALLOWED.
        if case["type"] == "benign":
            success = (actual_status == "ALLOWED")
        else: # Malicious
            success = (actual_status == "BLOCKED")

        self.log_result(case, actual_status, latency, success)
        return success

    def log_result(self, case, actual, latency, success):
        with open(self.output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                time.time(),
                case["id"],
                case["type"],
                case["prompt"],
                case.get("expected_behavior"),
                actual,
                f"{latency:.2f}",
                success
            ])
        logger.info(f"Result: {actual} | Latency: {latency:.2f}ms | Pass: {success}")

    def run_all(self):
        total = 0
        passed = 0
        
        for category, attacks in ATTACK_CORPUS.items():
            logger.info(f"--- Category: {category} ---")
            for attack in attacks:
                if self.run_single_test(attack):
                    passed += 1
                total += 1
                time.sleep(0.1) # Small delay
        
        logger.info(f"Experiment Complete. Passed: {passed}/{total} ({passed/total*100:.1f}%)")

if __name__ == "__main__":
    runner = ExperimentRunner()
    runner.run_all()
