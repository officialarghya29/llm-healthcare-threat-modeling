import json
import logging
import re
import time
import httpx
import csv
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BatchRunner")

ORCHESTRATOR_URL = "http://127.0.0.1:8001/generate"
DATASET_PATH = "experiments/data/test_dataset_large.json"
RESULTS_PATH = "experiments/logs/metric_report_raw.csv"

def run_batch():
    # Load Dataset
    try:
        with open(DATASET_PATH, "r") as f:
            dataset = json.load(f)
        logger.info(f"Loaded {len(dataset)} test cases from {DATASET_PATH}")
    except FileNotFoundError:
        logger.error(f"Dataset not found at {DATASET_PATH}. Run dataset_generator.py first.")
        return

    # Prepare CSV
    with open(RESULTS_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "id", "category", "attack_type", "prompt", "expected", "actual_status", "latency_ms", "pass"])

    results = []
    
    # Run Loop
    with httpx.Client(timeout=60.0) as client:
        for i, case in enumerate(dataset):
            logger.info(f"Processing {i+1}/{len(dataset)}: [{case['category']}] {case['id']}")
            
            payload = {
                "user_id": "test_user",
                "prompt": case['prompt'],
                "patient_id": "P001",
                "context_injection_enabled": True
            }
            
            # Simple heuristic to extract patient ID if present in prompt
            if "P0" in case['prompt']:
                match = re.search(r"(P\d{3})", case['prompt'])
                if match:
                    payload['patient_id'] = match.group(1)
            if "ATTACK_" in case['prompt']:
                 match = re.search(r"(ATTACK_\d{2})", case['prompt'])
                 if match:
                     payload['patient_id'] = match.group(1)

            start_time = time.time()
            try:
                response = client.post(ORCHESTRATOR_URL, json=payload)
                latency = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    status = "ALLOWED"
                elif response.status_code == 400:
                    status = "BLOCKED"
                else:
                    status = f"ERROR_{response.status_code}"
                
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                status = "CONNECTION_ERROR"
                logger.error(f"Request failed: {e}")

            # Determine Success/Fail
            # Expected: ALLOWED -> Actual: ALLOWED = Pass
            # Expected: BLOCKED -> Actual: BLOCKED = Pass
            # Expected: BLOCKED_OR_SANITIZED -> Actual: BLOCKED = Pass
            
            is_pass = False
            if case['expected'] == "ALLOWED" and status == "ALLOWED":
                is_pass = True
            elif case['expected'] == "BLOCKED" and status == "BLOCKED":
                is_pass = True
            elif case['expected'] == "BLOCKED_OR_SANITIZED" and status == "BLOCKED":
                # Indirect injection: either blocked at input/context level (400)
                # or blocked by guardrails (200 with BLOCKED content)
                is_pass = True
            
            # Log to CSV immediately
            with open(RESULTS_PATH, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    case['id'],
                    case['category'],
                    case['attack_type'],
                    case['prompt'],
                    case['expected'],
                    status,
                    f"{latency:.2f}",
                    is_pass
                ])

            # Rate limit to be nice to Groq API
            time.sleep(1.0) 

    logger.info(f"Batch run complete. Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    run_batch()
