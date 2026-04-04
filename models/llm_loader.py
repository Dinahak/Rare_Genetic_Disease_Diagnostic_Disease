# models/llm_loader.py

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """
    Connects to Ollama running locally.
    Sends clinical prompts to Qwen and returns responses.
    Model is configurable via .env — swap qwen:1.8b for
    qwen:7b on a machine with more RAM, no code changes needed.
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model    = os.getenv("MODEL_NAME", "qwen:1.8b")
        self.timeout  = int(os.getenv("LLM_TIMEOUT", "120"))
        print(f"LLM client ready — model: {self.model}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a prompt to Ollama and return the response text.
        Uses the /api/chat endpoint with system + user messages.
        """
        payload = {
            "model":  self.model,
            "stream": False,
            "options": {
                "temperature":   0.3,
                "num_predict":   300,
                "stop":          ["In conclusion", "Additionally,", "\n\n\n"]
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ]
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

        except requests.exceptions.Timeout:
            return "ERROR: LLM request timed out. Try a shorter prompt or restart Ollama."
        except requests.exceptions.ConnectionError:
            return "ERROR: Cannot connect to Ollama. Run 'ollama serve' in a separate terminal."
        except Exception as e:
            return f"ERROR: {str(e)}"

    def is_available(self) -> bool:
        """Quick health check — confirms Ollama is running."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False