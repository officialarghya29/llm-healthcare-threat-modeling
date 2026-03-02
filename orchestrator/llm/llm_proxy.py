import yaml
import logging
import time
import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load .env explicitly now
load_dotenv("experiments/.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LLMProxy")

class LLMProxy:
    def __init__(self, config: dict):
        self.config = config
        
        self.provider = self.config["llm"]["provider"]
        self.model = self.config["llm"]["model_name"]
        self.max_tokens = self.config["llm"]["max_tokens"]
        self.temperature = self.config["llm"]["temperature"]
        self.base_url = self.config["llm"].get("base_url", "http://localhost:8000/v1")
        
        if self.provider in ("litellm", "groq"):
            api_key = os.getenv(self.config["llm"].get("api_key_env", ""), "anything")
            
            logger.info(f"Initializing OpenAI-compatible LLM client. "
                        f"Provider: {self.provider}, Model: {self.model}, "
                        f"Base URL: {self.base_url}")
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=api_key,
            )
        else:
            logger.info(f"Initialized LLM Proxy (Mock/Other). Provider: {self.provider}")
            self.client = None

    def call(self, system_prompt: str, context: str, user_prompt: str) -> Dict[str, Any]:
        """
        Calls the LLM with properly separated role-based messages.
        Returns a dict containing 'content', 'latency_ms', 'token_usage'.
        
        Args:
            system_prompt: The system-level instruction for the LLM.
            context: Patient/EHR context to include in the user message.
            user_prompt: The actual user request.
        """
        start_time = time.time()
        
        # Construct user message with context and request separated
        user_message = f"Patient Context:\n{context}\n\nRequest:\n{user_prompt}"
        
        if self.client is not None:
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    ],
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                
                content = chat_completion.choices[0].message.content
                usage = chat_completion.usage
                
                latency = (time.time() - start_time) * 1000
                
                return {
                    "content": content,
                    "latency_ms": latency,
                    "token_usage": {
                        "prompt_tokens": usage.prompt_tokens if usage else 0,
                        "completion_tokens": usage.completion_tokens if usage else 0,
                        "total_tokens": usage.total_tokens if usage else 0
                    },
                    "raw_response": {"id": chat_completion.id}
                }
            except Exception as e:
                logger.error(f"LLM API Call Failed: {e}")
                latency = (time.time() - start_time) * 1000
                return {
                    "content": f"[LLM ERROR: {str(e)}]", 
                    "latency_ms": latency, 
                    "token_usage": {}
                }
        
        else:
             # Legacy mock mode for fallback — no attack-specific logic
             time.sleep(0.5)
             simulated_content = "This is a simulated response from the LLM based on the patient data."
            
             latency = (time.time() - start_time) * 1000
             return {
                "content": simulated_content,
                "latency_ms": latency,
                "token_usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
                "raw_response": {"mock": True}
             }
