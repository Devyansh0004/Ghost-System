#!/usr/bin/env python3
import asyncio
import os
import json
import subprocess
import nest_asyncio
from dotenv import load_dotenv
from droidrun import DroidAgent
from droidrun.config_manager.config_manager import DroidrunConfig, AgentConfig, LoggingConfig, ManagerConfig, ExecutorConfig
from llama_index.llms.google_genai import GoogleGenAI

# 1. Initialize environment
nest_asyncio.apply() 
load_dotenv()

# --- 🛠️ AGENT BRIDGES (Calling your scripts as processes) ---
def run_scraper_agent(group_name: str):
    """Triggers your scraper_agent.py script."""
    print(f"   🚀 Launching Scraper Agent for: {group_name}")
    # Using 'python3 agents/scraper_agent.py' assuming the structure from your image
    result = subprocess.run(
        ["python3", "-c", f"import asyncio; from agents.scraper_agent import scrape_whatsapp_group; asyncio.run(scrape_whatsapp_group('{group_name}'))"],
        capture_output=True, text=True
    )
    return result.stdout

def run_alarm_agent(name: str, time: str):
    """Triggers your alarm_agent.py script."""
    print(f"   ⏰ Launching Alarm Agent: {name} at {time}")
    result = subprocess.run(
        ["python3", "-c", f"import asyncio; from agents.alarm_agent import set_event_alarm; asyncio.run(set_event_alarm('{name}', '{time}'))"],
        capture_output=True, text=True
    )
    return result.stdout

# --- HELPER FUNCTIONS ---
def load_groups(filename="groups.json"):
    if not os.path.exists(filename): return []
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            return [g for g in data if isinstance(g, str)]
    except Exception: return []

async def main():
    print("👻 Ghost System: Intelligent Router Starting...")
    
    # Setup LLM - Using Gemini 2.5 Flash for the router
    llm = GoogleGenAI(api_key=os.environ["GEMINI_API_KEY"], model="models/gemini-2.5-flash")
    
    config = DroidrunConfig(
        agent=AgentConfig(reasoning=True, max_steps=50),
        logging=LoggingConfig(debug=True, save_trajectory="action")
    )

    while True:
        print("\n" + "="*40 + "\n🤖 Ghost System Command Center\n" + "="*40)
        print("1. 🟢 Task: Specific Workflow (Join Meeting and set events based on chat data from Whatsapp")
        print("2. 🔵 Task: Generic / Custom Request")
        print("q. 🔴 Quit")
        
        choice = input("\n👉 Select Option: ").strip().lower()
        if choice == 'q': break

        if choice == '1':
            target_groups = load_groups() #
            for group in target_groups:
                print(f"\n--- 🟢 Workflow: '{group}' ---")
                
                # Step 1: Run your Scraper Agent first manually
                scrape_output = run_scraper_agent(group)
                print(f"   📝 Scraper Result: {scrape_output}")
                
                # Step 2: Use the Main Agent to process the findings
                task_goal = (
                    f"I have just run the scraper for '{group}'. Here is the data found: {scrape_output}\n\n"
                    f"GOAL: Based on this data, navigate the phone to join any meetings "
                    f"using Zoom/Meet or set event details on GGOGLE TASK app."
                )
                
                agent = DroidAgent(goal=task_goal, config=config, llms=llm)
                await agent.run()

        elif choice == '2':
            user_prompt = input("   💬 Describe your task: ")
            agent = DroidAgent(goal=user_prompt, config=config, llms=llm)
            await agent.run()

    print("🏁 System Shutdown.")

if __name__ == "__main__":
    asyncio.run(main())