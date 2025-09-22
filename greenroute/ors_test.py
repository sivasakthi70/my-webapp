import os
import base64
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Decode ORS API key if base64-encoded JSON
def decode_ors_key(key):
    try:
        decoded = base64.b64decode(key).decode("utf-8")
        data = json.loads(decoded)
        if isinstance(data, dict) and "org" in data:
            return data["org"]
    except Exception:
        pass
    return key

ORS_API_KEY = decode_ors_key(os.getenv("ORS_API_KEY"))

if not ORS_API_KEY:
    print("❌ ORS_API_KEY not found in .env")
    exit()

print(f"✅ Using ORS key: {ORS_API_KEY}")

# Test 1: Geocoding Search (query param)
geo_url = f"https://api.openrouteservice.org/geocode/search"
geo_params = {"api_key": ORS_API_KEY, "text": "Berlin, Germany"}
geo_resp = requests.get(geo_url, params=geo_params)

print("\n🌍 Geocoding status:", geo_resp.status_code)
print("Result:", geo_resp.json())

# Test 2: Directions (Authorization header)
route_url = "https://api.openrouteservice.org/v2/directions/driving-car"
route_headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
route_body = {
    "coordinates": [[13.4050, 52.5200], [13.3777, 52.5163]]  # Berlin city points
}
route_resp = requests.post(route_url, headers=route_headers, json=route_body)

print("\n🛣️ Routing status:", route_resp.status_code)
print("Result:", route_resp.json())
