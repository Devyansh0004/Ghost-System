import os
from jinja2 import Template

def load_template(template_name):
    """
    Loads a Jinja2 template from the same directory as this script.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, template_name)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return Template(f.read())
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Template file not found: {file_path}")

# --- 1. WHATSAPP SCRAPER GOAL ---
def SCRAPE_GROUP_GOAL(group_name: str):
    return load_template("scrape.jinja2").render(
        group_name=group_name
    )

# --- 2. ALARM GOAL ---
def SET_ALARM_GOAL(time: str, label: str):
    return load_template("set_alarm.jinja2").render(
        time=time, 
        label=label
    )

# --- 3. MEETING GOAL (The Missing Function) ---
def JOIN_APP_SPECIFIC_GOAL(app_name: str, meeting_id: str, meeting_pass: str = None):
    """
    Dynamically generates instructions for Zoom, Meet, or Teams.
    """
    # Handle case where password is None or empty string
    if not meeting_pass:
        meeting_pass = "No Password"

    return load_template("join_meeting.jinja2").render(
        app_name=app_name,
        meeting_id=meeting_id,
        meeting_pass=meeting_pass
    )