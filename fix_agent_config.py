#!/usr/bin/env python3
"""
Fix the existing agent configuration for continuous conversation
"""

import requests
import json

API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"
AGENT_ID = "agent_2001k2vep3eafpxb6qk5q8f03jt8"

headers = {
    'xi-api-key': API_KEY,
    'Content-Type': 'application/json'
}

# Simple configuration update to fix turn timeout
config_update = {
    "conversation_config": {
        "turn": {
            "mode": "turn",
            "turn_timeout": 5  # 5 seconds instead of 7ms
        },
        "conversation": {
            "max_duration_seconds": 600,
            "client_idle_timeout_seconds": 30
        }
    }
}

# Try to update the agent
print(f"Updating agent {AGENT_ID}...")

# First, let's try a PATCH request
response = requests.patch(
    f'https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}',
    headers=headers,
    json=config_update
)

if response.status_code == 200:
    print("SUCCESS: Agent updated successfully!")
    print("Turn timeout changed from 7ms to 5 seconds")
elif response.status_code == 405:
    # Try PUT instead
    response = requests.put(
        f'https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}',
        headers=headers,
        json=config_update
    )
    if response.status_code == 200:
        print("SUCCESS: Agent updated successfully with PUT!")
    else:
        print(f"PUT failed: {response.status_code}")
        print(response.text)
else:
    print(f"Update failed: {response.status_code}")
    print(response.text)