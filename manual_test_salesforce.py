#!/usr/bin/env python3
"""
Manual test to trigger Salesforce integration from running app
"""

import sys
import os
import logging
import requests
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from app.py
from app import send_meeting_confirmation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_direct_salesforce_call():
    """Test calling send_meeting_confirmation directly"""
    log.info("MANUAL TEST: Calling send_meeting_confirmation directly")
    
    # Create test meeting info
    tomorrow = datetime.now() + timedelta(days=1)
    meeting_info = {
        'date': tomorrow,
        'time': '14:00',
        'advisor_name': 'Manual Test User',
        'day': 'Tomorrow'
    }
    
    conversation_text = "Perfect! Let's schedule our meeting for tomorrow at 2 PM to discuss American Funds ETF solutions."
    
    print(f"\nMANUAL SALESFORCE TEST")
    print(f"Meeting Info: {meeting_info}")
    print(f"Conversation: {conversation_text}")
    print("-" * 50)
    
    try:
        # Test the full workflow
        results = send_meeting_confirmation(meeting_info, conversation_text)
        
        print(f"\nTEST RESULTS:")
        print(f"Email Sent: {'Success' if results['email_sent'] else 'Failed'}")
        print(f"Salesforce Event Created: {'Success' if results['salesforce_created'] else 'Failed'}")
        print(f"Full Results: {results}")
        
        return results
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_http_endpoint():
    """Test calling the HTTP endpoint if the app is running"""
    try:
        response = requests.get("http://localhost:5050/test-salesforce", timeout=30)
        print(f"\nHTTP ENDPOINT TEST:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"\nHTTP ENDPOINT FAILED: {e}")
        return False

def main():
    """Run both tests"""
    print("Starting Manual Salesforce Integration Tests...")
    
    # Test 1: Direct function call
    print("\n" + "="*60)
    print("TEST 1: Direct Function Call")
    print("="*60)
    
    direct_results = test_direct_salesforce_call()
    
    # Test 2: HTTP endpoint (if app is running)
    print("\n" + "="*60)
    print("TEST 2: HTTP Endpoint")
    print("="*60)
    
    http_success = test_http_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if direct_results:
        print(f"Direct Call: Email={direct_results['email_sent']}, Salesforce={direct_results['salesforce_created']}")
    else:
        print("Direct Call: Failed")
    
    print(f"HTTP Endpoint: {'Working' if http_success else 'Failed'}")
    
    print("\nCheck the Flask application logs for detailed debugging information.")

if __name__ == "__main__":
    main()