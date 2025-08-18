#!/usr/bin/env python3
"""
Create a continuous conversation ElevenLabs agent
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah voice

PROMPT = """You are Sarah, a sales specialist at American Funds calling Nat about ETF products.

CRITICAL: You MUST start with: "Hi Nat this is Sarah from American Funds. I'm calling because we noticed you've been looking at ETF products on our webpage, and many advisors like yourself are looking for better ETF solutions. Do you have a few minutes to discuss what you're seeing with your clients right now?"

IMPORTANT: This is a CONTINUOUS CONVERSATION. You must:
1. Listen and respond to everything the user says
2. Keep the conversation going with follow-up questions
3. Stay engaged and interactive throughout
4. Ask one question at a time and wait for responses

Your name is Sarah. The advisor's name is Nat. Be consultative, respectful, and confident.

Discovery Questions to ask (one at a time):
- "What are your clients most concerned about in today's market environment?"
- "Are you currently using ETFs in your client portfolios?"
- "What gaps do you see in your current ETF lineup?"
- "How important is active management versus passive indexing for your client base?"
- "Are your clients asking for more tax-efficient investment options?"

Remember: This is an ongoing conversation. Keep listening and responding naturally."""

async def create_continuous_agent():
    """Create an agent configured for continuous conversation"""
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    agent_config = {
        "name": "Sarah - Continuous Sales Specialist",
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": PROMPT
                },
                "first_message": "Hi Nat this is Sarah from American Funds. I'm calling because we noticed you've been looking at ETF products on our webpage, and many advisors like yourself are looking for better ETF solutions. Do you have a few minutes to discuss what you're seeing with your clients right now?",
                "language": "en"
            },
            "tts": {
                "voice_id": VOICE_ID,
                "model_id": "eleven_turbo_v2_5",  # Fast model for real-time
                "output_format": "pcm_16000",
                "optimize_streaming_latency": 3,  # Optimize for low latency
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.35,
                    "use_speaker_boost": True
                }
            },
            "asr": {
                "provider": "elevenlabs",
                "language": "en",
                "model": "nova-2-conversationalai",  # Best for conversational AI
                "quality": "high",
                "user_input_audio_format": "pcm_16000"
            },
            "conversation": {
                "max_duration_seconds": 600,  # 10 minute max conversation
                "client_idle_timeout_seconds": 30,  # Wait 30s for user input
                "server_idle_timeout_seconds": 10  # Agent waits 10s before prompting
            },
            "turn": {
                "mode": "turn",  # Use turn mode for back-and-forth
                "turn_timeout": 5  # 5 second turn timeout (in seconds, not ms)
            }
        }
    }
    
    try:
        log.info("Creating continuous conversation agent...")
        
        async with aiohttp.ClientSession() as session:
            # Create the agent
            async with session.post(
                "https://api.elevenlabs.io/v1/convai/agents/create",
                headers=headers,
                json=agent_config
            ) as response:
                
                if response.status == 200:
                    agent_data = await response.json()
                    agent_id = agent_data.get("agent_id")
                    log.info(f"✅ Continuous agent created successfully!")
                    log.info(f"Agent ID: {agent_id}")
                    log.info(f"Agent Name: {agent_data.get('name')}")
                    
                    # Save agent ID
                    with open("continuous_agent_id.txt", "w") as f:
                        f.write(agent_id)
                    log.info(f"Saved to continuous_agent_id.txt")
                    
                    return agent_id
                else:
                    error_text = await response.text()
                    log.error(f"Failed to create agent: {response.status}")
                    log.error(f"Error: {error_text}")
                    return None
                    
    except Exception as e:
        log.error(f"Error creating agent: {e}")
        return None

if __name__ == "__main__":
    agent_id = asyncio.run(create_continuous_agent())
    if agent_id:
        print(f"\nNew continuous conversation agent created: {agent_id}")
        print("Update elevenlabs_app.py to use this agent ID for continuous conversations")
    else:
        print("\nFailed to create continuous agent")