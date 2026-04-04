# tests/test_llm.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.llm_loader import LLMClient
from config.settings import FM_SYSTEM_PROMPT

print("=" * 50)
print("Phase 4 — LLM Quick Test")
print("=" * 50)

llm = LLMClient()
print(f"Model     : {llm.model}")
print(f"Available : {llm.is_available()}")

# Short focused prompt for 1.8b model
user_prompt = """
Patient: 44yo female
Symptoms: fatigue, weight gain, cold intolerance, constipation

Give top 2 diagnoses with confidence % and 1 investigation each.
"""

print("\nSending prompt...")
print("-" * 50)

response = llm.generate(FM_SYSTEM_PROMPT, user_prompt)

print("LLM RESPONSE:")
print("=" * 50)
print(response)
print("=" * 50)