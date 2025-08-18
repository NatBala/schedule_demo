#!/usr/bin/env python3
"""
Compare how test_salesforce.py and app.py create events
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_salesforce_event

def test_scenario_1():
    """Exactly like test_salesforce.py does it"""
    print("="*60)
    print("SCENARIO 1: test_salesforce.py style")
    print("="*60)
    
    tomorrow = datetime.now() + timedelta(days=1)
    meeting_info = {
        'date': tomorrow,
        'time': '14:30',
        'advisor_name': 'Test Advisor',
        'day': 'Tomorrow'
    }
    
    print(f"Meeting info: {meeting_info}")
    print(f"Date type: {type(meeting_info['date'])}")
    print(f"Time type: {type(meeting_info['time'])}")
    
    # This is EXACTLY what test_salesforce.py does
    event_id = create_salesforce_event(meeting_info)
    print(f"Created event ID: {event_id}")
    
    return event_id

def test_scenario_2():
    """Like app.py with parsed time"""
    print("\n" + "="*60)
    print("SCENARIO 2: app.py with parsed time")
    print("="*60)
    
    # This is what happens when time IS parsed successfully
    meeting_info = {
        'day': 'Tuesday',
        'time': '14:00',  # Successfully parsed
        'date': datetime(2025, 8, 19, 11, 1, 25, 844943),  # Has current time in it
        'advisor_name': 'Nat',
        'advisor_email': 'nbalasubramanian1@KPMG.com',
        'wholesaler_name': 'Sarah Johnson'
    }
    
    print(f"Meeting info: {meeting_info}")
    print(f"Date type: {type(meeting_info['date'])}")
    print(f"Time type: {type(meeting_info['time'])}")
    
    event_id = create_salesforce_event(meeting_info)
    print(f"Created event ID: {event_id}")
    
    return event_id

def test_scenario_3():
    """Like app.py with default time"""
    print("\n" + "="*60)
    print("SCENARIO 3: app.py with default time (after fix)")
    print("="*60)
    
    # This is what happens after our fix when time is NOT parsed
    meeting_info = {
        'day': 'Tuesday',
        'time': '14:00',  # Default time after fix
        'date': datetime(2025, 8, 19, 11, 1, 41, 168906),  # Has current time in it
        'advisor_name': 'Nat',
        'advisor_email': 'nbalasubramanian1@KPMG.com',
        'wholesaler_name': 'Sarah Johnson'
    }
    
    print(f"Meeting info: {meeting_info}")
    print(f"Date type: {type(meeting_info['date'])}")
    print(f"Time type: {type(meeting_info['time'])}")
    
    event_id = create_salesforce_event(meeting_info)
    print(f"Created event ID: {event_id}")
    
    return event_id

def main():
    print("COMPARING EVENT CREATION METHODS")
    print("="*60)
    
    # Test all scenarios
    event1 = test_scenario_1()
    event2 = test_scenario_2()
    event3 = test_scenario_3()
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Test script style: {event1}")
    print(f"App with parsed time: {event2}")
    print(f"App with default time: {event3}")
    
    print("\nNow check if these appear in Salesforce UI:")
    print("https://orgfarm-eb776f0bfa-dev-ed.develop.lightning.force.com/lightning/r/Contact/003gK000007vmQTQAY/view")

if __name__ == "__main__":
    main()