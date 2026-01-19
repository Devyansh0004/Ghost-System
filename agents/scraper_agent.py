import asyncio
import os
import json
from droidrun import DroidAgent
from droidrun.config_manager.config_manager import (
    DroidrunConfig, TracingConfig, LoggingConfig, AgentConfig
)
from llama_index.llms.google_genai import GoogleGenAI
from agents.prompts import prompts
from agents.models import GroupScrapeResult
from dotenv import load_dotenv

load_dotenv()

async def scrape_whatsapp_group(group_name: str):
    print(f"🕵️ Scoping out group: {group_name}...")

    # 1. Setup LLM
    llm = GoogleGenAI(
        api_key=os.environ["GEMINI_API_KEY"],
        model="gemini-2.5-flash", 
    )

    # 2. Config 
    config = DroidrunConfig(
        agent=AgentConfig(reasoning=True, max_steps=20),
        tracing=TracingConfig(enabled=False),
        logging=LoggingConfig(debug=True, save_trajectory="action"),
    )

    # 3. Initialize Agent
    agent = DroidAgent(
        goal=prompts.SCRAPE_GROUP_GOAL(group_name),
        config=config,
        llms=llm,
        output_model=GroupScrapeResult, 
    )

    # 4. Run
    result = await agent.run()

    # 5. ROBUST DATA EXTRACTION
    # The data might be in 'output' OR 'structured_output' depending on the DroidRun version
    output_data = getattr(result, "output", None)
    
    if output_data is None:
        output_data = getattr(result, "structured_output", None)

    # 6. Save Data if found
    if result.success and output_data:
        # If output_data is a Pydantic model (which it should be), dump it to dict
        if hasattr(output_data, "model_dump"):
            data_dict = output_data.model_dump()
        elif hasattr(output_data, "dict"):
            data_dict = output_data.dict()
        else:
            data_dict = output_data # Fallback

        os.makedirs("data", exist_ok=True)
        filename = f"data/{group_name.replace(' ', '_')}_data.json"
        
        with open(filename, "w") as f:
            json.dump(data_dict, f, indent=4)
            
        # Safe access to list lengths for printing
        num_meetings = len(data_dict.get('meetings', []))
        num_events = len(data_dict.get('events', []))
        
        print(f"✅ Data saved to {filename}")
        print(f"   Found {num_meetings} meetings and {num_events} events.")
        return True
    else:
        print(f"❌ Failed to scrape {group_name}")
        # Print the reason if available
        reason = getattr(result, "reason", "Unknown reason")
        print(f"Reason: {reason}")
        return False