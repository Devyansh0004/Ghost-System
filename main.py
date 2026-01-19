import asyncio
import json
import os
# CHECK: Ensure this matches your file name in agents/ (likely scrape_group.py)
from agents.scraper_agent import scrape_whatsapp_group 
from agents.alarm_agent import set_event_alarm
# UPDATE: Import the new smart agent
from agents.meeting_agent import join_meeting_smart

def load_groups(filename="groups.json"):
    """Loads the list of groups from the JSON file."""
    try:
        if not os.path.exists(filename):
            print(f"⚠️ Error: {filename} not found.")
            return []
            
        with open(filename, "r") as f:
            groups = json.load(f)
            
        if not isinstance(groups, list):
            print(f"⚠️ Error: {filename} must contain a list of strings.")
            return []
            
        return groups
    except json.JSONDecodeError:
        print(f"⚠️ Error: {filename} contains invalid JSON.")
        return []

async def process_scraped_data(group_name):
    """Reads the JSON data for a group and triggers Alarms/Meetings."""
    file_path = f"data/{group_name.replace(' ', '_')}_data.json"
    
    if not os.path.exists(file_path):
        print(f"⚠️ No data file found for {group_name}")
        return

    with open(file_path, "r") as f:
        data = json.load(f)

    # 1. Process Events -> Set Alarms
    events = data.get("events", [])
    if events:
        print(f"\n⏰ Found {len(events)} events in '{group_name}'. Setting alarms...")
        for event in events:
            # Check if time exists and is not null
            if event.get("time") and event.get("name"):
                await set_event_alarm(event["name"], event["time"])
                await asyncio.sleep(2) # Pause between alarms

    # 2. Process Meetings -> Join the first one (For Demo)
    meetings = data.get("meetings", [])
    if meetings:
        first_meeting = meetings[0]
        print(f"\n🎥 Found meeting in '{group_name}': {first_meeting.get('name', 'Unknown')}")
        print("   Invoking Smart Meeting Agent...")
        
        # UPDATE: We now pass the WHOLE dictionary, not just the link.
        # The agent will extract ID/Code/Link from this object.
        await join_meeting_smart(first_meeting)
    else:
        print("ℹ️ No meetings found in this group.")

async def main():
    print("🚀 DroidRun Assistant Starting...")
    
    # 1. Load Target Groups
    target_groups = load_groups()
    
    if not target_groups:
        print("❌ No groups found in groups.json. Exiting.")
        return

    print(f"📋 Processing {len(target_groups)} groups: {target_groups}\n")

    # 2. Iterate through each group
    for group in target_groups:
        print(f"--- 🟢 Starting Workflow for '{group}' ---")
        
        # Step A: Scrape Data
        success = await scrape_whatsapp_group(group)
        
        if success:
            # Step B: Act on Data (Alarms & Meetings)
            print(f"   ✅ Scrape successful. Processing actions...")
            await process_scraped_data(group)
        else:
            print(f"   ❌ Scrape failed for '{group}'. Skipping actions.")
        
        print(f"--- 🔴 Completed '{group}' ---\n")
        await asyncio.sleep(3) # Cool down between groups

    print("\n🏁 All assistant tasks complete.")

if __name__ == "__main__":
    asyncio.run(main())