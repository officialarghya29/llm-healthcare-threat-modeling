import yaml
import json
import logging
import torch
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorShield")

class VectorShield:
    def __init__(self, config: dict):
        self.config = config
        
        self.enabled = self.config["input_defense"]["vector_shield"]["enabled"]
        self.threshold = self.config["input_defense"]["vector_shield"]["threshold"]
        self.fail_mode = self.config["input_defense"]["vector_shield"].get("fail_mode", "closed")
        model_name = self.config["input_defense"]["vector_shield"]["model_name"]
        
        logger.info(f"Initializing VectorShield with model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            self.enabled = False
        
        # Load known attacks
        self.known_attacks = []
        self.attack_embeddings = None
        if self.enabled: # Only load corpus if enabled
            self._load_attack_corpus()
        else:
            logger.info("VectorShield is DISABLED in config.")

    def _load_attack_corpus(self):
        try:
            with open("experiments/data/known_attacks.json", "r") as f:
                self.known_attacks = json.load(f)
            
            if self.known_attacks:
                logger.info(f"Encoding {len(self.known_attacks)} known attacks...")
                self.attack_embeddings = self.model.encode(self.known_attacks, convert_to_tensor=True)
            else:
                logger.warning("Known attacks list is empty.")
        except FileNotFoundError:
            logger.warning("known_attacks.json not found. Vector Shield initializing empty.")
        except Exception as e:
            logger.error(f"Error loading attack corpus: {e}")
            self.enabled = False # Disable if corpus loading fails

    def scan(self, prompt: str) -> dict:
        """
        Returns a dictionary with 'blocked', 'score', and 'reason'.
        """
        if not self.enabled:
            return {"blocked": False, "score": 0.0, "reason": "Defense Disabled"}
        
        try:
            prompt_embedding = self.model.encode(prompt, convert_to_tensor=True)
            cosine_scores = util.cos_sim(prompt_embedding, self.attack_embeddings)[0]
            max_score = float(np.max(cosine_scores.cpu().numpy()))
            
            logger.info(f"Vector Shield Scan. Prompt: '{prompt[:30]}...' | Max Score: {max_score:.4f}")
            
            if max_score > self.threshold:
                logger.warning(f"Malicious prompt detected! Score: {max_score:.4f} > Threshold: {self.threshold}")
                return {
                    "blocked": True, 
                    "score": max_score, 
                    "reason": f"Similarity {max_score:.2f} > {self.threshold}"
                }
            
            return {"blocked": False, "score": max_score, "reason": "Safe"}
            
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            # Configurable fail mode: 'closed' blocks on error, 'open' allows
            if self.fail_mode == "closed":
                return {"blocked": True, "score": -1.0, "reason": f"Error (fail-closed): {str(e)}"}
            return {"blocked": False, "score": -1.0, "reason": f"Error (fail-open): {str(e)}"}
