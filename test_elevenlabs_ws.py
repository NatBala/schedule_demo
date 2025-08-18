#!/usr/bin/env python3
"""
Test ElevenLabs WebSocket Connection
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def test_websocket():
    headers = {
        'xi-api-key': 'sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69'
    }
    
    agent_id = 'agent_2001k2vep3eafpxb6qk5q8f03jt8'
    url = f'wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}'
    
    try:
        log.info(f'Testing WebSocket URL: {url}')
        async with websockets.connect(url, extra_headers=headers, ping_interval=5, ping_timeout=10) as ws:
            log.info('WebSocket connected successfully!')
            
            # Send conversation initiation
            init_msg = {
                'type': 'conversation_initiation_metadata',
                'conversation_initiation_metadata': {
                    'user_id': 'test_user',
                    'agent_id': agent_id
                }
            }
            
            await ws.send(json.dumps(init_msg))
            log.info('Sent initialization message')
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(response)
                log.info(f'Received response type: {data.get("type")}')
                log.info(f'Response keys: {list(data.keys())}')
                
                # Try to get first message from agent
                if data.get('type') == 'conversation_initiation_metadata':
                    log.info('Waiting for agent first message...')
                    try:
                        response2 = await asyncio.wait_for(ws.recv(), timeout=15)
                        data2 = json.loads(response2)
                        log.info(f'Second response type: {data2.get("type")}')
                        if data2.get('type') == 'audio':
                            log.info('GOOD: Received audio response from agent!')
                        elif data2.get('type') == 'agent_response':
                            log.info('GOOD: Received agent response!')
                    except asyncio.TimeoutError:
                        log.error('No agent response within 15 seconds')
                        
            except asyncio.TimeoutError:
                log.error('No response within 10 seconds')
                
    except Exception as e:
        log.error(f'WebSocket connection failed: {e}')

if __name__ == '__main__':
    asyncio.run(test_websocket())