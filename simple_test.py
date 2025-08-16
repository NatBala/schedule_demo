import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

# AWS credentials
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY_HERE"
SECRET_KEY = "YOUR_AWS_SECRET_KEY_HERE"
REGION = "us-east-2"

# Email addresses
SENDER = "your_sender@email.com"
RECIPIENT = "your_recipient@email.com"

def send_simple_test():
    try:
        # Create SES client
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION
        )
        
        # Tomorrow at 10 AM
        tomorrow = datetime.now() + timedelta(days=1)
        meeting_date = tomorrow.strftime('%A, %B %d, %Y')
        
        subject = f"TEST - American Funds Meeting - {meeting_date} at 10:00 AM"
        
        body_text = f"""Dear Test Advisor,

This is a TEST calendar invite for tomorrow at 10:00 AM.

Meeting Details:
Date: {meeting_date}
Time: 10:00 AM
Duration: 20 minutes
Format: Virtual (TEST)

This is a test of the calendar invite system.

Best regards,
American Funds Team (TEST)
        """
        
        print("Attempting to send email...")
        print(f"From: {SENDER}")
        print(f"To: {RECIPIENT}")
        print(f"Subject: {subject}")
        print(f"Start time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
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
        
        print(f"End time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print("SUCCESS! Test email sent successfully!")
        print(f"Message ID: {response['MessageId']}")
        print(f"Meeting scheduled for: {meeting_date} at 10:00 AM")
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
    print("Testing calendar invite functionality...")
    success = send_simple_test()
    if success:
        print("\nCheck your email at nbalasubramanian1@KPMG.com!")
    else:
        print("\nEmail sending failed. Check AWS SES configuration.")