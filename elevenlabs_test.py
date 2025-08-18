#!/usr/bin/env python3
"""
ElevenLabs Conversational AI Test Script
"""

import asyncio
import websockets
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Configuration
ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"
ELEVENLABS_WS_URL = "wss://api.elevenlabs.io/v1/convai/conversation"

async def test_elevenlabs_connection():
    """Test basic connection to ElevenLabs Conversational AI"""
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # First, let's try to connect without agent_id to see what error we get
    try:
        log.info("Testing basic ElevenLabs WebSocket connection...")
        
        # Try connecting to the base endpoint
        async with websockets.connect(ELEVENLABS_WS_URL, extra_headers=headers) as ws:
            log.info("✅ Connected to ElevenLabs WebSocket!")
            
            # Send a test message
            test_message = {
                "type": "ping"
            }
            
            await ws.send(json.dumps(test_message))
            log.info("📤 Sent test message")
            
            # Listen for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                log.info(f"📥 Received: {response}")
            except asyncio.TimeoutError:
                log.info("⏰ No response within 5 seconds")
            
    except websockets.exceptions.InvalidStatusCode as e:
        log.error(f"❌ Connection failed with status {e.status_code}: {e.reason}")
        if hasattr(e, 'response_headers'):
            log.error(f"Response headers: {dict(e.response_headers)}")
    except Exception as e:
        log.error(f"❌ Connection failed: {e}")

async def test_with_agent_id():
    """Test connection with agent_id parameter"""
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Try with a test agent ID
    test_agent_id = "test_agent"
    url_with_agent = f"{ELEVENLABS_WS_URL}?agent_id={test_agent_id}"
    
    try:
        log.info(f"Testing ElevenLabs WebSocket with agent_id: {test_agent_id}")
        log.info(f"URL: {url_with_agent}")
        
        async with websockets.connect(url_with_agent, extra_headers=headers) as ws:
            log.info("✅ Connected to ElevenLabs WebSocket with agent_id!")
            
            # Try to start a conversation
            conversation_config = {
                "type": "conversation_initiation_metadata",
                "conversation_initiation_metadata": {
                    "user_id": "test_user_123",
                    "agent_prompt": "You are a helpful assistant named Sarah."
                }
            }
            
            await ws.send(json.dumps(conversation_config))
            log.info("📤 Sent conversation config")
            
            # Listen for responses
            for i in range(3):
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    log.info(f"📥 Response {i+1}: {response}")
                except asyncio.TimeoutError:
                    log.info(f"⏰ No response {i+1} within 5 seconds")
                    break
            
    except websockets.exceptions.InvalidStatusCode as e:
        log.error(f"❌ Connection with agent_id failed with status {e.status_code}: {e.reason}")
    except Exception as e:
        log.error(f"❌ Connection with agent_id failed: {e}")

async def test_api_key_validation():
    """Test if the API key is valid by making a simple HTTP request"""
    import aiohttp
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test with voices endpoint (should be accessible)
            async with session.get("https://api.elevenlabs.io/v1/voices", headers=headers) as response:
                if response.status == 200:
                    log.info("✅ API key is valid - can access ElevenLabs API")
                    data = await response.json()
                    log.info(f"Found {len(data.get('voices', []))} voices available")
                else:
                    log.error(f"❌ API key validation failed: {response.status}")
                    error_text = await response.text()
                    log.error(f"Error response: {error_text}")
    except Exception as e:
        log.error(f"❌ API key validation error: {e}")

async def main():
    """Run all tests"""
    log.info("🚀 Starting ElevenLabs Conversational AI Tests")
    log.info("=" * 50)
    
    # Test 1: API key validation
    log.info("Test 1: API Key Validation")
    await test_api_key_validation()
    print()
    
    # Test 2: Basic connection
    log.info("Test 2: Basic WebSocket Connection")
    await test_elevenlabs_connection()
    print()
    
    # Test 3: Connection with agent_id
    log.info("Test 3: WebSocket Connection with Agent ID")
    await test_with_agent_id()
    print()
    
    log.info("🏁 Tests completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("👋 Tests interrupted by user")
    except Exception as e:
        log.error(f"❌ Test suite failed: {e}")