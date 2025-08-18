#!/usr/bin/env python3
"""
Script to check if Salesforce events were actually created and associated correctly
"""

import subprocess
import json
import sys
import os

# Add the parent directory to the path so we can import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration from app.py
from app import SALESFORCE_CLI_PATH, SALESFORCE_ORG_ALIAS, SALESFORCE_CONTACT_ID

def check_recent_events():
    """Query recent events from Salesforce"""
    print(f"🔍 Checking for recent events associated with Contact ID: {SALESFORCE_CONTACT_ID}")
    
    try:
        # Query for recent events (last 7 days) associated with the contact
        query = f"""
        SELECT Id, Subject, StartDateTime, EndDateTime, WhoId, Description, Location, ShowAs, CreatedDate 
        FROM Event 
        WHERE WhoId = '{SALESFORCE_CONTACT_ID}' 
        AND CreatedDate = TODAY
        ORDER BY CreatedDate DESC
        LIMIT 10
        """
        
        cmd = [
            SALESFORCE_CLI_PATH, "data", "query",
            "--query", query,
            "--target-org", SALESFORCE_ORG_ALIAS,
            "--json"
        ]
        
        print(f"🔵 Running query: {query}")
        print(f"🔵 Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"🔵 Query result: returncode={result.returncode}")
        print(f"🔵 stdout={result.stdout}")
        if result.stderr:
            print(f"🔵 stderr={result.stderr}")
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            events = data.get('result', {}).get('records', [])
            
            print(f"✅ Found {len(events)} events created today for this contact:")
            for event in events:
                print(f"  - ID: {event['Id']}")
                print(f"    Subject: {event['Subject']}")
                print(f"    Start: {event['StartDateTime']}")
                print(f"    WhoId: {event['WhoId']}")
                print(f"    Created: {event['CreatedDate']}")
                print(f"    Description: {event.get('Description', 'None')[:100]}...")
                print()
            
            return events
        else:
            print(f"❌ Query failed with return code {result.returncode}")
            return []
            
    except Exception as e:
        print(f"❌ Error querying events: {e}")
        return []

def check_specific_events():
    """Check the specific event IDs from the logs"""
    event_ids = ["00UgK000000ZCkfUAG", "00UgK000000ZCmHUAW"]
    
    for event_id in event_ids:
        print(f"🔍 Checking specific event: {event_id}")
        
        try:
            cmd = [
                SALESFORCE_CLI_PATH, "data", "get", "record",
                "--sobject", "Event",
                "--record-id", event_id,
                "--target-org", SALESFORCE_ORG_ALIAS,
                "--json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                event_data = data.get('result', {})
                print(f"✅ Event {event_id} found:")
                print(f"  Subject: {event_data.get('Subject')}")
                print(f"  WhoId: {event_data.get('WhoId')}")
                print(f"  StartDateTime: {event_data.get('StartDateTime')}")
                print(f"  Description: {event_data.get('Description', '')[:100]}...")
                print()
            else:
                print(f"❌ Event {event_id} not found or query failed")
                print(f"  Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error checking event {event_id}: {e}")

def main():
    print("="*60)
    print("SALESFORCE EVENT VERIFICATION")
    print("="*60)
    print()
    
    # Check for recent events
    recent_events = check_recent_events()
    print()
    
    # Check specific events from logs
    check_specific_events()
    print()
    
    print("="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()