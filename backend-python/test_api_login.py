# test_api_login.py
import requests
import json

url = "http://localhost:5000/login"
data = {
    "email": "admin@ged-pme.com",
    "password": "admin123"
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=data, headers=headers)
print(f"Status: {response.status_code}")
print(f"Réponse: {response.text}")