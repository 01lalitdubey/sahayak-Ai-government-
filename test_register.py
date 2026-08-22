import urllib.request
import json
import sys

url = "http://localhost:8000/api/v1/auth/register"
data = json.dumps({
    "email": "testuser_script@gmail.com",
    "full_name": "Test User Script",
    "password": "TestPassword@123",
    "confirm_password": "TestPassword@123"
}).encode("utf-8")

headers = {
    "Content-Type": "application/json"
}

req = urllib.request.Request(url, data=data, headers=headers, method="POST")

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        print(response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode("utf-8"))
except Exception as e:
    print(f"Error: {e}")
