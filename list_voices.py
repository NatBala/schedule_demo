#!/usr/bin/env python3
"""
List available ElevenLabs voices
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

async def list_voices():
    """List all available ElevenLabs voices"""
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.elevenlabs.io/v1/voices", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    voices = data.get('voices', [])
                    log.info(f"📋 Found {len(voices)} voices:")
                    
                    for voice in voices:
                        voice_id = voice.get('voice_id')
                        name = voice.get('name')
                        category = voice.get('category', 'unknown')
                        gender = voice.get('labels', {}).get('gender', 'unknown')
                        age = voice.get('labels', {}).get('age', 'unknown')
                        accent = voice.get('labels', {}).get('accent', 'unknown')
                        description = voice.get('description', 'No description')
                        
                        log.info(f"  🎤 {name} ({gender}, {age})")
                        log.info(f"      ID: {voice_id}")
                        log.info(f"      Category: {category}")
                        log.info(f"      Accent: {accent}")
                        log.info(f"      Description: {description[:100]}...")
                        print()
                    
                    return voices
                else:
                    error_text = await response.text()
                    log.error(f"❌ Failed to list voices: {response.status}")
                    log.error(f"Error response: {error_text}")
                    return []
                    
    except Exception as e:
        log.error(f"❌ Error listing voices: {e}")
        return []

async def main():
    """Main function"""
    log.info("🚀 ElevenLabs Voice Listing")
    log.info("=" * 40)
    
    voices = await list_voices()
    
    if voices:
        log.info("🎯 Good voice options for professional sales:")
        for voice in voices:
            if voice.get('labels', {}).get('gender') == 'female':
                name = voice.get('name')
                accent = voice.get('labels', {}).get('accent', 'unknown')
                if 'american' in accent.lower() or 'british' in accent.lower():
                    log.info(f"  ✨ {name} - {voice.get('voice_id')} ({accent})")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("👋 Interrupted by user")
    except Exception as e:
        log.error(f"❌ Failed: {e}")