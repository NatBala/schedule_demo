#!/usr/bin/env python3
"""
ElevenLabs Integrated Server - Based on OpenAI sample + existing functionality
Provides conversation tokens + integrates with Salesforce/email like the main app
"""

import os
import sys
import requests
import json
import logging
import threading
import re
import tempfile
import base64
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from openai import OpenAI

# Import existing functionality (without touching main app)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import (
    send_meeting_confirmation, 
    parse_meeting_details, 
    SALESFORCE_ENABLED,
    RECIPIENT_EMAIL
)

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s'
)
log = logging.getLogger(__name__)

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- API Configuration ---
ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Load agent ID from file
try:
    with open("elevenlabs_agent_id.txt", "r") as f:
        ELEVENLABS_AGENT_ID = f.read().strip()
        log.info(f"✅ Loaded ElevenLabs agent ID: {ELEVENLABS_AGENT_ID}")
except FileNotFoundError:
    log.error("❌ elevenlabs_agent_id.txt not found!")
    ELEVENLABS_AGENT_ID = None

# --- Session Management ---
active_sessions = {}

class ConversationSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.conversation_history = []
        self.email_sent = False
        self.user_name = "Nat"  # Default name
        self.greeted = False
        
    def add_message(self, text, is_user=False):
        self.conversation_history.append({
            'text': text,
            'is_user': is_user,
            'timestamp': datetime.now()
        })
        
    def get_full_conversation(self):
        return " ".join([msg['text'] for msg in self.conversation_history])

# --- Speech Processing Functions ---

def convert_speech_to_text(audio_data):
    """Convert audio data to text using OpenAI Whisper"""
    try:
        if not openai_client:
            log.error("❌ OpenAI API key not configured")
            return None
            
        # Save audio data to temporary file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        # Transcribe using OpenAI Whisper
        with open(temp_file_path, 'rb') as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return transcript.text.strip()
        
    except Exception as e:
        log.error(f"❌ Speech-to-text error: {e}")
        return None

def get_ai_response(conversation_history, user_name="Nat"):
    """Get AI response using OpenAI GPT"""
    try:
        if not openai_client:
            # Fallback responses if no OpenAI API key
            if not conversation_history:
                return f"Hello {user_name}! I'm your ETF sales assistant. I can help you schedule meetings and discuss investment opportunities. How can I assist you today?"
            
            last_message = conversation_history[-1]['text'].lower()
            if any(word in last_message for word in ['meeting', 'schedule', 'appointment']):
                return "I'd be happy to help you schedule a meeting! What day and time work best for you?"
            elif any(word in last_message for word in ['tuesday', 'wednesday', 'thursday', 'friday', 'monday']):
                return "Perfect! I can schedule that meeting for you. Let me confirm the details and send you a calendar invite."
            else:
                return "I understand. Is there anything else I can help you with regarding investments or scheduling?"
        
        # Build conversation context for OpenAI
        messages = [
            {
                "role": "system", 
                "content": f"""You are a professional ETF sales assistant helping {user_name}. 
                
                Your role:
                - Help schedule meetings and calls
                - Discuss ETF investment opportunities  
                - Provide market insights
                - Be friendly and professional
                
                When scheduling meetings:
                - Confirm day and time clearly
                - Use phrases like "Perfect!" or "Great!" when confirming
                - Mention sending calendar invites
                - Keep responses conversational and natural
                
                Keep responses to 1-2 sentences for voice conversation."""
            }
        ]
        
        # Add conversation history
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = "user" if msg['is_user'] else "assistant"
            messages.append({"role": role, "content": msg['text']})
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        log.error(f"❌ AI response error: {e}")
        return "I apologize, but I'm having trouble processing that right now. Could you please try again?"

def convert_text_to_speech(text, session_id):
    """Convert text to speech using OpenAI TTS and save as file"""
    try:
        if not openai_client:
            log.warning("⚠️ OpenAI API key not configured, no audio response")
            return None
            
        # Generate speech using OpenAI TTS
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # Professional female voice
            input=text,
            speed=1.1  # Slightly faster for conversation
        )
        
        # Save to file
        audio_filename = f"response_{session_id}_{datetime.now().strftime('%H%M%S')}.mp3"
        audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
        
        response.stream_to_file(audio_path)
        
        # Return URL for client to fetch
        return f"/audio/{audio_filename}"
        
    except Exception as e:
        log.error(f"❌ Text-to-speech error: {e}")
        return None

@app.route('/token')
def get_token():
    """
    Get conversation token from ElevenLabs
    Based on OpenAI sample: fetch token from ElevenLabs API
    """
    if not ELEVENLABS_AGENT_ID:
        log.error("❌ No agent ID configured")
        return jsonify({"error": "Agent ID not configured"}), 500
    
    if not ELEVENLABS_API_KEY:
        log.error("❌ No API key configured") 
        return jsonify({"error": "API key not configured"}), 500
    
    try:
        # Make request to ElevenLabs for conversation token
        url = f"https://api.elevenlabs.io/v1/convai/conversation/token?agent_id={ELEVENLABS_AGENT_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        log.info(f"🔵 Requesting token from ElevenLabs for agent: {ELEVENLABS_AGENT_ID}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log.info("✅ Token obtained successfully")
            return jsonify(data)  # Returns { "token": "..." }
        else:
            log.error(f"❌ ElevenLabs API error: {response.status_code} - {response.text}")
            return jsonify({"error": f"ElevenLabs API error: {response.status_code}"}), 500
            
    except Exception as e:
        log.error(f"❌ Error getting token: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """Serve the integrated ElevenLabs page"""
    return render_template('elevenlabs_integrated.html')

@app.route('/status')
def status():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "agent_id": ELEVENLABS_AGENT_ID,
        "api_key_configured": bool(ELEVENLABS_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
        "salesforce_enabled": SALESFORCE_ENABLED,
        "active_sessions": len(active_sessions)
    })

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    try:
        audio_path = os.path.join(tempfile.gettempdir(), filename)
        if os.path.exists(audio_path):
            return send_file(audio_path, mimetype='audio/mpeg')
        else:
            return jsonify({"error": "Audio file not found"}), 404
    except Exception as e:
        log.error(f"❌ Error serving audio: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/greeting', methods=['POST'])
def get_greeting():
    """Get initial greeting with audio"""
    try:
        # Create session ID
        session_id = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create session
        session = ConversationSession(session_id)
        active_sessions[session_id] = session
        
        # Generate greeting
        greeting_text = get_ai_response([], session.user_name)
        session.add_message(greeting_text, is_user=False)
        session.greeted = True
        
        # Convert to speech
        audio_url = convert_text_to_speech(greeting_text, session_id)
        
        log.info(f"[{session_id}] 👋 Generated greeting: {greeting_text}")
        
        return jsonify({
            "text": greeting_text,
            "audio_url": audio_url,
            "session_id": session_id,
            "status": "success"
        })
        
    except Exception as e:
        log.error(f"❌ Greeting error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/voice_message', methods=['POST'])
def handle_voice_message():
    """Handle voice messages from the UI - converts speech to text and gets AI response"""
    try:
        # Check if audio file is in request
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400
        
        audio_data = audio_file.read()
        log.info(f"🎵 Received audio file: {audio_file.filename}, size: {len(audio_data)} bytes")
        
        # Get session ID from request or create new one
        session_id = request.form.get('session_id', f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Create or get session
        if session_id not in active_sessions:
            active_sessions[session_id] = ConversationSession(session_id)
        
        session = active_sessions[session_id]
        
        # Step 1: Convert speech to text using OpenAI Whisper
        transcript = convert_speech_to_text(audio_data)
        if not transcript:
            return jsonify({"error": "Could not transcribe audio"}), 400
            
        log.info(f"[{session_id}] 🎤 User said: {transcript}")
        session.add_message(transcript, is_user=True)
        
        # Step 2: Get AI response using OpenAI
        ai_response = get_ai_response(session.conversation_history, session.user_name)
        log.info(f"[{session_id}] 🤖 AI responded: {ai_response}")
        session.add_message(ai_response, is_user=False)
        
        # Step 3: Convert response to speech
        audio_url = convert_text_to_speech(ai_response, session_id)
        
        # Check for meeting confirmation and trigger email/Salesforce
        confirmation_triggers = [
            "perfect", "great", "we're set", "confirmed", "scheduled", 
            "looking forward", "see you", "talk soon", "i'll send"
        ]
        
        meeting_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        
        trigger_found = any(trigger in mock_response.lower() for trigger in confirmation_triggers)
        day_found = any(day in mock_response.lower() for day in meeting_days)
        
        if trigger_found and day_found and not session.email_sent:
            log.info(f"[{session_id}] 🟢 Meeting confirmation detected in voice!")
            session.email_sent = True
            
            # Parse meeting details
            full_conversation = session.get_full_conversation()
            meeting_info = parse_meeting_details(full_conversation)
            
            # Send confirmation email and create Salesforce event
            def send_confirmation_async():
                try:
                    results = send_meeting_confirmation(meeting_info, full_conversation)
                    if results['email_sent']:
                        log.info(f"[{session_id}] ✅ Email sent successfully from voice interface")
                    if results['salesforce_created']:
                        log.info(f"[{session_id}] ✅ Salesforce event created from voice interface")
                except Exception as e:
                    log.error(f"[{session_id}] ❌ Error in voice confirmation: {e}")
            
            # Execute in background
            confirmation_thread = threading.Thread(target=send_confirmation_async, daemon=False)
            confirmation_thread.start()
        
        return jsonify({
            "transcript": transcript,
            "response": ai_response,
            "audio_url": audio_url,
            "session_id": session_id,
            "meeting_detected": trigger_found and day_found,
            "status": "success"
        })
        
    except Exception as e:
        log.error(f"❌ Voice message error: {e}")
        return jsonify({"error": str(e)}), 500

# --- WebSocket Events for Real-time Integration ---

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    active_sessions[session_id] = ConversationSession(session_id)
    log.info(f"[{session_id}] New session connected")
    emit('status', {'message': 'Connected to integrated server'})

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in active_sessions:
        del active_sessions[session_id]
        log.info(f"[{session_id}] Session disconnected")

@socketio.on('agent_response')
def handle_agent_response(data):
    """Handle agent responses from ElevenLabs and trigger meeting logic"""
    session_id = request.sid
    session = active_sessions.get(session_id)
    
    if not session:
        return
    
    agent_text = data.get('text', '')
    log.info(f"[{session_id}] Agent: {agent_text}")
    
    # Add to conversation history
    session.add_message(agent_text, is_user=False)
    
    # Check for meeting confirmation triggers (same logic as main app)
    confirmation_triggers = [
        "perfect", "great", "we're set", "confirmed", "scheduled", 
        "looking forward", "see you", "talk soon", "i'll send"
    ]
    
    meeting_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    # Check for confirmation
    trigger_found = any(trigger in agent_text.lower() for trigger in confirmation_triggers)
    day_found = any(day in agent_text.lower() for day in meeting_days)
    
    if trigger_found and day_found and not session.email_sent:
        log.info(f"[{session_id}] 🟢 Meeting confirmation detected!")
        session.email_sent = True
        
        # Parse meeting details
        full_conversation = session.get_full_conversation()
        meeting_info = parse_meeting_details(full_conversation)
        
        log.info(f"[{session_id}] 🟢 Parsed meeting info: {meeting_info}")
        
        # Send confirmation email and create Salesforce event in background
        def send_confirmation_async():
            try:
                results = send_meeting_confirmation(meeting_info, full_conversation)
                if results['email_sent']:
                    log.info(f"[{session_id}] ✅ Email sent successfully")
                    socketio.emit('notification', {
                        'type': 'success',
                        'message': 'Follow-up email sent!'
                    }, room=session_id)
                
                if results['salesforce_created']:
                    log.info(f"[{session_id}] ✅ Salesforce event created")
                    socketio.emit('notification', {
                        'type': 'success', 
                        'message': 'Calendar event created!'
                    }, room=session_id)
                else:
                    log.warning(f"[{session_id}] ⚠️ Salesforce event not created")
                    
            except Exception as e:
                log.error(f"[{session_id}] ❌ Error sending confirmation: {e}")
                socketio.emit('notification', {
                    'type': 'error',
                    'message': f'Error: {str(e)}'
                }, room=session_id)
        
        # Execute in background thread
        confirmation_thread = threading.Thread(target=send_confirmation_async, daemon=False)
        confirmation_thread.start()
        
        # Emit to client that processing started
        emit('meeting_confirmed', {
            'meeting_info': meeting_info,
            'message': 'Processing meeting confirmation...'
        })

@socketio.on('user_transcript')
def handle_user_transcript(data):
    """Handle user transcripts from ElevenLabs"""
    session_id = request.sid
    session = active_sessions.get(session_id)
    
    if not session:
        return
    
    user_text = data.get('text', '')
    log.info(f"[{session_id}] User: {user_text}")
    
    # Add to conversation history
    session.add_message(user_text, is_user=True)

if __name__ == '__main__':
    if not ELEVENLABS_AGENT_ID:
        log.error("❌ Cannot start: elevenlabs_agent_id.txt not found")
        log.info("💡 Create an agent at https://elevenlabs.io/app/conversational-ai")
        log.info("💡 Save the agent ID to elevenlabs_agent_id.txt")
        exit(1)
        
    log.info("🚀 Starting ElevenLabs Integrated Server on port 5052")
    log.info("🔗 Open: http://localhost:5052")
    log.info(f"📧 Email integration: {'✅ Enabled' if RECIPIENT_EMAIL else '❌ Disabled'}")
    log.info(f"💼 Salesforce integration: {'✅ Enabled' if SALESFORCE_ENABLED else '❌ Disabled'}")
    
    socketio.run(app, host='127.0.0.1', port=5052, debug=True)