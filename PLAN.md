# Voice Agent Demo Plan

## Overview
This is a complete voice-enabled sales agent for American Funds that conducts professional outbound calls to financial advisors about ETF products. The agent uses OpenAI Realtime API for natural voice conversations and automatically sends follow-up emails when meetings are scheduled.

## Key Features

### 🎯 Personalized Conversation
- **Agent Identity**: Sarah Johnson, American Funds wholesaler
- **Target Advisor**: Nat (customizable)
- **Opening Hook**: References advisor's webpage interest in ETF products
- **Professional Discovery-First Approach**: 4-6 qualifying questions before pitching

### 📧 Instant Email Delivery
- **Trigger**: Sends email immediately when meeting is confirmed (< 1 second)
- **Content**: Professional meeting confirmation with agenda
- **Personalization**: Includes advisor name and wholesaler signature
- **No Calendar Complexity**: Plain email for fast demo delivery

### 🎤 Voice Technology
- **Platform**: OpenAI Realtime API with WebSocket connection
- **Audio**: PCM16 format at 24kHz for high-quality voice
- **Interruption Handling**: Natural conversation flow with interruption support
- **Real-time**: Immediate response processing

## Demo Flow

### 1. Opening (Personalized)
**Sarah**: "Hi Nat, this is Sarah with American Funds. I'm calling because we noticed you've been looking at ETF products on our webpage, and many advisors like yourself are looking for better ETF solutions. Do you have a few minutes to discuss what you're seeing with your clients right now?"

### 2. Permission Request
- Waits for advisor response
- If YES: Proceeds to discovery
- If NO/BUSY: Offers alternative timing

### 3. Discovery Questions (Ask One at a Time)
1. "What are your clients most concerned about in today's market environment?"
2. "Are you currently using ETFs in your client portfolios? Which ones are working well for you?"
3. "What gaps do you see in your current ETF lineup—maybe income, growth, or international exposure?"
4. "How important is active management versus passive indexing for your client base?"
5. "Are your clients asking for more tax-efficient investment options?"
6. "What's driving the most interest from your clients this quarter—income generation, growth, or capital preservation?"

### 4. Rapport Building
- References webpage interest: "That's exactly what I thought you might be interested in, Nat, based on what you were looking at on our site..."
- Shares performance data when relevant: "Our CGUS has been performing really well - 29.43% over the past year"
- Shows understanding and builds connection

### 5. Interest Assessment
"Based on what you're telling me, it sounds like [summarize their needs/challenges]. This is exactly what our wholesaler specializes in helping with. Is this something you'd be open to exploring further?"

### 6. Meeting Scheduling (Only if Interested)
"Great! How does **Tuesday 10:30am PT** or **Thursday 2:00pm PT** for a **15–20 min** intro sound? Virtual is easiest, but we can meet in person if you prefer."

### 7. Confirmation & Email Trigger
"Perfect—so we're set for [day/date/time/timezone]. I'm sending you a follow-up email right now with all the details and a brief agenda. Do you have any questions, or is there anything else I can help you with before we wrap up?"

**⚡ EMAIL SENDS INSTANTLY HERE ⚡**

## Technical Architecture

### Core Components
- **Flask-SocketIO**: WebSocket server for real-time communication
- **OpenAI Realtime API**: Voice processing and conversation AI
- **AWS SES**: Email delivery system
- **Web Audio API**: Browser-based microphone and speaker access

### Email System
- **Trigger**: Real-time detection of meeting confirmation keywords
- **Speed**: < 1 second delivery via AWS SES
- **Content**: Professional meeting confirmation with agenda
- **Personalization**: Dynamic advisor/wholesaler names

### Meeting Detection
Triggers email when assistant says + day mentioned:
- "perfect" + "tuesday" → Email sent
- "great" + "thursday" → Email sent  
- "confirmed" + "friday" → Email sent
- "scheduled for" + any day → Email sent

## Setup Instructions

### 1. Environment Configuration
```bash
# Install dependencies
pip install flask flask-socketio websockets boto3 python-dotenv

# Configure AWS SES credentials (replace with your values)
AWS_ACCESS_KEY = "your_aws_access_key"
AWS_SECRET_KEY = "your_aws_secret_key" 
AWS_REGION = "us-east-2"

# Configure email addresses
SENDER_EMAIL = "your_sender@email.com"
RECIPIENT_EMAIL = "your_recipient@email.com"

# Set OpenAI API key
OPENAI_API_KEY = "your_openai_api_key"
```

### 2. Run Application
```bash
python app.py
```
Access at: http://127.0.0.1:5050

### 3. Test Email Delivery
```bash
python simple_test.py  # Test plain email delivery
```

## Demo Script

### For Live Presentation

1. **Setup**: 
   - Open http://127.0.0.1:5050 in browser
   - Ensure microphone permissions granted
   - Have email client open to show instant delivery

2. **Demo Flow**:
   - Click "Start Conversation"
   - Let Sarah give personalized opening
   - Respond positively to permission request
   - Answer 2-3 discovery questions naturally
   - Express interest in learning more
   - Confirm meeting when offered time slots
   - **Point out email arrives within 1 second**

3. **Key Demo Points**:
   - "Notice how Sarah used my name and referenced the webpage visit"
   - "She's asking discovery questions, not just pitching"
   - "Watch this - when I confirm the meeting, you'll see the email arrive instantly"
   - "This email includes all meeting details and a professional agenda"

## Customization Options

### Change Advisor Name
In `app.py`, update line 79:
```python
'advisor_name': 'YourAdvisorName',  # Change from 'Nat'
```

### Change Wholesaler Name  
In `app.py`, update line 81:
```python
'wholesaler_name': 'YourWholesalerName'  # Change from 'Sarah Johnson'
```

### Update Opening Message
In `app.py`, update lines 857:
```
MANDATORY FIRST WORDS: "Hi [Name], this is [Wholesaler] with American Funds..."
```

### Modify Discovery Questions
Update the discovery questions section in session_instructions to match your specific use case.

## File Structure

```
test_schedule/
├── app.py                  # Main application
├── corpus.txt             # ETF knowledge base  
├── templates/
│   └── index.html         # Web interface
├── simple_test.py         # Email testing script
├── test_calendar.py       # Calendar invite testing (unused in current demo)
├── verify_emails.py       # AWS SES email verification
├── .env.example           # Environment variable template
├── .gitignore            # Git ignore rules
├── README.md             # Project documentation
└── PLAN.md               # This file
```

## Troubleshooting

### Common Issues

**Email not sending:**
- Check AWS SES credentials
- Verify sender/recipient emails are verified in AWS SES
- Check if in SES sandbox mode (limits sending)

**Voice not working:**
- Ensure microphone permissions granted
- Check OpenAI API key is valid
- Verify WebSocket connection in browser console

**Wrong greeting:**
- Clear browser cache and refresh
- Restart the application
- Check session_instructions are loading correctly

**Code changes not reflecting:**
- Kill all Python processes: `powershell "Get-Process python | Stop-Process -Force"`
- Restart application completely fresh
- This is CRITICAL when updating greetings, instructions, or core functionality

### Debug Commands

```bash
# Test email delivery with timing
python simple_test.py

# Check AWS SES email verification status  
python verify_emails.py

# View application logs in real-time
python app.py  # Check console output

# Force restart when code changes aren't reflecting (IMPORTANT!)
powershell "Get-Process python | Stop-Process -Force"
python app.py
```

## Performance Metrics

- **Email Delivery**: < 1 second via AWS SES
- **Voice Response**: Near real-time with OpenAI Realtime API
- **Meeting Detection**: Instant keyword-based triggering
- **Audio Quality**: 24kHz PCM16 for professional sound

## Security Notes - LIVE DEMO READY

- **AWS credentials are HARDCODED and WORKING** in ALL files
- **OpenAI API key uses environment variable** (make sure OPENAI_API_KEY is set)  
- **Email addresses are HARDCODED and VERIFIED**
- **DEMO CONFIGURATION (WORKING):**
  - AWS Access Key: [REMOVED FOR SECURITY]
  - AWS Secret Key: [REMOVED FOR SECURITY]
  - Sender Email: achalshahkpmg@outlook.com
  - Recipient Email: nbalasubramanian1@KPMG.com
  - Region: us-east-2
  
- **FILES UPDATED:** app.py, simple_test.py, test_email.py, test_calendar.py
- **EMAIL DELIVERY:** Working - tested successfully (0.7 seconds delivery)
- Use environment variables for production deployment

## Future Enhancements

1. **Calendar Integration**: Add ICS file attachments for calendar invites
2. **CRM Integration**: Automatically log call details and outcomes  
3. **Analytics Dashboard**: Track conversion rates and call metrics
4. **Multi-Language Support**: Expand to non-English speaking advisors
5. **Custom Voice Training**: Train specific voice models for brand consistency

---

**Ready for Demo**: The application is configured for immediate use in live demonstrations with fast email delivery and professional conversation flow.