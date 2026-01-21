# 🤖 Android "Ghost" System: AI Task Automation Agent

**Ghost System** is an intelligent, automated agent framework designed to bridge the gap between unstructured mobile communication and structured productivity tools.

It autonomously navigates a real Android device to **scrape event details from WhatsApp group chats**, **automatically schedules them into Google Tasks**, and **auto-joins video meetings** (Zoom/Meet/Teams) while ensuring your privacy settings are active.

---

## 🌟 Key Features

* **📱 Real-Device Automation**: Uses ADB (Android Debug Bridge) to control a physical or emulated Android device—no hacking or unofficial APIs required.
* **🧠 LLM-Powered Parsing**: Leverages **Google Gemini 2.5 Flash** to intelligently extract dates, times, and meeting links from natural language conversations.
* **Smart WhatsApp Scraper**:
    * Auto-navigates to specific groups defined in config.
    * Performs intelligent scrolling (historical lookup) to capture recent context.
    * Outputs structured JSON data.
* **📅 Google Tasks Auto-Entry**:
    * Handles complex UI interactions (Title, Description, Date/Time pickers).
    * **Smart Time Entry**: Uses a fallback strategy to switch Google Tasks' clock UI to "Keyboard Mode" for precise time setting.
* **🎥 Auto-Meeting Joiner**:
    * **Multi-Platform**: Supports Zoom, Google Meet, and Microsoft Teams.
    * **Privacy First**: Automatically toggles **OFF** Audio and Video before joining any meeting.
    * **Secure Access**: autonomously handles Meeting ID and Password entry.

---


## 🔄 The Workflow Pipeline

### Phase 1: The Scraper (`scraper_agent.py`)
1.  **Turbo Nav**: Force-stops and launches WhatsApp to ensure a clean state.
2.  **Search & Enter**: Types the group name and enters the chat.
3.  **Scroll & Extract**: Performs vertical swipes to load history and uses LLM to parse events into JSON.

### Phase 2: The Task Scheduler (`set_event.jinja2`)
1.  **Launch**: Opens Google Tasks.
2.  **Input**: Types Title and Description (including links).
3.  **Smart Time**: Switches UI to **Keyboard Input Mode** to set precise deadlines.
4.  **Save**: Commits the task.

### Phase 3: The Meeting Automator (`join_meeting.jinja2`)
1.  **Direct Launch**: Uses `adb shell monkey` to launch Zoom/Meet/Teams directly.
2.  **Join Flow**: Inputs Meeting ID.
3.  **Privacy Guard**:
    * **Critical**: Identifies and taps "Turn off Video" and "Turn off Audio" toggles.
    * **Verify**: Ensures switches are active before proceeding.
4.  **Credential Entry**: Handles Password/Passcode entry if prompted by the app.
5.  **Finalize**: Taps "Join" and waits for the "Waiting for Host" screen.

## 🛠️ Tech Stack

* **Core Language**: Python 3.10+
* **AI/LLM**: `llama-index`, Google Gemini 2.5 Flash API
* **Device Control**: ADB (Android Debug Bridge) via `subprocess`
* **Agent Framework**: `DroidRun` (Custom wrapper for agentic reasoning)
* **Data Validation**: Pydantic

---

## 📂 Project Structure

```text
ghost-system/
│
├── agents/
│   ├── __init__.py
│   ├── scraper_agent.py      # The "Eye": Navigates WhatsApp & extracts data
│   ├── models.py             # Pydantic models (GroupScrapeResult) for validation
|   |── meeeting_agent.py
|   |── event_agent.py
│   │
│   └── prompts/              # Prompt Engineering Hub
│       ├── __init__.py
│       ├── prompts.py        # Python loader/manager for templates
│       ├── set_event.jinja2   # Template for Task Creation
│       ├── scrape.jinja2   # Template for WhatsApp Parsing
│       └── join_meeting.jinja2  # Template for Zoom/Meet Automation
│
├── data/                     # Output folder for scraped JSON files
│
├── droidrun/                 # Core Agent Framework (Config, Agent, Executors)
│
├── main.py                   # The "Brain": Router logic & Agent orchestration
├── groups.json               # Config: List of WhatsApp groups to monitor
├── .env                      # Config: API Keys (GEMINI_API_KEY)
├── requirements.txt          # Python dependencies
└── README.md                 # This file