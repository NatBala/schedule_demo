#!/usr/bin/env python3
"""
Test ElevenLabs API directly to ensure it's working
"""

import requests
import json

# Configuration
ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"

# Load agent ID
try:
    with open("elevenlabs_agent_id.txt", "r") as f:
        ELEVENLABS_AGENT_ID = f.read().strip()
        print(f"✅ Agent ID loaded: {ELEVENLABS_AGENT_ID}")
except FileNotFoundError:
    print("❌ Agent ID file not found")
    exit(1)

def test_api_key():
    """Test if API key is valid"""
    print("\n🔍 Testing API key...")
    
    url = "https://api.elevenlabs.io/v1/user"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ API key valid. User: {user_data.get('user', {}).get('email', 'Unknown')}")
            return True
        else:
            print(f"❌ API key invalid. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

def test_agent():
    """Test if agent exists and is accessible"""
    print("\n🔍 Testing agent...")
    
    # Try to get agent info
    url = f"https://api.elevenlabs.io/v1/convai/agents/{ELEVENLABS_AGENT_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            agent_data = response.json()
            print(f"✅ Agent found: {agent_data.get('name', 'Unknown')}")
            return True
        else:
            print(f"⚠️ Agent endpoint returned: {response.status_code}")
            # This might be normal - the agent might exist but this endpoint might not be public
            return None
    except Exception as e:
        print(f"⚠️ Could not check agent directly: {e}")
        return None

def test_token_generation():
    """Test getting a conversation token"""
    print("\n🔍 Testing token generation...")
    
    url = f"https://api.elevenlabs.io/v1/convai/conversation/token?agent_id={ELEVENLABS_AGENT_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        print(f"📡 Requesting token from: {url}")
        response = requests.get(url, headers=headers)
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📡 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token', '')
            if token:
                print(f"✅ Token generated successfully!")
                print(f"   Token preview: {token[:50]}...")
                return True
            else:
                print(f"❌ No token in response: {data}")
                return False
        else:
            print(f"❌ Token generation failed. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating token: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_init():
    """Test initializing a conversation"""
    print("\n🔍 Testing conversation initialization...")
    
    # First get a token
    url = f"https://api.elevenlabs.io/v1/convai/conversation/token?agent_id={ELEVENLABS_AGENT_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Could not get token for conversation test")
            return False
            
        token = response.json().get('token')
        print(f"✅ Got token for conversation test")
        
        # The actual WebSocket connection would be done by the JavaScript client
        # We can't fully test it here, but getting a token is the key part
        print(f"✅ Token is ready for client-side connection")
        print(f"ℹ️ The client will use this token to establish WebRTC connection")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing conversation: {e}")
        return False

def main():
    print("="*60)
    print("ELEVENLABS API TEST")
    print("="*60)
    
    # Test API key
    if not test_api_key():
        print("\n❌ API key is invalid. Check your key.")
        return
    
    # Test agent (might not have direct API access)
    test_agent()
    
    # Test token generation - this is the critical part
    if not test_token_generation():
        print("\n❌ Token generation failed. This is required for the client.")
        print("\nPossible issues:")
        print("1. Agent ID might be incorrect")
        print("2. Agent might not be properly configured")
        print("3. API key might not have conversation permissions")
        return
    
    # Test conversation initialization
    test_conversation_init()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\n✅ API is working! The server should be able to provide tokens.")
    print("\nIf the client still shows 'Failed to fetch', check:")
    print("1. Is the server running? (python elevenlabs_integrated_server.py)")
    print("2. Is the URL correct? (http://localhost:5052)")
    print("3. Are there any browser console errors? (Press F12)")

if __name__ == "__main__":
    main()