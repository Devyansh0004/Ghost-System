import asyncio
import os
import json
import subprocess
import time
from droidrun import DroidAgent
from droidrun.config_manager.config_manager import (
    DroidrunConfig, TracingConfig, LoggingConfig, AgentConfig, ManagerConfig, ExecutorConfig
)
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.tools import FunctionTool
from agents.prompts import prompts
from agents.models import GroupScrapeResult
from dotenv import load_dotenv

load_dotenv()

# --- 1. DEFINE SHELL TOOL FOR AGENT ---
def execute_shell_command(command: str) -> str:
    """Executes ADB commands. Used by Agent for swiping."""
    try:
        if "input text" in command: # Auto-fix spaces
            parts = command.split("input text")
            if len(parts) > 1:
                text = parts[1].strip().replace(" ", "%s").strip("'").strip('"')
                command = f"adb shell input text {text}"
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return f"✅ Output: {result.stdout.strip()}" if result.returncode == 0 else f"❌ Error: {result.stderr.strip()}"
    except Exception as e:
        return f"💥 Exception: {str(e)}"

shell_tool = FunctionTool.from_defaults(
    fn=execute_shell_command, name="shell_executor", description="Executes ADB commands. Use for 'adb shell input swipe' or 'input text'."
)

# --- 2. PYTHON FAST NAV ---
def adb_fast_nav(command: str, description: str):
    """Executes a blind ADB command for initial setup."""
    print(f"   ⚡ Fast Nav: {description}")
    if "input text" in command:
        parts = command.split("input text")
        if len(parts) > 1:
            text = parts[1].strip().replace(" ", "%s")
            command = f"adb shell input text {text}"
    subprocess.run(command, shell=True, timeout=5)
    time.sleep(1.0)

# --- 3. MAIN FUNCTION ---
async def scrape_whatsapp_group(group_name: str):
    # PHASE 1: TURBO NAVIGATION (Hardcoded ADB for Speed)
    try:
        # Reset and Launch
        adb_fast_nav("adb shell am force-stop com.whatsapp", "Reset WhatsApp")
        adb_fast_nav("adb shell monkey -p com.whatsapp 1", "Launch App")
        time.sleep(1.5) # Wait for splash screen
        
        # Search and Enter Chat
        adb_fast_nav("adb shell input keyevent 84", "Open Search") 
        adb_fast_nav(f"adb shell input text '{group_name}'", "Type Group Name")
        time.sleep(1.0) # Wait for search results
        adb_fast_nav("adb shell input keyevent 20", "Down Arrow to Result")
        adb_fast_nav("adb shell input keyevent 66", "Enter Chat")
        
        # ⚡ INSTANT JUMP TO BOTTOM
        # Keyevent 123 (Move to End) is reliable, but adding a fast swipe 
        # ensures we are at the absolute bottom.
        adb_fast_nav("adb shell input keyevent 123", "Jump to Bottom")
        adb_fast_nav("adb shell input swipe 500 500 500 200 100", "Quick Push to Bottom")
        
    except Exception as e:
        print(f"❌ Navigation Failed: {e}")
        return False

    # ... Rest of your agent setup ...

    # PHASE 2: AGENT TAKEOVER (Scanning & Swiping)
    print("   🧠 Chat Open. Waking Agent to Extract & Swipe...")
    
    llm = GoogleGenAI(api_key=os.environ["GEMINI_API_KEY"], model="gemini-2.5-flash")
    config = DroidrunConfig(
        agent=AgentConfig(reasoning=False, max_steps=50),
        logging=LoggingConfig(debug=True, save_trajectory="action")
    )

    # We inject the shell_tool so the Agent can swipe using ADB
    agent = DroidAgent(
        goal=prompts.SCRAPE_GROUP_GOAL(group_name),
        config=config,
        llms=llm,
        output_model=GroupScrapeResult,
        tools=[shell_tool]
    )

    result = await agent.run()

    # PHASE 3: SAVE DATA
    output_data = getattr(result, "output", None) or getattr(result, "structured_output", None)

    if result.success and output_data:
        if hasattr(output_data, "dict"): data_dict = output_data.dict()
        else: data_dict = output_data

        os.makedirs("data", exist_ok=True)
        filename = f"data/{group_name.replace(' ', '_')}_data.json"
        with open(filename, "w") as f:
            json.dump(data_dict, f, indent=4)
            
        print(f"✅ Data saved to {filename}")
        return True
    else:
        print(f"❌ Extraction Failed")
        return False