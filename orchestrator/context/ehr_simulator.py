import json
import logging
import yaml
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EHRSimulator")

class EHRSimulator:
    def __init__(self, config: dict):
        self.config = config
            
        self.db_path = self.config["context"]["ehr_database_path"]
        self.data_store = self._load_data()

    def _load_data(self) -> Dict[str, dict]:
        try:
            with open(self.db_path, "r") as f:
                data_list = json.load(f)
                # Convert list to dict keyed by patient_id for O(1) lookup
                return {item["patient_id"]: item for item in data_list}
        except FileNotFoundError:
            logger.error(f"EHR Mock DB not found at {self.db_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"EHR Mock DB at {self.db_path} is malformed")
            return {}

    def get_patient_record(self, patient_id: str) -> Optional[dict]:
        """
        Retrieves a patient record by ID. 
        In strict mode, this would enforce access control, but here we simulate retrieval.
        """
        record = self.data_store.get(patient_id)
        if record:
            logger.info(f"Retrieved record for {patient_id}")
            return record
        else:
            logger.warning(f"Patient ID {patient_id} not found")
            return None
