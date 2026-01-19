import asyncio
import os
from droidrun import DroidAgent
from droidrun.config_manager.config_manager import DroidrunConfig, AgentConfig, LoggingConfig
from llama_index.llms.google_genai import GoogleGenAI
from agents.prompts import prompts
from dotenv import load_dotenv

load_dotenv()

async def set_event_alarm(event_name: str, event_time: str):
    print(f"⏰ [ALARM] Setting alarm for '{event_name}' at {event_time}...")

    llm = GoogleGenAI(api_key=os.environ["GEMINI_API_KEY"], model="gemini-2.5-flash")
    
    # We don't need strict JSON output here, just success/fail
    config = DroidrunConfig(
        agent=AgentConfig(reasoning=True, max_steps=20),
        logging=LoggingConfig(debug=True, save_trajectory="action"),
    )

    agent = DroidAgent(
        goal=prompts.SET_ALARM_GOAL(time=event_time, label=event_name),
        config=config,
        llms=llm,
    )

    result = await agent.run()
    
    if result.success:
        print(f"✅ [ALARM] Set successfully for {event_time}")
        return True
    else:
        print(f"❌ [ALARM] Failed to set.")
        return False