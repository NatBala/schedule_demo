import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# AWS credentials (REPLACE WITH YOUR OWN)
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-2"

# Email addresses (HARDCODED FOR DEMO)
SENDER = "achalshahkpmg@outlook.com"
RECIPIENT = "nbalasubramanian1@KPMG.com"

def create_ics_calendar_invite():
    # Tomorrow at 10 AM
    tomorrow = datetime.now() + timedelta(days=1)
    start_datetime = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(minutes=20)
    
    # Format for ICS (UTC time)
    start_utc = start_datetime.strftime('%Y%m%dT%H%M%S')
    end_utc = end_datetime.strftime('%Y%m%dT%H%M%S')
    
    uid = str(uuid.uuid4())
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//American Funds//Meeting Scheduler//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_utc}
DTEND:{end_utc}
SUMMARY:American Funds - ETF Discussion Meeting
DESCRIPTION:Meeting with American Funds wholesaler to discuss ETF solutions and portfolio construction strategies.
ORGANIZER;CN=American Funds:mailto:{SENDER}
ATTENDEE;CN=Financial Advisor;RSVP=TRUE:mailto:{RECIPIENT}
STATUS:CONFIRMED
SEQUENCE:0
END:VEVENT
END:VCALENDAR"""
    
    return ics_content, start_datetime

def send_calendar_invite_test():
    try:
        # Create SES client
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION
        )
        
        # Generate ICS content
        ics_content, meeting_datetime = create_ics_calendar_invite()
        
        # Create email content
        meeting_date = meeting_datetime.strftime('%A, %B %d, %Y')
        meeting_time = meeting_datetime.strftime('%I:%M %p')
        
        subject = f"Calendar Invite - American Funds Meeting - {meeting_date}"
        
        body_text = f"""Dear Financial Advisor,

You have been invited to a meeting with American Funds.

Meeting Details:
Date: {meeting_date}
Time: {meeting_time}
Duration: 20 minutes
Format: Virtual

This meeting will cover:
- Capital Group ETF performance and portfolio construction
- Tax-efficient investment strategies
- Solutions tailored to your client base

Please accept this calendar invitation to confirm your attendance.

Best regards,
American Funds Team
        """
        
        # Create multipart message
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = SENDER
        msg['To'] = RECIPIENT
        
        # Add text body
        msg.attach(MIMEText(body_text, 'plain'))
        
        # Add ICS calendar attachment
        ics_attachment = MIMEApplication(ics_content.encode('utf-8'))
        ics_attachment.add_header('Content-Disposition', 'attachment', filename='meeting.ics')
        ics_attachment.add_header('Content-Type', 'text/calendar; method=REQUEST; name="meeting.ics"')
        msg.attach(ics_attachment)
        
        print("Sending calendar invite...")
        print(f"From: {SENDER}")
        print(f"To: {RECIPIENT}")
        print(f"Meeting: {meeting_date} at {meeting_time}")
        
        # Send raw email with attachment
        response = ses_client.send_raw_email(
            Source=SENDER,
            Destinations=[RECIPIENT],
            RawMessage={'Data': msg.as_string()}
        )
        
        print("SUCCESS! Calendar invite sent with ICS attachment!")
        print(f"Message ID: {response['MessageId']}")
        print("Check your email - you should see a calendar invite that you can accept/decline")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"ERROR: {error_code}")
        print(f"Message: {error_message}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing proper calendar invite with ICS attachment...")
    success = send_calendar_invite_test()
    if success:
        print("\nCheck your email - you should now see a proper calendar invitation!")
        print("The email should show calendar options like Accept/Decline/Tentative")
    else:
        print("\nCalendar invite sending failed.")