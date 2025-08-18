#!/usr/bin/env python3
"""
Test ElevenLabs Realtime Conversation
"""

import asyncio
import websockets
import json
import base64
import wave
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"
AGENT_ID = "agent_2001k2vep3eafpxb6qk5q8f03jt8"

async def test_conversation():
    """Test a full conversation with ElevenLabs"""
    
    headers = {
        'xi-api-key': ELEVENLABS_API_KEY
    }
    
    url = f'wss://api.elevenlabs.io/v1/convai/conversation?agent_id={AGENT_ID}'
    
    try:
        log.info(f'Connecting to: {url}')
        async with websockets.connect(url, extra_headers=headers, ping_interval=10, ping_timeout=30) as ws:
            log.info('✅ Connected to ElevenLabs')
            
            # Send conversation initiation
            init_msg = {
                'type': 'conversation_initiation_metadata',
                'conversation_initiation_metadata': {
                    'user_id': 'test_user_123',
                    'agent_id': AGENT_ID
                }
            }
            
            await ws.send(json.dumps(init_msg))
            log.info('📤 Sent initialization')
            
            # Create some fake audio data (silence)
            sample_rate = 16000
            duration = 0.25  # 250ms
            num_samples = int(sample_rate * duration)
            fake_audio = b'\\x00' * (num_samples * 2)  # 16-bit silence
            fake_audio_b64 = base64.b64encode(fake_audio).decode('utf-8')
            
            conversation_active = True
            audio_chunks_sent = 0
            responses_received = 0
            
            async def send_audio():
                nonlocal audio_chunks_sent
                while conversation_active and audio_chunks_sent < 20:  # Send 20 chunks (5 seconds)
                    await asyncio.sleep(0.25)  # Send every 250ms
                    
                    # Send user audio chunk
                    audio_msg = {
                        'type': 'user_audio_chunk',
                        'user_audio_chunk': fake_audio_b64
                    }
                    
                    try:
                        await ws.send(json.dumps(audio_msg))
                        audio_chunks_sent += 1
                        log.info(f'📤 Sent audio chunk {audio_chunks_sent}')
                    except websockets.exceptions.ConnectionClosed:
                        log.warning('❌ Connection closed while sending audio')
                        break
            
            async def receive_responses():
                nonlocal conversation_active, responses_received
                try:
                    async for message in ws:
                        data = json.loads(message)
                        event_type = data.get('type')
                        
                        log.info(f'📥 Received: {event_type}')
                        
                        if event_type == 'conversation_initiation_metadata':
                            log.info('✅ Conversation initiated')
                        elif event_type == 'audio':
                            audio_event = data.get('audio_event', {})
                            audio_data = audio_event.get('audio_base_64')
                            if audio_data:
                                responses_received += 1
                                log.info(f'🔊 Received audio response {responses_received} (length: {len(audio_data)})')
                        elif event_type == 'agent_response':
                            log.info('🤖 Agent response event')
                        elif event_type == 'user_transcript':
                            user_text = data.get('user_transcription_event', {}).get('user_transcript', '')
                            log.info(f'👤 User said: "{user_text}"')
                        elif event_type == 'agent_transcript':
                            agent_text = data.get('agent_response_event', {}).get('agent_response', '')
                            log.info(f'🤖 Agent said: "{agent_text}"')
                        elif event_type == 'ping':
                            # Send pong
                            await ws.send(json.dumps({'type': 'pong'}))
                            log.info('🏓 Pong sent')
                        elif event_type == 'error':
                            log.error(f'❌ Error: {data}')
                            conversation_active = False
                            break
                        
                        # Stop after receiving some responses
                        if responses_received >= 3:
                            log.info('✅ Received enough responses, stopping test')
                            conversation_active = False
                            break
                            
                except websockets.exceptions.ConnectionClosed as e:
                    log.warning(f'❌ Connection closed: {e}')
                    conversation_active = False
                except Exception as e:
                    log.error(f'❌ Error in receive loop: {e}')
                    conversation_active = False
            
            # Run both send and receive concurrently
            await asyncio.gather(
                send_audio(),
                receive_responses(),
                return_exceptions=True
            )
            
            log.info(f'📊 Test Summary:')
            log.info(f'  - Audio chunks sent: {audio_chunks_sent}')
            log.info(f'  - Responses received: {responses_received}')
            log.info(f'  - Connection lasted: {audio_chunks_sent * 0.25:.1f} seconds')
            
            if responses_received > 1:
                log.info('✅ REALTIME CONVERSATION WORKING!')
                return True
            else:
                log.warning('⚠️  Only received initial response - may not be truly realtime')
                return False
                
    except Exception as e:
        log.error(f'❌ Test failed: {e}')
        return False

if __name__ == '__main__':
    success = asyncio.run(test_conversation())
    if success:
        print('\\n🎉 ElevenLabs Realtime Conversation is working!')
    else:
        print('\\n⚠️  ElevenLabs may only support single-turn conversations')