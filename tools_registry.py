import asyncio
import os
import subprocess
from llama_index.core.tools import FunctionTool

# --- Import DroidRun's Standard Tools ---
# Try to import default tools to merge them
try:
    from droidrun.tools import default_tools
except ImportError:
    default_tools = []

# --- Import Your Custom Logic ---
from agents.scraper_agent import scrape_whatsapp_group
from agents.meeting_agent import join_meeting_smart
from agents.event_agent import set_event_alarm

# ==============================================================================
# 1. SHELL EXECUTOR (The "Fast Hand")
# ==============================================================================
def execute_shell_command(command: str) -> str:
    """Executes ADB/System shell commands."""
    try:
        # Auto-fix spaces for input text
        if "input text" in command:
            parts = command.split("input text")
            if len(parts) > 1:
                clean_text = parts[1].strip().strip("'").strip('"').replace(" ", "%s")
                command = f"adb shell input text {clean_text}"
        
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10
        )
        return f"✅ Output: {result.stdout.strip()}" if result.returncode == 0 else f"❌ Error: {result.stderr.strip()}"
    except Exception as e:
        return f"💥 Exception: {str(e)}"

# ==============================================================================
# 2. SYNC WRAPPERS (So the Agent can call them easily)
# ==============================================================================
def sync_scrape(group_name: str) -> str:
    """Scrapes WhatsApp data. Use for 'get meeting links' or 'read group'."""
    return str(asyncio.run(scrape_whatsapp_group(group_name)))

def sync_join(group_name: str) -> str:
    """Joins a meeting found in the scraped data."""
    return str(asyncio.run(join_meeting_smart({"name": group_name}))) # Simplified payload

def sync_alarm(group_name: str) -> str:
    """Sets alarms based on scraped data."""
    return str(asyncio.run(set_event_alarm("Event", "10:00"))) # Simplified wrapper

# ==============================================================================
# 3. EXPORT ALL TOOLS (Default + Custom)
# ==============================================================================
def get_all_tools():
    custom_tools = [
        FunctionTool.from_defaults(
            fn=execute_shell_command, 
            name="shell_executor", 
            description="Executes ADB shell commands. Use for fast typing, scrolling, or launching apps."
        ),
        FunctionTool.from_defaults(
            fn=sync_scrape, 
            name="whatsapp_scraper", 
            description="Scrapes a WhatsApp group for meetings/events. Returns JSON."
        ),
        FunctionTool.from_defaults(
            fn=sync_join, 
            name="meeting_joiner", 
            description="Joins a meeting (Zoom/Meet) found in the group data."
        ),
        FunctionTool.from_defaults(
            fn=sync_alarm, 
            name="alarm_setter", 
            description="Sets alarms for events found in the group data."
        )
    ]
    
    # 🌟 THE FIX: Combine Standard Tools + Your Tools
    return default_tools + custom_tools

def get_tools_dict():
    """Returns a dictionary of the actual functions for injection into the Agent's globals."""
    return {
        "shell_executor": execute_shell_command,
        "whatsapp_scraper": sync_scrape,
        "meeting_joiner": sync_join,
        "alarm_setter": sync_alarm
    }