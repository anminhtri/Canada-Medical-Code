import json
import os

import requests
from dotenv import load_dotenv


def load_cci(path: str) -> str:
    if not os.path.exists(path):
        return "No CCI code file found"
    print("Loading CCICode.json\n")
    with open(path, encoding="utf-8") as f:
        cci_json = json.load(f)
        return json.dumps(cci_json)


def get_code(query: str, cci_data: str) -> str:
    api_key = os.getenv("API_KEY")
    if not api_key:
        return "No API key found in the current environment."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    system_prompt = f"""You are an expert Canadian Classification of Health Interventions (CCI) medical coding assistant. 
        I will provide you with a JSON database of parsed CCI codes. 
        Your task:
        - Search the database and find the **single most relevant CCI code** 
        that matches the user's procedure or condition query. 
        - Return **only the CCI code object** in the **exact same JSON format** as in the database, 
        including all attributes: "code", "description", "note", "code_also", "includes", "excludes".
        - **Do not provide explanations, reasoning, or any extra text.** 
        - Only return the JSON object for the best match.
        Here is the database: 
        {cci_data}"""

    data = {
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Find the CCI medical code for: {query}"},
        ],
        "n": 1,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        response_json = response.json()
        if "choices" in response_json:
            return response_json["choices"][0]["message"]["content"]
        else:
            print(response_json)
            return f"Unexpected response format: {response_json}"

    except requests.exceptions.RequestException as error:
        return f"API request failed: {error}"


if __name__ == "__main__":
    load_dotenv()
    path = "./CCICodeExample(68-100)_output.json"
    cci_data = load_cci(path)
    print("Press q to quit\n")

    while True:
        query = input("Enter medical term: ").strip()
        if query.lower() == "q":
            break

        result = get_code(query, cci_data)
        print("\n" + result + "\n")
