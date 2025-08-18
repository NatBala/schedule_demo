import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import uuid

# AWS credentials (REPLACE WITH YOUR OWN)
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-2"

# Email addresses (HARDCODED FOR DEMO)
SENDER = "achalshahkpmg@outlook.com"
RECIPIENT = "nbalasubramanian1@KPMG.com"

def create_test_meeting_invite():
    # Tomorrow at 10 AM
    tomorrow = datetime.now() + timedelta(days=1)
    meeting_start = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    meeting_end = meeting_start + timedelta(minutes=20)
    
    meeting_info = {
        'date': meeting_start,
        'time': '10:00',
        'day': meeting_start.strftime('%A'),
        'advisor_name': 'Test Advisor',
        'advisor_email': RECIPIENT
    }
    
    return meeting_info

def generate_ics_content(meeting_info):
    """Generate ICS calendar invite content"""
    start_datetime = meeting_info['date']
    end_datetime = start_datetime + timedelta(minutes=20)
    
    # Format for ICS
    start_utc = start_datetime.strftime('%Y%m%dT%H%M%S')
    end_utc = end_datetime.strftime('%Y%m%dT%H%M%S')
    
    uid = str(uuid.uuid4())
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//American Funds//Meeting Scheduler//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_utc}
DTEND:{end_utc}
SUMMARY:American Funds - ETF Discussion Meeting (TEST)
DESCRIPTION:Test meeting with American Funds wholesaler to discuss ETF solutions and portfolio construction strategies.
ORGANIZER:mailto:{SENDER}
ATTENDEE:mailto:{RECIPIENT}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
    
    return ics_content

def send_test_calendar_invite():
    try:
        # Create SES client
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION
        )
        
        # Create test meeting info
        meeting_info = create_test_meeting_invite()
        
        # Generate calendar invite
        ics_content = generate_ics_content(meeting_info)
        
        # Create email subject and body
        meeting_date = meeting_info['date'].strftime('%A, %B %d, %Y')
        meeting_time = meeting_info['time']
        
        subject = f"TEST - American Funds Meeting - {meeting_date} at {meeting_time}"
        
        body_text = f"""Dear {meeting_info['advisor_name']},

This is a TEST calendar invite for tomorrow at 10:00 AM.

Meeting Details:
Date: {meeting_date}
Time: {meeting_time} 
Duration: 20 minutes
Format: Virtual (TEST)

This is a test of the calendar invite system.

Best regards,
American Funds Team (TEST)
        """
        
        print(f"Attempting to send email...")
        print(f"From: {SENDER}")
        print(f"To: {RECIPIENT}")
        print(f"Subject: {subject}")
        
        # Send email
        response = ses_client.send_email(
            Source=SENDER,
            Destination={'ToAddresses': [RECIPIENT]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text}
                }
            }
        )
        
        print(f"✅ Test calendar invite sent successfully!")
        print(f"Message ID: {response['MessageId']}")
        print(f"Meeting scheduled for: {meeting_date} at {meeting_time}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Email Error: {error_code}")
        print(f"Message: {error_message}")
        
        if error_code == "MessageRejected":
            print("\n💡 This usually means:")
            print("- Your sender email is not verified in AWS SES")
            print("- You're in SES sandbox mode and recipient isn't verified")
        elif error_code == "InvalidParameterValue":
            print("- Check email format")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing calendar invite functionality...")
    send_test_calendar_invite()