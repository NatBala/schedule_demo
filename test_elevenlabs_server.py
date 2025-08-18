#!/usr/bin/env python3
"""
Test script to check ElevenLabs server dependencies and basic functionality
"""

import sys
import traceback

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print("❌ requests - Run: pip install requests")
        return False
        
    try:
        import flask
        print("✅ flask")
    except ImportError as e:
        print("❌ flask - Run: pip install flask")
        return False
        
    try:
        import flask_cors
        print("✅ flask-cors")
    except ImportError as e:
        print("❌ flask-cors - Run: pip install flask-cors")
        return False
        
    try:
        import flask_socketio
        print("✅ flask-socketio")
    except ImportError as e:
        print("❌ flask-socketio - Run: pip install flask-socketio")
        return False
        
    return True

def test_agent_id():
    """Test if agent ID file exists"""
    print("\n🔍 Testing agent ID file...")
    
    try:
        with open("elevenlabs_agent_id.txt", "r") as f:
            agent_id = f.read().strip()
            print(f"✅ Agent ID found: {agent_id}")
            return True
    except FileNotFoundError:
        print("❌ elevenlabs_agent_id.txt not found")
        print("💡 Create an agent at: https://elevenlabs.io/app/conversational-ai")
        print("💡 Save the agent ID to: elevenlabs_agent_id.txt")
        return False

def test_simple_flask():
    """Test simple Flask server"""
    print("\n🔍 Testing simple Flask server...")
    
    try:
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        
        @app.route('/')
        def hello():
            return jsonify({"status": "working", "message": "ElevenLabs server test"})
            
        @app.route('/test')
        def test():
            return jsonify({"test": "passed"})
            
        print("✅ Flask app created successfully")
        print("🚀 Starting test server on port 3000...")
        print("🔗 Open: http://localhost:3000")
        print("🔗 Test: http://localhost:3000/test")
        print("⚠️ Press Ctrl+C to stop")
        
        app.run(host='0.0.0.0', port=3000, debug=True)
        
    except Exception as e:
        print(f"❌ Flask server failed: {e}")
        traceback.print_exc()
        return False

def test_app_imports():
    """Test importing from app.py"""
    print("\n🔍 Testing app.py imports...")
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import send_meeting_confirmation, parse_meeting_details
        print("✅ Successfully imported from app.py")
        return True
    except Exception as e:
        print(f"❌ Failed to import from app.py: {e}")
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("ELEVENLABS SERVER DIAGNOSTIC")
    print("="*60)
    
    # Test imports
    if not test_imports():
        print("\n❌ Missing dependencies. Install them and try again.")
        return
    
    # Test agent ID
    has_agent = test_agent_id()
    
    # Test app imports
    test_app_imports()
    
    print("\n" + "="*60)
    print("DIAGNOSTICS COMPLETE")
    print("="*60)
    
    if has_agent:
        print("✅ All checks passed. Starting simple test server...")
        test_simple_flask()
    else:
        print("❌ Please create ElevenLabs agent first")

if __name__ == "__main__":
    main()