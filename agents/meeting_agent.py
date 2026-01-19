#!/usr/bin/env python3
import asyncio
import os
import subprocess
import re  # Added for regex extraction
from datetime import datetime
from dotenv import load_dotenv
from droidrun import DroidAgent
from droidrun.config_manager.config_manager import DroidrunConfig, AgentConfig, LoggingConfig
from llama_index.llms.google_genai import GoogleGenAI
from agents.prompts import prompts

load_dotenv()

# Config
SCREENSHOT_INTERVAL = 5 * 60  # 5 minutes

def identify_target_app(name: str, description: str, link: str) -> str:
    """
    Determines the best app to open based on priority logic:
    1. Search Name/Description for app keywords.
    2. Search Link for known domains.
    3. Default to 'Browser' if unknown.
    """
    full_text = (name + " " + description).lower()
    link = link.lower() if link else ""

    # --- PRIORITY 1: Check Meeting Name & Description ---
    known_apps = {
        "zoom": "Zoom",
        "google meet": "Google Meet",
        "gmeet": "Google Meet",
        "teams": "Teams",
        "discord": "Discord",
        "skype": "Skype",
        "webex": "Webex",
        "slack": "Slack"
    }

    for keyword, app_name in known_apps.items():
        if keyword in full_text:
            return app_name

    # --- PRIORITY 2: Check Link Domain ---
    if "zoom.us" in link:
        return "Zoom"
    elif "meet.google" in link:
        return "Google Meet"
    elif "teams.microsoft" in link:
        return "Teams"
    elif "discord.gg" in link:
        return "Discord"

    # --- PRIORITY 3: Fallback ---
    return "Browser"

async def take_screenshot_loop(duration_minutes=5):
    """Takes a screenshot every 30 seconds for a set duration."""
    print(f"📸 [SURVEILLANCE] Starting capture for {duration_minutes} mins...")
    end_time = asyncio.get_event_loop().time() + (duration_minutes * 60)
    
    os.makedirs("meeting_screenshots", exist_ok=True)
    
    while asyncio.get_event_loop().time() < end_time:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting_screenshots/meet_{timestamp}.png"
        
        # Silent ADB capture
        subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screen.png"], 
                       stderr=subprocess.DEVNULL)
        subprocess.run(["adb", "pull", "/sdcard/screen.png", filename], 
                       stderr=subprocess.DEVNULL)
        
        print(f"   [Saved]: {filename}")
        await asyncio.sleep(30)

async def join_meeting_smart(meeting_data: dict):
    """
    Smart Joiner that extracts credentials and routes to the correct app.
    """
    # 1. ROBUST EXTRACTION
    m_name = meeting_data.get("name") or "Unknown Meeting"
    m_desc = meeting_data.get("description", "")
    m_link = meeting_data.get("link", "")
    
    # Try 'id' first (scraper standard), then 'meeting_id' (legacy/other sources)
    m_id = meeting_data.get("id") or meeting_data.get("meeting_id") or ""
    
    # Try 'code' (scraper standard), then 'password', then 'pass'
    m_pass = meeting_data.get("code") or meeting_data.get("password") or meeting_data.get("pass") or ""

    # 2. DEBUG LOG
    print(f"\n🔹 [MEETING AGENT] Received Data:")
    print(f"   Name: {m_name}")
    print(f"   Link: {m_link}")
    print(f"   ID:   '{m_id}'")
    print(f"   Pass: '{m_pass}'")

    # 3. IDENTIFY APP
    app_name = identify_target_app(m_name, m_desc, m_link)
    print(f"   👉 Decision: Use App '{app_name}'")

    # 4. AUTO-EXTRACT ID FROM LINK (If missing)
    if not m_id and m_link:
        if "zoom.us" in m_link:
            numbers = re.findall(r'\d+', m_link)
            if numbers:
                # Zoom IDs are usually the longest sequence (9-11 digits)
                m_id = max(numbers, key=len)
                print(f"   ⚠️ Auto-extracted ID from link: {m_id}")

    # Safety Check: If we still lack an ID and it's not a browser link, we can't proceed
    if not m_id and app_name != "Browser":
        print("❌ [MEETING AGENT] Error: Meeting ID is missing. Cannot join app.")
        return False

    try:
        llm = GoogleGenAI(api_key=os.environ["GEMINI_API_KEY"], model="models/gemini-2.5-pro")
        config = DroidrunConfig(
            agent=AgentConfig(reasoning=True, max_steps=30),
            logging=LoggingConfig(debug=True, save_trajectory="action"),
        )

        # 5. SELECT STRATEGY & GOAL
        if app_name == "Browser":
            # For Browser, the 'meeting_id' prompt input becomes the Link URL
            goal = prompts.JOIN_APP_SPECIFIC_GOAL(
                app_name="Chrome", 
                meeting_id=m_link, 
                meeting_pass="Just Open Link"
            )
        else:
            # For Apps, we use the actual ID and Password
            goal = prompts.JOIN_APP_SPECIFIC_GOAL(
                app_name=app_name, 
                meeting_id=m_id, 
                meeting_pass=m_pass
            )

        agent = DroidAgent(
            goal=goal,
            config=config,
            llms=llm,
        )

        result = await agent.run()
        
        # 6. VERIFY SUCCESS
        if result.success:
            print(f"✅ [{app_name.upper()} AGENT] Joined successfully.")
            await take_screenshot_loop(duration_minutes=5)
            return True
        else:
            print(f"❌ [{app_name.upper()} AGENT] Failed. Reason: {result.reason}")
            return False

    except Exception as e:
        print(f"❌ [MEETING AGENT] Crashed: {e}")
        return False