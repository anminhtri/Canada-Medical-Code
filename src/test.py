import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

data = {
    "model": "nvidia/nemotron-3-super-120b-a12b:free",
    "messages": [{"role": "user", "content": "give me your model name"}],
}

response = requests.post(url, headers=headers, json=data)
message = response.json()["choices"][0]["message"]["content"]

print(message)

with open("response.json", "w", encoding="utf-8") as f:
    json.dump(response.json(), f, indent=4, ensure_ascii=False)
