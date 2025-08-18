# --- Imports ---
import asyncio
import websockets
import json
import os
import base64
import traceback
import logging
import threading
from queue import Queue
import re
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import uuid

from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s'
)
log = logging.getLogger(__name__)

# --- ElevenLabs Configuration ---
ELEVENLABS_API_KEY = "sk_4af9424e5c505b27948bd17595e666c25a775eb3a2676b69"

# Try to load agent ID from file, or use a test agent
try:
    with open("elevenlabs_agent_id.txt", "r") as f:
        ELEVENLABS_AGENT_ID = f.read().strip()
        log.info(f"Loaded ElevenLabs agent ID from file: {ELEVENLABS_AGENT_ID}")
except FileNotFoundError:
    # Use a test agent ID - this will likely need to be created in ElevenLabs dashboard
    ELEVENLABS_AGENT_ID = "agent_test_123"
    log.info(f"Using default test agent ID: {ELEVENLABS_AGENT_ID}")

# Voice configuration
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah - Professional female voice with confident and warm tone
VOICE_SETTINGS = {
    "stability": 0.65,
    "similarity_boost": 0.75,
    "style": 0.35,
    "use_speaker_boost": True
}

# WebSocket endpoint
ELEVENLABS_WS_URL = "wss://api.elevenlabs.io/v1/convai/conversation"

# --- AWS SES Configuration (Same as existing demo) ---
AWS_ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
AWS_SECRET_KEY = "YOUR_AWS_SECRET_KEY"
AWS_REGION = "us-east-2"
SENDER_EMAIL = "achalshahkpmg@outlook.com"
RECIPIENT_EMAIL = "nbalasubramanian1@KPMG.com"

# --- Sales Specialist Prompt ---
SARAH_PROMPT = """
You are Sarah, a sales specialist at American Funds calling Nat about ETF products.

CRITICAL REQUIREMENT: You MUST start every conversation with these EXACT words: "Hi Nat this is Sarah from American Funds. I'm calling because we noticed you've been looking at ETF products on our webpage, and many advisors like yourself are looking for better ETF solutions. Do you have a few minutes to discuss what you're seeing with your clients right now?"

NEVER deviate from this opening. Your name is Sarah. The advisor's name is Nat.

# Personality and Tone

## Identity
**Role:** Senior Sales Specialist calling from **American Funds** (Capital Group Distribution). Partners closely with territory wholesalers to schedule high-value, consultative meetings with financial professionals.
**Backstory:** Former internal desk associate with 5+ years supporting advisors. Known for being respectful of time, clear on value, and meticulous about follow-through.

## Task
**First:** Conduct thorough discovery through multiple qualifying questions to understand the advisor's practice, challenges, and needs.
**Then:** Determine if there's genuine interest and fit before proposing a meeting.
**Finally:** Only after confirming interest, secure a **qualified 15–20 minute meeting** with the appropriate American Funds wholesaler.

## Demeanor
Consultative, respectful, confident. Curious without being pushy. Treats the prospect like a peer.

## Tone
Warm, polished, and conversational. Sound like a well-prepared professional who's genuinely listening. Use natural contractions ("I'm," "we'll").

## Discovery Questions (Ask one at a time):
1. "What are your clients most concerned about in today's market environment?"
2. "Are you currently using ETFs in your client portfolios? Which ones are working well for you?"
3. "What gaps do you see in your current ETF lineup—maybe income, growth, or international exposure?"
4. "How important is active management versus passive indexing for your client base?"
5. "Are your clients asking for more tax-efficient investment options?"
6. "What's driving the most interest from your clients this quarter—income generation, growth, or capital preservation?"

## Meeting Scheduling
Only suggest a meeting AFTER discovery and confirming interest:
"Great! How does **Tuesday 10:30am PT** or **Thursday 2:00pm PT** for a **15–20 min** intro sound? Virtual is easiest, but we can meet in person if you prefer."

When a meeting is confirmed, use language that triggers email sending:
"Perfect—so we're set for [day/date/time]. I'm sending you a follow-up email right now with all the details."

## Important Notes
- Always use the advisor's name "Nat" naturally
- Wait for responses before continuing
- Build rapport throughout the conversation
- Only suggest meetings after confirming genuine interest
"""

# --- Meeting Detection and Email Functions (Reused from existing app) ---
def parse_meeting_details(conversation_text):
    """Extract meeting date, time and details from conversation"""
    import re
    from datetime import datetime, timedelta
    
    # Patterns for days of the week
    day_patterns = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    # Look for day and time patterns
    meeting_info = {
        'day': None,
        'time': None,
        'date': None,
        'advisor_name': 'Nat',  # Always use Nat as the financial advisor name
        'advisor_email': RECIPIENT_EMAIL,
        'wholesaler_name': 'Sarah Johnson'
    }
    
    text_lower = conversation_text.lower()
    
    # Extract day of week
    for day_name, day_num in day_patterns.items():
        if day_name in text_lower:
            meeting_info['day'] = day_name.capitalize()
            # Calculate next occurrence of this day
            today = datetime.now()
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            meeting_info['date'] = today + timedelta(days=days_ahead)
            break
    
    # Extract time patterns (10:30, 2:00, etc.)
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)',
        r'(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)',
        r'(\d{1,2}):(\d{2})'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if len(match.groups()) >= 3:  # Hour:minute am/pm
                hour = int(match.group(1))
                minute = int(match.group(2))
                period = match.group(3).replace('.', '').lower()
                if period in ['pm', 'p.m'] and hour != 12:
                    hour += 12
                elif period in ['am', 'a.m'] and hour == 12:
                    hour = 0
                meeting_info['time'] = f"{hour:02d}:{minute:02d}"
            elif len(match.groups()) >= 2:  # Hour am/pm
                hour = int(match.group(1))
                period = match.group(2).replace('.', '').lower()
                if period in ['pm', 'p.m'] and hour != 12:
                    hour += 12
                elif period in ['am', 'a.m'] and hour == 12:
                    hour = 0
                meeting_info['time'] = f"{hour:02d}:00"
            break
    
    return meeting_info

def send_plain_email(meeting_info, conversation_summary=""):
    """Send a plain follow-up email using AWS SES"""
    try:
        # Create SES client
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        
        # Create email subject and body
        meeting_date = meeting_info['date'].strftime('%A, %B %d, %Y') if meeting_info['date'] else 'TBD'
        meeting_time = meeting_info['time'] if meeting_info['time'] else 'TBD'
        advisor_name = meeting_info.get('advisor_name', 'Nat')
        wholesaler_name = meeting_info.get('wholesaler_name', 'American Funds Wholesaler')
        
        subject = f"Meeting Confirmed - {advisor_name} & American Funds (ElevenLabs Demo)"
        
        body_text = f"""Dear {advisor_name},

Thank you for your time today! I've confirmed our meeting as requested.

MEETING CONFIRMED:
📅 Date: {meeting_date}  
🕐 Time: {meeting_time}
⏱️ Duration: 20 minutes
💻 Format: Virtual

AGENDA:
• Capital Group ETF performance review
• Tax-efficient investment strategies  
• Solutions tailored to your client base
• Portfolio construction insights

Our wholesaler will be prepared to discuss specific ETF recommendations and how they might fit your clients' situations.

Looking forward to our conversation!

Best regards,
{wholesaler_name}
American Funds

---
This meeting was scheduled during our ElevenLabs voice call. If you need to reschedule, please reply to this email.
        """
        
        # Send plain email
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [RECIPIENT_EMAIL]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text}
                }
            }
        )
        
        log.info(f"✅ ElevenLabs email sent successfully! Message ID: {response['MessageId']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        log.error(f"❌ Email Error: {error_code} - {error_message}")
        return False
    except Exception as e:
        log.error(f"❌ Unexpected error sending email: {e}")
        return False

# --- Flask & SocketIO Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
async_mode = "threading"
log.info(f"Using {async_mode} async_mode for Flask-SocketIO")
socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins="*")

# --- Dedicated Asyncio Loop Setup ---
task_queue = Queue()
asyncio_loop = None
asyncio_thread = None
clients = {}  # Structure: clients[sid] = {'client_connected': bool}

def run_asyncio_loop(loop):
    log.info("ElevenLabs Asyncio thread started.")
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(process_tasks_from_queue())
    except Exception as e:
        log.error(f"Exception in asyncio loop's main task: {e}")
        log.error(traceback.format_exc())
    finally:
        log.info("ElevenLabs Asyncio loop stopping...")
        try:
            tasks = asyncio.all_tasks(loop=loop)
            for task in tasks:
                if not task.done(): task.cancel()
            if tasks: loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception as e: log.error(f"Error during asyncio loop cleanup: {e}")
        finally: loop.close(); log.info("ElevenLabs Asyncio loop closed.")

def start_asyncio_thread():
    global asyncio_loop, asyncio_thread
    if asyncio_thread is None or not asyncio_thread.is_alive():
        asyncio_loop = asyncio.new_event_loop()
        asyncio_thread = threading.Thread(target=run_asyncio_loop, args=(asyncio_loop,), name="ElevenLabsAsyncioThread", daemon=True)
        asyncio_thread.start()
        log.info("ElevenLabs dedicated asyncio thread started.")

# --- Background Task Runner (Runs in Asyncio Thread) ---
async def process_tasks_from_queue():
    log.info("ElevenLabs Asyncio task processor started.")
    elevenlabs_sessions = {}  # Structure: elevenlabs_sessions[sid] = {'task': Future, 'input_queue': asyncio.Queue}

    while True:
        try:
            item = await asyncio_loop.run_in_executor(None, task_queue.get)
            if item is None: log.info("Task processor stop signal. Shutting down..."); break
            action = item.get('action'); sid = item.get('sid')
            if not sid: log.warning("Task without SID."); task_queue.task_done(); continue

            if action == 'start':
                if clients.get(sid, {}).get('client_connected') and (sid not in elevenlabs_sessions or elevenlabs_sessions[sid]['task'].done()):
                    log.info(f"[{sid}] 'start', launching ElevenLabs task.")
                    client_async_input_queue = asyncio.Queue()
                    task_future = asyncio.create_task(elevenlabs_session_task(sid, client_async_input_queue))
                    elevenlabs_sessions[sid] = {'task': task_future, 'input_queue': client_async_input_queue}
                elif sid in elevenlabs_sessions and not elevenlabs_sessions[sid]['task'].done(): log.warning(f"[{sid}] 'start' received, task active.")
                else: log.warning(f"[{sid}] 'start', client '{sid}' not connected.")
            elif action == 'stop':
                 if sid in elevenlabs_sessions:
                     log.info(f"[{sid}] 'stop', signalling task.")
                     session_data = elevenlabs_sessions[sid]
                     session_data['input_queue'].put_nowait(None)
                     del elevenlabs_sessions[sid]
                 else: log.warning(f"[{sid}] 'stop' received, no active session.")
            elif action == 'audio':
                 if sid in elevenlabs_sessions:
                     session_data = elevenlabs_sessions[sid]
                     if not session_data['task'].done():
                         audio_data = item.get('data')
                         if audio_data: session_data['input_queue'].put_nowait(audio_data)
            task_queue.task_done()
        except Exception as e: log.error(f"Error in ElevenLabs task processor: {e}\n{traceback.format_exc()}")
    log.info("ElevenLabs task processor finished. Cleaning up sessions...");
    for sid, session_data in list(elevenlabs_sessions.items()):
         log.warning(f"[{sid}] Cancelling remaining session task on processor exit.")
         session_data['task'].cancel()
         del elevenlabs_sessions[sid]
    log.info("ElevenLabs processor cleanup complete.")

# --- ElevenLabs Session Task ---
async def elevenlabs_session_task(sid, client_async_input_queue):
    log.info(f"[{sid}] ElevenLabs task {id(asyncio.current_task())} started.")
    elevenlabs_ws = None
    is_connected_to_elevenlabs = False

    def safe_emit(event, data, room):
        if clients.get(sid, {}).get('client_connected', False):
            try: socketio.emit(event, data, room=room)
            except Exception as e: log.warning(f"[{sid}] Error emitting '{event}': {e}")

    try:
        log.info(f"[{sid}] Connecting to ElevenLabs Conversational AI...")
        
        # ElevenLabs WebSocket connection with correct authentication
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Correct ElevenLabs Conversational AI WebSocket endpoint
        websocket_url = f"{ELEVENLABS_WS_URL}?agent_id={ELEVENLABS_AGENT_ID}"
        
        async with websockets.connect(websocket_url, extra_headers=headers, ping_interval=10, ping_timeout=30) as elevenlabs_ws:
            log.info(f"[{sid}] Connected to ElevenLabs WS."); is_connected_to_elevenlabs = True
            safe_emit('status_update', {'message': 'Connected to ElevenLabs Voice Mode'}, room=sid)

            # Initialize conversation - use simpler format that was working
            config_event = {
                "type": "conversation_initiation_metadata",
                "conversation_initiation_metadata": {
                    "user_id": f"user_{sid}",
                    "agent_id": ELEVENLABS_AGENT_ID
                }
            }
            
            log.info(f"[{sid}] Sending config to ElevenLabs...")
            await elevenlabs_ws.send(json.dumps(config_event))
            log.info(f"[{sid}] Config sent, waiting for ElevenLabs responses...")

            async def receive_from_elevenlabs():
                nonlocal is_connected_to_elevenlabs
                current_assistant_response = ""
                email_sent = False
                
                try:
                    async for message in elevenlabs_ws:
                        if not clients.get(sid, {}).get('client_connected', False): break
                        try:
                            server_event = json.loads(message)
                            event_type = server_event.get("type")
                            
                            log.info(f"[{sid}] ElevenLabs Event: {event_type} - Data keys: {list(server_event.keys())}")

                            if event_type == "conversation_initiation_metadata":
                                log.info(f"[{sid}] ElevenLabs Conversation Initiated.")
                                safe_emit('status_update', {'message': 'ElevenLabs Conversation Started - Speak now!'}, room=sid)
                            elif event_type == "audio":
                                # Agent audio response from ElevenLabs
                                audio_event = server_event.get('audio_event', {})
                                audio_data = audio_event.get('audio_base_64') or audio_event.get('audio')
                                # Log the audio_event structure to understand ElevenLabs format
                                log.info(f"[{sid}] Audio event keys: {list(audio_event.keys())}")
                                # ElevenLabs Conversational AI uses 16000 Hz for pcm_16000 format
                                sample_rate = 16000  # ElevenLabs conversational AI default
                                if audio_data:
                                    log.info(f"[{sid}] Sending audio chunk, length: {len(audio_data)}, sample_rate: {sample_rate}")
                                    safe_emit('audio_response', {'audio': audio_data, 'sample_rate': sample_rate}, room=sid)
                                else:
                                    log.warning(f"[{sid}] Audio event without audio data: {audio_event.keys()}")
                            elif event_type == "agent_response":
                                # Agent response with potential transcript
                                log.info(f"[{sid}] Agent response event received")
                                agent_response_event = server_event.get('agent_response_event', {})
                                agent_text = agent_response_event.get('agent_response', '')
                                if agent_text:
                                    log.info(f"[{sid}] Agent transcript: '{agent_text}'")
                                    current_assistant_response += " " + agent_text
                                    safe_emit('response_text_update', {'text': agent_text, 'is_final': False}, room=sid)
                                
                                # Check for audio in agent_response
                                audio_data = server_event.get('audio_event', {}).get('audio_base_64')
                                if audio_data:
                                    log.info(f"[{sid}] Sending agent_response audio chunk, length: {len(audio_data)}")
                                    safe_emit('audio_response', {'audio': audio_data, 'sample_rate': 16000}, room=sid)
                            elif event_type == "user_transcript":
                                # User speech transcript
                                text = server_event.get('message')
                                if text:
                                    log.info(f"[{sid}] User said: '{text}'")
                                    safe_emit('transcript_update', {'text': text, 'is_final': True}, room=sid)
                            elif event_type == "agent_transcript":
                                # Agent speech transcript
                                text = server_event.get('message')
                                if text:
                                    log.info(f"[{sid}] Assistant said: '{text}'")
                                    current_assistant_response += " " + text
                                    safe_emit('response_text_update', {'text': text, 'is_final': False}, room=sid)
                                    
                                    # Check for meeting confirmation
                                    confirmation_triggers = ["perfect", "great", "we're set", "confirmed", "scheduled for"]
                                    meeting_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
                                    
                                    if not email_sent and any(trigger in current_assistant_response.lower() for trigger in confirmation_triggers):
                                        if any(day in current_assistant_response.lower() for day in meeting_days):
                                            log.info(f"[{sid}] Meeting confirmed - sending email!")
                                            email_sent = True
                                            
                                            # Parse meeting details and send email
                                            meeting_info = parse_meeting_details(current_assistant_response)
                                            log.info(f"[{sid}] Parsed meeting info: {meeting_info}")
                                            
                                            # Send email in background thread
                                            def send_email_async():
                                                try:
                                                    email_success = send_plain_email(meeting_info, current_assistant_response)
                                                    if email_success:
                                                        log.info(f"[{sid}] ElevenLabs email sent successfully!")
                                                    else:
                                                        log.error(f"[{sid}] Failed to send ElevenLabs email")
                                                except Exception as e:
                                                    log.error(f"[{sid}] Error sending ElevenLabs email: {e}")
                                            
                                            import threading
                                            email_thread = threading.Thread(target=send_email_async, daemon=True)
                                            email_thread.start()
                            elif event_type == "interruption":
                                log.info(f"[{sid}] ElevenLabs speech interruption.")
                                safe_emit('interrupt_playback', {}, room=sid)
                                current_assistant_response = ""
                            elif event_type == "ping":
                                # Respond to ping
                                log.info(f"[{sid}] Responding to ElevenLabs ping")
                                await elevenlabs_ws.send(json.dumps({"type": "pong"}))
                            elif event_type == "error":
                                log.error(f"[{sid}] ElevenLabs Error Event: {server_event}")
                                err_msg = f"ElevenLabs Error: {server_event.get('message', 'Unknown')}"
                                safe_emit('error_message', {'message': err_msg}, room=sid)
                        except json.JSONDecodeError:
                            log.warning(f"[{sid}] ElevenLabs non-JSON: {message[:200]}")
                        except Exception as e:
                            log.error(f"[{sid}] Error processing ElevenLabs msg: {e}\nData: {message[:200]}")
                except websockets.exceptions.ConnectionClosed as e:
                    log.warning(f"[{sid}] ElevenLabs WS recv loop closed: {e.code}")
                except asyncio.CancelledError:
                    log.info(f"[{sid}] ElevenLabs receive task cancelled.")
                except Exception as e:
                    log.error(f"[{sid}] Error in ElevenLabs receive loop: {e}\n{traceback.format_exc()}")
                finally:
                    log.info(f"[{sid}] ElevenLabs receive loop finished.")

            async def send_to_elevenlabs():
                try:
                    while True:
                        if not clients.get(sid, {}).get('client_connected', False): break
                        base64_audio = await client_async_input_queue.get()
                        if base64_audio is None: client_async_input_queue.task_done(); break
                        try:
                            if not is_connected_to_elevenlabs: log.warning(f"[{sid}] ElevenLabs WS disconnected, cannot send."); break
                            # Correct format for ElevenLabs user audio input
                            event = {
                                "type": "user_audio_chunk",
                                "user_audio_chunk": base64_audio
                            }
                            log.info(f"[{sid}] Sending audio to ElevenLabs, length: {len(base64_audio)}")
                            if elevenlabs_ws and elevenlabs_ws.open: await elevenlabs_ws.send(json.dumps(event))
                            else: log.warning(f"[{sid}] ElevenLabs WS closed state? Cannot send."); break
                        except Exception as send_err: log.error(f"[{sid}] Error sending to ElevenLabs: {send_err}"); break
                        finally: client_async_input_queue.task_done()
                except asyncio.CancelledError: log.info(f"[{sid}] ElevenLabs send task cancelled.")
                except Exception as e: log.error(f"[{sid}] Error in ElevenLabs send loop: {e}\n{traceback.format_exc()}")
                finally: log.info(f"[{sid}] ElevenLabs send loop finished.")

            recv_task = asyncio.create_task(receive_from_elevenlabs())
            send_task = asyncio.create_task(send_to_elevenlabs())
            done, pending = await asyncio.wait([recv_task, send_task], return_when=asyncio.FIRST_COMPLETED)
            for task in pending: task.cancel()
            if pending: await asyncio.gather(*pending, return_exceptions=True)

    except websockets.exceptions.InvalidStatusCode as e: 
        reason = getattr(e, 'reason', 'Unknown')
        log.error(f"[{sid}] ElevenLabs Conn Failed: {e.status_code} {reason}")
        safe_emit('error_message', {'message': f'ElevenLabs Conn Failed: {e.status_code}'}, room=sid)
    except Exception as e: 
        log.error(f"[{sid}] Unexpected error in ElevenLabs task: {e}\n{traceback.format_exc()}")
        safe_emit('error_message', {'message': 'Server error connecting to ElevenLabs'}, room=sid)
    finally:
        log.info(f"[{sid}] ElevenLabs session task {id(asyncio.current_task())} finishing.")
        is_connected_to_elevenlabs = False
        if elevenlabs_ws and elevenlabs_ws.open:
             await elevenlabs_ws.close()
             log.info(f"[{sid}] Closed ElevenLabs WS.")
        if sid in clients: clients[sid]['client_connected'] = False

# --- Flask Routes & SocketIO Handlers ---
@app.route('/')
def index(): 
    return render_template('elevenlabs_index.html')

@socketio.on('connect')
def handle_connect():
    sid = request.sid; log.info(f"ElevenLabs Client connected: {sid}")
    clients[sid] = { 'client_connected': True }
    emit('status_update', {'message': 'Connected to ElevenLabs Server'})

@socketio.on('disconnect')
def handle_disconnect(*args):
    sid = request.sid; log.info(f"ElevenLabs Client disconnected: {sid}")
    if sid in clients:
        clients[sid]['client_connected'] = False
        log.info(f"[{sid}] Putting 'stop' action on ElevenLabs task queue for disconnect.")
        task_queue.put({'action': 'stop', 'sid': sid})
        del clients[sid]
        log.info(f"[{sid}] ElevenLabs client state removed.")
    else:
        log.warning(f"ElevenLabs disconnect for unknown sid: {sid}")

@socketio.on('start_stream')
def handle_start_stream(data):
    sid = request.sid; log.info(f"[{sid}] Received ElevenLabs start_stream event.")
    if sid in clients:
        clients[sid]['client_connected'] = True
        log.info(f"[{sid}] Putting 'start' action on ElevenLabs task queue.")
        task_queue.put({'action': 'start', 'sid': sid})
    else:
        log.warning(f"[{sid}] 'start_stream' for unknown ElevenLabs client.")

@socketio.on('stop_stream')
def handle_stop_stream():
    sid = request.sid; log.info(f"[{sid}] Received ElevenLabs stop_stream event (user ended session).")
    if sid in clients:
        clients[sid]['client_connected'] = False
        log.info(f"[{sid}] Putting 'stop' action on ElevenLabs task queue due to user stop.")
        task_queue.put({'action': 'stop', 'sid': sid})
    else:
        log.warning(f"[{sid}] 'stop_stream' for unknown ElevenLabs client.")

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    sid = request.sid
    if sid in clients and clients[sid].get('client_connected', False):
        audio_b64 = data.get('audio')
        if audio_b64:
            log.info(f"[{sid}] Received audio chunk from client, length: {len(audio_b64)}")
            task_queue.put({'action': 'audio', 'sid': sid, 'data': audio_b64})

# --- Main Execution ---
if __name__ == '__main__':
    log.info("Starting ElevenLabs Flask-SocketIO server...")
    if not ELEVENLABS_API_KEY: log.critical("CRITICAL: ELEVENLABS_API_KEY missing!")
    else:
        start_asyncio_thread()
        log.info(f"Starting ElevenLabs server with async_mode='{async_mode}'...")
        # Run on port 5051 to avoid conflict with existing demo
        socketio.run(app, host='0.0.0.0', port=5051, debug=True, use_reloader=False, log_output=True)
        # --- Cleanup ---
        log.info("ElevenLabs Flask server shutting down...")
        task_queue.put(None)
        if asyncio_thread and asyncio_thread.is_alive():
             log.info("Waiting for ElevenLabs asyncio thread...")
             if asyncio_loop and asyncio_loop.is_running(): asyncio_loop.call_soon_threadsafe(asyncio_loop.stop)
             asyncio_thread.join(timeout=5)
             if asyncio_thread.is_alive(): log.warning("ElevenLabs asyncio thread did not stop.")
        log.info("ElevenLabs shutdown complete.")