import boto3
from botocore.exceptions import ClientError

# AWS credentials
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY_HERE"
SECRET_KEY = "YOUR_AWS_SECRET_KEY_HERE"
REGION = "us-east-2"

# Email addresses that need verification
EMAILS_TO_VERIFY = [
    "your_sender@email.com",
    "your_recipient@email.com"
]

def verify_email_addresses():
    try:
        # Create SES client
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION
        )
        
        print("Checking current verified email addresses...")
        
        # List verified email addresses
        response = ses_client.list_verified_email_addresses()
        verified_emails = response.get('VerifiedEmailAddresses', [])
        
        print(f"Currently verified emails: {verified_emails}")
        
        # Check which emails need verification
        for email in EMAILS_TO_VERIFY:
            if email in verified_emails:
                print(f"✅ {email} is already verified")
            else:
                print(f"❌ {email} needs verification")
                
                # Send verification email
                try:
                    ses_client.verify_email_identity(EmailAddress=email)
                    print(f"📧 Verification email sent to {email}")
                    print(f"   Please check the inbox for {email} and click the verification link")
                except ClientError as e:
                    print(f"❌ Failed to send verification to {email}: {e}")
        
        print("\nNOTE: You must verify BOTH email addresses before sending calendar invites will work.")
        print("Check the email inboxes and click the verification links.")
        
    except ClientError as e:
        print(f"❌ AWS Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    verify_email_addresses()