#!/usr/bin/env python3
"""
Test script to verify Salesforce integration functionality
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from app.py
from app import check_salesforce_cli, create_salesforce_event, send_meeting_confirmation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_salesforce_cli():
    """Test Salesforce CLI connectivity"""
    log.info("🔵 Testing Salesforce CLI connectivity...")
    result = check_salesforce_cli()
    log.info(f"Salesforce CLI check result: {result}")
    return result

def test_create_event():
    """Test creating a Salesforce event"""
    log.info("🔵 Testing Salesforce event creation...")
    
    # Create test meeting info
    tomorrow = datetime.now() + timedelta(days=1)
    meeting_info = {
        'date': tomorrow,
        'time': '14:30',
        'advisor_name': 'Test Advisor',
        'day': 'Tomorrow'
    }
    
    log.info(f"Test meeting info: {meeting_info}")
    
    # Try to create the event
    event_id = create_salesforce_event(meeting_info)
    log.info(f"Created event ID: {event_id}")
    
    return event_id is not None

def test_full_workflow():
    """Test the complete send_meeting_confirmation workflow"""
    log.info("🔵 Testing complete meeting confirmation workflow...")
    
    # Create test meeting info
    tomorrow = datetime.now() + timedelta(days=1)
    meeting_info = {
        'date': tomorrow,
        'time': '15:00',
        'advisor_name': 'Test Full Workflow',
        'day': 'Tomorrow'
    }
    
    conversation_text = f"Great! I'll schedule our meeting for tomorrow at 3 PM to discuss American Funds ETF solutions."
    
    # Test the full workflow
    results = send_meeting_confirmation(meeting_info, conversation_text)
    log.info(f"Full workflow results: {results}")
    
    return results

def main():
    """Run all tests"""
    log.info("🚀 Starting Salesforce integration tests...")
    
    # Test 1: CLI connectivity
    cli_ok = test_salesforce_cli()
    if not cli_ok:
        log.error("❌ Salesforce CLI test failed - stopping tests")
        return False
    
    log.info("✅ Salesforce CLI test passed")
    
    # Test 2: Event creation
    event_ok = test_create_event()
    if not event_ok:
        log.error("❌ Salesforce event creation test failed")
        return False
    
    log.info("✅ Salesforce event creation test passed")
    
    # Test 3: Full workflow
    workflow_results = test_full_workflow()
    if not workflow_results or not workflow_results.get('salesforce_created'):
        log.error("❌ Full workflow test failed")
        log.error(f"Results: {workflow_results}")
        return False
    
    log.info("✅ Full workflow test passed")
    log.info("🎉 All Salesforce integration tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)