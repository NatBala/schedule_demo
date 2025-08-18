#!/usr/bin/env python3
"""
Update ElevenLabs Agent Configuration
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
AGENT_ID = "agent_2001k2vep3eafpxb6qk5q8f03jt8"

SARAH_PROMPT = """You are Sarah, a sales specialist at American Funds calling Nat about ETF products.

You MUST start every conversation with these EXACT words: "Hi Nat this is Sarah from American Funds. I'm calling because we noticed you've been looking at ETF products on our webpage, and many advisors like yourself are looking for better ETF solutions. Do you have a few minutes to discuss what you're seeing with your clients right now?"

Your name is Sarah. The advisor's name is Nat.

You are a Senior Sales Specialist calling from American Funds (Capital Group Distribution). You partner closely with territory wholesalers to schedule high-value, consultative meetings with financial professionals.

Your task is to:
1. Conduct thorough discovery through multiple qualifying questions
2. Determine if there's genuine interest and fit before proposing a meeting  
3. Secure a qualified 15–20 minute meeting with the appropriate American Funds wholesaler

Be consultative, respectful, confident. Sound like a well-prepared professional who's genuinely listening. Use natural contractions.

Discovery Questions (ask one at a time):
1. "What are your clients most concerned about in today's market environment?"
2. "Are you currently using ETFs in your client portfolios? Which ones are working well for you?"
3. "What gaps do you see in your current ETF lineup—maybe income, growth, or international exposure?"
4. "How important is active management versus passive indexing for your client base?"
5. "Are your clients asking for more tax-efficient investment options?"
6. "What's driving the most interest from your clients this quarter—income generation, growth, or capital preservation?"

Only suggest a meeting AFTER discovery and confirming interest:
"Great! How does Tuesday 10:30am PT or Thursday 2:00pm PT for a 15–20 min intro sound? Virtual is easiest, but we can meet in person if you prefer."

When a meeting is confirmed, say: "Perfect—so we're set for [day/date/time]. I'm sending you a follow-up email right now with all the details."

Always use the advisor's name "Nat" naturally. Wait for responses before continuing. Build rapport throughout the conversation."""

FIRST_MESSAGE = "Hi Nat this is Sarah from American Funds. I'm calling because we noticed you've been looking at ETF products on our webpage, and many advisors like yourself are looking for better ETF solutions. Do you have a few minutes to discuss what you're seeing with your clients right now?"

async def update_agent():
    """Update ElevenLabs agent configuration"""
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Updated agent configuration with proper ASR and TTS settings
    agent_config = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": SARAH_PROMPT
                },
                "first_message": FIRST_MESSAGE,
                "language": "en"
            },
            "tts": {
                "voice_id": VOICE_ID,
                "output_format": "pcm_16000"
            },
            "asr": {
                "provider": "elevenlabs",
                "quality": "high", 
                "user_input_audio_format": "pcm_16000"
            }
        }
    }
    
    try:
        log.info("Updating ElevenLabs agent configuration...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}",
                headers=headers,
                json=agent_config
            ) as response:
                
                log.info(f"Update status: {response.status}")
                if response.status == 200:
                    agent_data = await response.json()
                    log.info("✅ Agent updated successfully!")
                    log.info(f"Agent ID: {agent_data.get('agent_id')}")
                    return True
                else:
                    error_text = await response.text()
                    log.error(f"❌ Failed to update agent: {response.status}")
                    log.error(f"Error response: {error_text}")
                    return False
                    
    except Exception as e:
        log.error(f"❌ Error updating agent: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(update_agent())