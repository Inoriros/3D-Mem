import requests

url = "http://localhost:11434/api/chat"

payload = {
    "model": "qwen2.5vl:7b",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the capital of France?"}
    ],
    "temperature": 0.7,
    "top_p": 0.95,
    "stream": False  # << disable streaming
}

response = requests.post(url, json=payload)
print(response.json()["message"]["content"])
