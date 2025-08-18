# ElevenLabs Conversational AI - Implementation Plan

## Overview
Create a parallel implementation using ElevenLabs API for voice conversation, comparing it with OpenAI Realtime API without touching the existing demo code.

## Architecture Comparison

### Current OpenAI Implementation
- **Voice Processing**: OpenAI Realtime API (WebSocket)
- **Speech-to-Text**: Built into OpenAI Realtime
- **LLM**: GPT-4 (built-in)
- **Text-to-Speech**: Built into OpenAI Realtime
- **Latency**: ~500ms end-to-end

### Proposed ElevenLabs Implementation
- **Voice Processing**: ElevenLabs WebSocket API
- **Speech-to-Text**: Need separate service (Whisper API or Web Speech API)
- **LLM**: OpenAI Chat API (GPT-4)
- **Text-to-Speech**: ElevenLabs Streaming TTS
- **Expected Latency**: Need to test

## Implementation Plan

### Phase 1: Setup & Infrastructure
1. **Create new files** (don't modify existing):
   - `elevenlabs_app.py` - Main application
   - `elevenlabs_config.py` - Configuration
   - `templates/elevenlabs_index.html` - UI
   - `elevenlabs_test.py` - Testing utilities

2. **ElevenLabs API Setup**:
   - API Key: sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69
   - Use WebSocket streaming for low latency
   - Select appropriate voice model

### Phase 2: Core Components

#### 1. Speech-to-Text Options
**Option A: Web Speech API (Browser-based)**
- Pros: Low latency, free, no API needed
- Cons: Browser compatibility, less accurate
- Implementation: JavaScript in frontend

**Option B: OpenAI Whisper API**
- Pros: High accuracy, supports many languages
- Cons: Additional API call, added latency
- Implementation: Server-side processing

**Option C: Azure Speech Services**
- Pros: Real-time streaming, good accuracy
- Cons: Additional service setup

#### 2. Text-to-Speech (ElevenLabs)
```python
# WebSocket streaming for ultra-low latency
elevenlabs_ws = "wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input"

# Configuration
voice_settings = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": True
}
```

#### 3. LLM Integration
```python
# Use OpenAI Chat API for conversation logic
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "system", "content": sales_prompt}],
    stream=True  # Stream for lower latency
)
```

### Phase 3: Conversation Flow

```
User speaks → STT → LLM → TTS → User hears
     ↓         ↓      ↓      ↓
  Browser   Whisper  GPT-4  ElevenLabs
```

### Phase 4: Features to Implement

1. **Voice Activity Detection (VAD)**
   - Client-side VAD for speech detection
   - Prevent cutting off user mid-sentence

2. **Interruption Handling**
   - Stop TTS playback when user speaks
   - Clear pending responses

3. **Conversation Context**
   - Maintain conversation history
   - Same sales specialist persona (Sarah)

4. **Email Integration**
   - Reuse existing email functionality
   - Same trigger detection logic

### Phase 5: Performance Optimizations

1. **Parallel Processing**:
   - Start TTS while LLM is still generating
   - Stream audio chunks as they arrive

2. **Caching**:
   - Cache common responses
   - Pre-generate greetings

3. **Connection Pooling**:
   - Maintain persistent WebSocket connections
   - Reduce connection overhead

## File Structure
```
test_schedule/
├── app.py                      # EXISTING - DON'T TOUCH
├── elevenlabs_app.py          # NEW - Main ElevenLabs app
├── elevenlabs_config.py       # NEW - Configuration
├── elevenlabs_test.py         # NEW - Testing
├── templates/
│   ├── index.html             # EXISTING - DON'T TOUCH
│   └── elevenlabs_index.html  # NEW - ElevenLabs UI
└── static/
    └── elevenlabs.js          # NEW - Client-side logic
```

## Technical Challenges & Solutions

### Challenge 1: Latency
- **Issue**: Multiple API calls (STT → LLM → TTS)
- **Solution**: Stream everything, parallel processing

### Challenge 2: Synchronization
- **Issue**: Coordinating multiple services
- **Solution**: Queue-based architecture with asyncio

### Challenge 3: Voice Quality
- **Issue**: Natural conversation flow
- **Solution**: Fine-tune voice settings, add prosody

## Testing Plan

1. **Latency Comparison**:
   - Measure end-to-end response time
   - Compare with OpenAI Realtime

2. **Voice Quality**:
   - Natural sound
   - Emotion/tone consistency

3. **Reliability**:
   - Connection stability
   - Error recovery

## API Costs Comparison

### OpenAI Realtime
- $0.06/minute (input)
- $0.24/minute (output)

### ElevenLabs + OpenAI Chat
- ElevenLabs: $0.30/1000 chars
- Whisper: $0.006/minute
- GPT-4: $0.03/1K tokens

## Advantages of ElevenLabs Approach

1. **Voice Customization**: More control over voice characteristics
2. **Voice Cloning**: Can clone specific voices
3. **Multiple Languages**: Better multilingual support
4. **Voice Library**: Access to diverse voice options

## Disadvantages

1. **Complexity**: Multiple services to coordinate
2. **Latency**: Potentially higher due to multiple hops
3. **Cost**: May be more expensive depending on usage
4. **Integration**: More complex error handling

## Implementation Timeline

- **Hour 1**: Setup project structure, ElevenLabs connection
- **Hour 2**: Implement STT solution
- **Hour 3**: Integrate LLM and conversation flow
- **Hour 4**: Add TTS streaming
- **Hour 5**: Test and optimize latency
- **Hour 6**: Compare with OpenAI implementation

## Success Metrics

1. **Response Latency**: < 1 second
2. **Voice Quality**: Natural and clear
3. **Conversation Flow**: Smooth and interruptible
4. **Reliability**: 99% uptime
5. **Cost Efficiency**: Comparable or better than OpenAI

## Next Steps

1. Confirm STT approach (Web API vs Whisper)
2. Select ElevenLabs voice model
3. Create base implementation
4. Run side-by-side comparison
5. Document findings

---

**Note**: This implementation will run on port 5051 (not 5050) to avoid conflicts with the existing demo.