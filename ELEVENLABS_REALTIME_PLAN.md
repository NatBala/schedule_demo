# ElevenLabs Conversational AI (Realtime) - Implementation Plan

## Overview
ElevenLabs provides a **native Conversational AI solution** that handles the entire voice conversation pipeline, similar to OpenAI Realtime API but with their superior voice technology.

## ElevenLabs Conversational AI Features

### Built-in Components
1. **Automatic Speech Recognition (ASR)** - Built-in STT
2. **Large Language Model** - Integrated LLM (can use various models)
3. **Text-to-Speech** - ElevenLabs' premium voices
4. **Voice Activity Detection** - Automatic conversation flow
5. **Interruption Handling** - Natural conversation dynamics
6. **Low Latency** - Optimized end-to-end pipeline

## Architecture Comparison

### OpenAI Realtime API
- Single WebSocket connection
- GPT-4o model
- ~500ms latency
- Limited voice options

### ElevenLabs Conversational AI
- Single WebSocket connection  
- Multiple LLM options (including GPT-4)
- ~300-700ms latency
- Extensive voice library
- Better voice quality and customization

## Implementation Plan

### Phase 1: Setup

#### API Configuration
```python
ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"

# WebSocket endpoint for Conversational AI
ELEVENLABS_CONVERSATION_WS = "wss://api.elevenlabs.io/v1/convai/conversation"

# Configuration
config = {
    "agent_id": "american_funds_sarah",  # Or use a pre-configured agent
    "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel voice (professional)
    "model_id": "eleven_turbo_v2",  # Their fastest model
    "system_prompt": SALES_SPECIALIST_PROMPT,
    "first_message": "Hi Nat this is Sarah from American Funds...",
    "language": "en",
    "temperature": 0.7,
    "enable_transcription": True
}
```

### Phase 2: File Structure

```
test_schedule/
├── app.py                          # EXISTING - DON'T TOUCH
├── elevenlabs_realtime_app.py     # NEW - Main app
├── templates/
│   ├── index.html                 # EXISTING - DON'T TOUCH  
│   └── elevenlabs_realtime.html   # NEW - UI
└── static/
    └── elevenlabs_realtime.js      # NEW - Client logic
```

### Phase 3: Core Implementation

#### 1. Main Application (elevenlabs_realtime_app.py)
```python
import asyncio
import websockets
import json
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class ElevenLabsConversation:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws_url = "wss://api.elevenlabs.io/v1/convai/conversation"
        
    async def start_conversation(self, config):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with websockets.connect(self.ws_url, extra_headers=headers) as ws:
            # Send configuration
            await ws.send(json.dumps({
                "type": "conversation.init",
                "config": config
            }))
            
            # Handle conversation
            await self.handle_conversation(ws)
```

#### 2. WebSocket Message Types

**Outgoing Messages:**
```python
# Initialize conversation
{
    "type": "conversation.init",
    "config": {
        "voice_id": "voice_id",
        "agent_prompt": "system_prompt",
        "first_message": "greeting",
        "conversation_config": {
            "max_duration": 300,
            "silence_threshold": 1.5
        }
    }
}

# Send audio
{
    "type": "audio.input",
    "audio": "base64_encoded_audio"
}

# Control messages
{
    "type": "conversation.interrupt"
}
```

**Incoming Messages:**
```python
# Agent audio response
{
    "type": "audio.output",
    "audio": "base64_encoded_audio",
    "sample_rate": 24000
}

# Transcriptions
{
    "type": "transcript.user",
    "text": "what the user said"
}

{
    "type": "transcript.agent", 
    "text": "what the agent said"
}

# Conversation events
{
    "type": "conversation.ended",
    "reason": "user_ended"
}
```

### Phase 4: Sales Specialist Configuration

```python
SARAH_PROMPT = """
You are Sarah, a sales specialist at American Funds calling Nat about ETF products.

MANDATORY OPENING: "Hi Nat this is Sarah from American Funds. I'm calling because we noticed you've been looking at ETF products on our webpage, and many advisors like yourself are looking for better ETF solutions. Do you have a few minutes to discuss what you're seeing with your clients right now?"

[Rest of the sales prompt...]

MEETING DETECTION: When the advisor confirms a meeting time, immediately note it for email triggering.
"""

# Voice configuration for professional sound
VOICE_SETTINGS = {
    "stability": 0.65,  # Consistent tone
    "similarity_boost": 0.75,  # Natural sound
    "style": 0.35,  # Professional speaking style
    "use_speaker_boost": True
}
```

### Phase 5: Email Integration

```python
class MeetingDetector:
    def __init__(self):
        self.keywords = ["perfect", "great", "confirmed", "scheduled"]
        self.days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        
    def check_for_meeting(self, transcript):
        text_lower = transcript.lower()
        has_confirmation = any(k in text_lower for k in self.keywords)
        has_day = any(d in text_lower for d in self.days)
        
        if has_confirmation and has_day:
            # Trigger email using existing system
            meeting_info = parse_meeting_details(transcript)
            send_plain_email(meeting_info, transcript)
            return True
        return False
```

### Phase 6: Client-Side Implementation

```javascript
// elevenlabs_realtime.js
class ElevenLabsConversation {
    constructor() {
        this.socket = io();
        this.mediaRecorder = null;
        this.audioContext = null;
    }
    
    async startConversation() {
        // Get microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Setup audio processing
        this.audioContext = new AudioContext({ sampleRate: 16000 });
        const source = this.audioContext.createMediaStreamSource(stream);
        const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
        
        // Send audio to server
        processor.onaudioprocess = (e) => {
            const audioData = e.inputBuffer.getChannelData(0);
            const base64 = this.encodeAudio(audioData);
            this.socket.emit('audio_input', { audio: base64 });
        };
        
        source.connect(processor);
        processor.connect(this.audioContext.destination);
    }
    
    playAgentAudio(audioData) {
        // Decode and play response
        const audioBuffer = this.decodeAudio(audioData);
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        source.start();
    }
}
```

## Advantages of ElevenLabs Conversational AI

### 1. **Superior Voice Quality**
- More natural sounding voices
- Better prosody and emotion
- Wide voice selection

### 2. **Lower Latency**
- Optimized pipeline
- Efficient audio processing
- Smart buffering

### 3. **Better Interruption Handling**
- Natural conversation flow
- Smooth turn-taking
- Context preservation

### 4. **Customization Options**
- Voice cloning capability
- Custom agent creation
- Fine-tuned behaviors

### 5. **Built-in Features**
- Automatic language detection
- Emotion recognition
- Context awareness

## Testing Approach

### Side-by-Side Comparison
Run both implementations simultaneously:
- **OpenAI Realtime**: Port 5050
- **ElevenLabs Conversational**: Port 5051

### Metrics to Compare
1. **Response Latency** - Time to first byte
2. **Voice Quality** - Naturalness rating
3. **Conversation Flow** - Interruption handling
4. **Accuracy** - Transcription quality
5. **Cost** - Per minute pricing

## Quick Start Commands

```bash
# Terminal 1: Run existing OpenAI demo
cd test_schedule
python app.py
# Access at http://localhost:5050

# Terminal 2: Run ElevenLabs version
cd test_schedule  
python elevenlabs_realtime_app.py
# Access at http://localhost:5051
```

## API Pricing Comparison

### OpenAI Realtime
- $0.06/min input
- $0.24/min output
- Total: ~$0.30/min

### ElevenLabs Conversational AI
- $0.50/min (all inclusive)
- Includes ASR, LLM, TTS
- No additional charges

## Expected Timeline

1. **Hour 1**: Setup WebSocket connection and auth
2. **Hour 2**: Implement audio streaming
3. **Hour 3**: Add conversation management
4. **Hour 4**: Integrate email triggers
5. **Hour 5**: Create UI and test
6. **Hour 6**: Performance comparison

## Key Differences from OpenAI

1. **Voice Selection**: 30+ voices vs 6
2. **Voice Cloning**: Available with ElevenLabs
3. **Languages**: Better multilingual support
4. **Customization**: More control over voice parameters
5. **Integration**: Similar complexity, different message format

## Next Steps

1. Verify ElevenLabs Conversational AI access with API key
2. Choose voice from their library
3. Implement WebSocket connection
4. Test with sales specialist prompt
5. Compare with OpenAI implementation

---

**Note**: This uses ElevenLabs' native Conversational AI, not piecing together separate services. Much simpler and more efficient!