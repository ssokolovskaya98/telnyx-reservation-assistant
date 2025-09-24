import requests

url = "https://telnyx-reservation-assistant.onrender.com/mcp"

payload = {
    "jsonrpc": "2.0",
    "id": "1",
    "method": "search_availability",
    "params": {
        "cuisine": "italian",
        "party_size": 2,
        "date": "2025-09-25",
        "time": "19:00:00"
    }
}

response = requests.post(url, json=payload)
print(response.json())
