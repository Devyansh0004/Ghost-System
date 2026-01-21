import asyncio
import os
import subprocess
import re
from datetime import datetime
from dotenv import load_dotenv
from droidrun import DroidAgent
from droidrun.config_manager.config_manager import DroidrunConfig, AgentConfig, LoggingConfig, ManagerConfig, ExecutorConfig
from llama_index.llms.google_genai import GoogleGenAI
from agents.prompts import prompts

load_dotenv()

def parse_time_string(time_str: str):
    """
    Converts natural time strings (1:50 am, 14:30) into Hour (0-23) and Minute (0-59).
    """
    time_str = time_str.lower().strip()
    hour = 0
    minute = 0
    
    # Clean up string
    time_str = time_str.replace(".", "").replace(" ", "") # "1:50 am" -> "1:50am"
    
    # Regex to find HH:MM and am/pm
    match = re.match(r"(\d{1,2}):(\d{2})([ap]m)?", time_str)
    
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        meridiem = match.group(3) # 'am' or 'pm'
        
        # Convert to 24-hour format
        if meridiem == "pm" and h != 12:
            h += 12
        elif meridiem == "am" and h == 12:
            h = 0
            
        hour = h
        minute = m
        return hour, minute
    
    # Fallback: Return current time + 1 hour if parse fails
    print(f"   ⚠️ Could not parse time '{time_str}'. Defaulting to +1 hour.")
    now = datetime.now()
    return (now.hour + 1) % 24, 0

async def set_google_task(event_name: str, event_time: str, description: str = "", link: str = ""):
    """
    Sets a Google Task with description and link using a mix of Intent and UI Automation.
    """
    print(f"📝 [TASK] Creating Google Task: {event_name}")

    # 1. DIRECT INTENT TO CREATE TASK
    # This opens the Google Tasks "New Task" overlay immediately.
    launch_cmd = "adb shell am start -n com.google.android.apps.tasks/com.google.android.apps.tasks.ui.TaskShortcutActivity"
    subprocess.run(launch_cmd, shell=True)
    await asyncio.sleep(1.5) # Wait for the overlay to slide up

    # 2. FAST NAV: FILL TITLE
    # The title field is usually focused by default.
    clean_name = event_name.replace(" ", "%s")
    subprocess.run(f"adb shell input text '{clean_name}'", shell=True)

    # 3. CONSTRUCT DESCRIPTION
    # We combine the description and the link for the "Details" field.
    full_details = f"{description}\n\nLink: {link}".strip()
    
    # 4. AGENT TAKEOVER (To handle the 'Details' and 'Save' buttons)
    # This is safer than blind ADB because the "Details" icon location can shift.
    llm = GoogleGenAI(api_key=os.environ["GEMINI_API_KEY"], model="models/gemini-2.5-flash")
    config = DroidrunConfig(
        agent=AgentConfig(reasoning=True, max_steps=50),
        logging=LoggingConfig(debug=True, save_trajectory="action")
    )

    task_goal = (
        f"I have already typed the title '{event_name}'.\n"
        f"1. Tap the 'Details' or 'Add details' icon/field.\n"
        f"2. Type the following text: '{full_details}'\n"
        f"3. Tap the 'Date/Time' icon and set it to '{event_time}' if possible.\n"
        f"4. Tap 'Save' or 'Done'."
    )

    agent = DroidAgent(goal=task_goal, config=config, llms=llm)
    await agent.run()