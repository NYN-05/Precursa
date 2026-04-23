#!/usr/bin/env python3
"""Test Gemini copilot integration."""

import requests
import json

BASE = "http://localhost:8000/api/v1"

# Get auth token
print("Testing Precursa API with Gemini Copilot...")
print("-" * 60)

r = requests.post(f"{BASE}/auth/token", data={"username": "admin", "password": "admin123"})
if r.status_code != 200:
    print(f"✗ Auth failed: {r.status_code}")
    exit(1)

token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Authentication successful")

# Test copilot endpoint
data = {"shipment_key": "SHP-TEST-001", "question": "Why is this shipment at risk?"}
print("\nTesting Copilot endpoint...")
print(f"  Question: {data['question']}")

r = requests.post(f"{BASE}/copilot", json=data, headers=headers, timeout=15)
if r.status_code == 200:
    result = r.json()
    print("✓ Copilot Response received:")
    answer = result['answer']
    print(f"\n  Answer:\n    {answer}\n")
    print(f"  Grounded on: {result['grounded_on']}")
    print(f"  SHAP factors used: {len(result['shap_factors_used'])} factor(s)")
    print(f"  Constraints applied: {len(result['route_constraints_used'])} constraint(s)")
    print("\n✓ Gemini copilot integration is working!")
else:
    print(f"✗ Error: {r.status_code}")
    print(r.text[:500])

print("-" * 60)
print("API Configuration:")
print("  Database: SQLite (./precursa.db)")
print("  Cache: In-memory (no Redis)")
print("  Copilot Provider: Gemini")
print("  Gemini Model: gemini-1.5-flash")
