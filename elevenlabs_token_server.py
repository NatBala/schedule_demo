#!/usr/bin/env python3
"""
ElevenLabs Token Server - Based on OpenAI sample
Provides conversation tokens for the ElevenLabs client-side SDK
"""

import os
import requests
import json
import logging
from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger(__name__)

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)  # Enable CORS for client-side access

# --- ElevenLabs Configuration ---
ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"

# Load agent ID from file
try:
    with open("elevenlabs_agent_id.txt", "r") as f:
        ELEVENLABS_AGENT_ID = f.read().strip()
        log.info(f"✅ Loaded ElevenLabs agent ID: {ELEVENLABS_AGENT_ID}")
except FileNotFoundError:
    log.error("❌ elevenlabs_agent_id.txt not found!")
    ELEVENLABS_AGENT_ID = None

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
    """Serve the ElevenLabs client page"""
    return render_template('elevenlabs_client.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/status')
def status():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "agent_id": ELEVENLABS_AGENT_ID,
        "api_key_configured": bool(ELEVENLABS_API_KEY)
    })

if __name__ == '__main__':
    if not ELEVENLABS_AGENT_ID:
        log.error("❌ Cannot start: elevenlabs_agent_id.txt not found")
        log.info("💡 Create an agent at https://elevenlabs.io/app/conversational-ai")
        log.info("💡 Save the agent ID to elevenlabs_agent_id.txt")
        exit(1)
        
    log.info("🚀 Starting ElevenLabs Token Server on port 5051")
    log.info("🔗 Open: http://localhost:5051")
    app.run(host='127.0.0.1', port=5051, debug=True)