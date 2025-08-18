#!/usr/bin/env python3
"""
Quick script to verify a specific Salesforce event and check its details
"""

import subprocess
import json
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import SALESFORCE_CLI_PATH, SALESFORCE_ORG_ALIAS, SALESFORCE_CONTACT_ID

def check_event(event_id):
    """Check a specific event by ID"""
    print(f"🔍 Checking event: {event_id}")
    
    try:
        # Get event details
        cmd = [
            SALESFORCE_CLI_PATH, "data", "get", "record",
            "--sobject", "Event",
            "--record-id", event_id,
            "--target-org", SALESFORCE_ORG_ALIAS,
            "--json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            event_data = data.get('result', {})
            print(f"✅ Event found!")
            print(f"  Subject: {event_data.get('Subject')}")
            print(f"  WhoId: {event_data.get('WhoId')}")
            print(f"  Contact Match: {'✅ CORRECT' if event_data.get('WhoId') == SALESFORCE_CONTACT_ID else '❌ WRONG CONTACT'}")
            print(f"  StartDateTime: {event_data.get('StartDateTime')}")
            print(f"  EndDateTime: {event_data.get('EndDateTime')}")
            print(f"  Location: {event_data.get('Location')}")
            print(f"  ShowAs: {event_data.get('ShowAs')}")
            print(f"  IsDeleted: {event_data.get('IsDeleted')}")
            print(f"  ActivityDate: {event_data.get('ActivityDate')}")
            print(f"  ActivityDateTime: {event_data.get('ActivityDateTime')}")
            print(f"  Description: {event_data.get('Description', '')[:100]}...")
            
            # Check if it's in the past
            import datetime
            start_time = event_data.get('StartDateTime')
            if start_time:
                from dateutil import parser
                event_dt = parser.parse(start_time)
                now = datetime.datetime.now(datetime.timezone.utc)
                if event_dt < now:
                    print(f"  ⚠️ WARNING: Event is in the PAST ({event_dt} < {now})")
                else:
                    print(f"  ✅ Event is in the FUTURE ({event_dt})")
                    
            return event_data
        else:
            print(f"❌ Event not found or error")
            print(f"  Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def check_contact_events():
    """Check all events for the contact"""
    print(f"\n🔍 Checking ALL events for contact: {SALESFORCE_CONTACT_ID}")
    
    try:
        # Query for ALL events (no date filter)
        query = f"""
        SELECT Id, Subject, StartDateTime, EndDateTime, WhoId, ActivityDate, IsDeleted
        FROM Event 
        WHERE WhoId = '{SALESFORCE_CONTACT_ID}'
        ORDER BY CreatedDate DESC
        LIMIT 20
        """
        
        cmd = [
            SALESFORCE_CLI_PATH, "data", "query",
            "--query", query,
            "--target-org", SALESFORCE_ORG_ALIAS,
            "--json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            events = data.get('result', {}).get('records', [])
            print(f"✅ Found {len(events)} total events for this contact")
            for event in events:
                print(f"  - {event['Id']}: {event['Subject']} on {event['StartDateTime']}")
        else:
            print(f"❌ Query failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Main execution
if __name__ == "__main__":
    event_id = "00UgK000000ZEw9UAG"  # The event from your log
    
    print("="*60)
    print(f"VERIFYING EVENT: {event_id}")
    print("="*60)
    
    event_data = check_event(event_id)
    
    if event_data:
        print("\n" + "="*60)
        print("CHECKING VISIBILITY ISSUES")
        print("="*60)
        
        # Direct Salesforce URLs
        print("\nTry these direct links:")
        print(f"1. Event Page: https://orgfarm-eb776f0bfa-dev-ed.develop.lightning.force.com/lightning/r/Event/{event_id}/view")
        print(f"2. Contact Page: https://orgfarm-eb776f0bfa-dev-ed.develop.lightning.force.com/lightning/r/Contact/{SALESFORCE_CONTACT_ID}/view")
        print(f"3. Calendar View: https://orgfarm-eb776f0bfa-dev-ed.develop.lightning.force.com/lightning/n/standard__Calendar")
    
    # Check all events
    check_contact_events()
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)