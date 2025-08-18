#!/usr/bin/env python3
"""
Create an ElevenLabs Conversational AI Agent
"""

import asyncio
import aiohttp
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Configuration
ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah - Professional female voice with confident and warm tone

# Sales Specialist Prompt
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

async def create_agent():
    """Create an ElevenLabs Conversational AI agent"""
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Agent configuration with correct 16kHz format
    agent_config = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": SARAH_PROMPT
                },
                "first_message": "Hi Nat this is Sarah from American Funds. I'm calling because we noticed you've been looking at ETF products on our webpage, and many advisors like yourself are looking for better ETF solutions. Do you have a few minutes to discuss what you're seeing with your clients right now?",
                "language": "en"
            },
            "tts": {
                "voice_id": VOICE_ID,
                "output_format": "pcm_16000"  # 16kHz format
            }
        }
    }
    
    try:
        log.info("Creating ElevenLabs Conversational AI agent...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.elevenlabs.io/v1/convai/agents/create",
                headers=headers,
                json=agent_config
            ) as response:
                
                if response.status == 200:
                    agent_data = await response.json()
                    agent_id = agent_data.get("agent_id")
                    log.info(f"✅ Agent created successfully!")
                    log.info(f"🆔 Agent ID: {agent_id}")
                    log.info(f"📝 Agent Name: {agent_data.get('name')}")
                    
                    # Save agent ID to a file for use in the app
                    with open("elevenlabs_agent_id.txt", "w") as f:
                        f.write(agent_id)
                    log.info(f"💾 Agent ID saved to elevenlabs_agent_id.txt")
                    
                    return agent_id
                else:
                    error_text = await response.text()
                    log.error(f"❌ Failed to create agent: {response.status}")
                    log.error(f"Error response: {error_text}")
                    return None
                    
    except Exception as e:
        log.error(f"❌ Error creating agent: {e}")
        return None

async def list_agents():
    """List existing agents"""
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        log.info("Listing existing ElevenLabs agents...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.elevenlabs.io/v1/convai/agents",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    agents = data.get("agents", [])
                    log.info(f"📋 Found {len(agents)} existing agents:")
                    
                    for agent in agents:
                        log.info(f"  🤖 {agent.get('name')} (ID: {agent.get('agent_id')})")
                    
                    return agents
                else:
                    error_text = await response.text()
                    log.error(f"❌ Failed to list agents: {response.status}")
                    log.error(f"Error response: {error_text}")
                    return []
                    
    except Exception as e:
        log.error(f"❌ Error listing agents: {e}")
        return []

async def main():
    """Main function"""
    log.info("🚀 ElevenLabs Agent Creation")
    log.info("=" * 40)
    
    # First, list existing agents
    existing_agents = await list_agents()
    print()
    
    # Check if we already have a Sarah agent
    sarah_agents = [a for a in existing_agents if "Sarah" in a.get("name", "")]
    
    if sarah_agents:
        log.info("🔍 Found existing Sarah agent(s):")
        for agent in sarah_agents:
            log.info(f"  Using existing agent: {agent.get('name')} (ID: {agent.get('agent_id')})")
            # Save the first one
            with open("elevenlabs_agent_id.txt", "w") as f:
                f.write(agent.get('agent_id'))
            log.info(f"💾 Agent ID saved to elevenlabs_agent_id.txt")
        return
    
    # Create new agent
    log.info("🆕 Creating new Sarah agent...")
    agent_id = await create_agent()
    
    if agent_id:
        log.info(f"🎉 Ready to use agent: {agent_id}")
    else:
        log.error("❌ Failed to create agent")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("👋 Interrupted by user")
    except Exception as e:
        log.error(f"❌ Failed: {e}")