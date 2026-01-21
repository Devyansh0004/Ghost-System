#!/usr/bin/env python3
import asyncio
import os
import subprocess
import re
import time
from datetime import datetime
from dotenv import load_dotenv
from droidrun import DroidAgent
from droidrun.config_manager.config_manager import DroidrunConfig, AgentConfig, LoggingConfig, ManagerConfig, ExecutorConfig
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.tools import FunctionTool
from agents.prompts import prompts

# --- TRICK: Import default tools ---
try:
    from droidrun.tools import default_tools
except ImportError:
    default_tools = []

load_dotenv()

# ==============================================================================
# 1. ROBUST FAST NAV (Python-Driven Speed)
# ==============================================================================
def adb_fast_nav(command: str, description: str):
    """Executes a blind ADB command. Raises exception if it fails."""
    print(f"   ⚡ Fast Nav: {description}")
    
    if "input text" in command:
        parts = command.split("input text")
        if len(parts) > 1:
            text = parts[1].strip().replace(" ", "%s")
            command = f"adb shell input text {text}"
            
    result = subprocess.run(command, shell=True, timeout=5, capture_output=True)
    
    if result.returncode != 0:
        raise Exception(f"Command failed: {description}")
        
    time.sleep(1.5) 

# ==============================================================================
# 2. SHELL TOOL (For the Agent to Type Fast)
# ==============================================================================
def execute_shell_command(command: str) -> str:
    """Executes ADB shell commands."""
    try:
        if "input text" in command:
            parts = command.split("input text")
            if len(parts) > 1:
                text_content = parts[1].strip().strip("'").strip('"')
                safe_text = text_content.replace(" ", "%s")
                command = f"adb shell input text {safe_text}"

        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return f"✅ Output: {result.stdout.strip()}" if result.returncode == 0 else f"❌ Error: {result.stderr.strip()}"
    except Exception as e:
        return f"💥 Exception: {str(e)}"

shell_tool = FunctionTool.from_defaults(
    fn=execute_shell_command,
    name="shell_executor",
    description="Executes ADB shell commands. Use 'adb shell input text <string>' to type IDs/Passwords instantly."
)

# ==============================================================================
# 3. HELPER LOGIC (Updated Screenshot Loop)
# ==============================================================================
def identify_target_app(name: str, description: str, link: str) -> str:
    full_text = (name + " " + description).lower()
    link = link.lower() if link else ""

    known_apps = {"zoom": "Zoom", "google meet": "Google Meet", "gmeet": "Google Meet", "teams": "Teams"}
    for keyword, app_name in known_apps.items():
        if keyword in full_text: return app_name
    
    if "zoom.us" in link: return "Zoom"
    elif "meet.google" in link: return "Google Meet"
    elif "teams.microsoft" in link: return "Teams"
    return "Browser"

async def take_screenshot_loop(meeting_name: str, duration_minutes=5):
    """
    Takes surveillance screenshots and saves them to a specific folder
    named after the meeting and timestamp.
    """
    # Create a sanitized folder name
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', meeting_name)[:20]  # Limit length
    timestamp_folder = datetime.now().strftime("%Y%m%d")
    
    # Structure: data/screenshots/20231025_MeetingName/
    save_path = f"data/screenshots/{timestamp_folder}_{clean_name}"
    os.makedirs(save_path, exist_ok=True)
    
    print(f"📸 [SURVEILLANCE] Capturing evidence to: {save_path}")
    print(f"   ⏱️ Duration: {duration_minutes} minutes")

    end_time = asyncio.get_event_loop().time() + (duration_minutes * 60)
    
    shot_count = 1
    while asyncio.get_event_loop().time() < end_time:
        # Create unique filename
        time_str = datetime.now().strftime("%H%M%S")
        filename = f"{save_path}/shot_{shot_count:03d}_{time_str}.png"
        
        # Capture and Pull
        subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screen.png"], stderr=subprocess.DEVNULL)
        subprocess.run(["adb", "pull", "/sdcard/screen.png", filename], stderr=subprocess.DEVNULL)
        
        print(f"   💾 Saved: {filename}")
        shot_count += 1
        await asyncio.sleep(30) # Capture every 30 seconds

# ==============================================================================
# 4. SAFETY NET
# ==============================================================================
async def join_with_ai_safety_net(app_name, meeting_id, meeting_pass):
    print(f"   🛡️ [SAFETY NET] Engaging AI Agent for '{app_name}'...")
    llm = GoogleGenAI(api_key=os.environ["GEMINI_API_KEY"], model="models/gemini-2.5-flash")
    config = DroidrunConfig(
        agent=AgentConfig(reasoning=False, max_steps=50),
        logging=LoggingConfig(debug=True, save_trajectory="action"),
        manager=ManagerConfig(vision=True), # Enable vision
        executor=ExecutorConfig(vision=True)
    )
    goal = f"Open {app_name}. Find the 'Join Meeting' button. Enter ID: {meeting_id}. Enter Password: {meeting_pass}."
    all_tools = default_tools + [shell_tool]
    agent = DroidAgent(goal=goal, config=config, llms=llm, tools=all_tools)
    result = await agent.run()
    return result.success

# ==============================================================================
# 5. MAIN WORKFLOW
# ==============================================================================
async def join_meeting_smart(meeting_data: dict):
    # 1. DATA EXTRACTION
    m_name = meeting_data.get("name") or "Unknown_Meeting"
    m_link = meeting_data.get("link", "")
    m_id = meeting_data.get("id") or meeting_data.get("meeting_id") or ""
    m_pass = meeting_data.get("code") or meeting_data.get("password") or ""

    print(f"\n🔹 [MEETING AGENT] Processing: {m_name} | ID: {m_id}")

    # 2. IDENTIFY APP
    app_name = identify_target_app(m_name, meeting_data.get("description", ""), m_link)
    print(f"   👉 Decision: Use App '{app_name}'")

    if not m_id and m_link and "zoom.us" in m_link:
        numbers = re.findall(r'\d+', m_link)
        if numbers: m_id = max(numbers, key=len)

    if not m_id and app_name != "Browser":
        print("❌ [MEETING AGENT] Error: Meeting ID is missing.")
        return False

    launch_success = False

    # 3. PHASE 1: TURBO LAUNCH
    try:
        if app_name == "Zoom":
            adb_fast_nav("adb shell am force-stop us.zoom.videomeetings", "Reset Zoom")
            adb_fast_nav("adb shell monkey -p us.zoom.videomeetings 1", "Launch Zoom")
            launch_success = True
        elif app_name == "Google Meet":
            adb_fast_nav("adb shell am force-stop com.google.android.apps.meetings", "Reset Meet")
            adb_fast_nav("adb shell monkey -p com.google.android.apps.meetings 1", "Launch Meet")
            launch_success = True
        elif app_name == "Teams":
            adb_fast_nav("adb shell am force-stop com.microsoft.teams", "Reset Teams")
            adb_fast_nav("adb shell monkey -p com.microsoft.teams 1", "Launch Teams")
            launch_success = True
        elif app_name == "Browser":
            clean_link = m_link.replace("&", "\\&")
            adb_fast_nav(f"adb shell am start -a android.intent.action.VIEW -d '{clean_link}'", "Open Link")
            print("✅ [BROWSER] Link opened directly.")
            # Start monitoring browser session
            await take_screenshot_loop(m_name, 5) 
            return True
            
    except Exception as e:
        print(f"   ⚠️ Fast Launch Malfunction: {e}")

    # 4. PHASE 2: SAFETY NET CHECK
    if not launch_success:
        print("   🚨 Triggering Safety Net...")
        success = await join_with_ai_safety_net(app_name, m_id, m_pass)
        if success:
            print("✅ [SAFETY NET] Joined successfully.")
            await take_screenshot_loop(m_name, 5) # <--- UPDATED
            return True
        else:
            print("❌ [SAFETY NET] Failed.")
            return False

    # 5. PHASE 3: AGENT INTERACTION
    print(f"   🧠 App Launched. Waking Agent...")

    try:
        llm = GoogleGenAI(api_key=os.environ["GEMINI_API_KEY"], model="models/gemini-2.5-flash")
        config = DroidrunConfig(
            agent=AgentConfig(reasoning=True, max_steps=50),
            logging=LoggingConfig(debug=True, save_trajectory="action"),
            manager=ManagerConfig(vision=True),
            executor=ExecutorConfig(vision=True)
            )

        # Get the correct Prompt Template
        if "google_tasks" in prompts and hasattr(prompts, "render"):
             # If using Jinja2Template object
             goal = prompts.render(app_name=app_name, meeting_id=m_id, meeting_pass=m_pass)
        elif isinstance(prompts, dict) and "meeting_agent" in prompts:
            # If using Dict structure (recommended based on previous turns)
             goal = prompts["meeting_agent"].render(app_name=app_name, meeting_id=m_id, meeting_pass=m_pass)
        else:
            # Fallback string format
            goal = f"Join {app_name} meeting {m_id} with pass {m_pass}"


        all_tools = default_tools + [shell_tool]

        agent = DroidAgent(
            goal=goal,
            config=config,
            llms=llm,
            tools=all_tools
        )

        result = await agent.run()
        
        if result.success:
            print(f"✅ [{app_name.upper()} AGENT] Joined successfully.")
            await take_screenshot_loop(m_name, 5) # <--- UPDATED
            return True
        else:
            print(f"❌ [{app_name.upper()} AGENT] Failed.")
            return False

    except Exception as e:
        print(f"❌ [MEETING AGENT] Crashed: {e}")
        return False