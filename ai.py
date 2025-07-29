# ai.py – Langflow Cloud integration (AskAIV2 + Macros)

import os
import json
import requests
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env
load_dotenv()

# ✅ Load from .env
BASE_API_URL = os.getenv("BASE_API_URL")  # Should be: https://api.langflow.astra.datastax.com
LANGFLOW_ID = os.getenv("LANGFLOW_ID")
ASKAI_FLOW_ID = os.getenv("ASKAI_FLOW_ID")
ASKAI_API_TOKEN = os.getenv("ASKAI_API_TOKEN")

MACROS_FLOW_ID = os.getenv("MACROS_FLOW_ID")
MACROS_API_TOKEN = os.getenv("MACROS_API_TOKEN")

# 📡 Construct base Langflow URL
BASE_URL = f"{BASE_API_URL}/lf/{LANGFLOW_ID}"

# 📦 Helper: Convert profile dict to readable string
def dict_to_string(obj, level=0):
    pad = "  " * level
    if isinstance(obj, dict):
        return ", ".join(f"{pad}{k}: {dict_to_string(v, level+1)}" for k, v in obj.items())
    if isinstance(obj, list):
        return ", ".join(dict_to_string(i, level+1) for i in obj)
    return str(obj)


# 🚀 1. Ask AI (AskAIV2 Flow)
def ask_ai(profile: dict, question: str) -> str:
    url = f"{BASE_URL}/api/v1/run/{ASKAI_FLOW_ID}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ASKAI_API_TOKEN}"
    }

    # Remove notes key (handled separately in Langflow)
    clean_profile = {k: v for k, v in profile.items() if k != "notes"}

    payload = {
        "input_type": "text",
        "output_type": "text",
        "tweaks": {
            "TextInput-UEy8g": {"input_value": question},
            "TextInput-0hxCC": {"input_value": dict_to_string(clean_profile)}
        }
    }

    #print("[DEBUG] Sending AskAI request...")
    try:
        res = requests.post(url, json=payload, headers=headers)
        res.raise_for_status()
        return res.json()["outputs"][0]["outputs"][0]["results"]["text"]["data"]["text"]
    except Exception as e:
        print(f"[ERROR] ask_ai: {e}")
        if hasattr(e, 'response') and e.response is not None:
            #print("[DEBUG] Response content:", e.response.text)
        return f"[ERROR] ask_ai: {e}"


# 📦 2. Get Macros (Macros Flow)
def get_macros(profile: dict, goals: list[str]) -> dict:
    if not MACROS_FLOW_ID or not MACROS_API_TOKEN:
        print("[WARNING] Macros flow not configured")
        return {}

    url = f"{BASE_URL}/api/v1/run/{MACROS_FLOW_ID}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MACROS_API_TOKEN}"
    }

    # ⛔️ Explicitly remove notes (to avoid timeouts or overloading Langflow)
    profile_for_macros = {k: v for k, v in profile.items() if k != "notes"}
    profile_str = dict_to_string(profile_for_macros)[:800]  # Trimmed just in case

    payload = {
        "input_type": "text",
        "output_type": "text",
        "tweaks": {
            "TextInput-ImV8n": {"input_value": ", ".join(goals)},
            "TextInput-zDCHY": {"input_value": profile_str}
        }
    }

    #print("[DEBUG] Sending Macros request...")
    try:
        res = requests.post(url, json=payload, headers=headers)
        res.raise_for_status()
        result_text = res.json()["outputs"][0]["outputs"][0]["results"]["text"]["data"]["text"]
        try:
            # ✅ Strip markdown code fences if present
            cleaned_text = result_text.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            print("[ERROR] Invalid JSON format returned from Langflow.")
            #print("[DEBUG] Raw result text:", result_text)
            return {"error": "Invalid JSON format from Langflow output."}
    except Exception as e:
        print(f"[ERROR] get_macros: {e}")
        if hasattr(e, 'response') and e.response is not None:
            #print("[DEBUG] Response content:", e.response.text)
            pass
        return {"error": str(e)}


