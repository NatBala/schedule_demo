# Schedule Demo - Voice ETF Sales Assistant

A voice-enabled sales assistant application that helps American Funds specialists make outbound calls to financial advisors about Capital Group ETFs.

## Features

- **Voice-First Interface**: Real-time voice interaction using OpenAI's realtime API
- **Sales Specialist Persona**: Acts as Michael Davidson from American Funds
- **ETF Knowledge Base**: Comprehensive information about Capital Group ETFs with performance data
- **Automatic Greeting**: Proactively starts sales conversations
- **Real-time Audio**: Two-way voice communication with text transcription

## Technology Stack

- **Backend**: Python Flask with SocketIO for real-time communication
- **Frontend**: HTML5 with Web Audio API for voice processing
- **AI**: OpenAI Realtime API for voice interaction
- **Audio**: PCM16 audio processing at 24kHz

## Quick Start

1. Install dependencies:
```bash
pip install Flask Flask-SocketIO python-dotenv websockets==11.0.3
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

3. Run the application:
```bash
python app.py
```

4. Open your browser to `http://localhost:5050`

## Usage

1. Click the microphone button to start the sales call
2. The AI will automatically begin with: "Hi there! This is Michael Davidson calling from American Funds..."
3. Have a natural conversation about ETF opportunities
4. The system provides detailed ETF performance data and sales talking points

## ETF Information

The system includes comprehensive data on Capital Group ETFs including:
- CGUS: Core Equity ETF (29.43% 1-year return)
- CGGR: Growth ETF (27.33% 1-year return)  
- CGDV: Dividend Value ETF (17.67% 1-year return)
- And many more with real performance metrics

## Configuration

- Voice model: OpenAI's Alloy voice
- Audio format: PCM16 at 24kHz
- Turn detection: Server-side voice activity detection
- Response generation: Automatic with interrupt capability

## Development

The application is structured as:
- `app.py`: Main Flask application with WebSocket handling
- `templates/index.html`: Frontend interface with voice controls
- `corpus.txt`: ETF knowledge base and sales content

## License

This is a demonstration application for educational purposes.